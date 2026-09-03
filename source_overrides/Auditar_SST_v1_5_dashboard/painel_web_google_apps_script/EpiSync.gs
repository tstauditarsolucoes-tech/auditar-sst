const EPI_SYNC_FOLDER = 'Auditar EPI';
const EPI_SYNC_DATA_FOLDER = 'Dados';
const EPI_SYNC_FILE = 'auditar_epi_sync.json';
const EPI_SYNC_VERSION = 1;

/**
 * Sincronização compartilhada entre Auditar EPI Campo e Gestão.
 * Reutiliza AUDITAR_SYNC_KEY do projeto atual.
 *
 * Rota esperada no doPost:
 * if (request.action === 'epi_sync_merge') {
 *   if (request.syncKey !== expectedKey) return jsonResponse_({ok:false,message:'Chave de sincronização inválida.'});
 *   return jsonResponse_(epiSyncMerge_(request));
 * }
 */
function epiSyncMerge_(request) {
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const incoming = normalizeEpiSnapshot_(request && request.payload);
    const stored = readEpiSnapshot_();
    const merged = mergeEpiSnapshots_(stored, incoming);
    merged.revision = Math.max(Number(stored.revision || 0), Number(incoming.revision || 0)) + 1;
    merged.updatedAt = new Date().toISOString();
    merged.version = EPI_SYNC_VERSION;
    writeEpiSnapshot_(merged);
    return {
      ok: true,
      revision: merged.revision,
      updatedAt: merged.updatedAt,
      payload: merged,
      message: 'Auditar EPI sincronizado.'
    };
  } catch (error) {
    return {ok:false, message:'Falha na sincronização do Auditar EPI: ' + String(error)};
  } finally {
    lock.releaseLock();
  }
}

function epiSyncStatus_() {
  const data = readEpiSnapshot_();
  return {
    ok: true,
    revision: Number(data.revision || 0),
    updatedAt: String(data.updatedAt || ''),
    companies: data.app.companies.length,
    workers: data.app.workers.length,
    epis: data.app.epis.length,
    deliveries: data.app.deliveries.length,
    stockMovements: data.stock.movements.length
  };
}

function normalizeEpiSnapshot_(value) {
  const root = value && typeof value === 'object' ? value : {};
  const app = root.app && typeof root.app === 'object' ? root.app : {};
  const stock = root.stock && typeof root.stock === 'object' ? root.stock : {};
  return {
    version: Number(root.version || EPI_SYNC_VERSION),
    revision: Number(root.revision || 0),
    updatedAt: String(root.updatedAt || ''),
    app: {
      companies: normalizeArray_(app.companies),
      workers: normalizeArray_(app.workers),
      epis: normalizeArray_(app.epis),
      deliveries: normalizeArray_(app.deliveries)
    },
    stock: {
      startedAt: String(stock.startedAt || ''),
      processedDeliveryIds: uniqueStrings_(stock.processedDeliveryIds),
      movements: normalizeArray_(stock.movements),
      minimums: normalizeMap_(stock.minimums)
    }
  };
}

function blankEpiSnapshot_() {
  return normalizeEpiSnapshot_({});
}

function mergeEpiSnapshots_(server, client) {
  server = normalizeEpiSnapshot_(server);
  client = normalizeEpiSnapshot_(client);
  return {
    version: EPI_SYNC_VERSION,
    revision: Math.max(server.revision, client.revision),
    updatedAt: server.updatedAt || client.updatedAt || '',
    app: {
      companies: mergeRecordsById_(server.app.companies, client.app.companies),
      workers: mergeRecordsById_(server.app.workers, client.app.workers),
      epis: mergeRecordsById_(server.app.epis, client.app.epis),
      // Entregas são registros históricos: nunca são sobrescritas por um registro vazio.
      deliveries: mergeRecordsById_(server.app.deliveries, client.app.deliveries)
    },
    stock: {
      startedAt: earliestIso_(server.stock.startedAt, client.stock.startedAt),
      processedDeliveryIds: uniqueStrings_(server.stock.processedDeliveryIds.concat(client.stock.processedDeliveryIds)),
      movements: mergeRecordsById_(server.stock.movements, client.stock.movements),
      minimums: Object.assign({}, server.stock.minimums, client.stock.minimums)
    }
  };
}

function mergeRecordsById_(a, b) {
  const map = {};
  normalizeArray_(a).concat(normalizeArray_(b)).forEach(function(item) {
    const id = String(item && item.id || '').trim();
    if (!id) return;
    const current = map[id];
    if (!current) {
      map[id] = item;
      return;
    }
    const currentTime = recordTime_(current);
    const incomingTime = recordTime_(item);
    // Em empate, conserva o registro mais completo.
    if (incomingTime > currentTime || (incomingTime === currentTime && JSON.stringify(item).length > JSON.stringify(current).length)) {
      map[id] = item;
    }
  });
  return Object.keys(map).map(function(id){ return map[id]; });
}

function recordTime_(item) {
  const raw = String(item && (item.updatedAt || item.createdAt) || '');
  const t = Date.parse(raw);
  return isNaN(t) ? 0 : t;
}

function normalizeArray_(value) {
  return Array.isArray(value) ? value.filter(function(x){ return x && typeof x === 'object'; }) : [];
}

function normalizeMap_(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {};
  const out = {};
  Object.keys(value).forEach(function(k){ out[String(k)] = value[k]; });
  return out;
}

function uniqueStrings_(value) {
  const seen = {};
  const out = [];
  (Array.isArray(value) ? value : []).forEach(function(v){
    const s = String(v || '').trim();
    if (!s || seen[s]) return;
    seen[s] = true; out.push(s);
  });
  return out;
}

function earliestIso_(a, b) {
  if (!a) return b || '';
  if (!b) return a || '';
  const ta = Date.parse(a), tb = Date.parse(b);
  if (isNaN(ta)) return b;
  if (isNaN(tb)) return a;
  return ta <= tb ? a : b;
}

function getEpiDataFolder_() {
  const root = findOrCreateDriveFolder_(DriveApp.getRootFolder(), EPI_SYNC_FOLDER);
  return findOrCreateDriveFolder_(root, EPI_SYNC_DATA_FOLDER);
}

function getEpiSyncFile_() {
  const folder = getEpiDataFolder_();
  const files = folder.getFilesByName(EPI_SYNC_FILE);
  if (files.hasNext()) return files.next();
  return folder.createFile(EPI_SYNC_FILE, JSON.stringify(blankEpiSnapshot_()), MimeType.PLAIN_TEXT);
}

function readEpiSnapshot_() {
  const file = getEpiSyncFile_();
  try {
    return normalizeEpiSnapshot_(JSON.parse(file.getBlob().getDataAsString('UTF-8') || '{}'));
  } catch (_) {
    return blankEpiSnapshot_();
  }
}

function writeEpiSnapshot_(data) {
  const file = getEpiSyncFile_();
  file.setContent(JSON.stringify(normalizeEpiSnapshot_(data)));
}

function configurarAuditarEpi() {
  getEpiSyncFile_();
  const props = PropertiesService.getScriptProperties();
  const hasKey = String(props.getProperty('AUDITAR_SYNC_KEY') || '').trim() !== '';
  if (!hasKey) throw new Error('Execute setupAuditar() primeiro para criar a chave de sincronização.');
  Logger.log('Auditar EPI pronto para sincronizar Campo e Gestão.');
  Logger.log(JSON.stringify(epiSyncStatus_()));
  return epiSyncStatus_();
}

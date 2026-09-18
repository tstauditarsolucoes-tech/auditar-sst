const SST_EPI_SYNC_VERSION = 2;
const SST_EPI_FOLDER = 'EPI';
const SST_EPI_DATA_FOLDER = 'Dados';
const SST_EPI_SYNC_FILE = 'epi_sync.json';
const SST_EPI_PURCHASE_FOLDER = 'Notas Fiscais';

function sstEpiSyncMerge_(request) {
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const incoming = sstEpiNormalizeSnapshot_(request && request.payload);
    const stored = sstEpiReadSnapshot_();
    const merged = sstEpiMergeSnapshots_(stored, incoming);
    sstEpiEnsureDeliveryStock_(merged);
    merged.revision = Math.max(Number(stored.revision || 0), Number(incoming.revision || 0)) + 1;
    merged.updatedAt = new Date().toISOString();
    merged.version = SST_EPI_SYNC_VERSION;
    sstEpiWriteSnapshot_(merged);
    return {
      ok: true,
      revision: merged.revision,
      updatedAt: merged.updatedAt,
      payload: merged,
      message: 'Gestão de EPI sincronizada.'
    };
  } catch (error) {
    return {ok:false, message:'Falha na sincronização de EPI: ' + String(error)};
  } finally {
    lock.releaseLock();
  }
}

function sstEpiStatus_() {
  const data = sstEpiReadSnapshot_();
  return {
    ok:true,
    revision:Number(data.revision || 0),
    updatedAt:String(data.updatedAt || ''),
    companies:data.app.companies.length,
    workers:data.app.workers.length,
    epis:data.app.epis.length,
    deliveries:data.app.deliveries.length,
    purchases:data.app.purchases.length,
    batches:data.app.batches.length,
    auditEvents:data.app.auditLog.length,
    stockMovements:data.stock.movements.length
  };
}

function sstEpiNormalizeSnapshot_(value) {
  const root = value && typeof value === 'object' ? value : {};
  const app = root.app && typeof root.app === 'object' ? root.app : {};
  const stock = root.stock && typeof root.stock === 'object' ? root.stock : {};
  return {
    version:Number(root.version || SST_EPI_SYNC_VERSION),
    revision:Number(root.revision || 0),
    updatedAt:String(root.updatedAt || ''),
    app:{
      companies:sstEpiNormalizeArray_(app.companies),
      workers:sstEpiNormalizeArray_(app.workers),
      epis:sstEpiNormalizeArray_(app.epis),
      deliveries:sstEpiNormalizeArray_(app.deliveries),
      purchases:sstEpiNormalizeArray_(app.purchases),
      batches:sstEpiNormalizeArray_(app.batches),
      auditLog:sstEpiNormalizeArray_(app.auditLog).slice(-1000)
    },
    stock:{
      startedAt:String(stock.startedAt || ''),
      processedDeliveryIds:sstEpiUniqueStrings_(stock.processedDeliveryIds),
      movements:sstEpiNormalizeArray_(stock.movements),
      minimums:sstEpiNormalizeMap_(stock.minimums)
    }
  };
}

function sstEpiBlankSnapshot_() {
  return sstEpiNormalizeSnapshot_({});
}

function sstEpiMergeSnapshots_(server, client) {
  server = sstEpiNormalizeSnapshot_(server);
  client = sstEpiNormalizeSnapshot_(client);
  return {
    version:SST_EPI_SYNC_VERSION,
    revision:Math.max(server.revision, client.revision),
    updatedAt:server.updatedAt || client.updatedAt || '',
    app:{
      companies:sstEpiMergeRecords_(server.app.companies, client.app.companies),
      workers:sstEpiMergeRecords_(server.app.workers, client.app.workers),
      epis:sstEpiMergeRecords_(server.app.epis, client.app.epis),
      deliveries:sstEpiMergeRecords_(server.app.deliveries, client.app.deliveries),
      purchases:sstEpiMergeRecords_(server.app.purchases, client.app.purchases),
      batches:sstEpiMergeRecords_(server.app.batches, client.app.batches),
      auditLog:sstEpiMergeRecords_(server.app.auditLog, client.app.auditLog).slice(-1000)
    },
    stock:{
      startedAt:sstEpiEarliestIso_(server.stock.startedAt, client.stock.startedAt),
      processedDeliveryIds:sstEpiUniqueStrings_(
        server.stock.processedDeliveryIds.concat(client.stock.processedDeliveryIds)
      ),
      movements:sstEpiMergeRecords_(server.stock.movements, client.stock.movements),
      minimums:Object.assign({}, server.stock.minimums, client.stock.minimums)
    }
  };
}

function sstEpiEnsureDeliveryStock_(snapshot) {
  const data = sstEpiNormalizeSnapshot_(snapshot);
  const existing = {};
  data.stock.movements.forEach(function(m) {
    const deliveryId = String(m && m.deliveryId || '').trim();
    const epiId = String(m && m.epiId || '').trim();
    const batchId = String(m && m.batchId || '').trim();
    if (deliveryId && epiId && String(m.type || '') === 'OUT') {
      existing[deliveryId + '::' + epiId + '::' + batchId] = true;
    }
  });

  data.app.deliveries.forEach(function(d) {
    const deliveryId = String(d && d.id || '').trim();
    const companyId = String(d && d.companyId || '').trim();
    if (!deliveryId || !companyId) return;
    const totals = {};
    (Array.isArray(d.items) ? d.items : []).forEach(function(item) {
      const epiId = String(item && item.epiId || '').trim();
      const batchId = String(item && item.batchId || '').trim();
      const qty = Math.max(0, Number(item && item.qty || 0));
      if (!epiId || !qty) return;
      const key = epiId + '::' + batchId;
      if (!totals[key]) {
        totals[key] = {
          epiId:epiId,
          batchId:batchId,
          purchaseId:String(item && item.purchaseId || ''),
          lot:String(item && item.lot || ''),
          physicalExpiry:String(item && item.physicalExpiry || ''),
          invoiceNumber:String(item && item.invoiceNumber || ''),
          qty:0
        };
      }
      totals[key].qty += qty;
    });

    Object.keys(totals).forEach(function(totalKey) {
      const row = totals[totalKey];
      const key = deliveryId + '::' + row.epiId + '::' + row.batchId;
      if (existing[key]) return;
      data.stock.movements.push({
        id:'epi_out_' + deliveryId + '_' + row.epiId + '_' + (row.batchId || 'legacy'),
        type:'OUT',
        delta:-row.qty,
        companyId:companyId,
        epiId:row.epiId,
        batchId:row.batchId,
        purchaseId:row.purchaseId,
        lot:row.lot,
        physicalExpiry:row.physicalExpiry,
        invoiceNumber:row.invoiceNumber,
        deliveryId:deliveryId,
        workerId:String(d.workerId || ''),
        note:'Baixa automática da entrega' + (row.lot ? ' • lote ' + row.lot : ''),
        createdAt:String(d.createdAt || new Date().toISOString()),
        updatedAt:String(d.updatedAt || d.createdAt || new Date().toISOString())
      });
      const minKey = companyId + '::' + row.epiId;
      if (data.stock.minimums[minKey] == null) data.stock.minimums[minKey] = 5;
      existing[key] = true;
    });
    data.stock.processedDeliveryIds.push(deliveryId);
  });

  data.stock.processedDeliveryIds = sstEpiUniqueStrings_(data.stock.processedDeliveryIds);
  snapshot.stock = data.stock;
}

function sstEpiMergeRecords_(a, b) {
  const map = {};
  sstEpiNormalizeArray_(a).concat(sstEpiNormalizeArray_(b)).forEach(function(item) {
    const id = String(item && item.id || '').trim();
    if (!id) return;
    const current = map[id];
    if (!current) {
      map[id] = item;
      return;
    }
    const currentTime = sstEpiRecordTime_(current);
    const incomingTime = sstEpiRecordTime_(item);
    if (
      incomingTime > currentTime ||
      (incomingTime === currentTime && JSON.stringify(item).length > JSON.stringify(current).length)
    ) {
      map[id] = item;
    }
  });
  return Object.keys(map).map(function(id){ return map[id]; });
}

function sstEpiRecordTime_(item) {
  const raw = String(item && (item.updatedAt || item.createdAt) || '');
  const value = Date.parse(raw);
  return isNaN(value) ? 0 : value;
}

function sstEpiNormalizeArray_(value) {
  return Array.isArray(value)
    ? value.filter(function(x){ return x && typeof x === 'object'; })
    : [];
}

function sstEpiNormalizeMap_(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {};
  const out = {};
  Object.keys(value).forEach(function(key){ out[String(key)] = value[key]; });
  return out;
}

function sstEpiUniqueStrings_(value) {
  const seen = {};
  const out = [];
  (Array.isArray(value) ? value : []).forEach(function(v) {
    const s = String(v || '').trim();
    if (!s || seen[s]) return;
    seen[s] = true;
    out.push(s);
  });
  return out;
}

function sstEpiEarliestIso_(a, b) {
  if (!a) return b || '';
  if (!b) return a || '';
  const ta = Date.parse(a);
  const tb = Date.parse(b);
  if (isNaN(ta)) return b;
  if (isNaN(tb)) return a;
  return ta <= tb ? a : b;
}

function sstEpiRootFolder_() {
  const root = typeof ensureDriveRootFolder_ === 'function'
    ? ensureDriveRootFolder_()
    : sstEpiFindOrCreateFolder_(DriveApp.getRootFolder(), 'SST Gestão');
  return sstEpiFindOrCreateFolder_(root, SST_EPI_FOLDER);
}

function sstEpiDataFolder_() {
  return sstEpiFindOrCreateFolder_(sstEpiRootFolder_(), SST_EPI_DATA_FOLDER);
}

function sstEpiFindOrCreateFolder_(parent, name) {
  const it = parent.getFoldersByName(name);
  return it.hasNext() ? it.next() : parent.createFolder(name);
}

function sstEpiSyncFile_() {
  const folder = sstEpiDataFolder_();
  const files = folder.getFilesByName(SST_EPI_SYNC_FILE);
  if (files.hasNext()) return files.next();
  return folder.createFile(
    SST_EPI_SYNC_FILE,
    JSON.stringify(sstEpiBlankSnapshot_()),
    MimeType.PLAIN_TEXT
  );
}

function sstEpiReadSnapshot_() {
  try {
    return sstEpiNormalizeSnapshot_(
      JSON.parse(sstEpiSyncFile_().getBlob().getDataAsString('UTF-8') || '{}')
    );
  } catch (_) {
    return sstEpiBlankSnapshot_();
  }
}

function sstEpiWriteSnapshot_(data) {
  sstEpiSyncFile_().setContent(JSON.stringify(sstEpiNormalizeSnapshot_(data)));
}

function configurarSstGestaoEpi() {
  sstEpiSyncFile_();
  Logger.log(JSON.stringify(sstEpiStatus_()));
  return sstEpiStatus_();
}

function sstEpiAiAssistant_(payload) {
  payload = payload && typeof payload === 'object' ? payload : {};
  const mode = String(payload.mode || '').trim();

  if (mode === 'employee_pdf_import' && typeof runAiAssistant_ === 'function') {
    return runAiAssistant_(payload);
  }
  if (mode === 'invoice_pdf_import') {
    return sstEpiInvoicePdf_(String(payload.document || ''));
  }
  if (mode === 'ca_validate') {
    return sstEpiValidateCa_(Array.isArray(payload.items) ? payload.items : []);
  }
  return {ok:false, code:'EPI_AI_MODE_UNSUPPORTED', message:'Modo de IA de EPI não suportado: ' + mode};
}

function sstEpiGeminiKey_() {
  const props = PropertiesService.getScriptProperties();
  return String(
    props.getProperty('GEMINI_API_KEY') ||
    props.getProperty('GOOGLE_AI_API_KEY') ||
    ''
  ).trim();
}

function sstEpiGeminiModels_() {
  const props = PropertiesService.getScriptProperties();
  const configured = String(props.getProperty('SST_GESTAO_AI_MODEL') || '').trim();
  return [configured, 'gemini-2.5-flash', 'gemini-2.5-flash-lite']
    .filter(function(v, i, a){ return v && a.indexOf(v) === i; });
}

function sstEpiGenerateJson_(body) {
  const key = sstEpiGeminiKey_();
  if (!key) throw new Error('Configure GEMINI_API_KEY nas Propriedades do Script.');
  const models = sstEpiGeminiModels_();
  let lastError = null;

  for (let i = 0; i < models.length; i++) {
    const model = models[i];
    try {
      const response = UrlFetchApp.fetch(
        'https://generativelanguage.googleapis.com/v1beta/models/' +
          encodeURIComponent(model) +
          ':generateContent?key=' +
          encodeURIComponent(key),
        {
          method:'post',
          contentType:'application/json',
          payload:JSON.stringify(body),
          muteHttpExceptions:true,
          followRedirects:true
        }
      );
      const status = Number(response.getResponseCode() || 0);
      const raw = response.getContentText('UTF-8');
      if (status < 200 || status >= 300) {
        throw new Error('Gemini HTTP ' + status + ': ' + raw.substring(0, 300));
      }
      const data = JSON.parse(raw || '{}');
      const text = String(
        data &&
        data.candidates &&
        data.candidates[0] &&
        data.candidates[0].content &&
        data.candidates[0].content.parts &&
        data.candidates[0].content.parts[0] &&
        data.candidates[0].content.parts[0].text ||
        ''
      ).trim();
      const cleaned = text.replace(/^\`\`\`(?:json)?/i, '').replace(/\`\`\`$/,'').trim();
      return {json:JSON.parse(cleaned || '{}'), model:model};
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError || new Error('Nenhum modelo Gemini respondeu.');
}

function sstEpiNormalizeDate_(value) {
  const s = String(value || '').trim();
  if (!s) return '';
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
  const m = s.match(/^(\d{1,2})[\/\-.](\d{1,2})[\/\-.](\d{4})$/);
  if (!m) return '';
  return m[3] + '-' + ('0' + m[2]).slice(-2) + '-' + ('0' + m[1]).slice(-2);
}

function sstEpiInvoicePdf_(documentData) {
  try {
    if (!/^data:application\/pdf;base64,/i.test(documentData)) {
      return {ok:false, message:'Envie um PDF válido da nota fiscal.'};
    }
    if (documentData.length > 18000000) {
      return {ok:false, message:'O PDF é muito grande para análise por IA.'};
    }
    const base64 = documentData.substring(documentData.indexOf(',') + 1);
    const prompt = [
      'Analise este DANFE/NF-e de compra e extraia SOMENTE itens que sejam EPI (Equipamento de Proteção Individual).',
      'Ignore ferramentas, materiais e produtos que não sejam EPI.',
      'Leia QUANT como qty; código do produto nunca é quantidade.',
      'Mantenha código, nome, CA, tamanho, fabricante, lote e validade separados.',
      'NUNCA invente CA, lote ou validade. Campo ausente deve ser string vazia.',
      'Use physicalExpiry no formato YYYY-MM-DD quando a validade estiver legível.',
      'Extraia number, series, key, date, supplier e supplierCnpj da nota.',
      'Retorne SOMENTE JSON válido no formato:',
      '{"invoice":{"number":"","series":"","key":"","date":"","supplier":"","supplierCnpj":"","items":[{"code":"","name":"","ca":"","size":"","unit":"","qty":1,"unitValue":0,"total":0,"manufacturer":"","lot":"","physicalExpiry":"","isEpi":true,"confidence":0.9}]}}'
    ].join('\n');

    const generated = sstEpiGenerateJson_({
      contents:[{
        role:'user',
        parts:[
          {text:prompt},
          {inlineData:{mimeType:'application/pdf',data:base64}}
        ]
      }],
      generationConfig:{temperature:0.05,responseMimeType:'application/json'}
    });
    const root = generated.json || {};
    const invoice = root.invoice && typeof root.invoice === 'object' ? root.invoice : root;
    const items = (Array.isArray(invoice.items) ? invoice.items : [])
      .map(function(i) {
        return {
          code:String(i && i.code || '').trim(),
          name:String(i && i.name || '').trim(),
          ca:String(i && i.ca || '').replace(/\D/g,''),
          size:String(i && i.size || '').trim(),
          unit:String(i && i.unit || '').trim(),
          qty:Math.max(0,Number(i && i.qty || 0)),
          unitValue:Number(i && i.unitValue || 0),
          total:Number(i && i.total || 0),
          manufacturer:String(i && i.manufacturer || '').trim(),
          lot:String(i && i.lot || '').trim(),
          physicalExpiry:sstEpiNormalizeDate_(i && (i.physicalExpiry || i.expiry || i.validity)),
          isEpi:i && i.isEpi !== false,
          confidence:Number(i && i.confidence || 0)
        };
      })
      .filter(function(i){ return i.name && i.isEpi && i.qty > 0; });

    return {
      ok:true,
      provider:'gemini',
      model:generated.model,
      result:{invoice:{
        number:String(invoice.number || '').trim(),
        series:String(invoice.series || '').trim(),
        key:String(invoice.key || '').replace(/\D/g,''),
        date:String(invoice.date || '').trim(),
        supplier:String(invoice.supplier || '').trim(),
        supplierCnpj:String(invoice.supplierCnpj || '').trim(),
        items:items
      }}
    };
  } catch (error) {
    return {ok:false, code:'INVOICE_AI_FAILED', message:'A IA não conseguiu organizar a nota fiscal: ' + String(error)};
  }
}

function sstEpiValidateCa_(items) {
  const unique = {};
  (items || []).slice(0, 20).forEach(function(item) {
    const ca = String(item && item.ca || '').replace(/\D/g,'');
    if (ca) unique[ca] = item;
  });

  const checks = Object.keys(unique).map(function(ca) {
    const proxy = sstEpiCaProxyLookup_(ca);
    if (proxy && proxy.found) return proxy;
    const ai = sstEpiCaGeminiLookup_(ca, unique[ca]);
    if (ai && ai.found) return ai;
    return {
      ca:ca,
      found:false,
      status:'não confirmado',
      equipment:'',
      manufacturer:'',
      validity:'',
      sourceUrl:'https://caepi.trabalho.gov.br/internet/ConsultaCAInternet.aspx'
    };
  });
  return {ok:true, result:{checks:checks}, provider:'mte-caepi'};
}

function sstEpiCaProxyLookup_(ca) {
  const props = PropertiesService.getScriptProperties();
  const base = String(
    props.getProperty('SST_GESTAO_CA_PROXY_URL') ||
    props.getProperty('GESTAO_EPI_CA_PROXY_URL') ||
    ''
  ).trim();
  if (!base) return null;
  try {
    const response = UrlFetchApp.fetch(
      base.replace(/\/+$/,'') + '/?ca=' + encodeURIComponent(ca),
      {method:'get',muteHttpExceptions:true,followRedirects:true}
    );
    const status = Number(response.getResponseCode() || 0);
    if (status < 200 || status >= 300) return null;
    const data = JSON.parse(response.getContentText('UTF-8') || '{}');
    if (!data || !data.ok || data.found === false) return null;
    return {
      ca:String(data.ca || ca),
      found:true,
      status:String(data.status || 'confirmado'),
      equipment:String(data.equipment || ''),
      manufacturer:String(data.manufacturer || ''),
      validity:String(data.validity || ''),
      sourceUrl:'https://caepi.trabalho.gov.br/internet/ConsultaCAInternet.aspx'
    };
  } catch (_) {
    return null;
  }
}

function sstEpiCaGeminiLookup_(ca, item) {
  if (!sstEpiGeminiKey_()) return null;
  try {
    const generated = sstEpiGenerateJson_({
      contents:[{role:'user',parts:[{text:[
        'Valide o Certificado de Aprovação CA ' + ca + ' de EPI.',
        'Use somente informação oficial do Ministério do Trabalho/CAEPI.',
        'Nome informado: ' + String(item && item.name || ''),
        'Fabricante informado: ' + String(item && item.manufacturer || ''),
        'Se não conseguir confirmar com segurança, found deve ser false.',
        'Retorne somente JSON: {"ca":"' + ca + '","found":true,"status":"","equipment":"","manufacturer":"","validity":""}'
      ].join('\n')}]}],
      tools:[{google_search:{}}],
      generationConfig:{temperature:0.05,responseMimeType:'application/json'}
    });
    const x = generated.json || {};
    return {
      ca:ca,
      found:x.found === true,
      status:String(x.status || (x.found ? 'confirmado' : 'não confirmado')),
      equipment:String(x.equipment || ''),
      manufacturer:String(x.manufacturer || ''),
      validity:String(x.validity || ''),
      sourceUrl:'https://caepi.trabalho.gov.br/internet/ConsultaCAInternet.aspx'
    };
  } catch (_) {
    return null;
  }
}

function sstEpiStorePurchaseDocument_(request) {
  try {
    const doc = String(request && request.document || '');
    if (!/^data:application\/pdf;base64,/i.test(doc)) {
      return {ok:false,message:'Documento de nota fiscal inválido.'};
    }
    if (doc.length > 18000000) return {ok:false,message:'PDF muito grande.'};

    const meta = request && request.meta && typeof request.meta === 'object'
      ? request.meta
      : {};
    const companyName = String(meta.companyName || 'Sem empresa')
      .replace(/[\\/:*?"<>|]/g,'_')
      .trim()
      .slice(0,80);
    const invoiceNumber = String(meta.invoiceNumber || 'sem_numero')
      .replace(/[^A-Za-z0-9_-]+/g,'_')
      .slice(0,40);
    const folder = sstEpiFindOrCreateFolder_(sstEpiRootFolder_(), SST_EPI_PURCHASE_FOLDER);
    const companyFolder = sstEpiFindOrCreateFolder_(folder, companyName || 'Sem empresa');
    const bytes = Utilities.base64Decode(doc.substring(doc.indexOf(',') + 1));
    const fileName = 'NF_' + invoiceNumber + '_' + Utilities.formatDate(
      new Date(),
      Session.getScriptTimeZone() || 'America/Fortaleza',
      'yyyyMMdd_HHmmss'
    ) + '.pdf';
    const file = companyFolder.createFile(Utilities.newBlob(bytes, 'application/pdf', fileName));
    return {ok:true,fileId:file.getId(),fileName:fileName,message:'Nota fiscal salva no Drive.'};
  } catch (error) {
    return {ok:false,message:'Falha ao salvar a nota fiscal: ' + String(error)};
  }
}

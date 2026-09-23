/**
 * Auditar SST | Acesso individual no Painel Gerencial.
 * Este módulo reutiliza as abas Usuarios/Sessoes e os snapshots PainelDados.
 * Nunca entrega a chave da Central, token do link, nem dados brutos ao navegador.
 */
const CLIENT_PORTAL_EVIDENCE_SHEET = 'EvidenciasClientes';
const CLIENT_PORTAL_PERMISSION_KEYS = [
  'indicadores', 'naoConformidades', 'acoesCorretivas', 'relatorios', 'enviarEvidencia'
];

function clientPortalPermissions_(value) {
  const input = value && typeof value === 'object' ? value : {};
  const result = {};
  CLIENT_PORTAL_PERMISSION_KEYS.forEach(function(key) {
    result[key] = input[key] === true;
  });
  return result;
}

function clientPortalDefaultPermissions_() {
  return {indicadores:true, naoConformidades:true, acoesCorretivas:true,
    relatorios:true, enviarEvidencia:false};
}

function clientPortalLogin(email, password) {
  const normalized = normalizeAuthEmail_(email);
  const credential = String(password || '');
  const cache = CacheService.getScriptCache();
  const digest = authHex_(Utilities.computeDigest(
    Utilities.DigestAlgorithm.SHA_256, normalized, Utilities.Charset.UTF_8));
  const attemptKey = 'cp_login_' + digest;
  const attempts = Number(cache.get(attemptKey) || 0);
  if (attempts >= 5) return {ok:false, message:'Acesso temporariamente bloqueado. Tente novamente mais tarde.'};
  try {
    const user = readAuthUsers_().find(function(item) {return item.email === normalized;});
    if (!user || !user.active || (user.role !== 'cliente' && user.role !== 'admin' && user.role !== 'tecnico') ||
        !credential || authPasswordHash_(credential, user.passwordSalt) !== user.passwordHash ||
        (user.role === 'cliente' && (user.allCompanies || user.companyIds.length !== 1))) {
      cache.put(attemptKey, String(attempts + 1), 900);
      return {ok:false, message:'E-mail ou senha inválidos.'};
    }
    cache.remove(attemptKey);
    const session = authCreateSession_(user, {
      deviceId:'client-portal-' + Utilities.getUuid(),
      platform:'client_portal'
    });
    const active = authUserFromToken_(session.token, false);
    if (!active || !active.sessionRowNumber) throw new Error('Sessão não criada.');
    const expires = new Date(Date.now() + 12 * 60 * 60 * 1000).toISOString();
    getSheet_(AUTH_SESSIONS_SHEET).getRange(active.sessionRowNumber, 7).setValue(expires);
    auditAuthEvent_(user, 'client_portal_login', 'session', '', '',
      '', 'client_portal', {});
    return {ok:true, token:session.token, expiresAt:expires,
      user:{name:user.name, role:user.role}};
  } catch (err) {
    console.error('Falha no login do portal: ' + String(err));
    return {ok:false, message:'Não foi possível entrar no momento.'};
  }
}

function clientPortalAuthorizedUser_(token) {
  const user = authUserFromToken_(String(token || '').trim(), false);
  if (!user || !user.active || user.sessionPlatform !== 'client_portal') return null;
  if (user.role === 'cliente' && (user.allCompanies || user.companyIds.length !== 1)) return null;
  if (['cliente','admin','tecnico'].indexOf(user.role) < 0) return null;
  return user;
}

function clientPortalLogout(token) {
  const user = clientPortalAuthorizedUser_(token);
  if (!user) return {ok:true};
  return authLogout_({authToken:token});
}

function clientPortalFindSnapshot_(companyId) {
  const id = String(companyId || '').trim();
  if (!id) return null;
  const sheet = getSheet_(PANEL_SHEET);
  if (sheet.getLastRow() < 2) return null;
  const rows = sheet.getRange(2, 1, sheet.getLastRow() - 1, 6).getValues();
  let selected = null;
  rows.forEach(function(row) {
    if (String(row[1] || '') !== id ||
        !(row[3] === true || String(row[3]).toLowerCase() === 'true')) return;
    let payload;
    try {payload = JSON.parse(String(row[5] || '{}'));} catch (_) {return;}
    if (String((payload.company || {}).id || '') !== id ||
        payload.enabled === false) return;
    if (!selected || String(row[4]) > selected.updatedAt) {
      selected = {updatedAt:String(row[4] || ''), payload:payload};
    }
  });
  return selected;
}

function clientPortalRow_(item) {
  const obj = item && typeof item === 'object' ? item : {};
  const safeText = function(key, max) {
    return String(obj[key] == null ? '' : obj[key]).slice(0, max || 400);
  };
  return {
    id:safeText('id',120) || safeText('code',120) || safeText('ncCode',120),
    title:safeText('title',240) || safeText('code',120) ||
      safeText('reportNumber',120) || safeText('ncCode',120),
    description:safeText('description',1800) || safeText('problem',1800),
    sector:safeText('sector',200) || safeText('area',200),
    status:safeText('status',100),
    priority:safeText('priority',80) || safeText('classification',80),
    date:safeText('date',60),
    dueDate:safeText('dueDate',60) || safeText('nextDueDate',60),
    responsible:safeText('responsible',180),
    recommendation:safeText('recommendation',1200),
    action:safeText('action',1200) || safeText('correctiveAction',1200)
  };
}

function clientPortalRows_(payload, alternatives) {
  for (let i = 0; i < alternatives.length; i++) {
    const rows = payload[alternatives[i]];
    if (Array.isArray(rows)) return rows.slice(0, 250).map(clientPortalRow_);
  }
  return [];
}

function clientPortalSummary_(payload) {
  const raw = payload.summary && typeof payload.summary === 'object' ? payload.summary : {};
  const keys = ['total','conformity','inspections','openNcs','overdueNcs',
    'resolvedNcs','pendingActions','overdueActions','critical','trainingExpired'];
  const safe = {};
  keys.forEach(function(key) {
    const n = Number(raw[key]);
    if (raw[key] != null && Number.isFinite(n)) safe[key] = Math.max(0, Math.min(n, 1000000));
  });
  if (safe.openNcs == null) safe.openNcs = ['ncPending','ncInProgress','ncAwaiting','ncOverdue']
    .reduce(function(total,key){ return total + Math.max(0,Number(raw[key])||0); },0);
  if (safe.overdueNcs == null) safe.overdueNcs = Math.max(0,Number(raw.ncOverdue)||0);
  if (safe.overdueActions == null) safe.overdueActions = Math.max(0,Number(raw.overdue)||0);
  return safe;
}

function clientPortalData(token) {
  const user = clientPortalAuthorizedUser_(token);
  if (!user) return {ok:false, code:'SESSION_INVALID', message:'Entre novamente.'};
  let companyIds = user.role === 'admin' ? [] : user.companyIds.slice();
  if (user.role === 'admin') {
    const rows = getSheet_(PANEL_SHEET).getDataRange().getValues().slice(1);
    companyIds = rows.map(function(row) {return String(row[1] || '').trim();})
      .filter(function(id,index,list) {return id && list.indexOf(id) === index;});
  }
  const permissions = user.role === 'cliente'
    ? clientPortalPermissions_(user.clientPermissions)
    : clientPortalDefaultPermissions_();
  if (user.role !== 'cliente') permissions.enviarEvidencia = true;
  const companies = [];
  companyIds.forEach(function(companyId) {
    if (!companyId || (user.role !== 'admin' && !userCanAccessCompany_(user,companyId))) return;
    const record = clientPortalFindSnapshot_(companyId);
    if (!record) return;
    const payload = record.payload;
    const company = payload.company || {};
    const result = {
      id:companyId,
      name:String(company.name || 'Empresa').slice(0,160),
      updatedAt:record.updatedAt,
      permissions:permissions
    };
    if (permissions.indicadores) {
      result.summary = clientPortalSummary_(payload);
      result.trainingSummary = clientPortalSummary_({summary:payload.trainingSummary || {}});
    }
    if (permissions.naoConformidades) {
      result.nonConformities = clientPortalRows_(payload,
        ['openNonConformities','nonConformities','ncs','ncRecords','nonConformityRows']);
    }
    if (permissions.acoesCorretivas) {
      result.actions = clientPortalRows_(payload,
        ['pendingActions','actions','actionPlans','correctiveActions','actionRows']);
    }
    if (permissions.relatorios) {
      result.reports = clientPortalRows_(payload,
        ['reports','reportHistory','recentReports']);
      result.inspections = clientPortalRows_(payload,
        ['recentInspections','inspections','inspectionRows']);
    }
    companies.push(result);
  });
  auditAuthEvent_(user,'client_portal_view','panel','',companies.map(function(c){return c.id;}).join(','),
    '', 'client_portal', {companyCount:companies.length});
  return {ok:true, user:{name:user.name,role:user.role},
    companies:companies};
}

function clientPortalEvidenceSheet_() {
  const ss = ensureAuthStorage_();
  return ensureSheet_(ss, CLIENT_PORTAL_EVIDENCE_SHEET, [
    'id','company_id','nc_id','user_id','created_at','note',
    'drive_file_id','status','reviewed_at','reviewed_by'
  ]);
}

function clientPortalEvidenceFolder_() {
  const props = PropertiesService.getScriptProperties();
  const saved = String(props.getProperty('AUDITAR_CLIENT_EVIDENCE_FOLDER_ID') || '');
  if (saved) {
    try {return DriveApp.getFolderById(saved);} catch (_) {}
  }
  const folder = DriveApp.createFolder('Auditar SST - Evidencias Clientes');
  props.setProperty('AUDITAR_CLIENT_EVIDENCE_FOLDER_ID',folder.getId());
  return folder;
}

function clientPortalSubmitEvidence(token, companyId, ncId, note, image) {
  const user = clientPortalAuthorizedUser_(token);
  const cid = String(companyId || '').trim();
  const id = String(ncId || '').trim();
  if (!user) return {ok:false, code:'SESSION_INVALID', message:'Entre novamente.'};
  if (!cid || !id || id.length > 120 || !userCanAccessCompany_(user,cid)) {
    return {ok:false, code:'ACCESS_DENIED', message:'Registro não autorizado.'};
  }
  if (user.role === 'cliente' &&
      !clientPortalPermissions_(user.clientPermissions).enviarEvidencia) {
    return {ok:false, code:'ACCESS_DENIED', message:'Envio não autorizado.'};
  }
  const snapshot = clientPortalFindSnapshot_(cid);
  if (!snapshot) return {ok:false, message:'Empresa indisponível.'};
  const ncs = clientPortalRows_(snapshot.payload,
    ['nonConformities','ncs','ncRecords','nonConformityRows']);
  if (!ncs.some(function(row) {return row.id && row.id === id;})) {
    return {ok:false, code:'ACCESS_DENIED', message:'Não conformidade não publicada.'};
  }
  const observation = String(note || '').trim().slice(0,1000);
  const photo = image && typeof image === 'object' ? image : {};
  if (!observation && !photo.base64) return {ok:false, message:'Informe uma observação ou fotografia.'};
  let fileId = '';
  try {
    if (photo.base64) {
      const mime = String(photo.mimeType || '').toLowerCase();
      if (['image/jpeg','image/png','image/webp'].indexOf(mime) < 0 ||
          String(photo.base64).length > 2800000 ||
          !/^[A-Za-z0-9+/]+={0,2}$/.test(String(photo.base64))) {
        return {ok:false, message:'Fotografia inválida ou maior que 2 MB.'};
      }
      const bytes = Utilities.base64Decode(String(photo.base64));
      if (bytes.length > 2000000 || bytes.length === 0) {
        return {ok:false, message:'Fotografia maior que 2 MB.'};
      }
      const blob = Utilities.newBlob(bytes,mime,'evidencia-'+Utilities.getUuid());
      fileId = clientPortalEvidenceFolder_().createFile(blob).getId();
    }
    const evidenceId = Utilities.getUuid();
    clientPortalEvidenceSheet_().appendRow([
      evidenceId,cid,id,user.id,new Date().toISOString(),observation,
      fileId,'PENDENTE_VALIDACAO','',''
    ]);
    auditAuthEvent_(user,'client_portal_submit_evidence','evidence',evidenceId,cid,
      '', 'client_portal',{ncId:id,hasPhoto:!!fileId});
    return {ok:true,id:evidenceId,status:'PENDENTE_VALIDACAO',
      message:'Evidência enviada para análise da Auditar. A NC não foi encerrada.'};
  } catch (err) {
    console.error('Falha ao receber evidência: '+String(err));
    return {ok:false,message:'Não foi possível salvar a evidência.'};
  }
}

function clientPortalEvidenceQueue(token, companyId) {
  const user = clientPortalAuthorizedUser_(token);
  const cid = String(companyId || '').trim();
  if (!user || user.role === 'cliente' || !cid || !userCanAccessCompany_(user,cid)) {
    return {ok:false,code:'ACCESS_DENIED',message:'Acesso negado.'};
  }
  const sheet = clientPortalEvidenceSheet_();
  const rows = sheet.getLastRow() < 2 ? [] :
    sheet.getRange(2,1,sheet.getLastRow()-1,10).getValues();
  return {ok:true, evidences:rows.filter(function(row){
    return String(row[1]) === cid;
  }).map(function(row){
    return {id:String(row[0]), companyId:String(row[1]), ncId:String(row[2]),
      submittedBy:String(row[3]), date:String(row[4]), note:String(row[5]),
      hasPhoto:!!row[6],status:String(row[7])};
  })};
}

function clientPortalReviewEvidence(token, evidenceId, decision) {
  const user = clientPortalAuthorizedUser_(token);
  if (!user || user.role === 'cliente') {
    return {ok:false,code:'ACCESS_DENIED',message:'Acesso negado.'};
  }
  if (['VALIDADA','REJEITADA'].indexOf(String(decision || '')) < 0) {
    return {ok:false,message:'Decisão inválida.'};
  }
  const sheet = clientPortalEvidenceSheet_();
  if (sheet.getLastRow() < 2) return {ok:false,message:'Evidência não encontrada.'};
  const rows = sheet.getRange(2,1,sheet.getLastRow()-1,10).getValues();
  for (let i=0;i<rows.length;i++) {
    const row=rows[i];
    if (String(row[0]) !== String(evidenceId || '')) continue;
    const companyId=String(row[1]);
    if (!companyId || !userCanAccessCompany_(user,companyId)) {
      return {ok:false,code:'ACCESS_DENIED',message:'Acesso negado.'};
    }
    if (String(row[7]) !== 'PENDENTE_VALIDACAO') {
      return {ok:false,message:'Evidência já analisada.'};
    }
    sheet.getRange(i+2,8,1,3).setValues([[decision,new Date().toISOString(),user.id]]);
    auditAuthEvent_(user,'client_portal_review_evidence','evidence',String(evidenceId),
      companyId,'','client_portal',{decision:decision});
    return {ok:true,message:'Evidência analisada. A situação da NC permanece sob controle do técnico.'};
  }
  return {ok:false,message:'Evidência não encontrada.'};
}

/** Fotografia privada, acessível somente ao técnico autorizado na mesma empresa. */
function clientPortalEvidencePhoto(token, evidenceId) {
  const user = clientPortalAuthorizedUser_(token);
  if (!user || user.role === 'cliente') {
    return {ok:false,code:'ACCESS_DENIED',message:'Acesso negado.'};
  }
  const sheet = clientPortalEvidenceSheet_();
  if (sheet.getLastRow() < 2) return {ok:false,message:'Fotografia não encontrada.'};
  const rows = sheet.getRange(2,1,sheet.getLastRow()-1,10).getValues();
  for (let i=0;i<rows.length;i++) {
    const row=rows[i];
    if (String(row[0]) !== String(evidenceId || '')) continue;
    const companyId = String(row[1] || '');
    if (!companyId || !userCanAccessCompany_(user,companyId)) {
      return {ok:false,code:'ACCESS_DENIED',message:'Acesso negado.'};
    }
    const fileId = String(row[6] || '');
    if (!fileId) return {ok:false,message:'Esta evidência não possui fotografia.'};
    try {
      const blob = DriveApp.getFileById(fileId).getBlob();
      const mime = String(blob.getContentType() || '').toLowerCase();
      const bytes = blob.getBytes();
      if (['image/jpeg','image/png','image/webp'].indexOf(mime) < 0 ||
          bytes.length < 1 || bytes.length > 2000000) {
        return {ok:false,message:'Arquivo inválido.'};
      }
      auditAuthEvent_(user,'client_portal_view_evidence','evidence',String(evidenceId),
        companyId,'','client_portal',{});
      return {ok:true,mimeType:mime,base64:Utilities.base64Encode(bytes)};
    } catch (_) {
      return {ok:false,message:'Fotografia indisponível.'};
    }
  }
  return {ok:false,message:'Fotografia não encontrada.'};
}

/**
 * Link simples: continua como compartilhamento somente leitura, sem credenciais
 * embutidas no JSON do navegador. Não confundir o link com login individual.
 */
function clientPortalSharePayload_(payload) {
  const clean = publicPanelPayload_(payload);
  [
    'accessToken','syncKey','authToken','sessionToken','notifications',
    'medicalExams','medicalAlerts','workforceDetails','apiKey','credentials'
  ].forEach(function(key) {delete clean[key];});
  if (clean.company && typeof clean.company === 'object') {
    ['email','phone','contactEmail','contactPhone','medicalAlertsEnabled']
      .forEach(function(key) {delete clean.company[key];});
  }
  return clean;
}

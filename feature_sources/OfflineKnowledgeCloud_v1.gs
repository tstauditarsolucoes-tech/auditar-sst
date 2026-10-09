/**
 * AUDITAR SST - Modelos técnicos compartilhados V1.
 * Rota isolada. Não altera device_sync, fotos, empresas ou documentos.
 * Disponível apenas a usuários internos autenticados da Auditar.
 */
function offlineKnowledgeSyncV1_(request) {
  const auth = authorizeMultiUserToken_(request);
  if (!auth || auth.ok !== true) return auth || {ok:false, code:'AUTH_REQUIRED'};
  const user = auth.user;
  if (!user || user.active === false || String(user.role).toLowerCase() === 'cliente')
    return {ok:false, code:'FORBIDDEN', message:'Acesso restrito à equipe Auditar.'};

  const changes = request.changes || [];
  if (!Array.isArray(changes) || changes.length > 20)
    return {ok:false, code:'BAD_BATCH', message:'Lote de modelos inválido.'};
  const cursor = Number(request.cursor || 0);
  if (!Number.isSafeInteger(cursor) || cursor < 0 || cursor > 10000)
    return {ok:false, code:'BAD_CURSOR'};
  const limit = Math.min(80, Math.max(1, Number(request.limit) || 80));
  const normalized = changes.map(offlineKnowledgeValidateV1_);
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const ss = ensureAuthStorage_();
    const sheetName = 'AUDITAR_OFFLINE_KNOWLEDGE_V1';
    let sheet = ss.getSheetByName(sheetName);
    if (!sheet) {
      sheet = ss.insertSheet(sheetName);
      sheet.appendRow(['model_id','rule_id','title','description','risk','consequence',
        'recommendation','priority','revision','updated_at','updated_by']);
    }
    const columns = 11;
    const rows = sheet.getLastRow() > 1
      ? sheet.getRange(2,1,sheet.getLastRow()-1,columns).getValues() : [];
    const byId = Object.create(null);
    rows.forEach((row,i) => {
      const id = String(row[0] || '');
      if (id) {
        if (byId[id] !== undefined) throw new Error('Modelo duplicado na Central.');
        byId[id] = i;
      }
    });
    const accepted = [], conflicts = [];
    normalized.forEach(model => {
      const at = byId[model.id];
      const previous = at === undefined ? null : rows[at];
      const revision = previous ? Number(previous[8]) : 0;
      if (model.baseVersion !== revision) {
        conflicts.push({id:model.id,version:revision});
        return;
      }
      const next = revision + 1;
      const row = [model.id,model.ruleId,model.title,model.description,model.risk,
        model.possibleConsequence,model.recommendation,model.priority,next,
        new Date().toISOString(),String(user.id || '')];
      if (at === undefined) {
        byId[model.id] = rows.length;
        rows.push(row);
      } else {
        rows[at] = row;
      }
      accepted.push({id:model.id,version:next});
    });
    if (accepted.length && rows.length)
      sheet.getRange(2,1,rows.length,columns).setValues(rows);
    // Latest first; pagination is based on a snapshot within this request.
    const visible = rows.filter(r => String(r[0] || '') !== '')
      .sort((a,b)=>String(b[9]).localeCompare(String(a[9])));
    const items = visible.slice(cursor,cursor+limit).map(r => ({
      id:String(r[0]), ruleId:String(r[1]), title:String(r[2]),
      description:String(r[3]), risk:String(r[4]),
      possibleConsequence:String(r[5]), recommendation:String(r[6]),
      priority:String(r[7]), version:Number(r[8] || 0), source:'manual_cloud_approved'
    }));
    return {ok:true,accepted:accepted,conflicts:conflicts,items:items,
      nextCursor:cursor+items.length < visible.length ? cursor+items.length : null,
      total:visible.length};
  } finally { lock.releaseLock(); }
}

function offlineKnowledgeValidateV1_(raw) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw))
    throw new Error('Modelo inválido.');
  function scalar(name,max) {
    const v = String(raw[name] || '').trim().replace(/\s+/g,' ');
    if (v.length > max) throw new Error('Campo técnico excede o limite: '+name);
    // Não compartilhar campos identificáveis em um modelo reutilizável.
    if (/@|(?:\bcpf\b)|(?:\bcnpj\b)|(?:\b\d{11}\b)|(?:\b\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2}\b)/i.test(v))
      throw new Error('Informação identificável não é permitida na biblioteca.');
    return v;
  }
  const id=scalar('id',190), ruleId=scalar('ruleId',80);
  if (!/^auto-[A-Za-z0-9_-]{10,180}$/.test(id) || !/^[a-z][a-z0-9-]{1,70}$/.test(ruleId))
    throw new Error('Identificador técnico inválido.');
  const title=scalar('title',110), description=scalar('description',220);
  const risk=scalar('risk',350), possibleConsequence=scalar('possibleConsequence',350);
  const recommendation=scalar('recommendation',650);
  const priority=scalar('priority',15);
  if (!title || !description || !risk || !recommendation ||
      ['Baixa','Média','Alta','Crítica'].indexOf(priority)<0)
    throw new Error('Campos técnicos obrigatórios inválidos.');
  const baseVersion=Number(raw.baseVersion || 0);
  if (!Number.isSafeInteger(baseVersion) || baseVersion < 0)
    throw new Error('Revisão inválida.');
  return {id,ruleId,title,description,risk,possibleConsequence,recommendation,
    priority,baseVersion};
}
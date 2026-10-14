/** Canal isolado de organização. Não lê/escreve a fila device_sync. */
function companyGroupsSync_(request) {
  const authorization = authorizeMultiUserToken_(request);
  if (!authorization.ok) return authorization;
  const user = authorization.user;
  if (!user || user.role === 'cliente') return {ok:false, code:'AUTH_REQUIRED', message:'Entre como usuário da Auditar.'};
  const changes = request.changes || [];
  if (!Array.isArray(changes) || changes.length > 250) throw new Error('Lote de grupos inválido.');
  const seen = Object.create(null);
  const clean = changes.map(c => {
    const id = String(c.companyId || '').trim();
    if (!id || id.length > 200 || seen[id] || !userCanAccessCompany_(user, id)) throw new Error('Empresa não autorizada ou duplicada.');
    seen[id] = true;
    const group = String(c.group || '').trim().replace(/\s+/g, ' ');
    const type = String(c.type || '');
    const alias = String(c.alias || '').trim();
    const version = c.baseVersion;
    if (group.length > 80 || group === '*' || alias.length > 120 || ['', 'Padaria', 'Obra', 'Indústria', 'Outros'].indexOf(type) < 0 || !Number.isSafeInteger(version) || version < 0) throw new Error('Dados de organização inválidos.');
    return {id:id, group:group, type:type, alias:alias, version:version};
  });
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const ss = ensureAuthStorage_();
    let sheet = ss.getSheetByName('AUDITAR_COMPANY_GROUPS_V1');
    if (!sheet) {
      sheet = ss.insertSheet('AUDITAR_COMPANY_GROUPS_V1');
      sheet.appendRow(['company_id','group_name','company_type','unit_alias','revision','updated_at','updated_by']);
    }
    const rows = sheet.getDataRange().getValues().slice(1).filter(r => r[0]);
    const byId = Object.create(null);
    rows.forEach((r, i) => { if (byId[String(r[0])] !== undefined) throw new Error('Grupo com registro duplicado; revisão ADM necessária.'); byId[String(r[0])] = i; });
    function visibleItems() {
      return rows.filter(r => userCanAccessCompany_(user, String(r[0]))).map(r => ({companyId:String(r[0]), group:String(r[1] || ''), type:String(r[2] || ''), alias:String(r[3] || ''), version:Number(r[4] || 0)}));
    }
    for (const c of clean) {
      const index = byId[c.id];
      const revision = index === undefined ? 0 : Number(rows[index][4]);
      if (revision !== c.version) return {ok:false, code:'GROUP_CONFLICT', message:'A organização foi alterada em outro aparelho. Revise antes de substituir.', items:visibleItems()};
    }
    const now = new Date().toISOString();
    clean.forEach(c => {
      const row = [c.id,c.group,c.type,c.alias,c.version+1,now,user.id];
      const index = byId[c.id];
      if (index === undefined) { byId[c.id] = rows.length; rows.push(row); } else { rows[index] = row; }
    });
    if (clean.length) sheet.getRange(2,1,rows.length,7).setValues(rows);
    return {ok:true, items:visibleItems()};
  } finally { lock.releaseLock(); }
}

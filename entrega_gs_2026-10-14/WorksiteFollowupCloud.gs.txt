/**
 * AUDITAR SST - acompanhamento compartilhado de obras V1.
 * Canal exclusivo, sem tocar nas rotas device_sync/fotos/relatorios.
 * Registros por ID da empresa/obra existente; acesso verificado em toda operação.
 */
function worksiteFollowupCloudV1_(request) {
  const auth=authorizeMultiUserToken_(request);
  if(!auth||auth.ok!==true) return auth||{ok:false,code:'AUTH_REQUIRED'};
  const user=auth.user;
  const companyId=String(request.companyId||'').trim();
  if(!user||user.active===false||String(user.role).toLowerCase()==='cliente'||
     !companyId||companyId.length>200||!userCanAccessCompany_(user,companyId))
    return {ok:false,code:'FORBIDDEN',message:'Sem permissão para esta obra.'};
  const mode=String(request.mode||'read');
  if(mode!=='read'&&mode!=='save')
    return {ok:false,code:'INVALID_MODE'};
  let payload='';
  const proposed=Number(request.baseVersion);
  if(mode==='save') {
    if(!Number.isSafeInteger(proposed)||proposed<0)
      return {ok:false,code:'BAD_VERSION'};
    payload=worksiteValidatePayloadV1_(request.record);
  }
  const lock=LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const ss=ensureAuthStorage_();
    const sheetName='AUDITAR_WORKSITE_FOLLOWUP_V1';
    let sheet=ss.getSheetByName(sheetName);
    if(!sheet) {
      sheet=ss.insertSheet(sheetName);
      sheet.appendRow(['company_id','revision','updated_at','updated_by',
        'payload_json_1','payload_json_2','payload_json_3']);
    }
    const last=sheet.getLastRow();
    const data=last>1?sheet.getRange(2,1,last-1,7).getValues():[];
    let found=-1;
    for(let i=0;i<data.length;i++) {
      if(String(data[i][0])===companyId) {
        if(found!==-1) throw new Error('Obra duplicada na Central.');
        found=i;
      }
    }
    const old=found===-1?null:data[found];
    const revision=old?Number(old[1]):0;
    if(!Number.isSafeInteger(revision)||revision<0) throw new Error('Revisão de obra inválida.');
    function state(row,version) {
      let decoded=null;
      if(row) {
        const text=String(row[4]||'')+String(row[5]||'')+String(row[6]||'');
        if(text) decoded=JSON.parse(text);
      }
      return {companyId:companyId,version:version,record:decoded,
        updatedAt:row?String(row[2]||''):'',
        updatedBy:row?String(row[3]||''):''};
    }
    if(mode==='read') return {ok:true,...state(old,revision)};
    if(proposed!==revision)
      return {ok:false,code:'WORKSITE_CONFLICT',
        message:'A obra mudou em outro aparelho. Nenhuma alteração foi substituída.',
        ...state(old,revision)};
    const parts=payload.match(/[\s\S]{1,28000}/g)||[''];
    if(parts.length>3) throw new Error('Diário grande demais para o compartilhamento.');
    const row=[companyId,revision+1,new Date().toISOString(),
      String(user.id||''),parts[0]||'',parts[1]||'',parts[2]||''];
    if(found===-1) sheet.appendRow(row);
    else sheet.getRange(found+2,1,1,7).setValues([row]);
    return {ok:true,...state(row,revision+1)};
  } finally {lock.releaseLock();}
}
function worksiteValidatePayloadV1_(raw) {
  if(!raw||typeof raw!=='object'||Array.isArray(raw))
    throw new Error('Acompanhamento inválido.');
  const phases=['Planejamento','Fundação','Estrutura','Alvenaria','Instalações',
    'Acabamento','Entrega','Outros'];
  const statuses=['Não iniciada','Em andamento','Pausada','Concluída'];
  const logTypes=['Visita','Orientação','Avanço','Pendência','Outro'];
  function text(value,max) {
    const out=String(value||'').trim();
    if(out.length>max) throw new Error('Campo extenso no acompanhamento.');
    return out;
  }
  function date(v) {
    const s=text(v,10);
    if(s&&!/^\d{4}-\d{2}-\d{2}$/.test(s))
      throw new Error('Data inválida no acompanhamento.');
    return s;
  }
  const phase=text(raw.phase,30),status=text(raw.status,30);
  if(phases.indexOf(phase)<0||statuses.indexOf(status)<0)
    throw new Error('Etapa ou situação não reconhecida.');
  const progress=Number(raw.progress);
  if(!Number.isInteger(progress)||progress<0||progress>100)
    throw new Error('Avanço inválido.');
  const incoming=raw.log||[];
  if(!Array.isArray(incoming)||incoming.length>80)
    throw new Error('Diário excedeu o limite de registros.');
  const log=incoming.map(x=>{
    if(!x||typeof x!=='object') throw new Error('Diário inválido.');
    const at=text(x.at,40),type=text(x.type,30),note=text(x.note,800);
    if(!/^\d{4}-\d{2}-\d{2}T/.test(at)||logTypes.indexOf(type)<0||!note)
      throw new Error('Registro do diário inválido.');
    return {at:at,type:type,note:note};
  });
  const value={schemaVersion:1,phase:phase,status:status,progress:progress,
    responsible:text(raw.responsible,120),nextVisit:date(raw.nextVisit),
    targetDate:date(raw.targetDate),notes:text(raw.notes,1000),log:log};
  const result=JSON.stringify(value);
  if(result.length>84000) throw new Error('Diário da obra excede o tamanho de compartilhamento.');
  return result;
}

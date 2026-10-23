/**
 * AUDITAR SST — Agenda de Técnicos V1, candidata aditiva (NÃO publicada).
 * Usa a autenticação existente. Nunca altera NC, fotos, login ou sincronização.
 * Integrar a rota agenda_tecnicos_v1 no despachante POST em HOMOLOGAÇÃO.
 */
const AGENDA_V1_SHEET = 'AgendaTecnicosV1';
const AGENDA_V1_AUDIT = 'AgendaTecnicosEventosV1';
const AGENDA_V1_COLUMNS = [
  'id','company_id','technician_id','title','description','scheduled_at',
  'due_at','status','created_by','created_at','updated_at','last_reason','request_id'
];

function agendaV1Clean_(value,limit) {
  const text=String(value===undefined||value===null?'':value).trim().slice(0,limit);
  return /^[=+@-]/.test(text)?"'"+text:text;
}
function agendaV1Date_(value) {
  const v=String(value||'').trim();
  if(!v)return '';
  const d=new Date(v);
  if(!isFinite(d.getTime()))return null;
  return d.toISOString();
}
function agendaV1Sheet_(ss) {
  const sh=ensureSheet_(ss,AGENDA_V1_SHEET,AGENDA_V1_COLUMNS);
  return sh || ss.getSheetByName(AGENDA_V1_SHEET);
}
function agendaV1History_(ss) {
  const columns=['event_id','task_id','event_at','actor_id','action',
    'from_status','to_status','note'];
  const sh=ensureSheet_(ss,AGENDA_V1_AUDIT,columns);
  return sh || ss.getSheetByName(AGENDA_V1_AUDIT);
}
function agendaV1Public_(row) {
  const keys=['id','companyId','technicianId','title','description','scheduledAt',
    'dueAt','status','createdBy','createdAt','updatedAt','lastReason'];
  const out={};
  keys.forEach((key,i)=>out[key]=i===0?String(row[i]||''):String(row[i]||''));
  return out;
}
function agendaV1Authorized_(request) {
  const token=String(request.authToken||'').trim();
  if(!token)return {error:{ok:false,code:'AUTH_REQUIRED',message:'Faça login novamente.'}};
  const actor=authUserFromToken_(token,true);
  if(!actor||actor.active!==true||
      (actor.role!=='admin'&&actor.role!=='tecnico'))
    return {error:{ok:false,code:'ACCESS_DENIED',message:'Sem permissão para agenda.'}};
  return {actor:actor};
}
function agendaTecnicosV1_(request) {
  request=request||{};
  const auth=agendaV1Authorized_(request);
  if(auth.error)return auth.error;
  const actor=auth.actor,kind=String(request.operation||'list').trim();
  const ss=ensureAuthStorage_(),sheet=agendaV1Sheet_(ss);
  const n=sheet.getLastRow();
  const rows=n>1?sheet.getRange(2,1,n-1,AGENDA_V1_COLUMNS.length).getValues():[];
  if(kind==='list') {
    const company=String(request.companyId||'').trim();
    const result=rows.filter(r=>
      (actor.role==='admin'||String(r[2])===actor.id) &&
      (!company||String(r[1])===company) &&
      userCanAccessCompany_(actor,String(r[1]||'')));
    result.sort((a,b)=>String(a[5]).localeCompare(String(b[5])));
    return {ok:true,tasks:result.slice(0,300).map(agendaV1Public_),
      truncated:result.length>300,generatedAt:new Date().toISOString()};
  }
  if(kind!=='create'&&kind!=='status')
    return {ok:false,code:'BAD_ACTION',message:'Operação não autorizada.'};
  const lock=LockService.getScriptLock();
  if(!lock.tryLock(25000))return {ok:false,code:'BUSY',message:'Agenda ocupada; tente novamente.'};
  try {
    const nr=sheet.getLastRow();
    const current=nr>1?sheet.getRange(2,1,nr-1,AGENDA_V1_COLUMNS.length).getValues():[];
    if(kind==='create') {
      if(actor.role!=='admin')return {ok:false,code:'ACCESS_DENIED'};
      const companyId=agendaV1Clean_(request.companyId,130);
      const techId=agendaV1Clean_(request.technicianId,130);
      const title=agendaV1Clean_(request.title,140);
      const description=agendaV1Clean_(request.description,1800);
      const due=agendaV1Date_(request.dueAt);
      const when=agendaV1Date_(request.scheduledAt);
      const requestId=agendaV1Clean_(request.requestId,120);
      if(!companyId||!techId||title.length<4||!when||due===null||
        (due&&Date.parse(due)<Date.parse(when)))
        return {ok:false,code:'INVALID_INPUT',message:'Preencha empresa, técnico, serviço e data corretamente.'};
      if(!userCanAccessCompany_(actor,companyId))
        return {ok:false,code:'ACCESS_DENIED'};
      const tech=readAuthUsers_().find(u=>u.id===techId&&u.active===true&&u.role==='tecnico');
      if(!tech||!userCanAccessCompany_(tech,companyId))
        return {ok:false,code:'INVALID_TECHNICIAN',
          message:'Técnico sem autorização para esta empresa.'};
      if(!requestId)return {ok:false,code:'REQUEST_ID_REQUIRED'};
      const duplicate=current.find(r=>String(r[12])===requestId&&String(r[8])===actor.id);
      if(duplicate)return {ok:true,task:agendaV1Public_(duplicate),idempotent:true};
      const now=new Date().toISOString();
      const row=[Utilities.getUuid(),companyId,techId,title,description,when,due,
        'planned',actor.id,now,now,'',requestId];
      sheet.appendRow(row);
      agendaV1History_(ss).appendRow([Utilities.getUuid(),row[0],now,actor.id,
        'create','','planned','']);
      return {ok:true,task:agendaV1Public_(row)};
    }
    const id=agendaV1Clean_(request.taskId,130),newStatus=String(request.status||'');
    const idx=current.findIndex(r=>String(r[0])===id);
    if(idx<0)return {ok:false,code:'NOT_FOUND'};
    const row=current[idx],companyId=String(row[1]||''),techId=String(row[2]||'');
    if(!userCanAccessCompany_(actor,companyId)||
      (actor.role!=='admin'&&techId!==actor.id))
      return {ok:false,code:'ACCESS_DENIED'};
    const transitions={
      planned:['in_progress','blocked','done','cancelled'],
      in_progress:['blocked','done','cancelled'],
      blocked:['in_progress','done','cancelled'],
      done:[],cancelled:[]
    };
    const before=String(row[7]||'planned');
    if(!(transitions[before]||[]).includes(newStatus)||
      (newStatus==='cancelled'&&actor.role!=='admin'))
      return {ok:false,code:'INVALID_TRANSITION'};
    const reason=agendaV1Clean_(request.reason,500);
    if((newStatus==='blocked'||newStatus==='done')&&reason.length<5)
      return {ok:false,code:'REASON_REQUIRED',
        message:'Informe o motivo ou o resumo do serviço (mínimo 5 caracteres).'};
    const now=new Date().toISOString();
    row[7]=newStatus;row[10]=now;row[11]=reason;
    sheet.getRange(idx+2,1,1,AGENDA_V1_COLUMNS.length).setValues([row]);
    agendaV1History_(ss).appendRow([Utilities.getUuid(),id,now,actor.id,
      'status',before,newStatus,reason]);
    return {ok:true,task:agendaV1Public_(row)};
  }finally{lock.releaseLock();}
}

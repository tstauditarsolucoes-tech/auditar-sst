/**
 * Agenda mínima de vistorias CIPA por membro/mandato.
 * Sem notificações push e sem marcar vistoria concluída automaticamente.
 * Somente ADM autenticado pode criar/cancelar. Histórico append-only.
 */
const CIPA_MEM_INSPECT_SCHEDULE='CipaPortalAgendaVistoriasV1';
const CIPA_MEM_INSPECT_HEADERS=[
  'schedule_id','created_at','company_id','mandate_id','member_id',
  'sector','due_date','note','active','admin_id','request_id'
];
const CIPA_MEM_INSPECT_SECTORS=[
  'Panificação','Cerâmica','Construção civil','Laticínios',
  'Logística e depósitos','Limpeza urbana','Comércio e escritórios',
  'Organização e circulação','Máquinas e equipamentos',
  'Incêndio e emergência','Ambiente e proteção'
];
function cipaMemV1ScheduledRows_(){
  var sheet=cipaMemV1Sheet_(CIPA_MEM_INSPECT_SCHEDULE,CIPA_MEM_INSPECT_HEADERS);
  var last=sheet.getLastRow();
  if(last<2)return [];
  if(last>25000)throw new Error('Agenda exige paginação antes da produção');
  return sheet.getRange(2,1,last-1,11).getValues();
}
function cipaMemV1ScheduleCurrent_(cid,mid,memberId){
  var byId=Object.create(null);
  cipaMemV1ScheduledRows_().forEach(function(r){
    if(String(r[2])!==cid||String(r[3])!==mid)return;
    if(memberId&&String(r[4])!==memberId)return;
    byId[String(r[0])]={id:String(r[0]),companyId:cid,mandateId:mid,
      memberId:String(r[4]),sector:String(r[5]),dueDate:String(r[6]),
      note:String(r[7]),active:r[8]===true||String(r[8])==='true'};
  });
  return Object.keys(byId).map(function(id){return byId[id];})
    .filter(function(r){return r.active;}).sort(function(a,b){
      return a.dueDate.localeCompare(b.dueDate);
    }).slice(0,100);
}
function cipaMemV1ScheduleMember_(account){
  var linked=Object.create(null);
  cipaMemV1Events_(account).forEach(function(e){
    if(e.kind==='observation'&&e.targetId)
      linked[e.targetId]=e.id;
  });
  return cipaMemV1ScheduleCurrent_(
    account.companyId,account.mandateId,account.memberId)
    .map(function(r){return {
      id:r.id,type:'scheduledInspection',
      title:'Vistoria: '+r.sector,
      description:'Setor: '+r.sector+
        (r.note?' • Orientação: '+r.note:''),
      status:linked[r.id]?'Relato enviado para análise':'Programada',
      observationId:linked[r.id]||'',dueDate:r.dueDate,
      companyId:r.companyId,mandateId:r.mandateId,
      assignedMemberId:r.memberId,visibleToAllMembers:false,
    };});
}
function cipaMemV1ScheduleValidDate_(text){
  if(!/^\d{4}-\d{2}-\d{2}$/.test(text))return false;
  var n=Date.parse(text+'T12:00:00Z');
  if(!Number.isFinite(n)||new Date(n).toISOString().slice(0,10)!==text)
    return false;
  var today=new Date().toISOString().slice(0,10);
  return text>=today&&n-Date.now()<=185*86400000;
}
function cipaMemV1ScheduleCreate_(request) {
  var admin=cipaMemV1Admin_(request.authToken);
  if(!admin)return {ok:false,code:'ACCESS_DENIED'};
  var cid=String(request.companyId||'').trim();
  var mid=String(request.mandateId||'').trim();
  var memberId=String(request.memberId||'').trim();
  var sector=String(request.sector||'').trim();
  var dueDate=String(request.dueDate||'').trim();
  var note=String(request.note||'').trim();
  var requestId=String(request.requestId||'');
  if(!cid||!mid||!memberId||
     CIPA_MEM_INSPECT_SECTORS.indexOf(sector)<0||
     !cipaMemV1ScheduleValidDate_(dueDate)||note.length>180||
     !/^[A-Za-z0-9_-]{16,120}$/.test(requestId)||
     /^[=+\-@]/.test(note))return {ok:false,code:'INVALID_INPUT'};
  var lock=LockService.getScriptLock();lock.waitLock(20000);
  try {
    admin=cipaMemV1Admin_(request.authToken);
    if(!admin)return {ok:false,code:'ACCESS_DENIED'};
    var records=cipaMemV1Records_(cid);
    if(!records.some(function(r){return r.table==='sst_records'&&
      r.type==='CIPA_MANDATO'&&r.id===mid&&r.status==='Ativo';}) ||
      !records.some(function(r){return r.table==='sst_records'&&
      r.type==='CIPA_MEMBRO'&&r.id===memberId&&r.status==='Ativo'&&
      r.payload.mandateId===mid}))
      return {ok:false,code:'MEMBERSHIP_INVALID'};
    var rows=cipaMemV1ScheduledRows_();
    var existing=rows.find(function(r){return String(r[10])===requestId;});
    if(existing) {
      return String(existing[2])===cid&&String(existing[3])===mid&&
        String(existing[4])===memberId&&String(existing[5])===sector&&
        String(existing[6])===dueDate&&String(existing[7])===note
          ?{ok:true,duplicate:true,id:String(existing[0])}:
            {ok:false,code:'ID_REUSED'};
    }
    var id='cipa-inspection-'+Utilities.getUuid();
    cipaMemV1Sheet_(CIPA_MEM_INSPECT_SCHEDULE,CIPA_MEM_INSPECT_HEADERS)
      .appendRow([id,new Date().toISOString(),cid,mid,memberId,
        sector,dueDate,note,true,String(admin.id||''),requestId]);
    auditAuthEvent_(admin,'cipa_schedule_create','CIPA_MANDATO',mid,
      cid,'','cipa_member',{memberId:memberId,id:id});
    return {ok:true,id:id};
  }finally{lock.releaseLock();}
}
function cipaMemV1ScheduleCancel_(request) {
  var admin=cipaMemV1Admin_(request.authToken);
  if(!admin)return {ok:false,code:'ACCESS_DENIED'};
  var cid=String(request.companyId||'').trim();
  var mid=String(request.mandateId||'').trim();
  var id=String(request.scheduleId||'').trim();
  if(!cid||!mid||!id)return {ok:false,code:'INVALID_INPUT'};
  var lock=LockService.getScriptLock();lock.waitLock(20000);
  try{
    admin=cipaMemV1Admin_(request.authToken);
    if(!admin)return {ok:false,code:'ACCESS_DENIED'};
    var item=cipaMemV1ScheduleCurrent_(cid,mid,'')
      .find(function(r){return r.id===id;});
    if(!item)return {ok:false,code:'NOT_FOUND'};
    cipaMemV1Sheet_(CIPA_MEM_INSPECT_SCHEDULE,CIPA_MEM_INSPECT_HEADERS)
      .appendRow([id,new Date().toISOString(),cid,mid,item.memberId,
        item.sector,item.dueDate,item.note,false,String(admin.id||''),'']);
    return {ok:true};
  }finally{lock.releaseLock();}
}
function cipaMemV1ScheduleAdminList_(request){
  if(!cipaMemV1Admin_(request.authToken))
    return {ok:false,code:'ACCESS_DENIED'};
  var cid=String(request.companyId||'').trim();
  var mid=String(request.mandateId||'').trim();
  if(!cid||!mid)return {ok:false,code:'INVALID_INPUT'};
  return {ok:true,items:cipaMemV1ScheduleCurrent_(cid,mid,'')};
}

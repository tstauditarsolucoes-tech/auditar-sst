/**
 * Programação de vistorias CIPA sem anexos/NC. Homologação.
 * Alterações append-only: histórico preservado, último evento prevalece.
 */
const CIPA_MEM_V1_SCHEDULES='CipaPortalVistoriasProgramadasV1';
const CIPA_MEM_V1_SCHED_HEADERS=[
  'schedule_id','created_at','company_id','mandate_id','member_id',
  'location','theme','planned_at','status','actor_id','request_id',
];
function cipaMemV1Schedules_(cid,mid) {
  var sheet=cipaMemV1Sheet_(CIPA_MEM_V1_SCHEDULES,CIPA_MEM_V1_SCHED_HEADERS);
  if(sheet.getLastRow()<2)return [];
  if(sheet.getLastRow()>20000)
    throw new Error('Programações exigem paginação antes da produção.');
  var latest=Object.create(null);
  sheet.getRange(2,1,sheet.getLastRow()-1,11).getValues().forEach(function(r){
    if(String(r[2])!==cid||String(r[3])!==mid)return;
    var id=String(r[0]||'');
    if(!id)return;
    latest[id]={id:id,companyId:cid,mandateId:mid,
      memberId:String(r[4]),location:String(r[5]),
      theme:String(r[6]),plannedAt:String(r[7]),
      status:String(r[8])};
  });
  return Object.keys(latest).map(function(k){return latest[k];});
}
function cipaMemV1SchedulesForMember_(cid,mid,memberId) {
  return cipaMemV1Schedules_(cid,mid).filter(function(s){
    return s.memberId===memberId&&s.status==='Agendada';
  }).sort(function(a,b){return a.plannedAt.localeCompare(b.plannedAt);})
    .slice(0,50)
    .map(function(s){return {
      id:s.id,type:'reminder',title:'Vistoria programada • '+s.location,
      description:'Tema: '+s.theme,
      status:'Agendada',date:s.plannedAt,
    };});
}
function cipaMemV1ScheduleCreate_(request) {
  var cid=String(request.companyId||'').trim();
  var mid=String(request.mandateId||'').trim();
  var actor=cipaMemV1Reviewer_(request.authToken,cid,mid);
  if(!actor)return {ok:false,code:'ACCESS_DENIED'};
  var memberId=String(request.memberId||'').trim();
  var location=String(request.location||'').trim();
  var theme=String(request.theme||'').trim();
  var themes=['Organização e circulação','Máquinas e equipamentos',
    'Incêndio e emergência','Ambiente e proteção'];
  var requestId=String(request.requestId||'').trim();
  var planned=Date.parse(String(request.plannedAt||''));
  if(!memberId||location.length<2||location.length>120||
     /^[=+@-]/.test(location)||themes.indexOf(theme)<0||
     !/^[A-Za-z0-9_-]{16,120}$/.test(requestId)||
     !Number.isFinite(planned)||planned<Date.now()+3600000 ||
     planned>Date.now()+366*86400000)
    return {ok:false,code:'INVALID_INPUT'};
  var records=cipaMemV1Records_(cid);
  var mandate=records.some(function(r){return r.table==='sst_records'&&
    r.type==='CIPA_MANDATO'&&r.id===mid&&r.status==='Ativo';});
  var member=records.some(function(r){return r.table==='sst_records'&&
    r.type==='CIPA_MEMBRO'&&r.id===memberId&&r.status==='Ativo'&&
    r.payload.mandateId===mid;});
  if(!mandate||!member)return {ok:false,code:'MEMBER_OR_MANDATE_INVALID'};
  var lock=LockService.getScriptLock();lock.waitLock(20000);
  try {
    actor=cipaMemV1Reviewer_(request.authToken,cid,mid);
    if(!actor)return {ok:false,code:'ACCESS_DENIED'};
    records=cipaMemV1Records_(cid);
    if(!records.some(function(r){return r.id===mid&&r.type==='CIPA_MANDATO'&&
       r.status==='Ativo';})||
       !records.some(function(r){return r.id===memberId&&
        r.type==='CIPA_MEMBRO'&&r.status==='Ativo'&&
        r.payload.mandateId===mid;}))
      return {ok:false,code:'MEMBER_OR_MANDATE_INVALID'};
    var sheet=cipaMemV1Sheet_(CIPA_MEM_V1_SCHEDULES,CIPA_MEM_V1_SCHED_HEADERS);
    if(sheet.getLastRow()>1) {
      var found=sheet.getRange(2,1,sheet.getLastRow()-1,11).getValues()
        .find(function(r){return String(r[10])===requestId;});
      if(found){
        var same=String(found[2])===cid&&String(found[3])===mid&&
          String(found[4])===memberId&&String(found[5])===location&&
          String(found[6])===theme&&String(found[7])===new Date(planned).toISOString();
        return same?{ok:true,duplicate:true,id:String(found[0])}:
          {ok:false,code:'ID_REUSED'};
      }
    }
    var id='cipa-schedule-'+Utilities.getUuid();
    sheet.appendRow([id,new Date().toISOString(),cid,mid,memberId,
      location,theme,new Date(planned).toISOString(),'Agendada',
      String(actor.id),requestId]);
    auditAuthEvent_(actor,'cipa_member_schedule','CIPA_MANDATO',mid,
      cid,'','cipa_member',{scheduleId:id,memberId:memberId});
    return {ok:true,id:id};
  }finally{lock.releaseLock();}
}
function cipaMemV1ScheduleCancel_(request) {
  var cid=String(request.companyId||'').trim();
  var mid=String(request.mandateId||'').trim();
  var actor=cipaMemV1Reviewer_(request.authToken,cid,mid);
  if(!actor)return {ok:false,code:'ACCESS_DENIED'};
  var id=String(request.scheduleId||'').trim();
  var lock=LockService.getScriptLock();lock.waitLock(20000);
  try{
    actor=cipaMemV1Reviewer_(request.authToken,cid,mid);
    if(!actor)return {ok:false,code:'ACCESS_DENIED'};
    var record=cipaMemV1Schedules_(cid,mid).find(function(s){return s.id===id;});
    if(!record)return {ok:false,code:'NOT_FOUND'};
    if(record.status==='Cancelada')return {ok:true,alreadyCanceled:true};
    var sheet=cipaMemV1Sheet_(CIPA_MEM_V1_SCHEDULES,CIPA_MEM_V1_SCHED_HEADERS);
    sheet.appendRow([id,new Date().toISOString(),cid,mid,record.memberId,
      record.location,record.theme,record.plannedAt,'Cancelada',
      String(actor.id),'cancel-'+Utilities.getUuid()]);
    auditAuthEvent_(actor,'cipa_member_schedule_cancel','CIPA_MANDATO',mid,
      cid,'','cipa_member',{scheduleId:id});
    return {ok:true};
  }finally{lock.releaseLock();}
}
function cipaMemV1ScheduleList_(request) {
  var cid=String(request.companyId||'').trim();
  var mid=String(request.mandateId||'').trim();
  if(!cipaMemV1Reviewer_(request.authToken,cid,mid))
    return {ok:false,code:'ACCESS_DENIED'};
  return {ok:true,schedules:cipaMemV1Schedules_(cid,mid).slice(0,150)};
}

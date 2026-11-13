/**
 * Indicadores da CIPA apenas para ADM ou TST delegado ao mesmo mandato.
 * Contagens são calculadas no servidor, nunca enviam nomes nem fotos.
 * Sem publicar antes de backup, homologação e revisão de fuso horário.
 */
function cipaTstMetricsToday_(){
  try {
    if(typeof Session!=='undefined'&&Session.getScriptTimeZone){
      return Utilities.formatDate(new Date(),Session.getScriptTimeZone(),
        'yyyy-MM-dd');
    }
  }catch(_){}
  return new Date().toISOString().slice(0,10);
}
function cipaTstMetrics_(request){
  var cid=String(request.companyId||'').trim();
  var mid=String(request.mandateId||'').trim();
  if(!cid||!mid)return {ok:false,code:'INVALID_INPUT'};
  var user=cipaMemV1Admin_(request.authToken)||
    cipaTstReviewAllowed_(request.authToken,cid,mid);
  if(!user)return {ok:false,code:'ACCESS_DENIED'};
  // Escopo obrigatório também para o administrador.
  var records=cipaMemV1Records_(cid);
  var activeMandate=records.some(function(r){
    return r.table==='sst_records'&&r.type==='CIPA_MANDATO'&&
      r.id===mid&&r.status==='Ativo';
  });
  if(!activeMandate)return {ok:false,code:'MANDATE_INVALID'};
  var members=Object.create(null),activeCount=0;
  records.forEach(function(r){
    if(r.table==='sst_records'&&r.type==='CIPA_MEMBRO'&&
       r.status==='Ativo'&&String(r.payload.mandateId||'')===mid){
      if(!members[r.id])activeCount++;
      members[r.id]=true;
    }
  });
  // Agenda append-only: última linha por id, inclusive cancelamentos.
  var scheduleMap=Object.create(null);
  cipaMemV1ScheduledRows_().forEach(function(r){
    if(String(r[2])!==cid||String(r[3])!==mid)return;
    var id=String(r[0]||'');
    if(!id)return;
    scheduleMap[id]={
      id:id,memberId:String(r[4]||''),
      dueDate:String(r[6]||'').slice(0,10),
      active:r[8]===true||String(r[8])==='true'
    };
  });
  var schedules=Object.keys(scheduleMap).map(function(id){
    return scheduleMap[id];
  }).filter(function(s){return s.active&&members[s.memberId];});

  var sheet=cipaMemV1Sheet_(CIPA_MEM_V1_EVENTS,
    ['request_id','created_at','account_id','company_id','mandate_id',
      'member_id','kind','target_id','location','detail']);
  if(sheet.getLastRow()>25000)
    throw new Error('Métricas da CIPA exigem paginação.');
  var rows=sheet.getLastRow()<2?[]:
    sheet.getRange(2,1,sheet.getLastRow()-1,10).getValues();
  var obs=Object.create(null),participants=Object.create(null);
  var linkedSchedules=Object.create(null);
  rows.forEach(function(r){
    if(String(r[3])!==cid||String(r[4])!==mid||
       String(r[6])!=='observation')return;
    var member=String(r[5]||''),id=String(r[0]||'');
    if(!members[member]||!id||obs[id])return;
    participants[member]=true;
    obs[id]=true;
    var target=String(r[7]||'');
    if(target&&scheduleMap[target]&&scheduleMap[target].memberId===member)
      linkedSchedules[target]=true;
  });
  var observationIds=Object.keys(obs);
  var reviews=cipaMemV1Reviews_(cid,mid,'',observationIds);
  var awaiting=0,replied=0;
  observationIds.forEach(function(id){
    if(reviews[id]&&reviews[id].status==='Orientação enviada')replied++;
    else awaiting++;
  });
  var today=cipaTstMetricsToday_();
  var completed=schedules.filter(function(s){
    return !!linkedSchedules[s.id];
  }).length;
  var inspectionsLate=schedules.filter(function(s){
    return !linkedSchedules[s.id]&&
      /^\d{4}-\d{2}-\d{2}$/.test(s.dueDate)&&s.dueDate<today;
  }).length;
  var scheduledMeeting=0,recordedMeeting=0,overdueActions=0;
  records.forEach(function(r){
    if(r.table!=='sst_records'||String(r.payload.mandateId||'')!==mid)
      return;
    if(r.type==='CIPA_REUNIAO'){
      if(r.status==='Agendada')scheduledMeeting++;
      if(r.status==='Realizada'||r.status==='Concluída')recordedMeeting++;
    }
    if(r.type==='CIPA_ACAO'&&r.status!=='Resolvida'&&
       r.status!=='Concluída'&&/^\d{4}-\d{2}-\d{2}/.test(r.dueDate)&&
       String(r.dueDate).slice(0,10)<today)overdueActions++;
  });
  return {ok:true,scope:{companyId:cid,mandateId:mid},
    calculatedAt:new Date().toISOString(),
    metrics:{
      membersActive:activeCount,
      membersParticipating:Object.keys(participants).length,
      inspectionsScheduled:schedules.length,
      inspectionsSubmitted:completed,
      inspectionsOverdue:inspectionsLate,
      meetingsScheduled:scheduledMeeting,
      meetingsRecorded:recordedMeeting,
      correctiveActionsOverdue:overdueActions,
      observationsPendingReview:awaiting,
      observationsReplied:replied
    }};
}

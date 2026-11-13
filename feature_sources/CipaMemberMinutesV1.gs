/**
 * Minutas CIPA (homologação). Registro para conferência pelo TST/ADM.
 * Não substitui ata assinada, convocação, reunião ou livro oficial.
 * O membro não pode atestar presença nem emitir documento final.
 */
const CIPA_MINUTES_V1_SHEET='CipaMinutasReunioesV1';
const CIPA_MINUTES_V1_HEADERS=[
  'id','created_at','account_id','company_id','mandate_id','member_id',
  'meeting_id','content','status','review_note','reviewed_by','reviewed_at'
];
function cipaMinutesV1Rows_(){
  var sh=cipaMemV1Sheet_(CIPA_MINUTES_V1_SHEET,CIPA_MINUTES_V1_HEADERS);
  if(sh.getLastRow()>25000)throw new Error('Minutas exigem paginação.');
  return sh.getLastRow()<2?[]:
    sh.getRange(2,1,sh.getLastRow()-1,12).getValues();
}
function cipaMinutesV1Dto_(r){
  return {id:String(r[0]),createdAt:String(r[1]),
    companyId:String(r[3]),mandateId:String(r[4]),
    memberId:String(r[5]),meetingId:String(r[6]),
    content:String(r[7]),status:String(r[8]),
    reviewNote:String(r[9]),reviewedAt:String(r[11])};
}
function cipaMinutesV1Submit_(request){
  var session=cipaMemV1Authorize_(request.sessionToken);
  if(!session)return {ok:false,code:'SESSION_INVALID'};
  var a=session.verified.account,id=String(request.requestId||''),
    meeting=String(request.meetingId||''),
    content=String(request.content||'').trim();
  if(!/^[A-Za-z0-9_-]{16,120}$/.test(id)||
    !/^[A-Za-z0-9_-]{3,150}$/.test(meeting)||
    content.length<130||content.length>5000||
    content.indexOf('RASCUNHO EDUCATIVO')!==0)
    return {ok:false,code:'INVALID_MINUTES_DRAFT'};
  function allowed(context) {
    return cipaMemV1RecordsAllowed_(context).meetings.some(
      function(m){return m.id===meeting;});
  }
  if(!allowed(session))return {ok:false,code:'MEETING_NOT_ALLOWED'};
  var lock=LockService.getScriptLock();lock.waitLock(20000);
  try {
    session=cipaMemV1Authorize_(request.sessionToken);
    if(!session||session.verified.account.id!==a.id||
       !allowed(session))return {ok:false,code:'SESSION_INVALID'};
    var rows=cipaMinutesV1Rows_();
    var prior=rows.find(function(r){return String(r[0])===id;});
    if(prior)return String(prior[2])===a.id&&
      String(prior[3])===a.companyId&&
      String(prior[4])===a.mandateId&&
      String(prior[5])===a.memberId&&
      String(prior[6])===meeting&&String(prior[7])===content?
        {ok:true,duplicate:true,id:id}:{ok:false,code:'ID_REUSED'};
    cipaMemV1Sheet_(CIPA_MINUTES_V1_SHEET,CIPA_MINUTES_V1_HEADERS)
      .appendRow([id,new Date().toISOString(),a.id,a.companyId,
        a.mandateId,a.memberId,meeting,content,'Recebida','','','']);
    return {ok:true,id:id,status:'Recebida'};
  }finally{lock.releaseLock();}
}
function cipaMinutesV1MemberList_(request){
  var session=cipaMemV1Authorize_(request.sessionToken);
  if(!session)return {ok:false,code:'SESSION_INVALID'};
  var a=session.verified.account;
  return {ok:true,minutes:cipaMinutesV1Rows_().filter(function(r){
    return String(r[2])===a.id&&String(r[3])===a.companyId&&
      String(r[4])===a.mandateId&&String(r[5])===a.memberId;
  }).slice(-50).reverse().map(cipaMinutesV1Dto_)};
}
function cipaMinutesV1Staff_(request){
  var cid=String(request.companyId||'').trim(),
    mid=String(request.mandateId||'').trim();
  if(!cid||!mid)return null;
  var staff=cipaMemV1Admin_(request.authToken)||
    cipaTstReviewAllowed_(request.authToken,cid,mid);
  if(!staff)return null;
  // O TST só recebe autorização para um mandato ativo.
  var valid=cipaMemV1Records_(cid).some(function(r){
    return r.table==='sst_records'&&r.id===mid&&
      r.type==='CIPA_MANDATO'&&r.status==='Ativo';});
  return valid?{staff:staff,cid:cid,mid:mid}:null;
}
function cipaMinutesV1StaffList_(request){
  var staff=cipaMinutesV1Staff_(request);
  if(!staff)return {ok:false,code:'ACCESS_DENIED'};
  return {ok:true,minutes:cipaMinutesV1Rows_().filter(function(r){
    return String(r[3])===staff.cid&&String(r[4])===staff.mid;
  }).slice(-100).reverse().map(cipaMinutesV1Dto_)};
}
function cipaMinutesV1Review_(request){
  var staff=cipaMinutesV1Staff_(request);
  if(!staff)return {ok:false,code:'ACCESS_DENIED'};
  var id=String(request.minuteId||''),
    status=String(request.status||''),
    note=String(request.note||'').trim();
  if(!/^[A-Za-z0-9_-]{16,120}$/.test(id)||
    !['Em revisão','Devolvida','Pronta para formalização'].includes(status)||
    note.length>600||(status==='Devolvida'&&note.length<8))
    return {ok:false,code:'INVALID_INPUT'};
  var lock=LockService.getScriptLock();lock.waitLock(20000);
  try {
    staff=cipaMinutesV1Staff_(request);
    if(!staff)return {ok:false,code:'ACCESS_DENIED'};
    var rows=cipaMinutesV1Rows_(),idx=rows.findIndex(function(r){
      return String(r[0])===id&&String(r[3])===staff.cid&&
        String(r[4])===staff.mid;
    });
    if(idx<0)return {ok:false,code:'NOT_FOUND'};
    var sh=cipaMemV1Sheet_(CIPA_MINUTES_V1_SHEET,CIPA_MINUTES_V1_HEADERS);
    sh.getRange(idx+2,9,1,4).setValues([[status,note,
      String(staff.staff.id||''),new Date().toISOString()]]);
    return {ok:true,status:status,
      message:'Minuta revisada; não é ata assinada ou publicada.'};
  }finally{lock.releaseLock();}
}

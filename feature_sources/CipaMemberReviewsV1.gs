/**
 * Central de devolutivas da CIPA: só administrator, histórico append-only.
 * NÃO implantar na Central real sem testes de autorização e backup.
 */
const CIPA_MEM_V1_REVIEWS='CipaPortalDevolutivasV1';
const CIPA_MEM_V1_REVIEW_HEADERS=[
  'review_id','created_at','company_id','mandate_id','member_id',
  'event_id','status','message','reviewer_id','request_id',
];

function cipaMemV1Reviews_(cid,mid,memberId,allowedIds) {
  var sheet=cipaMemV1Sheet_(CIPA_MEM_V1_REVIEWS,CIPA_MEM_V1_REVIEW_HEADERS);
  if(sheet.getLastRow()<2)return {};
  if(sheet.getLastRow()>25000)
    throw new Error('Revisões da CIPA exigem paginação antes de produção.');
  var allowed=Object.create(null);
  (allowedIds||[]).forEach(function(id){allowed[id]=true;});
  var results=Object.create(null);
  sheet.getRange(2,1,sheet.getLastRow()-1,10).getValues().forEach(function(r){
    var id=String(r[5]||'');
    if(String(r[2])!==cid||String(r[3])!==mid||
       (memberId && String(r[4])!==memberId)||!allowed[id])return;
    // A última linha válida é o último registro de revisão gravado.
    results[id]={status:String(r[6]),feedback:String(r[7]||''),
      reviewedAt:String(r[1]||'')};
  });
  return results;
}

function cipaMemV1ReviewSafeText_(value) {
  var text=String(value||'').trim();
  // Evita executar entradas de usuário como fórmulas no Google Sheets.
  if(/^[=+\-@]/.test(text))text="'"+text;
  return text;
}

function cipaMemV1AdminReviewObservation_(request,delegatedTst) {
  var admin=delegatedTst?
    cipaTstReviewAllowed_(request.authToken,
      String(request.companyId||'').trim(),
      String(request.mandateId||'').trim()):
    cipaMemV1Admin_(request.authToken);
  if(!admin)return {ok:false,code:'ACCESS_DENIED'};
  var cid=String(request.companyId||'').trim();
  var mid=String(request.mandateId||'').trim();
  var id=String(request.observationId||'').trim();
  var status=String(request.status||'').trim();
  var message=cipaMemV1ReviewSafeText_(request.message);
  var requestId=String(request.requestId||'');
  if(!cid||!mid||!id || !/^[A-Za-z0-9_-]{16,120}$/.test(requestId) ||
      ['Em análise','Orientação enviada'].indexOf(status)<0 ||
      message.length>600 ||
      (status==='Orientação enviada' && message.length<8) ||
      (message.length>0&&message.length<8)) {
    return {ok:false,code:'INVALID_INPUT'};
  }
  var lock=LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    // Nova verificação no instante da gravação, sem confiar só no botão UI.
    admin=delegatedTst?
      cipaTstReviewAllowed_(request.authToken,cid,mid):
      cipaMemV1Admin_(request.authToken);
    if(!admin)return {ok:false,code:'ACCESS_DENIED'};
    var events=cipaMemV1Sheet_(CIPA_MEM_V1_EVENTS,
      ['request_id','created_at','account_id','company_id','mandate_id',
       'member_id','kind','target_id','location','detail']);
    if(events.getLastRow()<2)return {ok:false,code:'NOT_FOUND'};
    var matches=events.getRange(2,1,events.getLastRow()-1,10).getValues()
      .filter(function(r){return String(r[0])===id &&
        String(r[3])===cid&&String(r[4])===mid&&
        String(r[6])==='observation';});
    if(matches.length!==1)return {ok:false,code:'NOT_FOUND'};
    var memberId=String(matches[0][5]||'');
    if(!memberId)return {ok:false,code:'INVALID_EVENT'};
    var revisions=cipaMemV1Sheet_(CIPA_MEM_V1_REVIEWS,CIPA_MEM_V1_REVIEW_HEADERS);
    if(revisions.getLastRow()>1){
      var existing=revisions.getRange(2,1,revisions.getLastRow()-1,10)
        .getValues().find(function(r){return String(r[9])===requestId;});
      if(existing){
        return existing[5]===id && existing[2]===cid &&
          existing[3]===mid && existing[6]===status &&
          existing[7]===message
          ?{ok:true,duplicate:true}:{ok:false,code:'ID_REUSED'};
      }
    }
    var reviewId='review-'+Utilities.getUuid();
    var date=new Date().toISOString();
    revisions.appendRow([reviewId,date,cid,mid,memberId,id,
      status,message,String(admin.id||''),requestId]);
    auditAuthEvent_(admin,delegatedTst?'cipa_tst_review':'cipa_member_review',
      'CIPA_OBSERVACAO',id,
      cid,'','cipa_member',{mandateId:mid,memberId:memberId,status:status});
    return {ok:true,reviewId:reviewId,status:status};
  }finally{lock.releaseLock();}
}

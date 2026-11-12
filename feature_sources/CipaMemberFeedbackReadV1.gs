/**
 * Confirmação de leitura de uma orientação. NÃO é concordância, fechamento
 * de não conformidade, comprovação de reparo nem assinatura de ata.
 * Escrita somente após revalidar a sessão individual e o relato próprio.
 */
const CIPA_FEEDBACK_READ_SHEET='CipaPortalLeituraOrientacoesV1';
const CIPA_FEEDBACK_READ_HEADERS=[
  'request_id','created_at','company_id','mandate_id','member_id',
  'observation_id','review_id','account_id'
];

function cipaFeedbackReadRows_() {
  var sheet=cipaMemV1Sheet_(CIPA_FEEDBACK_READ_SHEET,
    CIPA_FEEDBACK_READ_HEADERS);
  if(sheet.getLastRow()<2)return [];
  if(sheet.getLastRow()>25000)
    throw new Error('Leituras exigem paginação antes de produção.');
  return sheet.getRange(2,1,sheet.getLastRow()-1,8).getValues();
}
function cipaFeedbackReadMap_(account,allowedObservationIds,reviews) {
  var allowed=Object.create(null);
  allowedObservationIds.forEach(function(id){allowed[id]=true;});
  var read=Object.create(null);
  cipaFeedbackReadRows_().forEach(function(r){
    var observationId=String(r[5]||''),reviewId=String(r[6]||'');
    var review=reviews[observationId];
    if(!allowed[observationId]||!review||!review.reviewId||
       review.reviewId!==reviewId)return;
    if(String(r[2])!==account.companyId||
       String(r[3])!==account.mandateId||
       String(r[4])!==account.memberId||
       String(r[7])!==account.id)return;
    read[observationId]=true;
  });
  return read;
}

function cipaFeedbackAcknowledge_(request) {
  var context=cipaMemV1Authorize_(request.sessionToken);
  if(!context)return {ok:false,code:'SESSION_INVALID'};
  var observationId=String(request.observationId||'').trim();
  var reviewId=String(request.reviewId||'').trim();
  var requestId=String(request.requestId||'').trim();
  if(!/^[A-Za-z0-9_-]{16,120}$/.test(requestId)||
     !/^[A-Za-z0-9_-]{10,160}$/.test(observationId)||
     !/^[A-Za-z0-9_-]{10,160}$/.test(reviewId))
    return {ok:false,code:'INVALID_INPUT'};
  var lock=LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    // A revogação do membro pode ocorrer enquanto ele preenche a tela.
    context=cipaMemV1Authorize_(request.sessionToken);
    if(!context)return {ok:false,code:'SESSION_INVALID'};
    var account=context.verified.account;
    var own=cipaMemV1Events_(account).find(function(e){
      return e.id===observationId&&e.kind==='observation';});
    if(!own)return {ok:false,code:'ACCESS_DENIED'};
    var review=cipaMemV1Reviews_(account.companyId,account.mandateId,
      account.memberId,[observationId])[observationId];
    if(!review||review.reviewId!==reviewId||
       review.status!=='Orientação enviada'||!review.feedback)
      return {ok:false,code:'REVIEW_NOT_CURRENT'};
    var rows=cipaFeedbackReadRows_();
    var reused=rows.find(function(r){return String(r[0])===requestId;});
    if(reused){
      return String(reused[2])===account.companyId&&
        String(reused[3])===account.mandateId&&
        String(reused[4])===account.memberId&&
        String(reused[5])===observationId&&
        String(reused[6])===reviewId&&
        String(reused[7])===account.id
        ?{ok:true,duplicate:true}:{ok:false,code:'ID_REUSED'};
    }
    if(rows.some(function(r){return String(r[2])===account.companyId&&
      String(r[3])===account.mandateId&&
      String(r[4])===account.memberId&&
      String(r[5])===observationId&&
      String(r[6])===reviewId&&String(r[7])===account.id;}))
      return {ok:true,duplicate:true};
    cipaMemV1Sheet_(CIPA_FEEDBACK_READ_SHEET,
      CIPA_FEEDBACK_READ_HEADERS).appendRow([
      requestId,new Date().toISOString(),account.companyId,
      account.mandateId,account.memberId,observationId,reviewId,account.id
    ]);
    return {ok:true,read:true};
  } finally {lock.releaseLock();}
}

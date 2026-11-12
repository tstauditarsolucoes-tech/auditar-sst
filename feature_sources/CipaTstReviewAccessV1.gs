/**
 * Delegação limitada de triagem para TST (homologação).
 * Somente administrador concede/revoga; role e empresa/mandato checados
 * no servidor em CADA chamada. Nenhum acesso a contas CIPA/documentos.
 */
const CIPA_TST_REVIEW_GRANTS='CipaTstRevisoresV1';
const CIPA_TST_REVIEW_HEADERS=[
  'user_id','company_id','mandate_id','active','updated_at','granted_by'
];
function cipaTstReviewSheet_(){
  return cipaMemV1Sheet_(CIPA_TST_REVIEW_GRANTS,CIPA_TST_REVIEW_HEADERS);
}
function cipaTstReviewRole_(user) {
  // Perfis de membro e administrativos não herdam a delegação do TST.
  return !!user && user.active===true &&
    ['tecnico','tst'].indexOf(String(user.role||'').toLowerCase())>=0 &&
    String(user.id||'').length>0;
}
function cipaTstReviewAllowed_(token,cid,mid) {
  var user=authUserFromToken_(String(token||''),true);
  if(!cipaTstReviewRole_(user)||!cid||!mid)return null;
  var sheet=cipaTstReviewSheet_(),last=sheet.getLastRow();
  if(last<2)return null;
  if(last>25000)throw new Error('Permissões TST exigem paginação.');
  var rows=sheet.getRange(2,1,last-1,6).getValues();
  // Última atualização ganha: retirar e reautorizar não revive sessão antiga.
  var match=null;
  rows.forEach(function(r){
    if(String(r[0])===String(user.id)&&String(r[1])===cid&&
       String(r[2])===mid)match=r;
  });
  return match&&(match[3]===true||String(match[3])==='true')?user:null;
}
function cipaTstReviewGrant_(request){
  var admin=cipaMemV1Admin_(request.authToken);
  if(!admin)return {ok:false,code:'ACCESS_DENIED'};
  var userId=String(request.userId||'').trim();
  var cid=String(request.companyId||'').trim();
  var mid=String(request.mandateId||'').trim();
  if(!/^[\w-]{3,120}$/.test(userId)||!cid||!mid||
     !['grant','revoke'].includes(String(request.operation||'')))
    return {ok:false,code:'INVALID_INPUT'};
  // Admin escolhe escopo de mandato existente; não confiar apenas no ID.
  var records=cipaMemV1Records_(cid);
  if(!records.some(function(r){return r.table==='sst_records'&&
     r.id===mid&&r.type==='CIPA_MANDATO'&&r.status==='Ativo';}))
    return {ok:false,code:'MANDATE_INVALID'};
  var lock=LockService.getScriptLock(); lock.waitLock(20000);
  try {
    admin=cipaMemV1Admin_(request.authToken);
    if(!admin)return {ok:false,code:'ACCESS_DENIED'};
    var sheet=cipaTstReviewSheet_();
    sheet.appendRow([userId,cid,mid,request.operation==='grant',
      new Date().toISOString(),String(admin.id||'')]);
    auditAuthEvent_(admin,'cipa_tst_review_'+request.operation,
      'CIPA_MANDATO',mid,cid,'','cipa_tst',{userId:userId});
    return {ok:true};
  }finally{lock.releaseLock();}
}
function cipaTstReviewInbox_(request) {
  var cid=String(request.companyId||'').trim();
  var mid=String(request.mandateId||'').trim();
  if(!cipaTstReviewAllowed_(request.authToken,cid,mid))
    return {ok:false,code:'ACCESS_DENIED'};
  // Inbox administrativo já valida escopo; aqui não confiar em tal permissão.
  var sheet=cipaMemV1Sheet_(CIPA_MEM_V1_EVENTS,
    ['request_id','created_at','account_id','company_id','mandate_id',
      'member_id','kind','target_id','location','detail']);
  if(sheet.getLastRow()<2)return {ok:true,events:[]};
  var rows=sheet.getRange(2,1,sheet.getLastRow()-1,10).getValues()
    .filter(function(r){return String(r[3])===cid &&
      String(r[4])===mid && String(r[6])==='observation';}).slice(-100);
  var reviews=cipaMemV1Reviews_(cid,mid,'',rows.map(function(r){return String(r[0]);}));
  return {ok:true,events:rows.map(function(r){
    var id=String(r[0]),review=reviews[id];
    return {id:id,companyId:cid,mandateId:mid,
      location:String(r[8]||'').slice(0,120),
      detail:String(r[9]||'').slice(0,1200),
      status:review?review.status:'Recebido',
      feedback:review?review.feedback:'',
      createdAt:String(r[1]||'')};
  })};
}

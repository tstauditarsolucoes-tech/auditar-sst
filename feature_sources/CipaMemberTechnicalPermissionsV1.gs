/**
 * Autorização do TST por empresa e mandato (homologação, não publicar).
 * A concessão só pode ser feita por ADM e nunca cria privilégios gerais.
 */
const CIPA_MEM_V1_TECH_GRANTS='CipaPortalPermissoesTSTV1';
const CIPA_MEM_V1_TECH_HEADERS=[
  'user_id','company_id','mandate_id','active','updated_at','admin_id'
];

function cipaMemV1Technician_(token) {
  var user=authUserFromToken_(String(token||''),true);
  return user&&user.active&&
    ['tecnico','tecnico_sst','technician','tst'].indexOf(user.role)>=0
    ?user:null;
}

function cipaMemV1TstPermission_(user,cid,mid) {
  if(!user||!cid||!mid)return false;
  var sheet=cipaMemV1Sheet_(CIPA_MEM_V1_TECH_GRANTS,CIPA_MEM_V1_TECH_HEADERS);
  if(sheet.getLastRow()<2)return false;
  if(sheet.getLastRow()>25000)
    throw new Error('Volume de delegações exige consulta otimizada.');
  var latest=null;
  sheet.getRange(2,1,sheet.getLastRow()-1,6).getValues().forEach(function(row){
    if(String(row[0])!==String(user.id) ||
       String(row[1])!==cid||String(row[2])!==mid)return;
    latest=row; // última concessão ou revogação explícita
  });
  return !!latest && (latest[3]===true||String(latest[3]).toLowerCase()==='true');
}

function cipaMemV1Reviewer_(token,cid,mid) {
  if(!cid||!mid)return null;
  var admin=cipaMemV1Admin_(token);
  if(admin)return admin;
  var technician=cipaMemV1Technician_(token);
  return technician&&cipaMemV1TstPermission_(technician,cid,mid)?
    technician:null;
}

function cipaMemV1AdminSetTstPermission_(request) {
  var admin=cipaMemV1Admin_(request.authToken);
  if(!admin)return {ok:false,code:'ACCESS_DENIED'};
  var userId=String(request.userId||'').trim();
  var cid=String(request.companyId||'').trim();
  var mid=String(request.mandateId||'').trim();
  var active=request.active===true;
  if(!userId||!cid||!mid||typeof request.active!=='boolean')
    return {ok:false,code:'INVALID_INPUT'};
  // Não autorizar técnicos por nome, e-mail ou um ID declarado pelo cliente
  // sem verificar sua existência e papel no armazenamento de autenticação.
  // Integração com a API de usuários reais é obrigatória antes de habilitar.
  if(typeof cipaMemV1TrustedTechnicalUserLookup_!=='function')
    return {ok:false,code:'TECHNICIAN_LOOKUP_NOT_CONFIGURED'};
  var tech=cipaMemV1TrustedTechnicalUserLookup_(userId);
  if(!tech||!tech.active||String(tech.id)!==userId||
     ['tecnico','tecnico_sst','technician','tst'].indexOf(tech.role)<0)
    return {ok:false,code:'TECHNICIAN_NOT_VERIFIED'};
  // Confirmar que o mandato pertence à empresa informada.
  var exists=cipaMemV1Records_(cid).some(function(r){
    return r.table==='sst_records'&&r.id===mid&&
      r.type==='CIPA_MANDATO'&&r.status==='Ativo';});
  if(!exists)return {ok:false,code:'MANDATE_NOT_ACTIVE'};
  var lock=LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    admin=cipaMemV1Admin_(request.authToken);
    if(!admin)return {ok:false,code:'ACCESS_DENIED'};
    tech=cipaMemV1TrustedTechnicalUserLookup_(userId);
    if(!tech||!tech.active||String(tech.id)!==userId||
       ['tecnico','tecnico_sst','technician','tst'].indexOf(tech.role)<0)
      return {ok:false,code:'TECHNICIAN_NOT_VERIFIED'};
    var sheet=cipaMemV1Sheet_(CIPA_MEM_V1_TECH_GRANTS,CIPA_MEM_V1_TECH_HEADERS);
    sheet.appendRow([userId,cid,mid,active,new Date().toISOString(),admin.id]);
    auditAuthEvent_(admin,active?'cipa_tst_grant':'cipa_tst_revoke',
      'CIPA_MANDATO',mid,cid,'','cipa_member',{technicalUserId:userId});
    return {ok:true,active:active};
  }finally{lock.releaseLock();}
}

/** Consulta exclusiva de observações para TST com concessão vigente. */
function cipaMemV1TechnicalInbox_(request) {
  var cid=String(request.companyId||'').trim();
  var mid=String(request.mandateId||'').trim();
  var reviewer=cipaMemV1Reviewer_(request.authToken,cid,mid);
  if(!reviewer)return {ok:false,code:'ACCESS_DENIED'};
  var events=cipaMemV1Sheet_(CIPA_MEM_V1_EVENTS,
    ['request_id','created_at','account_id','company_id','mandate_id',
     'member_id','kind','target_id','location','detail']);
  if(events.getLastRow()<2)return {ok:true,events:[]};
  var rows=events.getRange(2,1,events.getLastRow()-1,10).getValues()
    .filter(function(row){return String(row[3])===cid&&
      String(row[4])===mid&&String(row[6])==='observation';})
    .slice(-120);
  var reviews=cipaMemV1Reviews_(cid,mid,'',rows.map(function(row){
    return String(row[0]);}));
  return {ok:true,events:rows.map(function(row){
    var id=String(row[0]),review=reviews[id];
    return {id:id,companyId:cid,mandateId:mid,
      memberId:String(row[5]),kind:'observation',
      createdAt:String(row[1]),location:String(row[8]).slice(0,120),
      detail:String(row[9]).slice(0,1200),
      status:review?review.status:'Recebido',
      feedback:review?review.feedback:''};
  })};
}

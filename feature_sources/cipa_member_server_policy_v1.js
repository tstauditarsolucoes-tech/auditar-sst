/* Auditar SST | pure member authorization for future Central integration.
 * This file MUST NOT be exposed directly as a public service.
 * The caller must look up the account, membership and mandate in trusted
 * server storage on EVERY request, including after role changes/revocation.
 */
(function(root) {
  'use strict';
  var allowedActions={
    view_dashboard:true,
    view_meetings:true,
    view_own_actions:true,
    view_notices:true,
    view_training:true,
    view_published_documents:true,
    acknowledge_meeting:true,
    report_own_progress:true,
    request_own_support:true,
    submit_observation:true
  };
  function isNonEmpty(value) {
    return typeof value==='string' && value.trim().length>0;
  }
  function authorized(account,session,mandate,membership) {
    if(!account||!session||!mandate||!membership)return false;
    if(account.status!=='Ativo'||account.role!=='membro_cipa'||
       session.revoked!==false ||
       !Number.isFinite(session.expiresAt) || session.expiresAt<=Date.now()||
       mandate.status!=='Ativo'||membership.status!=='Ativo')return false;
    if(!isNonEmpty(session.accountId)||session.accountId!==account.id||
       !isNonEmpty(account.id)||!isNonEmpty(account.companyId)||
       !isNonEmpty(account.mandateId)||!isNonEmpty(account.memberId))return false;
    return mandate.id===account.mandateId&&
      mandate.companyId===account.companyId&&
      membership.id===account.memberId&&
      membership.companyId===account.companyId&&
      membership.mandateId===account.mandateId&&
      isNonEmpty(membership.workerId);
  }
  function can(account,session,mandate,membership,action,record) {
    if(!authorized(account,session,mandate,membership)||
       allowedActions[action]!==true) return false;
    if(action==='submit_observation'||action==='view_dashboard')return true;
    if(!record||record.companyId!==account.companyId||
       record.mandateId!==account.mandateId)return false;
    if(action==='view_meetings'||action==='acknowledge_meeting') {
      return record.type==='CIPA_REUNIAO'&&
        (Array.isArray(record.memberIds) &&
         record.memberIds.indexOf(account.memberId)>=0)&&
        (action!=='acknowledge_meeting'||record.status==='Agendada');
    }
    if(action==='view_own_actions'||action==='report_own_progress'||
       action==='request_own_support') {
      return record.type==='CIPA_ACAO' &&
        record.assignedMemberId===account.memberId &&
        (action==='view_own_actions'||
         (record.status!=='Resolvida'&&record.status!=='Concluída'));
    }
    if(action==='view_published_documents'){
      return record.type==='CIPA_DOCUMENTO' &&
        record.publishedToMembers===true &&
        record.containsPersonalData!==true &&
        record.signedRestricted!==true;
    }
    if(action==='view_training'){
      return record.type==='CIPA_TREINAMENTO' &&
        record.workerId===membership.workerId;
    }
    if(action==='view_notices'){
      return record.type==='CIPA_AVISO' &&
        record.publishedToMembers===true;
    }
    return false;
  }
  function filter(account,session,mandate,membership,action,records) {
    if(!authorized(account,session,mandate,membership))return [];
    if(!Array.isArray(records))return [];
    return records.filter(function(r){
      return can(account,session,mandate,membership,action,r);
    });
  }
  function memberName(membership) {
    if(!membership)return '';
    var name=String(membership.name||'').trim().slice(0,140);
    var roles=['Presidente','Vice-presidente','Titular','Suplente',
      'Secretário','Membro designado'];
    var role=String(membership.cipaRole||'').trim();
    return name+(roles.indexOf(role)>=0?' — '+role+' da CIPA':'');
  }
  var api={authorized:authorized,can:can,filter:filter,
    memberName:memberName,allowedActions:Object.freeze(allowedActions)};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  root.CipaMemberServerPolicy=api;
})(typeof globalThis!=='undefined'?globalThis:this);

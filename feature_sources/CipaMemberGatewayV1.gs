/**
 * Auditar SST | Portal individual da CIPA (projeto de homologação).
 * Totalmente separado das credenciais, tabelas e sincronização do técnico.
 * NÃO habilitar em produção sem backup, revisão do GS real e testes de
 * duas empresas/mandatos/membros e de revogação.
 *
 * Requer arquivos do projeto: MultiUser.gs, Code.gs e
 * CipaMemberServerPolicy.gs, além da integração explícita do roteador.
 */
const CIPA_MEM_V1_ACCOUNTS='CipaPortalAcessosV1';
const CIPA_MEM_V1_SESSIONS='CipaPortalSessoesV1';
const CIPA_MEM_V1_EVENTS='CipaPortalEventosV1';
const CIPA_MEM_V1_ASSIGNMENTS='CipaPortalAtribuicoesV1';

function cipaMemV1Route_(request) {
  var action=String((request||{}).action||'');
  var known=['cipa_member_begin','cipa_member_verify','cipa_member_dashboard',
    'cipa_member_event','cipa_member_logout','cipa_member_admin_grant',
    'cipa_member_admin_revoke','cipa_member_admin_list','cipa_member_admin_assign',
    'cipa_member_admin_inbox',
    'cipa_member_admin_publish_notice','cipa_member_admin_withdraw_notice',
    'cipa_member_admin_publish_document','cipa_member_admin_unpublish_document',
    'cipa_member_admin_publications',
    'cipa_member_admin_review_observation',
    'cipa_tst_review_inbox','cipa_tst_review_observation','cipa_tst_review_grant',
    'cipa_schedule_create','cipa_schedule_cancel','cipa_schedule_list',
    'cipa_member_ack_feedback',
    'cipa_member_photo_upload','cipa_member_photo_list',
    'cipa_member_photo_get','cipa_tst_photo_list','cipa_tst_photo_get',
    'cipa_tst_metrics',
    'cipa_mural_create','cipa_mural_list','cipa_mural_comment',
    'cipa_mural_photo','cipa_mural_moderator_list',
    'cipa_mural_moderate','cipa_mural_moderate_comment',
    'cipa_mural_reply','cipa_mural_moderator_photo',
    'cipa_member_avatar_get','cipa_member_avatar_save',
    'cipa_member_avatar_delete','cipa_member_admin_avatar_save',
    'cipa_member_admin_avatar_delete',
    'cipa_minutes_submit','cipa_minutes_list',
    'cipa_minutes_staff_list','cipa_minutes_review'];
  if(known.indexOf(action)<0)return null;
  if(PropertiesService.getScriptProperties().getProperty('CIPA_MEMBER_V1_ENABLED')!=='true')
    return {ok:false,code:'FEATURE_DISABLED',message:'Acesso de membros ainda não habilitado.'};
  try {
    if(action==='cipa_minutes_submit')return cipaMinutesV1Submit_(request);
    if(action==='cipa_minutes_list')return cipaMinutesV1MemberList_(request);
    if(action==='cipa_minutes_staff_list')return cipaMinutesV1StaffList_(request);
    if(action==='cipa_minutes_review')return cipaMinutesV1Review_(request);
    if(action==='cipa_member_avatar_get')return cipaAvatarV1MemberGet_(request);
    if(action==='cipa_member_avatar_save')return cipaAvatarV1MemberSave_(request);
    if(action==='cipa_member_avatar_delete')return cipaAvatarV1MemberDelete_(request);
    if(action==='cipa_member_admin_avatar_save')return cipaAvatarV1AdminSave_(request);
    if(action==='cipa_member_admin_avatar_delete')return cipaAvatarV1AdminDelete_(request);
    if(action==='cipa_mural_create')return cipaMuralCreate_(request);
    if(action==='cipa_mural_list')return cipaMuralMemberList_(request);
    if(action==='cipa_mural_comment')return cipaMuralMemberComment_(request);
    if(action==='cipa_mural_photo')return cipaMuralPhoto_(request,false);
    if(action==='cipa_mural_moderator_list')return cipaMuralModeratorList_(request);
    if(action==='cipa_mural_moderate')return cipaMuralModerate_(request);
    if(action==='cipa_mural_moderate_comment')return cipaMuralModerateComment_(request);
    if(action==='cipa_mural_reply')return cipaMuralModeratorReply_(request);
    if(action==='cipa_mural_moderator_photo')return cipaMuralPhoto_(request,true);
    if(action==='cipa_member_begin')return cipaMemV1Begin_(request);
    if(action==='cipa_member_verify')return cipaMemV1Verify_(request);
    if(action==='cipa_member_dashboard')return cipaMemV1Dashboard_(request);
    if(action==='cipa_member_event')return cipaMemV1Event_(request);
    if(action==='cipa_member_photo_upload')return cipaPhotoV1Upload_(request);
    if(action==='cipa_member_photo_list')return cipaPhotoV1List_(request,false);
    if(action==='cipa_member_photo_get')return cipaPhotoV1Get_(request,false);
    if(action==='cipa_tst_photo_list')return cipaPhotoV1List_(request,true);
    if(action==='cipa_tst_photo_get')return cipaPhotoV1Get_(request,true);
    if(action==='cipa_tst_metrics')return cipaTstMetrics_(request);
    if(action==='cipa_member_ack_feedback')
      return cipaFeedbackAcknowledge_(request);
    if(action==='cipa_member_logout')return cipaMemV1Logout_(request);
    if(action==='cipa_member_admin_grant')return cipaMemV1AdminGrant_(request);
    if(action==='cipa_member_admin_revoke')return cipaMemV1AdminRevoke_(request);
    if(action==='cipa_member_admin_list')return cipaMemV1AdminList_(request);
    if(action==='cipa_member_admin_assign')return cipaMemV1AdminAssign_(request);
    if(action==='cipa_member_admin_inbox')return cipaMemV1AdminInbox_(request);
    if(action==='cipa_member_admin_review_observation')
      return cipaMemV1AdminReviewObservation_(request);
    if(action==='cipa_tst_review_inbox')return cipaTstReviewInbox_(request);
    if(action==='cipa_schedule_create')return cipaMemV1ScheduleCreate_(request);
    if(action==='cipa_schedule_cancel')return cipaMemV1ScheduleCancel_(request);
    if(action==='cipa_schedule_list')return cipaMemV1ScheduleAdminList_(request);
    if(action==='cipa_tst_review_grant')return cipaTstReviewGrant_(request);
    if(action==='cipa_tst_review_observation')
      return cipaMemV1AdminReviewObservation_(request,true);
    if(action==='cipa_member_admin_publish_notice')
      return cipaMemV1PublishNotice_(request);
    if(action==='cipa_member_admin_withdraw_notice')
      return cipaMemV1WithdrawNotice_(request);
    if(action==='cipa_member_admin_publish_document')
      return cipaMemV1PublishDocument_(request);
    if(action==='cipa_member_admin_unpublish_document')
      return cipaMemV1UnpublishDocument_(request);
    if(action==='cipa_member_admin_publications')
      return cipaMemV1AdminPublicationList_(request);
  } catch(error) {
    console.error('Portal CIPA: '+String(error));
    return {ok:false,code:'CIPA_MEMBER_ERROR',
      message:'A operação não foi concluída. Confira o acesso e tente novamente.'};
  }
  return {ok:false,code:'ACCESS_DENIED'};
}
function cipaMemV1Sheet_(name,headers) {
  var ss=ensureAuthStorage_();
  ensureSheet_(ss,name,headers);
  return ss.getSheetByName(name);
}
function cipaMemV1Accounts_() {
  var sheet=cipaMemV1Sheet_(CIPA_MEM_V1_ACCOUNTS,
    ['id','email','company_id','mandate_id','member_id','worker_id',
      'active','version','created_at','updated_at']);
  if(sheet.getLastRow()<2)return [];
  return sheet.getRange(2,1,sheet.getLastRow()-1,10).getValues().map(function(r,i){
    return {row:i+2,id:String(r[0]||''),email:String(r[1]||'').toLowerCase(),
      companyId:String(r[2]||''),mandateId:String(r[3]||''),
      memberId:String(r[4]||''),workerId:String(r[5]||''),
      active:r[6]===true||String(r[6]).toLowerCase()==='true',
      version:Number(r[7])||0,createdAt:String(r[8]||''),updatedAt:String(r[9]||'')};
  });
}
function cipaMemV1Hash_(text) {
  return authHex_(Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256,
    String(text||''),Utilities.Charset.UTF_8));
}
function cipaMemV1RandomToken_() {
  return Utilities.getUuid().replace(/-/g,'')+
    Utilities.getUuid().replace(/-/g,'')+
    Utilities.getUuid().replace(/-/g,'');
}
function cipaMemV1Email_(value) {
  var e=String(value||'').trim().toLowerCase();
  return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(e)?e:'';
}
function cipaMemV1Pepper_() {
  var pepper=PropertiesService.getScriptProperties()
    .getProperty('CIPA_MEMBER_V1_PEPPER');
  if(!pepper||pepper.length<48)throw new Error('Segredo do portal não configurado.');
  return pepper;
}
function cipaMemV1Admin_(token) {
  var user=authUserFromToken_(String(token||''),true);
  return user&&user.active&&user.role==='admin'?user:null;
}
// Somente os registros da empresa selecionada, na última versão por id.
// Não inferir empresa de nome ou de payload sem company_id e coluna de scope.
function cipaMemV1Records_(companyId) {
  if(!companyId) return [];
  var sheet=getSheet_(DEVICE_SYNC_SHEET);
  var last=sheet.getLastRow();
  if(last<2)return [];
  if(last>25000)throw new Error('Volume exige consulta otimizada antes de liberar o portal.');
  var rows=sheet.getRange(2,1,last-1,10).getValues();
  var latest={};
  rows.forEach(function(r){
    var table=String(r[0]||''),id=String(r[1]||'');
    if(['sst_records','training_controls'].indexOf(table)<0||!id||
      String(r[8]||'')!==companyId)return;
    var version=Number(r[3])||0,key=table+':'+id;
    if(latest[key]&&latest[key].version>=version)return;
    var deleted=r[2]===true||String(r[2]).toLowerCase()==='true';
    if(deleted){latest[key]={version:version,deleted:true};return;}
    var raw={};
    try {raw=JSON.parse(String(r[7]||'{}'));} catch (_) {return;}
    if(!raw||typeof raw!=='object'||
      String(raw.company_id||'')!==companyId||
      String(raw.id||'')!==id) return;
    var payload={};
    try {payload=JSON.parse(String(raw.payload_json||'{}'));}catch (_) {}
    if(!payload||typeof payload!=='object'||Array.isArray(payload))payload={};
    latest[key]={version:version,deleted:false,
      id:id,table:table,type:String(raw.type||''),
      title:String(raw.title||'').slice(0,240),
      status:String(raw.status||'').slice(0,50),
      companyId:companyId,date:String(raw.date||''),
      dueDate:String(raw.due_date||''),
      workerId:String(raw.worker_id||''),
      payload:payload};
  });
  return Object.keys(latest).map(function(k){return latest[k];})
    .filter(function(r){return !r.deleted;});
}
function cipaMemV1VerifyMember_(account) {
  if(!account||!account.active||!account.companyId||
     !account.mandateId||!account.memberId||!account.workerId)return null;
  var rows=cipaMemV1Records_(account.companyId);
  var mandate=rows.find(function(r){return r.table==='sst_records'&&
    r.type==='CIPA_MANDATO'&&r.id===account.mandateId&&r.status==='Ativo';});
  var member=rows.find(function(r){return r.table==='sst_records'&&
    r.type==='CIPA_MEMBRO'&&r.id===account.memberId&&r.status==='Ativo'&&
    r.payload.mandateId===account.mandateId&&
    r.payload.workerId===account.workerId;});
  if(!mandate||!member)return null;
  var roles=['Presidente','Vice-presidente','Titular','Suplente',
    'Secretário','Membro designado'];
  if(roles.indexOf(String(member.payload.cipaRole||''))<0)return null;
  var membership={id:member.id,name:member.title,status:member.status,
    companyId:account.companyId,mandateId:account.mandateId,
    workerId:account.workerId,cipaRole:member.payload.cipaRole};
  var linked={id:mandate.id,companyId:account.companyId,status:mandate.status};
  return {account:account,member:membership,mandate:linked,rows:rows};
}
function cipaMemV1AdminGrant_(request) {
  var admin=cipaMemV1Admin_(request.authToken);
  if(!admin)return {ok:false,code:'ACCESS_DENIED'};
  var email=cipaMemV1Email_(request.email);
  var account={id:'',companyId:String(request.companyId||'').trim(),
    mandateId:String(request.mandateId||'').trim(),
    memberId:String(request.memberId||'').trim(),
    workerId:String(request.workerId||'').trim(),active:true};
  if(!email||!cipaMemV1VerifyMember_(account))
    return {ok:false,code:'MEMBER_NOT_VERIFIED'};
  var lock=LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var current=cipaMemV1Accounts_().find(function(a){return a.email===email;});
    if(current&&current.active&&
       (current.companyId!==account.companyId||
        current.memberId!==account.memberId||
        current.mandateId!==account.mandateId)){
      return {ok:false,code:'EMAIL_ALREADY_ACTIVE',
        message:'Revogue primeiro o acesso anterior antes de mudar o vínculo.'};
    }
    var sheet=cipaMemV1Sheet_(CIPA_MEM_V1_ACCOUNTS,
      ['id','email','company_id','mandate_id','member_id','worker_id',
       'active','version','created_at','updated_at']);
    var id=current?current.id:Utilities.getUuid();
    var now=new Date().toISOString();
    if(current) {
      sheet.getRange(current.row,3,1,5).setValues([[
        account.companyId,account.mandateId,account.memberId,
        account.workerId,true]]);
      sheet.getRange(current.row,8).setValue(current.version+1);
      sheet.getRange(current.row,10).setValue(now);
    } else {
      sheet.appendRow([id,email,account.companyId,account.mandateId,
        account.memberId,account.workerId,true,1,now,now]);
    }
    auditAuthEvent_(admin,'cipa_member_grant','CIPA_MEMBRO',account.memberId,
      account.companyId,'','cipa_member',
      {accountId:id,mandateId:account.mandateId});
    return {ok:true,id:id,reused:!!current};
  } finally {lock.releaseLock();}
}
function cipaMemV1AdminList_(request) {
  var admin=cipaMemV1Admin_(request.authToken);
  if(!admin)return {ok:false,code:'ACCESS_DENIED'};
  var cid=String(request.companyId||'').trim();
  if(!cid)return {ok:false,code:'INVALID_INPUT'};
  return {ok:true,accounts:cipaMemV1Accounts_()
    .filter(function(a){return a.companyId===cid;})
    .map(function(a){return {
      id:a.id,email:a.email,active:a.active,
      companyId:a.companyId,mandateId:a.mandateId,
      memberId:a.memberId,workerId:a.workerId,
    };})};
}
function cipaMemV1AdminRevoke_(request) {
  var admin=cipaMemV1Admin_(request.authToken);
  if(!admin)return {ok:false,code:'ACCESS_DENIED'};
  var a=cipaMemV1Accounts_().find(function(x){return x.id===request.accountId;});
  if(!a)return {ok:false,code:'NOT_FOUND'};
  var sheet=cipaMemV1Sheet_(CIPA_MEM_V1_ACCOUNTS,
    ['id','email','company_id','mandate_id','member_id','worker_id',
     'active','version','created_at','updated_at']);
  sheet.getRange(a.row,7).setValue(false);
  sheet.getRange(a.row,8).setValue(a.version+1);
  sheet.getRange(a.row,10).setValue(new Date().toISOString());
  auditAuthEvent_(admin,'cipa_member_revoke','CIPA_MEMBRO',a.memberId,
    a.companyId,'','cipa_member',{accountId:a.id});
  return {ok:true};
}
function cipaMemV1Begin_(request) {
  var email=cipaMemV1Email_(request.email);
  var generic={ok:true,message:'Se o acesso estiver ativo, '
    +'você receberá um código no e-mail cadastrado.'};
  if(!email)return generic;
  var cache=CacheService.getScriptCache();
  var hash=cipaMemV1Hash_(email+'|'+cipaMemV1Pepper_());
  var throttle='cipa_begin_'+hash;
  if(cache.get(throttle))return generic;
  cache.put(throttle,'1',75);
  var account=cipaMemV1Accounts_().find(function(a){return a.email===email&&a.active;});
  if(!account||!cipaMemV1VerifyMember_(account))return generic;
  var random=cipaMemV1RandomToken_();
  var pin=String(parseInt(random.slice(0,12),16)%100000000).padStart(8,'0');
  var challengeHash=cipaMemV1Hash_(email+'|'+pin+'|'+cipaMemV1Pepper_());
  cache.put('cipa_challenge_'+hash,JSON.stringify({
    accountId:account.id,hash:challengeHash,
    expiresAt:Date.now()+600000,attempts:0}),600);
  MailApp.sendEmail(email,'Código de acesso Minha CIPA',
    'Seu código de acesso é: '+pin+'\nValidade: 10 minutos. '
    +'Não compartilhe este código com ninguém.');
  return generic;
}
function cipaMemV1Verify_(request) {
  var email=cipaMemV1Email_(request.email),pin=String(request.code||'').trim();
  var denied={ok:false,code:'INVALID_CODE',message:'Código inválido ou expirado.'};
  if(!email||!/^\d{8}$/.test(pin))return denied;
  var lock=LockService.getScriptLock();
  lock.waitLock(15000);
  try {
  var cache=CacheService.getScriptCache();
  var hash=cipaMemV1Hash_(email+'|'+cipaMemV1Pepper_());
  var key='cipa_challenge_'+hash;
  var raw=cache.get(key);
  if(!raw)return denied;
  var challenge=JSON.parse(raw);
  if(!challenge||challenge.attempts>=5||Date.now()>challenge.expiresAt)return denied;
  challenge.attempts+=1;
  cache.put(key,JSON.stringify(challenge),
    Math.max(1,Math.ceil((challenge.expiresAt-Date.now())/1000)));
  if(cipaMemV1Hash_(email+'|'+pin+'|'+cipaMemV1Pepper_())!==challenge.hash)
    return denied;
  var account=cipaMemV1Accounts_().find(function(a){
    return a.id===challenge.accountId&&a.email===email&&a.active;});
  var verified=cipaMemV1VerifyMember_(account);
  if(!verified)return denied;
  cache.remove(key);
  var token=cipaMemV1RandomToken_(),expiry=Date.now()+8*60*60*1000;
  cipaMemV1Sheet_(CIPA_MEM_V1_SESSIONS,
    ['token_hash','account_id','expires_at','revoked',
     'created_at','credential_version'])
    .appendRow([cipaMemV1Hash_(token),account.id,expiry,false,
      Date.now(),account.version]);
  return {ok:true,sessionToken:token,expiresAt:expiry,
    person:cipaMemV1Name_(verified.member),companyId:account.companyId,
    mandateId:account.mandateId};
  } finally {lock.releaseLock();}
}
function cipaMemV1Name_(member) {
  return CipaMemberServerPolicy.memberName(member);
}
function cipaMemV1Authorize_(token) {
  if(!token||String(token).length<64)return null;
  var sheet=cipaMemV1Sheet_(CIPA_MEM_V1_SESSIONS,
    ['token_hash','account_id','expires_at','revoked',
     'created_at','credential_version']);
  if(sheet.getLastRow()<2)return null;
  var hash=cipaMemV1Hash_(token);
  var rows=sheet.getRange(2,1,sheet.getLastRow()-1,6).getValues();
  var i=rows.findIndex(function(r){return String(r[0])===hash;});
  if(i<0)return null;
  var row=rows[i],account=cipaMemV1Accounts_().find(function(a){
    return a.id===String(row[1]);});
  if(!account||account.version!==Number(row[5]))return null;
  var verified=cipaMemV1VerifyMember_(account);
  if(!verified)return null;
  var session={accountId:account.id,
    expiresAt:Number(row[2]),
    revoked:row[3]===false||String(row[3]).toLowerCase()==='false'?false:true};
  return CipaMemberServerPolicy.authorized(
    {id:account.id,companyId:account.companyId,
      mandateId:account.mandateId,memberId:account.memberId,
      role:'membro_cipa',status:account.active?'Ativo':'Inativo'},
    session,verified.mandate,verified.member)
    ? {verified:verified,sessionRow:i+2,session:session}:null;
}
function cipaMemV1Assignments_(companyId,mandateId) {
  var sheet=cipaMemV1Sheet_(CIPA_MEM_V1_ASSIGNMENTS,
    ['company_id','mandate_id','action_id','member_id','updated_at']);
  if(sheet.getLastRow()<2)return {};
  var rows=sheet.getRange(2,1,sheet.getLastRow()-1,5).getValues(),map={};
  rows.forEach(function(r){
    if(String(r[0])===companyId&&String(r[1])===mandateId){
      map[String(r[2])]=String(r[3]);
    }
  });
  return map;
}
function cipaMemV1AdminAssign_(request) {
  var admin=cipaMemV1Admin_(request.authToken);
  if(!admin)return {ok:false,code:'ACCESS_DENIED'};
  var cid=String(request.companyId||''),mid=String(request.mandateId||'');
  var aid=String(request.actionId||''),memberId=String(request.memberId||'');
  if(!cid||!mid||!aid||!memberId)return {ok:false,code:'INVALID_INPUT'};
  var records=cipaMemV1Records_(cid);
  var validMandate=records.some(function(r){return r.id===mid&&
    r.type==='CIPA_MANDATO'&&r.status==='Ativo';});
  var validMember=records.some(function(r){return r.id===memberId&&
    r.type==='CIPA_MEMBRO'&&r.status==='Ativo'&&r.payload.mandateId===mid;});
  var validAction=records.some(function(r){return r.id===aid&&
    r.type==='CIPA_ACAO'&&r.status!=='Resolvida'&&r.payload.mandateId===mid;});
  if(!validMandate||!validMember||!validAction)
    return {ok:false,code:'MEMBERSHIP_OR_ACTION_INVALID'};
  cipaMemV1Sheet_(CIPA_MEM_V1_ASSIGNMENTS,
    ['company_id','mandate_id','action_id','member_id','updated_at'])
    .appendRow([cid,mid,aid,memberId,new Date().toISOString()]);
  auditAuthEvent_(admin,'cipa_member_assign','CIPA_ACAO',aid,cid,'','cipa_member',
    {mandateId:mid,memberId:memberId});
  return {ok:true};
}
function cipaMemV1RecordsAllowed_(context) {
  var v=context.verified,a=v.account,assignment=cipaMemV1Assignments_(
    a.companyId,a.mandateId);
  var meetings=[],actions=[],notices=[],documents=[],trainings=[],reminders=[];
  var publishedIds=cipaMemV1PublishedDocumentIds_(a.companyId,a.mandateId)
    .filter(function(d){return d.published;})
    .map(function(d){return d.id;});
  v.rows.forEach(function(r){
    if(r.table==='training_controls'&&r.workerId===a.workerId){
      trainings.push({id:r.id,type:'training',title:r.title||'Treinamento',
        status:r.status});return;
    }
    if(r.table!=='sst_records'||r.payload.mandateId!==a.mandateId)return;
    if(r.type==='CIPA_REUNIAO' && Array.isArray(r.payload.memberIds) &&
      r.payload.memberIds.indexOf(a.memberId)>=0){
      var safeMeeting={id:r.id,type:'meeting',title:r.title,
        description:String(r.payload.place||'').slice(0,200),
        status:r.status,date:r.date};
      meetings.push(safeMeeting);
      if(r.status==='Agendada')reminders.push({
        id:'reminder-'+r.id,type:'reminder',title:'Reunião: '+r.title,
        date:r.date,status:'Agendada'});
    }
    if(r.type==='CIPA_ACAO'&&assignment[r.id]===a.memberId){
      actions.push({id:r.id,type:'action',title:r.title,
        description:String(r.payload.description||'').slice(0,600),
        status:r.status,date:r.date,dueDate:r.dueDate});
      // Alertas no painel, não notificações push ou garantia legal de prazo.
      if(r.status!=='Resolvida'&&r.status!=='Concluída'&&r.dueDate){
        var deadline=Date.parse(r.dueDate);
        if(Number.isFinite(deadline)){
          var days=Math.ceil((deadline-Date.now())/86400000);
          if(days<=7){
            reminders.push({
              id:'deadline-'+r.id,type:'reminder',
              title:days<0?'Ação com prazo vencido: '+r.title:
                'Prazo próximo da ação: '+r.title,
              date:r.dueDate,
              status:days<0?'Prazo para conferir':'Prazo próximo',
            });
          }
        }
      }
    }
    if(r.type==='CIPA_DOCUMENTO' && publishedIds.indexOf(r.id)>=0 &&
       r.payload.containsPersonalData!==true &&
       r.payload.signedRestricted!==true) {
      documents.push({id:r.id,type:'document',title:r.title,
        description:'Documento da CIPA disponibilizado para consulta',
        status:r.status,date:r.date});
    }
  });
  notices=cipaMemV1Notices_(a.companyId,a.mandateId)
    .filter(function(n){return n.active;})
    .map(function(n){return {
      id:n.id,type:'notice',title:n.title,
      description:n.description,status:'Publicado',date:n.date,
    };});
  // Etiquetar cada item na Central: o Android também rejeita divergências
  // de empresa, mandato ou proprietário em vez de confiar no grupo da lista.
  function scoped(rows,privateToMember,limit) {
    return rows.slice(0,limit).map(function(item){
      var obj=Object.assign({},item);
      obj.companyId=a.companyId;
      obj.mandateId=a.mandateId;
      obj.assignedMemberId=privateToMember?a.memberId:'';
      obj.visibleToAllMembers=!privateToMember;
      return obj;
    });
  }
  return {
    meetings:scoped(meetings,true,100),
    actions:scoped(actions,true,100),
    notices:scoped(notices,false,60),
    trainings:scoped(trainings,true,50),
    documents:scoped(documents,false,60),
    reminders:scoped(reminders,true,100)
  };
}
function cipaMemV1Events_(account) {
  var sheet=cipaMemV1Sheet_(CIPA_MEM_V1_EVENTS,
    ['request_id','created_at','account_id','company_id','mandate_id',
     'member_id','kind','target_id','location','detail']);
  if(sheet.getLastRow()<2)return [];
  return sheet.getRange(2,1,sheet.getLastRow()-1,10).getValues()
    .filter(function(r){return String(r[2])===account.id&&
      String(r[3])===account.companyId&&String(r[4])===account.mandateId;})
    .map(function(r){return {id:String(r[0]),date:String(r[1]),
      kind:String(r[6]),targetId:String(r[7]),
      location:String(r[8]).slice(0,120),
      detail:String(r[9]).slice(0,700)};}).slice(-100);
}
function cipaMemV1CompanyName_(companyId) {
  var companyName='Empresa vinculada à CIPA';
  var id=String(companyId||'');
  if(!id)return companyName;
  var sheet=getSheet_('PainelDados');
  if(!sheet||sheet.getLastRow()<2)return companyName;
  var rows=sheet.getRange(2,1,sheet.getLastRow()-1,5).getValues();
  var candidates=rows.filter(function(r){
    return String(r[1]||'')===id &&
      (r[3]===true||String(r[3]).toLowerCase()==='true');
  });
  if(!candidates.length)return companyName;
  candidates.sort(function(a,b){return String(b[4]).localeCompare(String(a[4]));});
  var value=String(candidates[0][2]||'').trim();
  return value?value.slice(0,140):companyName;
}
function cipaMemV1Dashboard_(request) {
  var session=cipaMemV1Authorize_(request.sessionToken);
  if(!session)return {ok:false,code:'SESSION_INVALID'};
  var v=session.verified,a=v.account;
  var data=cipaMemV1RecordsAllowed_(session);
  var mandateRecord=v.rows.find(function(r){return r.id===a.mandateId;});
  var observations=cipaMemV1Events_(a).filter(function(e){
    return e.kind==='observation';});
  var reviews=cipaMemV1Reviews_(a.companyId,a.mandateId,a.memberId,
    observations.map(function(e){return e.id;}));
  var feedbackRead=cipaFeedbackReadMap_(a,
    observations.map(function(e){return e.id;}),reviews);
  return {ok:true,companyName:cipaMemV1CompanyName_(a.companyId),
    mandateTitle:mandateRecord?mandateRecord.title:'Mandato atual',
    profile:{
    userId:a.id,companyId:a.companyId,mandateId:a.mandateId,
    memberId:a.memberId,workerId:a.workerId,
    fullName:v.member.name,cipaRole:v.member.cipaRole,
    representation:String(v.rows.find(function(r){
      return r.id===a.memberId;}).payload.representation||''),
    jobTitle:''},
    ...data,scheduledInspections:cipaMemV1ScheduleMember_(a),
    observations:observations.map(function(e){
      var review=reviews[e.id];
      return {
        id:e.id,type:'observation',
        title:'Situação observada • '+e.location,
        description:e.detail,
        status:review?review.status:'Recebido',
        feedback:review?review.feedback:'',
        reviewId:review?review.reviewId:'',
        feedbackRead:feedbackRead[e.id]===true,
        date:e.date,companyId:a.companyId,mandateId:a.mandateId,
        assignedMemberId:a.memberId,visibleToAllMembers:false,
      };
    })};
}
function cipaMemV1Event_(request) {
  var session=cipaMemV1Authorize_(request.sessionToken);
  if(!session)return {ok:false,code:'SESSION_INVALID'};
  var a=session.verified.account,kind=String(request.kind||''),
      targetId=String(request.targetId||''),location=String(request.location||'').trim(),
      detail=String(request.detail||'').trim(),requestId=String(request.requestId||'');
  if(!/^[A-Za-z0-9_-]{16,120}$/.test(requestId)||
     detail.length<8||detail.length>1200||
     location.length>120)return {ok:false,code:'INVALID_INPUT'};
  if(['observation','progress','support','acknowledge'].indexOf(kind)<0)
    return {ok:false,code:'ACCESS_DENIED'};
  var data=cipaMemV1RecordsAllowed_(session);
  if(kind==='observation'&&location.length<2)return {ok:false,code:'INVALID_INPUT'};
  // O agendamento só pode ser associado pelo integrante da mesma empresa e mandato.
  if(kind==='observation'&&targetId&&
     !cipaMemV1ScheduleCurrent_(a.companyId,a.mandateId,a.memberId)
       .some(function(r){return r.id===targetId;}))
    return {ok:false,code:'ACCESS_DENIED'};
  if(kind==='progress'||kind==='support'){
    if(!data.actions.some(function(r){return r.id===targetId&&
      r.status!=='Resolvida'&&r.status!=='Concluída';}))
      return {ok:false,code:'ACCESS_DENIED'};
  }
  if(kind==='acknowledge' && !data.meetings.some(function(r){
    return r.id===targetId&&r.status==='Agendada';}))
    return {ok:false,code:'ACCESS_DENIED'};
  var lock=LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    // A revogação durante a preparação também precisa bloquear a gravação.
    var freshSession=cipaMemV1Authorize_(request.sessionToken);
    if(!freshSession||freshSession.verified.account.id!==a.id)
      return {ok:false,code:'SESSION_INVALID'};
    // Revalidar agenda sob o mesmo lock da gravação: cancelamento e revogação.
    if(kind==='observation'&&targetId&&
       !cipaMemV1ScheduleCurrent_(a.companyId,a.mandateId,a.memberId)
         .some(function(r){return r.id===targetId;}))
      return {ok:false,code:'ACCESS_DENIED'};
    var sheet=cipaMemV1Sheet_(CIPA_MEM_V1_EVENTS,
      ['request_id','created_at','account_id','company_id','mandate_id',
       'member_id','kind','target_id','location','detail']);
    if(sheet.getLastRow()>1){
      var rows=sheet.getRange(2,1,sheet.getLastRow()-1,10).getValues();
      var repeated=rows.find(function(r){return String(r[0])===requestId;});
      if(repeated)return String(repeated[2])===a.id&&
        String(repeated[3])===a.companyId&&String(repeated[4])===a.mandateId&&
        String(repeated[5])===a.memberId&&String(repeated[6])===kind&&
        String(repeated[7])===targetId&&String(repeated[8])===location&&
        String(repeated[9])===detail?
          {ok:true,duplicate:true}:{ok:false,code:'ID_REUSED'};
      if(kind==='observation'&&targetId&&rows.some(function(r){
        return String(r[3])===a.companyId&&String(r[4])===a.mandateId&&
          String(r[5])===a.memberId&&String(r[6])==='observation'&&
          String(r[7])===targetId;
      }))return {ok:false,code:'ALREADY_SUBMITTED'};
    }
    sheet.appendRow([requestId,new Date().toISOString(),a.id,
      a.companyId,a.mandateId,a.memberId,kind,targetId,location,detail]);
    return {ok:true};
  } finally {lock.releaseLock();}
}
function cipaMemV1Logout_(request) {
  var session=cipaMemV1Authorize_(request.sessionToken);
  if(!session)return {ok:true};
  cipaMemV1Sheet_(CIPA_MEM_V1_SESSIONS,
    ['token_hash','account_id','expires_at','revoked',
     'created_at','credential_version'])
     .getRange(session.sessionRow,4).setValue(true);
  return {ok:true};
}
function cipaMemV1AdminInbox_(request) {
  var admin=cipaMemV1Admin_(request.authToken);
  if(!admin)return {ok:false,code:'ACCESS_DENIED'};
  var cid=String(request.companyId||'').trim();
  if(!cid)return {ok:false,code:'INVALID_INPUT'};
  var sheet=cipaMemV1Sheet_(CIPA_MEM_V1_EVENTS,
    ['request_id','created_at','account_id','company_id','mandate_id',
     'member_id','kind','target_id','location','detail']);
  if(sheet.getLastRow()<2)return {ok:true,events:[]};
  var mid=String(request.mandateId||'').trim();
  var rows=sheet.getRange(2,1,sheet.getLastRow()-1,10).getValues()
    .filter(function(r){return String(r[3])===cid &&
      (!mid||String(r[4])===mid);}).slice(-250);
  var reviews=mid?cipaMemV1Reviews_(cid,mid,'',
    rows.filter(function(r){return String(r[6])==='observation';})
      .map(function(r){return String(r[0]);})):{};
  return {ok:true,events:rows.map(function(r){
    var id=String(r[0]),kind=String(r[6]),review=reviews[id];
    return {id:id,createdAt:String(r[1]),accountId:String(r[2]),
      companyId:cid,mandateId:String(r[4]),memberId:String(r[5]),
      kind:kind,targetId:String(r[7]),location:String(r[8]),
      detail:String(r[9]).slice(0,1200),
      status:kind==='observation'?
        (review?review.status:'Recebido'):'',
      feedback:kind==='observation'&&review?review.feedback:''};
  })};
}

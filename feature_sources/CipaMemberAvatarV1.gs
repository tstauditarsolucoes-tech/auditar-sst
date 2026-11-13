/**
 * Foto de perfil opcional de membro CIPA. Somente em homologação.
 * Nunca usar como identidade, prova de presença, crachá ou reconhecimento.
 * Imagens ficam numa pasta Drive privada; nenhum link público é gerado.
 * Reutiliza a pasta restrita configurada para fotos da CIPA, mas usa
 * tabela e funções independentes das imagens de vistorias.
 */
const CIPA_AVATAR_V1_SHEET='CipaPortalAvataresV1';
const CIPA_AVATAR_V1_HEADERS=['account_id','company_id','mandate_id',
  'member_id','file_id','sha256','size_bytes','updated_at'];
const CIPA_AVATAR_V1_MAX_BYTES=150000;

function cipaAvatarV1Rows_() {
  var sheet=cipaMemV1Sheet_(CIPA_AVATAR_V1_SHEET,CIPA_AVATAR_V1_HEADERS);
  if(sheet.getLastRow()>25000)throw new Error('Avatares exigem paginação.');
  return sheet.getLastRow()<2?[]:
    sheet.getRange(2,1,sheet.getLastRow()-1,8).getValues();
}
function cipaAvatarV1Account_(request,staff) {
  if(staff) {
    if(!cipaMemV1Admin_(request.authToken))return null;
    var cid=String(request.companyId||'').trim(),
      mid=String(request.mandateId||'').trim(),
      memberId=String(request.memberId||'').trim();
    if(!cid||!mid||!memberId)return null;
    var matches=cipaMemV1Accounts_().filter(function(a){
      return a.active&&a.companyId===cid&&a.mandateId===mid&&
        a.memberId===memberId;
    });
    if(matches.length!==1)return null;
    return cipaMemV1VerifyMember_(matches[0])?matches[0]:null;
  }
  var authorized=cipaMemV1Authorize_(request.sessionToken);
  return authorized?authorized.verified.account:null;
}
function cipaAvatarV1Latest_(account) {
  var found=cipaAvatarV1Rows_().filter(function(r){
    return String(r[0])===account.id &&
      String(r[1])===account.companyId &&
      String(r[2])===account.mandateId &&
      String(r[3])===account.memberId;
  });
  return found.length?found[found.length-1]:null;
}
function cipaAvatarV1Valid_(data) {
  return data.length>=8&&data.length<=CIPA_AVATAR_V1_MAX_BYTES&&
    (data[0]&255)===255&&(data[1]&255)===216&&(data[2]&255)===255&&
    (data[data.length-2]&255)===255&&(data[data.length-1]&255)===217;
}
function cipaAvatarV1Response_(request,staff) {
  var a=cipaAvatarV1Account_(request,staff);
  if(!a)return {ok:false,code:'ACCESS_DENIED'};
  var entry=cipaAvatarV1Latest_(a);
  if(!entry||!String(entry[4]))return {ok:true,hasPhoto:false};
  var folder=cipaPhotoV1Folder_();
  if(!folder)return {ok:false,code:'PHOTO_STORE_NOT_CONFIGURED'};
  var file=DriveApp.getFileById(String(entry[4]));
  if(file.getSharingAccess()!==DriveApp.Access.PRIVATE||
    file.getViewers().length||file.getEditors().length)
    return {ok:false,code:'PHOTO_NOT_PRIVATE'};
  var parents=file.getParents(),inside=false;
  while(parents.hasNext())if(parents.next().getId()===folder.getId())inside=true;
  if(!inside)return {ok:false,code:'PHOTO_STORAGE_MISMATCH'};
  var bytes=file.getBlob().getBytes();
  var sha=cipaPhotoV1Hex_(Utilities.computeDigest(
    Utilities.DigestAlgorithm.SHA_256,bytes));
  if(!cipaAvatarV1Valid_(bytes)||bytes.length!==Number(entry[6])||
     sha!==String(entry[5]))return {ok:false,code:'PHOTO_INTEGRITY_ERROR'};
  return {ok:true,hasPhoto:true,jpegBase64:Utilities.base64Encode(bytes)};
}
function cipaAvatarV1Write_(request,staff,remove) {
  var a=cipaAvatarV1Account_(request,staff);
  if(!a)return {ok:false,code:'ACCESS_DENIED'};
  var bytes=null,hash='';
  if(!remove) {
    var encoded=String(request.jpegBase64||'');
    if(encoded.length>210000||
      !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(encoded))
      return {ok:false,code:'INVALID_PHOTO'};
    try {bytes=Utilities.base64Decode(encoded);}catch(_) {
      return {ok:false,code:'INVALID_PHOTO'};
    }
    if(!cipaAvatarV1Valid_(bytes))return {ok:false,code:'INVALID_PHOTO'};
    hash=cipaPhotoV1Hex_(Utilities.computeDigest(
      Utilities.DigestAlgorithm.SHA_256,bytes));
  }
  var lock=LockService.getScriptLock();lock.waitLock(20000);
  try {
    // Revalidar dentro da seção crítica para impedir sessão revogada
    // ou alteração de membro enquanto os dados da foto são processados.
    a=cipaAvatarV1Account_(request,staff);
    if(!a)return {ok:false,code:'ACCESS_DENIED'};
    var old=cipaAvatarV1Latest_(a);
    if(!remove&&old&&String(old[5])===hash&&String(old[4])) {
      return {ok:true,unchanged:true};
    }
    if(remove&&(!old||!String(old[4])))return {ok:true,hasPhoto:false};
    var folder=cipaPhotoV1Folder_();
    if(!folder)return {ok:false,code:'PHOTO_STORE_NOT_CONFIGURED'};
    var file=null;
    try {
      if(!remove) {
        file=folder.createFile(Utilities.newBlob(bytes,'image/jpeg',
          'cipa-avatar-'+Utilities.getUuid()+'.jpg'));
        if(file.getSharingAccess()!==DriveApp.Access.PRIVATE||
           file.getViewers().length||file.getEditors().length)
          throw new Error('Avatar não privado.');
      }
      cipaMemV1Sheet_(CIPA_AVATAR_V1_SHEET,CIPA_AVATAR_V1_HEADERS)
        .appendRow([a.id,a.companyId,a.mandateId,a.memberId,
          remove?'':file.getId(),remove?'':hash,
          remove?0:bytes.length,new Date().toISOString()]);
      // A referência no banco já aponta para a versão atual.
      // Nunca exclua arquivo anterior antes de confirmar o registro.
      if(old&&String(old[4])) {
        try {DriveApp.getFileById(String(old[4])).setTrashed(true);}
        catch(_) {/* Guarda de retenção para limpeza posterior. */}
      }
    }catch(error) {
      if(file)try{file.setTrashed(true);}catch(_){}
      throw error;
    }
    return {ok:true,hasPhoto:!remove};
  } finally {lock.releaseLock();}
}
function cipaAvatarV1MemberGet_(request) {
  return cipaAvatarV1Response_(request,false);
}
function cipaAvatarV1MemberSave_(request) {
  return cipaAvatarV1Write_(request,false,false);
}
function cipaAvatarV1MemberDelete_(request) {
  return cipaAvatarV1Write_(request,false,true);
}
function cipaAvatarV1AdminSave_(request) {
  return cipaAvatarV1Write_(request,true,false);
}
function cipaAvatarV1AdminDelete_(request) {
  return cipaAvatarV1Write_(request,true,true);
}

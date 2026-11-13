/**
 * Fotos privadas da CIPA — somente homologação. Sem URLs públicas.
 * Exige CIPA_MEMBER_PHOTO_FOLDER_ID apontando para pasta Drive sem
 * compartilhamento público OU individual. Não ativa no app técnico.
 */
const CIPA_PHOTO_V1_SHEET='CipaPortalFotosV1';
const CIPA_PHOTO_V1_HEADERS=[
  'event_id','company_id','mandate_id','member_id','slot',
  'file_id','sha256','size_bytes','created_at'
];
const CIPA_PHOTO_V1_MAX=700000;

function cipaPhotoV1Rows_() {
  var sh=cipaMemV1Sheet_(CIPA_PHOTO_V1_SHEET,CIPA_PHOTO_V1_HEADERS);
  if(sh.getLastRow()>25000)throw new Error('Fotos exigem paginação.');
  return sh.getLastRow()<2?[]:sh.getRange(2,1,sh.getLastRow()-1,9).getValues();
}
function cipaPhotoV1Folder_(){
  var id=PropertiesService.getScriptProperties()
    .getProperty('CIPA_MEMBER_PHOTO_FOLDER_ID');
  if(!id)return null;
  var folder=DriveApp.getFolderById(id);
  // Compartilhamentos individuais também são proibidos nesta pasta.
  if(folder.getSharingAccess()!==DriveApp.Access.PRIVATE||
     folder.getViewers().length||folder.getEditors().length)
    throw new Error('Pasta CIPA não é privada.');
  return folder;
}
function cipaPhotoV1Event_(eventId,cid,mid,memberId){
  if(!/^[A-Za-z0-9_-]{16,120}$/.test(eventId)||!cid||!mid)return null;
  var sh=cipaMemV1Sheet_(CIPA_MEM_V1_EVENTS,
    ['request_id','created_at','account_id','company_id','mandate_id',
     'member_id','kind','target_id','location','detail']);
  if(sh.getLastRow()>25000)throw new Error('Eventos exigem paginação.');
  if(sh.getLastRow()<2)return null;
  var found=sh.getRange(2,1,sh.getLastRow()-1,10).getValues()
    .filter(function(r){return String(r[0])===eventId&&
      String(r[3])===cid&&String(r[4])===mid&&
      (!memberId||String(r[5])===memberId)&&String(r[6])==='observation';});
  return found.length===1?{id:eventId,companyId:cid,mandateId:mid,
    memberId:String(found[0][5]),accountId:String(found[0][2])}:null;
}
function cipaPhotoV1Auth_(request,staff){
  var cid=String(request.companyId||'').trim();
  var mid=String(request.mandateId||'').trim();
  var eventId=String(request.observationId||'').trim();
  if(staff) {
    var user=cipaMemV1Admin_(request.authToken)||
      cipaTstReviewAllowed_(request.authToken,cid,mid);
    if(!user||!cid||!mid)return null;
    return cipaPhotoV1Event_(eventId,cid,mid,'');
  }
  var session=cipaMemV1Authorize_(request.sessionToken);
  if(!session)return null;
  var a=session.verified.account;
  return cipaPhotoV1Event_(eventId,a.companyId,a.mandateId,a.memberId);
}
function cipaPhotoV1ValidJpeg_(data){
  return data.length>=8&&data.length<=CIPA_PHOTO_V1_MAX&&
    (data[0]&255)===255&&(data[1]&255)===216&&(data[2]&255)===255&&
    (data[data.length-2]&255)===255&&(data[data.length-1]&255)===217;
}
function cipaPhotoV1Hex_(bytes){
  return bytes.map(function(x){return (x&255).toString(16).padStart(2,'0');}).join('');
}
function cipaPhotoV1Upload_(request){
  var event=cipaPhotoV1Auth_(request,false);
  if(!event)return {ok:false,code:'ACCESS_DENIED'};
  var slot=Number(request.slot);
  var encoded=String(request.jpegBase64||'');
  if((slot!==1&&slot!==2)||encoded.length>960000||
     !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(encoded))
    return {ok:false,code:'INVALID_PHOTO'};
  var data;
  try {data=Utilities.base64Decode(encoded);}catch(_){
    return {ok:false,code:'INVALID_PHOTO'};
  }
  if(!cipaPhotoV1ValidJpeg_(data))return {ok:false,code:'INVALID_PHOTO'};
  var hash=cipaPhotoV1Hex_(Utilities.computeDigest(
    Utilities.DigestAlgorithm.SHA_256,data));
  var lock=LockService.getScriptLock();lock.waitLock(20000);
  try {
    // Token pode ser revogado durante compressão; revalidar com lock.
    event=cipaPhotoV1Auth_(request,false);
    if(!event)return {ok:false,code:'ACCESS_DENIED'};
    var existing=cipaPhotoV1Rows_().find(function(r){
      return String(r[0])===event.id&&String(r[1])===event.companyId&&
        String(r[2])===event.mandateId&&String(r[3])===event.memberId&&
        Number(r[4])===slot;
    });
    if(existing)return String(existing[6])===hash?
      {ok:true,duplicate:true,slot:slot}:{ok:false,code:'PHOTO_SLOT_USED'};
    var folder=cipaPhotoV1Folder_();
    if(!folder)return {ok:false,code:'PHOTO_STORE_NOT_CONFIGURED'};
    var file=null;
    try {
      var blob=Utilities.newBlob(data,'image/jpeg',
        'cipa-'+Utilities.getUuid()+'.jpg');
      file=folder.createFile(blob);
      if(file.getSharingAccess()!==DriveApp.Access.PRIVATE||
         file.getViewers().length||file.getEditors().length)
        throw new Error('Foto herdou permissão indevida.');
      cipaMemV1Sheet_(CIPA_PHOTO_V1_SHEET,CIPA_PHOTO_V1_HEADERS)
        .appendRow([event.id,event.companyId,event.mandateId,
          event.memberId,slot,file.getId(),hash,data.length,
          new Date().toISOString()]);
    }catch(error){
      if(file)try{file.setTrashed(true);}catch(_){}
      throw error;
    }
    return {ok:true,slot:slot};
  }finally{lock.releaseLock();}
}
function cipaPhotoV1List_(request,staff){
  var event=cipaPhotoV1Auth_(request,staff);
  if(!event)return {ok:false,code:'ACCESS_DENIED'};
  var slots=cipaPhotoV1Rows_().filter(function(r){
    return String(r[0])===event.id&&String(r[1])===event.companyId&&
      String(r[2])===event.mandateId&&String(r[3])===event.memberId;
  }).map(function(r){return Number(r[4]);}).filter(function(s){
    return s===1||s===2;
  }).sort();
  return {ok:true,slots:slots};
}
function cipaPhotoV1Get_(request,staff){
  var event=cipaPhotoV1Auth_(request,staff);
  if(!event)return {ok:false,code:'ACCESS_DENIED'};
  var slot=Number(request.slot);
  if(slot!==1&&slot!==2)return {ok:false,code:'INVALID_INPUT'};
  var entry=cipaPhotoV1Rows_().find(function(r){
    return String(r[0])===event.id&&String(r[1])===event.companyId&&
      String(r[2])===event.mandateId&&String(r[3])===event.memberId&&
      Number(r[4])===slot;
  });
  if(!entry)return {ok:false,code:'NOT_FOUND'};
  var folder=cipaPhotoV1Folder_();
  if(!folder)return {ok:false,code:'PHOTO_STORE_NOT_CONFIGURED'};
  var file=DriveApp.getFileById(String(entry[5]));
  if(file.getSharingAccess()!==DriveApp.Access.PRIVATE||
     file.getViewers().length||file.getEditors().length)
    return {ok:false,code:'PHOTO_NOT_PRIVATE'};
  var parents=file.getParents(),inside=false;
  while(parents.hasNext())if(parents.next().getId()===folder.getId())inside=true;
  if(!inside)return {ok:false,code:'PHOTO_STORAGE_MISMATCH'};
  var bytes=file.getBlob().getBytes();
  if(!cipaPhotoV1ValidJpeg_(bytes)||bytes.length!==Number(entry[7])||
    cipaPhotoV1Hex_(Utilities.computeDigest(
      Utilities.DigestAlgorithm.SHA_256,bytes))!==String(entry[6]))
    return {ok:false,code:'PHOTO_INTEGRITY_ERROR'};
  return {ok:true,slot:slot,mimeType:'image/jpeg',
    jpegBase64:Utilities.base64Encode(bytes)};
}

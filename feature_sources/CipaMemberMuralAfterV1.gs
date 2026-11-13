/**
 * Minha CIPA: foto DEPOIS da ocorrência, separada da foto original.
 * A foto não comprova correção; precisa de moderação e confirmação técnica.
 * Sem URLs públicas, acesso sem sessão ou compartilhamento entre empresas.
 */
const CIPA_MURAL_AFTER_SHEET='CipaMuralDepoisV1';
const CIPA_MURAL_AFTER_HEADERS=[
  'post_id','company_id','mandate_id','member_id','account_id','file_id',
  'sha256','size_bytes','created_at','visibility','reviewed_by','reviewed_at'
];
function cipaMuralAfterRows_(){
  return cipaMuralRows_(CIPA_MURAL_AFTER_SHEET,CIPA_MURAL_AFTER_HEADERS);
}
function cipaMuralAfter_(row){
  return {postId:String(row[0]),companyId:String(row[1]),
    mandateId:String(row[2]),memberId:String(row[3]),
    accountId:String(row[4]),fileId:String(row[5]),sha:String(row[6]),
    size:Number(row[7]),createdAt:String(row[8]),
    visibility:String(row[9])};
}
function cipaMuralAfterLatest_(post){
  var all=cipaMuralAfterRows_().map(cipaMuralAfter_)
    .filter(function(e){return e.postId===post.id&&
      e.companyId===post.companyId&&e.mandateId===post.mandateId;});
  return all.length?all[all.length-1]:null;
}
function cipaMuralAfterMetadata_(post,account,staff){
  var after=cipaMuralAfterLatest_(post);
  if(!after)return {afterStatus:'',hasAfter:false};
  var visible=after.visibility==='Aprovado'||staff||
    (account&&post.memberId===account.memberId&&
      post.accountId===account.id);
  return {afterStatus:visible?after.visibility:'',
    hasAfter:!!after.fileId&&!!visible,
    afterCreatedAt:visible?after.createdAt:''};
}
function cipaMuralAfterSubmit_(request){
  var a=cipaMuralSession_(request);
  if(!a)return {ok:false,code:'ACCESS_DENIED'};
  var id=cipaMuralToken_(request.postId),
    data=cipaMuralJpeg_(String(request.jpegBase64||''));
  if(!id||!data)return {ok:false,code:'INVALID_PHOTO'};
  var sha=cipaMuralHash_(data);
  var lock=LockService.getScriptLock();lock.waitLock(20000);
  try{
    a=cipaMuralSession_(request);
    if(!a)return {ok:false,code:'ACCESS_DENIED'};
    var post=cipaMuralPostsFor_(a.companyId,a.mandateId)
      .find(function(p){return p.id===id&&p.memberId===a.memberId&&
        p.accountId===a.id&&p.visibility==='Aprovado';});
    if(!post)return {ok:false,code:'NOT_FOUND'};
    var old=cipaMuralAfterLatest_(post);
    if(old&&old.visibility!=='Não publicado')return old.sha===sha?
      {ok:true,duplicate:true,afterStatus:old.visibility}:
      {ok:false,code:'AFTER_ALREADY_SENT'};
    var folder=cipaPhotoV1Folder_();
    if(!folder)return {ok:false,code:'PHOTO_STORE_NOT_CONFIGURED'};
    var file=null;
    try {
      file=folder.createFile(Utilities.newBlob(data,'image/jpeg',
        'cipa-depois-'+Utilities.getUuid()+'.jpg'));
      if(file.getSharingAccess()!==DriveApp.Access.PRIVATE||
        file.getViewers().length||file.getEditors().length)
        throw new Error('Depois fora de pasta privada.');
      cipaMuralSheet_(CIPA_MURAL_AFTER_SHEET,CIPA_MURAL_AFTER_HEADERS)
        .appendRow([id,a.companyId,a.mandateId,a.memberId,a.id,
          file.getId(),sha,data.length,new Date().toISOString(),
          'Pendente','','']);
    }catch(error){
      if(file)try{file.setTrashed(true);}catch(_){}
      throw error;
    }
    return {ok:true,afterStatus:'Pendente'};
  }finally{lock.releaseLock();}
}
function cipaMuralAfterModerate_(request) {
  var mod=cipaMuralModerator_(request);
  if(!mod)return {ok:false,code:'ACCESS_DENIED'};
  var id=cipaMuralToken_(request.postId),
    visibility=String(request.visibility||'');
  if(!id||!['Aprovado','Não publicado'].includes(visibility))
    return {ok:false,code:'INVALID_INPUT'};
  var lock=LockService.getScriptLock();lock.waitLock(20000);
  try {
    mod=cipaMuralModerator_(request);
    if(!mod)return {ok:false,code:'ACCESS_DENIED'};
    var sh=cipaMuralSheet_(CIPA_MURAL_AFTER_SHEET,CIPA_MURAL_AFTER_HEADERS),
      rows=cipaMuralAfterRows_();
    var i=-1;
    for(var k=0;k<rows.length;k++)if(
      String(rows[k][0])===id&&
      String(rows[k][1])===mod.companyId&&
      String(rows[k][2])===mod.mandateId)i=k;
    if(i<0)return {ok:false,code:'NOT_FOUND'};
    sh.getRange(i+2,10,1,3).setValues([[visibility,
      String(mod.user.id),new Date().toISOString()]]);
    return {ok:true,visibility:visibility,
      message:'Foto posterior analisada; não comprova conclusão.'};
  }finally{lock.releaseLock();}
}
function cipaMuralAfterPhoto_(request,staff){
  var account=staff?null:cipaMuralSession_(request),
    mod=staff?cipaMuralModerator_(request):null;
  if(!account&&!mod)return {ok:false,code:'ACCESS_DENIED'};
  var id=cipaMuralToken_(request.postId),
    cid=staff?mod.companyId:account.companyId,
    mid=staff?mod.mandateId:account.mandateId;
  var post=cipaMuralPostsFor_(cid,mid).find(function(p){return p.id===id;});
  if(!post)return {ok:false,code:'NOT_FOUND'};
  var after=cipaMuralAfterLatest_(post);
  if(!after||!after.fileId)return {ok:true,hasPhoto:false};
  if(!staff&&!(after.visibility==='Aprovado'&&
     post.visibility==='Aprovado')&&
     !(post.memberId===account.memberId&&post.accountId===account.id))
    return {ok:false,code:'NOT_FOUND'};
  var folder=cipaPhotoV1Folder_();
  if(!folder)return {ok:false,code:'PHOTO_STORE_NOT_CONFIGURED'};
  var file=DriveApp.getFileById(after.fileId);
  if(file.getSharingAccess()!==DriveApp.Access.PRIVATE||
    file.getViewers().length||file.getEditors().length)
    return {ok:false,code:'PHOTO_NOT_PRIVATE'};
  var parents=file.getParents(),inside=false;
  while(parents.hasNext())if(parents.next().getId()===folder.getId())inside=true;
  if(!inside)return {ok:false,code:'PHOTO_STORAGE_MISMATCH'};
  var bytes=file.getBlob().getBytes();
  if(!cipaMuralJpeg_(Utilities.base64Encode(bytes))||
     bytes.length!==after.size||cipaMuralHash_(bytes)!==after.sha)
    return {ok:false,code:'PHOTO_INTEGRITY_ERROR'};
  return {ok:true,hasPhoto:true,jpegBase64:Utilities.base64Encode(bytes)};
}

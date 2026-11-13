/**
 * Minha CIPA • Mural moderado interno (homologação, não chat público).
 * Não cria NC, CAT, ata, assinatura ou certificação de correção.
 * POST somente por conta membro ativa; moderação por ADM/TST delegado.
 * Separado do portal do técnico e da fila de fotos de vistoria.
 */
const CIPA_MURAL_POSTS='CipaMuralPostsV1';
const CIPA_MURAL_COMMENTS='CipaMuralComentariosV1';
const CIPA_MURAL_POST_HEADERS=[
  'id','created_at','company_id','mandate_id','member_id','account_id',
  'place','detail','status','visibility','file_id','sha256','size_bytes',
  'reviewed_at','reviewed_by'
];
const CIPA_MURAL_COMMENT_HEADERS=[
  'id','created_at','post_id','company_id','mandate_id','member_id',
  'body','visibility','reviewed_by','author_kind'
];
const CIPA_MURAL_MAX_JPEG=250000;
function cipaMuralSheet_(name,headers) {
  return cipaMemV1Sheet_(name,headers);
}
function cipaMuralRows_(name,headers) {
  var sh=cipaMuralSheet_(name,headers),last=sh.getLastRow();
  if(last>25000)throw new Error('Mural precisa de paginação.');
  return last<2?[]:sh.getRange(2,1,last-1,headers.length).getValues();
}
function cipaMuralToken_(id) {
  return /^[A-Za-z0-9_-]{16,120}$/.test(String(id||''))?String(id):'';
}
function cipaMuralText_(text,min,max) {
  var clean=String(text||'').trim();
  return clean.length>=min&&clean.length<=max&&
    !/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(clean)?clean:'';
}
function cipaMuralSession_(request) {
  var s=cipaMemV1Authorize_(request.sessionToken);
  return s?s.verified.account:null;
}
function cipaMuralModerator_(request) {
  var cid=String(request.companyId||'').trim(),
    mid=String(request.mandateId||'').trim();
  if(!cid||!mid)return null;
  var u=cipaMemV1Admin_(request.authToken)||
    cipaTstReviewAllowed_(request.authToken,cid,mid);
  if(!u)return null;
  var active=cipaMemV1Records_(cid).some(function(r) {
    return r.table==='sst_records'&&r.type==='CIPA_MANDATO'&&
      r.id===mid&&r.status==='Ativo';
  });
  return active?{user:u,companyId:cid,mandateId:mid}:null;
}
function cipaMuralPost_(r) {
  return {id:String(r[0]),createdAt:String(r[1]),
    companyId:String(r[2]),mandateId:String(r[3]),
    memberId:String(r[4]),accountId:String(r[5]),
    place:String(r[6]),detail:String(r[7]),status:String(r[8]),
    visibility:String(r[9]),fileId:String(r[10]),sha:String(r[11]),
    size:Number(r[12]),reviewedAt:String(r[13]),reviewedBy:String(r[14])};
}
function cipaMuralComment_(r) {
  return {id:String(r[0]),createdAt:String(r[1]),postId:String(r[2]),
    companyId:String(r[3]),mandateId:String(r[4]),memberId:String(r[5]),
    body:String(r[6]),visibility:String(r[7]),
    reviewedBy:String(r[8]),authorKind:String(r[9])};
}
function cipaMuralScope_(p,account) {
  return p&&account&&p.companyId===account.companyId&&
    p.mandateId===account.mandateId;
}
function cipaMuralPostsFor_(cid,mid){
  return cipaMuralRows_(CIPA_MURAL_POSTS,CIPA_MURAL_POST_HEADERS)
    .map(cipaMuralPost_)
    .filter(function(p){return p.companyId===cid&&p.mandateId===mid;});
}
function cipaMuralCommentsFor_(cid,mid){
  return cipaMuralRows_(CIPA_MURAL_COMMENTS,CIPA_MURAL_COMMENT_HEADERS)
    .map(cipaMuralComment_)
    .filter(function(c){return c.companyId===cid&&c.mandateId===mid;});
}
function cipaMuralJpeg_(encoded){
  if(typeof encoded!=='string'||encoded.length>340000||
    !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(encoded))
    return null;
  var b;
  try{b=Utilities.base64Decode(encoded);}catch(_){return null;}
  if(b.length<8||b.length>CIPA_MURAL_MAX_JPEG||
    (b[0]&255)!==255||(b[1]&255)!==216||(b[2]&255)!==255||
    (b[b.length-2]&255)!==255||(b[b.length-1]&255)!==217)
    return null;
  return b;
}
function cipaMuralHash_(data) {
  return cipaPhotoV1Hex_(Utilities.computeDigest(
    Utilities.DigestAlgorithm.SHA_256,data));
}
function cipaMuralCreate_(request) {
  var a=cipaMuralSession_(request);
  if(!a)return {ok:false,code:'ACCESS_DENIED'};
  var id=cipaMuralToken_(request.requestId),
    place=cipaMuralText_(request.place,2,120),
    detail=cipaMuralText_(request.detail,12,900),
    encoded=String(request.jpegBase64||'');
  if(!id||!place||!detail)return {ok:false,code:'INVALID_INPUT'};
  var data=encoded?cipaMuralJpeg_(encoded):null;
  if(encoded&&!data)return {ok:false,code:'INVALID_PHOTO'};
  var hash=data?cipaMuralHash_(data):'';
  var lock=LockService.getScriptLock();lock.waitLock(20000);
  try {
    a=cipaMuralSession_(request);
    if(!a)return {ok:false,code:'ACCESS_DENIED'};
    // Identificador global nunca pode ser reutilizado por outro membro.
    var existing=cipaMuralRows_(CIPA_MURAL_POSTS,CIPA_MURAL_POST_HEADERS)
      .map(cipaMuralPost_).find(function(p){return p.id===id;});
    if(existing) {
      return cipaMuralScope_(existing,a)&&existing.memberId===a.memberId&&
        existing.accountId===a.id&&existing.place===place&&
        existing.detail===detail&&existing.sha===hash?
          {ok:true,duplicate:true,id:id}:{ok:false,code:'ID_REUSED'};
    }
    var folder=null,file=null;
    if(data){
      folder=cipaPhotoV1Folder_();
      if(!folder)return {ok:false,code:'PHOTO_STORE_NOT_CONFIGURED'};
    }
    try {
      if(data) {
        file=folder.createFile(Utilities.newBlob(data,'image/jpeg',
          'cipa-mural-'+Utilities.getUuid()+'.jpg'));
        if(file.getSharingAccess()!==DriveApp.Access.PRIVATE||
          file.getViewers().length||file.getEditors().length)
          throw new Error('Foto fora da pasta privada.');
      }
      cipaMuralSheet_(CIPA_MURAL_POSTS,CIPA_MURAL_POST_HEADERS)
        .appendRow([id,new Date().toISOString(),a.companyId,a.mandateId,
          a.memberId,a.id,place,detail,'Recebido','Pendente',
          file?file.getId():'',hash,data?data.length:0,'','']);
    } catch(error) {
      if(file)try{file.setTrashed(true);}catch(_){}
      throw error;
    }
    return {ok:true,id:id,visibility:'Pendente'};
  } finally {lock.releaseLock();}
}
function cipaMuralMemberList_(request) {
  var a=cipaMuralSession_(request);
  if(!a)return {ok:false,code:'ACCESS_DENIED'};
  var posts=cipaMuralPostsFor_(a.companyId,a.mandateId)
    .filter(function(p){return p.visibility==='Aprovado'||
      (p.memberId===a.memberId&&p.accountId===a.id);})
    .slice(-70).reverse();
  var comments=cipaMuralCommentsFor_(a.companyId,a.mandateId);
  return {ok:true,posts:posts.map(function(p) {
    var own=p.memberId===a.memberId&&p.accountId===a.id;
    return {id:p.id,place:p.place,detail:p.detail,
      createdAt:p.createdAt,status:p.status,
      visibility:p.visibility,hasPhoto:!!p.fileId,isMine:own,
      comments:comments.filter(function(c) {
        return c.postId===p.id&&(c.visibility==='Aprovado'||
          (c.memberId===a.memberId&&c.authorKind==='member'));
      }).slice(-15).map(function(c){
        return {id:c.id,body:c.body,createdAt:c.createdAt,
          visibility:c.visibility,
          authorLabel:c.authorKind==='moderator'?'Equipe SST':'Cipeiro'};
      })};
  })};
}
function cipaMuralMemberComment_(request) {
  var a=cipaMuralSession_(request);
  if(!a)return {ok:false,code:'ACCESS_DENIED'};
  var id=cipaMuralToken_(request.requestId),
    postId=cipaMuralToken_(request.postId),
    body=cipaMuralText_(request.body,5,450);
  if(!id||!postId||!body)return {ok:false,code:'INVALID_INPUT'};
  var lock=LockService.getScriptLock();lock.waitLock(20000);
  try {
    a=cipaMuralSession_(request);
    if(!a)return {ok:false,code:'ACCESS_DENIED'};
    var post=cipaMuralPostsFor_(a.companyId,a.mandateId)
      .find(function(p){return p.id===postId&&p.visibility==='Aprovado';});
    if(!post)return {ok:false,code:'NOT_FOUND'};
    var old=cipaMuralRows_(CIPA_MURAL_COMMENTS,CIPA_MURAL_COMMENT_HEADERS)
      .map(cipaMuralComment_).find(function(c){return c.id===id;});
    if(old)return cipaMuralScope_(old,a)&&old.memberId===a.memberId&&
      old.postId===postId&&old.body===body?
      {ok:true,duplicate:true,id:id}:{ok:false,code:'ID_REUSED'};
    cipaMuralSheet_(CIPA_MURAL_COMMENTS,CIPA_MURAL_COMMENT_HEADERS)
      .appendRow([id,new Date().toISOString(),postId,a.companyId,
        a.mandateId,a.memberId,body,'Pendente','','member']);
    return {ok:true,id:id,visibility:'Pendente'};
  }finally{lock.releaseLock();}
}
function cipaMuralModeratorList_(request) {
  var m=cipaMuralModerator_(request);
  if(!m)return {ok:false,code:'ACCESS_DENIED'};
  var posts=cipaMuralPostsFor_(m.companyId,m.mandateId).slice(-80).reverse();
  var comments=cipaMuralCommentsFor_(m.companyId,m.mandateId);
  return {ok:true,posts:posts.map(function(p) {
    return {id:p.id,place:p.place,detail:p.detail,status:p.status,
      visibility:p.visibility,hasPhoto:!!p.fileId,
      createdAt:p.createdAt,comments:comments
        .filter(function(c){return c.postId===p.id;})
        .slice(-25).map(function(c){
          return {id:c.id,body:c.body,visibility:c.visibility,
            authorLabel:c.authorKind==='moderator'?'Equipe SST':'Cipeiro'};
        })};
  })};
}
function cipaMuralModerate_(request) {
  var m=cipaMuralModerator_(request);
  if(!m)return {ok:false,code:'ACCESS_DENIED'};
  var id=cipaMuralToken_(request.postId);
  var visibility=String(request.visibility||''),
    status=String(request.status||'');
  if(!id||!['Aprovado','Não publicado'].includes(visibility)||
    !['Em análise','Orientação enviada','Resolvido'].includes(status))
    return {ok:false,code:'INVALID_INPUT'};
  if(status==='Resolvido'&&request.confirmedByResponsible!==true)
    return {ok:false,code:'CONFIRMATION_REQUIRED'};
  var lock=LockService.getScriptLock();lock.waitLock(20000);
  try {
    m=cipaMuralModerator_(request);
    if(!m)return {ok:false,code:'ACCESS_DENIED'};
    var sh=cipaMuralSheet_(CIPA_MURAL_POSTS,CIPA_MURAL_POST_HEADERS);
    var rows=cipaMuralRows_(CIPA_MURAL_POSTS,CIPA_MURAL_POST_HEADERS);
    var i=rows.findIndex(function(r){return String(r[0])===id&&
      String(r[2])===m.companyId&&String(r[3])===m.mandateId;});
    if(i<0)return {ok:false,code:'NOT_FOUND'};
    sh.getRange(i+2,9,1,2).setValues([[status,visibility]]);
    sh.getRange(i+2,14,1,2)
      .setValues([[new Date().toISOString(),String(m.user.id)]]);
    return {ok:true,status:status,visibility:visibility};
  }finally{lock.releaseLock();}
}
function cipaMuralModerateComment_(request) {
  var m=cipaMuralModerator_(request);
  if(!m)return {ok:false,code:'ACCESS_DENIED'};
  var id=cipaMuralToken_(request.commentId),
    visibility=String(request.visibility||'');
  if(!id||!['Aprovado','Não publicado'].includes(visibility))
    return {ok:false,code:'INVALID_INPUT'};
  var lock=LockService.getScriptLock();lock.waitLock(20000);
  try {
    m=cipaMuralModerator_(request);
    if(!m)return {ok:false,code:'ACCESS_DENIED'};
    var sh=cipaMuralSheet_(CIPA_MURAL_COMMENTS,CIPA_MURAL_COMMENT_HEADERS);
    var rows=cipaMuralRows_(CIPA_MURAL_COMMENTS,CIPA_MURAL_COMMENT_HEADERS);
    var i=rows.findIndex(function(r){return String(r[0])===id&&
      String(r[3])===m.companyId&&String(r[4])===m.mandateId;});
    if(i<0)return {ok:false,code:'NOT_FOUND'};
    sh.getRange(i+2,8,1,2)
      .setValues([[visibility,String(m.user.id)]]);
    return {ok:true};
  }finally{lock.releaseLock();}
}
function cipaMuralModeratorReply_(request){
  var m=cipaMuralModerator_(request);
  if(!m)return {ok:false,code:'ACCESS_DENIED'};
  var id=cipaMuralToken_(request.requestId),
    postId=cipaMuralToken_(request.postId),
    body=cipaMuralText_(request.body,5,450);
  if(!id||!postId||!body)return {ok:false,code:'INVALID_INPUT'};
  var lock=LockService.getScriptLock();lock.waitLock(20000);
  try{
    m=cipaMuralModerator_(request);
    if(!m)return {ok:false,code:'ACCESS_DENIED'};
    var post=cipaMuralPostsFor_(m.companyId,m.mandateId)
      .find(function(p){return p.id===postId&&p.visibility==='Aprovado';});
    if(!post)return {ok:false,code:'NOT_FOUND'};
    var old=cipaMuralRows_(CIPA_MURAL_COMMENTS,CIPA_MURAL_COMMENT_HEADERS)
      .map(cipaMuralComment_).find(function(c){return c.id===id;});
    if(old)return old.companyId===m.companyId&&
      old.mandateId===m.mandateId&&old.postId===postId&&
      old.body===body&&old.authorKind==='moderator'?
      {ok:true,duplicate:true,id:id}:{ok:false,code:'ID_REUSED'};
    cipaMuralSheet_(CIPA_MURAL_COMMENTS,CIPA_MURAL_COMMENT_HEADERS)
      .appendRow([id,new Date().toISOString(),postId,m.companyId,
        m.mandateId,'',body,'Aprovado',String(m.user.id),'moderator']);
    return {ok:true,id:id};
  }finally{lock.releaseLock();}
}
function cipaMuralPhoto_(request,staff) {
  var account=null,mod=null;
  if(staff)mod=cipaMuralModerator_(request);
  else account=cipaMuralSession_(request);
  if(!mod&&!account)return {ok:false,code:'ACCESS_DENIED'};
  var id=cipaMuralToken_(request.postId);
  var cid=staff?mod.companyId:account.companyId,
    mid=staff?mod.mandateId:account.mandateId;
  var post=cipaMuralPostsFor_(cid,mid).find(function(p){return p.id===id;});
  if(!post||(!staff&&post.visibility!=='Aprovado'&&
    !(post.memberId===account.memberId&&post.accountId===account.id)))
    return {ok:false,code:'NOT_FOUND'};
  if(!post.fileId)return {ok:true,hasPhoto:false};
  var folder=cipaPhotoV1Folder_();
  if(!folder)return {ok:false,code:'PHOTO_STORE_NOT_CONFIGURED'};
  var file=DriveApp.getFileById(post.fileId);
  if(file.getSharingAccess()!==DriveApp.Access.PRIVATE||
    file.getViewers().length||file.getEditors().length)
    return {ok:false,code:'PHOTO_NOT_PRIVATE'};
  var parents=file.getParents(),inside=false;
  while(parents.hasNext())if(parents.next().getId()===folder.getId())inside=true;
  if(!inside)return {ok:false,code:'PHOTO_STORAGE_MISMATCH'};
  var bytes=file.getBlob().getBytes();
  if(!cipaMuralJpeg_(Utilities.base64Encode(bytes))||
     bytes.length!==post.size||cipaMuralHash_(bytes)!==post.sha)
    return {ok:false,code:'PHOTO_INTEGRITY_ERROR'};
  return {ok:true,hasPhoto:true,jpegBase64:Utilities.base64Encode(bytes)};
}

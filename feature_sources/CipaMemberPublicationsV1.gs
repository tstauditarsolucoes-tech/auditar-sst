/**
 * Minha CIPA — Publicações administrativas EXPLÍCITAS.
 * Somente metadados de documentos; não fornece PDFs nem arquivos restritos.
 * Todas as funções dependem de autenticação ADMIN validada em MultiUser.gs.
 * Não altera os cadastros e arquivos originais da CIPA.
 */
const CIPA_MEM_V1_NOTICES='CipaPortalAvisosV1';
const CIPA_MEM_V1_DOCUMENTS='CipaPortalDocumentosV1';
const CIPA_MEM_V1_NOTICE_HEADERS=[
  'id','company_id','mandate_id','title','body','active','created_at','created_by'
];
const CIPA_MEM_V1_DOC_HEADERS=[
  'company_id','mandate_id','document_id','published','updated_at','updated_by'
];

function cipaMemV1AdminScope_(request) {
  var admin=cipaMemV1Admin_(request.authToken);
  if(!admin)return null;
  var cid=String(request.companyId||'').trim(),
      mid=String(request.mandateId||'').trim();
  if(!cid||!mid)return null;
  var active=cipaMemV1Records_(cid).some(function(r){
    return r.table==='sst_records'&&r.type==='CIPA_MANDATO'&&
      r.id===mid&&r.status==='Ativo';
  });
  return active?{admin:admin,companyId:cid,mandateId:mid}:null;
}

function cipaMemV1Notices_(cid,mid) {
  var sheet=cipaMemV1Sheet_(CIPA_MEM_V1_NOTICES,CIPA_MEM_V1_NOTICE_HEADERS);
  if(sheet.getLastRow()<2)return [];
  return sheet.getRange(2,1,sheet.getLastRow()-1,8).getValues()
    .map(function(r,i){return {
      row:i+2,id:String(r[0]||''),companyId:String(r[1]||''),
      mandateId:String(r[2]||''),title:String(r[3]||''),
      description:String(r[4]||''),
      active:r[5]===true||String(r[5]).toLowerCase()==='true',
      date:String(r[6]||'')
    };}).filter(function(r){return r.companyId===cid&&r.mandateId===mid;});
}

function cipaMemV1PublishNotice_(request) {
  var scope=cipaMemV1AdminScope_(request);
  if(!scope)return {ok:false,code:'ACCESS_DENIED'};
  var title=String(request.title||'').trim(),
      detail=String(request.detail||'').trim();
  if(title.length<4||title.length>160||detail.length<8||detail.length>900)
    return {ok:false,code:'INVALID_INPUT',
      message:'Informe título e comunicado sem dados pessoais ou sigilosos.'};
  if(request.confirmedPublic!==true)
    return {ok:false,code:'CONFIRM_PUBLICATION_REQUIRED'};
  var id=Utilities.getUuid();
  cipaMemV1Sheet_(CIPA_MEM_V1_NOTICES,CIPA_MEM_V1_NOTICE_HEADERS)
    .appendRow([id,scope.companyId,scope.mandateId,
      title,detail,true,new Date().toISOString(),scope.admin.id]);
  auditAuthEvent_(scope.admin,'cipa_member_notice_publish','CIPA_AVISO',
    id,scope.companyId,'','cipa_member',{mandateId:scope.mandateId});
  return {ok:true,id:id};
}

function cipaMemV1WithdrawNotice_(request) {
  var scope=cipaMemV1AdminScope_(request);
  if(!scope)return {ok:false,code:'ACCESS_DENIED'};
  var id=String(request.noticeId||'').trim();
  var found=cipaMemV1Notices_(scope.companyId,scope.mandateId)
    .find(function(item){return item.id===id;});
  if(!found)return {ok:false,code:'NOT_FOUND'};
  cipaMemV1Sheet_(CIPA_MEM_V1_NOTICES,CIPA_MEM_V1_NOTICE_HEADERS)
    .getRange(found.row,6).setValue(false);
  auditAuthEvent_(scope.admin,'cipa_member_notice_withdraw','CIPA_AVISO',
    id,scope.companyId,'','cipa_member',{mandateId:scope.mandateId});
  return {ok:true};
}

function cipaMemV1PublishedDocumentIds_(cid,mid) {
  var sheet=cipaMemV1Sheet_(CIPA_MEM_V1_DOCUMENTS,CIPA_MEM_V1_DOC_HEADERS);
  if(sheet.getLastRow()<2)return [];
  var rows=sheet.getRange(2,1,sheet.getLastRow()-1,6).getValues();
  var latest={};
  rows.forEach(function(r,i){
    if(String(r[0]||'')!==cid||String(r[1]||'')!==mid)return;
    var id=String(r[2]||'');
    if(!id)return;
    latest[id]={
      id:id,row:i+2,
      published:r[3]===true||String(r[3]).toLowerCase()==='true'
    };
  });
  return Object.keys(latest).map(function(k){return latest[k];});
}

function cipaMemV1PublishDocument_(request) {
  var scope=cipaMemV1AdminScope_(request);
  if(!scope)return {ok:false,code:'ACCESS_DENIED'};
  if(request.confirmedSafeMetadata!==true)
    return {ok:false,code:'CONFIRM_SAFE_METADATA_REQUIRED'};
  var id=String(request.documentId||'').trim();
  var document=cipaMemV1Records_(scope.companyId).find(function(r){
    return r.table==='sst_records' && r.type==='CIPA_DOCUMENTO' &&
      r.id===id && r.payload.mandateId===scope.mandateId &&
      r.payload.containsPersonalData!==true &&
      r.payload.signedRestricted!==true;
  });
  if(!document)return {ok:false,code:'DOCUMENT_NOT_ELIGIBLE'};
  var lock=LockService.getScriptLock();lock.waitLock(15000);
  try {
    var sheet=cipaMemV1Sheet_(CIPA_MEM_V1_DOCUMENTS,CIPA_MEM_V1_DOC_HEADERS);
    var existing=cipaMemV1PublishedDocumentIds_(
      scope.companyId,scope.mandateId)
      .find(function(item){return item.id===id;});
    if(existing) {
      sheet.getRange(existing.row,4,1,3).setValues([[
        true,new Date().toISOString(),scope.admin.id
      ]]);
    } else {
      sheet.appendRow([scope.companyId,scope.mandateId,id,true,
        new Date().toISOString(),scope.admin.id]);
    }
  } finally {lock.releaseLock();}
  auditAuthEvent_(scope.admin,'cipa_member_document_publish',
    'CIPA_DOCUMENTO',id,scope.companyId,'','cipa_member',
    {mandateId:scope.mandateId});
  return {ok:true,id:id};
}

function cipaMemV1UnpublishDocument_(request) {
  var scope=cipaMemV1AdminScope_(request);
  if(!scope)return {ok:false,code:'ACCESS_DENIED'};
  var id=String(request.documentId||'').trim(),
      existing=cipaMemV1PublishedDocumentIds_(
        scope.companyId,scope.mandateId)
        .find(function(item){return item.id===id;});
  if(!existing)return {ok:false,code:'NOT_FOUND'};
  var sheet=cipaMemV1Sheet_(CIPA_MEM_V1_DOCUMENTS,CIPA_MEM_V1_DOC_HEADERS);
  sheet.getRange(existing.row,4,1,3).setValues([[
    false,new Date().toISOString(),scope.admin.id
  ]]);
  auditAuthEvent_(scope.admin,'cipa_member_document_unpublish',
    'CIPA_DOCUMENTO',id,scope.companyId,'','cipa_member',
    {mandateId:scope.mandateId});
  return {ok:true};
}

function cipaMemV1AdminPublicationList_(request) {
  var scope=cipaMemV1AdminScope_(request);
  if(!scope)return {ok:false,code:'ACCESS_DENIED'};
  return {ok:true,
    notices:cipaMemV1Notices_(scope.companyId,scope.mandateId)
      .map(function(n){return {
        id:n.id,title:n.title,description:n.description,
        active:n.active,date:n.date
      };}).slice(-100),
    documents:cipaMemV1PublishedDocumentIds_(
      scope.companyId,scope.mandateId)
      .filter(function(d){return d.published;})
      .map(function(d){return {id:d.id};})
  };
}

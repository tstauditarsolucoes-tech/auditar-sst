'use strict';
const assert=require('assert');
const fs=require('fs');
const path=require('path');
const crypto=require('crypto');
const vm=require('vm');

class FakeSheet {
  constructor(name,headers){this.name=name;this.rows=[headers.slice()];}
  getLastRow(){return this.rows.length;}
  appendRow(row){this.rows.push(row.slice());}
  getRange(r,c,n=1,w=1){
    return {
      getValues:()=>Array.from({length:n},(_,i)=>
        this.rows[r-1+i].slice(c-1,c-1+w)),
      setValue:(v)=>{this.rows[r-1][c-1]=v;},
      setValues:(values)=>{for(let i=0;i<values.length;i++)
        for(let j=0;j<values[i].length;j++)
          this.rows[r-1+i][c-1+j]=values[i][j];},
    };
  }
}
const sheets=new Map();
const mail=[];
const cache=new Map();
let sequence=0;
function sheet(name,headers=[]){
  if(!sheets.has(name))sheets.set(name,new FakeSheet(name,headers));
  return sheets.get(name);
}
const photoFiles=new Map();
const photoStore={
  share:'PRIVATE',
  getId:()=> 'private-cipa-folder',
  getSharingAccess(){return this.share;},
  getViewers:()=>[],getEditors:()=>[],
  createFile(blob){
    const id=crypto.randomUUID(),bytes=blob.getBytes();
    const f={
      id,bytes,trashed:false,
      getId(){return this.id;},
      getSharingAccess:()=> 'PRIVATE',
      getViewers:()=>[],getEditors:()=>[],
      getParents:()=>{
        let consumed=false;
        return {hasNext:()=>!consumed,next:()=>{
          consumed=true;return photoStore;
        }};
      },
      getBlob(){return {getBytes:()=>Array.from(bytes)};},
      setTrashed(v){this.trashed=v;},
    };
    photoFiles.set(id,f);return f;
  },
};
const props={
  CIPA_MEMBER_V1_ENABLED:'true',
  CIPA_MEMBER_V1_PEPPER:'a-very-long-test-only-secret-do-not-copy-into-production-999999999',
};
const fakeAdmin={
  id:'admin-A',active:true,role:'admin',email:'admin@example.test',
};
const fakeTst={id:'tst-A',active:true,role:'tst',email:'tst@example.test'};

const scope={
  console,
  Date,
  Number,
  String,
  Array,
  Object,
  JSON,
  Math,
  Map,
  Set,
  PropertiesService:{getScriptProperties(){return {
    getProperty:(name)=>props[name]||null,
    setProperty:(name,value)=>{props[name]=value;},
  };}},
  CacheService:{getScriptCache(){return {
    get(key){const o=cache.get(key);if(!o)return null;
      if(o.until<Date.now()){cache.delete(key);return null;}return o.value;},
    put(key,value,ttl){cache.set(key,{value,until:Date.now()+ttl*1000});},
    remove(key){cache.delete(key);},
  };}},
  MailApp:{sendEmail:(to,subject,body)=>mail.push({to,subject,body})},
  DriveApp:{
    Access:{PRIVATE:'PRIVATE'},
    getFolderById:(id)=>{
      if(id!==photoStore.getId())throw Error('Private folder not found');
      return photoStore;
    },
    getFileById:(id)=>{
      if(!photoFiles.has(id))throw Error('Private file not found');
      return photoFiles.get(id);
    },
  },
  Utilities:{
    DigestAlgorithm:{SHA_256:'SHA_256'},
    Charset:{UTF_8:'UTF_8'},
    getUuid:()=>crypto.randomUUID(),
    base64Decode:(x)=>Array.from(Buffer.from(x,'base64')),
    base64Encode:(x)=>Buffer.from(x).toString('base64'),
    newBlob:(data,mime,name)=>({
      getBytes:()=>Array.from(data),getContentType:()=>mime,getName:()=>name,
    }),
    computeDigest:(alg,input)=>Array.from(
      crypto.createHash('sha256').update(String(input)).digest()),
  },
  ensureAuthStorage_:()=>({
    getSheetByName:(name)=>sheet(name),
  }),
  ensureSheet_:(ss,name,headers)=>sheet(name,headers),
  getSheet_:(name)=>sheet(name),
  DEVICE_SYNC_SHEET:'SincronizacaoDispositivos',
  authHex_:(arr)=>arr.map(x=>(Number(x)+256)%256)
    .map(x=>x.toString(16).padStart(2,'0')).join(''),
  authUserFromToken_:(token)=>token==='valid-admin'?fakeAdmin:
    token==='valid-tst'?fakeTst:null,
  auditAuthEvent_:()=>{},
  LockService:{getScriptLock(){return {
    waitLock:()=>{},releaseLock:()=>{},
  };}},
};
scope.globalThis=scope;
vm.createContext(scope);
const root=path.resolve(__dirname,'..');
vm.runInContext(fs.readFileSync(path.join(
  root,'feature_sources/cipa_member_server_policy_v1.js'),'utf8'),
  scope,{filename:'CipaMemberServerPolicy.gs'});
vm.runInContext(fs.readFileSync(path.join(
  root,'feature_sources/CipaMemberGatewayV1.gs'),'utf8'),
  scope,{filename:'CipaMemberGatewayV1.gs'});
vm.runInContext(fs.readFileSync(path.join(
  root,'feature_sources/CipaMemberPublicationsV1.gs'),'utf8'),
  scope,{filename:'CipaMemberPublicationsV1.gs'});
vm.runInContext(fs.readFileSync(path.join(
  root,'feature_sources/CipaMemberReviewsV1.gs'),'utf8'),
  scope,{filename:'CipaMemberReviewsV1.gs'});
vm.runInContext(fs.readFileSync(path.join(
  root,'feature_sources/CipaMemberFeedbackReadV1.gs'),'utf8'),
  scope,{filename:'CipaMemberFeedbackReadV1.gs'});
vm.runInContext(fs.readFileSync(path.join(
  root,'feature_sources/CipaTstReviewAccessV1.gs'),'utf8'),
  scope,{filename:'CipaTstReviewAccessV1.gs'});
vm.runInContext(fs.readFileSync(path.join(
  root,'feature_sources/CipaMemberInspectionSchedulesV1.gs'),'utf8'),
  scope,{filename:'CipaMemberInspectionSchedulesV1.gs'});
vm.runInContext(fs.readFileSync(path.join(
  root,'feature_sources/CipaMemberPhotosV1.gs'),'utf8'),
  scope,{filename:'CipaMemberPhotosV1.gs'});
vm.runInContext(fs.readFileSync(path.join(
  root,'feature_sources/CipaMemberMetricsV1.gs'),'utf8'),
  scope,{filename:'CipaMemberMetricsV1.gs'});
vm.runInContext(fs.readFileSync(path.join(
  root,'feature_sources/CipaMemberMuralV1.gs'),'utf8'),
  scope,{filename:'CipaMemberMuralV1.gs'});
const invoke=(action,fields={})=>JSON.parse(JSON.stringify(
  scope.cipaMemV1Route_({action,...fields})));

const panel=sheet('PainelDados',[
  'token','company_id','company_name','active','updated_at'
]);
panel.appendRow(['fake-panel','company-A','Cerâmica de Exemplo',true,'2026-11-05']);
const sync=sheet('SincronizacaoDispositivos',[
  'table_name','record_id','deleted','server_version',
  'source_device','source_platform','updated_at','payload_json',
  'company_id','updated_by_user'
]);
function record(id,company,type,title,status,fields={}){
 const payload={
   id,company_id:company,type,title,status,
   date:'2026-11-05',due_date:String(fields.dueDate||''),
   payload_json:JSON.stringify(fields),
 };
 sync.appendRow(['sst_records',id,false,sync.getLastRow()+1,
   'synthetic','android','2026-11-05',JSON.stringify(payload),
   company,'admin-A']);
}
record('mandate-A','company-A','CIPA_MANDATO','CIPA 2026','Ativo');
record('member-A','company-A','CIPA_MEMBRO','Maria Silva','Ativo',{
 mandateId:'mandate-A',workerId:'worker-A',cipaRole:'Vice-presidente',
 representation:'Empregados',
});
record('meeting-A','company-A','CIPA_REUNIAO',
 'Reunião mensal da CIPA','Agendada',{
 mandateId:'mandate-A',memberIds:['member-A'],place:'Sala 2',
});
record('action-A','company-A','CIPA_ACAO',
 'Verificar extintor','Pendente',{
 mandateId:'mandate-A',description:'Extintor obstruído',
 dueDate:new Date(Date.now()+2*86400000).toISOString(),
});
record('document-private','company-A','CIPA_DOCUMENTO',
 'Documento restrito','Concluído',{
 mandateId:'mandate-A',memberPublished:false,
});
record('document-published','company-A','CIPA_DOCUMENTO',
 'Comunicado liberado','Concluído',{
 mandateId:'mandate-A',memberPublished:true,
 containsPersonalData:false,
});
record('mandate-B','company-B','CIPA_MANDATO','Mandato B','Ativo');
record('member-B','company-B','CIPA_MEMBRO','Outro integrante','Ativo',{
 mandateId:'mandate-B',workerId:'worker-B',cipaRole:'Titular',
 representation:'Empregados',
});
record('action-B','company-B','CIPA_ACAO','Dado de outra empresa',
 'Pendente',{mandateId:'mandate-B'});
// By default routes are disabled without the explicit script flag.
props.CIPA_MEMBER_V1_ENABLED='false';
assert.strictEqual(invoke('cipa_member_begin',{email:'maria@example.test'}).code,
 'FEATURE_DISABLED');
props.CIPA_MEMBER_V1_ENABLED='true';
assert.strictEqual(invoke('device_sync_pull'),null,
  'Outras rotas não devem ser interceptadas');

assert.strictEqual(invoke('cipa_member_admin_grant',{
  authToken:'invalid',companyId:'company-A',
  mandateId:'mandate-A',memberId:'member-A',
  workerId:'worker-A',email:'maria@example.test',
}).code,'ACCESS_DENIED');

assert.strictEqual(invoke('cipa_member_admin_grant',{
  authToken:'valid-admin',companyId:'company-B',
  mandateId:'mandate-A',memberId:'member-A',
  workerId:'worker-A',email:'maria@example.test',
}).code,'MEMBER_NOT_VERIFIED');

const grant=invoke('cipa_member_admin_grant',{
  authToken:'valid-admin',companyId:'company-A',
  mandateId:'mandate-A',memberId:'member-A',
  workerId:'worker-A',email:'maria@example.test',
});
assert.strictEqual(grant.ok,true);
const assignment=invoke('cipa_member_admin_assign',{
  authToken:'valid-admin',companyId:'company-A',
  mandateId:'mandate-A',memberId:'member-A',actionId:'action-A',
});
assert.strictEqual(assignment.ok,true);

const started=invoke('cipa_member_begin',{email:'maria@example.test'});
assert(started.ok);
assert.strictEqual(mail.length,1);
const pin=mail[0].body.match(/\b\d{8}\b/);
assert(pin,'A senha de uso único precisa ter 8 dígitos');
const rejected=invoke('cipa_member_verify',{email:'maria@example.test',code:'00000000'});
assert(!rejected.ok,'Código errado negado');
const login=invoke('cipa_member_verify',{email:'maria@example.test',code:pin[0]});
assert(login.ok,'Código válido e conta ativa entram');
assert(login.sessionToken&&login.sessionToken.length>=64);
const snapshot=invoke('cipa_member_dashboard',{sessionToken:login.sessionToken});
assert(snapshot.ok);
assert.strictEqual(snapshot.profile.fullName,'Maria Silva');
assert.strictEqual(snapshot.companyName,'Cerâmica de Exemplo');
assert.strictEqual(snapshot.mandateTitle,'CIPA 2026');
assert.strictEqual(snapshot.profile.cipaRole,'Vice-presidente');
assert(snapshot.meetings.some(x=>x.id==='meeting-A'));
assert(snapshot.meetings.every(x=>x.companyId==='company-A'&&
 x.mandateId==='mandate-A'&&x.assignedMemberId==='member-A'));
assert(snapshot.actions.every(x=>x.companyId==='company-A'&&
 x.mandateId==='mandate-A'&&x.assignedMemberId==='member-A'));
assert(snapshot.actions.some(x=>x.id==='action-A'));
assert(snapshot.reminders.some(x=>
  x.title.startsWith('Prazo próximo da ação: Verificar extintor')),
  'Lembrete de ação próxima somente do membro autorizado.');
assert(!JSON.stringify(snapshot).includes('Outra empresa'));
assert(!JSON.stringify(snapshot).includes('Documento restrito'));
assert(!snapshot.documents.some(x=>x.id==='document-published'),
  'Documento não é publicado só por um campo legado.');
assert(snapshot.notices.length===0,'Sem aviso criado, nenhuma publicação.');
assert.strictEqual(invoke('cipa_member_admin_publish_notice',{
  authToken:login.sessionToken,companyId:'company-A',
  mandateId:'mandate-A',title:'Reunião de Segurança',
  detail:'Teremos discussão sobre organização da fábrica.',
  confirmedPublic:true,
}).code,'ACCESS_DENIED','Membro não pode publicar avisos.');
assert.strictEqual(invoke('cipa_member_admin_publish_notice',{
  authToken:'valid-admin',companyId:'company-A',
  mandateId:'mandate-A',title:'Aviso de Exemplo',
  detail:'Esta mensagem precisa de confirmação explícita.'
}).code,'CONFIRM_PUBLICATION_REQUIRED');
const notice=invoke('cipa_member_admin_publish_notice',{
  authToken:'valid-admin',companyId:'company-A',
  mandateId:'mandate-A',title:'Reunião de Segurança',
  detail:'Teremos discussão sobre organização da fábrica.',
  confirmedPublic:true,
});
assert(notice.ok,'Aviso publicado pelo administrador.');
assert.strictEqual(invoke('cipa_member_admin_publish_document',{
  authToken:'valid-admin',companyId:'company-A',
  mandateId:'mandate-A',documentId:'document-published'
}).code,'CONFIRM_SAFE_METADATA_REQUIRED');
const document=invoke('cipa_member_admin_publish_document',{
  authToken:'valid-admin',companyId:'company-A',
  mandateId:'mandate-A',documentId:'document-published',
  confirmedSafeMetadata:true,
});
assert(document.ok,'Publicação de metadado com confirmação.');
const changed=invoke('cipa_member_dashboard',{sessionToken:login.sessionToken});
assert(changed.notices.some(x=>x.title==='Reunião de Segurança'));
assert(changed.documents.some(x=>x.id==='document-published'));
assert(!changed.documents.some(x=>x.id==='document-private'));
assert.strictEqual(invoke('cipa_member_admin_publish_document',{
  authToken:'valid-admin',companyId:'company-B',
  mandateId:'mandate-B',documentId:'document-published',
  confirmedSafeMetadata:true,
}).code,'DOCUMENT_NOT_ELIGIBLE','Não publicar documento de outra empresa.');
const listing=invoke('cipa_member_admin_publications',{
  authToken:'valid-admin',companyId:'company-A',mandateId:'mandate-A'
});
assert(listing.ok&&listing.documents.length===1&&listing.notices.length===1);
assert(invoke('cipa_member_admin_withdraw_notice',{
  authToken:'valid-admin',companyId:'company-A',mandateId:'mandate-A',
  noticeId:notice.id
}).ok);
assert(invoke('cipa_member_admin_unpublish_document',{
  authToken:'valid-admin',companyId:'company-A',mandateId:'mandate-A',
  documentId:'document-published'
}).ok);
const withdrawn=invoke('cipa_member_dashboard',{sessionToken:login.sessionToken});
assert(withdrawn.notices.length===0&&withdrawn.documents.length===0,
  'Retirada de publicação vale imediatamente.');
assert(!JSON.stringify(snapshot).includes('password_hash'));
assert(!JSON.stringify(snapshot).includes('syncKey'));
const forbidden=invoke('cipa_member_event',{
 sessionToken:login.sessionToken,kind:'progress',
 targetId:'action-B',detail:'Tentei editar outra empresa',
 requestId:'test-request-id-1234567890',
});
assert.strictEqual(forbidden.code,'ACCESS_DENIED');
const note=invoke('cipa_member_event',{
 sessionToken:login.sessionToken,kind:'progress',
 targetId:'action-A',detail:'O extintor foi desobstruído para conferência',
 requestId:'test-request-id-12345678901',
});
assert(note.ok);
const repeated=invoke('cipa_member_event',{
 sessionToken:login.sessionToken,kind:'progress',
 targetId:'action-A',detail:'O extintor foi desobstruído para conferência',
 requestId:'test-request-id-12345678901',
});
assert.strictEqual(repeated.duplicate,true,'Deduplicação por requestId');
const observed=invoke('cipa_member_event',{
 sessionToken:login.sessionToken,kind:'observation',
 location:'Produção',detail:'Caixas obstruindo parte do corredor',
 requestId:'test-request-id-12345678902',
});
assert(observed.ok);
const updated=invoke('cipa_member_dashboard',{sessionToken:login.sessionToken});
assert(updated.ok);
assert(updated.observations.some(x=>
  x.title.includes('Produção')&&x.description.includes('corredor')),
  'A pessoa deve consultar a própria observação em Minha CIPA.');
const inbox=invoke('cipa_member_admin_inbox',{
 authToken:'valid-admin',companyId:'company-A',
});
assert(inbox.ok&&inbox.events.length===2);
assert.strictEqual(invoke('cipa_member_admin_inbox',{
 authToken:login.sessionToken,companyId:'company-A',
}).code,'ACCESS_DENIED');

// Devolutivas: autorização, escopo, histórico e deduplicação obrigatórios.
const reviewFields={
  companyId:'company-A',mandateId:'mandate-A',
  observationId:'test-request-id-12345678902',
  status:'Em análise',message:'Conferência técnica em andamento.',
  requestId:'review-request-id-0000000001',
};
assert.strictEqual(invoke('cipa_member_admin_review_observation',{
  ...reviewFields,authToken:login.sessionToken,
}).code,'ACCESS_DENIED','Membro não responde ao próprio relato como ADM');
assert.strictEqual(invoke('cipa_member_admin_review_observation',{
  ...reviewFields,authToken:'invalid',
}).code,'ACCESS_DENIED','Sem conta ADM não há devolutiva');
assert.strictEqual(invoke('cipa_member_admin_review_observation',{
  ...reviewFields,authToken:'valid-admin',companyId:'company-B',
  mandateId:'mandate-B',
}).code,'NOT_FOUND','Devolutiva não cruza empresas');
assert.strictEqual(invoke('cipa_member_admin_review_observation',{
  ...reviewFields,authToken:'valid-admin',mandateId:'mandate-B',
}).code,'NOT_FOUND','Devolutiva não cruza mandatos');
assert.strictEqual(invoke('cipa_member_admin_review_observation',{
  ...reviewFields,authToken:'valid-admin',
  observationId:'test-request-id-12345678901',
}).code,'NOT_FOUND','Apenas observações podem receber devolutiva');
assert.strictEqual(invoke('cipa_member_admin_review_observation',{
  ...reviewFields,authToken:'valid-admin',status:'Concluído',
}).code,'INVALID_INPUT','Devolutiva não encerra NC automaticamente');
assert.strictEqual(invoke('cipa_member_admin_review_observation',{
  ...reviewFields,authToken:'valid-admin',status:'Orientação enviada',
  message:'',
}).code,'INVALID_INPUT','Orientação exige texto');
const firstReview=invoke('cipa_member_admin_review_observation',{
  ...reviewFields,authToken:'valid-admin',
});
assert(firstReview.ok&&!firstReview.duplicate);
const repeatReview=invoke('cipa_member_admin_review_observation',{
  ...reviewFields,authToken:'valid-admin',
});
assert.strictEqual(repeatReview.duplicate,true);
assert.strictEqual(invoke('cipa_member_admin_review_observation',{
  ...reviewFields,authToken:'valid-admin',status:'Orientação enviada',
}).code,'ID_REUSED','RequestId não pode mudar o conteúdo');
const afterReview=invoke('cipa_member_dashboard',{
  sessionToken:login.sessionToken,
});
const ownObservation=afterReview.observations.find(x=>x.id===
  'test-request-id-12345678902');
assert.strictEqual(ownObservation.status,'Em análise');
assert.strictEqual(ownObservation.feedback,'Conferência técnica em andamento.');
const reply=invoke('cipa_member_admin_review_observation',{
  ...reviewFields,authToken:'valid-admin',
  requestId:'review-request-id-0000000002',
  status:'Orientação enviada',
  message:'Verifique a passagem sem se aproximar de máquinas.',
});
assert(reply.ok);
const lastReview=invoke('cipa_member_dashboard',{
  sessionToken:login.sessionToken,
}).observations.find(x=>x.id==='test-request-id-12345678902');
assert.strictEqual(lastReview.status,'Orientação enviada');
assert.strictEqual(lastReview.feedback,
  'Verifique a passagem sem se aproximar de máquinas.');
assert.strictEqual(invoke('cipa_member_admin_inbox',{
  authToken:'valid-admin',companyId:'company-A',
  mandateId:'mandate-B',
}).events.length,0,'Caixa do técnico não mistura mandatos');
const reviewedInbox=invoke('cipa_member_admin_inbox',{
  authToken:'valid-admin',companyId:'company-A',
  mandateId:'mandate-A',
}).events.find(x=>x.id==='test-request-id-12345678902');
assert(reviewedInbox&&reviewedInbox.status==='Orientação enviada');
assert.strictEqual(reviewedInbox.feedback,lastReview.feedback);
assert(!JSON.stringify(lastReview).includes('admin@example.test'));

assert.strictEqual(lastReview.feedbackRead,false,
  'Orientação ainda não foi confirmada.');
assert.strictEqual(lastReview.reviewId,reply.reviewId,
  'Somente a revisão atual pode ser confirmada.');
const acknowledgement={
  sessionToken:login.sessionToken,
  observationId:'test-request-id-12345678902',
  reviewId:reply.reviewId,
  requestId:'feedback-read-request-12345678901',
};
assert.strictEqual(invoke('cipa_member_ack_feedback',{
  ...acknowledgement,sessionToken:'invalid',
}).code,'SESSION_INVALID','Sem sessão de membro não há ciência.');
assert.strictEqual(invoke('cipa_member_ack_feedback',{
  ...acknowledgement,observationId:'other-company-observation-888',
}).code,'ACCESS_DENIED','Não confirmar relato de outra empresa.');
assert.strictEqual(invoke('cipa_member_ack_feedback',{
  ...acknowledgement,reviewId:'review-stale-123456789012',
}).code,'REVIEW_NOT_CURRENT','Revisões antigas não recebem ciência.');
const reading=invoke('cipa_member_ack_feedback',acknowledgement);
assert(reading.ok&&reading.read===true,'Confirmação de leitura registrada.');
assert.strictEqual(invoke('cipa_member_ack_feedback',
  acknowledgement).duplicate,true,'Toques repetidos não duplicam a leitura.');
const afterRead=invoke('cipa_member_dashboard',{
  sessionToken:login.sessionToken,
}).observations.find(x=>x.id==='test-request-id-12345678902');
assert.strictEqual(afterRead.feedbackRead,true,
  'Membro vê que leu a resposta atual.');
assert.strictEqual(afterRead.status,'Orientação enviada',
  'Ciência não altera a avaliação do TST.');



// Um TST exige delegação explícita, mandato ativo e token com role próprio.
const reviewTstFields={
  authToken:'valid-tst',companyId:'company-A',mandateId:'mandate-A',
  observationId:'test-request-id-12345678902',
  status:'Orientação enviada',
  message:'Observe apenas de um local seguro; encaminhe ao responsável.',
  requestId:'tst-review-request-12345678901',
};
assert.strictEqual(invoke('cipa_tst_review_inbox',{
  authToken:'valid-tst',companyId:'company-A',mandateId:'mandate-A',
}).code,'ACCESS_DENIED','TST sem delegação não acessa relatos');
assert.strictEqual(invoke('cipa_tst_review_grant',{
  authToken:'valid-tst',userId:'tst-A',companyId:'company-A',
  mandateId:'mandate-A',operation:'grant',
}).code,'ACCESS_DENIED','TST não concede a si próprio');
assert(invoke('cipa_tst_review_grant',{
  authToken:'valid-admin',userId:'tst-A',companyId:'company-A',
  mandateId:'mandate-A',operation:'grant',
}).ok,'Administrador concede somente o escopo escolhido');
const tstStats=invoke('cipa_tst_metrics',{
  authToken:'valid-tst',companyId:'company-A',mandateId:'mandate-A',
});
assert(tstStats.ok&&tstStats.metrics.membersActive===1);
assert(tstStats.metrics.membersParticipating===1);
assert(tstStats.metrics.meetingsScheduled===1);
assert(tstStats.metrics.observationsPendingReview>=0);
assert.strictEqual(invoke('cipa_tst_metrics',{
  authToken:login.sessionToken,companyId:'company-A',mandateId:'mandate-A',
}).code,'ACCESS_DENIED','Integrante não lê métricas da equipe');
assert.strictEqual(invoke('cipa_tst_metrics',{
  authToken:'valid-tst',companyId:'company-B',mandateId:'mandate-B',
}).code,'ACCESS_DENIED','TST não lê métricas de outra empresa');
assert.strictEqual(invoke('cipa_tst_metrics',{
  authToken:'valid-admin',companyId:'company-B',mandateId:'mandate-A',
}).code,'MANDATE_INVALID','ADM só pode consultar mandato existente no escopo');
const tstInbox=invoke('cipa_tst_review_inbox',{
  authToken:'valid-tst',companyId:'company-A',mandateId:'mandate-A',
});
assert(tstInbox.ok&&tstInbox.events.length===1);
assert(tstInbox.events.every(e=>e.kind===undefined &&
  e.companyId==='company-A'&&e.mandateId==='mandate-A'));
assert.strictEqual(invoke('cipa_tst_review_inbox',{
  authToken:'valid-tst',companyId:'company-B',mandateId:'mandate-B',
}).code,'ACCESS_DENIED','TST não lê outra empresa');
assert.strictEqual(invoke('cipa_tst_review_observation',{
  ...reviewTstFields,companyId:'company-B',mandateId:'mandate-B',
}).code,'ACCESS_DENIED','TST não responde outra empresa');
assert.strictEqual(invoke('cipa_member_admin_review_observation',{
  ...reviewTstFields,
}).code,'ACCESS_DENIED','TST não utiliza endpoint de administrador');
const tstReviewed=invoke('cipa_tst_review_observation',reviewTstFields);
assert(tstReviewed.ok,'TST delegado pode responder relato autorizado');
const newer=invoke('cipa_member_dashboard',{
  sessionToken:login.sessionToken,
}).observations.find(x=>x.id==='test-request-id-12345678902');
assert.strictEqual(newer.feedbackRead,false,
  'Uma orientação posterior precisa de nova leitura.');
assert.notStrictEqual(newer.reviewId,reply.reviewId);
assert.strictEqual(invoke('cipa_member_ack_feedback',{
  ...acknowledgement,
  requestId:'feedback-read-request-12345678902',
}).code,'REVIEW_NOT_CURRENT',
  'Não é possível confirmar orientação substituída.');

const tstRepeat=invoke('cipa_tst_review_observation',reviewTstFields);
assert(tstRepeat.duplicate===true,'Reenvio seguro sem duplicação');
assert(invoke('cipa_tst_review_grant',{
  authToken:'valid-admin',userId:'tst-A',companyId:'company-A',
  mandateId:'mandate-A',operation:'revoke',
}).ok,'Administrador revoga a autorização');
assert.strictEqual(invoke('cipa_tst_review_observation',{
  ...reviewTstFields,requestId:'tst-review-request-12345678902',
}).code,'ACCESS_DENIED','Revogação vale para o próximo pedido');
assert.strictEqual(invoke('cipa_tst_review_inbox',{
  authToken:'valid-tst',companyId:'company-A',mandateId:'mandate-A',
}).code,'ACCESS_DENIED','Revogação bloqueia leitura também');

// Calendário: somente ADM agenda; apenas o membro vê o próprio evento.
const day=new Date(Date.now()+12*86400000).toISOString().slice(0,10);
const inspectionInput={
  authToken:'valid-admin',companyId:'company-A',mandateId:'mandate-A',
  memberId:'member-A',sector:'Cerâmica',dueDate:day,
  note:'Observe somente de local seguro.',
  requestId:'schedule-request-123456789012',
};
assert.strictEqual(invoke('cipa_schedule_create',{
  ...inspectionInput,authToken:login.sessionToken,
}).code,'ACCESS_DENIED');
assert.strictEqual(invoke('cipa_schedule_create',{
  ...inspectionInput,memberId:'member-B',
}).code,'MEMBERSHIP_INVALID','Não agendar membro de outra empresa');
assert.strictEqual(invoke('cipa_schedule_create',{
  ...inspectionInput,sector:'Entrada no forno quente',
}).code,'INVALID_INPUT','Temas indevidos não são aceitos');
const createdInspection=invoke('cipa_schedule_create',inspectionInput);
assert(createdInspection.ok&&createdInspection.id);
assert.strictEqual(invoke('cipa_schedule_create',inspectionInput).duplicate,true);
assert.strictEqual(invoke('cipa_schedule_create',{
  ...inspectionInput,sector:'Panificação',
}).code,'ID_REUSED','RequestId não muda o agendamento');
const scheduledDashboard=invoke('cipa_member_dashboard',{
  sessionToken:login.sessionToken,
});
assert(scheduledDashboard.scheduledInspections.some(x=>
  x.id===createdInspection.id&&x.title==='Vistoria: Cerâmica'));
assert(scheduledDashboard.scheduledInspections.every(x=>
  x.companyId==='company-A'&&x.mandateId==='mandate-A'&&
  x.assignedMemberId==='member-A'));
const scheduleObservation={
  sessionToken:login.sessionToken,kind:'observation',
  targetId:createdInspection.id,location:'Área industrial',
  detail:'Observação visual feita no local permitido para circulação.',
  requestId:'scheduled-report-request-12345678901',
};
assert.strictEqual(invoke('cipa_member_event',{
  ...scheduleObservation,targetId:'cipa-inspection-outra-empresa',
}).code,'ACCESS_DENIED','Não aceitar agenda de outro vínculo');
assert(invoke('cipa_member_event',scheduleObservation).ok);
assert.strictEqual(invoke('cipa_member_event',scheduleObservation).duplicate,true,
  'Retry do mesmo envio precisa ser idempotente');
assert.strictEqual(invoke('cipa_member_event',{
  ...scheduleObservation,detail:'Descrição adulterada e diferente.',
}).code,'ID_REUSED','RequestId repetido não troca o conteúdo');
assert.strictEqual(invoke('cipa_member_event',{
  ...scheduleObservation,requestId:'scheduled-report-request-12345678902',
}).code,'ALREADY_SUBMITTED','Um agendamento não recebe dois relatos');
const memberWithReport=invoke('cipa_member_dashboard',{
  sessionToken:login.sessionToken,
});
const linked=memberWithReport.scheduledInspections
  .find(x=>x.id===createdInspection.id);
assert.strictEqual(linked.status,'Registro enviado');
assert.strictEqual(linked.observationId,scheduleObservation.requestId);
// Fotos: nunca expor base64/links na listagem pública.
const jpg=Buffer.from([255,216,255,224,1,2,3,255,217]).toString('base64');
const photoRequest={
  sessionToken:login.sessionToken,observationId:scheduleObservation.requestId,
  jpegBase64:jpg,slot:1,
};
assert.strictEqual(invoke('cipa_member_photo_upload',photoRequest).code,
  'PHOTO_STORE_NOT_CONFIGURED','Falhar fechado sem pasta privada');
props.CIPA_MEMBER_PHOTO_FOLDER_ID='private-cipa-folder';
assert.strictEqual(invoke('cipa_member_photo_upload',{
  ...photoRequest,observationId:'other-company-observation',
}).code,'ACCESS_DENIED','Sem fotos de outros relatos');
assert.strictEqual(invoke('cipa_member_photo_upload',{
  ...photoRequest,jpegBase64:'bm90LWEtanBlZw==',
}).code,'INVALID_PHOTO','Recusar binário que não seja JPEG');
assert(invoke('cipa_member_photo_upload',photoRequest).ok);
assert.strictEqual(invoke('cipa_member_photo_upload',photoRequest).duplicate,true,
  'Mesmo conteúdo no mesmo slot não duplica');
assert.strictEqual(invoke('cipa_member_photo_upload',{
  ...photoRequest, jpegBase64:Buffer.from(
    [255,216,255,224,4,5,6,255,217]).toString('base64'),
}).code,'PHOTO_SLOT_USED','Slot preenchido não admite substituição');
assert(invoke('cipa_member_photo_upload',{
  ...photoRequest,slot:2,
}).ok,'Segundo slot permitido');
assert.strictEqual(invoke('cipa_member_photo_upload',{
  ...photoRequest,slot:3,
}).code,'INVALID_PHOTO','Não permitir terceira foto');
const myPhotos=invoke('cipa_member_photo_list',{
  sessionToken:login.sessionToken,
  observationId:scheduleObservation.requestId,
});
assert.deepStrictEqual(myPhotos.slots,[1,2]);
assert(!JSON.stringify(myPhotos).includes('file_id'));
const photoData=invoke('cipa_member_photo_get',{
  sessionToken:login.sessionToken,
  observationId:scheduleObservation.requestId,slot:1,
});
assert.strictEqual(photoData.jpegBase64,jpg);
assert.strictEqual(invoke('cipa_tst_photo_get',{
  authToken:'valid-tst',companyId:'company-A',mandateId:'mandate-A',
  observationId:scheduleObservation.requestId,slot:1,
}).code,'ACCESS_DENIED','TST sem delegação não visualiza fotos');
assert.strictEqual(invoke('cipa_tst_photo_get',{
  authToken:'valid-admin',companyId:'company-B',mandateId:'mandate-B',
  observationId:scheduleObservation.requestId,slot:1,
}).code,'ACCESS_DENIED','Admin não mistura escopo');
assert.strictEqual(invoke('cipa_tst_photo_get',{
  authToken:'valid-admin',companyId:'company-A',mandateId:'mandate-A',
  observationId:scheduleObservation.requestId,slot:1,
}).jpegBase64,jpg,'Acesso privilegiado validado por empresa/mandato');
photoStore.share='ANYONE';
assert.strictEqual(invoke('cipa_member_photo_get',{
  sessionToken:login.sessionToken,
  observationId:scheduleObservation.requestId,slot:1,
}).ok,false,'Pasta compartilhada deve bloquear leitura');
photoStore.share='PRIVATE';
assert(!JSON.stringify(invoke('cipa_member_dashboard',{
  sessionToken:login.sessionToken,
})).includes(jpg),'Dados binários não entram em listagens');
const adminSchedule=invoke('cipa_schedule_list',{
  authToken:'valid-admin',companyId:'company-A',mandateId:'mandate-A',
});
assert.strictEqual(adminSchedule.items
  .find(x=>x.id===createdInspection.id).observationId,
  scheduleObservation.requestId,'Central enxerga vínculo sem concluir ação');
assert.strictEqual(invoke('cipa_schedule_list',{
  authToken:login.sessionToken,companyId:'company-A',
  mandateId:'mandate-A',
}).code,'ACCESS_DENIED');
assert.strictEqual(invoke('cipa_schedule_cancel',{
  authToken:'valid-admin',companyId:'company-B',
  mandateId:'mandate-B',scheduleId:createdInspection.id,
}).code,'NOT_FOUND');
assert(invoke('cipa_schedule_cancel',{
  authToken:'valid-admin',companyId:'company-A',
  mandateId:'mandate-A',scheduleId:createdInspection.id,
}).ok,'Admin pode cancelar agendamento próprio');
assert(invoke('cipa_member_dashboard',{
  sessionToken:login.sessionToken,
}).scheduledInspections.length===0,'Cancelamento retira lembrete do membro');


// Mural interno, privado e moderado, isolado de vistorias e chats públicos.
const postInput={
  sessionToken:login.sessionToken,
  place:'Área industrial',
  detail:'Observada obstrução parcial do corredor; solicito avaliação.',
  requestId:'mural-post-12345678901234567890',
};
assert.strictEqual(invoke('cipa_mural_create',{
  ...postInput,sessionToken:'sem-sessao'
}).code,'ACCESS_DENIED');
assert.strictEqual(invoke('cipa_mural_create',{
  ...postInput,jpegBase64:'aW52YWxpZG8='
}).code,'INVALID_PHOTO');
assert(invoke('cipa_mural_create',postInput).ok);
assert.strictEqual(invoke('cipa_mural_create',postInput).duplicate,true);
assert.strictEqual(invoke('cipa_mural_create',{
  ...postInput,detail:'Tentativa de adulteração do ID'
}).code,'ID_REUSED'); // Mesmo ID com outra descrição não altera relato.
const secondMemberRecord={
  mandateId:'mandate-A',workerId:'worker-A2',cipaRole:'Titular',
  representation:'Empregados',
};
record('member-A2','company-A','CIPA_MEMBRO','Integrante de Teste','Ativo',
  secondMemberRecord);
const grantOther=invoke('cipa_member_admin_grant',{
  authToken:'valid-admin',companyId:'company-A',
  mandateId:'mandate-A',memberId:'member-A2',workerId:'worker-A2',
  email:'outro@example.test',
});
assert(grantOther.ok);
assert(invoke('cipa_member_begin',{email:'outro@example.test'}).ok);
const otherMail=mail.find(x=>x.to==='outro@example.test');
const otherCode=otherMail.body.match(/\b\d{8}\b/);
const otherLogin=invoke('cipa_member_verify',{
  email:'outro@example.test',code:otherCode[0],
});
assert(otherLogin.ok);
assert.strictEqual(invoke('cipa_mural_list',{
  sessionToken:otherLogin.sessionToken,
}).posts.length,0,'Post pendente não aparece para colega');
assert.strictEqual(invoke('cipa_mural_moderator_list',{
  authToken:login.sessionToken,companyId:'company-A',
  mandateId:'mandate-A',
}).code,'ACCESS_DENIED','Membro não se torna moderador');
assert.strictEqual(invoke('cipa_mural_moderator_list',{
  authToken:'valid-admin',companyId:'company-B',mandateId:'mandate-B'
}).posts.length,0,'Nenhum mural de outra empresa');
const modList=invoke('cipa_mural_moderator_list',{
  authToken:'valid-admin',companyId:'company-A',mandateId:'mandate-A'
});
assert.strictEqual(modList.posts[0].visibility,'Pendente');
assert.strictEqual(invoke('cipa_mural_moderate',{
  authToken:'valid-admin',companyId:'company-A',mandateId:'mandate-A',
  postId:postInput.requestId,visibility:'Aprovado',status:'Resolvido',
}).code,'CONFIRMATION_REQUIRED','Não concluir sem confirmação técnica');
assert(invoke('cipa_mural_moderate',{
  authToken:'valid-admin',companyId:'company-A',mandateId:'mandate-A',
  postId:postInput.requestId,visibility:'Aprovado',status:'Em análise',
}).ok);
const visible=invoke('cipa_mural_list',{
  sessionToken:otherLogin.sessionToken,
});
assert.strictEqual(visible.posts.length,1);
assert.strictEqual(visible.posts[0].isMine,false);
assert.strictEqual(visible.posts[0].detail,postInput.detail);
assert(!JSON.stringify(visible).includes('accountId')&&
  !JSON.stringify(visible).includes('memberId'),
  'Identificadores de membros não podem vazar para o mural');
const comment={
  sessionToken:otherLogin.sessionToken,postId:postInput.requestId,
  requestId:'mural-comment-1234567890123456789',
  body:'Esta passagem está sinalizada?',
};
assert(invoke('cipa_mural_comment',comment).ok);
assert.strictEqual(invoke('cipa_mural_comment',comment).duplicate,true);
const commentsBefore=invoke('cipa_mural_list',{
  sessionToken:login.sessionToken,
});
assert.strictEqual(commentsBefore.posts[0].comments.length,0,
  'Comentário pendente não fica público');
const muralReply=invoke('cipa_mural_reply',{
  authToken:'valid-admin',companyId:'company-A',mandateId:'mandate-A',
  postId:postInput.requestId,requestId:'mural-reply-1234567890123456789',
  body:'A equipe de SST vai avaliar a circulação.',
});
assert(muralReply.ok);
assert.strictEqual(invoke('cipa_mural_list',{
  sessionToken:login.sessionToken,
}).posts[0].comments.length,1,'Resposta técnica aparece');
assert(invoke('cipa_mural_moderate_comment',{
  authToken:'valid-admin',companyId:'company-A',mandateId:'mandate-A',
  commentId:comment.requestId,visibility:'Aprovado',
}).ok);
assert.strictEqual(invoke('cipa_mural_list',{
  sessionToken:login.sessionToken,
}).posts[0].comments.length,2);
assert.strictEqual(invoke('cipa_mural_moderate_comment',{
  authToken:'valid-admin',companyId:'company-B',mandateId:'mandate-B',
  commentId:comment.requestId,visibility:'Aprovado',
}).code,'NOT_FOUND','Sem moderação entre empresas');
assert.strictEqual(invoke('cipa_mural_create',{
  ...postInput,requestId:'mural-post-photo-1234567890123456',
  jpegBase64:jpg,
}).ok,true);
assert.strictEqual(invoke('cipa_mural_photo',{
  sessionToken:otherLogin.sessionToken,
  postId:'mural-post-photo-1234567890123456',
}).code,'NOT_FOUND','Foto pendente invisível a outros membros');
assert.strictEqual(invoke('cipa_mural_photo',{
  sessionToken:login.sessionToken,
  postId:'mural-post-photo-1234567890123456',
}).jpegBase64,jpg,'Autor vê foto própria pendente');
assert(invoke('cipa_mural_moderate',{
  authToken:'valid-admin',companyId:'company-A',mandateId:'mandate-A',
  postId:'mural-post-photo-1234567890123456',
  visibility:'Aprovado',status:'Em análise',
}).ok);
assert.strictEqual(invoke('cipa_mural_photo',{
  sessionToken:otherLogin.sessionToken,
  postId:'mural-post-photo-1234567890123456',
}).jpegBase64,jpg,'Foto aprovada visível só em escopo');
assert.strictEqual(invoke('cipa_mural_moderator_photo',{
  authToken:'valid-admin',companyId:'company-B',mandateId:'mandate-B',
  postId:'mural-post-photo-1234567890123456',
}).code,'NOT_FOUND');
assert(!JSON.stringify(invoke('cipa_mural_list',{
  sessionToken:login.sessionToken,
})).includes(jpg),'Fotos não são inseridas na listagem');
assert.strictEqual(invoke('cipa_mural_moderate',{
  authToken:'valid-admin',companyId:'company-A',mandateId:'mandate-A',
  postId:postInput.requestId,visibility:'Aprovado',
  status:'Resolvido',confirmedByResponsible:true,
}).status,'Resolvido');
assert.strictEqual(invoke('cipa_mural_moderate',{
  authToken:'valid-admin',companyId:'company-A',mandateId:'mandate-A',
  postId:postInput.requestId,visibility:'Não publicado',
  status:'Em análise',
}).visibility,'Não publicado');
assert(!invoke('cipa_mural_list',{
  sessionToken:otherLogin.sessionToken,
}).posts.some(x=>x.id===postInput.requestId),
  'Publicação ocultada não pode continuar no mural dos colegas');
assert.strictEqual(invoke('cipa_mural_comment',{
  ...comment,requestId:'mural-comment-1234567890123456780'
}).code,'NOT_FOUND','Sem comentários em post ocultado');

const revoke=invoke('cipa_member_admin_revoke',{
 authToken:'valid-admin',accountId:grant.id,
});
assert(revoke.ok);
assert.strictEqual(invoke('cipa_member_dashboard',{
 sessionToken:login.sessionToken,
}).code,'SESSION_INVALID','Revogação deve bloquear acesso já conectado');
const reactivate=invoke('cipa_member_admin_grant',{
  authToken:'valid-admin',companyId:'company-A',
  mandateId:'mandate-A',memberId:'member-A',
  workerId:'worker-A',email:'maria@example.test',
});
assert(reactivate.ok&&reactivate.reused===true);
assert.strictEqual(reactivate.id,grant.id,'Reativação não deve criar outro usuário');
assert.strictEqual(invoke('cipa_member_dashboard',{
  sessionToken:login.sessionToken,
}).code,'SESSION_INVALID',
  'A reativação nunca pode reviver sessão revogada');
console.log('CIPA_MEMBER_GATEWAY_ISOLATED_OTP_REVOKE_CROSS_COMPANY_OK');

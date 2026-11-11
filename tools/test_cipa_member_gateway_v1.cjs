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
const props={
  CIPA_MEMBER_V1_ENABLED:'true',
  CIPA_MEMBER_V1_PEPPER:'a-very-long-test-only-secret-do-not-copy-into-production-999999999',
};
const fakeAdmin={
  id:'admin-A',active:true,role:'admin',email:'admin@example.test',
};
const fakeTst={id:'tst-A',active:true,role:'tecnico',email:'tst@example.test'};
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
  Utilities:{
    DigestAlgorithm:{SHA_256:'SHA_256'},
    Charset:{UTF_8:'UTF_8'},
    getUuid:()=>crypto.randomUUID(),
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
  cipaMemV1TrustedTechnicalUserLookup_:(id)=>id==='tst-A'?fakeTst:null,
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
for(const moduleName of ['CipaMemberTechnicalPermissionsV1.gs',
    'CipaMemberSchedulesV1.gs']) {
  vm.runInContext(fs.readFileSync(path.join(
    root,'feature_sources',moduleName),'utf8'),scope,{filename:moduleName});
}
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


// Permissões TST: administrador concede acesso estritamente por empresa/mandato.
assert.strictEqual(invoke('cipa_member_tst_inbox',{
  authToken:'valid-tst',companyId:'company-A',mandateId:'mandate-A'
}).code,'ACCESS_DENIED','TST sem concessão não acessa relatos');
assert.strictEqual(invoke('cipa_member_admin_set_tst_permission',{
  authToken:'valid-tst',userId:'tst-A',
  companyId:'company-A',mandateId:'mandate-A',active:true,
}).code,'ACCESS_DENIED','TST não pode liberar o próprio acesso');
assert.strictEqual(invoke('cipa_member_admin_set_tst_permission',{
  authToken:'valid-admin',userId:'fake-user',
  companyId:'company-A',mandateId:'mandate-A',active:true,
}).code,'TECHNICIAN_NOT_VERIFIED','Não concede a usuário inexistente');
assert.strictEqual(invoke('cipa_member_admin_set_tst_permission',{
  authToken:'valid-admin',userId:'tst-A',
  companyId:'company-A',mandateId:'mandate-B',active:true,
}).code,'MANDATE_NOT_ACTIVE','Mandato não corresponde à empresa');
assert(invoke('cipa_member_admin_set_tst_permission',{
  authToken:'valid-admin',userId:'tst-A',
  companyId:'company-A',mandateId:'mandate-A',active:true,
}).ok);
const tstInbox=invoke('cipa_member_tst_inbox',{
  authToken:'valid-tst',companyId:'company-A',mandateId:'mandate-A'
});
assert(tstInbox.ok&&tstInbox.events.length===1);
assert(tstInbox.events.every(e=>e.kind==='observation'));
assert(!JSON.stringify(tstInbox).includes('action-B'));
assert.strictEqual(invoke('cipa_member_tst_inbox',{
  authToken:'valid-tst',companyId:'company-B',mandateId:'mandate-B'
}).code,'ACCESS_DENIED','TST não pode visualizar outra empresa');
assert.strictEqual(invoke('cipa_member_admin_inbox',{
  authToken:'valid-tst',companyId:'company-A',mandateId:'mandate-A'
}).code,'ACCESS_DENIED','TST não herda perfil ADM completo');
assert.strictEqual(invoke('cipa_member_admin_review_observation',{
  ...reviewFields,authToken:'valid-tst',
  requestId:'tst-review-0000000000001',
  status:'Em análise',message:'Conferência com gerente de setor.',
}).ok,true,'TST autorizado responde apenas à observação vinculada');
assert.strictEqual(invoke('cipa_member_admin_review_observation',{
  ...reviewFields,authToken:'valid-tst',
  requestId:'tst-review-0000000000002',
  companyId:'company-B',mandateId:'mandate-B',
}).code,'ACCESS_DENIED','Sem concessão para outra empresa');

// Programação: só TST autorizado ou ADM, com vínculo a membro ativo.
const when=new Date(Date.now()+2*86400000).toISOString();
const scheduleBase={companyId:'company-A',mandateId:'mandate-A',
  memberId:'member-A',location:'Produção',theme:'Organização e circulação',
  plannedAt:when,requestId:'schedule-request-00000001'};
assert.strictEqual(invoke('cipa_member_schedule_create',{
  ...scheduleBase,authToken:login.sessionToken
}).code,'ACCESS_DENIED','Membro não agenda vistoria por conta própria');
assert.strictEqual(invoke('cipa_member_schedule_create',{
  ...scheduleBase,authToken:'valid-tst',companyId:'company-B',
  mandateId:'mandate-B'
}).code,'ACCESS_DENIED');
const scheduled=invoke('cipa_member_schedule_create',{
  ...scheduleBase,authToken:'valid-tst'
});
assert(scheduled.ok&&scheduled.id);
assert.strictEqual(invoke('cipa_member_schedule_create',{
  ...scheduleBase,authToken:'valid-tst'
}).duplicate,true,'Criação repetida não duplica programação');
const agenda=invoke('cipa_member_schedule_list',{
  authToken:'valid-tst',companyId:'company-A',mandateId:'mandate-A'
});
assert(agenda.schedules.some(x=>x.id===scheduled.id));
const memberAgenda=invoke('cipa_member_dashboard',{
  sessionToken:login.sessionToken
});
assert(memberAgenda.reminders.some(x=>x.id===scheduled.id&&
  x.title.includes('Vistoria programada')));
assert.strictEqual(invoke('cipa_member_schedule_cancel',{
  authToken:login.sessionToken,companyId:'company-A',
  mandateId:'mandate-A',scheduleId:scheduled.id,
}).code,'ACCESS_DENIED');
assert.strictEqual(invoke('cipa_member_schedule_cancel',{
  authToken:'valid-tst',companyId:'company-B',
  mandateId:'mandate-B',scheduleId:scheduled.id,
}).code,'ACCESS_DENIED');
assert(invoke('cipa_member_schedule_cancel',{
  authToken:'valid-tst',companyId:'company-A',
  mandateId:'mandate-A',scheduleId:scheduled.id
}).ok);
assert(!invoke('cipa_member_dashboard',{sessionToken:login.sessionToken})
  .reminders.some(x=>x.id===scheduled.id));
assert(invoke('cipa_member_admin_set_tst_permission',{
  authToken:'valid-admin',userId:'tst-A',
  companyId:'company-A',mandateId:'mandate-A',active:false,
}).ok);
assert.strictEqual(invoke('cipa_member_tst_inbox',{
  authToken:'valid-tst',companyId:'company-A',mandateId:'mandate-A'
}).code,'ACCESS_DENIED','Acesso revogado bloqueia consulta imediatamente');
assert.strictEqual(invoke('cipa_member_schedule_create',{
  ...scheduleBase,authToken:'valid-tst',
  requestId:'schedule-request-00000002'
}).code,'ACCESS_DENIED','Revogação também bloqueia agendamento');

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

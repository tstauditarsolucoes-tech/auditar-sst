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
  authUserFromToken_:(token)=>token==='valid-admin'?fakeAdmin:null,
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
const invoke=(action,fields={})=>JSON.parse(JSON.stringify(
  scope.cipaMemV1Route_({action,...fields})));

const sync=sheet('SincronizacaoDispositivos',[
  'table_name','record_id','deleted','server_version',
  'source_device','source_platform','updated_at','payload_json',
  'company_id','updated_by_user'
]);
function record(id,company,type,title,status,fields={}){
 const payload={
   id,company_id:company,type,title,status,
   date:'2026-11-05',payload_json:JSON.stringify(fields),
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
assert.strictEqual(snapshot.profile.cipaRole,'Vice-presidente');
assert(snapshot.meetings.some(x=>x.id==='meeting-A'));
assert(snapshot.actions.some(x=>x.id==='action-A'));
assert(!JSON.stringify(snapshot).includes('Outra empresa'));
assert(!JSON.stringify(snapshot).includes('Documento restrito'));
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
const inbox=invoke('cipa_member_admin_inbox',{
 authToken:'valid-admin',companyId:'company-A',
});
assert(inbox.ok&&inbox.events.length===2);
assert.strictEqual(invoke('cipa_member_admin_inbox',{
 authToken:login.sessionToken,companyId:'company-A',
}).code,'ACCESS_DENIED');

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

import test from 'node:test';
import assert from 'node:assert/strict';
import {once} from 'node:events';
import {createApp} from './server.mjs';
import {legacyCompatibilityCapabilities,inspectLegacyManifest} from './legacyCompatibility.mjs';

const admin={role:'adm',companyId:'10000000-0000-4000-8000-000000000001'};
const manifest={
 marker:'SST_LEGACY_METADATA_ONLY',source:'legacy-device-sync-v1',platform:'android',
 tables:[
  {name:'companies',count:4,pendingDeletes:0},
  {name:'inspections',count:10,pendingDeletes:2},
  {name:'cipa_voters',count:5,pendingDeletes:0},
 ],
};
test('compatibilidade bloqueia uso real, sem ACK, com diagnostico de lacunas',()=>{
 const capabilities=legacyCompatibilityCapabilities(admin);
 assert.equal(capabilities.writeEnabled,false);
 assert.equal(capabilities.dataImportEnabled,false);
 const result=inspectLegacyManifest(admin,manifest);
 assert.equal(result.assessment,'BLOCKED_FOR_REAL_SYNC');
 assert.equal(result.safeToSwitchEndpoint,false);
 assert.equal(result.writesPerformed,0);
 assert.equal(result.localQueueAcknowledged,0);
 assert.equal(result.totals.records,19);
 assert.equal(result.totals.tablesWithoutTarget,1);
 assert.equal(result.tables[2].status,'NOT_IMPLEMENTED');
});
test('somente administrador enxerga metadados da compatibilidade',()=>{
 for(const role of ['cliente','tecnico','gestor']){
  assert.throws(()=>legacyCompatibilityCapabilities({role}),e=>e.status===403);
  assert.throws(()=>inspectLegacyManifest({role},manifest),e=>e.status===403);
 }
});
test('rejeita registros pessoais, tokens, payloads, tabelas desconhecidas e duplicadas',()=>{
 const bad=[
  {...manifest,syncKey:'segredo-legado'},
  {...manifest,changes:[{row:{email:'pessoa@exemplo.invalid'}}]},
  {...manifest,tables:[{name:'companies',count:1,pendingDeletes:0,rows:[{nome:'Pessoa'}]}]},
  {...manifest,tables:[{name:'users',count:1,pendingDeletes:0}]},
  {...manifest,tables:[{name:'companies',count:1,pendingDeletes:0},
                       {name:'companies',count:2,pendingDeletes:0}]},
  {...manifest,tables:[{name:'companies',count:1.3,pendingDeletes:0}]},
  {...manifest,tables:[]},
 ];
 for(const input of bad){
  assert.throws(()=>inspectLegacyManifest(admin,input),e=>e.status===422);
 }
});
async function withServer(app,fn){
 app.listen(0,'127.0.0.1');await once(app,'listening');
 try{await fn('http://127.0.0.1:'+app.address().port);}
 finally{await new Promise(r=>app.close(r));}
}
test('rotas protegidas continuam fail-closed sem login',async()=>{
 await withServer(createApp(),async base=>{
  for(const [method,path] of [
   ['GET','/api/v1/migration/compatibility'],
   ['POST','/api/v1/migration/compatibility/check'],
  ]){
   const res=await fetch(base+path,{method,headers:{
     'x-role':'adm','x-company-id':admin.companyId,
   }});
   assert.equal(res.status,401);
  }
 });
});
test('auditoria HTTP so retorna contagens sem tocar em banco real',async()=>{
 await withServer(createApp({resolvePrincipal:async()=>admin}),async base=>{
  const capabilities=await fetch(base+'/api/v1/migration/compatibility');
  assert.equal(capabilities.status,200);
  assert.equal((await capabilities.json()).writeEnabled,false);
  const checked=await fetch(base+'/api/v1/migration/compatibility/check',{
   method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(manifest),
  });
  assert.equal(checked.status,200);
  assert.equal((await checked.json()).safeToSwitchEndpoint,false);
  const unsafe=await fetch(base+'/api/v1/migration/compatibility/check',{
   method:'POST',headers:{'content-type':'application/json'},
   body:JSON.stringify({...manifest,photos:[{url:'https://drive.google.com/private'}]}),
  });
  assert.equal(unsafe.status,422);
 });
});

const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
let actor={id:'cliente-a',name:'Representante Vale do Leite',role:'cliente',
 clientPermissions:{tratativas:true,naoConformidades:true},companyIds:['vale']};
const data={vale:{payload:{openNonConformities:[{id:'exaustores',title:'Exaustores'},
 {id:'escada',title:'Escada de terceiro'}]}},
 other:{payload:{openNonConformities:[{id:'outra-nc'}]}}};
const rows=[],sheet={
 appendRow:r=>rows.push(r),
 getLastRow:()=>rows.length,
 getRange:(start,col,count,size)=>({getValues:()=>rows.slice(start-1,start-1+count)
  .map(row=>row.slice(col-1,col-1+size))})
};
const ctx={
 Date,JSON,String,Number,Array,Object,LockService:{getScriptLock:()=>({waitLock(){},releaseLock(){}})},
 Utilities:{getUuid:()=> 'test-uuid'},
 ensureAuthStorage_:()=>({getSheetByName:()=>rows.length?sheet:null,
   insertSheet:()=>sheet}),
 clientPortalAuthorizedUser_:()=>actor,
 userCanAccessCompany_:(user,id)=>user.role==='admin'||user.companyIds.includes(id),
 clientPortalPermissions_:perms=>perms||{},
 clientPortalFindSnapshot_:id=>data[id]||null,
 clientPortalRows_:(payload,names)=>payload.openNonConformities||[]
};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(__dirname,'../feature_sources/ClientPortalTreatments_v1.gs'),'utf8'),ctx);
const list=(c='vale',t='exaustores')=>ctx.clientPortalTreatmentList('token',c,t);
const post=(c='vale',t='exaustores',val={})=>
 ctx.clientPortalTreatmentPost('token',c,t,{
 requestId:'request_abc123',message:'Exaustores ligados pelo operador',type:'esclarecimento',...val});
assert.equal(list().ok,true);
assert.equal(list('other','outra-nc').code,'ACCESS_DENIED');
assert.equal(list('vale','inventada').code,'TOPIC_UNAVAILABLE');
assert.equal(post().ok,true);
assert.equal(list().events.length,1);
assert.equal(list('vale','escada').events.length,0);
assert.equal(post().duplicate,true);
assert.equal(post('vale','exaustores',{type:'eficacia_confirmada',requestId:'id_client_123'}).code,'TYPE_NOT_ALLOWED');
assert.equal(post('vale','exaustores',{type:'encaminhamento',requestId:'id_client_125'}).code,'TYPE_NOT_ALLOWED');
assert.equal(post('vale','exaustores',{responsible:'Sócio',requestId:'id_client_126'}).code,'TYPE_NOT_ALLOWED');
actor={id:'tecnico-1',name:'TST Auditar',role:'tecnico',companyIds:['vale']};
assert.equal(post('vale','exaustores',{type:'solicitar_verificacao',requestId:'id_staff_123',
 message:'Realizar verificação funcional com exaustores acionados.'}).ok,true);
assert.equal(post('vale','exaustores',{type:'encaminhamento',requestId:'id_staff_124',
 message:'Definir plano de ação e responsável.',dueDate:'2026-10-17',responsible:'Operações'}).ok,true);
assert.equal(post('vale','exaustores',{type:'eficacia_confirmada',requestId:'id_staff_125',
 message:'Correção verificada in loco por técnico responsável.'}).ok,true);
assert.equal(list().events.length,4);
assert.ok(rows.some(r=>String(r[6]).startsWith('{')));
actor={id:'cliente-a',role:'cliente',companyIds:['vale'],clientPermissions:{tratativas:false,naoConformidades:true}};
assert.equal(list().code,'ACCESS_DENIED');
actor=null;
assert.equal(list().code,'SESSION_INVALID');
console.log('CLIENT_TREATMENTS_V1: case scope, session, permissions, staff authority, idempotency, immutable events OK');

const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
let actor={id:'cliente-a',name:'Representante Vale do Leite',role:'cliente',
 clientPermissions:{tratativas:true,naoConformidades:true},companyIds:['vale']};
const data={vale:{payload:{openNonConformities:[{id:'exaustores',title:'Exaustores'},
 {id:'escada',title:'Escada de terceiro'}],
 resolvedNonConformities:[{id:'guardacorpo',title:'Guarda-corpo corrigido',status:'Concluída'}]}},
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
 authUserFromToken_:()=>null,
 userCanAccessCompany_:(user,id)=>user.role==='admin'||user.companyIds.includes(id),
 clientPortalPermissions_:perms=>perms||{},
 clientPortalFindSnapshot_:id=>data[id]||null,
 clientPortalRows_:(payload,names)=>{
  for(const key of names){if(Array.isArray(payload[key]))return payload[key];}
  return [];
 }
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
assert.equal(post('vale','exaustores',{message:'Outra mensagem com o mesmo requestId'}).code,'REQUEST_PAYLOAD_MISMATCH');
assert.equal(post('vale','exaustores',{type:'eficacia_confirmada',requestId:'id_client_123'}).code,'TYPE_NOT_ALLOWED');
assert.equal(post('vale','exaustores',{type:'encaminhamento',requestId:'id_client_125'}).code,'TYPE_NOT_ALLOWED');
assert.equal(post('vale','exaustores',{responsible:'Sócio',requestId:'id_client_126'}).code,'TYPE_NOT_ALLOWED');
const support=post('vale','GERAL',{type:'pedido_apoio',requestId:'client_support_01',
 message:'Precisamos de orientação da Auditar sobre a segurança no setor de produção.'});
assert.equal(support.ok,true);
assert.equal(post('vale','GERAL',{type:'informar_correcao',requestId:'client_wrong_01'}).code,'TOPIC_TYPE_INVALID');
const correction=post('vale','guardacorpo',{type:'informar_correcao',requestId:'client_fixed_01',
 message:'Guarda-corpo ajustado pela manutenção; solicitamos conferência.'});
assert.equal(correction.ok,true);
assert.equal(list('vale','guardacorpo').events.length,1);
assert.equal(post('vale','guardacorpo',{type:'pedido_apoio',requestId:'client_wrong_02'}).code,'TOPIC_TYPE_INVALID');
actor={id:'tecnico-1',name:'TST Auditar',role:'tecnico',companyIds:['vale']};
assert.equal(post('vale','exaustores',{type:'solicitar_verificacao',requestId:'id_staff_123',
 message:'Realizar verificação funcional com exaustores acionados.'}).ok,true);
assert.equal(post('vale','exaustores',{type:'encaminhamento',requestId:'id_staff_124',
 message:'Definir plano de ação e responsável.',dueDate:'2026-10-17',responsible:'Operações'}).ok,true);
assert.equal(post('vale','exaustores',{type:'eficacia_confirmada',requestId:'id_staff_125',
 message:'Correção verificada em visita técnica com registro documental e novo teste.',
 verificationMethod:'vistoria_in_loco'}).ok,true);
assert.equal(list().events.length,4);
const topics=ctx.clientTreatmentAppV2_({authToken:'token',mode:'topics',companyId:'vale'});
assert.equal(topics.ok,true);
assert.ok(topics.topics.some(t=>t.id==='exaustores'));
assert.ok(topics.topics.some(t=>t.id==='guardacorpo'&&t.status==='Concluída'));
assert.equal(ctx.clientTreatmentAppV2_({authToken:'token',mode:'topics',companyId:'other'}).code,'ACCESS_DENIED');
const inbox=ctx.clientPortalTreatmentInbox('token','vale');
assert.equal(inbox.ok,true);
assert.equal(inbox.summary.awaitingAuditar,2);
assert.equal(inbox.threads.find(t=>t.topicId==='exaustores').status,'Concluída');
assert.equal(ctx.clientPortalTreatmentInbox('token','other').code,'ACCESS_DENIED');
assert.equal(inbox.threads.find(t=>t.topicId==='GERAL').lastType,'pedido_apoio');
assert.equal(inbox.threads.find(t=>t.topicId==='guardacorpo').lastType,'informar_correcao');
assert.equal(post('vale','escada',{type:'eficacia_confirmada',requestId:'id_staff_noproof',
 message:'Concluída sem prova'}).code,'VERIFICATION_REQUIRED');
assert.ok(rows.some(r=>String(r[6]).startsWith('{')));
actor={id:'cliente-a',role:'cliente',companyIds:['vale'],clientPermissions:{tratativas:true,naoConformidades:false}};
const limited=ctx.clientPortalTreatmentTopics('token','vale');
assert.equal(limited.ok,true);
assert.equal(limited.topics.length,1);
assert.equal(limited.topics[0].id,'GERAL');
assert.equal(ctx.clientPortalTreatmentList('token','vale','exaustores').code,'ACCESS_DENIED');
assert.equal(ctx.clientPortalTreatmentList('token','vale','GERAL').ok,true);
actor={id:'cliente-a',role:'cliente',companyIds:['vale'],clientPermissions:{tratativas:false,naoConformidades:true}};
assert.equal(list().code,'ACCESS_DENIED');
actor=null;
assert.equal(list().code,'SESSION_INVALID');
console.log('CLIENT_TREATMENTS_V1: case scope, session, permissions, staff authority, idempotency, immutable events OK');

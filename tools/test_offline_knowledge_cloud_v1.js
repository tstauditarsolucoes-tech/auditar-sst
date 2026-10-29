// Regressão do backend de modelos - não precisa de acesso à Central real.
const assert=require('node:assert/strict'), vm=require('node:vm'), fs=require('node:fs');
let rows=[];
const sheet={
  getLastRow:()=>rows.length,
  appendRow:v=>rows.push(v),
  getRange:(row,col,n,width)=>({
    getValues:()=>rows.slice(row-1,row-1+n).map(r=>r.slice(col-1,col-1+width)),
    setValues:v=>{for(let i=0;i<v.length;i++)rows[row-1+i]=v[i]}
  })
};
let allowed=true;
const sandbox={
  authorizeMultiUserToken_:()=> allowed? {ok:true,user:{id:'tst-1',role:'tecnico',active:true}}:{ok:false,code:'AUTH_REQUIRED'},
  ensureAuthStorage_:()=>({
    getSheetByName:()=>rows.length ? sheet : null,
    insertSheet:()=>sheet
  }),
  LockService:{getScriptLock:()=>({waitLock(){},releaseLock(){}})},
  Date,Number,String,Array,Object,Error,RegExp
};
vm.createContext(sandbox);
const source=fs.readFileSync(require('node:path').join(__dirname,'../feature_sources/OfflineKnowledgeCloud_v1.gs'),'utf8');
vm.runInContext(source,sandbox);
const model={id:'auto-c3RvcHxlZmZlY3Q',ruleId:'stop',title:'Parada de emergência',
 description:'Botão de emergência inoperante',risk:'Movimento perigoso',
 possibleConsequence:'Esmagamento',recommendation:'Impedir uso inseguro.',
 priority:'Alta',baseVersion:0};
let r=sandbox.offlineKnowledgeSyncV1_({changes:[model]});
assert.equal(r.ok,true);assert.equal(r.accepted[0].version,1);
r=sandbox.offlineKnowledgeSyncV1_({changes:[{...model,recommendation:'Recomendação concorrente'}]});
assert.equal(r.conflicts[0].version,1);
assert.equal(r.items[0].recommendation,model.recommendation);
r=sandbox.offlineKnowledgeSyncV1_({changes:[{...model,baseVersion:1,recommendation:'Revisado'}]});
assert.equal(r.accepted[0].version,2);
assert.equal(r.items[0].recommendation,'Revisado');
allowed=false;
assert.equal(sandbox.offlineKnowledgeSyncV1_({changes:[]}).ok,false);
allowed=true;
assert.throws(()=>sandbox.offlineKnowledgeSyncV1_({changes:[{...model,title:'Empresa @pessoal'}]}),/identificável/);
assert.throws(()=>sandbox.offlineKnowledgeSyncV1_({changes:[{...model,ruleId:'../x'}]}),/Identificador/);
assert.equal(sandbox.offlineKnowledgeSyncV1_({changes:[]}).items.length,1);
console.log('OFFLINE_KNOWLEDGE_CLOUD_V1: ALL ASSERTIONS PASSED');
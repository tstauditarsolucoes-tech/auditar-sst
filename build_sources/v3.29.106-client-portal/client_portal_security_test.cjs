'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const src=fs.readFileSync(process.argv[2],'utf8');
const rows=[
 ['linkA','company-A','Empresa A',true,'2026-09-22T10:00:00Z',JSON.stringify({
  company:{id:'company-A',name:'Empresa A'},accessToken:'MUST_NOT_LEAK',
  summary:{conformity:81,openNcs:1},medicalExams:[{patient:'PRIVATE'}],
  nonConformities:[{id:'ncA',title:'Máquina sem proteção',description:'Pendência',priority:'alta'}],
  actions:[{id:'actA',title:'Instalar proteção'}],reports:[{id:'repA',title:'Relatório liberado'}]
 })],
 ['linkB','company-B','Empresa B',true,'2026-09-22T10:00:00Z',JSON.stringify({
  company:{id:'company-B',name:'Empresa B'},accessToken:'MUST_NOT_LEAK_B',
  summary:{conformity:70},nonConformities:[{id:'ncB',title:'Outra pendência'}]
 })]
];
const evidence=[['id','company_id','nc_id','user_id','created_at','note','drive_file_id','status','reviewed_at','reviewed_by']];
const userA={id:'userA',name:'Cliente A',email:'a@example.invalid',role:'cliente',active:true,
 allCompanies:false,companyIds:['company-A'],sessionPlatform:'client_portal',
 clientPermissions:{indicadores:true,naoConformidades:true,acoesCorretivas:true,relatorios:true,enviarEvidencia:true}};
const userB={...userA,id:'userB',name:'Cliente B',companyIds:['company-B']};
const admin={...userA,id:'admin',name:'Admin',role:'admin',allCompanies:true,companyIds:[]};
const actors={a:userA,b:userB,admin};
const logs=[];
function sheetOf(data,withHeader){
 return {
  getLastRow:()=>data.length+(withHeader?0:1),
  getDataRange:()=>({getValues:()=>withHeader?data:[['token','company_id','company_name','active','updated_at','payload_json'],...data]}),
  getRange:(row,col,numRows,cols)=>({
   getValues:()=>data.slice(row-(withHeader?1:2),row-(withHeader?1:2)+numRows).map(v=>v.slice(col-1,col-1+cols)),
   setValues:(items)=>{items.forEach((item,i)=>data[row-(withHeader?1:2)+i].splice(col-1,item.length,...item))},
   setValue:(value)=>{data[row-(withHeader?1:2)][col-1]=value}
  }),
  appendRow:row=>data.push(row)
 };
}
const sheets={PainelDados:sheetOf(rows,false),EvidenciasClientes:sheetOf(evidence,true)};
const context={
 console:{error:()=>{}},PANEL_SHEET:'PainelDados',
 Utilities:{getUuid:(()=>{let i=0;return()=> 'test-'+(++i)})()},
 getSheet_:name=>sheets[name],ensureAuthStorage_:()=>({}),
 ensureSheet_:(_ss,name,header)=>sheets[name]||(sheets[name]=sheetOf([header],true)),
 authUserFromToken_:token=>actors[token]||null,authLogout_:()=>({ok:true}),
 userCanAccessCompany_:(user,id)=>!!id&&(user.role==='admin'||user.companyIds.includes(id)),
 auditAuthEvent_:(user,action,kind,id,company)=>logs.push({user:user.id,action,company}),
 DriveApp:{getFileById:()=>{throw Error('No photo')}},
 PropertiesService:{getScriptProperties:()=>({getProperty:()=>''})}
};
vm.createContext(context);vm.runInContext(src,context,{filename:'ClientPortal.gs'});
const viewA=context.clientPortalData('a');
assert.equal(viewA.ok,true);
assert.deepEqual(Array.from(viewA.companies.map(x=>x.id)),['company-A']);
assert.equal(viewA.companies[0].nonConformities[0].id,'ncA');
assert.equal(viewA.companies[0].actions[0].id,'actA');
assert.equal(viewA.companies[0].reports[0].id,'repA');
assert.equal(JSON.stringify(viewA).includes('MUST_NOT_LEAK'),false);
assert.equal(JSON.stringify(viewA).includes('PRIVATE'),false);
assert.deepEqual(Array.from(context.clientPortalData('b').companies.map(x=>x.id)),['company-B']);
assert.equal(context.clientPortalData('invalid').ok,false);
assert.equal(context.clientPortalSubmitEvidence('a','company-B','ncB','fraud',null).ok,false);
assert.equal(context.clientPortalSubmitEvidence('a','company-A','ncB','foreign NC',null).ok,false);
assert.equal(context.clientPortalSubmitEvidence('b','company-A','ncA','fraud',null).ok,false);
const accepted=context.clientPortalSubmitEvidence('a','company-A','ncA','Proteção instalada',null);
assert.equal(accepted.ok,true);
assert.equal(accepted.status,'PENDENTE_VALIDACAO');
assert.equal(evidence[1][1],'company-A');
assert.equal(evidence[1][7],'PENDENTE_VALIDACAO');
assert.equal(context.clientPortalEvidenceQueue('b','company-A').ok,false);
assert.equal(context.clientPortalReviewEvidence('a',accepted.id,'VALIDADA').ok,false);
assert.equal(context.clientPortalReviewEvidence('admin',accepted.id,'VALIDADA').ok,true);
assert.equal(evidence[1][7],'VALIDADA');
assert.equal(rows[0][3],true,'validation never closes the NC');
actors.readOnly={...userA,id:'readOnly',clientPermissions:{...userA.clientPermissions,enviarEvidencia:false}};
assert.equal(context.clientPortalSubmitEvidence('readOnly','company-A','ncA','test',null).ok,false);
console.log('CLIENT_PORTAL_TESTS_OK: isolamento A/B, payload, evidencias e validacao');

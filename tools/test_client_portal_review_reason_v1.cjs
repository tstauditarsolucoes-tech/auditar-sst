#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync(process.argv[2]||
 'build_sources/v3.29.106-client-portal/ClientPortal.gs','utf8');

let actor={id:'tstA',role:'tecnico',active:true,sessionPlatform:'client_portal',
 companyIds:['A'],allCompanies:false};
const evidence=[
 ['E1','A','NC1','cA','2026-10-26','Foto da proteção','foto1','PENDENTE_VALIDACAO','',''],
 ['E2','B','NC2','cB','2026-10-26','Outra empresa','','REJEITADA','',''],
];
const reasons=[];
function view(arr,start,rows,col,count){
 return arr.slice(start-1,start-1+rows).map(x=>x.slice(col-1,col-1+count));
}
const evidenceSheet={
 getLastRow:()=>evidence.length+1,
 getRange(row,col,count,cols){
  return {
   getValues:()=>view(evidence,row-1,count,col,cols),
   setValues(values){values.forEach((v,i)=>v.forEach((value,j)=>{
     evidence[row-2+i][col-1+j]=value;
   }));}
  };
 }
};
const reasonSheet={
 getLastRow:()=>reasons.length+1,
 appendRow(row){reasons.push([...row]);},
 getRange(row,col,count,cols){return {
  getValues:()=>view(reasons,row-1,count,col,cols)
 };}
};
const store={getSheetByName:(name)=>name==='ClientPortalEvidenceReviewReasonsV1'?
 (reasons.length?reasonSheet:null):null};
const context=vm.createContext({console,Date,String,Array,Object,JSON,Number,Math});
vm.runInContext(source,context,{filename:'ClientPortal.gs'});
context.clientPortalAuthorizedUser_=()=>actor;
context.clientPortalEvidenceSheet_=()=>evidenceSheet;
context.ensureAuthStorage_=()=>store;
context.ensureSheet_=(_,name)=>{assert.equal(name,'ClientPortalEvidenceReviewReasonsV1');return reasonSheet};
context.userCanAccessCompany_=(user,cid)=>user.companyIds.includes(cid);
context.clientPortalPermissions_=()=>({enviarEvidencia:true});
context.auditAuthEvent_=()=>{};
const reject=(reason)=>context.clientPortalReviewEvidence('token','E1','REJEITADA',reason);
assert.equal(reject('curto').ok,false);
assert.equal(reasons.length,0);
assert.equal(evidence[0][7],'PENDENTE_VALIDACAO');
assert.equal(reject('Foto não mostra proteção recolocada').ok,true);
assert.equal(evidence[0][7],'REJEITADA');
assert.equal(evidence[0].length,10,'Legacy evidence remains 10 columns');
assert.equal(reasons.length,1);
assert.equal(reasons[0][1],'A');
assert.equal(reasons[0][2],'Foto não mostra proteção recolocada');
let tech=context.clientPortalEvidenceQueue('token','A');
assert.equal(tech.ok,true);
assert.equal(tech.evidences.length,1);
assert.equal(tech.evidences[0].reviewReason,reasons[0][2]);
actor={id:'cA',role:'cliente',active:true,sessionPlatform:'client_portal',
 companyIds:['A'],allCompanies:false};
const mine=context.clientPortalMyEvidence('token','A');
assert.equal(mine.ok,true);
assert.equal(mine.evidences.length,1);
assert.equal(mine.evidences[0].reviewReason,reasons[0][2]);
assert.equal(context.clientPortalMyEvidence('token','B').code,'ACCESS_DENIED');
assert.equal(context.clientPortalReviewEvidence('token','E2','VALIDADA').code,'ACCESS_DENIED');
console.log('CLIENT_EVIDENCE_REJECTION_REASON_TENANT_ISOLATION_OK');
console.log('LEGACY_EVIDENCE_TEN_COLUMN_SCHEMA_PRESERVED_OK');

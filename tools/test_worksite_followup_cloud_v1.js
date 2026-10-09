const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const pages=new Map();
function getSheet(name) {
 if(pages.has(name))return pages.get(name);
 const rows=[],sheet={
  appendRow:r=>rows.push(r),
  getLastRow:()=>rows.length,
  getRange:(row,col,amount,width)=>({
   getValues:()=>rows.slice(row-1,row-1+amount).map(r=>r.slice(col-1,col-1+width)),
   setValues:value=>{value.forEach((r,i)=>{rows[row-1+i]=r;});}
  })
 };
 pages.set(name,sheet);return sheet;
}
let signedIn=true,allowed=true;
const scope={Date,Number,String,RegExp,JSON,Error,Array,Object,
 authorizeMultiUserToken_:()=>signedIn?{ok:true,user:{id:'tst-1',role:'tecnico',active:true}}:{ok:false,code:'AUTH_REQUIRED'},
 userCanAccessCompany_:()=>allowed,
 ensureAuthStorage_:()=>({getSheetByName:name=>pages.get(name)||null,insertSheet:getSheet}),
 LockService:{getScriptLock:()=>({waitLock(){},releaseLock(){}})}
};
vm.createContext(scope);
vm.runInContext(fs.readFileSync(path.join(__dirname,'../feature_sources/WorksiteFollowupCloud_v1.gs'),'utf8'),scope);
const record={schemaVersion:1,phase:'Estrutura',status:'Em andamento',progress:35,
 responsible:'Engenheira responsável',nextVisit:'2026-10-10',
 targetDate:'2027-02-01',notes:'Revisar proteção coletiva',
 log:[{at:'2026-10-09T12:00:00Z',type:'Visita',note:'Inspeção de andaimes'}]};
const request={companyId:'obra-a',mode:'save',baseVersion:0,record};
let a=scope.worksiteFollowupCloudV1_({companyId:'obra-a',mode:'read'});
assert.equal(a.ok,true);assert.equal(a.record,null);assert.equal(a.version,0);
a=scope.worksiteFollowupCloudV1_(request);
assert.equal(a.ok,true);assert.equal(a.version,1);
assert.equal(a.record.log[0].note,'Inspeção de andaimes');
let b=scope.worksiteFollowupCloudV1_({...request,record:{...record,progress:70}});
assert.equal(b.ok,false);assert.equal(b.code,'WORKSITE_CONFLICT');assert.equal(b.record.progress,35);
a=scope.worksiteFollowupCloudV1_({...request,baseVersion:1,record:{...record,progress:70}});
assert.equal(a.ok,true);assert.equal(a.version,2);
a=scope.worksiteFollowupCloudV1_({companyId:'obra-b',mode:'read'});
assert.equal(a.record,null);
allowed=false;
assert.equal(scope.worksiteFollowupCloudV1_({companyId:'obra-a',mode:'read'}).code,'FORBIDDEN');
allowed=true;signedIn=false;
assert.equal(scope.worksiteFollowupCloudV1_({companyId:'obra-a',mode:'read'}).code,'AUTH_REQUIRED');
signedIn=true;
assert.throws(()=>scope.worksiteFollowupCloudV1_({...request,baseVersion:2,record:{...record,progress:999}}),/Avanço/);
assert.throws(()=>scope.worksiteFollowupCloudV1_({...request,baseVersion:2,record:{...record,log:[{at:'wrong',type:'Visita',note:'x'}]}}),/Diário/);
const big={...record,log:Array.from({length:80},(_,i)=>({at:'2026-10-09T12:00:00Z',type:'Visita',note:'A'.repeat(800)}))};
a=scope.worksiteFollowupCloudV1_({...request,baseVersion:2,record:big});
assert.equal(a.ok,true);
assert.equal(a.record.log.length,80);
assert.ok(pages.get('AUDITAR_WORKSITE_FOLLOWUP_V1').getLastRow()>=2);
console.log('WORKSITE_CLOUD_V1: ACCESS, CONFLICTS, ISOLATION, FULL DIARY AND LIMITS OK');
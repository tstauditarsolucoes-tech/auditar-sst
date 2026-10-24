const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const now=Date.now(),ago=n=>new Date(now-n*60000).toISOString(),later=n=>new Date(now+n*60000).toISOString();
const users=[
{id:'t1',role:'tecnico',active:true,name:'Tecnico 1',lastLoginAt:ago(3)},
{id:'t2',role:'tecnico',active:true,name:'Tecnico 2',lastLoginAt:ago(80)},
{id:'adm',role:'admin',active:true,name:'ADM'}];
const sessions=[
['token1','t1','','android','',ago(10),later(100),false],
['token2','t2','','windows','',ago(40),later(100),false],
['expired','t2','','android','',ago(1),ago(1),false]];
const events=[
[ago(20),'t1','','record_sync','inspections','','C1','','android',''],
[ago(19),'t1','','record_sync','non_conformities','','C1','','android',''],
[ago(18),'t1','','record_sync','evidence_photos','','C1','','android',''],
[ago(18),'t2','','record_sync','workers','','C2','','windows',''],
[ago(2),'t2','','record_sync','unknown','','C2','','windows',''],
[ago(1),'adm','','record_sync','inspections','','C1','','windows','']];
function sheet(rows){return {getLastRow:()=>rows.length+1,
getRange:(row,col,length,width)=>({getValues:()=>
rows.slice(row-2,row-2+length).map(x=>x.slice(col-1,col-1+width))})};}
const sandbox={AUTH_SESSIONS_SHEET:'sessions',AUTH_AUDIT_SHEET:'audit',
authUserFromToken_:token=>token==='adm'?users[2]:token==='t1'?users[0]:null,
ensureAuthStorage_:()=>({getSheetByName:name=>name==='sessions'?sheet(sessions):name==='audit'?sheet(events):null}),
readAuthUsers_:()=>users,Date,Object,Array,String,Number,Math};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync('feature_sources/TechnicianSupervisionCloud_v1.gs','utf8'),sandbox);
const run=(authToken,more={})=>JSON.parse(JSON.stringify(sandbox.technicianSupervisionV1_({authToken,...more})));
assert.equal(run('t1').code,'ACCESS_DENIED');
assert.equal(run('invalid').code,'ACCESS_DENIED');
assert.equal(run('adm',{days:91}).code,'INVALID_FILTER');
assert.equal(run('adm',{limit:201}).code,'INVALID_FILTER');
const out=run('adm');
assert.equal(out.ok,true);
assert.equal(out.technicians.length,2);
assert.equal(out.summary.recent,1);
assert.equal(out.events.length,4);
const a=out.technicians.find(x=>x.id==='t1'),b=out.technicians.find(x=>x.id==='t2');
assert.equal(a.status,'Ativo recentemente');
assert.equal(a.lastActivityAt,users[0].lastLoginAt);
assert.equal(a.productivity.inspections,1);
assert.equal(a.productivity.nonConformities,1);
assert.equal(a.productivity.photos,1);
assert.equal(b.status,'Ausente');
assert.equal(b.productivity.other,1);
assert.equal(out.events.some(x=>x.userId==='adm'||x.entityType==='unknown'),false);
console.log('SUPERVISION_TESTS_PASSED');

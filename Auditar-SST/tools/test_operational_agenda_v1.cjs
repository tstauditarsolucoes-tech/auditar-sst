const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const tables=new Map();
function sheet(name){
 if(!tables.has(name))tables.set(name,{rows:[]});
 const entry=tables.get(name);
 return {
   getLastRow(){return entry.rows.length+1;},
   appendRow(row){entry.rows.push([...row]);},
   getRange(row,col,count,width){
     return {
       getValues(){return entry.rows.slice(row-2,row-2+count).map(x=>x.slice(col-1,col-1+width));},
       setValues(values){
         for(let i=0;i<values.length;i++)
           for(let j=0;j<values[i].length;j++)
             entry.rows[row-2+i][col-1+j]=values[i][j];
       }
     };
   }
 };
}
const ss={getSheetByName:sheet};
const actors={
  adm:{id:'admin',role:'admin',active:true,allCompanies:true,companyIds:[]},
  t1:{id:'t1',role:'tecnico',active:true,allCompanies:false,companyIds:['C1']},
  t2:{id:'t2',role:'tecnico',active:true,allCompanies:false,companyIds:['C2']}
};
let uuid=0,lockCount=0;
const sandbox={
  ensureAuthStorage_:()=>ss,
  ensureSheet_:(ss,name)=>sheet(name),
  authUserFromToken_:(token)=>actors[token]||null,
  readAuthUsers_:()=>Object.values(actors),
  userCanAccessCompany_:(u,id)=>u.role==='admin'||u.companyIds.includes(id),
  LockService:{getScriptLock:()=>({tryLock(){lockCount++;return true;},releaseLock(){lockCount--;}})},
  Utilities:{getUuid:()=>('id-'+(++uuid))},Date,Number,String,Object,Array,isFinite,console
};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync('feature_sources/OperationalAgendaV1.gs','utf8'),sandbox,
 {filename:'OperationalAgendaV1.gs'});
const run=(token,operation,other={})=>JSON.parse(JSON.stringify(
 sandbox.agendaTecnicosV1_({authToken:token,operation,...other})));
assert.equal(run('', 'list').code,'AUTH_REQUIRED');
assert.equal(run('unknown','list').code,'ACCESS_DENIED');
const payload={
 companyId:'C1',technicianId:'t1',title:'Visita técnica programada',
 scheduledAt:'2026-11-04T08:00:00-03:00',
 dueAt:'2026-11-04T11:00:00-03:00',requestId:'request-one'
};
assert.equal(run('t1','create',payload).code,'ACCESS_DENIED');
assert.equal(run('adm','create',{...payload,technicianId:'t2'}).code,'INVALID_TECHNICIAN');
assert.equal(run('adm','create',{...payload,scheduledAt:'invalid'}).code,'INVALID_INPUT');
const created=run('adm','create',payload);
assert.equal(created.ok,true);
assert.equal(created.task.status,'planned');
assert.equal(run('adm','create',payload).idempotent,true);
assert.equal(run('adm','create',{...payload,title:'Outro serviço'}).code,'IDEMPOTENCY_CONFLICT');
assert.equal(run('adm','create',{...payload,dueAt:'2026-11-04T12:00:00-03:00'}).code,
  'IDEMPOTENCY_CONFLICT');
assert.equal(run('adm','list').tasks.length,1);
assert.equal(run('t1','list').tasks.length,1);
assert.equal(run('t2','list').tasks.length,0);
assert.equal(run('t2','list',{companyId:'C1'}).tasks.length,0);
assert.equal(run('t2','status',{taskId:created.task.id,status:'done',reason:'Concluí a visita'}).code,'ACCESS_DENIED');
assert.equal(run('t1','status',{taskId:created.task.id,status:'blocked',reason:'x'}).code,'REASON_REQUIRED');
const blocked=run('t1','status',{taskId:created.task.id,status:'blocked',reason:'Acesso impedido'}); 
assert.equal(blocked.task.status,'blocked');
assert.equal(run('t1','status',{taskId:created.task.id,status:'cancelled'}).code,'INVALID_TRANSITION');
const done=run('t1','status',{taskId:created.task.id,status:'done',reason:'Atividade realizada'});
assert.equal(done.task.status,'done');
assert.equal(run('t1','status',{taskId:created.task.id,status:'in_progress'}).code,'INVALID_TRANSITION');
assert.equal(tables.get('AgendaTecnicosV1').rows.length,1);
assert.equal(tables.get('AgendaTecnicosEventosV1').rows.length,3);
assert.equal(lockCount,0);
console.log('AGENDA_V1_TESTS_PASSED',JSON.stringify({tasks:1,events:3,idempotent:true,access:'scoped'}));

// Validacao HTTP do servidor de homologacao privado dentro da CI descartavel.
import assert from 'node:assert/strict';
const origin='https://homologacao-ci.auditarsolucoes.invalid';
if (process.env.AUDITAR_SST_EPHEMERAL_CI_DB!=='FAKE_DATA_CI_ONLY') {
  throw new Error('Smoke privado permitido somente CI efemera');
}
const base='http://127.0.0.1:3000/api/v1/';
const health=await fetch(base+'health');
assert.equal(health.status,200);
assert.equal((await health.json()).productionDataConnected,false);
const unauth=await fetch(base+'auth/session');
assert.equal(unauth.status,401);
const login=await fetch(base+'auth/login',{
  method:'POST',
  headers:{'content-type':'application/json',origin},
  body:JSON.stringify({email:'tecnico-ci-a@example.invalid',password:'SenhaFicticiaCI-2026!'}),
});
assert.equal(login.status,200,'Login no container privado deve estar ativo na CI');
const session=await login.json();
const cookie=login.headers.get('set-cookie').split(';')[0];
assert.equal(session.role,'tecnico');
const nc=await fetch(base+'nonconformities',{headers:{cookie}});
assert.equal(nc.status,200);
const inspectionUnauthorized=await fetch(base+'inspections',{headers:{
  'x-company-id':'20000000-0000-4000-8000-000000000002','x-role':'adm',
}});
assert.equal(inspectionUnauthorized.status,401);
const inspectionPayload={
  inspectionType:'vistoria',title:'Teste HTTP ficticio CI',sector:'Setor sintético',
  location:'Local ficticio',description:'Somente CI',
  clientRequestId:'98000000-0000-4000-8000-000000000001',
};
const headers={'content-type':'application/json',cookie,origin,'x-csrf-token':session.csrfToken};
const createdInspection=await fetch(base+'inspections',{
  method:'POST',headers,body:JSON.stringify(inspectionPayload),
});
assert.equal(createdInspection.status,201);
const inspectionId=(await createdInspection.json()).item.id;
const duplicateInspection=await fetch(base+'inspections',{
  method:'POST',headers,body:JSON.stringify(inspectionPayload),
});
assert.equal((await duplicateInspection.json()).item.id,inspectionId);
const findingResponse=await fetch(base+'inspections/'+inspectionId+'/findings',{
  method:'POST',headers,body:JSON.stringify({
    shortTitle:'Extintor ficticio',description:'Vencido apenas no teste',
    probability:4,severity:4,clientRequestId:'98000000-0000-4000-8000-000000000002',
  }),
});
assert.equal(findingResponse.status,201);
const completedInspection=await fetch(base+'inspections/'+inspectionId+'/complete',{
  method:'POST',headers,
});
assert.equal(completedInspection.status,200);
const detailInspection=await fetch(base+'inspections/'+inspectionId,{headers:{cookie}});
assert.equal(detailInspection.status,200);
const detail=(await detailInspection.json());
assert.equal(detail.inspection.status,'concluida');
assert.equal(detail.findings.length,1);
const privateTask=await fetch(base+'tasks',{
  method:'POST',headers,body:JSON.stringify({
    title:'Agenda HTTP ficticia CI',description:'Apenas ambiente descartavel',
    priority:'media',clientRequestId:'96000000-0000-4000-8000-000000000001',
  }),
});
assert.equal(privateTask.status,201);
const taskId=(await privateTask.json()).item.id;
const taskList=await fetch(base+'tasks',{headers:{cookie}});
assert.equal(taskList.status,200);
assert.ok((await taskList.json()).items.some(t=>t.id===taskId));
const taskStarted=await fetch(base+'tasks/'+taskId+'/status',{
  method:'POST',headers,body:JSON.stringify({status:'em_andamento',message:'Inicio CI'}),
});
assert.equal(taskStarted.status,200);
const taskDone=await fetch(base+'tasks/'+taskId+'/status',{
  method:'POST',headers,body:JSON.stringify({status:'concluida',message:'Fim CI'}),
});
assert.equal(taskDone.status,200);
const taskDetail=await fetch(base+'tasks/'+taskId,{headers:{cookie}});
assert.equal(taskDetail.status,200);
assert.deepEqual((await taskDetail.json()).events.map(e=>e.kind),
  ['criada','em_andamento','concluida']);
const dashboard=await fetch(base+'portal/dashboard',{headers:{cookie}});
assert.equal(dashboard.status,200);
const visible=(await dashboard.json()).pending;
assert.ok(visible.some(item=>item.id===detail.findings[0].id));
const support=await fetch(base+'portal/threads',{
  method:'POST',headers,body:JSON.stringify({
    subject:'Atendimento HTTP ficticio',message:'Preciso de apoio de teste',
    clientRequestId:'a9000000-0000-4000-8000-000000000001',
  }),
});
assert.equal(support.status,201);
const ticketId=(await support.json()).item.id;
const messages=await fetch(base+'portal/threads/'+ticketId,{headers:{cookie}});
assert.equal(messages.status,200);
assert.equal((await messages.json()).messages.length,1);
const heartbeat=await fetch(base+'activity/ping',{
  method:'POST',headers,body:'{}',
});
assert.equal(heartbeat.status,200);
const logout=await fetch(base+'auth/logout',{
  method:'POST',headers:{cookie,origin,'x-csrf-token':session.csrfToken},
});
assert.equal(logout.status,200);
const revoked=await fetch(base+'auth/session',{headers:{cookie}});
assert.equal(revoked.status,401);
const afterLogout=await fetch(base+'inspections',{headers:{cookie}});
assert.equal(afterLogout.status,401);
const taskAfterLogout=await fetch(base+'tasks',{headers:{cookie}});
assert.equal(taskAfterLogout.status,401);
process.stdout.write('PRIVATE_AUTH_BOOTSTRAP_SMOKE_OK\n');

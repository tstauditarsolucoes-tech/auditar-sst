// SOMENTE CI DESCARTAVEL: agenda SST com empresas e pessoas inteiramente ficticias.
import assert from 'node:assert/strict';
import test from 'node:test';
import pg from 'pg';
import {createTaskService} from './taskService.mjs';
import {ApiError} from './ncService.mjs';

const companyA='10000000-0000-4000-8000-000000000001';
const companyB='20000000-0000-4000-8000-000000000002';
const techA={companyId:companyA,userId:'11000000-0000-4000-8000-000000000001',role:'tecnico'};
const clientA={companyId:companyA,userId:'11000000-0000-4000-8000-000000000002',role:'cliente'};
const managerA={companyId:companyA,userId:'33000000-0000-4000-8000-000000000003',role:'gestor'};
const techB={companyId:companyB,userId:'22000000-0000-4000-8000-000000000002',role:'tecnico'};
test('agenda: gestor atribui, tecnico acompanha, escopo e eventos preservados',async()=>{
  assert.equal(process.env.AUDITAR_SST_EPHEMERAL_CI_DB,'FAKE_DATA_CI_ONLY');
  assert.equal(process.env.PGHOST,'db');
  assert.equal(process.env.PGDATABASE,'auditar_web_hml');
  assert.equal(process.env.PGUSER,'sst_ci_runner');
  const pool=new pg.Pool({max:2,connectionTimeoutMillis:5000});
  try{
    const roles=await pool.query('SELECT current_user,rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user');
    assert.equal(roles.rows[0].current_user,'sst_ci_runner');
    assert.equal(roles.rows[0].rolsuper,false);
    assert.equal(roles.rows[0].rolbypassrls,false);
    const service=createTaskService(pool);
    const assignees=await service.assignees(managerA);
    assert.ok(assignees.some(a=>a.user_id===techA.userId));
    assert.ok(!assignees.some(a=>a.user_id===techB.userId));
    await assert.rejects(service.assignees(clientA),e=>e.status===403);
    const dueAt='2026-11-03T09:00:00.000Z';
    const taskPayload={
      title:'Verificar extintor ficticio',description:'Visita tecnica de homologacao',
      priority:'alta',dueAt,assignedTo:techA.userId,
      clientRequestId:'97000000-0000-4000-8000-000000000001',
    };
    const created=await service.create(managerA,taskPayload);
    assert.equal(created.status,'aberta');
    assert.equal((await service.create(managerA,taskPayload)).id,created.id);
    await assert.rejects(service.create(managerA,{...taskPayload,title:'Outro'}),
      e=>e.code==='IDEMPOTENCY_CONFLICT');
    await assert.rejects(service.create(managerA,{
      ...taskPayload,clientRequestId:'97000000-0000-4000-8000-000000000002',
      assignedTo:techB.userId,
    }),e=>e.code==='INVALID_ASSIGNEE');
    await assert.rejects(service.create(techA,{
      ...taskPayload,clientRequestId:'97000000-0000-4000-8000-000000000003',
      assignedTo:managerA.userId,
    }),e=>e.status===403);
    await assert.rejects(service.list(clientA),e=>e.status===403);
    assert.equal((await service.list(techA)).length,1);
    assert.deepEqual(await service.list(techB),[]);
    await assert.rejects(service.get(techB,created.id),e=>e.status===404);
    await assert.rejects(service.edit(techA,created.id,{...taskPayload,expectedRevision:1}),
      e=>e.status===403);
    await assert.rejects(service.edit(managerA,created.id,{...taskPayload,expectedRevision:99}),
      e=>e.code==='STALE_REVISION');
    const edited=await service.edit(managerA,created.id,{
      ...taskPayload,title:'Verificar extintor revisado',expectedRevision:1,
    });
    assert.equal(edited.revision,2);
    const started=await service.status(techA,created.id,{
      status:'em_andamento',message:'Inspecao ficticia iniciada',
    });
    assert.equal(started.status,'em_andamento');
    await assert.rejects(service.status(techB,created.id,{status:'concluida'}),
      e=>e.status===404);
    const ended=await service.status(techA,created.id,{
      status:'concluida',message:'Concluido para teste',
    });
    assert.equal(ended.status,'concluida');
    await assert.rejects(service.status(techA,created.id,{status:'em_andamento'}),
      e=>e.code==='INVALID_STATE');
    const detail=await service.get(managerA,created.id);
    assert.equal(detail.task.title,'Verificar extintor revisado');
    assert.ok(detail.task.completed_at);
    assert.deepEqual(detail.events.map(event=>event.kind),[
      'criada','editada','em_andamento','concluida',
    ]);
    assert.deepEqual(await service.list(techB),[]);
    const selfTask=await service.create(techA,{
      title:'Autoagenda ficticia',description:'',priority:'baixa',
      clientRequestId:'97000000-0000-4000-8000-000000000004',
    });
    assert.equal(selfTask.assigned_to,techA.userId);
    await assert.rejects(service.status(managerA,selfTask.id,{
      status:'cancelada',message:' ',
    }),e=>e.status===400);
    assert.equal((await service.status(managerA,selfTask.id,{
      status:'cancelada',message:'Reagendamento ficticio',
    })).status,'cancelada');
  }finally{await pool.end();}
});

// APENAS CI EFEMERA: Plano de Acao novo, sem importar dados legados.
import test from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import {createActionPlanService} from './actionPlanService.mjs';
import {createNcService} from './ncService.mjs';

const A='10000000-0000-4000-8000-000000000001';
const B='20000000-0000-4000-8000-000000000002';
const techA={companyId:A,userId:'11000000-0000-4000-8000-000000000001',role:'tecnico'};
const clientA={companyId:A,userId:'11000000-0000-4000-8000-000000000002',role:'cliente'};
const managerA={companyId:A,userId:'33000000-0000-4000-8000-000000000003',role:'gestor'};
const techB={companyId:B,userId:'22000000-0000-4000-8000-000000000002',role:'tecnico'};

test('Plano de Acao: RLS, NC, responsavel, revisao, status e reenvio seguro',async()=>{
 assert.equal(process.env.AUDITAR_SST_EPHEMERAL_CI_DB,'FAKE_DATA_CI_ONLY');
 assert.equal(process.env.PGHOST,'db');
 assert.equal(process.env.PGDATABASE,'auditar_web_hml');
 assert.equal(process.env.PGUSER,'sst_ci_runner');
 const pool=new pg.Pool({max:2,connectionTimeoutMillis:5000});
 try{
  const identity=await pool.query('SELECT current_user,rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user');
  assert.equal(identity.rows[0].current_user,'sst_ci_runner');
  assert.equal(identity.rows[0].rolsuper,false);
  assert.equal(identity.rows[0].rolbypassrls,false);
  const ncService=createNcService(pool);
  const planService=createActionPlanService(pool);
  const ncA=await ncService.create(techA,{
   shortTitle:'Extintor vencido ficticio',description:'Ocorrencia de teste A',
   probability:4,severity:4,
  });
  const ncB=await ncService.create(techB,{
   shortTitle:'Protecao ausente ficticia',description:'Ocorrencia de teste B',
   probability:5,severity:5,
  });
  const draft={
   nonConformityId:ncA.id,title:'Substituir extintor ficticio',
   description:'Fotografar novo equipamento apos vistoria de teste',
   assignedTo:techA.userId,dueAt:'2026-11-05T18:00:00.000Z',
   clientRequestId:'96000000-0000-4000-8000-000000000001',
  };
  await assert.rejects(planService.list(clientA),e=>e.status===403);
  await assert.rejects(planService.create(clientA,draft),e=>e.status===403);
  await assert.rejects(planService.create(managerA,{...draft,
   nonConformityId:ncB.id,clientRequestId:'96000000-0000-4000-8000-000000000002'
  }),e=>e.status===404);
  await assert.rejects(planService.create(managerA,{...draft,
   assignedTo:techB.userId,clientRequestId:'96000000-0000-4000-8000-000000000003'
  }),e=>e.code==='INVALID_ASSIGNEE');
  await assert.rejects(planService.create(techA,{...draft,
   assignedTo:managerA.userId,clientRequestId:'96000000-0000-4000-8000-000000000004'
  }),e=>e.status===403);

  const created=await planService.create(managerA,draft);
  assert.equal(created.status,'aberta');
  assert.equal(created.revision,1);
  assert.equal((await planService.create(managerA,draft)).id,created.id);
  await assert.rejects(planService.create(managerA,{...draft,title:'Outra medida'}),
   e=>e.code==='IDEMPOTENCY_CONFLICT');
  assert.equal((await planService.list(techA)).length,1);
  assert.deepEqual(await planService.list(techB),[]);
  assert.equal((await planService.list(managerA,ncA.id)).length,1);
  assert.deepEqual(await planService.list(managerA,ncB.id),[]);
  await assert.rejects(planService.get(techB,created.id),e=>e.status===404);
  await assert.rejects(planService.edit(techA,created.id,{...draft,expectedRevision:1}),e=>e.status===403);
  await assert.rejects(planService.edit(managerA,created.id,{...draft,expectedRevision:99}),
   e=>e.code==='STALE_REVISION');
  const edited=await planService.edit(managerA,created.id,{
   title:'Substituir equipamento ficticio',description:draft.description,
   assignedTo:techA.userId,dueAt:draft.dueAt,expectedRevision:1,
  });
  assert.equal(edited.revision,2);
  assert.equal((await planService.create(managerA,draft)).id,created.id,
   'reenvio de criacao precisa funcionar mesmo apos edicao');

  const started={
   status:'em_andamento',expectedRevision:2,message:'Planejamento iniciado',
   clientRequestId:'96000000-0000-4000-8000-000000000005',
  };
  assert.equal((await planService.status(techA,created.id,started)).revision,3);
  const replay=await planService.status(techA,created.id,started);
  assert.equal(replay.replayed,true);
  assert.equal(replay.revision,3);
  await assert.rejects(planService.status(techA,created.id,{
   ...started,message:'Diferente'
  }),e=>e.code==='IDEMPOTENCY_CONFLICT');
  await assert.rejects(planService.status(techB,created.id,{
   status:'concluida',message:'',expectedRevision:3,
   clientRequestId:'96000000-0000-4000-8000-000000000006',
  }),e=>e.status===404);
  const ended=await planService.status(managerA,created.id,{
   status:'concluida',message:'Terminado',expectedRevision:3,
   clientRequestId:'96000000-0000-4000-8000-000000000007',
  });
  assert.equal(ended.status,'concluida');
  await assert.rejects(planService.status(managerA,created.id,{
   status:'em_andamento',message:'',expectedRevision:4,
   clientRequestId:'96000000-0000-4000-8000-000000000008',
  }),e=>e.code==='INVALID_STATE');
  const detail=await planService.get(managerA,created.id);
  assert.ok(detail.plan.completed_at);
  assert.deepEqual(detail.events.map(e=>e.kind),
   ['criada','editada','em_andamento','concluida']);

  const privatePlan=await planService.create(techA,{
   nonConformityId:ncA.id,title:'Sinalizacao auxiliar',
   description:'Pintar area ficticia',clientRequestId:'96000000-0000-4000-8000-000000000009',
  });
  await assert.rejects(planService.status(techA,privatePlan.id,{
   status:'cancelada',message:' ',expectedRevision:1,
   clientRequestId:'96000000-0000-4000-8000-000000000010'
  }),e=>e.status===400);
 }finally{await pool.end();}
});

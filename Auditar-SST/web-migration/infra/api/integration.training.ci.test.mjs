// Somente GitHub CI efemera, base auditar_web_hml e identidades sintéticas.
import assert from 'node:assert/strict';
import test from 'node:test';
import pg from 'pg';
import {createTrainingService} from './trainingService.mjs';
const A='10000000-0000-4000-8000-000000000001';
const B='20000000-0000-4000-8000-000000000002';
const techA={companyId:A,userId:'11000000-0000-4000-8000-000000000001',role:'tecnico'};
const clientA={companyId:A,userId:'11000000-0000-4000-8000-000000000002',role:'cliente'};
const managerA={companyId:A,userId:'33000000-0000-4000-8000-000000000003',role:'gestor'};
const techB={companyId:B,userId:'22000000-0000-4000-8000-000000000002',role:'tecnico'};

test('Treinamentos/DDS: escopo por empresa, revisão, eventos e idempotência',async()=>{
  assert.equal(process.env.AUDITAR_SST_EPHEMERAL_CI_DB,'FAKE_DATA_CI_ONLY');
  assert.equal(process.env.PGHOST,'db');
  assert.equal(process.env.PGDATABASE,'auditar_web_hml');
  assert.equal(process.env.PGUSER,'sst_ci_runner');
  const pool=new pg.Pool({max:2,connectionTimeoutMillis:5000});
  try{
    const role=await pool.query('SELECT current_user,rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user');
    assert.equal(role.rows[0].current_user,'sst_ci_runner');
    assert.equal(role.rows[0].rolsuper,false);
    assert.equal(role.rows[0].rolbypassrls,false);
    const service=createTrainingService(pool);
    const payload={
      kind:'dds',title:'Uso correto de protetor auricular CI',
      sector:'Oficina ficticia',nrReference:'NR-06',instructor:'Instrutor TESTE',
      plannedAt:'2026-11-03T10:00:00.000Z',
      durationMinutes:null,participantsCount:null,
      clientRequestId:'95000000-0000-4000-8000-000000000001',
    };
    await assert.rejects(service.list(clientA),e=>e.status===403);
    await assert.rejects(service.create(clientA,payload),e=>e.status===403);
    assert.deepEqual(await service.list(techB),[]);
    const created=await service.create(techA,payload);
    assert.equal(created.status,'planejado');
    assert.equal(created.revision,1);
    assert.equal((await service.create(techA,payload)).id,created.id);
    await assert.rejects(service.create(techA,{...payload,title:'Outro titulo'}),
      e=>e.code==='IDEMPOTENCY_CONFLICT');
    assert.equal((await service.list(managerA,'dds')).length,1);
    assert.equal((await service.list(managerA,'treinamento')).length,0);
    await assert.rejects(service.list(managerA,'invalido'),e=>e.code==='INVALID_INPUT');
    assert.deepEqual(await service.list(techB),[]);
    await assert.rejects(service.get(techB,created.id),e=>e.status===404);
    await assert.rejects(service.edit(managerA,created.id,{...payload,expectedRevision:9}),
      e=>e.code==='STALE_REVISION');
    await assert.rejects(service.status(techA,created.id,{
      status:'realizado',expectedRevision:1,message:'',
      clientRequestId:'95000000-0000-4000-8000-000000000002',
    }),e=>e.code==='INCOMPLETE_ACTIVITY');
    const edit=await service.edit(techA,created.id,{
      ...payload,durationMinutes:15,participantsCount:12,expectedRevision:1,
    });
    assert.equal(edit.revision,2);
    const statusRequest={
      status:'realizado',message:'DDS de teste registrado',expectedRevision:2,
      clientRequestId:'95000000-0000-4000-8000-000000000002',
    };
    const done=await service.status(techA,created.id,statusRequest);
    assert.equal(done.status,'realizado');
    assert.equal(done.revision,3);
    const replay=await service.status(techA,created.id,statusRequest);
    assert.equal(replay.replayed,true);
    assert.equal(replay.revision,3);
    await assert.rejects(service.status(techA,created.id,{...statusRequest,message:'Reuso diferente'}),
      e=>e.code==='IDEMPOTENCY_CONFLICT');
    await assert.rejects(service.edit(managerA,created.id,{
      ...payload,durationMinutes:15,participantsCount:12,expectedRevision:3,
    }),e=>e.code==='INVALID_STATE');
    const detail=await service.get(techA,created.id);
    assert.deepEqual(detail.events.map(x=>x.kind),['criada','editada','realizado']);
    assert.ok(detail.training.completed_at);
    assert.deepEqual(await service.list(techB),[]);
    const another=await service.create(techB,{
      ...payload,kind:'treinamento',title:'Teste B',
      clientRequestId:'95000000-0000-4000-8000-000000000003',
    });
    await assert.rejects(service.get(techA,another.id),e=>e.status===404);
    const cancel=await service.create(managerA,{
      ...payload,kind:'integracao',title:'Integração fictícia',
      clientRequestId:'95000000-0000-4000-8000-000000000004',
    });
    await assert.rejects(service.status(managerA,cancel.id,{
      status:'cancelado',expectedRevision:1,message:' ',
      clientRequestId:'95000000-0000-4000-8000-000000000005',
    }),e=>e.code==='INVALID_INPUT');
    const canceled=await service.status(managerA,cancel.id,{
      status:'cancelado',expectedRevision:1,message:'Evento adiado por teste',
      clientRequestId:'95000000-0000-4000-8000-000000000005',
    });
    assert.equal(canceled.status,'cancelado');
  }finally{await pool.end();}
});

// Apenas GitHub Actions: PostgreSQL descartavel, contas e composicao CIPA sinteticas.
import assert from 'node:assert/strict';
import test from 'node:test';
import pg from 'pg';
import {createCipaService} from './cipaService.mjs';
const A='10000000-0000-4000-8000-000000000001';
const B='20000000-0000-4000-8000-000000000002';
const techA={companyId:A,userId:'11000000-0000-4000-8000-000000000001',role:'tecnico'};
const clientA={companyId:A,userId:'11000000-0000-4000-8000-000000000002',role:'cliente'};
const managerA={companyId:A,userId:'33000000-0000-4000-8000-000000000003',role:'gestor'};
const techB={companyId:B,userId:'22000000-0000-4000-8000-000000000002',role:'tecnico'};
test('CIPA ficticia: isolamento, composicao, reuniao, historico e status administrativo',async()=>{
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
    const svc=createCipaService(pool);
    assert.deepEqual(await svc.list(techA),[]);
    await assert.rejects(svc.list(clientA),e=>e.status===403);
    const draft={name:'Mandato CIPA CI 2027',startsOn:'2027-01-01',
      endsOn:'2027-12-31',electionOn:'2026-12-10',
      clientRequestId:'94000000-0000-4000-8000-000000000001'};
    await assert.rejects(svc.create(clientA,draft),e=>e.status===403);
    await assert.rejects(svc.create(techA,{...draft,endsOn:'2026-12-31'}),
      e=>e.code==='INVALID_INPUT');
    const m=await svc.create(techA,draft);
    assert.equal(m.status,'preparacao');
    assert.equal((await svc.create(techA,draft)).id,m.id);
    await assert.rejects(svc.create(techA,{...draft,name:'Outro mandato'}),
      e=>e.code==='IDEMPOTENCY_CONFLICT');
    await assert.rejects(svc.get(techB,m.id),e=>e.status===404);
    assert.deepEqual(await svc.list(techB),[]);
    const member={displayName:'Membro FICTICIO CI',representation:'empregados',seat:'titular',
      clientRequestId:'94000000-0000-4000-8000-000000000002'};
    await assert.rejects(svc.addMember(techA,m.id,{...member,seat:'designado'}),
      e=>e.code==='INVALID_INPUT');
    const joined=await svc.addMember(techA,m.id,member);
    assert.equal(joined.representation,'empregados');
    assert.equal((await svc.addMember(techA,m.id,member)).id,joined.id);
    await assert.rejects(svc.addMember(techA,m.id,{...member,displayName:'Outro'}),
      e=>e.code==='IDEMPOTENCY_CONFLICT');
    await assert.rejects(svc.addMember(techB,m.id,{
      ...member,clientRequestId:'94000000-0000-4000-8000-000000000003',
    }),e=>e.status===404);
    const meeting={title:'Reuniao mensal ficticia',
      scheduledAt:'2027-02-02T12:00:00.000Z',
      clientRequestId:'94000000-0000-4000-8000-000000000004'};
    const event=await svc.addMeeting(techA,m.id,meeting);
    assert.equal(event.status,'planejada');
    assert.equal((await svc.addMeeting(techA,m.id,meeting)).id,event.id);
    await assert.rejects(svc.decideMeeting(techB,event.id,{
      status:'realizada',summary:'Relato falso',expectedRevision:1,
    }),e=>e.status===404);
    await assert.rejects(svc.decideMeeting(techA,event.id,{
      status:'realizada',summary:'',expectedRevision:1,
    }),e=>e.code==='INVALID_INPUT');
    await assert.rejects(svc.decideMeeting(techA,event.id,{
      status:'realizada',summary:'Resumo registrado em teste',expectedRevision:10,
    }),e=>e.code==='STALE_REVISION');
    const done=await svc.decideMeeting(techA,event.id,{
      status:'realizada',summary:'Resumo registrado em teste',expectedRevision:1,
    });
    assert.equal(done.status,'realizada');
    assert.equal(done.revision,2);
    await assert.rejects(svc.decideMeeting(techA,event.id,{
      status:'cancelada',summary:'Outro',expectedRevision:2,
    }),e=>e.code==='INVALID_STATE');
    const detail=await svc.get(managerA,m.id);
    assert.equal(detail.members.length,1);
    assert.equal(detail.meetings.length,1);
    assert.equal(detail.meetings[0].status,'realizada');
    assert.deepEqual(detail.events.map(x=>x.kind),[
      'mandato_criado','membro_adicionado','reuniao_agendada','reuniao_realizada',
    ]);
    await assert.rejects(svc.mandateStatus(techA,m.id,{status:'ativo',expectedRevision:1}),
      e=>e.status===403);
    const started=await svc.mandateStatus(managerA,m.id,{status:'ativo',expectedRevision:1});
    assert.equal(started.revision,2);
    await assert.rejects(svc.mandateStatus(managerA,m.id,{status:'encerrado',expectedRevision:2}),
      e=>e.code==='INVALID_INPUT');
    const ended=await svc.mandateStatus(managerA,m.id,{
      status:'encerrado',expectedRevision:2,note:'Termino administrativo ficticio',
    });
    assert.equal(ended.status,'encerrado');
    await assert.rejects(svc.addMeeting(techA,m.id,{
      ...meeting,clientRequestId:'94000000-0000-4000-8000-000000000005',
    }),e=>e.code==='INVALID_STATE');
    const mandateB=await svc.create(techB,{...draft,name:'CIPA FICTICIA B',
      clientRequestId:'94000000-0000-4000-8000-000000000006'});
    assert.equal((await svc.list(techA)).length,1);
    assert.equal((await svc.list(techB)).length,1);
    await assert.rejects(svc.get(techA,mandateB.id),e=>e.status===404);
  }finally{await pool.end();}
});

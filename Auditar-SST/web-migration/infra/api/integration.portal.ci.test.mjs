// SOMENTE CI EFEMERA: cliente, atendimento, gestor e atividade web multiempresa.
import test from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import {createPortalService} from './portalService.mjs';
import {createNcService} from './ncService.mjs';
const A='10000000-0000-4000-8000-000000000001';
const B='20000000-0000-4000-8000-000000000002';
const techA={companyId:A,userId:'11000000-0000-4000-8000-000000000001',role:'tecnico'};
const clientA={companyId:A,userId:'11000000-0000-4000-8000-000000000002',role:'cliente'};
const managerA={companyId:A,userId:'33000000-0000-4000-8000-000000000003',role:'gestor'};
const techB={companyId:B,userId:'22000000-0000-4000-8000-000000000002',role:'tecnico'};
test('portal: isolamento RLS, atendimento do cliente e adm da empresa',async()=>{
  assert.equal(process.env.AUDITAR_SST_EPHEMERAL_CI_DB,'FAKE_DATA_CI_ONLY');
  assert.equal(process.env.PGHOST,'db');
  assert.equal(process.env.PGDATABASE,'auditar_web_hml');
  assert.equal(process.env.PGUSER,'sst_ci_runner');
  const pool=new pg.Pool({max:2,connectionTimeoutMillis:5000});
  try{
    const portal=createPortalService(pool),ncs=createNcService(pool);
    const nc=await ncs.create(techA,{
      shortTitle:'Extintor vencido ficticio',description:'Extintor de teste vencido',probability:4,severity:4,
    });
    const dash=await portal.dashboard(clientA);
    assert.ok(dash.pending.some(row=>row.id===nc.id));
    assert.equal((await portal.dashboard(techB)).pending.length,0);
    const key='a7000000-0000-4000-8000-000000000001';
    const first=await portal.createThread(clientA,{
      subject:'Dúvida ficticia sobre extintor',message:'Cliente de teste solicitou orientação',clientRequestId:key,
    });
    assert.equal(first.status,'aberta');
    assert.equal((await portal.createThread(clientA,{
      subject:'Dúvida ficticia sobre extintor',message:'Cliente de teste solicitou orientação',clientRequestId:key,
    })).id,first.id);
    assert.equal((await portal.threads(clientA)).some(row=>row.id===first.id),true);
    assert.equal((await portal.threads(techA)).some(row=>row.id===first.id),true);
    assert.equal((await portal.threads(techB)).some(row=>row.id===first.id),false);
    await assert.rejects(portal.thread(techB,first.id),e=>e.status===404);
    await assert.rejects(portal.reply(techB,first.id,{
      message:'Resposta indevida',clientRequestId:'a7000000-0000-4000-8000-000000000002',
    }),e=>e.status===404);
    const detail=await portal.thread(clientA,first.id);
    assert.equal(detail.messages.length,1);
    const responseKey='a7000000-0000-4000-8000-000000000003';
    const response=await portal.reply(techA,first.id,{message:'Equipe ficticia respondeu',clientRequestId:responseKey});
    assert.equal(response.replayed,false);
    assert.equal((await portal.reply(techA,first.id,{message:'Equipe ficticia respondeu',clientRequestId:responseKey})).replayed,true);
    assert.equal((await portal.thread(clientA,first.id)).messages.length,2);
    await assert.rejects(portal.changeStatus(clientA,first.id,'close',{}),e=>e.status===403);
    assert.equal((await portal.changeStatus(techA,first.id,'close',{message:'Concluida em teste'})).status,'encerrada');
    await assert.rejects(portal.reply(clientA,first.id,{
      message:'Nao pode apos fechar',clientRequestId:'a7000000-0000-4000-8000-000000000004',
    }),e=>e.code==='INVALID_STATE');
    assert.equal((await portal.changeStatus(clientA,first.id,'reopen',{message:'Ainda tenho duvida'})).status,'aberta');
    assert.deepEqual((await portal.thread(clientA,first.id)).messages.map(row=>row.kind),
      ['mensagem','mensagem','encerramento','reabertura']);
    await assert.rejects(portal.overview(clientA),e=>e.status===403);
    await assert.rejects(portal.team(techA),e=>e.status===403);
    await assert.rejects(portal.ping(clientA),e=>e.status===403);
    assert.deepEqual(await portal.ping(techA),{ok:true});
    const team=await portal.team(managerA);
    assert.ok(team.some(user=>user.id===techA.userId&&user.web_recent));
    assert.ok(!team.some(user=>user.id===techB.userId));
    const overview=await portal.overview(managerA);
    assert.ok(overview.nc_pendentes>=1);
    assert.ok(overview.apoio_aberto>=1);
    assert.equal((await portal.overview({...techB,role:'gestor'})).apoio_aberto,0);
    assert.deepEqual(await portal.threads(techB),[]);
  }finally{await pool.end();}
});

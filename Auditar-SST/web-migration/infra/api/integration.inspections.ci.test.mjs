/**
 * SOMENTE CI efemera com identidades ficticias. NUNCA contra dados reais.
 */
import assert from 'node:assert/strict';
import test from 'node:test';
import pg from 'pg';
import { createInspectionService } from './inspectionService.mjs';
import { ApiError } from './ncService.mjs';

const companyA='10000000-0000-4000-8000-000000000001';
const companyB='20000000-0000-4000-8000-000000000002';
const techA={companyId:companyA,userId:'11000000-0000-4000-8000-000000000001',role:'tecnico'};
const clientA={companyId:companyA,userId:'11000000-0000-4000-8000-000000000002',role:'cliente'};
const techB={companyId:companyB,userId:'22000000-0000-4000-8000-000000000002',role:'tecnico'};
const requestId='99000000-0000-4000-8000-000000000001';
const findingRequestId='99000000-0000-4000-8000-000000000002';

test('API de vistorias: rascunho, deduplicacao, versao, achado, fechamento e RLS',async()=>{
  assert.equal(process.env.AUDITAR_SST_EPHEMERAL_CI_DB,'FAKE_DATA_CI_ONLY');
  assert.equal(process.env.PGHOST,'db');
  assert.equal(process.env.PGDATABASE,'auditar_web_hml');
  assert.equal(process.env.PGUSER,'sst_ci_runner');
  assert.ok(process.env.PGPASSWORD);
  const pool=new pg.Pool({max:2,connectionTimeoutMillis:5000});
  try {
    const role=await pool.query(
      'SELECT current_user,rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user');
    assert.equal(role.rows[0].current_user,'sst_ci_runner');
    assert.equal(role.rows[0].rolsuper,false);
    assert.equal(role.rows[0].rolbypassrls,false);
    const service=createInspectionService(pool);
    const payload={
      inspectionType:'ronda_expressa',title:'Ronda ficticia teste 001',
      description:'Cenario gerado para testes',sector:'Producao',
      location:'Esteira ficticia',clientRequestId:requestId,
    };
    assert.deepEqual(await service.list(techA),[]);
    assert.deepEqual(await service.list(techB),[]);
    const created=await service.create(techA,payload);
    assert.equal(created.status,'rascunho');
    assert.equal(created.revision,1);
    assert.equal((await service.create(techA,payload)).id,created.id,
      'retry com mesma chave nao pode duplicar a vistoria');
    await assert.rejects(service.create(techA,{...payload,title:'Diferente'}),
      e=>e instanceof ApiError&&e.code==='IDEMPOTENCY_CONFLICT');
    await assert.rejects(service.create(clientA,{...payload,clientRequestId:'99000000-0000-4000-8000-000000000003'}),
      e=>e instanceof ApiError&&e.status===403);
    assert.deepEqual(await service.list(clientA),[],'Cliente nao le rascunho');
    await assert.rejects(service.get(clientA,created.id),e=>e.status===404);
    await assert.rejects(service.get(techB,created.id),e=>e.status===404);
    await assert.rejects(service.update(techA,created.id,{
      expectedRevision:99,title:'Divergente',sector:'',location:'',description:'',
    }),e=>e.code==='STALE_REVISION');
    const updated=await service.update(techA,created.id,{
      expectedRevision:1,title:'Ronda ficticia revisada',
      description:'Atualizacao controlada',sector:'Producao',location:'Esteira 4',
    });
    assert.equal(updated.revision,2);
    await assert.rejects(service.addFinding(techB,created.id,{
      description:'Nunca deve gravar',probability:1,severity:1,
      clientRequestId:'99000000-0000-4000-8000-000000000004',
    }),e=>e.status===404);
    const findingPayload={
      shortTitle:'Protecao removida',
      description:'Protecao ficticia retirada da esteira',
      recommendation:'Reinstalar protecao fixa e conferir antes do retorno ficticio.',
      probability:4,severity:5,
      recurring:true,clientRequestId:findingRequestId,
    };
    const nc=await service.addFinding(techA,created.id,findingPayload);
    assert.equal(nc.short_title,'Protecao removida');
    assert.match(nc.recommendation,/Reinstalar protecao/);
    assert.equal(nc.inspection_id,created.id);
    assert.equal((await service.addFinding(techA,created.id,findingPayload)).id,nc.id);
    await assert.rejects(service.addFinding(techA,created.id,{...findingPayload,
      recommendation:'Recomendacao diferente'}),e=>e.code==='IDEMPOTENCY_CONFLICT');
    await assert.rejects(service.addFinding(techA,created.id,{...findingPayload,shortTitle:'Outro'}),
      e=>e.code==='IDEMPOTENCY_CONFLICT');
    assert.equal((await service.get(techA,created.id)).inspection.revision,3);
    assert.equal((await service.complete(techA,created.id)).status,'concluida');
    assert.equal((await service.complete(techA,created.id)).status,'concluida');
    await assert.rejects(service.addFinding(techA,created.id,{
      ...findingPayload,clientRequestId:'99000000-0000-4000-8000-000000000005',
    }),e=>e.code==='INVALID_STATE');
    await assert.rejects(service.update(techA,created.id,{
      expectedRevision:4,title:'Nao pode',description:'',sector:'',location:'',
    }),e=>e.code==='INVALID_STATE');
    const view=await service.get(techA,created.id);
    assert.equal(view.inspection.status,'concluida');
    assert.equal(view.findings.length,1);
    assert.equal(view.findings[0].recommendation,findingPayload.recommendation);
    assert.deepEqual(view.events.map(event=>event.kind),[
      'criada','editada','achado_incluido','concluida',
    ]);
    assert.equal((await service.list(clientA)).length,1);
    assert.equal((await service.get(clientA,created.id)).findings[0].id,nc.id);
    assert.deepEqual(await service.list(techB),[]);
  } finally {await pool.end();}
});

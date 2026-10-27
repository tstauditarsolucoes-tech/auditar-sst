/**
 * TESTE COM POSTGRES REAL EXCLUSIVO DA CI EFEMERA.
 * Nao usar na VPS, em staging persistente ou com dados de clientes.
 */
import assert from 'node:assert/strict';
import test from 'node:test';
import pg from 'pg';
import { createNcService, ApiError } from './ncService.mjs';

const expectedMarker = 'FAKE_DATA_CI_ONLY';
const companyA='10000000-0000-4000-8000-000000000001';
const companyB='20000000-0000-4000-8000-000000000002';
const techA={companyId:companyA,userId:'11000000-0000-4000-8000-000000000001',role:'tecnico'};
const clientA={companyId:companyA,userId:'11000000-0000-4000-8000-000000000002',role:'cliente'};
const techB={companyId:companyB,userId:'22000000-0000-4000-8000-000000000002',role:'tecnico'};

test('CI efemera: fluxo real de NC e isolamento de empresa na conta DB restrita', async()=>{
  assert.equal(process.env.AUDITAR_SST_EPHEMERAL_CI_DB,expectedMarker,
    'Este teste exige ambiente CI efemero explicito');
  assert.equal(process.env.PGHOST,'db','Nunca apontar para host externo');
  assert.equal(process.env.PGDATABASE,'auditar_web_hml','Nunca apontar para base real');
  assert.equal(process.env.PGUSER,'sst_ci_runner','Nunca usar usuario superuser');
  assert.ok(process.env.PGPASSWORD,'Credencial sintetica CI obrigatoria');

  const pool=new pg.Pool({max:2,connectionTimeoutMillis:5000});
  try {
    const identity=await pool.query(
      "SELECT current_user, rolsuper, rolbypassrls FROM pg_roles WHERE rolname=current_user"
    );
    assert.equal(identity.rows[0].current_user,'sst_ci_runner');
    assert.equal(identity.rows[0].rolsuper,false);
    assert.equal(identity.rows[0].rolbypassrls,false);

    const service=createNcService(pool);
    assert.deepEqual(await service.list(techB),[],'Nenhum registro deve pertencer a B');
    const created=await service.create(techA,{
      description:' Extintor ficticio vencido em homologacao ',
      probability:4,severity:4,recurring:true,
    });
    assert.match(created.id,/^[0-9a-f-]{36}$/i);
    assert.equal(created.status,'aberta');

    const visibleA=await service.list(techA);
    assert.equal(visibleA.length,1);
    assert.equal(visibleA[0].description,'Extintor ficticio vencido em homologacao');
    assert.deepEqual(await service.list(techB),[],'B nao pode ler NC de A');
    await assert.rejects(service.events(techB,created.id),
      err=>err instanceof ApiError && err.status===404);

    const first=await service.reportCorrection(clientA,created.id,{message:'Foto ficticia revisada'});
    assert.equal(first.status,'correcao_informada');
    await assert.rejects(service.decideCorrection(clientA,created.id,{accepted:true}),
      err=>err instanceof ApiError && err.status===403);
    await assert.rejects(service.decideCorrection(techA,created.id,{accepted:false,reason:'  '}),
      err=>err instanceof ApiError && err.status===400);
    const rejected=await service.decideCorrection(techA,created.id,{
      accepted:false,reason:'Protecao ainda removida',
    });
    assert.equal(rejected.status,'rejeitada');

    await service.reportCorrection(clientA,created.id,{message:'Protecao reinstalada'});
    const validated=await service.decideCorrection(techA,created.id,{accepted:true,reason:''});
    assert.equal(validated.status,'validada');
    const events=await service.events(techA,created.id);
    assert.deepEqual(events.map(e=>e.kind),[
      'identificada','correcao_informada','rejeitada','correcao_informada','validada',
    ]);
    await assert.rejects(service.reportCorrection(clientA,created.id,{message:'Duplicado'}),
      err=>err instanceof ApiError && err.status===409);
    assert.deepEqual(await service.list(techB),[],'Isolamento persiste apos escrita e validacao');
  } finally {
    await pool.end();
  }
});

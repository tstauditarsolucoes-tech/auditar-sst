import test from 'node:test';
import assert from 'node:assert/strict';
import { createNcService, ApiError } from './ncService.mjs';
import { createApp } from './server.mjs';
import { once } from 'node:events';

const companyId = '10000000-0000-4000-8000-000000000001';
const userId = '11000000-0000-4000-8000-000000000001';
const ncId = '12000000-0000-4000-8000-000000000001';
const principal = (role = 'tecnico') => ({companyId,userId,role});

function fakePool(status = 'aberta') {
  const queries = [];
  let released = false;
  const client = {
    async query(sql, params = []) {
      queries.push({sql,params});
      if (sql.includes('RETURNING id,description,status,created_at')) {
        return {rows:[{id:ncId,description:params[1],status:'aberta'}],rowCount:1};
      }
      if (sql.startsWith('SELECT status')) return {rows:[{status}],rowCount:1};
      if (sql.startsWith('SELECT id FROM sst.non_conformity')) return {rows:[{id:ncId}],rowCount:1};
      if (sql.startsWith('SELECT id,kind,message')) return {rows:[{id:'test-event',kind:'identificada'}],rowCount:1};
      if (sql.startsWith('SELECT id, description, probability')) return {rows:[],rowCount:0};
      return {rows:[],rowCount:0};
    },
    release() { released = true; },
  };
  return {queries, client, get released() {return released;}, async connect() {return client;}};
}

test('create NC aplica role restrito, tenant da sessao e parametros SQL', async () => {
  const pool = fakePool();
  const item = await createNcService(pool).create(principal(), {
    description:' Extintor vencido ',probability:4,severity:4,recurring:true,
  });
  assert.equal(item.id,ncId);
  assert.deepEqual(pool.queries.slice(0,3).map(x=>x.sql),[
    'BEGIN','SET LOCAL ROLE sst_app_runtime',"SELECT set_config('app.company_id', $1, true)"
  ]);
  assert.deepEqual(pool.queries[2].params,[companyId]);
  assert.ok(pool.queries.some(x => x.sql.includes('INSERT INTO sst.nc_treatment_event')));
  assert.equal(pool.queries.at(-1).sql,'COMMIT');
  assert.equal(pool.released,true);
});

test('perfil cliente nao cria NC e transacao e revertida', async () => {
  const pool=fakePool();
  await assert.rejects(
    createNcService(pool).create(principal('cliente'),{description:'Teste',probability:3,severity:3}),
    e => e instanceof ApiError && e.status===403
  );
  assert.equal(pool.queries.at(-1).sql,'ROLLBACK');
});

test('cliente informa correcao, mas nao valida tecnicamente', async () => {
  const pool=fakePool('aberta');
  const service=createNcService(pool);
  const info=await service.reportCorrection(principal('cliente'),ncId,{message:'Correção realizada'});
  assert.equal(info.status,'correcao_informada');
  assert.ok(pool.queries.some(x=>x.sql.includes('FOR UPDATE')));
  await assert.rejects(
    service.decideCorrection(principal('cliente'),ncId,{accepted:true}),
    e => e.status===403
  );
});

test('rejeicao exige motivo e mantem evento, valida somente pendente', async () => {
  const pool=fakePool('correcao_informada');
  const service=createNcService(pool);
  await assert.rejects(
    service.decideCorrection(principal(),ncId,{accepted:false,reason:' '}),
    e => e.status===400
  );
  const result=await service.decideCorrection(principal(),ncId,{accepted:false,reason:'Proteção ainda ausente'});
  assert.equal(result.status,'rejeitada');
  assert.ok(pool.queries.some(x=>x.sql.includes('INSERT INTO sst.nc_treatment_event') && x.params.includes('rejeitada')));
});

test('NC de outro estado nao pode validar e nao gera evento', async () => {
  const pool=fakePool('aberta');
  await assert.rejects(
    createNcService(pool).decideCorrection(principal(),ncId,{accepted:true}),
    e => e.status===409
  );
  assert.ok(!pool.queries.some(x=>x.sql.includes('INSERT INTO sst.nc_treatment_event')));
});

test('erros invalidos e parametros nao viram interpolacao SQL', async () => {
  const pool=fakePool();
  await assert.rejects(
    createNcService(pool).create(principal(),{description:'x',probability:99,severity:3}),
    e => e.status===400
  );
  await assert.rejects(
    createNcService(pool).events(principal(),'invalido'),
    e => e.status===400
  );
});

test('HTTP aceita consulta apenas com principal injetado pela sessao do servidor', async () => {
  const pool=fakePool();
  const app=createApp({pool,resolvePrincipal:async()=>principal()});
  app.listen(0,'127.0.0.1');
  await once(app,'listening');
  try {
    const base='http://127.0.0.1:'+app.address().port;
    const get=await fetch(base+'/api/v1/nonconformities');
    assert.equal(get.status,200);
    assert.deepEqual((await get.json()).items,[]);
    const post=await fetch(base+'/api/v1/nonconformities',{
      method:'POST',headers:{'content-type':'application/json'},
      body:JSON.stringify({description:'Extintor vencido',probability:3,severity:4}),
    });
    assert.equal(post.status,201);
    assert.equal((await post.json()).item.id,ncId);
  } finally {
    await new Promise((resolve,reject)=>app.close(e=>e?reject(e):resolve()));
  }
});

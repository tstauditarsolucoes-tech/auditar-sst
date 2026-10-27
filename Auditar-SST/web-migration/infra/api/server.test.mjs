import test from 'node:test';
import assert from 'node:assert/strict';
import { once } from 'node:events';
import { createApp } from './server.mjs';

async function withServer(callback) {
  const server = createApp();
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  try {
    await callback('http://127.0.0.1:' + server.address().port);
  } finally {
    await new Promise((resolve, reject) =>
      server.close(err => err ? reject(err) : resolve())
    );
  }
}

test('health responde com ambiente isolado e sem dados de producao', async () => {
  await withServer(async base => {
    const res = await fetch(base + '/api/v1/health');
    assert.equal(res.status, 200);
    assert.match(res.headers.get('content-type'), /application\/json/);
    assert.equal(res.headers.get('cache-control'), 'no-store');
    const payload = await res.json();
    assert.equal(payload.ok, true);
    assert.equal(payload.productionDataConnected, false);
  });
});

test('outras rotas nao simulam login nem dados reais', async () => {
  await withServer(async base => {
    for (const pathname of ['/api/v1/session', '/api/v1/companies']) {
      const res = await fetch(base + pathname);
      assert.equal(res.status, 404);
      assert.equal((await res.json()).code, 'NOT_IMPLEMENTED');
    }
  });
});

test('health nao aceita escrita', async () => {
  await withServer(async base => {
    const res = await fetch(base + '/api/v1/health', { method: 'POST' });
    assert.equal(res.status, 404);
  });
});

test('NC protegida nao aceita headers de empresa/perfil como identidade', async () => {
  await withServer(async base => {
    for (const method of ['GET','POST']) {
      const res = await fetch(base + '/api/v1/nonconformities', {
        method,
        headers: {'x-company-id':'10000000-0000-4000-8000-000000000001','x-role':'adm'},
      });
      assert.equal(res.status, 401);
      assert.equal((await res.json()).code, 'UNAUTHENTICATED');
    }
  });
});

test('vistoria protegida nao confia em headers de empresa nem perfil',async()=>{
  await withServer(async base=>{
    for(const [method,path] of [
      ['GET','/api/v1/inspections'],
      ['POST','/api/v1/inspections'],
      ['GET','/api/v1/inspections/10000000-0000-4000-8000-000000000001'],
    ]) {
      const res=await fetch(base+path,{method,headers:{
        'x-company-id':'10000000-0000-4000-8000-000000000001','x-role':'adm',
      }});
      assert.equal(res.status,401);
      assert.equal((await res.json()).code,'UNAUTHENTICATED');
    }
  });
});

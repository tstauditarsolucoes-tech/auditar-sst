/**
 * Exercita LOGIN NOVO exclusivamente na CI efemera com senhas e empresas ficticias.
 * Jamais rodar em VPS ou ambiente persistente.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import {once} from 'node:events';
import pg from 'pg';
import {createHash} from 'node:crypto';
import {createApp} from './server.mjs';
import {createAuthService} from './authService.mjs';

const origin='https://homologacao-ci.auditarsolucoes.invalid';
const userId='11000000-0000-4000-8000-000000000001';
const companyA='10000000-0000-4000-8000-000000000001';
const companyB='20000000-0000-4000-8000-000000000002';
const fakePassword='SenhaFicticiaCI-2026!';

test('CI: autentica, exige cookie/CSRF, separa empresas e revoga sessao',async()=>{
  assert.equal(process.env.AUDITAR_SST_EPHEMERAL_CI_DB,'FAKE_DATA_CI_ONLY');
  assert.equal(process.env.PGHOST,'db');
  assert.equal(process.env.PGDATABASE,'auditar_web_hml');
  assert.equal(process.env.PGUSER,'sst_ci_runner');
  assert.equal(process.env.AUDITAR_PG_AUTH_USER,'sst_ci_auth_runner');

  const dataPool=new pg.Pool({max:2,connectionTimeoutMillis:5000});
  const authPool=new pg.Pool({
    host:'db',database:'auditar_web_hml',user:'sst_ci_auth_runner',
    password:process.env.AUDITAR_PG_AUTH_PASSWORD,max:2,connectionTimeoutMillis:5000,
  });
  const authService=createAuthService({pool:authPool,allowedOrigin:origin});
  const app=createApp({pool:dataPool,authService});
  app.listen(0,'0.0.0.0');
  await once(app,'listening');
  try {
    const base='http://127.0.0.1:'+app.address().port;
    const json=(body)=>({method:'POST',headers:{'content-type':'application/json',origin},
      body:JSON.stringify(body)});
    const unauth=await fetch(base+'/api/v1/auth/session');
    assert.equal(unauth.status,401);

    const invalid=await fetch(base+'/api/v1/auth/login',json({
      email:'tecnico-ci-a@example.invalid',password:'senha-falsa',
    }));
    assert.equal(invalid.status,401);
    // Forca o contador perto do limite sem desperdiçar 10 derivacoes de senha.
    const fakeEmail='nao-existe-ci@example.invalid';
    const h=createHash('sha256').update(fakeEmail).digest('hex');
    const rateConn=await authPool.connect();
    try {
      await rateConn.query('BEGIN');
      await rateConn.query('SET LOCAL ROLE sst_auth_runtime');
      await rateConn.query(
        'INSERT INTO sst.auth_login_counter(identity_hash,attempt_count,window_start) '+
        'VALUES ($1,9,now())',[h],
      );
      await rateConn.query('COMMIT');
    } finally {rateConn.release();}
    const tenth=await fetch(base+'/api/v1/auth/login',json({email:fakeEmail,password:'errada'}));
    assert.equal(tenth.status,401);
    const limited=await fetch(base+'/api/v1/auth/login',json({email:fakeEmail,password:'errada'}));
    assert.equal(limited.status,429);
    const login=await fetch(base+'/api/v1/auth/login',json({
      email:'tecnico-ci-a@example.invalid',password:fakePassword,
    }));
    assert.equal(login.status,200);
    const setCookie=login.headers.get('set-cookie');
    assert.match(setCookie,/__Host-auditar_sst=/);
    assert.match(setCookie,/HttpOnly/);
    assert.match(setCookie,/Secure/);
    assert.match(setCookie,/SameSite=Lax/);
    const cookie=setCookie.split(';')[0];
    const logged=await login.json();
    assert.equal(logged.user.id,userId);
    assert.equal(logged.companyId,companyA);
    assert.equal(logged.role,'tecnico');
    assert.match(logged.csrfToken,/^[A-Za-z0-9_-]{43}$/);

    const authedHeaders={cookie};
    const session=await fetch(base+'/api/v1/auth/session',{headers:authedHeaders});
    assert.equal(session.status,200);
    assert.equal((await session.json()).companyId,companyA);

    const ncPayload={description:'NC ficticia autenticada',probability:3,severity:4};
    const withoutCsrf=await fetch(base+'/api/v1/nonconformities',{
      ...json(ncPayload),headers:{...json(ncPayload).headers,cookie},
    });
    assert.equal(withoutCsrf.status,403);
    const wrongOrigin=await fetch(base+'/api/v1/nonconformities',{
      ...json(ncPayload),headers:{'content-type':'application/json',origin:'https://hostil.invalid',
        cookie,'x-csrf-token':logged.csrfToken},
    });
    assert.equal(wrongOrigin.status,403);
    const writeHeaders={'content-type':'application/json',origin,cookie,
      'x-csrf-token':logged.csrfToken};
    const createdResponse=await fetch(base+'/api/v1/nonconformities',{
      method:'POST',headers:writeHeaders,body:JSON.stringify(ncPayload),
    });
    assert.equal(createdResponse.status,201);
    const created=(await createdResponse.json()).item;
    assert.ok(created.id);

    const listA=await fetch(base+'/api/v1/nonconformities',{headers:authedHeaders});
    assert.equal(listA.status,200);
    assert.ok((await listA.json()).items.some(x=>x.id===created.id));

    const options=await fetch(base+'/api/v1/auth/companies',{headers:authedHeaders});
    assert.equal(options.status,200);
    const companies=(await options.json()).items;
    assert.equal(companies.length,2);

    const switchB=await fetch(base+'/api/v1/auth/company',{
      method:'POST',headers:writeHeaders,body:JSON.stringify({companyId:companyB}),
    });
    assert.equal(switchB.status,200);
    assert.equal((await switchB.json()).role,'cliente');
    const listB=await fetch(base+'/api/v1/nonconformities',{headers:authedHeaders});
    assert.equal(listB.status,200);
    assert.deepEqual((await listB.json()).items,[],'B nao enxerga NC de A');
    const createB=await fetch(base+'/api/v1/nonconformities',{
      method:'POST',headers:writeHeaders,body:JSON.stringify(ncPayload),
    });
    assert.equal(createB.status,403,'Perfil cliente nao pode criar NC');

    const notMember=await fetch(base+'/api/v1/auth/company',{
      method:'POST',headers:writeHeaders,body:JSON.stringify({
        companyId:'30000000-0000-4000-8000-000000000003',
      }),
    });
    assert.equal(notMember.status,403);
    const switchA=await fetch(base+'/api/v1/auth/company',{
      method:'POST',headers:writeHeaders,body:JSON.stringify({companyId:companyA}),
    });
    assert.equal(switchA.status,200);
    assert.equal((await switchA.json()).role,'tecnico');

    const logout=await fetch(base+'/api/v1/auth/logout',{
      method:'POST',headers:writeHeaders,body:'{}',
    });
    assert.equal(logout.status,200);
    assert.match(logout.headers.get('set-cookie'),/Max-Age=0/);
    assert.equal((await fetch(base+'/api/v1/auth/session',{headers:authedHeaders})).status,401);
    assert.equal((await fetch(base+'/api/v1/nonconformities',{headers:authedHeaders})).status,401);

    // A conta da API de NC nao ganha permissao para ler hashes de senha.
    const conn=await dataPool.connect();
    try {
      await conn.query('BEGIN');
      await conn.query('SET LOCAL ROLE sst_app_runtime');
      await assert.rejects(conn.query('SELECT user_id FROM sst.auth_credential'),
        err=>err.code==='42501');
      await conn.query('ROLLBACK');
    } finally {conn.release();}
  } finally {
    await new Promise((resolve,reject)=>app.close(e=>e?reject(e):resolve()));
    await Promise.all([dataPool.end(),authPool.end()]);
  }
});

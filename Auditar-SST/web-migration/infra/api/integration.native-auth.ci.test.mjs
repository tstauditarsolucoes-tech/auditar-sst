// Auth nativa SOMENTE CI efemera com usuarios e senhas ficticios.
// Nunca rodar teste contra banco real/host externo.
import test from 'node:test';
import assert from 'node:assert/strict';
import {once} from 'node:events';
import pg from 'pg';
import {createHash} from 'node:crypto';
import {createApp} from './server.mjs';
import {createAuthService} from './authService.mjs';
import {createNativeAuthService} from './nativeAuthService.mjs';

test('sessao nativa: token independente, sem acesso business, 2 empresas e revogacao',async()=>{
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
 const origin='https://homologacao-ci.auditarsolucoes.invalid';
 const nativeAuthService=createNativeAuthService({pool:authPool});
 const authService=createAuthService({pool:authPool,allowedOrigin:origin});
 const app=createApp({pool:dataPool,authService,nativeAuthService});
 app.listen(0,'0.0.0.0');await once(app,'listening');
 const base='http://127.0.0.1:'+app.address().port+'/api/v1/';
 const email='tecnico-ci-a@example.invalid',password='SenhaFicticiaCI-2026!';
 const json=body=>({method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});
 try{
  const without=await fetch(base+'native/auth/session');
  assert.equal(without.status,401);
  const wrong=await fetch(base+'native/auth/login',json({email,password:'wrong'}));
  assert.equal(wrong.status,401);
  const htmlBrowser=await fetch(base+'native/auth/login',{
   ...json({email,password}),headers:{'content-type':'application/json',origin},
  });
  assert.equal(htmlBrowser.status,403);
  const extra=await fetch(base+'native/auth/login',json({email,password,deviceId:'FICTICIO'}));
  assert.equal(extra.status,400);
  const logged=await fetch(base+'native/auth/login',json({email,password}));
  assert.equal(logged.status,200);
  assert.equal(logged.headers.get('set-cookie'),null,'Login nativo nao emite cookie');
  const result=await logged.json();
  assert.equal(result.user.id,'11000000-0000-4000-8000-000000000001');
  assert.equal(result.companyId,'10000000-0000-4000-8000-000000000001');
  assert.equal(result.role,'tecnico');
  assert.equal(result.expiresInSeconds,1800);
  assert.equal(result.syncEnabled,false);
  assert.equal(result.writesEnabled,false);
  assert.match(result.token,/^[A-Za-z0-9_-]{43}$/);
  const h=createHash('sha256').update(result.token).digest('hex');
  const conn=await authPool.connect();
  try{
   await conn.query('BEGIN');await conn.query('SET LOCAL ROLE sst_auth_runtime');
   const rows=await conn.query('SELECT token_hash,expires_at,revoked_at FROM sst.native_session WHERE token_hash=$1',[h]);
   assert.equal(rows.rowCount,1);
   assert.equal(rows.rows[0].revoked_at,null);
   assert.notEqual(rows.rows[0].token_hash,result.token);
   await conn.query('ROLLBACK');
  }finally{conn.release();}
  const bearer={'authorization':'Bearer '+result.token};
  const session=await fetch(base+'native/auth/session',{headers:bearer});
  assert.equal(session.status,200);
  const data=await session.json();
  assert.equal(data.companyId,result.companyId);
  assert.equal(data.syncEnabled,false);
  assert.equal(data.writesEnabled,false);
  assert.ok(!('token' in data),'Sessao nao ecoa token');
  const nc=await fetch(base+'nonconformities',{headers:bearer});
  assert.equal(nc.status,401,'Bearer nativo nao autoriza rotas Web');
  const photo=await fetch(base+'evidence',{headers:bearer});
  assert.equal(photo.status,401);
  // Rotas nativas NOVAS somente leitura, autenticadas e filtradas pela empresa da sessao.
  const readNcs=await fetch(base+'native/data/nonconformities',{headers:bearer});
  assert.equal(readNcs.status,200);
  const ncItems=await readNcs.json();
  assert.equal(ncItems.readOnly,true);
  assert.equal(ncItems.syncEnabled,false);
  assert.ok(Array.isArray(ncItems.items));
  const readInspections=await fetch(base+'native/data/inspections',{headers:bearer});
  assert.equal(readInspections.status,200);
  const inspectionItems=await readInspections.json();
  assert.ok(Array.isArray(inspectionItems.items));
  assert.equal(inspectionItems.readOnly,true);
  // URL com empresa forjada NAO muda escopo: ID vem apenas do token validado.
  const forged=await fetch(base+'native/data/nonconformities?companyId=20000000-0000-4000-8000-000000000002',
    {headers:bearer});
  assert.equal(forged.status,200);
  assert.deepEqual((await forged.json()).items,ncItems.items);
  for(const [method,path] of [
    ['POST','native/data/nonconformities'],
    ['PATCH','native/data/inspections'],
  ]){
    const denied=await fetch(base+path,{method,headers:bearer});
    assert.equal(denied.status,405);
  }
  assert.equal((await fetch(base+'native/data/nonconformities')).status,401);
  const forbiddenSync=await fetch(base+'native/sync/push',{method:'POST',headers:bearer});
  assert.equal(forbiddenSync.status,404,'Nenhum envio esta habilitado');
  const mixed=await fetch(base+'native/auth/session',{
   headers:{...bearer,cookie:'__Host-auditar_sst=forjado'},
  });
  assert.equal(mixed.status,403);
  const logout=await fetch(base+'native/auth/logout',{method:'POST',headers:bearer});
  assert.equal(logout.status,200);
  assert.equal((await fetch(base+'native/auth/session',{headers:bearer})).status,401);
  assert.equal((await fetch(base+'native/data/nonconformities',{headers:bearer})).status,401);
  assert.equal((await fetch(base+'native/auth/logout',{method:'POST',headers:bearer})).status,401);
  // A role de dados RLS nao deve poder consultar tokens nativos nem senhas.
  const direct=await dataPool.connect();
  try{
   await direct.query('BEGIN');await direct.query('SET LOCAL ROLE sst_app_runtime');
   await assert.rejects(direct.query('SELECT token_hash FROM sst.native_session'),x=>x.code==='42501');
   await direct.query('ROLLBACK');
  }finally{direct.release();}
 }finally{
  await new Promise((resolve,reject)=>app.close(err=>err?reject(err):resolve()));
  await Promise.all([dataPool.end(),authPool.end()]);
 }
});

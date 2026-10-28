import test from 'node:test';
import assert from 'node:assert/strict';
import {once} from 'node:events';
import {cipaToken,CIPA_COOKIE,createCipaPortalAuth} from './cipaPortalAuth.mjs';
import {nextPortalStatus,portalId,portalText,withCipaMember,createCipaPortalService} from './cipaPortalService.mjs';
import {csrfForToken} from './authService.mjs';
import {createApp} from './server.mjs';
const UUID='10000000-0000-4000-8000-000000000001',token='a'.repeat(43),origin='https://hml.invalid';
test('member cookie is exclusive, bounded and rejects ambiguity',()=>{
  assert.equal(cipaToken({headers:{cookie:`${CIPA_COOKIE}=${token}`}}),token);
  for(const cookie of [`__Host-auditar_sst=${token}`,`${CIPA_COOKIE}=${token};${CIPA_COOKIE}=${token}`,`${CIPA_COOKIE}=${token}=extra`,`${CIPA_COOKIE}=short`,'x'.repeat(4097)])assert.equal(cipaToken({headers:{cookie}}),null);
});
test('auth requires fixed HTTPS origin, CSRF and separate member token',async()=>{
  for(const allowedOrigin of ['http://local','https://hml.invalid/path','https://hml.invalid/'])assert.throws(()=>createCipaPortalAuth({allowedOrigin}));
  const auth=createCipaPortalAuth({allowedOrigin:origin});
  assert.throws(()=>auth.mutation({headers:{origin}}),e=>e.code==='CSRF_DENIED');
  assert.throws(()=>auth.mutation({headers:{origin:'https://evil.invalid',cookie:`${CIPA_COOKIE}=${token}`,'x-csrf-token':csrfForToken(token)}}),e=>e.code==='ORIGIN_DENIED');
  auth.mutation({headers:{origin,cookie:`${CIPA_COOKIE}=${token}`,'x-csrf-token':csrfForToken(token)}});
  assert.equal(await auth.principal({headers:{cookie:`__Host-auditar_sst=${token}`}}),null);
});
test('member cannot validate, reopen completed action or bypass transition graph',()=>{
  for(const [from,to] of [['aberta','andamento'],['aberta','aguardando_validacao'],['andamento','aguardando_validacao'],['aguardando_validacao','andamento']])assert.equal(nextPortalStatus(from,to,false),to);
  for(const from of ['aberta','andamento','aguardando_validacao','concluida'])assert.throws(()=>nextPortalStatus(from,'concluida',false));
  assert.throws(()=>nextPortalStatus('concluida','andamento',false));
  assert.equal(nextPortalStatus('aguardando_validacao','concluida',true),'concluida');
  assert.equal(nextPortalStatus('concluida','andamento',true),'andamento');
  assert.throws(()=>nextPortalStatus('aberta','concluida',true));
});
test('boundary rejects invalid identifiers and overlong messages',()=>{
  assert.equal(portalId(UUID),UUID);assert.throws(()=>portalId("' OR 1=1"));assert.throws(()=>portalText(''));assert.throws(()=>portalText('x'.repeat(2001)));assert.equal(portalText('  teste  '),'teste');
});
test('member transaction refuses staff identity or temporary password without DB access',async()=>{
  const pool={connect:()=>{throw Error('must not connect');}};
  for(const p of [null,{companyId:UUID,userId:UUID,role:'adm'},{portal:'cipa',companyId:UUID,accountId:UUID,mustChangePassword:true}])await assert.rejects(withCipaMember(pool,p,()=>{}),e=>[401,403].includes(e.status));
});
test('member transaction sets least privileged role and both scope keys, then rolls back safely',async()=>{
  const seen=[];let released=false;const db={query:async(q,args)=>{seen.push([q,args]);return{rows:[]};},release:()=>{released=true;}};
  const p={portal:'cipa',companyId:UUID,accountId:UUID,mustChangePassword:false};
  await assert.rejects(withCipaMember({connect:async()=>db},p,async()=>{throw Error('test');}));
  assert.equal(seen[1][0],'SET LOCAL ROLE sst_cipa_runtime');assert.deepEqual(seen[2][1],[UUID,UUID]);assert.equal(seen.at(-1)[0],'ROLLBACK');assert.equal(released,true);
});
test('account management never promotes clients or technicians',async()=>{
  const s=createCipaPortalService(null);
  for(const role of ['cliente','tecnico']){
    const p={companyId:UUID,userId:UUID,role};
    assert.throws(()=>s.accounts(p),e=>e.status===403);
    await assert.rejects(s.createAccount(p,UUID,{}),e=>e.status===403);
    await assert.rejects(s.reset(p,UUID,{}),e=>e.status===403);
    assert.throws(()=>s.revoke(p,UUID,{}),e=>e.status===403);
  }
});
test('portal routes disabled by default; no spoofed headers grant access',async()=>{
  const app=createApp();app.listen(0,'127.0.0.1');await once(app,'listening');
  try{for(const path of ['cipa-portal/auth/session','cipa-portal/mandates','cipa-portal-admin/accounts']){
    const r=await fetch(`http://127.0.0.1:${app.address().port}/api/v1/${path}`,{headers:{'x-role':'adm','x-company-id':UUID}});
    assert.equal(r.status,404);assert.equal((await r.json()).code,'CIPA_PORTAL_DISABLED');
  }}finally{await new Promise(r=>app.close(r));}
});

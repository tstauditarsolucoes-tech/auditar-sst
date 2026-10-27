// Validacao HTTP do servidor de homologacao privado dentro da CI descartavel.
import assert from 'node:assert/strict';
const origin='https://homologacao-ci.auditarsolucoes.invalid';
if (process.env.AUDITAR_SST_EPHEMERAL_CI_DB!=='FAKE_DATA_CI_ONLY') {
  throw new Error('Smoke privado permitido somente CI efemera');
}
const base='http://127.0.0.1:3000/api/v1/';
const health=await fetch(base+'health');
assert.equal(health.status,200);
assert.equal((await health.json()).productionDataConnected,false);
const unauth=await fetch(base+'auth/session');
assert.equal(unauth.status,401);
const login=await fetch(base+'auth/login',{
  method:'POST',
  headers:{'content-type':'application/json',origin},
  body:JSON.stringify({email:'tecnico-ci-a@example.invalid',password:'SenhaFicticiaCI-2026!'}),
});
assert.equal(login.status,200,'Login no container privado deve estar ativo na CI');
const session=await login.json();
const cookie=login.headers.get('set-cookie').split(';')[0];
assert.equal(session.role,'tecnico');
const nc=await fetch(base+'nonconformities',{headers:{cookie}});
assert.equal(nc.status,200);
const logout=await fetch(base+'auth/logout',{
  method:'POST',headers:{cookie,origin,'x-csrf-token':session.csrfToken},
});
assert.equal(logout.status,200);
const revoked=await fetch(base+'auth/session',{headers:{cookie}});
assert.equal(revoked.status,401);
process.stdout.write('PRIVATE_AUTH_BOOTSTRAP_SMOKE_OK\n');

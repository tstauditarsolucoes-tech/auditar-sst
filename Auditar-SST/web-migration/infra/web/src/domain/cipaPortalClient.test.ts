import test from 'node:test';
import assert from 'node:assert/strict';
import {portalRequest,PortalError,shortDate} from '../cipaPortalClient.ts';
test('portal refuses SPA fallback HTML and never treats it as authenticated',async t=>{
  t.mock.method(globalThis,'fetch',async()=>new Response('<html>SPA fallback</html>',{headers:{'content-type':'text/html'}}));
  await assert.rejects(portalRequest('cipa-portal/auth/session'),e=>e instanceof PortalError&&e.code==='INVALID_RESPONSE');
});
test('empty JSON cannot create a portal session',async t=>{
  t.mock.method(globalThis,'fetch',async()=>Response.json({}));
  await assert.rejects(portalRequest('cipa-portal/auth/login',{companyId:'test',email:'test',password:'synthetic'}),e=>e instanceof PortalError&&e.code==='INVALID_RESPONSE');
});
test('portal mutation sends CSRF and same-origin cookie without local persistence',async t=>{
  let options:RequestInit|undefined;
  t.mock.method(globalThis,'fetch',async(_url:unknown,init:RequestInit)=>{options=init;return Response.json({item:{id:'synthetic'}});});
  await portalRequest('cipa-portal/mandates/synthetic/entries',{message:'synthetic'},'csrf-synthetic');
  assert.equal(options?.credentials,'same-origin');assert.equal(options?.cache,'no-store');assert.equal(options?.method,'POST');
  assert.equal((options?.headers as Record<string,string>)['X-CSRF-Token'],'csrf-synthetic');
});
test('disabled and expired sessions surface specific errors',async t=>{
  t.mock.method(globalThis,'fetch',async()=>Response.json({code:'CIPA_PORTAL_DISABLED'},{status:404}));
  await assert.rejects(portalRequest('cipa-portal/auth/session'),e=>e instanceof PortalError&&e.code==='CIPA_PORTAL_DISABLED');
});
test('calendar due date is not shifted by browser timezone',()=>{assert.equal(shortDate('2027-02-01T00:00:00.000Z'),'01/02/2027');});

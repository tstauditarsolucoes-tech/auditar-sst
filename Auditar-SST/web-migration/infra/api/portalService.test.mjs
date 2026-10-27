import assert from 'node:assert/strict';
import test from 'node:test';
import {createPortalService} from './portalService.mjs';
const companyId='10000000-0000-4000-8000-000000000001';
const userId='11000000-0000-4000-8000-000000000001';
const principal={companyId,userId,role:'gestor'};
test('portal: negado sem banco ou sessao verificada',async()=>{
  const svc=createPortalService();
  await assert.rejects(svc.dashboard(principal),e=>e.code==='DATABASE_UNAVAILABLE');
  await assert.rejects(svc.threads({companyId,userId,role:'superuser'}),e=>e.code==='UNAUTHENTICATED');
  await assert.rejects(svc.team(null),e=>e.code==='UNAUTHENTICATED');
});
test('portal: nao aceita identificadores sem validacao e faz rollback',async()=>{
  const sql=[];
  const pool={connect:async()=>({
    query:async(q)=>{sql.push(q);return {rows:[],rowCount:0};},
    release:()=>{},
  })};
  const svc=createPortalService(pool);
  await assert.rejects(svc.thread(principal,'invalido'),e=>e.code==='INVALID_ID');
  assert.ok(sql.includes('ROLLBACK'));
  await assert.rejects(svc.createThread(principal,{subject:'',message:'oi',clientRequestId:userId}),e=>e.code==='INVALID_INPUT');
  await assert.rejects(svc.reply(principal,'invalido',{message:'oi',clientRequestId:userId}),e=>e.code==='INVALID_ID');
});

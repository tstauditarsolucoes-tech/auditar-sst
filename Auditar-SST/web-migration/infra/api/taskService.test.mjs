import assert from 'node:assert/strict';
import test from 'node:test';
import { createTaskService } from './taskService.mjs';
import { ApiError } from './ncService.mjs';

const tech={companyId:'10000000-0000-4000-8000-000000000001',
  userId:'11000000-0000-4000-8000-000000000001',role:'tecnico'};
test('agenda sem banco falha fechada',async()=>{
  const service=createTaskService();
  await assert.rejects(service.list(tech),err=>err instanceof ApiError&&err.status===503);
});
test('agenda recusa principal invalido independentemente de header',async()=>{
  const service=createTaskService();
  await assert.rejects(service.create({...tech,role:'root'},{}),
    err=>err instanceof ApiError&&err.status===401);
});

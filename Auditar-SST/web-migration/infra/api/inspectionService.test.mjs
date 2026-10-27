import test from 'node:test';
import assert from 'node:assert/strict';
import { createInspectionService } from './inspectionService.mjs';
import { ApiError } from './ncService.mjs';

const tech={companyId:'10000000-0000-4000-8000-000000000001',
  userId:'11000000-0000-4000-8000-000000000001',role:'tecnico'};
test('vistoria sem banco nao cria registros nem bypass de seguranca',async()=>{
  const service=createInspectionService();
  await assert.rejects(service.list(tech),e=>e instanceof ApiError&&e.status===503);
  await assert.rejects(service.create(tech,{}),e=>e instanceof ApiError&&e.status===503);
});
test('vistoria recusa identidade forjada ou incompleta mesmo antes de consultar banco',async()=>{
  const service=createInspectionService();
  await assert.rejects(service.list({...tech,companyId:'empresa-qualquer'}),
    e=>e instanceof ApiError&&e.status===401);
  await assert.rejects(service.complete({...tech,role:'root'},tech.companyId),
    e=>e instanceof ApiError&&e.status===401);
});

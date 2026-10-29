import test from 'node:test';
import assert from 'node:assert/strict';
import {createReportService} from './reportService.mjs';
const p={companyId:'10000000-0000-4000-8000-000000000001',
  userId:'11000000-0000-4000-8000-000000000001',role:'tecnico'};
test('relatorio PDF da homologacao nao abre banco desconfigurado',async()=>{
  const reports=createReportService(undefined);
  await assert.rejects(reports.inspectionPdf(p,'10000000-0000-4000-8000-000000000001'),
    e=>e.code==='DATABASE_UNAVAILABLE');
});

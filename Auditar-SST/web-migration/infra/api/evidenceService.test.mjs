import test from 'node:test';
import assert from 'node:assert/strict';
import {createEvidenceService} from './evidenceService.mjs';
const companyId='10000000-0000-4000-8000-000000000001';
const userId='11000000-0000-4000-8000-000000000001';
const p={companyId,userId,role:'tecnico'};
const png='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/ZQoAAAAASUVORK5CYII=';
test('evidencia de homologacao falha fechada sem volume configurado',async()=>{
  const svc=createEvidenceService();
  await assert.rejects(svc.upload(p,{}),e=>e.code==='STORAGE_DISABLED');
  await assert.rejects(svc.list(p,{inspectionId:userId}),e=>e.code==='STORAGE_DISABLED');
});
test('valida mime, origem e tamanho antes de tocar o banco',async()=>{
  const svc=createEvidenceService(null,'/tmp/evidencia-piloto-inexistente');
  await assert.rejects(svc.upload(p,{mimeType:'image/svg+xml',contentBase64:png}),e=>e.code==='UNSUPPORTED_MEDIA');
  await assert.rejects(svc.upload(p,{mimeType:'image/png',contentBase64:'??'}),e=>e.code==='INVALID_IMAGE');
  await assert.rejects(svc.upload(p,{mimeType:'image/jpeg',contentBase64:png}),e=>e.code==='MEDIA_SIGNATURE');
  await assert.rejects(svc.upload(p,{
    mimeType:'image/png',contentBase64:png,clientRequestId:userId,nonConformityId:userId,
  }),e=>e.code==='DATABASE_UNAVAILABLE');
});

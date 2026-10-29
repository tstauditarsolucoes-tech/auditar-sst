// SOMENTE CI efemera: bytes de imagem sintetica sem dados de clientes.
import test from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import {mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createEvidenceService} from './evidenceService.mjs';
import {createNcService} from './ncService.mjs';
import {createInspectionService} from './inspectionService.mjs';
const A='10000000-0000-4000-8000-000000000001';
const B='20000000-0000-4000-8000-000000000002';
const staff={companyId:A,userId:'11000000-0000-4000-8000-000000000001',role:'tecnico'};
const customer={companyId:A,userId:'11000000-0000-4000-8000-000000000002',role:'cliente'};
const outside={companyId:B,userId:'22000000-0000-4000-8000-000000000002',role:'tecnico'};
const png='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/ZQoAAAAASUVORK5CYII=';
test('foto privada: salva bytes, confere hash e restringe empresas/perfis',async()=>{
  assert.equal(process.env.AUDITAR_SST_EPHEMERAL_CI_DB,'FAKE_DATA_CI_ONLY');
  assert.equal(process.env.PGHOST,'db');
  assert.equal(process.env.PGUSER,'sst_ci_runner');
  assert.equal(process.env.PGDATABASE,'auditar_web_hml');
  const store=await mkdtemp(join(tmpdir(),'auditar-evidence-ci-'));
  const pool=new pg.Pool({max:3,connectionTimeoutMillis:5000});
  try {
    const evidence=createEvidenceService(pool,store);
    const nc=await createNcService(pool).create(staff,{
      shortTitle:'Foto de extintor ficticio',description:'Somente no teste',probability:3,severity:4,
    });
    const payload={
      mimeType:'image/png',contentBase64:png,nonConformityId:nc.id,
      clientRequestId:'b1000000-0000-4000-8000-000000000001',
    };
    const created=await evidence.upload(customer,payload);
    assert.equal(created.replayed,false);
    assert.equal(created.item.kind,'foto');
    const same=await evidence.upload(customer,payload);
    assert.equal(same.replayed,true);
    assert.equal(same.item.id,created.item.id);
    const files=await evidence.list(customer,{nonConformityId:nc.id});
    assert.equal(files.length,1);
    assert.ok(!('object_key' in files[0]));
    const output=await evidence.download(customer,created.item.id);
    assert.equal(output.data.toString('base64'),png);
    assert.equal(output.mimeType,'image/png');
    assert.deepEqual(await evidence.list(outside,{nonConformityId:nc.id}),[]);
    await assert.rejects(evidence.download(outside,created.item.id),e=>e.status===404);
    await assert.rejects(evidence.upload(customer,{
      ...payload,contentBase64:'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/ZQoAAAAASUVORK5CYII=',
      nonConformityId:'20000000-0000-4000-8000-000000000002',
      clientRequestId:'b1000000-0000-4000-8000-000000000002',
    }),e=>e.status===404);
    const inspection=await createInspectionService(pool).create(staff,{
      inspectionType:'vistoria',title:'Vistoria ficticia foto',description:'',
      clientRequestId:'b1000000-0000-4000-8000-000000000003',
    });
    await assert.rejects(evidence.upload(customer,{
      mimeType:'image/png',contentBase64:png,inspectionId:inspection.id,
      clientRequestId:'b1000000-0000-4000-8000-000000000004',
    }),e=>e.status===403);
    const staffPhoto=await evidence.upload(staff,{
      mimeType:'image/png',contentBase64:png,inspectionId:inspection.id,
      clientRequestId:'b1000000-0000-4000-8000-000000000005',
    });
    await assert.rejects(evidence.download(customer,staffPhoto.item.id),e=>e.status===404);
    assert.equal((await evidence.download(staff,staffPhoto.item.id)).data.toString('base64'),png);
  } finally{
    await pool.end();
    await rm(store,{recursive:true,force:true});
  }
});

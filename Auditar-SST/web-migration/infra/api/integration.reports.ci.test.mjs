// SOMENTE CI efemera e contas ficticias: PDF com achados e foto em memoria.
import test from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import {mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createReportService} from './reportService.mjs';
import {createInspectionService} from './inspectionService.mjs';
import {createEvidenceService} from './evidenceService.mjs';
const A='10000000-0000-4000-8000-000000000001';
const B='20000000-0000-4000-8000-000000000002';
const techA={companyId:A,userId:'11000000-0000-4000-8000-000000000001',role:'tecnico'};
const clientA={companyId:A,userId:'11000000-0000-4000-8000-000000000002',role:'cliente'};
const techB={companyId:B,userId:'22000000-0000-4000-8000-000000000002',role:'tecnico'};
const png='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/ZQoAAAAASUVORK5CYII=';
test('gera PDF concluido com dois achados por pagina e isola empresa',async()=>{
  assert.equal(process.env.AUDITAR_SST_EPHEMERAL_CI_DB,'FAKE_DATA_CI_ONLY');
  assert.equal(process.env.PGHOST,'db');
  assert.equal(process.env.PGUSER,'sst_ci_runner');
  assert.equal(process.env.PGDATABASE,'auditar_web_hml');
  const dir=await mkdtemp(join(tmpdir(),'auditar-pdf-ci-'));
  const pool=new pg.Pool({max:3,connectionTimeoutMillis:5000});
  try{
    const inspections=createInspectionService(pool);
    const report=createReportService(pool,dir);
    const inspection=await inspections.create(techA,{
      inspectionType:'vistoria',title:'Ronda ficticia PDF',sector:'Area de teste',
      location:'Extintor hipotetico',description:'Apenas para CI, sem dados pessoais.',
      clientRequestId:'c1000000-0000-4000-8000-000000000001',
    });
    const id=inspection.id;
    await assert.rejects(report.inspectionPdf(techA,id),e=>e.code==='REPORT_NOT_FINAL');
    const created=[];
    for(let i=0;i<3;i++){
      created.push(await inspections.addFinding(techA,id,{
        shortTitle:'Achado teste '+(i+1),
        description:'Foto e recomendacao ficticias de seguranca.',
        recommendation:'Corrigir a NC de teste, fotografar e validar a correção fictícia.',
        probability:3,severity:4,
        clientRequestId:'c1000000-0000-4000-8000-00000000000'+(i+2),
      }));
    }
    await createEvidenceService(pool,dir).upload(techA,{
      mimeType:'image/png',contentBase64:png,nonConformityId:created[0].id,
      clientRequestId:'c1000000-0000-4000-8000-000000000008',
    });
    await inspections.complete(techA,id);
    const pdf=await report.inspectionPdf(clientA,id);
    assert.equal(pdf.subarray(0,5).toString('ascii'),'%PDF-');
    assert.ok(pdf.length>1500);
    // 1 capa + 2 paginas de achados (ate 2/pagina) + 1 pagina foto ampliada.
    assert.ok((pdf.toString('latin1').match(/\/Type \/Page\b/g)||[]).length>=4);
    await assert.rejects(report.inspectionPdf(techB,id),e=>e.status===404);
  }finally{
    await pool.end();
    await rm(dir,{recursive:true,force:true});
  }
});

// Exclusivamente CI efemera com identidades ficticias. Nunca executar na VPS com dados reais.
import assert from 'node:assert/strict';
import test from 'node:test';
import pg from 'pg';
import {createTrainingService} from './trainingService.mjs';
import {createTrainingReportService} from './trainingReportService.mjs';
const A='10000000-0000-4000-8000-000000000001';
const B='20000000-0000-4000-8000-000000000002';
const techA={companyId:A,userId:'11000000-0000-4000-8000-000000000001',role:'tecnico'};
const clientA={companyId:A,userId:'11000000-0000-4000-8000-000000000002',role:'cliente'};
const techB={companyId:B,userId:'22000000-0000-4000-8000-000000000002',role:'tecnico'};
const requestId=n=>'96000000-0000-4000-8000-'+String(n).padStart(12,'0');
test('Participantes ficticios: idempotencia, RLS, PDF multipagina e acesso negado ao cliente',async()=>{
 assert.equal(process.env.AUDITAR_SST_EPHEMERAL_CI_DB,'FAKE_DATA_CI_ONLY');
 assert.equal(process.env.PGHOST,'db');
 assert.equal(process.env.PGDATABASE,'auditar_web_hml');
 assert.equal(process.env.PGUSER,'sst_ci_runner');
 const pool=new pg.Pool({max:3,connectionTimeoutMillis:5000});
 try{
  const role=await pool.query('SELECT current_user,rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user');
  assert.equal(role.rows[0].rolsuper,false);
  assert.equal(role.rows[0].rolbypassrls,false);
  const service=createTrainingService(pool);
  const reports=createTrainingReportService(pool);
  const training=await service.create(techA,{
   kind:'dds',title:'DDS CI treinamento ficticio',sector:'Teste',nrReference:'NR-06',
   instructor:'Instrutor FICTICIO',plannedAt:'2027-02-18T13:00:00.000Z',
   durationMinutes:20,participantsCount:16,clientRequestId:requestId(1),
  });
  const attend={
   displayName:'Colaborador TESTE',
   presence:'nao_confirmada',note:'Sem assinatura',clientRequestId:requestId(2),
  };
  await assert.rejects(service.addParticipant(clientA,training.id,attend),
    e=>e.status===403);
  await assert.rejects(service.addParticipant(techB,training.id,attend),
    e=>e.status===404);
  const added=await service.addParticipant(techA,training.id,attend);
  assert.equal(added.presence,'nao_confirmada');
  assert.equal((await service.addParticipant(techA,training.id,attend)).id,added.id);
  await assert.rejects(service.addParticipant(techA,training.id,{
   ...attend,displayName:'Nome diferente',
  }),e=>e.code==='IDEMPOTENCY_CONFLICT');
  await assert.rejects(service.addParticipant(techA,training.id,{
   ...attend,displayName:'Vazio',presence:'assinado',clientRequestId:requestId(3),
  }),e=>e.code==='INVALID_INPUT');
  for(let n=3;n<=17;n++){
    await service.addParticipant(techA,training.id,{
      displayName:'Pessoa FICTICIA '+n,presence:'declarada',
      clientRequestId:requestId(n),
    });
  }
  const detail=await service.get(techA,training.id);
  assert.equal(detail.attendance.length,16);
  assert.equal(detail.attendance.filter(x=>x.presence==='declarada').length,15);
  await assert.rejects(service.get(clientA,training.id),e=>e.status===403);
  const pdf=await reports.attendancePdf(techA,training.id);
  assert.equal(pdf.toString('ascii',0,5),'%PDF-');
  assert.ok(pdf.length>1700);
  assert.ok((pdf.toString('latin1').match(/\/Type \/Page\b/g)||[]).length>=2);
  await assert.rejects(reports.attendancePdf(clientA,training.id),e=>e.status===403);
  await assert.rejects(reports.attendancePdf(techB,training.id),e=>e.status===404);
  const foreign=await service.create(techB,{
    kind:'treinamento',title:'Empresa B CI',plannedAt:null,durationMinutes:null,
    participantsCount:null,clientRequestId:requestId(20),
  });
  await assert.rejects(service.addParticipant(techA,foreign.id,{
    displayName:'Outro TESTE',clientRequestId:requestId(21),
  }),e=>e.status===404);
 }finally{await pool.end();}
});

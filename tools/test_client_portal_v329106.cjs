const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const file=process.argv[2];
if(!file) throw Error('Uso: node test_client_portal_v329106.cjs ClientPortal.gs');
const source=fs.readFileSync(file,'utf8');
const context=vm.createContext({console,Date,Number,String,JSON,Array,Math});
vm.runInContext(source,context,{filename:file});
let actor={
 id:'client-A',name:'Cliente A',role:'cliente',active:true,allCompanies:false,
 companyIds:['A'],clientPermissions:{
  indicadores:true,naoConformidades:true,acoesCorretivas:true,
  relatorios:true,enviarEvidencia:true},sessionPlatform:'client_portal'
};
context.authUserFromToken_=()=>actor;
context.userCanAccessCompany_=(user,id)=>user.role==='admin'||(!user.allCompanies&&user.companyIds.length===1&&user.companyIds[0]===id);
context.auditAuthEvent_=()=>{};
context.DEVICE_SYNC_SHEET='DispositivosDados';
context.getSheet_=name=>{
 assert.equal(name,'DispositivosDados');
 return {getLastRow:()=>1,getLastColumn:()=>10};
};

context.clientPortalFindSnapshot_=id=>id==='A'?{
 updatedAt:'2026-09-22T12:00:00Z',
 payload:{
  accessToken:'NEVER_EXPOSE_THIS',
  medicalExams:[{diagnosis:'secret'}],
  company:{id:'A',name:'Empresa A',cnpj:'secret'},
  summary:{conformity:78,ncPending:1,ncInProgress:2,ncAwaiting:0,ncOverdue:1},
  openNonConformities:[{code:'NC-A',description:'Proteção ausente',
    cpf:'DO_NOT_EXPOSE',companyId:'B',status:'ABERTA'}],
  pendingActions:[{ncCode:'NC-A',correctiveAction:'Instalar proteção',status:'PENDENTE',privateNotes:'secret'}],
  reports:[{id:'R-A',title:'Relatório',driveFileId:'SECRET_ID'}]
 }
}:null;
const data=context.clientPortalData('valid');
assert.equal(data.ok,true);
assert.equal(data.companies.length,1);
assert.equal(data.companies[0].id,'A');
assert.equal(data.companies[0].nonConformities[0].id,'NC-A');
assert.equal(data.companies[0].summary.openNcs,4);
assert.equal(data.companies[0].actions[0].action,'Instalar proteção');
const encoded=JSON.stringify(data);
for(const secret of ['NEVER_EXPOSE_THIS','DO_NOT_EXPOSE','SECRET_ID','diagnosis','privateNotes','cnpj']){
 assert.equal(encoded.includes(secret),false,'Vazamento de '+secret);
}
assert.equal(context.clientPortalSubmitEvidence('valid','B','NC-A','teste',null).code,'ACCESS_DENIED');
assert.equal(context.clientPortalSubmitEvidence('valid','A','NC-OUTRA','teste',null).code,'ACCESS_DENIED');
assert.equal(context.clientPortalEvidenceQueue('valid','A').code,'ACCESS_DENIED');
assert.equal(context.clientPortalReviewEvidence('valid','1','VALIDADA').code,'ACCESS_DENIED');
actor.clientPermissions.enviarEvidencia=false;
assert.equal(context.clientPortalEvidencePhoto('valid','1').code,'ACCESS_DENIED');
assert.equal(context.clientPortalMyEvidence('valid','A').code,'ACCESS_DENIED');
actor.clientPermissions.enviarEvidencia=true;
context.publicPanelPayload_=value=>JSON.parse(JSON.stringify(value));
const shared=context.clientPortalSharePayload_({
 accessToken:'SECRET',syncKey:'SECRET',notifications:{email:'secret'},
 workforceDetails:[{name:'Pessoa'}],company:{id:'A',name:'Empresa A',email:'private@example.com'}
});
assert.equal(shared.accessToken,undefined);
assert.equal(shared.syncKey,undefined);
assert.equal(shared.notifications,undefined);
assert.equal(shared.workforceDetails,undefined);
assert.equal(shared.company.email,undefined);

const pdfId='REPORT_DRIVE_FILE_VALID_123456789';
context.clientPortalFindSnapshot_=id=>id==='A'?{
 updatedAt:'2026-09-27T12:00:00Z',payload:{company:{id:'A',name:'Empresa A'},
  reports:[{id:'R-PDF',title:'Relatório publicado',driveFileId:pdfId}]
 }}:null;
context.Utilities={base64Encode:bytes=>Buffer.from(bytes).toString('base64')};
context.DriveApp={getFileById:id=>{
 assert.equal(id,pdfId);
 return {getBlob:()=>({getContentType:()=> 'application/pdf',
  getBytes:()=>[37,80,68,70,45,49,46,52]})};
}};
assert.equal(context.clientPortalReportPdf('valid','B','R-PDF').code,'ACCESS_DENIED');
assert.equal(context.clientPortalReportPdf('valid','A','OUTRO').ok,false);
actor.clientPermissions.relatorios=false;
assert.equal(context.clientPortalReportPdf('valid','A','R-PDF').code,'ACCESS_DENIED');
actor.clientPermissions.relatorios=true;
const pdf=context.clientPortalReportPdf('valid','A','R-PDF');
assert.equal(pdf.ok,true);assert.equal(pdf.mimeType,'application/pdf');
assert.equal(Buffer.from(pdf.base64,'base64').toString('utf8'),'%PDF-1.4');
assert.equal(JSON.stringify(context.clientPortalData('valid')).includes(pdfId),false);
actor={...actor,companyIds:['A','B']};
assert.equal(context.clientPortalAuthorizedUser_('valid'),null);
actor={...actor,role:'admin',companyIds:[],allCompanies:true};
assert.equal(context.clientPortalAuthorizedUser_('valid').role,'admin');
console.log('CLIENT_PORTAL_TENANT_PRIVACY_TESTS_OK');

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
context.clientPortalFindSnapshot_=id=>id==='A'?{
 updatedAt:'2026-09-22T12:00:00Z',
 payload:{
  accessToken:'NEVER_EXPOSE_THIS',
  medicalExams:[{diagnosis:'secret'}],
  company:{id:'A',name:'Empresa A',cnpj:'secret'},
  summary:{conformity:78,openNcs:1},
  nonConformities:[{id:'NC-A',title:'Proteção ausente',description:'Descrição',
    cpf:'DO_NOT_EXPOSE',companyId:'B',status:'ABERTA'}],
  actions:[{id:'AC-A',title:'Instalar proteção',status:'PENDENTE',privateNotes:'secret'}],
  reports:[{id:'R-A',title:'Relatório',driveFileId:'SECRET_ID'}]
 }
}:null;
const data=context.clientPortalData('valid');
assert.equal(data.ok,true);
assert.equal(data.companies.length,1);
assert.equal(data.companies[0].id,'A');
assert.equal(data.companies[0].nonConformities[0].id,'NC-A');
const encoded=JSON.stringify(data);
for(const secret of ['NEVER_EXPOSE_THIS','DO_NOT_EXPOSE','SECRET_ID','diagnosis','privateNotes','cnpj']){
 assert.equal(encoded.includes(secret),false,'Vazamento de '+secret);
}
assert.equal(context.clientPortalSubmitEvidence('valid','B','NC-A','teste',null).code,'ACCESS_DENIED');
assert.equal(context.clientPortalSubmitEvidence('valid','A','NC-OUTRA','teste',null).code,'ACCESS_DENIED');
assert.equal(context.clientPortalEvidenceQueue('valid','A').code,'ACCESS_DENIED');
assert.equal(context.clientPortalReviewEvidence('valid','1','VALIDADA').code,'ACCESS_DENIED');
assert.equal(context.clientPortalEvidencePhoto('valid','1').code,'ACCESS_DENIED');
actor={...actor,companyIds:['A','B']};
assert.equal(context.clientPortalAuthorizedUser_('valid'),null);
actor={...actor,role:'admin',companyIds:[],allCompanies:true};
assert.equal(context.clientPortalAuthorizedUser_('valid').role,'admin');
console.log('CLIENT_PORTAL_TENANT_PRIVACY_TESTS_OK');

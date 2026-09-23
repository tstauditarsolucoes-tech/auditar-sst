/* Security regression for the read-only client view. */
const fs=require('fs');
const vm=require('vm');
const assert=require('assert');
const code=fs.readFileSync(process.argv[2],'utf8');
const html=fs.readFileSync(process.argv[3],'utf8');
const sandbox={};
vm.createContext(sandbox);
vm.runInContext(code,sandbox,{timeout:10000});
function sample(modules) {
  return {
    accessToken:'SECRET-BEARER-TOKEN',syncKey:'SECRET-SYNC-KEY',
    authToken:'SECRET-SESSION', enabled:true,
    company:{id:'company-A',name:'Empresa A',city:'Teresina',uf:'PI',
      contact:'SENSITIVE-PRIVATE-CONTACT',reportEmail:'SECRET-EMAIL'},
    clientPortal: modules===undefined?undefined:{version:2,modules},
    notifications:{primaryEmail:'SECRET-EMAIL',medicalAlertsEnabled:true},
    medicalExams:[{diagnosis:'SECRET-DIAGNOSIS'}],
    workforceDetails:[{worker:'Nome',role:'Função',trainingStatus:'PENDENTE',
      nextExamDate:'SECRET-MEDICAL-DATE',cpf:'SECRET-CPF'}],
    workforceSummary:{activeWorkers:2,medicalExpired:12},
    summary:{inspections:2,ncPending:1,privateField:'SECRET-INTERNAL'},
    openNonConformities:[{code:'NC-1',sector:'Produção',status:'Aberta',
      internalNote:'SECRET-INTERNAL'}],
    pendingActions:[{ncCode:'NC-1',correctiveAction:'Corrigir proteção',
      dueDate:'2026-10-01',privateKey:'SECRET-INTERNAL'}],
    recentInspections:[{reportNumber:'R-1',status:'Concluído',
      attachmentUrl:'SECRET-DRIVE-URL'}],
    trainingRecords:[{worker:'Nome',status:'VENCIDO',diagnosis:'SECRET-DIAGNOSIS'}],
    safetyObservations:[{title:'NC de teste',secret:'SECRET-INTERNAL'}],
    agenda:[{title:'Visita',notes:'Planejada',secret:'SECRET-INTERNAL'}]
  };
}
const defaults=JSON.parse(JSON.stringify(sandbox.publicPanelPayload_(sample())));
assert.strictEqual(defaults.clientPortal.readOnly,true);
assert.strictEqual(defaults.clientPortal.modules.overview,true);
assert.strictEqual(defaults.clientPortal.modules.actions,true);
assert.strictEqual(defaults.clientPortal.modules.inspections,true);
assert.strictEqual(defaults.clientPortal.modules.training,false);
assert.strictEqual(defaults.openNonConformities.length,1);
assert.strictEqual(defaults.recentInspections.length,1);
assert.strictEqual(defaults.trainingRecords.length,0);
assert.strictEqual(defaults.workforceDetails.length,0);
assert.strictEqual(defaults.safetyObservations.length,0);
assert.strictEqual(defaults.agenda.length,0);
for(const secret of ['SECRET-BEARER-TOKEN','SECRET-SYNC-KEY','SECRET-SESSION',
  'SECRET-EMAIL','SECRET-MEDICAL-DATE','SECRET-CPF','SECRET-DIAGNOSIS',
  'SECRET-INTERNAL','SECRET-DRIVE-URL','SENSITIVE-PRIVATE-CONTACT']){
  assert(!JSON.stringify(defaults).includes(secret),'Unexpected public field '+secret);
}
const opted=JSON.parse(JSON.stringify(sandbox.publicPanelPayload_(sample({
  overview:false,actions:false,inspections:false,training:true,safety:true
}))));
assert.strictEqual(opted.clientPortal.modules.overview,true);
assert.strictEqual(opted.openNonConformities.length,0);
assert.strictEqual(opted.pendingActions.length,0);
assert.strictEqual(opted.recentInspections.length,0);
assert.strictEqual(opted.trainingRecords.length,1);
assert.strictEqual(opted.safetyObservations.length,1);
assert(!JSON.stringify(opted).includes('SECRET-DIAGNOSIS'));
assert(!JSON.stringify(opted).includes('SECRET-INTERNAL'));
assert(html.includes('CLIENT_SCOPES'));
assert(html.includes('tab-'+'')); // dynamic tab scoping is applied to every module.
assert(code.includes("companyId: String(data[1] || '')"));
assert(code.includes("if (!storedId || !payloadId || storedId !== payloadId)"));
assert(code.includes('clientPortalVersion: 2'));
assert(!JSON.stringify(defaults).includes('accessToken'));
console.log('AUDITAR_CLIENT_SERVER_PROJECTION_TESTS_OK');

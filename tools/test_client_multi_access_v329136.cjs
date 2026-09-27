const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const multi=fs.readFileSync(process.argv[2],'utf8');
const portal=fs.readFileSync(process.argv[3],'utf8');
const cache=new Map(),sessions=new Map();
let serial=0;
const ctx=vm.createContext({
 console,Date,Number,String,Array,JSON,Math,PANEL_SHEET:'PainelDados',
 CacheService:{getScriptCache:()=>({
  get:key=>cache.get(key),put:(key,v)=>cache.set(key,v),remove:key=>cache.delete(key)
 })},
 Utilities:{DigestAlgorithm:{SHA_256:'SHA_256'},Charset:{UTF_8:'UTF_8'},
  computeDigest:(_algo,value)=>Array.from(Buffer.from(value)),
  getUuid:()=> 'uuid-'+(++serial)}
});
vm.runInContext(multi,ctx,{filename:'MultiUser.gs'});
vm.runInContext(portal,ctx,{filename:'ClientPortal.gs'});
const admin={id:'admin',name:'Administrador',email:'admin@example.test',role:'admin',
 active:true,allCompanies:true,companyIds:[],clientPermissions:{},
 sessionDeviceId:'pc',sessionPlatform:'windows',rowNumber:2};
const users=[admin];
const records=[
 ['sA','A','Empresa A',true,'2026-09-26T17:00:00Z',JSON.stringify({
  company:{id:'A',name:'Empresa A'},summary:{inspections:8},
  openNonConformities:[{id:'NC-A',description:'Proteção ausente'}],
  reports:[{id:'REPORT-A',title:'Relatório A'}]
 })],
 ['sB','B','Empresa B',true,'2026-09-26T17:00:00Z',JSON.stringify({
  company:{id:'B',name:'Empresa B'},summary:{inspections:2},
  openNonConformities:[{id:'NC-B',description:'Outra empresa'}]
 })]
];
ctx.getSheet_=name=>({
 getLastRow:()=>name==='Usuarios'?users.length+1:name==='PainelDados'?records.length+1:1,
 getRange:()=>({getValues:()=>name==='PainelDados'?records:[],setValue:()=>{},setValues:()=>{}}),
 appendRow:row=>{
  assert.equal(name,'Usuarios');
  users.push({rowNumber:users.length+2,id:row[0],name:row[1],email:row[2],
   passwordHash:row[3],passwordSalt:row[4],role:row[5],active:row[6],
   allCompanies:row[7],companyIds:JSON.parse(row[8]),createdAt:row[9],
   updatedAt:row[10],lastLoginAt:row[11],clientPermissions:JSON.parse(row[12])});
 }
});
ctx.readAuthUsers_=()=>users;
ctx.auditAuthEvent_=()=>{};
ctx.authPasswordHash_=(pwd,salt)=>salt+'|'+pwd;
ctx.authHex_=bytes=>Buffer.from(bytes).toString('hex');
ctx.authCreateSession_=(user,opts)=>{
 const token='test-token-'+user.id;sessions.set(token,{id:user.id,platform:opts.platform});
 return {token};
};
ctx.authUserFromToken_=token=>{
 if(token==='admin-token')return admin;
 const s=sessions.get(token);
 const user=s&&users.find(u=>u.id===s.id&&u.active);
 return user?{...user,sessionPlatform:s.platform,sessionRowNumber:3}:null;
};
const create=(name,email,company,permissions,password)=>ctx.authUserSave_({
 authToken:'admin-token',user:{name,email,role:'cliente',password,
 active:true,allCompanies:false,companyIds:[company],clientPermissions:permissions}
});
const manager=create('Gerente A','gerente@example.test','A',{
 indicadores:true,naoConformidades:true,relatorios:true},'gerente-secret-123');
const board=create('Diretoria A','diretoria@example.test','A',{
 indicadores:true,naoConformidades:false,relatorios:true},'diretoria-secret-456');
const other=create('Contato B','contato@example.test','B',{
 indicadores:true,naoConformidades:true},'contato-secret-789');
for(const x of [manager,board,other])assert.equal(x.ok,true,x.message);
assert.notEqual(manager.user.id,board.user.id);
assert.deepEqual(Array.from(manager.user.companyIds),['A']);
assert.deepEqual(Array.from(board.user.companyIds),['A']);
assert.equal(create('Duplicado','GERENTE@example.test','A',{},'duplicate-secret').ok,false);
const lm=ctx.clientPortalLogin('gerente@example.test','gerente-secret-123');
const ld=ctx.clientPortalLogin('diretoria@example.test','diretoria-secret-456');
const lb=ctx.clientPortalLogin('contato@example.test','contato-secret-789');
for(const x of [lm,ld,lb])assert.equal(x.ok,true,x.message);
assert.notEqual(lm.token,ld.token);
assert.equal(ctx.clientPortalLogin('diretoria@example.test','gerente-secret-123').ok,false);
const dm=ctx.clientPortalData(lm.token),dd=ctx.clientPortalData(ld.token),
 db=ctx.clientPortalData(lb.token);
for(const x of [dm,dd,db])assert.equal(x.ok,true);
assert.deepEqual(Array.from(dm.companies,c=>c.id),['A']);
assert.deepEqual(Array.from(dd.companies,c=>c.id),['A']);
assert.deepEqual(Array.from(db.companies,c=>c.id),['B']);
assert.equal(dm.companies[0].summary.inspections,dd.companies[0].summary.inspections);
assert.equal(dm.companies[0].nonConformities[0].id,'NC-A');
assert.equal(dd.companies[0].nonConformities,undefined);
assert.equal(dd.companies[0].reports[0].id,'REPORT-A');
assert.equal(ctx.userCanAccessCompany_(users[1],'B'),false);
users[1].active=false;
assert.equal(ctx.clientPortalData(lm.token).ok,false);
assert.equal(ctx.clientPortalData(ld.token).ok,true);
console.log('MULTI_CLIENT_ONE_COMPANY_LOGIN_AND_TENANT_ISOLATION_OK');

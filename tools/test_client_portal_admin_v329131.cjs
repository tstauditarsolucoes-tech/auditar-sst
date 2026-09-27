const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const gs=fs.readFileSync(process.argv[2],'utf8');
const html=fs.readFileSync(process.argv[3],'utf8');
const context=vm.createContext({console,Date,Number,String,JSON,Array,Math,PANEL_SHEET:'PainelDados'});
vm.runInContext(gs,context,{filename:'ClientPortal.gs'});
const clients=[
 {id:'client-a',name:'Cliente A',email:'a@example.test',role:'cliente',active:true,
 companyIds:['A'],clientPermissions:{indicadores:true}},
 {id:'staff-b',name:'Equipe B',email:'b@example.test',role:'tecnico',active:true,
 companyIds:[]},
 {id:'admin-c',name:'Admin C',email:'c@example.test',role:'admin',active:true,
 companyIds:[]}
];
let actor={id:'client-a',role:'cliente',active:true,allCompanies:false,companyIds:['A'],
 sessionPlatform:'client_portal'};
let saves=[];
context.authUserFromToken_=()=>actor;
context.authPublicUser_=user=>({id:user.id,name:user.name,email:user.email,role:user.role,
 active:user.active,companyIds:user.companyIds,clientPermissions:user.clientPermissions});
context.readAuthUsers_=()=>clients;
context.normalizeAuthEmail_=input=>String(input||'').trim().toLowerCase();
context.getSheet_=name=>{assert.equal(name,'PainelDados');return {
 getLastRow:()=>3,
 getRange:()=>({getValues:()=>[
 ['token-A','A','Empresa A',true,'','{}'],
 ['token-B','B','Empresa B',false,'','{}']
 ]})
}};
context.authUserSave_=request=>{saves.push(request);return {
 ok:true,user:context.authPublicUser_({...request.user,id:request.user.id||'new-client'})
}};
const input={name:'Contato Cliente',email:'contato@example.test',password:'test-example-strong',
 companyId:'A',active:true,clientPermissions:{indicadores:true,relatorios:true,enviarEvidencia:false}};
assert.equal(context.clientPortalAdminUsers('client-token').code,'ACCESS_DENIED');
assert.equal(context.clientPortalAdminSaveClient('client-token',input).code,'ACCESS_DENIED');
actor={...actor,role:'tecnico'};
assert.equal(context.clientPortalAdminUsers('staff-token').code,'ACCESS_DENIED');
assert.equal(context.clientPortalAdminSaveClient('staff-token',input).code,'ACCESS_DENIED');
assert.equal(saves.length,0);
actor={...actor,id:'admin-c',role:'admin',allCompanies:true,companyIds:[]};
const found=context.clientPortalAdminUsers('admin-token');
assert.equal(found.ok,true);
assert.equal(found.users.length,1);
assert.equal(found.users[0].role,'cliente');
assert.equal(JSON.stringify(found).includes('passwordHash'),false);
assert.equal(context.clientPortalAdminSaveClient('admin-token',{...input,companyId:'B'}).ok,false);
assert.equal(context.clientPortalAdminSaveClient('admin-token',{...input,companyId:'C'}).ok,false);
assert.equal(context.clientPortalAdminSaveClient('admin-token',{...input,id:'admin-c'}).code,'ACCESS_DENIED');
assert.equal(context.clientPortalAdminSaveClient('admin-token',{...input,id:'staff-b'}).code,'ACCESS_DENIED');
assert.equal(saves.length,0);
const result=context.clientPortalAdminSaveClient('admin-token',input);
assert.equal(result.ok,true);
assert.equal(saves.length,1);
assert.equal(saves[0].user.role,'cliente');
assert.equal(saves[0].user.allCompanies,false);
assert.deepEqual(Array.from(saves[0].user.companyIds),['A']);
assert.equal(saves[0].user.clientPermissions.enviarEvidencia,false);
assert.equal(Object.prototype.hasOwnProperty.call(saves[0],'syncKey'),false);
assert.equal(gs.includes('function clientPortalBootstrapAdmin('),false);
assert.equal(html.includes('id="adminAccess"'),true);
assert.equal(html.includes('clientPortalAdminUsers'),true);
assert.equal(html.includes('clientPortalAdminSaveClient'),true);
assert.equal(html.includes('Primeiro acesso'),true);
const script=html.match(/<script[^>]*>([\s\S]*?)<\/script>/);
assert.ok(script,'missing portal JavaScript');
new vm.Script(script[1],{filename:'ClientPortal.html-script'});
console.log('CLIENT_PORTAL_ADMIN_ACCESS_TESTS_OK');

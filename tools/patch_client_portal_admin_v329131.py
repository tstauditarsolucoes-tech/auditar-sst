#!/usr/bin/env python3
"""Web portal client access manager, admin-only. No sync, schema, auth core or GS central edits."""
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1])
gs=root/'painel_web_google_apps_script/ClientPortal.gs'
html=root/'painel_web_google_apps_script/ClientPortal.html'
protected=[
 'lib/database.dart','lib/services/device_sync_service.dart',
 'lib/services/sync_coordinator.dart','lib/services/media_sync_service.dart',
 'lib/services/drive_service.dart','lib/services/apps_script_http.dart',
 'lib/services/auth_service.dart','lib/services/ai_assistant_service.dart',
 'painel_web_google_apps_script/Code.gs',
 'painel_web_google_apps_script/MultiUser.gs',
 'painel_web_google_apps_script/ReportEmail.gs',
]
before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in protected}
s=gs.read_text(encoding='utf-8')
if 'function clientPortalAdminUsers(' in s:
 raise SystemExit('Admin client management already present; no changes made.')
s+=r'''

/**
 * Administrative client accounts use an existing, authenticated admin session.
 * The web portal never receives the Central sync key or any password hash.
 * First administrator is created ONLY through the existing app first-access flow.
 */
function clientPortalAdminActor_(token) {
  const actor=clientPortalAuthorizedUser_(token);
  return actor && actor.role === 'admin' ? actor : null;
}

function clientPortalAdminUsers(token) {
  const actor=clientPortalAdminActor_(token);
  if (!actor) return {ok:false,code:'ACCESS_DENIED',
    message:'Entre com a conta administradora da Auditar.'};
  return {ok:true,users:readAuthUsers_()
    .filter(function(u){return u.role==='cliente';})
    .map(authPublicUser_)};
}

function clientPortalAdminSaveClient(token,input) {
  const actor=clientPortalAdminActor_(token);
  if (!actor) return {ok:false,code:'ACCESS_DENIED',
    message:'Apenas o administrador da Auditar pode criar acessos.'};
  const request=input && typeof input==='object' ? input : {};
  const companyId=String(request.companyId || '').trim();
  if (!companyId) return {ok:false,message:'Selecione a empresa do cliente.'};
  const panel=getSheet_(PANEL_SHEET);
  const rows=panel.getLastRow()>1
    ? panel.getRange(2,1,panel.getLastRow()-1,6).getValues() : [];
  const published=rows.some(function(row) {
    return String(row[1] || '')===companyId &&
      (row[3]===true || String(row[3]).toLowerCase()==='true');
  });
  if (!published) return {ok:false,message:
    'Publique o painel desta empresa antes de conceder acesso.'};
  const id=String(request.id || '').trim();
  if (id) {
    const existing=readAuthUsers_().find(function(u){return u.id===id;});
    if (!existing || existing.role!=='cliente') {
      return {ok:false,code:'ACCESS_DENIED',
        message:'Somente contas de clientes podem ser editadas aqui.'};
    }
  }
  const permissions=clientPortalPermissions_(request.clientPermissions);
  const result=authUserSave_({authToken:String(token || ''),user:{
    id:id,
    name:String(request.name || '').trim(),
    email:normalizeAuthEmail_(request.email),
    password:String(request.password || ''),
    role:'cliente',
    active:request.active!==false,
    allCompanies:false,
    companyIds:[companyId],
    clientPermissions:permissions
  }});
  if (!result || !result.ok) return result;
  return {ok:true,user:result.user,
    message:id?'Acesso do cliente atualizado.':'Acesso do cliente criado.'};
}
'''
h=html.read_text(encoding='utf-8')
before_login='<form id="loginForm">'
after_login='''<p class="muted">Administrador da Auditar: utilize a conta do aplicativo.
 Se não houver usuários, crie a primeira conta pela tela
 <strong>Primeiro acesso</strong> do Auditar SST. O portal não cria
 administradores publicamente.</p>
 '''+before_login
if h.count(before_login)!=1:raise SystemExit('Admin login form anchor missing')
h=h.replace(before_login,after_login,1)
dashboard_anchor='  <div id="companies"></div>'
admin_markup=r'''  <section id="adminAccess" class="panel hidden" aria-label="Gestão de acesso dos clientes">
   <div class="row"><div><h2>Administração Auditar • Acessos de clientes</h2>
    <p class="muted">Crie uma conta individual para cada empresa, com permissões específicas.</p></div>
    <button id="newClient" type="button">Novo acesso de cliente</button></div>
   <p id="adminMessage" role="status" class="muted"></p>
   <form id="clientForm" class="hidden">
    <input id="clientUserId" type="hidden">
    <div class="columns">
     <div><label for="clientName">Nome do contato</label><input id="clientName" required minlength="3" maxlength="120" autocomplete="off"></div>
     <div><label for="clientEmail">E-mail de acesso</label><input id="clientEmail" type="email" required autocomplete="off"></div>
     <div><label for="clientCompany">Empresa liberada</label><select id="clientCompany" required></select></div>
     <div><label for="clientPassword">Senha inicial (mínimo 8 caracteres; deixe vazia ao editar)</label><input id="clientPassword" type="password" minlength="8" autocomplete="new-password"></div>
    </div>
    <label><input id="clientActive" type="checkbox" checked style="width:auto"> Conta ativa</label>
    <h3>Permissões do cliente</h3>
    <div class="columns">
     <label><input id="cp_indicadores" type="checkbox" checked style="width:auto"> Indicadores</label>
     <label><input id="cp_naoConformidades" type="checkbox" checked style="width:auto"> Não conformidades</label>
     <label><input id="cp_acoesCorretivas" type="checkbox" checked style="width:auto"> Ações corretivas</label>
     <label><input id="cp_relatorios" type="checkbox" checked style="width:auto"> Relatórios e vistorias</label>
     <label><input id="cp_enviarEvidencia" type="checkbox" style="width:auto"> Envio de evidências (opcional)</label>
    </div>
    <p class="muted">Cada conta de cliente fica vinculada a exatamente uma empresa.
     Não envie a senha pelo próprio painel.</p>
    <div class="row"><button id="saveClient" type="submit">Salvar acesso</button>
     <button id="cancelClient" class="secondary" type="button">Cancelar</button></div>
   </form>
   <div id="adminUsers"></div>
  </section>
'''
if h.count(dashboard_anchor)!=1:raise SystemExit('Admin dashboard anchor missing')
h=h.replace(dashboard_anchor,admin_markup+dashboard_anchor,1)
insert_js=r'''
const CLIENT_PERMISSION_KEYS=['indicadores','naoConformidades','acoesCorretivas','relatorios','enviarEvidencia'];
let adminUsers=[];
function adminNotice(message,bad){
 const el=$('adminMessage');el.textContent=message||'';el.className=bad?'error':'muted';
}
function adminCompanies(){
 const select=$('clientCompany');select.replaceChildren();
 const placeholder=document.createElement('option');placeholder.value='';
 placeholder.textContent='Selecione uma empresa com painel publicado';select.append(placeholder);
 (current&&current.companies||[]).forEach(company=>{
  const opt=document.createElement('option');opt.value=company.id;
  opt.textContent=company.name||company.id;select.append(opt);
 });
}
function adminForm(user){
 $('clientForm').classList.remove('hidden');$('clientUserId').value=user?user.id:'';
 $('clientName').value=user?user.name||'':'';
 $('clientEmail').value=user?user.email||'':'';
 $('clientPassword').value='';
 $('clientPassword').required=!user;
 $('clientActive').checked=!user||user.active!==false;
 adminCompanies();
 if(user&&user.companyIds&&user.companyIds.length){
  const id=String(user.companyIds[0]);
  if(![...$('clientCompany').options].some(option=>option.value===id)){
   const option=document.createElement('option');option.value=id;
   option.textContent='Empresa sem painel publicado • '+id;$('clientCompany').append(option);
  }
  $('clientCompany').value=id;
 }
 CLIENT_PERMISSION_KEYS.forEach(key=>{
  const defaults={indicadores:true,naoConformidades:true,acoesCorretivas:true,
   relatorios:true,enviarEvidencia:false};
  $('cp_'+key).checked=user&&user.clientPermissions
   ? user.clientPermissions[key]===true:defaults[key];
 });
 adminNotice(user?'Editando acesso existente.':'Defina uma senha inicial para o novo cliente.');
 $('clientName').focus();
}
function adminLoadUsers(){
 adminNotice('Carregando acessos…');
 call('clientPortalAdminUsers',[token],result=>{
  if(!result||!result.ok){adminNotice(result&&result.message||'Acesso negado.',true);return;}
  adminUsers=result.users||[];const holder=$('adminUsers');holder.replaceChildren();
  if(!adminUsers.length)holder.append(text('p','Nenhum acesso de cliente cadastrado.','muted'));
  adminUsers.forEach(user=>{
   const line=text('div','','entry');const head=text('div','','row');
   const label=text('div');
   label.append(text('strong',user.name||'Cliente'),
    text('div',user.email||'','muted'),
    text('div',(user.active?'Ativo':'Inativo')+' • Empresa vinculada: '+
      ((user.companyIds||[])[0]||'Não definida'),'muted'));
   const edit=text('button','Editar acesso','secondary');edit.type='button';
   edit.onclick=()=>adminForm(user);head.append(label,edit);line.append(head);holder.append(line);
  });
  adminNotice('Acessos carregados.');
 },err=>adminNotice(err,true));
}
$('newClient').onclick=()=>adminForm(null);
$('cancelClient').onclick=()=>{$('clientForm').classList.add('hidden');$('clientPassword').value='';adminNotice('');};
$('clientForm').onsubmit=event=>{
 event.preventDefault();
 const id=$('clientUserId').value,companyId=$('clientCompany').value;
 if(!companyId){adminNotice('Selecione uma empresa com painel publicado.',true);return;}
 const password=$('clientPassword').value;
 if(!id&&password.length<8){adminNotice('Defina uma senha de pelo menos 8 caracteres.',true);return;}
 const save=$('saveClient');save.disabled=true;adminNotice('Salvando acesso…');
 const clientPermissions={};
 CLIENT_PERMISSION_KEYS.forEach(key=>{clientPermissions[key]=$('cp_'+key).checked;});
 call('clientPortalAdminSaveClient',[token,{
  id:id,name:$('clientName').value.trim(),email:$('clientEmail').value.trim(),
  password:password,companyId:companyId,active:$('clientActive').checked,
  clientPermissions:clientPermissions
 }],result=>{
  save.disabled=false;$('clientPassword').value='';
  if(!result||!result.ok){adminNotice(result&&result.message||'Não foi possível salvar.',true);return;}
  $('clientForm').classList.add('hidden');
  adminLoadUsers();adminNotice(result.message||'Acesso salvo.');
 },err=>{save.disabled=false;$('clientPassword').value='';adminNotice(err,true);});
};
'''
anchor_js="$('loginForm').onsubmit=event=>{"
if h.count(anchor_js)!=1:raise SystemExit('Admin js anchor missing')
h=h.replace(anchor_js,insert_js+anchor_js,1)
anchor_load="  res.companies.forEach(renderCompany);setMessage('Dados atualizados.');"
replacement="""  res.companies.forEach(renderCompany);setMessage('Dados atualizados.');
  if(res.user.role==='admin'){
   $('adminAccess').classList.remove('hidden');adminCompanies();adminLoadUsers();
  }else{
   $('adminAccess').classList.add('hidden');$('clientForm').classList.add('hidden');
  }"""
if h.count(anchor_load)!=1:raise SystemExit('Admin load anchor missing')
h=h.replace(anchor_load,replacement,1)
anchor_logout=" $('dashboard').classList.add('hidden');$('logout').classList.add('hidden');$('login').classList.remove('hidden');"
if h.count(anchor_logout)!=1:raise SystemExit('Admin logout anchor missing')
h=h.replace(anchor_logout,anchor_logout+"\n $('adminAccess').classList.add('hidden');$('clientPassword').value='';",1)
gs.write_text(s,encoding='utf-8',newline='\n')
html.write_text(h,encoding='utf-8',newline='\n')
changed=[p for p,digest in before.items()
 if hashlib.sha256((root/p).read_bytes()).hexdigest()!=digest]
if changed:raise SystemExit('PROTECTED SYNC DB CORE GS AUTH AI MODIFIED: '+repr(changed))
print('PORTAL_ADMIN_CLIENT_ACCESS_ISOLATED_OK')
print('CORE_SYNC_GS_AUTH_DATABASE_BYTE_IDENTICAL_OK')

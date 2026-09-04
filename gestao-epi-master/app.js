(() => {
  const ENDPOINT='https://script.google.com/macros/s/AKfycbxqMnKiTlAJTFv3-odS2dB1NRcSD8wwvtNxxa-zCFhTM6GeNZszib_1N6eT9wSnOnOyjg/exec';
  const TOKEN_KEY='gestaoEpiMasterToken';
  const USER_KEY='gestaoEpiMasterUser';
  let tenants=[];
  let setupMode=false;
  let codeTouched=false;

  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const esc=(v='')=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const token=()=>String(localStorage.getItem(TOKEN_KEY)||'').trim();
  function fmtDate(v){if(!v)return '—';const p=String(v).slice(0,10).split('-');return p.length===3?`${p[2]}/${p[1]}/${p[0]}`:v;}
  function toast(msg){const el=$('#toast');el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2600);}
  function futureDate(days){const d=new Date();d.setDate(d.getDate()+days);return d.toISOString().slice(0,10);}
  function statusLabel(s){return s==='active'?'Ativa':s==='trial'?'Teste':s==='expired'?'Vencida':'Suspensa';}
  function planLabel(p){return p==='basico'?'Básico':p==='premium'?'Premium':'Profissional';}

  async function api(action,extra={}){
    const body={action,...extra};if(token()&&!body.authToken)body.authToken=token();
    const res=await fetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify(body)});
    return res.json();
  }

  function showLogin(setup=false,msg=''){
    setupMode=setup;$('#loginOverlay').classList.remove('hidden');$('#setupKeyWrap').classList.toggle('hidden',!setup);$('#masterNameWrap').classList.toggle('hidden',!setup);$('#loginTitle').textContent=setup?'Criar acesso proprietário':'Painel Mestre';$('#loginText').textContent=setup?'Primeiro acesso: crie o administrador do Painel Mestre.':'Acesso exclusivo do proprietário do sistema.';$('#btnLogin').textContent=setup?'Criar administrador':'Entrar';$('#loginError').textContent=msg||'';setTimeout(()=>$(setup?'#setupKey':'#masterUser')?.focus(),60);
  }
  function hideLogin(){$('#loginOverlay').classList.add('hidden');}
  function saveSession(r){localStorage.setItem(TOKEN_KEY,r.token);localStorage.setItem(USER_KEY,JSON.stringify(r.user||{}));$('#masterDisplay').textContent=r.user?.name||r.user?.username||'Administrador';}
  function clearSession(){localStorage.removeItem(TOKEN_KEY);localStorage.removeItem(USER_KEY);}

  async function login(){
    const username=$('#masterUser').value.trim(),password=$('#masterPass').value,btn=$('#btnLogin'),err=$('#loginError');
    if(!username||!password){err.textContent='Informe usuário e senha.';return;}
    if(setupMode&&!$('#setupKey').value.trim()){err.textContent='Informe a chave de instalação.';return;}
    btn.disabled=true;btn.textContent='Aguarde…';err.textContent='';
    try{
      const r=setupMode?await api('master_bootstrap',{setupKey:$('#setupKey').value.trim(),name:$('#masterName').value.trim(),username,password}):await api('master_login',{username,password});
      if(!r?.ok)throw new Error(r?.message||'Não foi possível entrar.');saveSession(r);hideLogin();await refresh();
    }catch(e){err.textContent=e.message||'Falha no acesso.';}
    finally{btn.disabled=false;btn.textContent=setupMode?'Criar administrador':'Entrar';}
  }

  function openView(id){$$('.view').forEach(v=>v.classList.toggle('active',v.id===id));$$('.nav').forEach(n=>n.classList.toggle('active',n.dataset.view===id));const titles={dashboard:['Visão geral','Acompanhe clientes, licenças e acessos.'],clients:['Clientes e licenças','Controle quem pode usar o Gestão EPI.']};const t=titles[id]||titles.dashboard;$('#viewTitle').textContent=t[0];$('#viewSub').textContent=t[1];}

  async function refresh(){
    const r=await api('master_list_tenants');if(!r?.ok){if(['SESSION_EXPIRED','SESSION_INVALID','USER_DISABLED'].includes(r?.code)){clearSession();showLogin(false,r.message);return;}throw new Error(r?.message||'Falha ao carregar clientes.');}
    tenants=r.tenants||[];renderDashboard();renderClients();
  }

  function renderDashboard(){
    $('#mClients').textContent=tenants.length;$('#mActive').textContent=tenants.filter(t=>t.status==='active').length;$('#mTrial').textContent=tenants.filter(t=>t.status==='trial').length;$('#mAttention').textContent=tenants.filter(t=>['expired','suspended'].includes(t.status)).length;
    const today=new Date();today.setHours(0,0,0,0);const soon=tenants.filter(t=>t.validUntil&&!['expired','suspended'].includes(t.status)).map(t=>({t,days:Math.ceil((new Date(t.validUntil+'T23:59:59')-today)/86400000)})).filter(x=>x.days>=0&&x.days<=30).sort((a,b)=>a.days-b.days);
    $('#expiringList').innerHTML=soon.length?soon.map(x=>`<div class="list-item"><div><b>${esc(x.t.name)}</b><small>${esc(x.t.code)} • ${planLabel(x.t.plan)}</small></div><div><b>${x.days} dia(s)</b><small>${fmtDate(x.t.validUntil)}</small></div></div>`).join(''):'<div class="empty">Nenhuma licença vencendo nos próximos 30 dias.</div>';
    const recent=tenants.slice().sort((a,b)=>String(b.createdAt).localeCompare(String(a.createdAt))).slice(0,6);$('#recentList').innerHTML=recent.length?recent.map(t=>`<div class="list-item"><div><b>${esc(t.name)}</b><small>${esc(t.code)} • ${planLabel(t.plan)}</small></div><span class="badge ${t.status}">${statusLabel(t.status)}</span></div>`).join(''):'<div class="empty">Nenhum cliente cadastrado.</div>';
  }

  function renderClients(){
    const q=$('#clientSearch').value.trim().toLowerCase(),sf=$('#statusFilter').value;const rows=tenants.filter(t=>(!sf||t.status===sf)&&(!q||[t.name,t.code,t.cnpj].some(v=>String(v||'').toLowerCase().includes(q)))).sort((a,b)=>String(a.name).localeCompare(String(b.name)));
    $('#clientsTable').innerHTML=rows.length?`<table class="data-table"><thead><tr><th>Cliente</th><th>Código</th><th>Plano</th><th>Status</th><th>Validade</th><th>Usuários / aparelhos</th><th></th></tr></thead><tbody>${rows.map(t=>`<tr><td><b>${esc(t.name)}</b><br><small>${esc(t.cnpj||'CNPJ não informado')}</small></td><td><b>${esc(t.code)}</b></td><td>${planLabel(t.plan)}</td><td><span class="badge ${t.status}">${statusLabel(t.status)}</span></td><td>${fmtDate(t.validUntil)}</td><td>até ${Number(t.maxUsers||0)} usuário(s)<br><small>${(t.devices||[]).filter(d=>d.active!==false).length}/${Number(t.maxDevices||0)} dispositivo(s)</small></td><td><div class="row-actions"><button class="soft" data-license="${esc(t.id)}">Gerenciar</button>${t.status==='suspended'?`<button class="soft" data-quick-active="${esc(t.id)}">Ativar</button>`:`<button class="danger" data-quick-suspend="${esc(t.id)}">Suspender</button>`}</div></td></tr>`).join('')}</tbody></table>`:'<div class="empty">Nenhum cliente encontrado.</div>';
    $$('[data-license]').forEach(b=>b.onclick=()=>openLicense(b.dataset.license));$$('[data-quick-suspend]').forEach(b=>b.onclick=()=>quickStatus(b.dataset.quickSuspend,'suspended'));$$('[data-quick-active]').forEach(b=>b.onclick=()=>quickStatus(b.dataset.quickActive,'active'));
  }

  function newClient(){
    $('#clientForm').reset();$('#cPlan').value='profissional';$('#cStatus').value='trial';$('#cValidUntil').value=futureDate(14);$('#cMaxUsers').value='5';$('#cMaxDevices').value='3';$('#cAdminUser').value='admin';codeTouched=false;$('#clientDialog').showModal();setTimeout(()=>$('#cName').focus(),50);
  }

  function makeCode(name){return String(name||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase().replace(/[^A-Z0-9]+/g,'-').replace(/^-+|-+$/g,'').slice(0,24);}
  async function createClient(){
    const payload={name:$('#cName').value.trim(),cnpj:$('#cCnpj').value.trim(),code:$('#cCode').value.trim(),plan:$('#cPlan').value,status:$('#cStatus').value,validUntil:$('#cValidUntil').value,maxUsers:Number($('#cMaxUsers').value||5),maxDevices:Number($('#cMaxDevices').value||3),adminName:$('#cAdminName').value.trim(),adminUsername:$('#cAdminUser').value.trim(),adminPassword:$('#cAdminPass').value};
    if(!payload.name||!payload.code||!payload.adminUsername||payload.adminPassword.length<6){toast('Complete os campos obrigatórios.');return;}
    const btn=$('#btnCreateClient');btn.disabled=true;btn.textContent='Criando…';try{const r=await api('master_create_tenant',payload);if(!r?.ok)throw new Error(r?.message||'Falha ao criar cliente.');$('#clientDialog').close();toast('Cliente criado.');await refresh();openView('clients');}catch(e){toast(e.message||'Falha ao criar cliente.');}finally{btn.disabled=false;btn.textContent='Criar cliente';}
  }

  function openLicense(id){
    const t=tenants.find(x=>x.id===id);if(!t)return;$('#licenseTenantId').value=t.id;$('#licenseTitle').textContent=t.name;$('#licenseCode').textContent=`Código: ${t.code}`;$('#lPlan').value=t.plan==='premium'?'premium':t.plan==='basico'?'basico':'profissional';$('#lStatus').value=t.status==='suspended'?'suspended':t.status==='trial'?'trial':'active';$('#lValidUntil').value=t.validUntil||'';$('#lMaxUsers').value=t.maxUsers||5;$('#lMaxDevices').value=t.maxDevices||3;renderDevices(t);$('#licenseDialog').showModal();
  }

  function renderDevices(t){const rows=t.devices||[];$('#deviceList').innerHTML=`<b>Dispositivos autorizados (${rows.filter(d=>d.active!==false).length}/${t.maxDevices||0})</b>`+(rows.length?rows.map(d=>`<div class="device-row"><div><b>${esc(d.label||'Dispositivo')}</b><small>${d.lastSeenAt?'Último acesso: '+new Date(d.lastSeenAt).toLocaleString('pt-BR'):'Sem acesso recente'}</small></div><button class="${d.active!==false?'block':'allow'}" data-device="${esc(d.id)}" data-active="${d.active!==false?'0':'1'}">${d.active!==false?'Bloquear':'Liberar'}</button></div>`).join(''):'<div class="empty">Nenhum aparelho conectado.</div>');$$('[data-device]').forEach(b=>b.onclick=()=>toggleDevice(t.id,b.dataset.device,b.dataset.active==='1'));}

  async function saveLicense(){const tenantId=$('#licenseTenantId').value;const payload={tenantId,plan:$('#lPlan').value,status:$('#lStatus').value,validUntil:$('#lValidUntil').value,maxUsers:Number($('#lMaxUsers').value||1),maxDevices:Number($('#lMaxDevices').value||1)};const r=await api('master_update_tenant',payload);if(!r?.ok)return toast(r?.message||'Falha ao salvar.');toast('Licença atualizada.');$('#licenseDialog').close();await refresh();}
  async function quickStatus(id,status){const t=tenants.find(x=>x.id===id);if(!t)return;if(status==='suspended'&&!confirm(`Suspender o acesso de ${t.name}?`))return;const r=await api('master_update_tenant',{tenantId:id,status});if(!r?.ok)return toast(r?.message||'Falha ao atualizar.');toast(status==='active'?'Licença ativada.':'Licença suspensa.');await refresh();}
  async function toggleDevice(tenantId,deviceId,active){const r=await api('master_reset_device',{tenantId,deviceId,active});if(!r?.ok)return toast(r?.message||'Falha ao atualizar dispositivo.');toast(r.message||'Dispositivo atualizado.');await refresh();openLicense(tenantId);}
  async function migrateLegacy(){const tenantId=$('#licenseTenantId').value,t=tenants.find(x=>x.id===tenantId);if(!t)return;if(!confirm(`Migrar os dados do sistema antigo para ${t.name}?\n\nUse esta opção apenas para trazer sua base atual para o novo ambiente comercial.`))return;const btn=$('#btnMigrateLegacy');btn.disabled=true;btn.textContent='Migrando…';try{const r=await api('master_migrate_legacy',{tenantId});if(!r?.ok)throw new Error(r?.message||'Falha na migração.');toast(`Migração concluída: ${r.summary?.workers||0} trabalhadores e ${r.summary?.deliveries||0} entregas.`);}catch(e){toast(e.message||'Falha na migração.');}finally{btn.disabled=false;btn.textContent='Migrar dados atuais';}}

  async function init(){
    $('#btnLogin').onclick=login;$('#masterPass').addEventListener('keydown',e=>{if(e.key==='Enter')login();});$$('.nav').forEach(n=>n.onclick=()=>openView(n.dataset.view));$('#btnRefresh').onclick=()=>refresh().catch(e=>toast(e.message));$('#btnNewClient').onclick=newClient;$('#btnNewClientTop').onclick=newClient;$('#btnCreateClient').onclick=createClient;$('#btnSaveLicense').onclick=saveLicense;$('#btnMigrateLegacy').onclick=migrateLegacy;$('#btnLogout').onclick=()=>{clearSession();showLogin(false,'Você saiu do Painel Mestre.');};$('#clientSearch').oninput=renderClients;$('#statusFilter').onchange=renderClients;$('#cCode').addEventListener('input',()=>codeTouched=true);$('#cName').addEventListener('input',()=>{if(!codeTouched)$('#cCode').value=makeCode($('#cName').value);});$('#cStatus').addEventListener('change',()=>{$('#cValidUntil').value=futureDate($('#cStatus').value==='active'?365:14);});
    try{const s=await api('master_status');if(!s?.ok)throw new Error(s?.message||'Central indisponível.');if(!s.configured){showLogin(true);return;}if(token()){const me=await api('master_me');if(me?.ok){$('#masterDisplay').textContent=me.user?.name||me.user?.username||'Administrador';hideLogin();await refresh();return;}clearSession();}showLogin(false);}catch(e){showLogin(false,e.message||'Não foi possível acessar a central.');}
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();

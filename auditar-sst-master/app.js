(() => {
  const ENDPOINT = 'https://script.google.com/macros/s/AKfycbxNG-wU-jZMKMR2cb1nR9OUd31GSUpGM0FIEagZEUP7sAHxkahLDuJ6T3wZvEe9rm6WrQ/exec';
  const TOKEN_KEY = 'auditarSstMasterToken';
  const USER_KEY = 'auditarSstMasterUser';
  const DEVICE_KEY = 'auditarSstMasterDevice';
  let users = [];
  let companies = [];
  let currentUser = null;
  let editingUser = null;

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = (v = '') => String(v).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const token = () => String(localStorage.getItem(TOKEN_KEY) || '').trim();
  const usernameOf = u => String(u?.email || '').split('@')[0] || String(u?.name || '').toLowerCase().replace(/\s+/g,'.');
  const toast = msg => { const el = $('#toast'); el.textContent = msg; el.classList.add('show'); setTimeout(() => el.classList.remove('show'), 2800); };

  function deviceId(){
    let id = String(localStorage.getItem(DEVICE_KEY) || '').trim();
    if (!id) {
      id = 'master-' + (crypto?.randomUUID ? crypto.randomUUID() : Date.now() + '-' + Math.random().toString(36).slice(2));
      localStorage.setItem(DEVICE_KEY, id);
    }
    return id;
  }

  async function api(action, extra = {}){
    const body = { action, ...extra };
    if (token() && !body.authToken) body.authToken = token();
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 28000);
    try {
      const res = await fetch(ENDPOINT, {
        method: 'POST',
        headers: {'Content-Type':'text/plain;charset=utf-8'},
        body: JSON.stringify(body),
        signal: ctrl.signal,
      });
      const text = await res.text();
      let json;
      try { json = JSON.parse(text); } catch (_) { throw new Error('A Central Online retornou uma resposta inválida.'); }
      return json;
    } catch (e) {
      if (e?.name === 'AbortError') throw new Error('A Central Online demorou para responder. Tente novamente.');
      throw e;
    } finally { clearTimeout(timer); }
  }

  function clearSession(){
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    currentUser = null;
  }

  function showLogin(message = ''){
    $('#loginOverlay').classList.remove('hidden');
    $('#loginError').textContent = message;
    setTimeout(() => $('#loginUser')?.focus(), 70);
  }
  const hideLogin = () => $('#loginOverlay').classList.add('hidden');

  async function login(){
    const identifier = $('#loginUser').value.trim();
    const password = $('#loginPass').value;
    const btn = $('#btnLogin');
    const err = $('#loginError');
    if (!identifier || !password) { err.textContent = 'Informe usuário e senha.'; return; }
    btn.disabled = true; btn.textContent = 'Entrando…'; err.textContent = '';
    try {
      const r = await api('auth_login', {
        username: identifier,
        email: identifier,
        password,
        deviceId: deviceId(),
        platform: 'windows',
      });
      if (!r?.ok) throw new Error(r?.message || 'Usuário ou senha inválidos.');
      if (String(r.user?.role || '').toLowerCase() !== 'admin') throw new Error('Este Painel Mestre é exclusivo para administradores.');
      localStorage.setItem(TOKEN_KEY, String(r.sessionToken || ''));
      localStorage.setItem(USER_KEY, JSON.stringify(r.user || {}));
      currentUser = r.user;
      $('#adminDisplay').textContent = currentUser?.name || 'Administrador';
      hideLogin();
      await refresh();
    } catch (e) { err.textContent = e.message || 'Não foi possível entrar.'; }
    finally { btn.disabled = false; btn.textContent = 'Entrar'; }
  }

  async function verifySavedSession(){
    if (!token()) return false;
    try {
      const r = await api('auth_session', { authToken: token(), deviceId: deviceId(), platform: 'windows' });
      if (!r?.ok || String(r.user?.role || '').toLowerCase() !== 'admin') return false;
      currentUser = r.user;
      localStorage.setItem(USER_KEY, JSON.stringify(r.user || {}));
      $('#adminDisplay').textContent = r.user?.name || 'Administrador';
      return true;
    } catch (_) { return false; }
  }

  async function loadUsers(){
    const r = await api('auth_users_list');
    if (!r?.ok) {
      if (['SESSION_INVALID','AUTH_REQUIRED'].includes(r?.code)) { clearSession(); showLogin(r.message || 'Sessão expirada.'); return false; }
      throw new Error(r?.message || 'Falha ao carregar usuários.');
    }
    users = Array.isArray(r.users) ? r.users : [];
    return true;
  }

  async function loadCompanies(){
    const byId = new Map();
    let sinceVersion = 0;
    for (let page = 0; page < 20; page++) {
      const r = await api('device_sync_pull', {
        authToken: token(),
        deviceId: deviceId(),
        platform: 'windows',
        sinceVersion,
        limit: 300,
      });
      if (!r?.ok) {
        if (['SESSION_INVALID','AUTH_REQUIRED'].includes(r?.code)) { clearSession(); showLogin(r.message || 'Sessão expirada.'); return false; }
        throw new Error(r?.message || 'Falha ao carregar empresas.');
      }
      const changes = Array.isArray(r.changes) ? r.changes : [];
      for (const change of changes) {
        if (String(change?.table || '') !== 'companies') continue;
        const id = String(change?.id || '').trim();
        if (!id) continue;
        if (change.deleted === true) byId.delete(id);
        else if (change.payload && typeof change.payload === 'object') byId.set(id, {id, ...change.payload});
      }
      const next = Number(r.nextVersion || r.version || sinceVersion);
      if (next > sinceVersion) sinceVersion = next;
      if (r.hasMore !== true) break;
    }
    companies = [...byId.values()].sort((a,b) => String(a.name || '').localeCompare(String(b.name || ''), 'pt-BR'));
    return true;
  }

  async function refresh(){
    const btn = $('#btnRefresh');
    btn.disabled = true; btn.textContent = '↻ Atualizando…';
    try {
      const ok = await loadUsers();
      if (!ok) return;
      try { await loadCompanies(); } catch (e) { console.warn(e); companies = []; toast('Usuários carregados. Empresas aguardando sincronização.'); }
      renderAll();
    } catch (e) { toast(e.message || 'Falha ao atualizar.'); }
    finally { btn.disabled = false; btn.textContent = '↻ Atualizar'; }
  }

  function openView(id){
    $$('.view').forEach(v => v.classList.toggle('active', v.id === id));
    $$('.nav').forEach(n => n.classList.toggle('active', n.dataset.view === id));
    const titles = {
      dashboard:['Visão geral','Controle central dos acessos do Auditar SST.'],
      users:['Usuários','Crie acessos, redefina senhas e controle permissões.'],
      companies:['Empresas','Empresas disponíveis para liberação aos técnicos.'],
    };
    const t = titles[id] || titles.dashboard;
    $('#viewTitle').textContent = t[0]; $('#viewSub').textContent = t[1];
    $('#btnNewUserTop').classList.toggle('hidden', id === 'companies');
  }

  function renderAll(){ renderDashboard(); renderUsers(); renderCompanies(); }

  function renderDashboard(){
    const active = users.filter(u => u.active !== false);
    const techs = users.filter(u => String(u.role).toLowerCase() !== 'admin');
    $('#mUsers').textContent = users.length;
    $('#mActive').textContent = active.length;
    $('#mTechs').textContent = techs.length;
    $('#mBlocked').textContent = users.filter(u => u.active === false).length;
    const restricted = techs.filter(u => !u.allCompanies && Array.isArray(u.companyIds) && u.companyIds.length > 0).length;
    $('#accessSummary').innerHTML = [
      `<div class="list-item"><div><b>${companies.length} empresa(s) sincronizada(s)</b><small>Disponíveis para controle de permissão.</small></div><span class="badge active">Central</span></div>`,
      `<div class="list-item"><div><b>${restricted} técnico(s) com acesso restrito</b><small>Visualizam somente empresas selecionadas.</small></div><span class="badge tech">Controlado</span></div>`,
      `<div class="list-item"><div><b>${users.filter(u=>String(u.role).toLowerCase()==='admin').length} administrador(es)</b><small>Podem gerenciar usuários e todas as empresas.</small></div><span class="badge admin">Admin</span></div>`,
    ].join('');
    const recent = users.slice().reverse().slice(0,6);
    $('#recentUsers').innerHTML = recent.length ? recent.map(u => `<div class="list-item"><div><b>${esc(u.name)}</b><small>@${esc(usernameOf(u))} • ${String(u.role).toLowerCase()==='admin'?'Administrador':'Técnico SST'}</small></div><span class="badge ${u.active===false?'inactive':'active'}">${u.active===false?'Bloqueado':'Ativo'}</span></div>`).join('') : '<div class="empty">Nenhum usuário cadastrado.</div>';
  }

  function filteredUsers(){
    const q = $('#userSearch').value.trim().toLowerCase();
    const f = $('#userFilter').value;
    return users.filter(u => {
      const role = String(u.role || 'tecnico').toLowerCase();
      if (f === 'active' && u.active === false) return false;
      if (f === 'inactive' && u.active !== false) return false;
      if (f === 'admin' && role !== 'admin') return false;
      if (f === 'tecnico' && role === 'admin') return false;
      if (q && ![u.name, usernameOf(u), u.email, role].some(v => String(v || '').toLowerCase().includes(q))) return false;
      return true;
    }).sort((a,b) => String(a.name||'').localeCompare(String(b.name||''),'pt-BR'));
  }

  function accessLabel(u){
    if (String(u.role).toLowerCase() === 'admin' || u.allCompanies) return 'Todas as empresas';
    const count = Array.isArray(u.companyIds) ? u.companyIds.length : 0;
    return count ? `${count} empresa(s)` : 'Nenhuma empresa';
  }

  function renderUsers(){
    const rows = filteredUsers();
    $('#usersTable').innerHTML = rows.length ? `<table class="data-table"><thead><tr><th>Usuário</th><th>Perfil</th><th>Empresas</th><th>Status</th><th></th></tr></thead><tbody>${rows.map(u => {
      const admin = String(u.role).toLowerCase() === 'admin';
      const self = String(u.id) === String(currentUser?.id || '');
      return `<tr><td><b>${esc(u.name)}</b><br><small>@${esc(usernameOf(u))}${self?' • você':''}</small></td><td><span class="badge ${admin?'admin':'tech'}">${admin?'Administrador':'Técnico SST'}</span></td><td>${esc(accessLabel(u))}</td><td><span class="badge ${u.active===false?'inactive':'active'}">${u.active===false?'Bloqueado':'Ativo'}</span></td><td><div class="row-actions"><button class="soft" data-edit-user="${esc(u.id)}">Gerenciar</button></div></td></tr>`;
    }).join('')}</tbody></table>` : '<div class="empty">Nenhum usuário encontrado.</div>';
    $$('[data-edit-user]').forEach(b => b.onclick = () => openUserDialog(users.find(u => String(u.id) === String(b.dataset.editUser))));
  }

  function renderCompanies(){
    const q = $('#companySearch').value.trim().toLowerCase();
    const rows = companies.filter(c => !q || [c.name,c.legal_name,c.cnpj].some(v => String(v||'').toLowerCase().includes(q)));
    $('#companiesTable').innerHTML = rows.length ? `<table class="data-table"><thead><tr><th>Empresa</th><th>CNPJ</th><th>Situação</th><th>Técnicos liberados</th></tr></thead><tbody>${rows.map(c => {
      const granted = users.filter(u => String(u.role).toLowerCase() !== 'admin' && u.active !== false && (u.allCompanies || (u.companyIds||[]).includes(c.id))).length;
      return `<tr><td><span class="company-name">${esc(c.name || c.legal_name || 'Empresa')}</span></td><td>${esc(c.cnpj || '—')}</td><td><span class="badge ${Number(c.active||1)===0?'inactive':'active'}">${Number(c.active||1)===0?'Inativa':'Ativa'}</span></td><td>${granted} técnico(s)</td></tr>`;
    }).join('')}</tbody></table>` : '<div class="empty">Nenhuma empresa sincronizada ainda. Abra o Auditar SST e faça uma sincronização para enviar as empresas à Central Online.</div>';
  }

  function cleanUsername(value){
    return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9._-]+/g,'').replace(/^[._-]+|[._-]+$/g,'').slice(0,40);
  }

  function generatePassword(){
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#%';
    const values = new Uint32Array(12); crypto.getRandomValues(values);
    return [...values].map(v => chars[v % chars.length]).join('');
  }

  function openUserDialog(user = null){
    editingUser = user || null;
    $('#userForm').reset();
    $('#uId').value = user?.id || '';
    $('#uEmailExisting').value = user?.email || '';
    $('#uName').value = user?.name || '';
    $('#uUsername').value = user ? usernameOf(user) : '';
    $('#uUsername').disabled = !!user;
    $('#uRole').value = String(user?.role || 'tecnico').toLowerCase() === 'admin' ? 'admin' : 'tecnico';
    $('#uActive').checked = user?.active !== false;
    $('#uAllCompanies').checked = user?.allCompanies === true || String(user?.role || '').toLowerCase() === 'admin';
    $('#uPassword').value = user ? '' : generatePassword();
    $('#passwordHint').textContent = user ? '(opcional para redefinir)' : 'inicial';
    $('#userDialogTitle').textContent = user ? 'Gerenciar usuário' : 'Novo usuário';
    $('#userDialogSub').textContent = user ? 'Altere acesso, empresas ou defina uma nova senha.' : 'Crie um acesso individual para o Auditar SST.';
    $('#userFormError').textContent = '';
    renderCompanyPicker(new Set(user?.companyIds || []));
    syncRoleUi();
    const self = user && String(user.id) === String(currentUser?.id || '');
    $('#uActive').disabled = !!self;
    $('#uRole').disabled = !!self;
    $('#userDialog').showModal();
    setTimeout(() => (user ? $('#uPassword') : $('#uName'))?.focus(), 60);
  }

  function renderCompanyPicker(selected = null){
    const current = selected || new Set($$('[data-company-check]:checked').map(x => x.value));
    const q = $('#companyPickerSearch').value.trim().toLowerCase();
    const rows = companies.filter(c => !q || String(c.name || '').toLowerCase().includes(q));
    $('#companyPicker').innerHTML = rows.length ? rows.map(c => `<label class="company-check"><input data-company-check type="checkbox" value="${esc(c.id)}" ${current.has(c.id)?'checked':''}><span><b>${esc(c.name || c.legal_name || 'Empresa')}</b>${c.cnpj?`<small class="company-meta">${esc(c.cnpj)}</small>`:''}</span></label>`).join('') : '<div class="empty">Nenhuma empresa disponível.</div>';
  }

  function syncRoleUi(){
    const admin = $('#uRole').value === 'admin';
    if (admin) $('#uAllCompanies').checked = true;
    $('#companyAccessWrap').classList.toggle('hidden', admin);
    $('#companyPickerWrap').classList.toggle('hidden', $('#uAllCompanies').checked || admin);
  }

  async function saveUser(){
    const id = $('#uId').value.trim();
    const name = $('#uName').value.trim();
    const username = cleanUsername($('#uUsername').value);
    const role = $('#uRole').value === 'admin' ? 'admin' : 'tecnico';
    const active = $('#uActive').checked;
    const allCompanies = role === 'admin' ? true : $('#uAllCompanies').checked;
    const companyIds = role === 'admin' || allCompanies ? [] : $$('[data-company-check]:checked').map(x => x.value);
    const password = $('#uPassword').value;
    const err = $('#userFormError');
    if (name.length < 3) { err.textContent = 'Informe o nome do usuário.'; return; }
    if (!id && username.length < 3) { err.textContent = 'Crie um usuário com pelo menos 3 caracteres.'; return; }
    if (!id && password.length < 8) { err.textContent = 'A senha inicial deve ter pelo menos 8 caracteres.'; return; }
    if (id && password && password.length < 8) { err.textContent = 'A nova senha deve ter pelo menos 8 caracteres.'; return; }
    const email = id ? $('#uEmailExisting').value : `${username}@auditar.local`;
    const btn = $('#btnSaveUser'); btn.disabled = true; btn.textContent = 'Salvando…'; err.textContent = '';
    try {
      const r = await api('auth_user_save', {
        user: {
          id,
          name,
          email,
          role,
          active,
          allCompanies,
          companyIds,
          ...(password ? {password} : {}),
        },
      });
      if (!r?.ok) throw new Error(r?.message || 'Não foi possível salvar o usuário.');
      $('#userDialog').close();
      await loadUsers(); renderAll();
      toast(id ? 'Usuário atualizado.' : 'Usuário criado.');
      if (!id || password) showCredentials(usernameOf(r.user || {email}), password);
    } catch (e) { err.textContent = e.message || 'Falha ao salvar usuário.'; }
    finally { btn.disabled = false; btn.textContent = 'Salvar usuário'; }
  }

  function showCredentials(username, password){
    $('#createdUsername').textContent = username;
    $('#createdPassword').textContent = password || '(senha mantida)';
    $('#credentialDialog').showModal();
  }

  async function copyCredentials(){
    const text = `Auditar SST\nUsuário: ${$('#createdUsername').textContent}\nSenha: ${$('#createdPassword').textContent}`;
    try { await navigator.clipboard.writeText(text); toast('Usuário e senha copiados.'); }
    catch (_) {
      const ta = document.createElement('textarea'); ta.value = text; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); ta.remove(); toast('Usuário e senha copiados.');
    }
  }

  async function init(){
    $('#btnLogin').onclick = login;
    $('#loginPass').addEventListener('keydown', e => { if (e.key === 'Enter') login(); });
    $$('.nav').forEach(n => n.onclick = () => openView(n.dataset.view));
    $('#btnRefresh').onclick = refresh;
    $('#btnNewUser').onclick = () => openUserDialog();
    $('#btnNewUserTop').onclick = () => openUserDialog();
    $('#btnSaveUser').onclick = saveUser;
    $('#btnGeneratePass').onclick = () => { $('#uPassword').value = generatePassword(); $('#uPassword').focus(); $('#uPassword').select(); };
    $('#btnCopyCredentials').onclick = copyCredentials;
    $('#btnLogout').onclick = async () => { try { if (token()) await api('auth_logout'); } catch (_) {} clearSession(); showLogin('Você saiu do Painel Mestre.'); };
    $('#userSearch').oninput = renderUsers; $('#userFilter').onchange = renderUsers;
    $('#companySearch').oninput = renderCompanies;
    $('#companyPickerSearch').oninput = () => renderCompanyPicker();
    $('#uRole').onchange = syncRoleUi; $('#uAllCompanies').onchange = syncRoleUi;
    $('#uUsername').oninput = e => { const clean = cleanUsername(e.target.value); if (e.target.value !== clean) e.target.value = clean; };

    const saved = await verifySavedSession();
    if (!saved) { clearSession(); showLogin(); return; }
    hideLogin();
    await refresh();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();

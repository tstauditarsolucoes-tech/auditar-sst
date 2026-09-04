const GESTAO_COM_ROOT = 'Gestao EPI Comercial';
const GESTAO_COM_SYSTEM_FOLDER = 'Sistema';
const GESTAO_COM_CLIENTS_FOLDER = 'Clientes';
const GESTAO_COM_SYSTEM_FILE = 'sistema.json';
const GESTAO_COM_DATA_FILE = 'dados.json';
const GESTAO_COM_USERS_FILE = 'usuarios.json';
const GESTAO_COM_AUTH_SECRET_PROP = 'GESTAO_EPI_COM_AUTH_SECRET_V1';
const GESTAO_COM_TOKEN_HOURS = 12;
const GESTAO_COM_HASH_ROUNDS = 1200;

function doPost(e) {
  try {
    const request = JSON.parse((e.postData && e.postData.contents) || '{}');
    const action = String(request.action || '');

    if (action === 'master_status') return jsonResponse_(masterStatus_());
    if (action === 'master_bootstrap') return jsonResponse_(masterBootstrap_(request));
    if (action === 'master_login') return jsonResponse_(masterLogin_(request));
    if (action === 'master_me') return jsonResponse_(masterMe_(request));
    if (action === 'master_list_tenants') return jsonResponse_(masterListTenants_(request));
    if (action === 'master_create_tenant') return jsonResponse_(masterCreateTenant_(request));
    if (action === 'master_update_tenant') return jsonResponse_(masterUpdateTenant_(request));
    if (action === 'master_migrate_legacy') return jsonResponse_(masterMigrateLegacy_(request));
    if (action === 'master_reset_device') return jsonResponse_(masterResetDevice_(request));

    if (action === 'tenant_login') return jsonResponse_(tenantLogin_(request));
    if (action === 'tenant_me') return jsonResponse_(tenantMe_(request));
    if (action === 'tenant_list_users') return jsonResponse_(tenantListUsers_(request));
    if (action === 'tenant_create_user') return jsonResponse_(tenantCreateUser_(request));
    if (action === 'tenant_update_user') return jsonResponse_(tenantUpdateUser_(request));
    if (action === 'tenant_change_password') return jsonResponse_(tenantChangeOwnPassword_(request));

    if (action === 'epi_sync_merge') return jsonResponse_(tenantSync_(request));

    return jsonResponse_({ok:false,message:'Ação não reconhecida.'});
  } catch (error) {
    return jsonResponse_({ok:false,message:String(error)});
  }
}

function jsonResponse_(data) {
  return ContentService.createTextOutput(JSON.stringify(data)).setMimeType(ContentService.MimeType.JSON);
}

function masterStatus_() {
  const system = commercialLoadSystem_();
  return {ok:true,configured:system.masterUsers.length > 0,tenantCount:system.tenants.length};
}

function masterBootstrap_(request) {
  const props = PropertiesService.getScriptProperties();
  const setupKey = String(props.getProperty('AUDITAR_EPI_SYNC_KEY') || '').trim();
  if (!setupKey || String(request.setupKey || '').trim() !== setupKey) {
    return {ok:false,message:'Chave de instalação inválida.'};
  }
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const system = commercialLoadSystem_();
    if (system.masterUsers.length) return {ok:false,message:'O Painel Mestre já possui administrador.'};
    const username = commercialNormalizeUsername_(request.username);
    const password = String(request.password || '');
    const name = String(request.name || '').trim() || username;
    commercialValidateUsernamePassword_(username,password);
    const user = commercialNewUser_(username,name,'master',password);
    system.masterUsers.push(user);
    system.updatedAt = new Date().toISOString();
    commercialSaveSystem_(system);
    return {ok:true,message:'Administrador Mestre criado.',token:commercialCreateToken_({scope:'master',user:user}),user:commercialPublicUser_(user)};
  } catch (error) {
    return {ok:false,message:String(error)};
  } finally {
    lock.releaseLock();
  }
}

function masterLogin_(request) {
  const username = commercialNormalizeUsername_(request.username);
  const password = String(request.password || '');
  const system = commercialLoadSystem_();
  const user = system.masterUsers.find(function(u){return u.username === username;});
  if (!user || user.active === false || !commercialVerifyPassword_(password,user)) {
    Utilities.sleep(250);
    return {ok:false,message:'Usuário ou senha inválidos.'};
  }
  user.lastLoginAt = new Date().toISOString();
  commercialSaveSystem_(system);
  return {ok:true,token:commercialCreateToken_({scope:'master',user:user}),user:commercialPublicUser_(user)};
}

function masterMe_(request) {
  const session = commercialValidateToken_(request.authToken,'master');
  if (!session.ok) return session;
  return {ok:true,user:session.user};
}

function masterListTenants_(request) {
  const session = commercialValidateToken_(request.authToken,'master');
  if (!session.ok) return session;
  const system = commercialLoadSystem_();
  return {ok:true,tenants:system.tenants.map(commercialPublicTenant_)};
}

function masterCreateTenant_(request) {
  const session = commercialValidateToken_(request.authToken,'master');
  if (!session.ok) return session;
  const lock = LockService.getScriptLock();
  lock.waitLock(15000);
  try {
    const system = commercialLoadSystem_();
    const code = commercialNormalizeTenantCode_(request.code || request.name);
    const name = String(request.name || '').trim();
    if (!name) return {ok:false,message:'Informe o nome do cliente.'};
    if (code.length < 3) return {ok:false,message:'O código do cliente deve ter pelo menos 3 caracteres.'};
    if (system.tenants.some(function(t){return t.code === code;})) return {ok:false,message:'Já existe um cliente com esse código.'};

    const adminUsername = commercialNormalizeUsername_(request.adminUsername || 'admin');
    const adminPassword = String(request.adminPassword || '');
    const adminName = String(request.adminName || '').trim() || 'Administrador';
    commercialValidateUsernamePassword_(adminUsername,adminPassword);

    const now = new Date().toISOString();
    const tenant = {
      id:'t_' + Utilities.getUuid(),
      code:code,
      name:name,
      cnpj:String(request.cnpj || '').trim(),
      plan:commercialNormalizePlan_(request.plan),
      status:commercialNormalizeLicenseStatus_(request.status || 'trial'),
      validUntil:commercialNormalizeDate_(request.validUntil) || commercialFutureDate_(request.status === 'active' ? 365 : 14),
      maxUsers:Math.max(1,Number(request.maxUsers || 5)),
      maxDevices:Math.max(1,Number(request.maxDevices || 3)),
      devices:[],
      createdAt:now,
      updatedAt:now
    };
    const folder = commercialCreateTenantFolder_(tenant);
    tenant.folderId = folder.getId();
    const users = [commercialNewUser_(adminUsername,adminName,'admin',adminPassword)];
    commercialWriteJsonFile_(folder,GESTAO_COM_USERS_FILE,{version:1,users:users,updatedAt:now});
    commercialWriteJsonFile_(folder,GESTAO_COM_DATA_FILE,blankEpiSnapshot_());
    system.tenants.push(tenant);
    system.updatedAt = now;
    commercialSaveSystem_(system);
    return {ok:true,tenant:commercialPublicTenant_(tenant),message:'Cliente criado com sucesso.'};
  } catch (error) {
    return {ok:false,message:String(error)};
  } finally {
    lock.releaseLock();
  }
}

function masterUpdateTenant_(request) {
  const session = commercialValidateToken_(request.authToken,'master');
  if (!session.ok) return session;
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const system = commercialLoadSystem_();
    const tenant = system.tenants.find(function(t){return t.id === String(request.tenantId || '');});
    if (!tenant) return {ok:false,message:'Cliente não encontrado.'};
    if (request.name != null) tenant.name = String(request.name || '').trim() || tenant.name;
    if (request.cnpj != null) tenant.cnpj = String(request.cnpj || '').trim();
    if (request.plan != null) tenant.plan = commercialNormalizePlan_(request.plan);
    if (request.status != null) tenant.status = commercialNormalizeLicenseStatus_(request.status);
    if (request.validUntil != null) tenant.validUntil = commercialNormalizeDate_(request.validUntil);
    if (request.maxUsers != null) tenant.maxUsers = Math.max(1,Number(request.maxUsers || 1));
    if (request.maxDevices != null) tenant.maxDevices = Math.max(1,Number(request.maxDevices || 1));
    tenant.updatedAt = new Date().toISOString();
    commercialSaveSystem_(system);
    return {ok:true,tenant:commercialPublicTenant_(tenant),message:'Licença atualizada.'};
  } catch (error) {
    return {ok:false,message:String(error)};
  } finally {
    lock.releaseLock();
  }
}

function masterResetDevice_(request) {
  const session = commercialValidateToken_(request.authToken,'master');
  if (!session.ok) return session;
  const system = commercialLoadSystem_();
  const tenant = system.tenants.find(function(t){return t.id === String(request.tenantId || '');});
  if (!tenant) return {ok:false,message:'Cliente não encontrado.'};
  const deviceId = String(request.deviceId || '');
  const device = (tenant.devices || []).find(function(d){return d.id === deviceId;});
  if (!device) return {ok:false,message:'Dispositivo não encontrado.'};
  device.active = request.active !== false;
  device.updatedAt = new Date().toISOString();
  tenant.updatedAt = device.updatedAt;
  commercialSaveSystem_(system);
  return {ok:true,tenant:commercialPublicTenant_(tenant),message:device.active?'Dispositivo liberado.':'Dispositivo bloqueado.'};
}

function masterMigrateLegacy_(request) {
  const session = commercialValidateToken_(request.authToken,'master');
  if (!session.ok) return session;
  try {
    const system = commercialLoadSystem_();
    const tenant = system.tenants.find(function(t){return t.id === String(request.tenantId || '');});
    if (!tenant) return {ok:false,message:'Cliente não encontrado.'};
    const legacy = readEpiSnapshot_();
    const current = commercialReadTenantSnapshot_(tenant);
    const merged = mergeEpiSnapshots_(current,legacy);
    ensureDeliveryStockMovements_(merged);
    merged.revision = Math.max(Number(current.revision || 0),Number(legacy.revision || 0)) + 1;
    merged.updatedAt = new Date().toISOString();
    commercialWriteTenantSnapshot_(tenant,merged);
    return {ok:true,message:'Dados atuais migrados para o cliente.',summary:{companies:merged.app.companies.length,workers:merged.app.workers.length,epis:merged.app.epis.length,deliveries:merged.app.deliveries.length}};
  } catch (error) {
    return {ok:false,message:'Falha na migração: ' + String(error)};
  }
}

function tenantLogin_(request) {
  const code = commercialNormalizeTenantCode_(request.tenantCode);
  const username = commercialNormalizeUsername_(request.username);
  const password = String(request.password || '');
  const deviceId = String(request.deviceId || '').trim();
  const deviceLabel = String(request.deviceLabel || '').trim() || 'Dispositivo';
  if (!deviceId) return {ok:false,message:'Não foi possível identificar este dispositivo.'};

  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const system = commercialLoadSystem_();
    const tenant = system.tenants.find(function(t){return t.code === code;});
    if (!tenant) return {ok:false,message:'Cliente não encontrado. Verifique o código da empresa.'};
    const license = commercialLicenseState_(tenant);
    if (!license.ok) return license;

    const users = commercialLoadTenantUsers_(tenant);
    const user = users.find(function(u){return u.username === username;});
    if (!user || user.active === false || !commercialVerifyPassword_(password,user)) {
      Utilities.sleep(250);
      return {ok:false,message:'Usuário ou senha inválidos.'};
    }

    tenant.devices = Array.isArray(tenant.devices) ? tenant.devices : [];
    let device = tenant.devices.find(function(d){return d.id === deviceId;});
    if (device && device.active === false) return {ok:false,message:'Este dispositivo foi bloqueado pelo administrador.',code:'DEVICE_DISABLED'};
    if (!device) {
      const activeCount = tenant.devices.filter(function(d){return d.active !== false;}).length;
      if (activeCount >= Number(tenant.maxDevices || 1)) return {ok:false,message:'Limite de dispositivos atingido. Peça ao administrador para liberar um aparelho.',code:'DEVICE_LIMIT'};
      device = {id:deviceId,label:deviceLabel,active:true,createdAt:new Date().toISOString()};
      tenant.devices.push(device);
    }
    device.label = deviceLabel;
    device.lastSeenAt = new Date().toISOString();
    device.updatedAt = device.lastSeenAt;
    tenant.updatedAt = device.lastSeenAt;
    user.lastLoginAt = device.lastSeenAt;
    commercialSaveTenantUsers_(tenant,users);
    commercialSaveSystem_(system);

    const publicUser = commercialPublicUser_(user);
    const publicTenant = commercialPublicTenant_(tenant);
    return {ok:true,token:commercialCreateToken_({scope:'tenant',tenant:tenant,user:user,deviceId:deviceId}),user:publicUser,tenant:publicTenant,license:license.license};
  } catch (error) {
    return {ok:false,message:'Não foi possível entrar: ' + String(error)};
  } finally {
    lock.releaseLock();
  }
}

function tenantMe_(request) {
  const session = commercialValidateToken_(request.authToken,'tenant');
  if (!session.ok) return session;
  return {ok:true,user:session.user,tenant:session.tenant,license:session.license};
}

function tenantListUsers_(request) {
  const session = commercialRequireTenantRole_(request.authToken,['admin']);
  if (!session.ok) return session;
  const tenant = commercialTenantById_(session.tenant.id);
  return {ok:true,users:commercialLoadTenantUsers_(tenant).map(commercialPublicUser_),tenant:commercialPublicTenant_(tenant)};
}

function tenantCreateUser_(request) {
  const session = commercialRequireTenantRole_(request.authToken,['admin']);
  if (!session.ok) return session;
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const tenant = commercialTenantById_(session.tenant.id);
    const users = commercialLoadTenantUsers_(tenant);
    const activeCount = users.filter(function(u){return u.active !== false;}).length;
    if (activeCount >= Number(tenant.maxUsers || 1)) return {ok:false,message:'Limite de usuários da licença atingido.'};
    const username = commercialNormalizeUsername_(request.username);
    const password = String(request.password || '');
    const name = String(request.name || '').trim() || username;
    const role = commercialNormalizeTenantRole_(request.role);
    commercialValidateUsernamePassword_(username,password);
    if (users.some(function(u){return u.username === username;})) return {ok:false,message:'Esse usuário já existe.'};
    users.push(commercialNewUser_(username,name,role,password));
    commercialSaveTenantUsers_(tenant,users);
    return {ok:true,users:users.map(commercialPublicUser_),message:'Usuário criado.'};
  } catch (error) {
    return {ok:false,message:String(error)};
  } finally {
    lock.releaseLock();
  }
}

function tenantUpdateUser_(request) {
  const session = commercialRequireTenantRole_(request.authToken,['admin']);
  if (!session.ok) return session;
  const tenant = commercialTenantById_(session.tenant.id);
  const users = commercialLoadTenantUsers_(tenant);
  const username = commercialNormalizeUsername_(request.username);
  const user = users.find(function(u){return u.username === username;});
  if (!user) return {ok:false,message:'Usuário não encontrado.'};
  if (request.name != null) user.name = String(request.name || '').trim() || user.name;
  if (request.role != null) user.role = commercialNormalizeTenantRole_(request.role);
  if (request.active != null) user.active = request.active !== false;
  if (request.password) commercialSetPassword_(user,String(request.password));
  user.updatedAt = new Date().toISOString();
  if (!users.some(function(u){return u.role === 'admin' && u.active !== false;})) return {ok:false,message:'É necessário manter pelo menos um administrador ativo.'};
  commercialSaveTenantUsers_(tenant,users);
  return {ok:true,users:users.map(commercialPublicUser_),message:'Usuário atualizado.'};
}

function tenantChangeOwnPassword_(request) {
  const session = commercialValidateToken_(request.authToken,'tenant');
  if (!session.ok) return session;
  const tenant = commercialTenantById_(session.tenant.id);
  const users = commercialLoadTenantUsers_(tenant);
  const user = users.find(function(u){return u.username === session.user.username;});
  if (!user || !commercialVerifyPassword_(String(request.currentPassword || ''),user)) return {ok:false,message:'Senha atual incorreta.'};
  commercialSetPassword_(user,String(request.newPassword || ''));
  user.updatedAt = new Date().toISOString();
  commercialSaveTenantUsers_(tenant,users);
  return {ok:true,token:commercialCreateToken_({scope:'tenant',tenant:tenant,user:user,deviceId:session.deviceId}),user:commercialPublicUser_(user),tenant:commercialPublicTenant_(tenant),message:'Senha alterada.'};
}

function tenantSync_(request) {
  const session = commercialValidateToken_(request.authToken,'tenant');
  if (!session.ok) return session;
  const tenant = commercialTenantById_(session.tenant.id);
  if (!tenant) return {ok:false,message:'Cliente não encontrado.'};
  const license = commercialLicenseState_(tenant);
  if (!license.ok) return license;

  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const stored = commercialReadTenantSnapshot_(tenant);
    if (session.user.role === 'consulta') {
      return {ok:true,revision:Number(stored.revision || 0),updatedAt:String(stored.updatedAt || ''),payload:stored,readOnly:true,user:session.user,tenant:commercialPublicTenant_(tenant)};
    }

    const incoming = normalizeEpiSnapshot_(request.payload);
    let merged;
    if (session.user.role === 'campo') {
      merged = normalizeEpiSnapshot_(stored);
      merged.app.deliveries = mergeRecordsById_(stored.app.deliveries,incoming.app.deliveries);
      merged.stock = normalizeEpiSnapshot_(stored).stock;
    } else {
      merged = mergeEpiSnapshots_(stored,incoming);
    }
    ensureDeliveryStockMovements_(merged);
    merged.revision = Math.max(Number(stored.revision || 0),Number(incoming.revision || 0)) + 1;
    merged.updatedAt = new Date().toISOString();
    merged.version = EPI_SYNC_VERSION;
    commercialWriteTenantSnapshot_(tenant,merged);
    return {ok:true,revision:merged.revision,updatedAt:merged.updatedAt,payload:merged,user:session.user,tenant:commercialPublicTenant_(tenant),license:license.license};
  } catch (error) {
    return {ok:false,message:'Falha na sincronização: ' + String(error)};
  } finally {
    lock.releaseLock();
  }
}

function commercialLicenseState_(tenant) {
  const status = commercialNormalizeLicenseStatus_(tenant.status);
  const today = Utilities.formatDate(new Date(),Session.getScriptTimeZone() || 'America/Sao_Paulo','yyyy-MM-dd');
  const validUntil = commercialNormalizeDate_(tenant.validUntil);
  if (status === 'suspended') return {ok:false,message:'Licença suspensa. Entre em contato com o fornecedor.',code:'LICENSE_SUSPENDED'};
  if (validUntil && validUntil < today) return {ok:false,message:'Licença vencida em ' + validUntil.split('-').reverse().join('/') + '.',code:'LICENSE_EXPIRED'};
  return {ok:true,license:{status:status,validUntil:validUntil,plan:commercialNormalizePlan_(tenant.plan)}};
}

function commercialValidateToken_(token,expectedScope) {
  try {
    token = String(token || '');
    const parts = token.split('.');
    if (parts.length !== 2) return {ok:false,message:'Sessão inválida. Entre novamente.',code:'SESSION_INVALID'};
    const payloadEncoded = parts[0];
    if (!commercialSafeEqual_(parts[1],commercialSign_(payloadEncoded))) return {ok:false,message:'Sessão inválida. Entre novamente.',code:'SESSION_INVALID'};
    const bytes = Utilities.base64DecodeWebSafe(commercialPadBase64_(payloadEncoded));
    const payload = JSON.parse(Utilities.newBlob(bytes).getDataAsString('UTF-8'));
    if (payload.scope !== expectedScope) return {ok:false,message:'Sessão inválida.',code:'SESSION_INVALID'};
    if (!payload.exp || Date.now() > Number(payload.exp)) return {ok:false,message:'Sua sessão expirou. Entre novamente.',code:'SESSION_EXPIRED'};

    if (expectedScope === 'master') {
      const system = commercialLoadSystem_();
      const user = system.masterUsers.find(function(u){return u.username === payload.sub;});
      if (!user || user.active === false) return {ok:false,message:'Usuário Mestre bloqueado.',code:'USER_DISABLED'};
      return {ok:true,user:commercialPublicUser_(user)};
    }

    const system = commercialLoadSystem_();
    const tenant = system.tenants.find(function(t){return t.id === payload.tenantId;});
    if (!tenant) return {ok:false,message:'Cliente não encontrado.',code:'TENANT_NOT_FOUND'};
    const license = commercialLicenseState_(tenant);
    if (!license.ok) return license;
    const users = commercialLoadTenantUsers_(tenant);
    const user = users.find(function(u){return u.username === payload.sub;});
    if (!user || user.active === false) return {ok:false,message:'Usuário bloqueado ou removido.',code:'USER_DISABLED'};
    const device = (tenant.devices || []).find(function(d){return d.id === payload.deviceId;});
    if (!device || device.active === false) return {ok:false,message:'Este dispositivo não está autorizado.',code:'DEVICE_DISABLED'};
    return {ok:true,user:commercialPublicUser_(user),tenant:commercialPublicTenant_(tenant),license:license.license,deviceId:payload.deviceId};
  } catch (_) {
    return {ok:false,message:'Sessão inválida. Entre novamente.',code:'SESSION_INVALID'};
  }
}

function commercialRequireTenantRole_(token,roles) {
  const session = commercialValidateToken_(token,'tenant');
  if (!session.ok) return session;
  if (roles.indexOf(session.user.role) < 0) return {ok:false,message:'Seu usuário não tem permissão para esta ação.',code:'FORBIDDEN'};
  return session;
}

function commercialCreateToken_(ctx) {
  const now = Date.now();
  const payload = {scope:ctx.scope,sub:ctx.user.username,role:ctx.user.role,iat:now,exp:now + GESTAO_COM_TOKEN_HOURS * 60 * 60 * 1000,nonce:Utilities.getUuid()};
  if (ctx.scope === 'tenant') {
    payload.tenantId = ctx.tenant.id;
    payload.deviceId = String(ctx.deviceId || '');
  }
  const encoded = Utilities.base64EncodeWebSafe(JSON.stringify(payload)).replace(/=+$/,'');
  return encoded + '.' + commercialSign_(encoded);
}

function commercialSign_(value) {
  return Utilities.base64EncodeWebSafe(Utilities.computeHmacSha256Signature(String(value),commercialAuthSecret_())).replace(/=+$/,'');
}

function commercialAuthSecret_() {
  const props = PropertiesService.getScriptProperties();
  let secret = String(props.getProperty(GESTAO_COM_AUTH_SECRET_PROP) || '');
  if (!secret) {
    secret = Utilities.getUuid().replace(/-/g,'') + Utilities.getUuid().replace(/-/g,'');
    props.setProperty(GESTAO_COM_AUTH_SECRET_PROP,secret);
  }
  return secret;
}

function commercialNewUser_(username,name,role,password) {
  const user = {id:'u_' + Utilities.getUuid(),username:commercialNormalizeUsername_(username),name:String(name || username),role:role,active:true,createdAt:new Date().toISOString(),updatedAt:new Date().toISOString()};
  commercialSetPassword_(user,password);
  return user;
}

function commercialSetPassword_(user,password) {
  if (String(password || '').length < 6) throw new Error('A senha deve ter pelo menos 6 caracteres.');
  user.passwordSalt = Utilities.getUuid().replace(/-/g,'');
  user.passwordHash = commercialHashPassword_(password,user.passwordSalt);
}

function commercialVerifyPassword_(password,user) {
  return !!(user && user.passwordSalt && user.passwordHash && commercialSafeEqual_(commercialHashPassword_(password,user.passwordSalt),user.passwordHash));
}

function commercialHashPassword_(password,salt) {
  let value = String(salt) + ':' + String(password);
  for (let i=0;i<GESTAO_COM_HASH_ROUNDS;i++) {
    const bytes = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256,value,Utilities.Charset.UTF_8);
    value = commercialBytesHex_(bytes) + ':' + salt;
  }
  return value.split(':')[0];
}

function commercialBytesHex_(bytes) {
  return bytes.map(function(b){const n=b<0?b+256:b;return ('0'+n.toString(16)).slice(-2);}).join('');
}

function commercialSafeEqual_(a,b) {
  a=String(a||'');b=String(b||'');if(a.length!==b.length)return false;let diff=0;for(let i=0;i<a.length;i++)diff|=a.charCodeAt(i)^b.charCodeAt(i);return diff===0;
}

function commercialPadBase64_(value) {
  let s=String(value||'');while(s.length%4)s+='=';return s;
}

function commercialNormalizeUsername_(value) {
  return String(value || '').trim().toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/\s+/g,'.').replace(/[^a-z0-9._-]/g,'');
}

function commercialNormalizeTenantCode_(value) {
  return String(value || '').trim().toUpperCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^A-Z0-9]+/g,'-').replace(/^-+|-+$/g,'').slice(0,24);
}

function commercialNormalizeTenantRole_(value) {
  const role=String(value||'consulta').toLowerCase();return ['admin','campo','consulta'].indexOf(role)>=0?role:'consulta';
}

function commercialNormalizePlan_(value) {
  const plan=String(value||'profissional').toLowerCase();return ['basico','profissional','premium'].indexOf(plan)>=0?plan:'profissional';
}

function commercialNormalizeLicenseStatus_(value) {
  const status=String(value||'trial').toLowerCase();return ['trial','active','suspended'].indexOf(status)>=0?status:'trial';
}

function commercialValidateUsernamePassword_(username,password) {
  if (String(username||'').length<3) throw new Error('O usuário deve ter pelo menos 3 caracteres.');
  if (String(password||'').length<6) throw new Error('A senha deve ter pelo menos 6 caracteres.');
}

function commercialNormalizeDate_(value) {
  const s=String(value||'').trim();return /^\d{4}-\d{2}-\d{2}$/.test(s)?s:'';
}

function commercialFutureDate_(days) {
  const d=new Date();d.setDate(d.getDate()+Number(days||0));return Utilities.formatDate(d,Session.getScriptTimeZone()||'America/Sao_Paulo','yyyy-MM-dd');
}

function commercialPublicUser_(user) {
  return {id:String(user.id||''),username:String(user.username||''),name:String(user.name||user.username||''),role:String(user.role||''),active:user.active!==false,createdAt:String(user.createdAt||''),updatedAt:String(user.updatedAt||''),lastLoginAt:String(user.lastLoginAt||'')};
}

function commercialPublicTenant_(tenant) {
  const lic=commercialLicenseState_(tenant);
  return {id:String(tenant.id||''),code:String(tenant.code||''),name:String(tenant.name||''),cnpj:String(tenant.cnpj||''),plan:commercialNormalizePlan_(tenant.plan),status:lic.ok?commercialNormalizeLicenseStatus_(tenant.status):(lic.code==='LICENSE_EXPIRED'?'expired':commercialNormalizeLicenseStatus_(tenant.status)),validUntil:String(tenant.validUntil||''),maxUsers:Number(tenant.maxUsers||1),maxDevices:Number(tenant.maxDevices||1),devices:(tenant.devices||[]).map(function(d){return {id:String(d.id||''),label:String(d.label||''),active:d.active!==false,createdAt:String(d.createdAt||''),lastSeenAt:String(d.lastSeenAt||''),updatedAt:String(d.updatedAt||'')};}),createdAt:String(tenant.createdAt||''),updatedAt:String(tenant.updatedAt||'')};
}

function commercialRootFolder_() {
  return commercialFindOrCreateFolder_(DriveApp.getRootFolder(),GESTAO_COM_ROOT);
}

function commercialSystemFolder_() {
  return commercialFindOrCreateFolder_(commercialRootFolder_(),GESTAO_COM_SYSTEM_FOLDER);
}

function commercialClientsFolder_() {
  return commercialFindOrCreateFolder_(commercialRootFolder_(),GESTAO_COM_CLIENTS_FOLDER);
}

function commercialFindOrCreateFolder_(parent,name) {
  const it=parent.getFoldersByName(name);return it.hasNext()?it.next():parent.createFolder(name);
}

function commercialSystemFile_() {
  const folder=commercialSystemFolder_();const files=folder.getFilesByName(GESTAO_COM_SYSTEM_FILE);if(files.hasNext())return files.next();return folder.createFile(GESTAO_COM_SYSTEM_FILE,JSON.stringify({version:1,masterUsers:[],tenants:[],updatedAt:new Date().toISOString()}),MimeType.PLAIN_TEXT);
}

function commercialLoadSystem_() {
  try {
    const raw=JSON.parse(commercialSystemFile_().getBlob().getDataAsString('UTF-8')||'{}');
    return {version:1,masterUsers:Array.isArray(raw.masterUsers)?raw.masterUsers:[],tenants:Array.isArray(raw.tenants)?raw.tenants:[],updatedAt:String(raw.updatedAt||'')};
  } catch (_) {
    return {version:1,masterUsers:[],tenants:[],updatedAt:''};
  }
}

function commercialSaveSystem_(system) {
  system.version=1;system.updatedAt=new Date().toISOString();commercialSystemFile_().setContent(JSON.stringify(system));
}

function commercialCreateTenantFolder_(tenant) {
  const safeName=String(tenant.name||'Cliente').replace(/[\\/:*?"<>|]/g,' ').replace(/\s+/g,' ').trim().slice(0,70);
  return commercialClientsFolder_().createFolder(tenant.code+' - '+safeName);
}

function commercialTenantFolder_(tenant) {
  try {if(tenant.folderId)return DriveApp.getFolderById(tenant.folderId);} catch (_) {}
  const folder=commercialCreateTenantFolder_(tenant);tenant.folderId=folder.getId();const system=commercialLoadSystem_();const found=system.tenants.find(function(t){return t.id===tenant.id;});if(found){found.folderId=tenant.folderId;commercialSaveSystem_(system);}return folder;
}

function commercialTenantById_(tenantId) {
  return commercialLoadSystem_().tenants.find(function(t){return t.id===String(tenantId||'');}) || null;
}

function commercialReadJsonFile_(folder,name,fallback) {
  const files=folder.getFilesByName(name);if(!files.hasNext())return fallback;try{return JSON.parse(files.next().getBlob().getDataAsString('UTF-8')||'{}');}catch(_){return fallback;}
}

function commercialWriteJsonFile_(folder,name,data) {
  const files=folder.getFilesByName(name);const text=JSON.stringify(data);if(files.hasNext())files.next().setContent(text);else folder.createFile(name,text,MimeType.PLAIN_TEXT);
}

function commercialLoadTenantUsers_(tenant) {
  const root=commercialReadJsonFile_(commercialTenantFolder_(tenant),GESTAO_COM_USERS_FILE,{version:1,users:[]});return Array.isArray(root.users)?root.users:[];
}

function commercialSaveTenantUsers_(tenant,users) {
  commercialWriteJsonFile_(commercialTenantFolder_(tenant),GESTAO_COM_USERS_FILE,{version:1,users:users||[],updatedAt:new Date().toISOString()});
}

function commercialReadTenantSnapshot_(tenant) {
  const root=commercialReadJsonFile_(commercialTenantFolder_(tenant),GESTAO_COM_DATA_FILE,blankEpiSnapshot_());return normalizeEpiSnapshot_(root);
}

function commercialWriteTenantSnapshot_(tenant,data) {
  commercialWriteJsonFile_(commercialTenantFolder_(tenant),GESTAO_COM_DATA_FILE,normalizeEpiSnapshot_(data));
}

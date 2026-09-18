const SST_USER_PROFILES_SHEET = 'PerfisUsuarios';

function sstAuthNormalizeUsername_(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, '')
    .replace(/^[._-]+|[._-]+$/g, '')
    .substring(0, 40);
}

function sstAuthProfileSheet_() {
  ensureAuthStorage_();
  const id = PropertiesService.getScriptProperties().getProperty('SST_GESTAO_SPREADSHEET_ID');
  const ss = SpreadsheetApp.openById(id);
  return ensureSheet_(ss, SST_USER_PROFILES_SHEET, ['user_id','username','contact_email','updated_at']);
}

function sstAuthProfiles_() {
  const sheet = sstAuthProfileSheet_();
  const last = sheet.getLastRow();
  if (last < 2) return [];
  return sheet.getRange(2,1,last-1,4).getValues().map(function(row,index){
    return {
      rowNumber:index+2,
      userId:String(row[0]||''),
      username:sstAuthNormalizeUsername_(row[1]),
      contactEmail:String(row[2]||'').trim().toLowerCase(),
      updatedAt:String(row[3]||'')
    };
  });
}

function sstAuthDerivedUsername_(user) {
  const email = String(user && user.email || '').trim().toLowerCase();
  return sstAuthNormalizeUsername_(email.split('@')[0] || '');
}

function sstAuthProfileForUser_(user) {
  const profiles = sstAuthProfiles_();
  const found = profiles.find(function(p){ return p.userId === String(user && user.id || ''); });
  return found || {
    userId:String(user && user.id || ''),
    username:sstAuthDerivedUsername_(user),
    contactEmail:(String(user && user.email || '').indexOf('@sstgestao.local') < 0
      ? String(user && user.email || '').trim().toLowerCase()
      : '')
  };
}

function sstAuthSaveProfile_(userId, username, contactEmail) {
  const clean = sstAuthNormalizeUsername_(username);
  const email = String(contactEmail || '').trim().toLowerCase();
  if (clean.length < 3) throw new Error('O usuário deve ter pelo menos 3 caracteres.');
  if (email && !/^\S+@\S+\.\S+$/.test(email)) throw new Error('O e-mail opcional informado não é válido.');

  const profiles = sstAuthProfiles_();
  const owner = profiles.find(function(p){ return p.username === clean && p.userId !== String(userId||''); });
  if (owner) throw new Error('Este nome de usuário já está em uso.');

  const sheet = sstAuthProfileSheet_();
  const current = profiles.find(function(p){ return p.userId === String(userId||''); });
  const values = [String(userId||''), clean, email, new Date().toISOString()];
  if (current) sheet.getRange(current.rowNumber,1,1,4).setValues([values]);
  else sheet.appendRow(values);
  return {username:clean, contactEmail:email};
}

function sstAuthPublicUser_(user) {
  const base = authPublicUser_(user);
  const profile = sstAuthProfileForUser_(user);
  base.username = profile.username || sstAuthDerivedUsername_(user);
  base.contactEmail = profile.contactEmail || '';
  return base;
}

function sstAuthBootstrapAdmin_(request) {
  const username = sstAuthNormalizeUsername_(request.username);
  if (username.length < 3) return {ok:false,message:'Crie um usuário com pelo menos 3 caracteres.'};
  const loginEmail = username + '@sstgestao.local';
  const adapted = Object.assign({}, request, {email:loginEmail});
  const result = authBootstrapAdmin_(adapted);
  if (!result || result.ok !== true) return result;
  try {
    sstAuthSaveProfile_(result.user.id, username, request.contactEmail || '');
    const stored = readAuthUsers_().find(function(u){ return u.id === result.user.id; });
    if (stored) result.user = sstAuthPublicUser_(stored);
  } catch (error) {
    return {ok:false,message:String(error)};
  }
  return result;
}

function sstAuthLogin_(request) {
  const username = sstAuthNormalizeUsername_(request.username || request.email);
  const password = String(request.password || '');
  if (username.length < 3) return {ok:false,code:'LOGIN_INVALID',message:'Usuário ou senha inválidos.'};

  const profiles = sstAuthProfiles_();
  const users = readAuthUsers_();
  let user = null;
  const profile = profiles.find(function(p){ return p.username === username; });
  if (profile) user = users.find(function(u){ return u.id === profile.userId; }) || null;
  if (!user) user = users.find(function(u){ return sstAuthDerivedUsername_(u) === username; }) || null;

  if (!user || !user.active || authPasswordHash_(password, user.passwordSalt) !== user.passwordHash) {
    return {ok:false,code:'LOGIN_INVALID',message:'Usuário ou senha inválidos.'};
  }

  const now = new Date().toISOString();
  getSheet_(AUTH_USERS_SHEET).getRange(user.rowNumber, 12).setValue(now);
  user.lastLoginAt = now;
  const session = authCreateSession_(user, request);
  auditAuthEvent_(user,'login','session','','',request.deviceId,request.platform,{username:username});
  return {ok:true,user:sstAuthPublicUser_(user),sessionToken:session.token};
}

function sstAuthSession_(request) {
  const user = authUserFromToken_(request.authToken, true);
  if (!user) return {ok:false,code:'SESSION_INVALID',message:'Sessão expirada. Entre novamente.'};
  return {ok:true,user:sstAuthPublicUser_(user)};
}

function sstAuthUsersList_(request) {
  const actor = authUserFromToken_(request.authToken, true);
  if (!actor) return {ok:false,code:'SESSION_INVALID',message:'Sessão expirada. Entre novamente.'};
  if (actor.role !== 'admin') return {ok:false,code:'ACCESS_DENIED',message:'Apenas administradores podem gerenciar usuários.'};
  return {ok:true,users:readAuthUsers_().map(sstAuthPublicUser_)};
}

function sstAuthUserSave_(request) {
  const actor = authUserFromToken_(request.authToken, true);
  if (!actor) return {ok:false,code:'SESSION_INVALID',message:'Sessão expirada. Entre novamente.'};
  if (actor.role !== 'admin') return {ok:false,code:'ACCESS_DENIED',message:'Apenas administradores podem gerenciar usuários.'};

  const input = request.user || {};
  const username = sstAuthNormalizeUsername_(input.username);
  if (username.length < 3) return {ok:false,message:'Crie um usuário com pelo menos 3 caracteres.'};

  const existingUsers = readAuthUsers_();
  const existing = String(input.id||'')
    ? existingUsers.find(function(u){ return u.id === String(input.id||''); }) || null
    : null;

  const adapted = JSON.parse(JSON.stringify(request));
  adapted.user = Object.assign({}, input);
  adapted.user.email = existing
    ? existing.email
    : username + '@sstgestao.local';

  const result = authUserSave_(adapted);
  if (!result || result.ok !== true) return result;

  try {
    sstAuthSaveProfile_(result.user.id, username, input.contactEmail || '');
    const stored = readAuthUsers_().find(function(u){ return u.id === result.user.id; });
    if (stored) result.user = sstAuthPublicUser_(stored);
  } catch (error) {
    return {ok:false,message:String(error)};
  }
  return result;
}

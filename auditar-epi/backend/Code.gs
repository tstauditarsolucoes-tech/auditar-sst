function doPost(e) {
  try {
    const request = JSON.parse((e.postData && e.postData.contents) || '{}');
    const props = PropertiesService.getScriptProperties();
    const expectedKey = props.getProperty('AUDITAR_EPI_SYNC_KEY');

    if (!expectedKey) {
      return jsonResponse_({ok:false,message:'Central Gestão EPI ainda não configurada.'});
    }

    if (request.syncKey !== expectedKey) {
      return jsonResponse_({ok:false,message:'Chave da central inválida.'});
    }

    if (request.action === 'auth_status') return jsonResponse_(authStatus_());
    if (request.action === 'auth_bootstrap_admin') return jsonResponse_(authBootstrapAdmin_(request));
    if (request.action === 'auth_login') return jsonResponse_(authLogin_(request));
    if (request.action === 'auth_me') return jsonResponse_(authMe_(request));
    if (request.action === 'auth_list_users') return jsonResponse_(authListUsers_(request));
    if (request.action === 'auth_create_user') return jsonResponse_(authCreateUser_(request));
    if (request.action === 'auth_update_user') return jsonResponse_(authUpdateUser_(request));
    if (request.action === 'auth_change_password') return jsonResponse_(authChangeOwnPassword_(request));

    if (request.action === 'epi_sync_merge') {
      const session = authValidateToken_(request.authToken);
      if (!session.ok) return jsonResponse_(session);

      if (session.user.role === 'consulta') {
        const data = readEpiSnapshot_();
        return jsonResponse_({
          ok:true,
          revision:Number(data.revision || 0),
          updatedAt:String(data.updatedAt || ''),
          payload:data,
          readOnly:true,
          user:session.user,
          message:'Consulta sincronizada em modo somente leitura.'
        });
      }

      const result = epiSyncMerge_(request);
      if (result && result.ok) result.user = session.user;
      return jsonResponse_(result);
    }

    return jsonResponse_({ok:false,message:'Ação não reconhecida.'});
  } catch (error) {
    return jsonResponse_({ok:false,message:String(error)});
  }
}

function jsonResponse_(data) {
  return ContentService.createTextOutput(JSON.stringify(data)).setMimeType(ContentService.MimeType.JSON);
}

const EPI_AUTH_USERS_PROP = 'GESTAO_EPI_USERS_V1';
const EPI_AUTH_SECRET_PROP = 'GESTAO_EPI_AUTH_SECRET_V1';
const EPI_AUTH_TOKEN_HOURS = 12;
const EPI_AUTH_HASH_ROUNDS = 1200;

function authStatus_() {
  const users = authLoadUsers_();
  return {ok:true,configured:users.length > 0,userCount:users.length};
}

function authBootstrapAdmin_(request) {
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const users = authLoadUsers_();
    if (users.length) return {ok:false,message:'O administrador inicial já foi criado.'};
    const username = authNormalizeUsername_(request.username);
    const name = String(request.name || '').trim() || username;
    const password = String(request.password || '');
    authValidateUsernamePassword_(username,password);
    const user = authNewUser_(username,name,'admin',password);
    authSaveUsers_([user]);
    return {ok:true,message:'Administrador criado com sucesso.',token:authCreateToken_(user),user:authPublicUser_(user)};
  } catch (error) {
    return {ok:false,message:String(error)};
  } finally {
    lock.releaseLock();
  }
}

function authLogin_(request) {
  try {
    const username = authNormalizeUsername_(request.username);
    const password = String(request.password || '');
    const users = authLoadUsers_();
    const user = users.find(function(u){return u.username === username;});
    if (!user || user.active === false || !authVerifyPassword_(password,user)) {
      Utilities.sleep(250);
      return {ok:false,message:'Usuário ou senha inválidos.'};
    }
    user.lastLoginAt = new Date().toISOString();
    user.updatedAt = user.updatedAt || user.lastLoginAt;
    authSaveUsers_(users);
    return {ok:true,token:authCreateToken_(user),user:authPublicUser_(user)};
  } catch (error) {
    return {ok:false,message:'Não foi possível entrar: ' + String(error)};
  }
}

function authMe_(request) {
  const session = authValidateToken_(request.authToken);
  if (!session.ok) return session;
  return {ok:true,user:session.user};
}

function authListUsers_(request) {
  const session = authRequireRole_(request.authToken,['admin']);
  if (!session.ok) return session;
  return {ok:true,users:authLoadUsers_().map(authPublicUser_)};
}

function authCreateUser_(request) {
  const session = authRequireRole_(request.authToken,['admin']);
  if (!session.ok) return session;
  try {
    const username = authNormalizeUsername_(request.username);
    const name = String(request.name || '').trim() || username;
    const role = authNormalizeRole_(request.role);
    const password = String(request.password || '');
    authValidateUsernamePassword_(username,password);
    const users = authLoadUsers_();
    if (users.some(function(u){return u.username === username;})) return {ok:false,message:'Esse usuário já existe.'};
    users.push(authNewUser_(username,name,role,password));
    authSaveUsers_(users);
    return {ok:true,users:users.map(authPublicUser_),message:'Usuário criado.'};
  } catch (error) {
    return {ok:false,message:String(error)};
  }
}

function authUpdateUser_(request) {
  const session = authRequireRole_(request.authToken,['admin']);
  if (!session.ok) return session;
  try {
    const username = authNormalizeUsername_(request.username);
    const users = authLoadUsers_();
    const user = users.find(function(u){return u.username === username;});
    if (!user) return {ok:false,message:'Usuário não encontrado.'};
    if (request.name != null) user.name = String(request.name || '').trim() || user.name;
    if (request.role != null) user.role = authNormalizeRole_(request.role);
    if (request.active != null) user.active = request.active !== false;
    if (request.password) authSetPassword_(user,String(request.password));
    user.updatedAt = new Date().toISOString();
    const activeAdmins = users.filter(function(u){return u.role === 'admin' && u.active !== false;});
    if (!activeAdmins.length) return {ok:false,message:'É necessário manter pelo menos um administrador ativo.'};
    authSaveUsers_(users);
    return {ok:true,users:users.map(authPublicUser_),message:'Usuário atualizado.'};
  } catch (error) {
    return {ok:false,message:String(error)};
  }
}

function authChangeOwnPassword_(request) {
  const session = authValidateToken_(request.authToken);
  if (!session.ok) return session;
  try {
    const currentPassword = String(request.currentPassword || '');
    const newPassword = String(request.newPassword || '');
    if (newPassword.length < 6) return {ok:false,message:'A nova senha deve ter pelo menos 6 caracteres.'};
    const users = authLoadUsers_();
    const user = users.find(function(u){return u.username === session.user.username;});
    if (!user || !authVerifyPassword_(currentPassword,user)) return {ok:false,message:'Senha atual incorreta.'};
    authSetPassword_(user,newPassword);
    user.updatedAt = new Date().toISOString();
    authSaveUsers_(users);
    return {ok:true,token:authCreateToken_(user),user:authPublicUser_(user),message:'Senha alterada.'};
  } catch (error) {
    return {ok:false,message:String(error)};
  }
}

function authValidateToken_(token) {
  try {
    token = String(token || '');
    const parts = token.split('.');
    if (parts.length !== 2) return {ok:false,message:'Sessão inválida. Entre novamente.'};
    const payloadEncoded = parts[0];
    const expected = authSign_(payloadEncoded);
    if (!authSafeEqual_(parts[1],expected)) return {ok:false,message:'Sessão inválida. Entre novamente.'};
    const payloadBytes = Utilities.base64DecodeWebSafe(authPadBase64_(payloadEncoded));
    const payload = JSON.parse(Utilities.newBlob(payloadBytes).getDataAsString('UTF-8'));
    if (!payload.exp || Date.now() > Number(payload.exp)) return {ok:false,message:'Sua sessão expirou. Entre novamente.',code:'SESSION_EXPIRED'};
    const users = authLoadUsers_();
    const user = users.find(function(u){return u.username === payload.sub;});
    if (!user || user.active === false) return {ok:false,message:'Usuário bloqueado ou removido.',code:'USER_DISABLED'};
    return {ok:true,user:authPublicUser_(user)};
  } catch (_) {
    return {ok:false,message:'Sessão inválida. Entre novamente.'};
  }
}

function authRequireRole_(token,roles) {
  const session = authValidateToken_(token);
  if (!session.ok) return session;
  if (roles.indexOf(session.user.role) < 0) return {ok:false,message:'Seu usuário não tem permissão para esta ação.',code:'FORBIDDEN'};
  return session;
}

function authCreateToken_(user) {
  const now = Date.now();
  const payload = {sub:user.username,role:user.role,iat:now,exp:now + EPI_AUTH_TOKEN_HOURS * 60 * 60 * 1000,nonce:Utilities.getUuid()};
  const encoded = Utilities.base64EncodeWebSafe(JSON.stringify(payload)).replace(/=+$/,'');
  return encoded + '.' + authSign_(encoded);
}

function authSign_(value) {
  const secret = authSecret_();
  return Utilities.base64EncodeWebSafe(Utilities.computeHmacSha256Signature(String(value),secret)).replace(/=+$/,'');
}

function authSecret_() {
  const props = PropertiesService.getScriptProperties();
  let secret = String(props.getProperty(EPI_AUTH_SECRET_PROP) || '');
  if (!secret) {
    secret = Utilities.getUuid().replace(/-/g,'') + Utilities.getUuid().replace(/-/g,'');
    props.setProperty(EPI_AUTH_SECRET_PROP,secret);
  }
  return secret;
}

function authNewUser_(username,name,role,password) {
  const user = {id:'u_' + Utilities.getUuid(),username:username,name:name,role:authNormalizeRole_(role),active:true,createdAt:new Date().toISOString(),updatedAt:new Date().toISOString()};
  authSetPassword_(user,password);
  return user;
}

function authSetPassword_(user,password) {
  if (String(password || '').length < 6) throw new Error('A senha deve ter pelo menos 6 caracteres.');
  user.passwordSalt = Utilities.getUuid().replace(/-/g,'');
  user.passwordHash = authHashPassword_(password,user.passwordSalt);
}

function authVerifyPassword_(password,user) {
  if (!user.passwordSalt || !user.passwordHash) return false;
  return authSafeEqual_(authHashPassword_(password,user.passwordSalt),user.passwordHash);
}

function authHashPassword_(password,salt) {
  let value = String(salt) + ':' + String(password);
  for (let i = 0; i < EPI_AUTH_HASH_ROUNDS; i++) {
    const bytes = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256,value,Utilities.Charset.UTF_8);
    value = authBytesHex_(bytes) + ':' + salt;
  }
  return value.split(':')[0];
}

function authBytesHex_(bytes) {
  return bytes.map(function(b){const n=(b<0?b+256:b);return ('0'+n.toString(16)).slice(-2);}).join('');
}

function authSafeEqual_(a,b) {
  a = String(a || ''); b = String(b || '');
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i=0;i<a.length;i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function authPadBase64_(value) {
  let s = String(value || '');
  while (s.length % 4) s += '=';
  return s;
}

function authLoadUsers_() {
  try {
    const raw = PropertiesService.getScriptProperties().getProperty(EPI_AUTH_USERS_PROP) || '[]';
    const list = JSON.parse(raw);
    return Array.isArray(list) ? list : [];
  } catch (_) {
    return [];
  }
}

function authSaveUsers_(users) {
  PropertiesService.getScriptProperties().setProperty(EPI_AUTH_USERS_PROP,JSON.stringify(users || []));
}

function authPublicUser_(user) {
  return {id:String(user.id || ''),username:String(user.username || ''),name:String(user.name || user.username || ''),role:authNormalizeRole_(user.role),active:user.active !== false,createdAt:String(user.createdAt || ''),updatedAt:String(user.updatedAt || ''),lastLoginAt:String(user.lastLoginAt || '')};
}

function authNormalizeUsername_(value) {
  return String(value || '').trim().toLowerCase().replace(/\s+/g,'.').replace(/[^a-z0-9._-]/g,'');
}

function authNormalizeRole_(value) {
  const role = String(value || 'consulta').toLowerCase();
  return ['admin','campo','consulta'].indexOf(role) >= 0 ? role : 'consulta';
}

function authValidateUsernamePassword_(username,password) {
  if (username.length < 3) throw new Error('O usuário deve ter pelo menos 3 caracteres.');
  if (String(password || '').length < 6) throw new Error('A senha deve ter pelo menos 6 caracteres.');
}

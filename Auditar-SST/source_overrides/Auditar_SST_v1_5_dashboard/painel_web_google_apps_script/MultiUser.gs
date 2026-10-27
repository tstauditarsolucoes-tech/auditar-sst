const AUTH_USERS_SHEET = 'Usuarios';
const AUTH_SESSIONS_SHEET = 'Sessoes';
const AUTH_AUDIT_SHEET = 'AuditoriaUsuarios';
const AUTH_SESSION_DAYS = 180;

/**
 * Complemento multiusuário do Auditar SST v3.23.
 *
 * Compatibilidade:
 * - clientes 3.22 continuam autenticando pela AUDITAR_SYNC_KEY;
 * - clientes 3.23 enviam authToken e recebem somente as empresas liberadas;
 * - o mesmo usuário pode manter sessões distintas no Android e no Windows.
 */
function setupAuthStorage_(ss) {
  ensureSheet_(ss, AUTH_USERS_SHEET, [
    'user_id', 'name', 'email', 'password_hash', 'password_salt', 'role',
    'active', 'all_companies', 'company_ids_json', 'created_at', 'updated_at', 'last_login_at'
  ]);
  ensureSheet_(ss, AUTH_SESSIONS_SHEET, [
    'session_token', 'user_id', 'device_id', 'platform', 'created_at',
    'last_seen_at', 'expires_at', 'revoked'
  ]);
  ensureSheet_(ss, AUTH_AUDIT_SHEET, [
    'created_at', 'user_id', 'email', 'action', 'entity_type', 'entity_id',
    'company_id', 'device_id', 'platform', 'details_json'
  ]);
  ensureSheet_(ss, DEVICE_SYNC_SHEET, [
    'table_name', 'record_id', 'deleted', 'server_version',
    'source_device', 'source_platform', 'updated_at', 'payload_json',
    'company_id', 'updated_by_user'
  ]);
}

function ensureAuthStorage_() {
  const spreadsheetId = PropertiesService.getScriptProperties().getProperty('AUDITAR_SPREADSHEET_ID');
  if (!spreadsheetId) throw new Error('Execute setupAuditar() primeiro.');
  const ss = SpreadsheetApp.openById(spreadsheetId);
  setupAuthStorage_(ss);
  return ss;
}

function handleAuthAction_(request, expectedKey) {
  const action = String(request.action || '').trim();
  if (action === 'auth_status') {
    return {handled: true, response: authStatus_()};
  }
  if (action === 'auth_bootstrap_admin') {
    if (request.syncKey !== expectedKey) {
      return {handled: true, response: {ok: false, message: 'Chave de sincronização inválida.'}};
    }
    return {handled: true, response: authBootstrapAdmin_(request)};
  }
  if (action === 'auth_login') return {handled: true, response: authLogin_(request)};
  if (action === 'auth_session') return {handled: true, response: authSession_(request)};
  if (action === 'auth_logout') return {handled: true, response: authLogout_(request)};
  if (action === 'auth_users_list') return {handled: true, response: authUsersList_(request)};
  if (action === 'auth_user_save') return {handled: true, response: authUserSave_(request)};
  return {handled: false};
}

function authorizeMultiUserToken_(request) {
  const token = String(request.authToken || '').trim();
  if (!token) return {ok: false, code: 'AUTH_REQUIRED', message: 'Faça login novamente.'};
  const user = authUserFromToken_(token, true);
  if (!user) {
    return {ok: false, code: 'SESSION_INVALID', message: 'Sessão expirada. Entre novamente.'};
  }
  return {ok: true, user: user};
}

function requestCompanyIdMultiUser_(request) {
  if (request.companyId) return String(request.companyId || '').trim();
  const payload = request.payload || {};
  if (payload.companyId) return String(payload.companyId || '').trim();
  if (payload.company_id) return String(payload.company_id || '').trim();
  if (payload.company && payload.company.id) return String(payload.company.id || '').trim();
  if (payload.company && payload.company.company_id) return String(payload.company.company_id || '').trim();
  return '';
}

function userCanAccessCompany_(user, companyId) {
  if (!user) return true;
  const id = String(companyId || '').trim();
  if (!id) return true;
  return user.role === 'admin' || user.allCompanies || user.companyIds.indexOf(id) >= 0;
}

function authStatus_() {
  const spreadsheetId = String(
    PropertiesService.getScriptProperties().getProperty('AUDITAR_SPREADSHEET_ID') || ''
  ).trim();
  if (!spreadsheetId) return {ok: true, configured: false, hasUsers: false};
  ensureAuthStorage_();
  return {ok: true, configured: true, hasUsers: readAuthUsers_().length > 0};
}

function readAuthUsers_() {
  ensureAuthStorage_();
  const sheet = getSheet_(AUTH_USERS_SHEET);
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];
  return sheet.getRange(2, 1, lastRow - 1, 12).getValues().map((row, index) => ({
    rowNumber: index + 2,
    id: String(row[0] || ''),
    name: String(row[1] || ''),
    email: normalizeAuthEmail_(row[2]),
    passwordHash: String(row[3] || ''),
    passwordSalt: String(row[4] || ''),
    role: String(row[5] || 'tecnico').toLowerCase() === 'admin' ? 'admin' : 'tecnico',
    active: authBool_(row[6], true),
    allCompanies: authBool_(row[7], false),
    companyIds: authCompanyIds_(row[8]),
    createdAt: String(row[9] || ''),
    updatedAt: String(row[10] || ''),
    lastLoginAt: String(row[11] || '')
  }));
}

function authBool_(value, fallback) {
  if (value === true || String(value).toLowerCase() === 'true' || Number(value) === 1) return true;
  if (value === false || String(value).toLowerCase() === 'false' || Number(value) === 0) return false;
  return fallback;
}

function authCompanyIds_(value) {
  try {
    const parsed = JSON.parse(String(value || '[]'));
    return Array.isArray(parsed)
      ? parsed.map(item => String(item || '').trim()).filter(Boolean)
      : [];
  } catch (_) {
    return [];
  }
}

function normalizeAuthEmail_(value) {
  return String(value || '').trim().toLowerCase();
}

function authHex_(bytes) {
  return bytes
    .map(value => ((Number(value) + 256) % 256).toString(16).padStart(2, '0'))
    .join('');
}

function authPasswordHash_(password, salt) {
  return authHex_(Utilities.computeDigest(
    Utilities.DigestAlgorithm.SHA_256,
    String(salt || '') + '|' + String(password || ''),
    Utilities.Charset.UTF_8
  ));
}

function authPublicUser_(user) {
  return {
    id: user.id,
    name: user.name,
    email: user.email,
    role: user.role,
    active: user.active,
    allCompanies: user.role === 'admin' ? true : user.allCompanies,
    companyIds: user.role === 'admin' || user.allCompanies ? [] : user.companyIds
  };
}

function authBootstrapAdmin_(request) {
  ensureAuthStorage_();
  if (readAuthUsers_().length > 0) {
    return {ok: false, message: 'A conta administradora já foi criada.'};
  }
  const name = String(request.name || '').trim();
  const email = normalizeAuthEmail_(request.email);
  const password = String(request.password || '');
  if (name.length < 3) return {ok: false, message: 'Informe o nome do administrador.'};
  if (!/^\S+@\S+\.\S+$/.test(email)) return {ok: false, message: 'Informe um e-mail válido.'};
  if (password.length < 8) return {ok: false, message: 'A senha deve ter pelo menos 8 caracteres.'};

  const now = new Date().toISOString();
  const salt = Utilities.getUuid().replace(/-/g, '') + Utilities.getUuid().replace(/-/g, '');
  const user = {
    id: Utilities.getUuid(),
    name: name,
    email: email,
    passwordHash: authPasswordHash_(password, salt),
    passwordSalt: salt,
    role: 'admin',
    active: true,
    allCompanies: true,
    companyIds: [],
    createdAt: now,
    updatedAt: now,
    lastLoginAt: now
  };
  getSheet_(AUTH_USERS_SHEET).appendRow([
    user.id, user.name, user.email, user.passwordHash, user.passwordSalt,
    user.role, true, true, '[]', now, now, now
  ]);
  const session = authCreateSession_(user, request);
  auditAuthEvent_(
    user,
    'bootstrap_admin',
    'user',
    user.id,
    '',
    request.deviceId,
    request.platform,
    {}
  );
  return {ok: true, user: authPublicUser_(user), sessionToken: session.token};
}

function authLogin_(request) {
  const email = normalizeAuthEmail_(request.email);
  const password = String(request.password || '');
  const users = readAuthUsers_();
  const user = users.find(item => item.email === email);
  if (!user || !user.active || authPasswordHash_(password, user.passwordSalt) !== user.passwordHash) {
    return {ok: false, code: 'LOGIN_INVALID', message: 'E-mail ou senha inválidos.'};
  }

  const now = new Date().toISOString();
  getSheet_(AUTH_USERS_SHEET).getRange(user.rowNumber, 12).setValue(now);
  user.lastLoginAt = now;
  const session = authCreateSession_(user, request);
  auditAuthEvent_(
    user,
    'login',
    'session',
    '',
    '',
    request.deviceId,
    request.platform,
    {}
  );
  return {ok: true, user: authPublicUser_(user), sessionToken: session.token};
}

function authCreateSession_(user, request) {
  ensureAuthStorage_();
  const token =
    Utilities.getUuid().replace(/-/g, '') +
    Utilities.getUuid().replace(/-/g, '') +
    Utilities.getUuid().replace(/-/g, '');
  const now = new Date();
  const expires = new Date(now.getTime() + AUTH_SESSION_DAYS * 24 * 60 * 60 * 1000);
  getSheet_(AUTH_SESSIONS_SHEET).appendRow([
    token,
    user.id,
    String(request.deviceId || ''),
    String(request.platform || ''),
    now.toISOString(),
    now.toISOString(),
    expires.toISOString(),
    false
  ]);
  return {token: token, expiresAt: expires.toISOString()};
}

function authUserFromToken_(token, touch) {
  const clean = String(token || '').trim();
  if (!clean) return null;
  ensureAuthStorage_();
  const sheet = getSheet_(AUTH_SESSIONS_SHEET);
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return null;
  const rows = sheet.getRange(2, 1, lastRow - 1, 8).getValues();
  let sessionIndex = -1;
  for (let i = 0; i < rows.length; i++) {
    if (String(rows[i][0] || '') === clean) {
      sessionIndex = i;
      break;
    }
  }
  if (sessionIndex < 0) return null;

  const session = rows[sessionIndex];
  if (authBool_(session[7], false)) return null;
  const expires = new Date(String(session[6] || ''));
  if (!expires.getTime() || expires.getTime() < Date.now()) return null;

  const userId = String(session[1] || '');
  const user = readAuthUsers_().find(item => item.id === userId && item.active);
  if (!user) return null;
  user.sessionDeviceId = String(session[2] || '');
  user.sessionPlatform = String(session[3] || '');
  user.sessionRowNumber = sessionIndex + 2;

  if (touch) {
    const lastSeen = new Date(String(session[5] || ''));
    if (!lastSeen.getTime() || Date.now() - lastSeen.getTime() > 10 * 60 * 1000) {
      sheet.getRange(sessionIndex + 2, 6).setValue(new Date().toISOString());
    }
  }
  return user;
}

function authSession_(request) {
  const user = authUserFromToken_(request.authToken, true);
  if (!user) {
    return {ok: false, code: 'SESSION_INVALID', message: 'Sessão expirada. Entre novamente.'};
  }
  return {ok: true, user: authPublicUser_(user)};
}

function authLogout_(request) {
  const token = String(request.authToken || '').trim();
  if (!token) return {ok: true};
  ensureAuthStorage_();
  const sheet = getSheet_(AUTH_SESSIONS_SHEET);
  const lastRow = sheet.getLastRow();
  if (lastRow >= 2) {
    const rows = sheet.getRange(2, 1, lastRow - 1, 8).getValues();
    for (let i = 0; i < rows.length; i++) {
      if (String(rows[i][0] || '') === token) {
        sheet.getRange(i + 2, 8).setValue(true);
        break;
      }
    }
  }
  return {ok: true};
}

function authUsersList_(request) {
  const actor = authUserFromToken_(request.authToken, true);
  if (!actor) {
    return {ok: false, code: 'SESSION_INVALID', message: 'Sessão expirada. Entre novamente.'};
  }
  if (actor.role !== 'admin') {
    return {ok: false, code: 'ACCESS_DENIED', message: 'Apenas administradores podem gerenciar usuários.'};
  }
  return {ok: true, users: readAuthUsers_().map(authPublicUser_)};
}

function authUserSave_(request) {
  const actor = authUserFromToken_(request.authToken, true);
  if (!actor) {
    return {ok: false, code: 'SESSION_INVALID', message: 'Sessão expirada. Entre novamente.'};
  }
  if (actor.role !== 'admin') {
    return {ok: false, code: 'ACCESS_DENIED', message: 'Apenas administradores podem gerenciar usuários.'};
  }

  const input = request.user || {};
  const name = String(input.name || '').trim();
  const email = normalizeAuthEmail_(input.email);
  const role = String(input.role || '').toLowerCase() === 'admin' ? 'admin' : 'tecnico';
  const active = input.active !== false;
  const allCompanies = role === 'admin' ? true : input.allCompanies === true;
  const companyIds = allCompanies
    ? []
    : (Array.isArray(input.companyIds) ? input.companyIds : [])
        .map(item => String(item || '').trim())
        .filter(Boolean)
        .filter((id, index, array) => array.indexOf(id) === index)
        .slice(0, 300);
  const password = String(input.password || '');

  if (name.length < 3) return {ok: false, message: 'Informe o nome do usuário.'};
  if (!/^\S+@\S+\.\S+$/.test(email)) return {ok: false, message: 'Informe um e-mail válido.'};
  if (password && password.length < 8) {
    return {ok: false, message: 'A senha deve ter pelo menos 8 caracteres.'};
  }

  const users = readAuthUsers_();
  const requestedId = String(input.id || '').trim();
  let user = requestedId ? users.find(item => item.id === requestedId) || null : null;
  const emailOwner = users.find(item => item.email === email && (!user || item.id !== user.id));
  if (emailOwner) return {ok: false, message: 'Este e-mail já está sendo usado por outro usuário.'};
  if (user && user.id === actor.id && (!active || role !== 'admin')) {
    return {
      ok: false,
      message: 'Você não pode desativar ou remover seu próprio acesso de administrador.'
    };
  }

  const sheet = getSheet_(AUTH_USERS_SHEET);
  const now = new Date().toISOString();
  if (!user) {
    if (password.length < 8) {
      return {ok: false, message: 'Defina uma senha inicial com pelo menos 8 caracteres.'};
    }
    const salt = Utilities.getUuid().replace(/-/g, '') + Utilities.getUuid().replace(/-/g, '');
    user = {
      id: Utilities.getUuid(),
      name: name,
      email: email,
      passwordHash: authPasswordHash_(password, salt),
      passwordSalt: salt,
      role: role,
      active: active,
      allCompanies: allCompanies,
      companyIds: companyIds,
      createdAt: now,
      updatedAt: now,
      lastLoginAt: ''
    };
    sheet.appendRow([
      user.id, user.name, user.email, user.passwordHash, user.passwordSalt,
      user.role, user.active, user.allCompanies, JSON.stringify(user.companyIds),
      now, now, ''
    ]);
    auditAuthEvent_(
      actor,
      'create_user',
      'user',
      user.id,
      '',
      actor.sessionDeviceId,
      actor.sessionPlatform,
      {email: user.email, role: user.role}
    );
  } else {
    user.name = name;
    user.email = email;
    user.role = role;
    user.active = active;
    user.allCompanies = allCompanies;
    user.companyIds = companyIds;
    user.updatedAt = now;
    if (password) {
      user.passwordSalt =
        Utilities.getUuid().replace(/-/g, '') + Utilities.getUuid().replace(/-/g, '');
      user.passwordHash = authPasswordHash_(password, user.passwordSalt);
    }
    sheet.getRange(user.rowNumber, 1, 1, 12).setValues([[
      user.id, user.name, user.email, user.passwordHash, user.passwordSalt,
      user.role, user.active, user.allCompanies, JSON.stringify(user.companyIds),
      user.createdAt, now, user.lastLoginAt
    ]]);
    auditAuthEvent_(
      actor,
      'update_user',
      'user',
      user.id,
      '',
      actor.sessionDeviceId,
      actor.sessionPlatform,
      {email: user.email, role: user.role, active: user.active}
    );
  }
  return {ok: true, user: authPublicUser_(user)};
}

function auditAuthEvent_(user, action, entityType, entityId, companyId, deviceId, platform, details) {
  if (!user) return;
  try {
    ensureAuthStorage_();
    const text = JSON.stringify(details || {});
    getSheet_(AUTH_AUDIT_SHEET).appendRow([
      new Date().toISOString(),
      user.id,
      user.email,
      String(action || ''),
      String(entityType || ''),
      String(entityId || ''),
      String(companyId || ''),
      String(deviceId || user.sessionDeviceId || ''),
      String(platform || user.sessionPlatform || ''),
      text.length > 12000 ? text.substring(0, 12000) : text
    ]);
  } catch (error) {
    console.error('Falha ao registrar auditoria de usuário: ' + error);
  }
}

function pushDeviceChangesMultiUser_(request) {
  const deviceId = String(request.deviceId || '').trim();
  const platform = String(request.platform || '').trim().toLowerCase();
  const changes = Array.isArray(request.changes) ? request.changes : [];
  const user = request.__authUser || null;
  if (!user) return {ok: false, code: 'AUTH_REQUIRED', message: 'Faça login novamente.'};
  if (!deviceId) return {ok: false, message: 'Dispositivo não identificado.'};
  if (platform !== 'android' && platform !== 'windows') {
    return {ok: false, message: 'Plataforma de sincronização inválida.'};
  }
  if (changes.length > 250) {
    return {ok: false, message: 'Envie no máximo 250 alterações por lote.'};
  }

  ensureAuthStorage_();
  const allowed = DEVICE_SYNC_MASTER_TABLES.concat(DEVICE_SYNC_FIELD_TABLES);
  const globalTables = ['checklist_templates', 'checklist_items'];
  const prepared = changes.map(change => {
    const table = String((change && change.table) || '').trim();
    const recordId = String((change && change.id) || '').trim();
    const deleted = Boolean(change && change.deleted);
    let companyId = String((change && change.companyId) || '').trim();
    const rawPayload = (change && change.payload) || {};
    if (!companyId && rawPayload && rawPayload.company_id) {
      companyId = String(rawPayload.company_id || '').trim();
    }
    if (allowed.indexOf(table) < 0 || !recordId || recordId.length > 200) {
      throw new Error('Alteração não permitida: ' + table + '.');
    }
    if (companyId && !userCanAccessCompany_(user, companyId)) {
      throw new Error('Acesso negado à empresa do registro ' + table + '/' + recordId + '.');
    }
    if (!companyId && !deleted && globalTables.indexOf(table) < 0) {
      throw new Error('Não foi possível identificar a empresa do registro ' + table + '/' + recordId + '.');
    }
    const payload = deleted ? '' : JSON.stringify(rawPayload);
    if (!deleted && payload.length > 45000) {
      throw new Error('O registro ' + table + '/' + recordId + ' é grande demais para sincronizar.');
    }
    return {
      table: table,
      recordId: recordId,
      deleted: deleted,
      payload: payload,
      companyId: companyId
    };
  });

  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const sheet = getSheet_(DEVICE_SYNC_SHEET);
    const lastRow = sheet.getLastRow();
    const existing = lastRow >= 2
      ? sheet.getRange(2, 1, lastRow - 1, 10).getValues()
      : [];
    const rowByKey = {};
    const valueByKey = {};
    let maxStoredVersion = 0;
    existing.forEach((row, index) => {
      const key = String(row[0]) + '\n' + String(row[1]);
      rowByKey[key] = index + 2;
      valueByKey[key] = row;
      maxStoredVersion = Math.max(maxStoredVersion, Number(row[3]) || 0);
    });

    const props = PropertiesService.getScriptProperties();
    let version = Math.max(
      Number(props.getProperty(DEVICE_SYNC_VERSION_PROPERTY)) || 0,
      maxStoredVersion
    );
    const newRows = [];
    prepared.forEach(change => {
      version += 1;
      const key = change.table + '\n' + change.recordId;
      const current = valueByKey[key];
      let companyId = change.companyId;
      if (!companyId && current) {
        companyId = String(
          current[8] || syncCompanyIdForRow_(current, existing, {})
        ).trim();
      }
      if (companyId && !userCanAccessCompany_(user, companyId)) {
        throw new Error(
          'Acesso negado à empresa do registro ' + change.table + '/' + change.recordId + '.'
        );
      }

      const pcOwnsMaster =
        platform === 'android' &&
        DEVICE_SYNC_MASTER_TABLES.indexOf(change.table) >= 0 &&
        current &&
        String(current[5] || '').toLowerCase() === 'windows';
      const values = pcOwnsMaster
        ? [
            current[0], current[1], current[2], version,
            current[4], current[5], new Date().toISOString(), current[7],
            companyId || String(current[8] || ''), String(current[9] || '')
          ]
        : [
            change.table,
            change.recordId,
            change.deleted,
            version,
            deviceId,
            platform,
            new Date().toISOString(),
            change.payload,
            companyId,
            user.id
          ];
      const rowNumber = rowByKey[key];
      if (rowNumber) {
        sheet.getRange(rowNumber, 1, 1, values.length).setValues([values]);
        valueByKey[key] = values;
      } else {
        newRows.push(values);
        rowByKey[key] = lastRow + newRows.length;
        valueByKey[key] = values;
      }
    });
    if (newRows.length) {
      sheet.getRange(sheet.getLastRow() + 1, 1, newRows.length, 10).setValues(newRows);
    }
    props.setProperty(DEVICE_SYNC_VERSION_PROPERTY, String(version));

    if (prepared.length) {
      auditAuthEvent_(
        user,
        'device_sync_push',
        'batch',
        '',
        '',
        deviceId,
        platform,
        {
          accepted: prepared.length,
          tables: prepared.reduce((acc, item) => {
            acc[item.table] = (acc[item.table] || 0) + 1;
            return acc;
          }, {})
        }
      );
    }
    return {
      ok: true,
      accepted: prepared.length,
      version: version,
      message: 'Alterações recebidas.'
    };
  } finally {
    lock.releaseLock();
  }
}

function pullDeviceChangesMultiUser_(request) {
  const deviceId = String(request.deviceId || '').trim();
  const user = request.__authUser || null;
  if (!user) return {ok: false, code: 'AUTH_REQUIRED', message: 'Faça login novamente.'};
  if (!deviceId) return {ok: false, message: 'Dispositivo não identificado.'};

  ensureAuthStorage_();
  const sheet = getSheet_(DEVICE_SYNC_SHEET);
  const lastRow = sheet.getLastRow();
  const rows = lastRow >= 2
    ? sheet.getRange(2, 1, lastRow - 1, 10).getValues()
    : [];
  const props = PropertiesService.getScriptProperties();
  const storedVersion = Number(props.getProperty(DEVICE_SYNC_VERSION_PROPERTY)) || 0;
  const maxRowVersion = rows.reduce(
    (current, row) => Math.max(current, Number(row[3]) || 0),
    0
  );
  const currentVersion = Math.max(storedVersion, maxRowVersion);
  let since = Math.max(0, Number(request.sinceVersion) || 0);
  if (since > currentVersion) since = 0;
  const limit = Math.max(1, Math.min(500, Number(request.limit) || 300));

  const pending = rows
    .filter(row => (Number(row[3]) || 0) > since)
    .sort((a, b) => (Number(a[3]) || 0) - (Number(b[3]) || 0));

  const scopeCache = {};
  const selected = [];
  let scannedVersion = since;
  for (let i = 0; i < pending.length; i++) {
    const row = pending[i];
    scannedVersion = Number(row[3]) || scannedVersion;
    const companyId = String(
      row[8] || syncCompanyIdForRow_(row, rows, scopeCache)
    ).trim();
    if (!companyId || userCanAccessCompany_(user, companyId)) {
      selected.push({row: row, companyId: companyId});
      if (selected.length >= limit) break;
    }
  }

  const changes = selected.map(item => {
    const row = item.row;
    const deleted = row[2] === true || String(row[2]).toLowerCase() === 'true';
    let payload = null;
    if (!deleted) {
      try {
        payload = JSON.parse(String(row[7] || '{}'));
      } catch (_) {
        payload = {};
      }
    }
    return {
      table: String(row[0] || ''),
      id: String(row[1] || ''),
      deleted: deleted,
      serverVersion: Number(row[3]) || 0,
      sourceDevice: String(row[4] || ''),
      sourcePlatform: String(row[5] || ''),
      updatedAt: String(row[6] || ''),
      payload: payload,
      companyId: item.companyId,
      updatedByUser: String(row[9] || '')
    };
  });

  if (!pending.length) scannedVersion = currentVersion;
  else if (scannedVersion < currentVersion && selected.length < limit) {
    scannedVersion = currentVersion;
  }
  const hasMore = pending.some(row => (Number(row[3]) || 0) > scannedVersion);
  return {
    ok: true,
    version: currentVersion,
    nextVersion: scannedVersion,
    hasMore: hasMore,
    changes: changes
  };
}

function syncCompanyIdForRow_(row, rows, cache) {
  const table = String(row[0] || '');
  const recordId = String(row[1] || '');
  const key = table + '\n' + recordId;
  if (Object.prototype.hasOwnProperty.call(cache, key)) return cache[key];

  const directStored = String(row[8] || '').trim();
  if (directStored) return (cache[key] = directStored);
  if (table === 'companies') return (cache[key] = recordId);

  let payload = {};
  try {
    payload = JSON.parse(String(row[7] || '{}'));
  } catch (_) {}
  const direct = String(payload.company_id || '').trim();
  if (direct) return (cache[key] = direct);

  const findScope = (refTable, refId) => {
    const id = String(refId || '').trim();
    if (!id) return '';
    const target = rows.find(
      candidate =>
        String(candidate[0] || '') === refTable &&
        String(candidate[1] || '') === id
    );
    return target ? syncCompanyIdForRow_(target, rows, cache) : '';
  };

  let resolved = '';
  if (table === 'training_controls') {
    resolved = findScope('workers', payload.worker_id);
  } else if (table === 'cipa_candidates' || table === 'cipa_voters') {
    resolved = findScope('cipa_elections', payload.election_id);
  } else if (
    table === 'answers' ||
    table === 'non_conformities' ||
    table === 'action_plans'
  ) {
    resolved = findScope('inspections', payload.inspection_id);
  }
  cache[key] = resolved;
  return resolved;
}

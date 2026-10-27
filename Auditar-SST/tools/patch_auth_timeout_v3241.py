#!/usr/bin/env python3
"""Hotfix v3.24.1: reduzir latência da autenticação da Central Online."""
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
path = root / 'painel_web_google_apps_script' / 'MultiUser.gs'
text = path.read_text(encoding='utf-8')

def replace_once(old, new, label):
    global text
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f'Marcador não encontrado: {label}')
    text = text.replace(old, new, 1)

replace_once("function ensureAuthStorage_() {\n  const spreadsheetId = PropertiesService.getScriptProperties().getProperty('AUDITAR_SPREADSHEET_ID');\n  if (!spreadsheetId) throw new Error('Execute setupAuditar() primeiro.');\n  const ss = SpreadsheetApp.openById(spreadsheetId);\n  setupAuthStorage_(ss);\n  return ss;\n}\n", "function ensureAuthStorage_() {\n  const spreadsheetId = PropertiesService.getScriptProperties().getProperty('AUDITAR_SPREADSHEET_ID');\n  if (!spreadsheetId) throw new Error('Execute setupAuditar() primeiro.');\n  const ss = SpreadsheetApp.openById(spreadsheetId);\n\n  // Não regrava cabeçalhos/congelamento a cada login/status. Isso deixava\n  // a Central Online lenta e podia estourar o timeout de 30 s no app.\n  const requiredSheets = [\n    AUTH_USERS_SHEET,\n    AUTH_SESSIONS_SHEET,\n    AUTH_AUDIT_SHEET,\n    DEVICE_SYNC_SHEET\n  ];\n  const missingStorage = requiredSheets.some(name => !ss.getSheetByName(name));\n  if (missingStorage) setupAuthStorage_(ss);\n  return ss;\n}\n\nfunction authSheet_(ss, name) {\n  const sheet = ss.getSheetByName(name);\n  if (!sheet) throw new Error('Armazenamento de autenticação incompleto: ' + name + '.');\n  return sheet;\n}\n", 'ensureAuthStorage leve')
replace_once("function authStatus_() {\n  const spreadsheetId = String(\n    PropertiesService.getScriptProperties().getProperty('AUDITAR_SPREADSHEET_ID') || ''\n  ).trim();\n  if (!spreadsheetId) return {ok: true, configured: false, hasUsers: false};\n  ensureAuthStorage_();\n  return {ok: true, configured: true, hasUsers: readAuthUsers_().length > 0};\n}\n\nfunction readAuthUsers_() {\n  ensureAuthStorage_();\n  const sheet = getSheet_(AUTH_USERS_SHEET);\n", "function authStatus_() {\n  const spreadsheetId = String(\n    PropertiesService.getScriptProperties().getProperty('AUDITAR_SPREADSHEET_ID') || ''\n  ).trim();\n  if (!spreadsheetId) return {ok: true, configured: false, hasUsers: false};\n\n  // Caminho leve: abre a planilha uma única vez e só consulta a aba Usuários.\n  const ss = ensureAuthStorage_();\n  const sheet = authSheet_(ss, AUTH_USERS_SHEET);\n  return {ok: true, configured: true, hasUsers: sheet.getLastRow() > 1};\n}\n\nfunction readAuthUsers_(existingSs) {\n  const ss = existingSs || ensureAuthStorage_();\n  const sheet = authSheet_(ss, AUTH_USERS_SHEET);\n", 'auth status/read users')
replace_once("function authBootstrapAdmin_(request) {\n  ensureAuthStorage_();\n  if (readAuthUsers_().length > 0) {\n", "function authBootstrapAdmin_(request) {\n  const ss = ensureAuthStorage_();\n  if (readAuthUsers_(ss).length > 0) {\n", 'bootstrap abre uma vez')
replace_once("  getSheet_(AUTH_USERS_SHEET).appendRow([\n", "  authSheet_(ss, AUTH_USERS_SHEET).appendRow([\n", 'bootstrap users sheet')
replace_once("  const session = authCreateSession_(user, request);\n", "  const session = authCreateSession_(user, request, ss);\n", 'bootstrap session')
replace_once("    request.platform,\n    {}\n  );\n  return {ok: true, user: authPublicUser_(user), sessionToken: session.token};\n}\n\nfunction authLogin_(request) {\n", "    request.platform,\n    {},\n    ss\n  );\n  return {ok: true, user: authPublicUser_(user), sessionToken: session.token};\n}\n\nfunction authLogin_(request) {\n", 'bootstrap audit')
replace_once("function authLogin_(request) {\n  const email = normalizeAuthEmail_(request.email);\n  const password = String(request.password || '');\n  const users = readAuthUsers_();\n", "function authLogin_(request) {\n  const email = normalizeAuthEmail_(request.email);\n  const password = String(request.password || '');\n  const ss = ensureAuthStorage_();\n  const users = readAuthUsers_(ss);\n", 'login abre uma vez')
replace_once("  const userSheet = getSheet_(AUTH_USERS_SHEET);\n", "  const userSheet = authSheet_(ss, AUTH_USERS_SHEET);\n", 'login user sheet')
replace_once("  const session = authCreateSession_(user, request);\n", "  const session = authCreateSession_(user, request, ss);\n", 'login session')
replace_once("    request.platform,\n    {}\n  );\n  return {ok: true, user: authPublicUser_(user), sessionToken: session.token};\n}\n\nfunction authCreateSession_(user, request) {\n  ensureAuthStorage_();\n", "    request.platform,\n    {},\n    ss\n  );\n  return {ok: true, user: authPublicUser_(user), sessionToken: session.token};\n}\n\nfunction authCreateSession_(user, request, existingSs) {\n  const ss = existingSs || ensureAuthStorage_();\n", 'login audit/create session')
replace_once("  getSheet_(AUTH_SESSIONS_SHEET).appendRow([\n", "  authSheet_(ss, AUTH_SESSIONS_SHEET).appendRow([\n", 'session sheet')
replace_once("function authUserFromToken_(token, touch) {\n  const clean = String(token || '').trim();\n  if (!clean) return null;\n  ensureAuthStorage_();\n  const sheet = getSheet_(AUTH_SESSIONS_SHEET);\n", "function authUserFromToken_(token, touch) {\n  const clean = String(token || '').trim();\n  if (!clean) return null;\n  const ss = ensureAuthStorage_();\n  const sheet = authSheet_(ss, AUTH_SESSIONS_SHEET);\n", 'token session sheet')
replace_once("  const user = readAuthUsers_().find(item => item.id === userId && item.active);\n", "  const user = readAuthUsers_(ss).find(item => item.id === userId && item.active);\n", 'token users same spreadsheet')
replace_once("function authLogout_(request) {\n  const token = String(request.authToken || '').trim();\n  if (!token) return {ok: true};\n  ensureAuthStorage_();\n  const sheet = getSheet_(AUTH_SESSIONS_SHEET);\n", "function authLogout_(request) {\n  const token = String(request.authToken || '').trim();\n  if (!token) return {ok: true};\n  const ss = ensureAuthStorage_();\n  const sheet = authSheet_(ss, AUTH_SESSIONS_SHEET);\n", 'logout sheet')
replace_once("function auditAuthEvent_(user, action, entityType, entityId, companyId, deviceId, platform, details) {\n  if (!user) return;\n  try {\n    ensureAuthStorage_();\n    const text = JSON.stringify(details || {});\n    getSheet_(AUTH_AUDIT_SHEET).appendRow([\n", "function auditAuthEvent_(user, action, entityType, entityId, companyId, deviceId, platform, details, existingSs) {\n  if (!user) return;\n  try {\n    const ss = existingSs || ensureAuthStorage_();\n    const text = JSON.stringify(details || {});\n    authSheet_(ss, AUTH_AUDIT_SHEET).appendRow([\n", 'audit sheet')

path.write_text(text, encoding='utf-8')
assert 'hasUsers: sheet.getLastRow() > 1' in text
assert 'function authCreateSession_(user, request, existingSs)' in text
print('Hotfix de timeout da autenticação aplicado.')

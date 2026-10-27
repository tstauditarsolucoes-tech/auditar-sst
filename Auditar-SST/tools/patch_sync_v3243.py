#!/usr/bin/env python3
"""Auditar SST v3.24.3: sincronização mais confiável entre celular e PC."""
from pathlib import Path
import re, sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')

def read(rel):
    return (root / rel).read_text(encoding='utf-8')

def write(rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')

def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Marcador não encontrado: {label}')
    return text.replace(old, new, 1)

# Versão
pub = read('pubspec.yaml')
pub = re.sub(r'^version:\s*\d+\.\d+\.\d+\+\d+\s*$', 'version: 3.24.3+103', pub, flags=re.M)
write('pubspec.yaml', pub)

# 1) Auth: quando permissões mudam, força full pull para não perder dados antigos
# da empresa recém-liberada. Também expõe um fingerprint estável do escopo.
auth = read('lib/services/auth_service.dart')
marker = """  static bool canAccessCompany(String companyId) {\n    final user = _currentUser;\n    if (user == null || !user.active) return false;\n    if (user.isAdmin || user.allCompanies) return true;\n    return user.companyIds.contains(companyId);\n  }\n"""
insert = marker + """\n  static String _scopeFingerprint(AuditarUser? user) {\n    if (user == null) return '';\n    final companies = [...user.companyIds]..sort();\n    return [\n      user.id,\n      user.active ? '1' : '0',\n      user.role.toLowerCase(),\n      user.allCompanies ? 'ALL' : companies.join(','),\n    ].join('|');\n  }\n"""
auth = replace_once(auth, marker, insert, 'fingerprint de permissões')
old_verify = r'''  static Future<bool> verifySession() async {
    if (!isSignedIn) return false;
    try {
      final result = await _post({
        'action': 'auth_session',
        'authToken': _sessionToken,
        'deviceId': await deviceId(),
        'platform': Platform.isWindows ? 'windows' : 'android',
      });
      final rawUser = result['user'];
      if (rawUser is Map) {
        _currentUser = AuditarUser.fromMap(Map<String, dynamic>.from(rawUser));
        await _writeIdentitySettings();
        await _persist();
      }
      return true;
    } catch (_) {
      return false;
    }
  }
'''
new_verify = r'''  static Future<bool> verifySession() async {
    if (!isSignedIn) return false;
    final oldScope = _scopeFingerprint(_currentUser);
    try {
      final result = await _post({
        'action': 'auth_session',
        'authToken': _sessionToken,
        'deviceId': await deviceId(),
        'platform': Platform.isWindows ? 'windows' : 'android',
      });
      final rawUser = result['user'];
      if (rawUser is Map) {
        final refreshed = AuditarUser.fromMap(Map<String, dynamic>.from(rawUser));
        _currentUser = refreshed;
        await _writeIdentitySettings();
        await _persist();

        // Se o administrador liberou/retirou empresas ou mudou o perfil,
        // reinicia o cursor. Assim, empresas recém-liberadas recebem também
        // os registros históricos que já existiam antes da permissão.
        if (_scopeFingerprint(refreshed) != oldScope) {
          await AppDatabase.instance.setSetting('device_sync_server_version', '0');
          await AppDatabase.instance.setSetting(
            'last_device_sync_status',
            'Permissões atualizadas • sincronização completa pendente',
          );
        }
      }
      return true;
    } catch (_) {
      return false;
    }
  }
'''
auth = replace_once(auth, old_verify, new_verify, 'refresh de sessão com full resync')
write('lib/services/auth_service.dart', auth)

# 2) DeviceSync: usa o MESMO deviceId da sessão de login, valida ACK do push e
# impede paginação travada de ser tratada como sucesso.
sync = read('lib/services/device_sync_service.dart')
sync = sync.replace("import 'package:uuid/uuid.dart';\n", '')
sync = sync.replace("  static const _deviceIdSetting = 'device_sync_id';\n", '')
sync = replace_once(
    sync,
    "      final deviceId = await _deviceId(appDb);\n",
    "      final deviceId = await AuthService.deviceId();\n",
    'device id unificado',
)
old_push = r'''        await _post(uri, {
          'action': 'device_sync_push',
          'syncKey': syncKey,
          'authToken': AuthService.sessionToken,
          'deviceId': deviceId,
          'platform': isWindows ? 'windows' : 'android',
          'changes': changes,
        });
        await _acknowledgeChanges(db, changes);
        sent += changes.length;
'''
new_push = r'''        final pushResponse = await _post(uri, {
          'action': 'device_sync_push',
          'syncKey': syncKey,
          'authToken': AuthService.sessionToken,
          'deviceId': deviceId,
          'platform': isWindows ? 'windows' : 'android',
          'changes': changes,
        });
        if (pushResponse.containsKey('accepted')) {
          final accepted = _asInt(pushResponse['accepted']);
          if (accepted != changes.length) {
            throw StateError(
              'A Central Online confirmou $accepted de ${changes.length} alterações. '
              'Nada foi marcado como enviado para evitar perda de dados.',
            );
          }
        }
        await _acknowledgeChanges(db, changes);
        sent += changes.length;
'''
sync = replace_once(sync, old_push, new_push, 'ack seguro do push')
old_loop_tail = r'''        if (response['hasMore'] != true) break;
      }

      final now = DateTime.now().toUtc().toIso8601String();
'''
new_loop_tail = r'''        if (response['hasMore'] == true && savedVersion <= since) {
          throw StateError(
            'A Central Online informou mais dados, mas não avançou a versão. '
            'A sincronização foi interrompida para evitar repetição infinita.',
          );
        }
        if (response['hasMore'] != true) break;
      }

      final now = DateTime.now().toUtc().toIso8601String();
'''
sync = replace_once(sync, old_loop_tail, new_loop_tail, 'proteção de paginação')
sync = re.sub(
    r"\n  static Future<String> _deviceId\(AppDatabase db\) async \{.*?\n  \}\n\n  static Future<void> _ensureChangeTracking",
    "\n  static Future<void> _ensureChangeTracking",
    sync,
    count=1,
    flags=re.S,
)
write('lib/services/device_sync_service.dart', sync)

# 3) Coordenador: atualiza permissões/sessão no ciclo de manutenção e no resume,
# antes do sync completo. O ciclo de 20 s continua leve.
coord = read('lib/services/sync_coordinator.dart')
old_try = r'''    try {
      DeviceSyncResult? result;
      try {
        result = await DeviceSyncService.synchronize();
'''
new_try = r'''    try {
      if (!deviceOnly) {
        // Atualiza perfil/permissões sem bloquear o uso offline. Se a central
        // estiver momentaneamente indisponível, o sync normal ainda tenta com
        // a sessão já salva e mantém os dados locais intactos.
        try {
          await AuthService.verifySession().timeout(const Duration(seconds: 20));
        } catch (_) {}
      }

      DeviceSyncResult? result;
      try {
        result = await DeviceSyncService.synchronize();
'''
coord = replace_once(coord, old_try, new_try, 'refresh periódico de sessão')
write('lib/services/sync_coordinator.dart', coord)

# 4) Backend: reutiliza a mesma planilha já aberta no push/pull para reduzir
# latência e quantidade de chamadas ao SpreadsheetApp.
mu = read('painel_web_google_apps_script/MultiUser.gs')
mu = replace_once(
    mu,
    "  ensureAuthStorage_();\n  const allowed = DEVICE_SYNC_MASTER_TABLES.concat(DEVICE_SYNC_FIELD_TABLES);\n",
    "  const ss = ensureAuthStorage_();\n  const allowed = DEVICE_SYNC_MASTER_TABLES.concat(DEVICE_SYNC_FIELD_TABLES);\n",
    'push abre planilha uma vez',
)
mu = replace_once(
    mu,
    "    const sheet = getSheet_(DEVICE_SYNC_SHEET);\n",
    "    const sheet = authSheet_(ss, DEVICE_SYNC_SHEET);\n",
    'push reutiliza planilha',
)
mu = replace_once(
    mu,
    "  ensureAuthStorage_();\n  const sheet = getSheet_(DEVICE_SYNC_SHEET);\n  const lastRow = sheet.getLastRow();\n",
    "  const ss = ensureAuthStorage_();\n  const sheet = authSheet_(ss, DEVICE_SYNC_SHEET);\n  const lastRow = sheet.getLastRow();\n",
    'pull abre planilha uma vez',
)
write('painel_web_google_apps_script/MultiUser.gs', mu)

# 5) Reforça o teste E2E: o deviceId da sessão deve ser exatamente o mesmo
# usado no push/pull, evitando auditoria inconsistente entre login e sync.
test = read('test/device_sync_roundtrip_test.dart')
test = replace_once(
    test,
    "  final Set<String> authTokensSeen = <String>{};\n  int _version = 0;\n",
    "  final Set<String> authTokensSeen = <String>{};\n  final Set<String> deviceIdsSeen = <String>{};\n  int _version = 0;\n",
    'captura device id no teste',
)
test = replace_once(
    test,
    "        final authToken = '${payload['authToken'] ?? ''}'.trim();\n        if (authToken.isNotEmpty) authTokensSeen.add(authToken);\n",
    "        final authToken = '${payload['authToken'] ?? ''}'.trim();\n        if (authToken.isNotEmpty) authTokensSeen.add(authToken);\n        final deviceId = '${payload['deviceId'] ?? ''}'.trim();\n        if (deviceId.isNotEmpty) deviceIdsSeen.add(deviceId);\n",
    'registra device id no servidor fake',
)
test = replace_once(
    test,
    "      expect(central.authTokensSeen, contains('token-phone'));\n      expect(central.authTokensSeen, contains('token-pc'));\n",
    "      expect(central.authTokensSeen, contains('token-phone'));\n      expect(central.authTokensSeen, contains('token-pc'));\n      expect(central.deviceIdsSeen, contains('phone-device'));\n      expect(central.deviceIdsSeen, contains('pc-device'));\n",
    'valida device id unificado',
)
write('test/device_sync_roundtrip_test.dart', test)

write('MUDANCAS_V3_24_3_SINCRONIZACAO.txt', '''AUDITAR SST v3.24.3 — SINCRONIZAÇÃO\n\n- Unifica o identificador do dispositivo entre login, auditoria e sincronização.\n- Atualiza permissões automaticamente no ciclo de manutenção e ao retomar o app.\n- Quando o acesso a empresas muda, reinicia o cursor e faz sincronização completa para trazer histórico.\n- Só confirma alterações locais como enviadas quando a Central confirma o lote completo.\n- Detecta paginação sem avanço para evitar repetição infinita.\n- Reduz chamadas repetidas ao SpreadsheetApp no push/pull.\n- Reforça o teste automatizado celular <-> PC com validação do deviceId.\n\nObservação: arquivos físicos como fotos/assinaturas continuam fora da sincronização estruturada e usam fluxos próprios.\n''')

assert 'version: 3.24.3+103' in read('pubspec.yaml')
assert 'final deviceId = await AuthService.deviceId();' in read('lib/services/device_sync_service.dart')
assert '_scopeFingerprint(refreshed) != oldScope' in read('lib/services/auth_service.dart')
assert 'AuthService.verifySession().timeout' in read('lib/services/sync_coordinator.dart')
print('Auditar SST v3.24.3: correções de sincronização aplicadas.')

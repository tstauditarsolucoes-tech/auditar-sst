#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')


def read(rel):
    return (root / rel).read_text(encoding='utf-8')


def write(rel, text):
    (root / rel).write_text(text, encoding='utf-8')


def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Marcador não encontrado: {label}')
    return text.replace(old, new, 1)


pub = read('pubspec.yaml')
pub = re.sub(r'^version:\s*\d+\.\d+\.\d+\+\d+\s*$', 'version: 3.23.0+90', pub, flags=re.M)
write('pubspec.yaml', pub)

db = read('lib/database.dart')
if "import 'dart:io';" not in db:
    db = "import 'dart:io';\n\n" + db
old = """class AppDatabase {\n  AppDatabase._();\n  static final AppDatabase instance = AppDatabase._();\n\n  Database? _db;\n\n  Future<String> get databaseFilePath async {\n    final dbPath = await getDatabasesPath();\n    return join(dbPath, 'auditar_sst.db');\n  }\n"""
new = """class AppDatabase {\n  AppDatabase._();\n  static final AppDatabase instance = AppDatabase._();\n\n  static String _activeUserId = '';\n  Database? _db;\n\n  static String get activeUserId => _activeUserId;\n\n  static String _safeUserId(String value) {\n    final cleaned = value.trim().replaceAll(RegExp(r'[^A-Za-z0-9_-]'), '_');\n    return cleaned.length <= 80 ? cleaned : cleaned.substring(0, 80);\n  }\n\n  static Future<void> activateUser(\n    String userId, {\n    bool migrateLegacy = false,\n  }) async {\n    final safe = _safeUserId(userId);\n    if (safe.isEmpty) throw StateError('Usuário inválido para o banco local.');\n    if (_activeUserId == safe && instance._db != null) return;\n    await instance.closeForFileOperation();\n    _activeUserId = safe;\n    if (migrateLegacy) {\n      await _migrateLegacyDatabaseIfNeeded(safe);\n    }\n  }\n\n  static Future<void> deactivateUser() async {\n    await instance.closeForFileOperation();\n    _activeUserId = '';\n  }\n\n  static Future<void> _migrateLegacyDatabaseIfNeeded(String safeUserId) async {\n    final dbPath = await getDatabasesPath();\n    final legacyPath = join(dbPath, 'auditar_sst.db');\n    final targetPath = join(dbPath, 'auditar_sst_$safeUserId.db');\n    final legacy = File(legacyPath);\n    final target = File(targetPath);\n    if (await target.exists() || !await legacy.exists()) return;\n\n    try {\n      final legacyDb = await databaseFactory.openDatabase(legacyPath);\n      try {\n        await legacyDb.rawQuery('PRAGMA wal_checkpoint(FULL)');\n      } catch (_) {}\n      await legacyDb.close();\n    } catch (_) {}\n\n    await legacy.copy(targetPath);\n  }\n\n  Future<String> get databaseFilePath async {\n    final dbPath = await getDatabasesPath();\n    final fileName = _activeUserId.isEmpty\n        ? 'auditar_sst.db'\n        : 'auditar_sst_$_activeUserId.db';\n    return join(dbPath, fileName);\n  }\n"""
if "static String _activeUserId = '';" not in db:
    db = replace_once(db, old, new, 'AppDatabase multiusuário')
write('lib/database.dart', db)

main = read('lib/main.dart')
if "import 'services/auth_service.dart';" not in main:
    main = main.replace("import 'services/sync_coordinator.dart';\n", "import 'services/auth_service.dart';\nimport 'services/sync_coordinator.dart';\n", 1)
main = main.replace("import 'services/web_service_config.dart';\n", '')
old = """  await WebServiceConfig.applyEmbeddedConfiguration();\n  runApp(const AuditarSstApp());\n"""
new = """  await AuthService.initialize();\n  if (AuthService.isSignedIn) {\n    await AuthService.activateSavedSession();\n  }\n  runApp(const AuditarSstApp());\n"""
if 'await AuthService.initialize();' not in main:
    main = replace_once(main, old, new, 'inicialização AuthService')
write('lib/main.dart', main)

splash = read('lib/screens/splash_screen.dart')
if "import '../services/auth_service.dart';" not in splash:
    splash = splash.replace("import '../brand.dart';\n", "import '../brand.dart';\nimport '../services/auth_service.dart';\n", 1)
if "import 'login_screen.dart';" not in splash:
    splash = splash.replace("import 'home_screen.dart';\n", "import 'home_screen.dart';\nimport 'login_screen.dart';\n", 1)
old = "MaterialPageRoute(builder: (_) => const HomeScreen()),"
new = """MaterialPageRoute(\n          builder: (_) => AuthService.isSignedIn\n              ? const HomeScreen()\n              : const LoginScreen(),\n        ),"""
if 'AuthService.isSignedIn' not in splash:
    splash = replace_once(splash, old, new, 'rota do splash')
write('lib/screens/splash_screen.dart', splash)

settings = read('lib/screens/settings_screen.dart')
if "import '../services/auth_service.dart';" not in settings:
    settings = settings.replace("import '../database.dart';\n", "import '../database.dart';\nimport '../services/auth_service.dart';\n", 1)
if "import 'login_screen.dart';" not in settings:
    marker = "import '../services/web_service_config.dart';\n"
    settings = settings.replace(marker, marker + "import 'login_screen.dart';\nimport 'users_screen.dart';\n", 1)
logout_method = """  Future<void> _logout() async {\n    final confirm = await showDialog<bool>(\n      context: context,\n      builder: (context) => AlertDialog(\n        title: const Text('Sair desta conta?'),\n        content: const Text(\n          'Os dados desta conta permanecem salvos neste aparelho. Para abrir outra conta, será necessário entrar com o e-mail e a senha dela.',\n        ),\n        actions: [\n          TextButton(\n            onPressed: () => Navigator.pop(context, false),\n            child: const Text('Cancelar'),\n          ),\n          FilledButton(\n            onPressed: () => Navigator.pop(context, true),\n            child: const Text('Sair'),\n          ),\n        ],\n      ),\n    );\n    if (confirm != true) return;\n    await AuthService.logout();\n    if (!mounted) return;\n    Navigator.of(context).pushAndRemoveUntil(\n      MaterialPageRoute(builder: (_) => const LoginScreen()),\n      (_) => false,\n    );\n  }\n\n"""
if 'Future<void> _logout() async' not in settings:
    settings = settings.replace('  @override\n  Widget build(BuildContext context) {\n', logout_method + '  @override\n  Widget build(BuildContext context) {\n', 1)
account_block = """        children: [\n          Text(\n            'Conta e acesso',\n            style: Theme.of(context)\n                .textTheme\n                .titleMedium\n                ?.copyWith(fontWeight: FontWeight.bold),\n          ),\n          const SizedBox(height: 8),\n          Card(\n            child: Padding(\n              padding: const EdgeInsets.all(14),\n              child: Column(\n                crossAxisAlignment: CrossAxisAlignment.start,\n                children: [\n                  Row(\n                    children: [\n                      CircleAvatar(\n                        child: Icon(AuthService.isAdmin\n                            ? Icons.admin_panel_settings_rounded\n                            : Icons.person_rounded),\n                      ),\n                      const SizedBox(width: 12),\n                      Expanded(\n                        child: Column(\n                          crossAxisAlignment: CrossAxisAlignment.start,\n                          children: [\n                            Text(\n                              AuthService.currentUser?.name ?? 'Usuário',\n                              style: const TextStyle(fontWeight: FontWeight.w800),\n                            ),\n                            Text(\n                              AuthService.currentUser?.email ?? '',\n                              style: const TextStyle(fontSize: 12.5, color: Colors.black54),\n                            ),\n                            Text(\n                              AuthService.isAdmin ? 'Administrador' : 'Técnico SST',\n                              style: const TextStyle(fontSize: 12.5, color: Colors.black54),\n                            ),\n                          ],\n                        ),\n                      ),\n                    ],\n                  ),\n                  if (AuthService.isAdmin) ...[\n                    const SizedBox(height: 12),\n                    FilledButton.icon(\n                      onPressed: () => Navigator.of(context).push(\n                        MaterialPageRoute(builder: (_) => const UsersScreen()),\n                      ),\n                      icon: const Icon(Icons.manage_accounts_rounded),\n                      label: const Text('Usuários e acessos'),\n                    ),\n                  ],\n                  const SizedBox(height: 8),\n                  OutlinedButton.icon(\n                    onPressed: _logout,\n                    icon: const Icon(Icons.logout_rounded),\n                    label: const Text('Sair da conta'),\n                  ),\n                ],\n              ),\n            ),\n          ),\n          const SizedBox(height: 28),\n          Text(\n            'Preferências',\n"""
if "'Conta e acesso'" not in settings:
    settings = replace_once(settings, """        children: [\n          Text(\n            'Preferências',\n""", account_block, 'bloco de conta nas configurações')
write('lib/screens/settings_screen.dart', settings)

service_files = [
    'lib/services/worker_import_service.dart',
    'lib/services/drive_service.dart',
    'lib/services/medical_import_service.dart',
    'lib/services/management_panel_service.dart',
    'lib/services/cipa_voting_service.dart',
    'lib/services/ai_assistant_service.dart',
]
for rel in service_files:
    text = read(rel)
    if "import 'auth_service.dart';" not in text:
        idx = text.find("import '../")
        if idx >= 0:
            text = text[:idx] + "import 'auth_service.dart';\n" + text[idx:]
        else:
            matches = list(re.finditer(r'^import .*?;\n', text, flags=re.M))
            if not matches:
                raise RuntimeError(f'Import marker não encontrado em {rel}')
            pos = matches[-1].end()
            text = text[:pos] + "import 'auth_service.dart';\n" + text[pos:]
    if "'authToken': AuthService.sessionToken," not in text:
        text = text.replace("'syncKey': syncKey,", "'syncKey': syncKey,\n          'authToken': AuthService.sessionToken,")
    write(rel, text)

sync = read('lib/services/device_sync_service.dart')
if "import 'auth_service.dart';" not in sync:
    sync = sync.replace("import 'apps_script_http.dart';\n", "import 'apps_script_http.dart';\nimport 'auth_service.dart';\n", 1)
old = """      final endpoint = (await appDb.getSetting(\n        'management_panel_endpoint',\n      ))\n          .trim();\n      final syncKey = (await appDb.getSetting(\n        'management_panel_sync_key',\n      ))\n          .trim();\n\n      if (endpoint.isEmpty || syncKey.isEmpty) {\n        throw StateError('A Central Online ainda não está configurada.');\n      }\n"""
new = """      if (!AuthService.isSignedIn || AuthService.sessionToken.isEmpty) {\n        throw StateError('Faça login para sincronizar este dispositivo.');\n      }\n\n      final endpoint = (await appDb.getSetting(\n        'management_panel_endpoint',\n      ))\n          .trim();\n      final syncKey = (await appDb.getSetting(\n        'management_panel_sync_key',\n      ))\n          .trim();\n\n      if (endpoint.isEmpty || syncKey.isEmpty) {\n        throw StateError('A Central Online ainda não está configurada.');\n      }\n"""
if 'Faça login para sincronizar este dispositivo.' not in sync:
    sync = replace_once(sync, old, new, 'auth no device sync')
if sync.count("'authToken': AuthService.sessionToken,") < 2:
    sync = sync.replace("'syncKey': syncKey,\n          'deviceId': deviceId,", "'syncKey': syncKey,\n          'authToken': AuthService.sessionToken,\n          'deviceId': deviceId,", 2)
changes_table = """    await db.execute(\n      'CREATE TABLE IF NOT EXISTS $_changesTable('\n      'table_name TEXT NOT NULL, '\n      'record_id TEXT NOT NULL, '\n      'local_version INTEGER NOT NULL DEFAULT 1, '\n      'dirty INTEGER NOT NULL DEFAULT 1, '\n      'deleted INTEGER NOT NULL DEFAULT 0, '\n      'PRIMARY KEY(table_name, record_id)'\n      ')',\n    );\n\n"""
scopes_table = changes_table + """    await db.execute(\n      'CREATE TABLE IF NOT EXISTS device_sync_scopes('\n      'table_name TEXT NOT NULL, '\n      'record_id TEXT NOT NULL, '\n      'company_id TEXT NOT NULL DEFAULT "", '\n      'PRIMARY KEY(table_name, record_id)'\n      ')',\n    );\n\n"""
if 'CREATE TABLE IF NOT EXISTS device_sync_scopes' not in sync:
    sync = replace_once(sync, changes_table, scopes_table, 'device_sync_scopes')
if 'static Future<String> _companyIdForRecord(' not in sync:
    start = sync.index('  static Future<List<Map<String, Object?>>> _pendingChanges(')
    end = sync.index('  static Future<void> _acknowledgeChanges(', start)
    new_pending = r'''  static Future<List<Map<String, Object?>>> _pendingChanges(
    Database db, {
    required int limit,
  }) async {
    final tables = _outboundTables.toList()..sort();
    final placeholders = List.filled(tables.length, '?').join(',');
    final rows = await db.query(
      _changesTable,
      where: 'dirty = 1 AND table_name IN ($placeholders)',
      whereArgs: tables,
      orderBy: 'table_name, record_id',
      limit: limit,
    );

    final result = <Map<String, Object?>>[];
    for (final metadata in rows) {
      final table = metadata['table_name'] as String;
      final recordId = metadata['record_id'] as String;
      var deleted = _asInt(metadata['deleted']) == 1;
      Map<String, Object?>? payload;

      if (!deleted) {
        final records = await db.query(
          table,
          where: 'id = ?',
          whereArgs: [recordId],
          limit: 1,
        );
        if (records.isEmpty) {
          deleted = true;
        } else {
          payload = Map<String, Object?>.from(records.first);
          for (final column in _localOnlyColumns[table] ?? const <String>{}) {
            payload.remove(column);
          }
        }
      }

      var companyId = await _companyIdForRecord(
        db,
        table: table,
        recordId: recordId,
        payload: payload,
      );
      if (companyId.isEmpty) {
        final scope = await db.query(
          'device_sync_scopes',
          columns: ['company_id'],
          where: 'table_name = ? AND record_id = ?',
          whereArgs: [table, recordId],
          limit: 1,
        );
        if (scope.isNotEmpty) companyId = '${scope.first['company_id'] ?? ''}';
      } else {
        await db.insert(
          'device_sync_scopes',
          {'table_name': table, 'record_id': recordId, 'company_id': companyId},
          conflictAlgorithm: ConflictAlgorithm.replace,
        );
      }

      result.add({
        'table': table,
        'id': recordId,
        'localVersion': _asInt(metadata['local_version']),
        'deleted': deleted,
        'companyId': companyId,
        if (payload != null) 'payload': payload,
      });
    }
    return result;
  }

  static Future<String> _companyIdForRecord(
    Database db, {
    required String table,
    required String recordId,
    Map<String, Object?>? payload,
  }) async {
    if (table == 'companies') return recordId;
    final direct = '${payload?['company_id'] ?? ''}'.trim();
    if (direct.isNotEmpty) return direct;

    Future<String> companyFrom(String sourceTable, String sourceId) async {
      if (sourceId.isEmpty) return '';
      final rows = await db.query(
        sourceTable,
        columns: sourceTable == 'companies' ? ['id'] : ['company_id'],
        where: 'id = ?',
        whereArgs: [sourceId],
        limit: 1,
      );
      if (rows.isEmpty) return '';
      return sourceTable == 'companies'
          ? '${rows.first['id'] ?? ''}'
          : '${rows.first['company_id'] ?? ''}';
    }

    if (table == 'training_controls') {
      return companyFrom('workers', '${payload?['worker_id'] ?? ''}');
    }
    if (table == 'cipa_candidates' || table == 'cipa_voters') {
      return companyFrom('cipa_elections', '${payload?['election_id'] ?? ''}');
    }
    if (table == 'answers' ||
        table == 'non_conformities' ||
        table == 'action_plans') {
      return companyFrom('inspections', '${payload?['inspection_id'] ?? ''}');
    }
    return '';
  }

'''
    sync = sync[:start] + new_pending + sync[end:]
old = """        final table = '${change['table'] ?? ''}';\n        final recordId = '${change['id'] ?? ''}';\n        if (!_allTables.contains(table) || recordId.isEmpty) continue;\n\n        final deleted = change['deleted'] == true;\n"""
new = """        final table = '${change['table'] ?? ''}';\n        final recordId = '${change['id'] ?? ''}';\n        if (!_allTables.contains(table) || recordId.isEmpty) continue;\n        final companyId = '${change['companyId'] ?? ''}'.trim();\n\n        final deleted = change['deleted'] == true;\n"""
if "final companyId = '${change['companyId'] ?? ''}'.trim();" not in sync:
    sync = replace_once(sync, old, new, 'scope remoto')
old = """        await txn.rawInsert(\n          'INSERT INTO $_changesTable('\n"""
new = """        if (companyId.isNotEmpty) {\n          await txn.insert(\n            'device_sync_scopes',\n            {'table_name': table, 'record_id': recordId, 'company_id': companyId},\n            conflictAlgorithm: ConflictAlgorithm.replace,\n          );\n        }\n\n        await txn.rawInsert(\n          'INSERT INTO $_changesTable('\n"""
if "await txn.insert(\n            'device_sync_scopes'" not in sync:
    sync = replace_once(sync, old, new, 'gravação de scope remoto')
write('lib/services/device_sync_service.dart', sync)

coord = read('lib/services/sync_coordinator.dart')
if "import 'dart:io';" not in coord:
    coord = coord.replace("import 'dart:async';\n", "import 'dart:async';\nimport 'dart:io';\n", 1)
if "import 'auth_service.dart';" not in coord:
    coord = coord.replace("import 'device_sync_service.dart';\n", "import 'auth_service.dart';\nimport 'device_sync_service.dart';\n", 1)
if 'if (!AuthService.isSignedIn) return;' not in coord:
    coord = coord.replace('  void _handleConnectivity(List<ConnectivityResult> results) {\n    final hasNetwork', '  void _handleConnectivity(List<ConnectivityResult> results) {\n    if (!AuthService.isSignedIn) return;\n    final hasNetwork', 1)
if 'if (_syncing || !AuthService.isSignedIn) return;' not in coord:
    coord = coord.replace('  Future<void> _trySync({bool deviceOnly = false}) async {\n    if (_syncing) return;\n', '  Future<void> _trySync({bool deviceOnly = false}) async {\n    if (_syncing || !AuthService.isSignedIn) return;\n', 1)
coord = coord.replace('        if (_showIndicator)\n          Positioned(', '        if (Platform.isWindows && _showIndicator)\n          Positioned(', 1)
write('lib/services/sync_coordinator.dart', coord)

code = read('painel_web_google_apps_script/Code.gs')
setup_old = """  ensureSheet_(ss, DEVICE_SYNC_SHEET, [\n    'table_name', 'record_id', 'deleted', 'server_version',\n    'source_device', 'source_platform', 'updated_at', 'payload_json'\n  ]);\n  ensureDriveRootFolder_();\n"""
setup_new = """  ensureSheet_(ss, DEVICE_SYNC_SHEET, [\n    'table_name', 'record_id', 'deleted', 'server_version',\n    'source_device', 'source_platform', 'updated_at', 'payload_json'\n  ]);\n  setupAuthStorage_(ss);\n  ensureDriveRootFolder_();\n"""
if 'setupAuthStorage_(ss);' not in code:
    code = replace_once(code, setup_old, setup_new, 'setupAuthStorage Code.gs')
auth_old = """    const expectedKey = PropertiesService.getScriptProperties().getProperty('AUDITAR_SYNC_KEY');\n    if (!expectedKey) return jsonResponse_({ok: false, message: 'Execute setupAuditar() primeiro.'});\n\n    if (request.action === 'drive_connect') {\n"""
auth_new = """    const expectedKey = PropertiesService.getScriptProperties().getProperty('AUDITAR_SYNC_KEY');\n    if (!expectedKey) return jsonResponse_({ok: false, message: 'Execute setupAuditar() primeiro.'});\n\n    const authRoute = handleAuthAction_(request, expectedKey);\n    if (authRoute.handled) return jsonResponse_(authRoute.response);\n\n    const suppliedAuthToken = String(request.authToken || '').trim();\n    if (suppliedAuthToken) {\n      const authorization = authorizeMultiUserToken_(request);\n      if (!authorization.ok) return jsonResponse_(authorization);\n      request.__authUser = authorization.user;\n      request.syncKey = expectedKey;\n      const requestedCompanyId = requestCompanyIdMultiUser_(request);\n      if (requestedCompanyId && !userCanAccessCompany_(authorization.user, requestedCompanyId)) {\n        return jsonResponse_({\n          ok: false,\n          code: 'ACCESS_DENIED',\n          message: 'Você não possui acesso a esta empresa.'\n        });\n      }\n    }\n\n    if (request.action === 'drive_connect') {\n"""
if 'const authRoute = handleAuthAction_' not in code:
    code = replace_once(code, auth_old, auth_new, 'auth route Code.gs')
legacy_device = """    if (request.action === 'device_sync_push') {\n      if (request.syncKey !== expectedKey) return jsonResponse_({ok: false, message: 'Chave de sincronização inválida.'});\n      return jsonResponse_(pushDeviceChanges_(request));\n    }\n\n    if (request.action === 'device_sync_pull') {\n      if (request.syncKey !== expectedKey) return jsonResponse_({ok: false, message: 'Chave de sincronização inválida.'});\n      return jsonResponse_(pullDeviceChanges_(request));\n    }\n"""
multi_device = """    if (request.action === 'device_sync_push') {\n      if (request.syncKey !== expectedKey) return jsonResponse_({ok: false, message: 'Chave de sincronização inválida.'});\n      return jsonResponse_(request.__authUser\n        ? pushDeviceChangesMultiUser_(request)\n        : pushDeviceChanges_(request));\n    }\n\n    if (request.action === 'device_sync_pull') {\n      if (request.syncKey !== expectedKey) return jsonResponse_({ok: false, message: 'Chave de sincronização inválida.'});\n      return jsonResponse_(request.__authUser\n        ? pullDeviceChangesMultiUser_(request)\n        : pullDeviceChanges_(request));\n    }\n"""
if 'pushDeviceChangesMultiUser_' not in code:
    code = replace_once(code, legacy_device, multi_device, 'device sync multiuser Code.gs')
write('painel_web_google_apps_script/Code.gs', code)

print('Auditar SST v3.23 multiusuário aplicado com sucesso.')

#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
pubp = root / 'pubspec.yaml'
authp = root / 'lib/services/auth_service.dart'
mainp = root / 'lib/main.dart'
coordp = root / 'lib/services/sync_coordinator.dart'
bgp = root / 'lib/services/background_sync_service.dart'

pub = pubp.read_text(encoding='utf-8')
auth = authp.read_text(encoding='utf-8')
main = mainp.read_text(encoding='utf-8')
coord = coordp.read_text(encoding='utf-8')

if 'version: 3.29.43+185' not in pub:
    if 'version: 3.29.42+184' not in pub:
        raise RuntimeError('Base Android v3.29.42+184 não encontrada')
    pub = pub.replace('version: 3.29.42+184', 'version: 3.29.43+185', 1)

if '  workmanager: ^0.10.10\n' not in pub:
    marker = '  url_launcher: ^6.3.1\n'
    if marker not in pub:
        raise RuntimeError('Marcador de dependências não localizado')
    pub = pub.replace(marker, marker + '  workmanager: ^0.10.10\n', 1)

if "package:crypto/crypto.dart" not in auth:
    marker = "import 'package:path/path.dart' as p;\n"
    auth = auth.replace(
        marker,
        "import 'package:connectivity_plus/connectivity_plus.dart';\n"
        "import 'package:crypto/crypto.dart';\n"
        "import 'package:flutter_secure_storage/flutter_secure_storage.dart';\n" + marker,
        1,
    )

fields_marker = "  static String _deviceId = '';\n"
fields = r'''  static const FlutterSecureStorage _offlineStore = FlutterSecureStorage();
  static const String _offlineLoginKey = 'auditar_offline_login_v1';
  static const String _offlineSaltKey = 'auditar_offline_salt_v1';
  static const String _offlineVerifierKey = 'auditar_offline_verifier_v1';
  static const String _offlineUserKey = 'auditar_offline_user_v1';
  static bool _offlineMode = false;

  static bool get isOfflineMode => _offlineMode;
'''
if '_offlineVerifierKey' not in auth:
    if fields_marker not in auth:
        raise RuntimeError('Campos do AuthService não localizados')
    auth = auth.replace(fields_marker, fields_marker + fields, 1)

old_login = r'''  static Future<AuditarUser> login({
    required String username,
    required String password,
  }) async {
    final identifier = username.trim();
    final result = await _post({
      'action': 'auth_login',
      'username': identifier,
      'email': identifier,
      'password': password,
      'deviceId': await deviceId(),
      'platform': Platform.isWindows ? 'windows' : 'android',
    });
    final rawUser = result['user'];
    final isAdmin = rawUser is Map &&
        '${rawUser['role'] ?? ''}'.toLowerCase() == 'admin';
    return _acceptLogin(result, migrateLegacy: isAdmin);
  }
'''
new_login = r'''  static Future<AuditarUser> login({
    required String username,
    required String password,
  }) async {
    final identifier = username.trim();
    if (Platform.isAndroid) {
      try {
        final connectivity = await Connectivity().checkConnectivity();
        if (connectivity.every((item) => item == ConnectivityResult.none)) {
          return _loginOffline(identifier: identifier, password: password);
        }
      } catch (_) {}
    }
    try {
      final result = await _post({
        'action': 'auth_login',
        'username': identifier,
        'email': identifier,
        'password': password,
        'deviceId': await deviceId(),
        'platform': Platform.isWindows ? 'windows' : 'android',
      });
      final rawUser = result['user'];
      final isAdmin = rawUser is Map &&
          '${rawUser['role'] ?? ''}'.toLowerCase() == 'admin';
      final user = await _acceptLogin(result, migrateLegacy: isAdmin);
      await _rememberOfflineLogin(identifier, password, user);
      _offlineMode = false;
      try {
        await AppDatabase.instance.setSetting('auth_offline_mode', 'false');
      } catch (_) {}
      return user;
    } catch (error) {
      if (!_isOfflineTransportError(error)) rethrow;
      return _loginOffline(identifier: identifier, password: password);
    }
  }
'''
if '_rememberOfflineLogin(identifier, password, user)' not in auth:
    if old_login not in auth:
        raise RuntimeError('AuthService.login não localizado')
    auth = auth.replace(old_login, new_login, 1)

refresh_marker = '''        _currentUser = refreshed;\n        await _writeIdentitySettings();\n        await _persist();\n'''
refresh_replacement = '''        _currentUser = refreshed;\n        await _writeIdentitySettings();\n        await _persist();\n        await _storeOfflineUser(refreshed);\n        _offlineMode = false;\n        try {\n          await AppDatabase.instance.setSetting('auth_offline_mode', 'false');\n        } catch (_) {}\n'''
if 'await _storeOfflineUser(refreshed);' not in auth:
    if refresh_marker not in auth:
        raise RuntimeError('Bloco de refresh de sessão não localizado')
    auth = auth.replace(refresh_marker, refresh_replacement, 1)

helpers = r'''  static String _normalizeOfflineLogin(String value) => value.trim().toLowerCase();

  static bool _isOfflineTransportError(Object error) {
    if (error is CentralTransportException) return true;
    final text = error.toString().toLowerCase();
    return text.contains('failed host lookup') ||
        text.contains('socketexception') ||
        text.contains('clientexception') ||
        text.contains('timeoutexception') ||
        text.contains('não respondeu a tempo') ||
        text.contains('nao respondeu a tempo') ||
        text.contains('sem acesso à central') ||
        text.contains('sem acesso a central') ||
        text.contains('conexão com a central') ||
        text.contains('conexao com a central') ||
        text.contains('erro 500') ||
        text.contains('erro 502') ||
        text.contains('erro 503') ||
        text.contains('erro 504');
  }

  static String _offlineVerifier({
    required String identifier,
    required String password,
    required String salt,
  }) {
    var bytes = utf8.encode('$salt|${_normalizeOfflineLogin(identifier)}|$password');
    // Reforço iterativo: a senha nunca é gravada no aparelho.
    for (var i = 0; i < 12000; i++) {
      bytes = sha256.convert(bytes).bytes;
    }
    return base64Url.encode(bytes);
  }

  static Future<void> _storeOfflineUser(AuditarUser user) async {
    await _offlineStore.write(
      key: _offlineUserKey,
      value: jsonEncode(user.toMap()),
    );
  }

  static Future<void> _rememberOfflineLogin(
    String identifier,
    String password,
    AuditarUser user,
  ) async {
    if (!Platform.isAndroid) return;
    final salt = const Uuid().v4();
    final verifier = _offlineVerifier(
      identifier: identifier,
      password: password,
      salt: salt,
    );
    await _offlineStore.write(
      key: _offlineLoginKey,
      value: _normalizeOfflineLogin(identifier),
    );
    await _offlineStore.write(key: _offlineSaltKey, value: salt);
    await _offlineStore.write(key: _offlineVerifierKey, value: verifier);
    await _storeOfflineUser(user);
  }

  static Future<AuditarUser> _loginOffline({
    required String identifier,
    required String password,
  }) async {
    if (!Platform.isAndroid) {
      throw StateError('O modo offline está disponível somente no aplicativo Android.');
    }
    final savedLogin = (await _offlineStore.read(key: _offlineLoginKey) ?? '').trim();
    final salt = (await _offlineStore.read(key: _offlineSaltKey) ?? '').trim();
    final savedVerifier =
        (await _offlineStore.read(key: _offlineVerifierKey) ?? '').trim();
    final savedUserJson =
        (await _offlineStore.read(key: _offlineUserKey) ?? '').trim();

    if (savedLogin.isEmpty ||
        salt.isEmpty ||
        savedVerifier.isEmpty ||
        savedUserJson.isEmpty ||
        savedLogin != _normalizeOfflineLogin(identifier)) {
      throw StateError(
        'Sem internet. Para usar o modo offline, faça ao menos um login online neste aparelho com este usuário.',
      );
    }

    final calculated = _offlineVerifier(
      identifier: identifier,
      password: password,
      salt: salt,
    );
    if (calculated != savedVerifier) {
      throw StateError('Usuário ou senha incorretos.');
    }

    final rawUser = jsonDecode(savedUserJson);
    if (rawUser is! Map) {
      throw StateError('O acesso offline salvo neste aparelho está inválido.');
    }
    final token = await AuthSecureStore.readSessionToken();
    if (token.isEmpty) {
      throw StateError(
        'O acesso offline precisa ser renovado. Conecte-se à internet e faça login uma vez.',
      );
    }

    final user = AuditarUser.fromMap(Map<String, dynamic>.from(rawUser));
    if (!user.active) throw StateError('Este usuário está inativo.');

    _currentUser = user;
    _sessionToken = token;
    _offlineMode = true;
    await AppDatabase.activateUser(user.id, migrateLegacy: user.isAdmin);
    await WebServiceConfig.applyEmbeddedConfiguration();
    await _writeIdentitySettings();
    await AppDatabase.instance.setSetting('auth_offline_mode', 'true');
    await AppDatabase.instance.setSetting(
      'last_device_sync_status',
      'Modo offline • aguardando internet',
    );
    return user;
  }

  /// Restaura a última sessão online somente para o worker em segundo plano.
  /// A interface do aplicativo continua exigindo usuário e senha a cada abertura.
  static Future<bool> initializeBackgroundSession() async {
    if (!Platform.isAndroid) return false;
    _sessionToken = '';
    _currentUser = null;

    try {
      final savedUserJson =
          (await _offlineStore.read(key: _offlineUserKey) ?? '').trim();
      final token = await AuthSecureStore.readSessionToken();
      if (savedUserJson.isEmpty || token.isEmpty) return false;
      final rawUser = jsonDecode(savedUserJson);
      if (rawUser is! Map) return false;
      final user = AuditarUser.fromMap(Map<String, dynamic>.from(rawUser));
      if (!user.active) return false;

      _currentUser = user;
      _sessionToken = token;
      await AppDatabase.activateUser(user.id, migrateLegacy: user.isAdmin);
      await WebServiceConfig.applyEmbeddedConfiguration();
      await _writeIdentitySettings();
      return true;
    } catch (_) {
      _sessionToken = '';
      _currentUser = null;
      return false;
    }
  }

  static Future<void> _clearOfflineLogin() async {
    for (final key in const [
      _offlineLoginKey,
      _offlineSaltKey,
      _offlineVerifierKey,
      _offlineUserKey,
    ]) {
      try {
        await _offlineStore.delete(key: key);
      } catch (_) {}
    }
    _offlineMode = false;
  }

'''
logout_marker = '  static Future<void> logout() async {\n'
if 'initializeBackgroundSession()' not in auth:
    if logout_marker not in auth:
        raise RuntimeError('AuthService.logout não localizado')
    auth = auth.replace(logout_marker, helpers + logout_marker, 1)

logout_clear_marker = '''    _sessionToken = '';\n    _currentUser = null;\n    await AuthSecureStore.deleteSessionToken();\n'''
logout_clear_replacement = '''    _sessionToken = '';\n    _currentUser = null;\n    await AuthSecureStore.deleteSessionToken();\n    await _clearOfflineLogin();\n'''
if 'await _clearOfflineLogin();' not in auth:
    if logout_clear_marker not in auth:
        raise RuntimeError('Limpeza de logout não localizada')
    auth = auth.replace(logout_clear_marker, logout_clear_replacement, 1)

background_service = r'''import 'dart:io';
import 'dart:ui';

import 'package:flutter/widgets.dart';
import 'package:workmanager/workmanager.dart';

import 'auth_service.dart';
import 'device_sync_service.dart';

const String _backgroundSyncTaskName = 'auditar.background.sync';
const String _backgroundSyncPeriodicUnique = 'auditar.background.sync.periodic';
const String _backgroundSyncNetworkReturnUnique = 'auditar.background.sync.network-return';

@pragma('vm:entry-point')
void auditarBackgroundSyncDispatcher() {
  Workmanager().executeTask((task, inputData) async {
    WidgetsFlutterBinding.ensureInitialized();
    DartPluginRegistrant.ensureInitialized();
    if (!Platform.isAndroid) return true;

    try {
      final restored = await AuthService.initializeBackgroundSession();
      if (!restored || !AuthService.isSignedIn) return true;

      await DeviceSyncService.synchronize(force: true).timeout(
        const Duration(minutes: 3),
      );
      return true;
    } catch (_) {
      return false;
    }
  });
}

class BackgroundSyncService {
  BackgroundSyncService._();

  static Future<void> initialize() async {
    if (!Platform.isAndroid) return;
    await Workmanager().initialize(auditarBackgroundSyncDispatcher);

    await Workmanager().registerPeriodicTask(
      _backgroundSyncPeriodicUnique,
      _backgroundSyncTaskName,
      frequency: const Duration(minutes: 15),
      constraints: Constraints(networkType: NetworkType.connected),
      existingWorkPolicy: ExistingPeriodicWorkPolicy.update,
      backoffPolicy: BackoffPolicy.exponential,
      backoffPolicyDelay: const Duration(minutes: 1),
    );

    await armForNetworkReturn();
  }

  static Future<void> armForNetworkReturn() async {
    if (!Platform.isAndroid) return;
    try {
      await Workmanager().registerOneOffTask(
        _backgroundSyncNetworkReturnUnique,
        _backgroundSyncTaskName,
        constraints: Constraints(networkType: NetworkType.connected),
        existingWorkPolicy: ExistingWorkPolicy.keep,
        backoffPolicy: BackoffPolicy.exponential,
        backoffPolicyDelay: const Duration(minutes: 1),
      );
    } catch (_) {}
  }
}
'''
bgp.parent.mkdir(parents=True, exist_ok=True)
bgp.write_text(background_service, encoding='utf-8', newline='\n')

if "services/background_sync_service.dart" not in main:
    marker = "import 'services/auth_service.dart';\n"
    if marker not in main:
        raise RuntimeError('Import AuthService no main não localizado')
    main = main.replace(
        marker,
        "import 'services/background_sync_service.dart';\n" + marker,
        1,
    )
if 'await BackgroundSyncService.initialize();' not in main:
    marker = '''  if (Platform.isWindows) {\n    sqfliteFfiInit();\n    databaseFactory = databaseFactoryFfi;\n    await _prepareWindowsDatabasePath();\n  }\n  await AuthService.initialize();\n'''
    replacement = '''  if (Platform.isWindows) {\n    sqfliteFfiInit();\n    databaseFactory = databaseFactoryFfi;\n    await _prepareWindowsDatabasePath();\n  }\n  if (Platform.isAndroid) {\n    await BackgroundSyncService.initialize();\n  }\n  await AuthService.initialize();\n'''
    if marker not in main:
        raise RuntimeError('Inicialização principal não localizada')
    main = main.replace(marker, replacement, 1)

if "background_sync_service.dart" not in coord:
    marker = "import 'auth_service.dart';\n"
    coord = coord.replace(
        marker,
        "import 'background_sync_service.dart';\n" + marker,
        1,
    )

old_lifecycle = r'''  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _trySync(deviceOnly: true);
      _tryAutoBackup();
    }
  }
'''
new_lifecycle = r'''  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _trySync(deviceOnly: true);
      _tryAutoBackup();
    } else if (Platform.isAndroid &&
        (state == AppLifecycleState.paused ||
            state == AppLifecycleState.hidden ||
            state == AppLifecycleState.detached)) {
      BackgroundSyncService.armForNetworkReturn();
    }
  }
'''
if 'BackgroundSyncService.armForNetworkReturn();' not in coord:
    if old_lifecycle not in coord:
        raise RuntimeError('Lifecycle do SyncCoordinator não localizado')
    coord = coord.replace(old_lifecycle, new_lifecycle, 1)

old_offline = r'''    if (!hasNetwork) {
      _setDesktopStatus(
        label: 'Offline',
        tone: _SyncTone.offline,
      );
      return;
    }
'''
new_offline = r'''    if (!hasNetwork) {
      if (Platform.isAndroid) {
        BackgroundSyncService.armForNetworkReturn();
      }
      _setDesktopStatus(
        label: 'Offline',
        tone: _SyncTone.offline,
      );
      return;
    }
'''
if coord.count('BackgroundSyncService.armForNetworkReturn();') < 2:
    if old_offline not in coord:
        raise RuntimeError('Bloco offline do SyncCoordinator não localizado')
    coord = coord.replace(old_offline, new_offline, 1)

pubp.write_text(pub, encoding='utf-8', newline='\n')
authp.write_text(auth, encoding='utf-8', newline='\n')
mainp.write_text(main, encoding='utf-8', newline='\n')
coordp.write_text(coord, encoding='utf-8', newline='\n')

final_pub = pubp.read_text(encoding='utf-8')
final_auth = authp.read_text(encoding='utf-8')
final_main = mainp.read_text(encoding='utf-8')
final_coord = coordp.read_text(encoding='utf-8')
assert 'version: 3.29.43+185' in final_pub
assert 'workmanager: ^0.10.10' in final_pub
assert 'initializeBackgroundSession' in final_auth
assert '_rememberOfflineLogin' in final_auth
assert 'senha nunca é gravada' in final_auth
assert 'BackgroundSyncService.initialize' in final_main
assert final_coord.count('BackgroundSyncService.armForNetworkReturn();') >= 2
assert bgp.exists()
print('Android v3.29.43+185: modo offline seguro + sincronização automática em segundo plano aplicados.')

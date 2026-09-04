import 'dart:convert';
import 'dart:io';

import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:uuid/uuid.dart';

import '../database.dart';
import 'apps_script_http.dart';
import 'web_service_config.dart';

class AuditarUser {
  final String id;
  final String name;
  final String email;
  final String role;
  final bool active;
  final bool allCompanies;
  final List<String> companyIds;

  const AuditarUser({
    required this.id,
    required this.name,
    required this.email,
    required this.role,
    required this.active,
    required this.allCompanies,
    required this.companyIds,
  });

  bool get isAdmin => role.toLowerCase() == 'admin';

  factory AuditarUser.fromMap(Map<String, dynamic> map) {
    final rawCompanies = map['companyIds'];
    return AuditarUser(
      id: '${map['id'] ?? ''}',
      name: '${map['name'] ?? ''}',
      email: '${map['email'] ?? ''}',
      role: '${map['role'] ?? 'tecnico'}',
      active: map['active'] != false,
      allCompanies: map['allCompanies'] == true ||
          '${map['role'] ?? ''}'.toLowerCase() == 'admin',
      companyIds: rawCompanies is List
          ? rawCompanies.map((item) => '$item').where((id) => id.isNotEmpty).toList()
          : const <String>[],
    );
  }

  Map<String, dynamic> toMap() => {
        'id': id,
        'name': name,
        'email': email,
        'role': role,
        'active': active,
        'allCompanies': allCompanies,
        'companyIds': companyIds,
      };
}

class AuthStatus {
  final bool configured;
  final bool hasUsers;

  const AuthStatus({required this.configured, required this.hasUsers});
}

class AuthService {
  AuthService._();

  static const _authFileName = 'auditar_sst_auth.json';
  static AuditarUser? _currentUser;
  static String _sessionToken = '';
  static String _deviceId = '';

  static AuditarUser? get currentUser => _currentUser;
  static String get sessionToken => _sessionToken;
  static bool get isSignedIn => _currentUser != null && _sessionToken.isNotEmpty;
  static bool get isAdmin => _currentUser?.isAdmin == true;

  static bool canAccessCompany(String companyId) {
    final user = _currentUser;
    if (user == null || !user.active) return false;
    if (user.isAdmin || user.allCompanies) return true;
    return user.companyIds.contains(companyId);
  }

  static Future<File> _authFile() async {
    final root = await getApplicationSupportDirectory();
    await root.create(recursive: true);
    return File(p.join(root.path, _authFileName));
  }

  static Future<void> initialize() async {
    final file = await _authFile();
    if (!await file.exists()) return;
    try {
      final decoded = jsonDecode(await file.readAsString());
      if (decoded is! Map) return;
      final map = Map<String, dynamic>.from(decoded);
      final token = '${map['sessionToken'] ?? ''}'.trim();
      final rawUser = map['user'];
      if (token.isEmpty || rawUser is! Map) return;
      _sessionToken = token;
      _currentUser = AuditarUser.fromMap(Map<String, dynamic>.from(rawUser));
      _deviceId = '${map['deviceId'] ?? ''}'.trim();
      if (_deviceId.isEmpty) _deviceId = const Uuid().v4();
    } catch (_) {
      try {
        await file.delete();
      } catch (_) {}
      _sessionToken = '';
      _currentUser = null;
      _deviceId = '';
    }
  }

  static Future<void> activateSavedSession() async {
    final user = _currentUser;
    if (user == null || _sessionToken.isEmpty) return;
    await AppDatabase.activateUser(
      user.id,
      migrateLegacy: user.isAdmin,
    );
    await WebServiceConfig.applyEmbeddedConfiguration();
    await _writeIdentitySettings();
  }

  static Future<void> _persist() async {
    final user = _currentUser;
    if (user == null || _sessionToken.isEmpty) return;
    if (_deviceId.isEmpty) _deviceId = const Uuid().v4();
    final file = await _authFile();
    await file.writeAsString(jsonEncode({
      'sessionToken': _sessionToken,
      'deviceId': _deviceId,
      'user': user.toMap(),
    }));
  }

  static Future<void> _writeIdentitySettings() async {
    final user = _currentUser;
    if (user == null) return;
    final db = AppDatabase.instance;
    await db.setSetting('auth_user_id', user.id);
    await db.setSetting('auth_user_name', user.name);
    await db.setSetting('auth_user_email', user.email);
    await db.setSetting('auth_user_role', user.role);
    await db.setSetting('auth_all_companies', user.allCompanies ? 'true' : 'false');
    await db.setSetting('auth_company_ids', jsonEncode(user.companyIds));
    if ((await db.getSetting('default_technician')).trim().isEmpty) {
      await db.setSetting('default_technician', user.name);
    }
  }

  static Future<Uri> _endpoint() async {
    final embedded = WebServiceConfig.endpoint.trim();
    final uri = Uri.tryParse(embedded);
    if (uri != null && uri.scheme == 'https') return uri;
    final local = (await AppDatabase.instance.getSetting('management_panel_endpoint')).trim();
    final localUri = Uri.tryParse(local);
    if (localUri == null || localUri.scheme != 'https') {
      throw StateError('A Central Online ainda não está configurada.');
    }
    return localUri;
  }

  static Future<Map<String, dynamic>> _post(Map<String, Object?> payload) async {
    final response = await AppsScriptHttp.postJson(await _endpoint(), payload);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw StateError('A Central Online respondeu com erro ${response.statusCode}.');
    }
    dynamic decoded;
    try {
      decoded = jsonDecode(response.body);
    } catch (_) {
      throw StateError('A Central Online retornou uma resposta inválida.');
    }
    if (decoded is! Map) throw StateError('Resposta inválida da Central Online.');
    final result = Map<String, dynamic>.from(decoded);
    if (result['ok'] != true) {
      final code = '${result['code'] ?? ''}';
      final message = '${result['message'] ?? 'Não foi possível concluir a operação.'}';
      if (code == 'AUTH_REQUIRED' || code == 'SESSION_INVALID') {
        throw StateError('Sessão expirada. Entre novamente.');
      }
      throw StateError(message);
    }
    return result;
  }

  static Future<AuthStatus> status() async {
    final result = await _post({'action': 'auth_status'});
    return AuthStatus(
      configured: result['configured'] == true,
      hasUsers: result['hasUsers'] == true,
    );
  }

  static Future<AuditarUser> bootstrapAdmin({
    required String name,
    required String email,
    required String password,
  }) async {
    final syncKey = WebServiceConfig.syncKey.trim();
    if (syncKey.isEmpty) {
      throw StateError('A versão instalada não possui a chave da Central Online.');
    }
    final result = await _post({
      'action': 'auth_bootstrap_admin',
      'syncKey': syncKey,
      'name': name.trim(),
      'email': email.trim(),
      'password': password,
      'deviceId': await deviceId(),
      'platform': Platform.isWindows ? 'windows' : 'android',
    });
    return _acceptLogin(result, migrateLegacy: true);
  }

  static Future<AuditarUser> login({
    required String email,
    required String password,
  }) async {
    final result = await _post({
      'action': 'auth_login',
      'email': email.trim(),
      'password': password,
      'deviceId': await deviceId(),
      'platform': Platform.isWindows ? 'windows' : 'android',
    });
    final rawUser = result['user'];
    final isAdmin = rawUser is Map &&
        '${rawUser['role'] ?? ''}'.toLowerCase() == 'admin';
    return _acceptLogin(result, migrateLegacy: isAdmin);
  }

  static Future<AuditarUser> _acceptLogin(
    Map<String, dynamic> result, {
    required bool migrateLegacy,
  }) async {
    final rawUser = result['user'];
    if (rawUser is! Map) throw StateError('A Central Online não retornou o usuário.');
    final token = '${result['sessionToken'] ?? ''}'.trim();
    if (token.isEmpty) throw StateError('A Central Online não retornou a sessão.');
    final user = AuditarUser.fromMap(Map<String, dynamic>.from(rawUser));
    _currentUser = user;
    _sessionToken = token;
    await AppDatabase.activateUser(user.id, migrateLegacy: migrateLegacy && user.isAdmin);
    await WebServiceConfig.applyEmbeddedConfiguration();
    await _writeIdentitySettings();
    await AppDatabase.instance.setSetting('device_sync_server_version', '0');
    await _persist();
    return user;
  }

  static Future<bool> verifySession() async {
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

  static Future<List<AuditarUser>> listUsers() async {
    final result = await _post({
      'action': 'auth_users_list',
      'authToken': _sessionToken,
    });
    final raw = result['users'];
    if (raw is! List) return const [];
    return raw
        .whereType<Map>()
        .map((item) => AuditarUser.fromMap(Map<String, dynamic>.from(item)))
        .toList();
  }

  static Future<AuditarUser> saveUser({
    String? userId,
    required String name,
    required String email,
    required String role,
    required bool active,
    required bool allCompanies,
    required List<String> companyIds,
    String password = '',
  }) async {
    final result = await _post({
      'action': 'auth_user_save',
      'authToken': _sessionToken,
      'user': {
        'id': userId ?? '',
        'name': name.trim(),
        'email': email.trim(),
        'role': role,
        'active': active,
        'allCompanies': allCompanies,
        'companyIds': companyIds,
        if (password.isNotEmpty) 'password': password,
      },
    });
    final raw = result['user'];
    if (raw is! Map) throw StateError('Usuário não retornado pela Central Online.');
    return AuditarUser.fromMap(Map<String, dynamic>.from(raw));
  }

  static Future<void> logout() async {
    final token = _sessionToken;
    if (token.isNotEmpty) {
      try {
        await _post({'action': 'auth_logout', 'authToken': token});
      } catch (_) {
        // O logout local não depende de internet.
      }
    }
    _sessionToken = '';
    _currentUser = null;
    final file = await _authFile();
    if (await file.exists()) await file.delete();
    await AppDatabase.deactivateUser();
  }

  static Future<String> deviceId() async {
    if (_deviceId.isNotEmpty) return _deviceId;
    final file = await _authFile();
    if (await file.exists()) {
      try {
        final decoded = jsonDecode(await file.readAsString());
        if (decoded is Map) {
          final value = '${decoded['deviceId'] ?? ''}'.trim();
          if (value.isNotEmpty) {
            _deviceId = value;
            return value;
          }
        }
      } catch (_) {}
    }
    _deviceId = const Uuid().v4();
    return _deviceId;
  }
}

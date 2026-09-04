import 'dart:convert';
import 'dart:io';

import 'package:flutter/services.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite/sqflite.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

import 'package:auditar_sst/database.dart';
import 'package:auditar_sst/services/auth_service.dart';
import 'package:auditar_sst/services/device_sync_service.dart';

class _FakeCentral {
  late final HttpServer server;
  final List<Map<String, dynamic>> _log = <Map<String, dynamic>>[];
  final Set<String> authTokensSeen = <String>{};
  int _version = 0;

  Future<void> start() async {
    server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    server.listen((request) async {
      try {
        final body = await utf8.decoder.bind(request).join();
        final decoded = jsonDecode(body);
        final payload = Map<String, dynamic>.from(decoded as Map);
        final action = '${payload['action'] ?? ''}';
        final authToken = '${payload['authToken'] ?? ''}'.trim();
        if (authToken.isNotEmpty) authTokensSeen.add(authToken);

        if (payload['syncKey'] != 'test-sync-key') {
          await _reply(request, {
            'ok': false,
            'message': 'Chave inválida no teste.',
          });
          return;
        }
        if (authToken.isEmpty) {
          await _reply(request, {
            'ok': false,
            'message': 'authToken ausente no teste.',
          });
          return;
        }

        if (action == 'device_sync_push') {
          final changes = payload['changes'];
          if (changes is List) {
            for (final raw in changes) {
              if (raw is! Map) continue;
              _version++;
              final change = Map<String, dynamic>.from(raw);
              _log.add({
                ...change,
                'serverVersion': _version,
              });
            }
          }
          await _reply(request, {
            'ok': true,
            'version': _version,
          });
          return;
        }

        if (action == 'device_sync_pull') {
          final since = int.tryParse('${payload['sinceVersion'] ?? 0}') ?? 0;
          final limit = int.tryParse('${payload['limit'] ?? 300}') ?? 300;
          final available = _log
              .where((item) => (item['serverVersion'] as int) > since)
              .toList();
          final page = available.take(limit).toList();
          final nextVersion = page.isEmpty
              ? since
              : page.last['serverVersion'] as int;
          await _reply(request, {
            'ok': true,
            'changes': page,
            'version': _version,
            'nextVersion': nextVersion,
            'hasMore': available.length > page.length,
          });
          return;
        }

        await _reply(request, {
          'ok': false,
          'message': 'Ação inesperada no teste: $action',
        });
      } catch (error) {
        request.response.statusCode = 500;
        request.response.write(jsonEncode({
          'ok': false,
          'message': '$error',
        }));
        await request.response.close();
      }
    });
  }

  Uri get endpoint => Uri.parse(
        'http://${server.address.address}:${server.port}/exec',
      );

  Future<void> close() => server.close(force: true);

  Future<void> _reply(
    HttpRequest request,
    Map<String, Object?> payload,
  ) async {
    request.response.statusCode = 200;
    request.response.headers.contentType = ContentType.json;
    request.response.write(jsonEncode(payload));
    await request.response.close();
  }
}

Future<void> _writeSession({
  required Directory supportDir,
  required String userId,
  required String deviceId,
  required String token,
}) async {
  FlutterSecureStorage.setMockInitialValues({
    'auditar_sst_session_token_v1': token,
  });
  final authFile = File('${supportDir.path}/auditar_sst_auth.json');
  await authFile.writeAsString(jsonEncode({
    'deviceId': deviceId,
    'user': {
      'id': userId,
      'name': userId,
      'email': '$userId@teste.local',
      'role': 'admin',
      'active': true,
      'allCompanies': true,
      'companyIds': <String>[],
    },
  }));
  await AuthService.initialize();
  await AuthService.activateSavedSession();
  expect(AuthService.isSignedIn, isTrue);
  expect(AuthService.sessionToken, token);
}

Future<void> _configureSync(Uri endpoint) async {
  final appDb = AppDatabase.instance;
  await appDb.setSetting('management_panel_endpoint', endpoint.toString());
  await appDb.setSetting('management_panel_sync_key', 'test-sync-key');
  await appDb.setSetting('device_sync_server_version', '0');
}

Future<Map<String, Object?>?> _company(String id) async {
  final db = await AppDatabase.instance.database;
  final rows = await db.query(
    'companies',
    where: 'id = ?',
    whereArgs: [id],
    limit: 1,
  );
  return rows.isEmpty ? null : rows.first;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late Directory supportDir;
  late _FakeCentral central;

  setUpAll(() async {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;

    supportDir = await Directory.systemTemp.createTemp('auditar_sync_auth_');
    const channel = MethodChannel('plugins.flutter.io/path_provider');
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
      if (call.method == 'getApplicationSupportDirectory') {
        return supportDir.path;
      }
      return supportDir.path;
    });

    central = _FakeCentral();
    await central.start();
  });

  tearDownAll(() async {
    await AppDatabase.deactivateUser();
    await central.close();
    if (await supportDir.exists()) {
      await supportDir.delete(recursive: true);
    }
  });

  test(
    'sincroniza inclusão, alteração e exclusão entre dois bancos locais',
    () async {
      // Dispositivo 1: representa o celular em campo.
      await _writeSession(
        supportDir: supportDir,
        userId: 'sync-phone-user',
        deviceId: 'phone-device',
        token: 'token-phone',
      );
      await _configureSync(central.endpoint);

      var db = await AppDatabase.instance.database;
      await db.insert('companies', {
        'id': 'empresa-sync-1',
        'name': 'Empresa criada no celular',
        'logo_path': '/arquivo-local-nao-sincronizavel.png',
      });
      await db.insert('inspections', {
        'id': 'vistoria-sync-1',
        'company_id': 'empresa-sync-1',
        'area': 'Produção',
        'checklist_type': 'Geral',
        'date': '2026-09-04',
        'status': 'Em andamento',
        'general_notes': 'Criada no celular',
      });
      await db.insert('answers', {
        'id': 'resposta-sync-1',
        'inspection_id': 'vistoria-sync-1',
        'question_id': 'q1',
        'question_text': 'Proteções da máquina',
        'status': 'Não Conforme',
        'observation': 'Proteção removida',
      });

      final phoneFirst = await DeviceSyncService.synchronize(force: true);
      expect(phoneFirst.sent, greaterThan(0));

      // Dispositivo 2: representa outro banco local, como o PC.
      await _writeSession(
        supportDir: supportDir,
        userId: 'sync-pc-user',
        deviceId: 'pc-device',
        token: 'token-pc',
      );
      await _configureSync(central.endpoint);

      final pcFirst = await DeviceSyncService.synchronize(force: true);
      expect(pcFirst.received, greaterThan(0));

      final receivedCompany = await _company('empresa-sync-1');
      expect(receivedCompany, isNotNull);
      expect(receivedCompany!['name'], 'Empresa criada no celular');
      // Caminhos locais não podem atravessar a sincronização estruturada.
      expect(receivedCompany['logo_path'], isNull);

      db = await AppDatabase.instance.database;
      final receivedInspection = await db.query(
        'inspections',
        where: 'id = ?',
        whereArgs: ['vistoria-sync-1'],
        limit: 1,
      );
      final receivedAnswer = await db.query(
        'answers',
        where: 'id = ?',
        whereArgs: ['resposta-sync-1'],
        limit: 1,
      );
      expect(receivedInspection, hasLength(1));
      expect(receivedAnswer, hasLength(1));

      // O pull remoto não pode virar um novo push infinito no outro aparelho.
      final pcAfterPull = await DeviceSyncService.synchronize(force: true);
      expect(pcAfterPull.sent, 0);

      // Alteração feita no PC deve voltar ao celular.
      await db.update(
        'companies',
        {'name': 'Empresa alterada no PC'},
        where: 'id = ?',
        whereArgs: ['empresa-sync-1'],
      );
      final pcUpdate = await DeviceSyncService.synchronize(force: true);
      expect(pcUpdate.sent, greaterThan(0));

      await _writeSession(
        supportDir: supportDir,
        userId: 'sync-phone-user',
        deviceId: 'phone-device',
        token: 'token-phone',
      );
      // Mantém a versão já conhecida por este banco; só reconfigura endpoint/chave.
      final phoneDb = AppDatabase.instance;
      await phoneDb.setSetting('management_panel_endpoint', central.endpoint.toString());
      await phoneDb.setSetting('management_panel_sync_key', 'test-sync-key');

      final phoneUpdate = await DeviceSyncService.synchronize(force: true);
      expect(phoneUpdate.received, greaterThan(0));
      expect((await _company('empresa-sync-1'))!['name'], 'Empresa alterada no PC');

      // Exclusão no celular precisa chegar ao PC também.
      db = await AppDatabase.instance.database;
      await db.delete(
        'companies',
        where: 'id = ?',
        whereArgs: ['empresa-sync-1'],
      );
      final phoneDelete = await DeviceSyncService.synchronize(force: true);
      expect(phoneDelete.sent, greaterThan(0));

      await _writeSession(
        supportDir: supportDir,
        userId: 'sync-pc-user',
        deviceId: 'pc-device',
        token: 'token-pc',
      );
      await AppDatabase.instance.setSetting(
        'management_panel_endpoint',
        central.endpoint.toString(),
      );
      await AppDatabase.instance.setSetting(
        'management_panel_sync_key',
        'test-sync-key',
      );
      final pcDelete = await DeviceSyncService.synchronize(force: true);
      expect(pcDelete.received, greaterThan(0));
      expect(await _company('empresa-sync-1'), isNull);

      // Garante que a sincronização realmente passou por autenticação individual.
      expect(central.authTokensSeen, contains('token-phone'));
      expect(central.authTokensSeen, contains('token-pc'));
    },
    timeout: const Timeout(Duration(seconds: 45)),
  );
}

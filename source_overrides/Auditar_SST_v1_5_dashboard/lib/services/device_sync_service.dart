import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:sqflite/sqflite.dart';
import 'package:uuid/uuid.dart';

import '../database.dart';
import 'apps_script_http.dart';

class DeviceSyncResult {
  final int sent;
  final int received;
  final bool skipped;

  const DeviceSyncResult({
    this.sent = 0,
    this.received = 0,
    this.skipped = false,
  });
}

/// Sincronização automática dos dados estruturados entre celular e computador.
///
/// A central do Google Apps Script mantém a versão mais recente de cada
/// registro. O banco local continua sendo offline-first e uma pequena tabela
/// de controle registra somente o que mudou desde o último envio.
class DeviceSyncService {
  static const _changesTable = 'device_sync_changes';
  static const _serverVersionSetting = 'device_sync_server_version';
  static const _deviceIdSetting = 'device_sync_id';
  static const _lastAttemptSetting = 'last_device_sync_attempt';
  static const _lastSuccessSetting = 'last_device_sync_success';
  static const _lastStatusSetting = 'last_device_sync_status';
  static const _lastErrorSetting = 'last_device_sync_error';

  static const _masterTables = <String>{
    'companies',
    'worksites',
    'sectors',
    'workers',
    'training_controls',
    'training_requirements',
    'checklist_templates',
    'checklist_items',
    'cipa_elections',
    'cipa_candidates',
    'cipa_voters',
  };

  static const _fieldTables = <String>{
    'inspections',
    'answers',
    'non_conformities',
    'action_plans',
    'sst_records',
  };

  static const _localOnlyColumns = <String, Set<String>>{
    'companies': {'logo_path'},
    'workers': {'aso_path'},
    'training_controls': {'certificate_path'},
    'inspections': {
      'technician_signature_path',
      'responsible_signature_path',
    },
  };

  static bool _running = false;
  static final StreamController<DeviceSyncResult> _events =
      StreamController<DeviceSyncResult>.broadcast();

  static Stream<DeviceSyncResult> get events => _events.stream;

  static bool get isWindows => Platform.isWindows;

  static String get platformLabel => isWindows ? 'Computador' : 'Celular';

  static Set<String> get _allTables => {..._masterTables, ..._fieldTables};

  // O celular também pode publicar um cadastro ainda inexistente. Assim, uma
  // instalação de PC vazia recebe os dados que já estavam sendo usados no
  // campo. Depois que o PC altera um cadastro, a central passa a preservá-lo
  // como fonte principal.
  static Set<String> get _outboundTables => _allTables;

  static Future<DeviceSyncResult> synchronize({bool force = false}) async {
    if (_running) return const DeviceSyncResult(skipped: true);
    _running = true;

    final appDb = AppDatabase.instance;
    try {
      final endpoint = (await appDb.getSetting(
        'management_panel_endpoint',
      ))
          .trim();
      final syncKey = (await appDb.getSetting(
        'management_panel_sync_key',
      ))
          .trim();

      if (endpoint.isEmpty || syncKey.isEmpty) {
        throw StateError('A Central Online ainda não está configurada.');
      }

      if (!force && !await _attemptIsDue(appDb)) {
        return const DeviceSyncResult(skipped: true);
      }

      await appDb.setSetting(
        _lastAttemptSetting,
        DateTime.now().toUtc().toIso8601String(),
      );

      final db = await appDb.database;
      await _ensureChangeTracking(db);
      final deviceId = await _deviceId(appDb);
      final uri = Uri.parse(endpoint);

      var sent = 0;
      for (var page = 0; page < 8; page++) {
        final changes = await _pendingChanges(db, limit: 200);
        if (changes.isEmpty) break;

        await _post(uri, {
          'action': 'device_sync_push',
          'syncKey': syncKey,
          'deviceId': deviceId,
          'platform': isWindows ? 'windows' : 'android',
          'changes': changes,
        });
        await _acknowledgeChanges(db, changes);
        sent += changes.length;
      }

      var received = 0;
      for (var page = 0; page < 12; page++) {
        final since = int.tryParse(
              await appDb.getSetting(
                _serverVersionSetting,
                fallback: '0',
              ),
            ) ??
            0;
        final response = await _post(uri, {
          'action': 'device_sync_pull',
          'syncKey': syncKey,
          'deviceId': deviceId,
          'platform': isWindows ? 'windows' : 'android',
          'sinceVersion': since,
          'limit': 300,
        });

        final rawChanges = response['changes'];
        final changes = rawChanges is List ? rawChanges : const [];
        if (changes.isNotEmpty) {
          await _applyRemoteChanges(db, changes);
          received += changes.length;
        }

        final nextVersion = _asInt(response['nextVersion']);
        final currentVersion = _asInt(response['version']);
        final savedVersion = nextVersion > 0 ? nextVersion : currentVersion;
        if (savedVersion >= since) {
          await appDb.setSetting(_serverVersionSetting, '$savedVersion');
        }

        if (response['hasMore'] != true) break;
      }

      final now = DateTime.now().toUtc().toIso8601String();
      await appDb.setSetting(_lastSuccessSetting, now);
      await appDb.setSetting(
        _lastStatusSetting,
        sent == 0 && received == 0
            ? 'Tudo atualizado'
            : 'Enviados: $sent • Recebidos: $received',
      );
      await appDb.setSetting(_lastErrorSetting, '');
      final result = DeviceSyncResult(sent: sent, received: received);
      _events.add(result);
      return result;
    } catch (error) {
      await appDb.setSetting(_lastStatusSetting, 'Sincronização pendente');
      await appDb.setSetting(_lastErrorSetting, _friendlyError(error));
      _events.add(const DeviceSyncResult(skipped: true));
      rethrow;
    } finally {
      _running = false;
    }
  }

  static Future<bool> _attemptIsDue(AppDatabase db) async {
    final value = await db.getSetting(_lastAttemptSetting);
    final last = DateTime.tryParse(value)?.toUtc();
    if (last == null) return true;
    return DateTime.now().toUtc().difference(last) >=
        const Duration(seconds: 15);
  }

  static Future<String> _deviceId(AppDatabase db) async {
    final current = (await db.getSetting(_deviceIdSetting)).trim();
    if (current.isNotEmpty) return current;
    final created = const Uuid().v4();
    await db.setSetting(_deviceIdSetting, created);
    return created;
  }

  static Future<void> _ensureChangeTracking(Database db) async {
    await db.execute(
      'CREATE TABLE IF NOT EXISTS $_changesTable('
      'table_name TEXT NOT NULL, '
      'record_id TEXT NOT NULL, '
      'local_version INTEGER NOT NULL DEFAULT 1, '
      'dirty INTEGER NOT NULL DEFAULT 1, '
      'deleted INTEGER NOT NULL DEFAULT 0, '
      'PRIMARY KEY(table_name, record_id)'
      ')',
    );

    for (final table in _allTables) {
      await db.execute(
        'CREATE TRIGGER IF NOT EXISTS device_sync_${table}_insert '
        'AFTER INSERT ON $table BEGIN '
        'INSERT INTO $_changesTable('
        'table_name, record_id, local_version, dirty, deleted'
        ") VALUES('$table', NEW.id, 1, 1, 0) "
        'ON CONFLICT(table_name, record_id) DO UPDATE SET '
        'local_version = local_version + 1, dirty = 1, deleted = 0; '
        'END',
      );
      await db.execute(
        'CREATE TRIGGER IF NOT EXISTS device_sync_${table}_update '
        'AFTER UPDATE ON $table BEGIN '
        'INSERT INTO $_changesTable('
        'table_name, record_id, local_version, dirty, deleted'
        ") VALUES('$table', NEW.id, 1, 1, 0) "
        'ON CONFLICT(table_name, record_id) DO UPDATE SET '
        'local_version = local_version + 1, dirty = 1, deleted = 0; '
        'END',
      );
      await db.execute(
        'CREATE TRIGGER IF NOT EXISTS device_sync_${table}_delete '
        'AFTER DELETE ON $table BEGIN '
        'INSERT INTO $_changesTable('
        'table_name, record_id, local_version, dirty, deleted'
        ") VALUES('$table', OLD.id, 1, 1, 1) "
        'ON CONFLICT(table_name, record_id) DO UPDATE SET '
        'local_version = local_version + 1, dirty = 1, deleted = 1; '
        'END',
      );

      final initialDirty = _outboundTables.contains(table) ? 1 : 0;
      await db.execute(
        'INSERT OR IGNORE INTO $_changesTable('
        'table_name, record_id, local_version, dirty, deleted'
        ") SELECT '$table', id, 1, $initialDirty, 0 FROM $table",
      );
    }
  }

  static Future<List<Map<String, Object?>>> _pendingChanges(
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

      result.add({
        'table': table,
        'id': recordId,
        'localVersion': _asInt(metadata['local_version']),
        'deleted': deleted,
        if (payload != null) 'payload': payload,
      });
    }
    return result;
  }

  static Future<void> _acknowledgeChanges(
    Database db,
    List<Map<String, Object?>> changes,
  ) async {
    await db.transaction((txn) async {
      for (final change in changes) {
        await txn.update(
          _changesTable,
          {'dirty': 0},
          where: 'table_name = ? AND record_id = ? AND local_version = ?',
          whereArgs: [
            change['table'],
            change['id'],
            change['localVersion'],
          ],
        );
      }
    });
  }

  static Future<void> _applyRemoteChanges(
    Database db,
    List<dynamic> changes,
  ) async {
    final columnCache = <String, Set<String>>{};

    await db.transaction((txn) async {
      for (final raw in changes) {
        if (raw is! Map) continue;
        final change = Map<String, dynamic>.from(raw);
        final table = '${change['table'] ?? ''}';
        final recordId = '${change['id'] ?? ''}';
        if (!_allTables.contains(table) || recordId.isEmpty) continue;

        final deleted = change['deleted'] == true;
        if (deleted) {
          await txn.delete(table, where: 'id = ?', whereArgs: [recordId]);
        } else {
          final rawPayload = change['payload'];
          if (rawPayload is! Map) continue;

          var columns = columnCache[table];
          if (columns == null) {
            final info = await txn.rawQuery('PRAGMA table_info($table)');
            columns = info.map((row) => '${row['name']}').toSet();
            columnCache[table] = columns;
          }

          final payload = <String, Object?>{};
          rawPayload.forEach((key, value) {
            final name = '$key';
            if (columns!.contains(name) &&
                !(_localOnlyColumns[table] ?? const <String>{})
                    .contains(name)) {
              payload[name] = value as Object?;
            }
          });
          payload['id'] = recordId;

          final updated = await txn.update(
            table,
            payload,
            where: 'id = ?',
            whereArgs: [recordId],
          );
          if (updated == 0) {
            await txn.insert(
              table,
              payload,
              conflictAlgorithm: ConflictAlgorithm.replace,
            );
          }
        }

        await txn.rawInsert(
          'INSERT INTO $_changesTable('
          'table_name, record_id, local_version, dirty, deleted'
          ') VALUES(?, ?, 0, 0, ?) '
          'ON CONFLICT(table_name, record_id) DO UPDATE SET '
          'dirty = 0, deleted = excluded.deleted',
          [table, recordId, deleted ? 1 : 0],
        );
      }
    });
  }

  static Future<Map<String, dynamic>> _post(
    Uri endpoint,
    Map<String, Object?> payload,
  ) async {
    final response = await AppsScriptHttp.postJson(endpoint, payload);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw StateError('A Central Online não respondeu corretamente.');
    }

    final decoded = jsonDecode(response.body);
    if (decoded is! Map) {
      throw StateError('Resposta inválida da Central Online.');
    }
    final result = Map<String, dynamic>.from(decoded);
    if (result['ok'] != true) {
      throw StateError('${result['message'] ?? 'Falha na sincronização.'}');
    }
    return result;
  }

  static int _asInt(Object? value) {
    if (value is int) return value;
    if (value is num) return value.toInt();
    return int.tryParse('$value') ?? 0;
  }

  static String _friendlyError(Object error) {
    final text = '$error'.replaceFirst('Bad state: ', '').trim();
    return text.length <= 240 ? text : '${text.substring(0, 237)}...';
  }
}

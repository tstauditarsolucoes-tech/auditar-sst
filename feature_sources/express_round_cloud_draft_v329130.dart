import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

import '../database.dart';
import '../models.dart';
import 'auth_service.dart';
import 'device_sync_service.dart';
import 'media_sync_service.dart';

/// Ronda drafts use the existing company-scoped SST and media queues.
/// No new GS endpoints, tables, or sync algorithms. Local draft is kept until
/// server acknowledgement for both the structured record and every photo.
class ExpressRoundCloudDraftService {
  static const draftType = 'RONDA_RASCUNHO';
  static const photoType = 'round_draft_photo';
  static const maxPhotoBytes = 12 * 1024 * 1024;
  static String _id(String company, String round) => 'round_draft_' + company + '_' + round;

  static Map<String, dynamic> _refs(Object? raw) =>
      raw is Map ? Map<String, dynamic>.from(raw) : <String, dynamic>{};

  static Future<void> _registerPhoto(
      String company, String entityId, String path) async {
    final db = await AppDatabase.instance.database;
    final id = 'media_' + photoType + '_' + entityId;
    final old = await db.query('media_assets', where: 'id = ? AND company_id = ?',
        whereArgs: [id, company], limit: 1);
    if (old.isNotEmpty) {
      if ((old.first['local_path'] ?? '').toString() != path) {
        await db.update('media_assets', {'local_path': path},
            where: 'id = ? AND company_id = ?', whereArgs: [id, company]);
      }
      return;
    }
    await db.insert('media_assets', {
      'id': id, 'company_id': company, 'entity_type': photoType,
      'entity_id': entityId, 'local_path': path, 'drive_file_id': '',
      'file_name': p.basename(path),
      'mime_type': p.extension(path).toLowerCase() == '.png'
          ? 'image/png' : 'image/jpeg',
      'updated_at': DateTime.now().toUtc().toIso8601String(),
    }, conflictAlgorithm: ConflictAlgorithm.ignore);
  }

  static Future<bool> publish({
    required String companyId,
    required String roundId,
    required Map<String, dynamic> snapshot,
  }) async {
    if (companyId.trim().isEmpty || roundId.trim().isEmpty) {
      throw StateError('Empresa e ronda devem estar identificadas.');
    }
    await DeviceSyncService.pendingChangesCount();
    final refs = _refs(snapshot['cloudPhotoRefs']);
    for (final field in const ['photoPath', 'photoPath2']) {
      final local = (snapshot[field] ?? '').toString().trim();
      if (local.isEmpty) continue;
      final file = File(local);
      if (!await file.exists()) {
        throw StateError('Uma foto do rascunho não está disponível neste aparelho.');
      }
      final bytes = await file.readAsBytes();
      if (bytes.isEmpty || bytes.length > maxPhotoBytes) {
        throw StateError('A foto precisa ter até 12 MB.');
      }
      final slot = field == 'photoPath' ? 'primary' : 'secondary';
      final hash = sha256.convert(bytes).toString().substring(0, 24);
      // New content always receives a new media ID; an older Drive backup
      // cannot accidentally be treated as the replacement photo.
      final entityId = roundId + '_' + (snapshot['entryId'] ?? '').toString() +
          '_' + slot + '_' + hash;
      await _registerPhoto(companyId, entityId, local);
      refs[slot] = entityId;
    }
    final clean = Map<String, dynamic>.from(snapshot)
      ..['photoPath'] = ''
      ..['photoPath2'] = ''
      ..['cloudPhotoRefs'] = refs
      ..['cloudDraftSchema'] = 1
      ..['companyId'] = companyId
      ..['roundId'] = roundId
      ..['updatedAt'] = DateTime.now().toUtc().toIso8601String();
    final id = _id(companyId, roundId);
    await AppDatabase.instance.upsertSstRecord(SstRecord(
      id: id, companyId: companyId, type: draftType,
      title: 'Rascunho de vistoria', date: DateTime.now(),
      status: 'RASCUNHO', priority: 'Média', payload: clean,
    ));
    if (!AuthService.isSignedIn) return false;
    try {
      await MediaSyncService.uploadPending(limit: 12);
      await DeviceSyncService.synchronize(force: true);
    } catch (_) {
      return false;
    }
    final db = await AppDatabase.instance.database;
    final pending = await db.query('device_sync_changes',
      columns: ['dirty'], where: 'table_name = ? AND record_id = ?',
      whereArgs: ['sst_records', id], limit: 1,
    );
    if (pending.isEmpty || (pending.first['dirty'] ?? 1).toString() != '0') {
      return false;
    }
    for (final ref in refs.values) {
      final entity = ref.toString().trim();
      if (entity.isEmpty) continue;
      final rows = await db.query('media_assets', columns: ['drive_file_id'],
        where: 'id = ? AND company_id = ?',
        whereArgs: ['media_' + photoType + '_' + entity, companyId], limit: 1,
      );
      if (rows.isEmpty ||
          (rows.first['drive_file_id'] ?? '').toString().trim().isEmpty) {
        return false;
      }
    }
    return true;
  }

  static Future<List<SstRecord>> list(String companyId) async {
    final all = await AppDatabase.instance.getSstRecords(
        type: draftType, companyId: companyId);
    return all.where((r) => r.companyId == companyId &&
        r.status == 'RASCUNHO' &&
        r.payload['cloudDraftSchema'] == 1 &&
        (r.payload['roundId'] ?? '').toString().trim().isNotEmpty).toList()
      ..sort((a,b) => (b.payload['updatedAt'] ?? '').toString()
          .compareTo((a.payload['updatedAt'] ?? '').toString()));
  }

  static Future<Map<String, dynamic>> restore({
    required String companyId, required SstRecord record,
  }) async {
    if (record.companyId != companyId || record.type != draftType ||
        record.status != 'RASCUNHO' ||
        record.payload['cloudDraftSchema'] != 1) {
      throw StateError('Este rascunho não pertence à empresa selecionada.');
    }
    final payload = Map<String, dynamic>.from(record.payload);
    final refs = _refs(payload['cloudPhotoRefs']);
    var missing = false;
    for (final field in const ['photoPath','photoPath2']) {
      final slot = field == 'photoPath' ? 'primary' : 'secondary';
      final entity = (refs[slot] ?? '').toString().trim();
      payload[field] = '';
      if (entity.isEmpty) continue;
      final file = await MediaSyncService.trainingRecordMediaLocalPath(
          companyId: companyId, entityType: photoType, entityId: entity);
      if (file != null && file.isNotEmpty && await File(file).exists() &&
          await File(file).length() > 0) {
        payload[field] = file;
      } else {
        missing = true;
      }
    }
    payload['cloudPhotoRefs'] = refs;
    payload['cloudPhotoMissing'] = missing;
    return payload;
  }

  static Future<void> complete({
    required String companyId, required String roundId,
  }) async {
    final all = await AppDatabase.instance.getSstRecords(
        type: draftType, companyId: companyId);
    for (final record in all) {
      if (record.id != _id(companyId, roundId)) continue;
      await AppDatabase.instance.upsertSstRecord(SstRecord(
        id: record.id, companyId: companyId, sectorId: record.sectorId,
        type: draftType, title: record.title, date: record.date,
        dueDate: record.dueDate, status: 'CONCLUIDO',
        priority: record.priority, payload: {
          ...record.payload,
          'completedAt': DateTime.now().toUtc().toIso8601String(),
        },
      ));
      return;
    }
  }
}

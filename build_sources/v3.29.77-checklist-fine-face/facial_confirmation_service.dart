import 'dart:io';

import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

import '../database.dart';
import 'media_sync_service.dart';

class FacialConfirmationService {
  FacialConfirmationService._();

  static Future<void> register({
    required String companyId,
    required String entityType,
    required String confirmationId,
    required String localPath,
  }) async {
    final cleanCompany = companyId.trim();
    final cleanType = entityType.trim();
    final cleanId = confirmationId.trim();
    final cleanPath = localPath.trim();
    if (cleanCompany.isEmpty ||
        cleanType.isEmpty ||
        cleanId.isEmpty ||
        cleanPath.isEmpty) {
      return;
    }

    final db = await AppDatabase.instance.database;
    await db.insert(
      'media_assets',
      {
        'id': 'facial-$cleanType-$cleanId',
        'company_id': cleanCompany,
        'entity_type': cleanType,
        'entity_id': cleanId,
        'local_path': cleanPath,
        'drive_file_id': '',
        'file_name': p.basename(cleanPath),
        'mime_type': 'image/jpeg',
        'updated_at': DateTime.now().toUtc().toIso8601String(),
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  static Future<String?> localPath({
    required String companyId,
    required String entityType,
    required String confirmationId,
    bool restoreIfMissing = true,
  }) {
    return MediaSyncService.trainingRecordMediaLocalPath(
      companyId: companyId,
      entityType: entityType,
      entityId: confirmationId,
      restoreIfMissing: restoreIfMissing,
    );
  }

  static Future<void> remove({
    required String entityType,
    required String confirmationId,
    bool deleteLocalFile = true,
  }) async {
    final cleanType = entityType.trim();
    final cleanId = confirmationId.trim();
    if (cleanType.isEmpty || cleanId.isEmpty) return;
    final db = await AppDatabase.instance.database;
    final rows = await db.query(
      'media_assets',
      where: 'entity_type = ? AND entity_id = ?',
      whereArgs: [cleanType, cleanId],
      limit: 1,
    );
    if (deleteLocalFile && rows.isNotEmpty) {
      final path = '${rows.first['local_path'] ?? ''}'.trim();
      if (path.isNotEmpty) {
        try {
          final file = File(path);
          if (await file.exists()) await file.delete();
        } catch (_) {}
      }
    }
    await db.delete(
      'media_assets',
      where: 'entity_type = ? AND entity_id = ?',
      whereArgs: [cleanType, cleanId],
    );
  }
}

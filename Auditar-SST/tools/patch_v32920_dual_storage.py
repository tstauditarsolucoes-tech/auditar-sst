#!/usr/bin/env python3
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
APP = REPO / 'app' / 'Auditar_SST_v1_5_dashboard'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Trecho esperado não encontrado: {label}')
    return text.replace(old, new, 1)


def write_hostinger_service() -> None:
    path = APP / 'lib/services/hostinger_media_service.dart'
    path.write_text(r'''import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:http/http.dart' as http;
import 'package:path/path.dart' as p;

import '../database.dart';
import 'auth_service.dart';

/// Armazenamento primário opcional de mídias na Hostinger.
///
/// A Central Google/Drive continua existindo como backup e contingência. Se a
/// Hostinger não estiver configurada, todos os métodos retornam sem interferir
/// no fluxo atual do aplicativo.
class HostingerMediaService {
  HostingerMediaService._();

  static const int _maxMediaBytes = 12 * 1024 * 1024;
  static const String endpoint = String.fromEnvironment(
    'AUDITAR_MEDIA_HOSTINGER_URL',
  );
  static const String apiKey = String.fromEnvironment(
    'AUDITAR_MEDIA_HOSTINGER_KEY',
  );

  static bool get isConfigured {
    final uri = Uri.tryParse(endpoint.trim());
    return apiKey.trim().isNotEmpty &&
        uri != null &&
        uri.scheme == 'https' &&
        uri.host.isNotEmpty;
  }

  static Future<int> uploadPending({int limit = 40}) async {
    if (!isConfigured || !AuthService.isSignedIn) return 0;
    final appDb = AppDatabase.instance;
    final db = await appDb.database;
    final rows = await db.query(
      'media_assets',
      where: 'company_id IS NOT NULL AND company_id <> "" '
          'AND entity_type IS NOT NULL AND entity_type <> "" '
          'AND entity_id IS NOT NULL AND entity_id <> "" '
          'AND local_path IS NOT NULL AND local_path <> "" '
          'AND file_name IS NOT NULL AND file_name <> ""',
      orderBy:
          "CASE WHEN entity_type = 'company_logo' THEN 0 ELSE 1 END, updated_at ASC",
      limit: limit,
    );

    var uploaded = 0;
    String lastError = '';
    for (final raw in rows) {
      final row = Map<String, Object?>.from(raw);
      final companyId = '${row['company_id'] ?? ''}'.trim();
      if (companyId.isEmpty || !AuthService.canAccessCompany(companyId)) continue;
      try {
        final localPath = '${row['local_path'] ?? ''}'.trim();
        final file = File(localPath);
        if (!await file.exists()) continue;
        final bytes = await file.readAsBytes();
        if (bytes.isEmpty || bytes.length > _maxMediaBytes) continue;
        final hash = sha256.convert(bytes).toString();
        final assetId = '${row['id'] ?? ''}'.trim();
        final stateKey = _stateKey(assetId);
        if (assetId.isNotEmpty && (await appDb.getSetting(stateKey)).trim() == hash) {
          continue;
        }
        await _uploadRow(row, bytes, hash);
        if (assetId.isNotEmpty) await appDb.setSetting(stateKey, hash);
        uploaded++;
      } catch (e) {
        lastError = _friendlyError(e);
      }
    }
    if (uploaded > 0) {
      await appDb.setSetting(
        'hostinger_media_last_success',
        DateTime.now().toUtc().toIso8601String(),
      );
    }
    await appDb.setSetting('hostinger_media_last_error', lastError);
    return uploaded;
  }

  static Future<String> uploadEntity({
    required String companyId,
    required String entityType,
    required String entityId,
  }) async {
    if (!isConfigured) return '';
    if (!AuthService.isSignedIn || !AuthService.canAccessCompany(companyId)) {
      throw StateError('Sessão sem acesso à empresa.');
    }
    final appDb = AppDatabase.instance;
    final db = await appDb.database;
    final rows = await db.query(
      'media_assets',
      where: 'company_id = ? AND entity_type = ? AND entity_id = ? '
          'AND local_path IS NOT NULL AND local_path <> "" '
          'AND file_name IS NOT NULL AND file_name <> ""',
      whereArgs: [companyId, entityType, entityId],
      orderBy: 'updated_at DESC',
      limit: 1,
    );
    if (rows.isEmpty) throw StateError('Mídia local não encontrada.');
    final row = Map<String, Object?>.from(rows.first);
    final file = File('${row['local_path'] ?? ''}'.trim());
    if (!await file.exists()) throw StateError('Arquivo local não encontrado.');
    final bytes = await file.readAsBytes();
    if (bytes.isEmpty || bytes.length > _maxMediaBytes) {
      throw StateError('A mídia deve ter no máximo 12 MB.');
    }
    final hash = sha256.convert(bytes).toString();
    final storageId = await _uploadRow(row, bytes, hash);
    final assetId = '${row['id'] ?? ''}'.trim();
    if (assetId.isNotEmpty) await appDb.setSetting(_stateKey(assetId), hash);
    await appDb.setSetting(
      'hostinger_media_last_success',
      DateTime.now().toUtc().toIso8601String(),
    );
    await appDb.setSetting('hostinger_media_last_error', '');
    return storageId;
  }

  static Future<Map<String, dynamic>?> downloadAsset(
    Map<String, Object?> row,
  ) async {
    if (!isConfigured || !AuthService.isSignedIn) return null;
    final companyId = '${row['company_id'] ?? ''}'.trim();
    final entityType = '${row['entity_type'] ?? ''}'.trim();
    final entityId = '${row['entity_id'] ?? ''}'.trim();
    if (companyId.isEmpty || entityType.isEmpty || entityId.isEmpty) return null;
    if (!AuthService.canAccessCompany(companyId)) return null;

    final result = await _post(
      <String, Object?>{
        'action': 'download',
        'companyId': companyId,
        'entityType': entityType,
        'entityId': entityId,
      },
      allowNotFound: true,
    );
    if (result == null) return null;
    final encoded = '${result['contentBase64'] ?? ''}'.trim();
    if (encoded.isEmpty) return null;
    final bytes = base64Decode(encoded);
    if (bytes.isEmpty || bytes.length > _maxMediaBytes) {
      throw StateError('Mídia inválida recebida da Hostinger.');
    }
    final expected = '${result['sha256'] ?? ''}'.trim().toLowerCase();
    final actual = sha256.convert(bytes).toString();
    if (expected.isNotEmpty && expected != actual) {
      throw StateError('Falha de integridade na mídia da Hostinger.');
    }
    return result;
  }

  static Future<void> deleteAsset({
    required String companyId,
    required String entityType,
    required String entityId,
  }) async {
    if (!isConfigured || !AuthService.isSignedIn) return;
    if (!AuthService.canAccessCompany(companyId)) return;
    await _post(<String, Object?>{
      'action': 'delete',
      'companyId': companyId,
      'entityType': entityType,
      'entityId': entityId,
    });
  }

  static Future<String> _uploadRow(
    Map<String, Object?> row,
    List<int> bytes,
    String hash,
  ) async {
    final companyId = '${row['company_id'] ?? ''}'.trim();
    final entityType = '${row['entity_type'] ?? ''}'.trim();
    final entityId = '${row['entity_id'] ?? ''}'.trim();
    if (companyId.isEmpty || entityType.isEmpty || entityId.isEmpty) {
      throw StateError('Mídia sem empresa ou identificador.');
    }
    final result = await _post(<String, Object?>{
      'action': 'upload',
      'companyId': companyId,
      'entityType': entityType,
      'entityId': entityId,
      'fileName': '${row['file_name'] ?? p.basename('${row['local_path'] ?? ''}')}',
      'mimeType': '${row['mime_type'] ?? _mimeTypeFor('${row['local_path'] ?? ''}')}',
      'sha256': hash,
      'contentBase64': base64Encode(bytes),
    });
    final storageId = '${result?['storageId'] ?? ''}'.trim();
    if (storageId.isEmpty) throw StateError('A Hostinger não confirmou o armazenamento.');
    return storageId;
  }

  static Future<Map<String, dynamic>?> _post(
    Map<String, Object?> payload, {
    bool allowNotFound = false,
  }) async {
    if (!isConfigured) return null;
    final uri = Uri.parse(endpoint.trim());
    final response = await http
        .post(
          uri,
          headers: <String, String>{
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json',
            'X-Auditar-Key': apiKey.trim(),
          },
          body: jsonEncode(payload),
        )
        .timeout(const Duration(seconds: 25));
    if (allowNotFound && response.statusCode == 404) return null;
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw StateError('Hostinger respondeu com erro ${response.statusCode}.');
    }
    final decoded = jsonDecode(response.body);
    if (decoded is! Map) throw StateError('Resposta inválida da Hostinger.');
    final result = Map<String, dynamic>.from(decoded);
    if (result['ok'] != true) {
      if (allowNotFound && '${result['code'] ?? ''}' == 'NOT_FOUND') return null;
      throw StateError('${result['message'] ?? 'Falha no armazenamento Hostinger.'}');
    }
    return result;
  }

  static String _stateKey(String assetId) =>
      'hostinger_media_sha_${assetId.replaceAll(RegExp(r'[^A-Za-z0-9_-]'), '_')}';

  static String _mimeTypeFor(String filePath) {
    switch (p.extension(filePath).toLowerCase()) {
      case '.png':
        return 'image/png';
      case '.webp':
        return 'image/webp';
      default:
        return 'image/jpeg';
    }
  }

  static String _friendlyError(Object error) =>
      error.toString().replaceFirst('Bad state: ', '');
}
''', encoding='utf-8')


def patch_media_service() -> None:
    path = APP / 'lib/services/media_sync_service.dart'
    text = path.read_text(encoding='utf-8')

    if "import 'hostinger_media_service.dart';" not in text:
        marker = "import 'auth_service.dart';\n"
        if marker in text:
            text = text.replace(marker, marker + "import 'hostinger_media_service.dart';\n", 1)
        else:
            marker = 'class MediaSyncSummary {'
            text = replace_once(text, marker, "import 'hostinger_media_service.dart';\n\n" + marker, 'import Hostinger')

    text = text.replace(
      '/// Sincroniza evidências físicas (fotos e assinaturas) por meio do Google Drive\n'
      '/// da Central Online. Os metadados viajam pelo sync estruturado; os bytes ficam\n'
      '/// no Drive e são baixados sob demanda no outro dispositivo.',
      '/// Sincroniza mídias em armazenamento duplo: Hostinger como cópia principal e\n'
      '/// Google Drive como backup/contingência. O banco local continua offline-first.',
      1,
    )

    text = replace_once(
        text,
        '''    await _discoverLocalMedia(db);\n\n    final rows = await db.query(\n''',
        '''    await _discoverLocalMedia(db);\n    // Hostinger recebe uma cópia de todas as mídias locais, inclusive daquelas\n    // que já possuem fileId no Drive. Falhas não bloqueiam o backup do Drive.\n    try {\n      await HostingerMediaService.uploadPending(limit: 40);\n    } catch (_) {}\n\n    final rows = await db.query(\n''',
        'upload primário Hostinger',
    )

    text = replace_once(
        text,
        '''    if (rows.isEmpty) throw StateError('Logo local não encontrada para envio.');\n    return _uploadSingleAsset(\n      appDb,\n      db,\n      Map<String, Object?>.from(rows.first),\n    );\n''',
        '''    if (rows.isEmpty) throw StateError('Logo local não encontrada para envio.');\n    final row = Map<String, Object?>.from(rows.first);\n    String hostingerId = '';\n    try {\n      hostingerId = await HostingerMediaService.uploadEntity(\n        companyId: cleanCompanyId,\n        entityType: 'company_logo',\n        entityId: cleanCompanyId,\n      );\n    } catch (_) {}\n    try {\n      return await _uploadSingleAsset(appDb, db, row);\n    } catch (_) {\n      // Se a Hostinger confirmou, a logo já está protegida online. O Drive será\n      // tentado novamente pela fila de sincronização sem perder o arquivo local.\n      if (hostingerId.isNotEmpty) return hostingerId;\n      rethrow;\n    }\n''',
        'logo imediata em armazenamento duplo',
    )

    text = replace_once(
        text,
        '''      where: 'drive_file_id IS NOT NULL AND drive_file_id <> ""',\n''',
        '''      where: 'company_id IS NOT NULL AND company_id <> "" '\n          'AND entity_type IS NOT NULL AND entity_type <> "" '\n          'AND entity_id IS NOT NULL AND entity_id <> "" '\n          'AND file_name IS NOT NULL AND file_name <> ""',\n''',
        'seleção de mídia para fallback duplo',
    )

    text = replace_once(
        text,
        '''      final companyId = '${row['company_id'] ?? ''}'.trim();\n      final fileId = '${row['drive_file_id'] ?? ''}'.trim();\n      if (companyId.isEmpty || fileId.isEmpty) continue;\n      try {\n        final response = await _post(<String, Object?>{\n          'action': 'media_download',\n          'syncKey': await appDb.getSetting('management_panel_sync_key'),\n          'authToken': AuthService.sessionToken,\n          'companyId': companyId,\n          'fileId': fileId,\n        });\n        final encoded = '${response['contentBase64'] ?? ''}'.trim();\n''',
        '''      final companyId = '${row['company_id'] ?? ''}'.trim();\n      final fileId = '${row['drive_file_id'] ?? ''}'.trim();\n      if (companyId.isEmpty) continue;\n      try {\n        Map<String, dynamic>? response;\n        // Recuperação principal: Hostinger. Se estiver indisponível, ausente ou\n        // ainda não configurada, o Drive existente permanece como fallback.\n        try {\n          response = await HostingerMediaService.downloadAsset(row);\n        } catch (_) {}\n        if (response == null && fileId.isNotEmpty) {\n          response = await _post(<String, Object?>{\n            'action': 'media_download',\n            'syncKey': await appDb.getSetting('management_panel_sync_key'),\n            'authToken': AuthService.sessionToken,\n            'companyId': companyId,\n            'fileId': fileId,\n          });\n        }\n        if (response == null) continue;\n        final encoded = '${response['contentBase64'] ?? ''}'.trim();\n''',
        'download Hostinger com fallback Drive',
    )

    text = replace_once(
        text,
        '''  static Future<void> clearCompanyLogo(String companyId) async {\n    if(companyId.trim().isEmpty) return;\n    final db=await AppDatabase.instance.database; final id=_assetId('company_logo',companyId);\n''',
        '''  static Future<void> clearCompanyLogo(String companyId) async {\n    if(companyId.trim().isEmpty) return;\n    try {\n      await HostingerMediaService.deleteAsset(\n        companyId: companyId,\n        entityType: 'company_logo',\n        entityId: companyId,\n      );\n    } catch (_) {}\n    final db=await AppDatabase.instance.database; final id=_assetId('company_logo',companyId);\n''',
        'remoção da logo na Hostinger',
    )
    path.write_text(text, encoding='utf-8')


def patch_version() -> None:
    pub = APP / 'pubspec.yaml'
    text = pub.read_text(encoding='utf-8')
    text = replace_once(text, 'version: 3.29.19+162', 'version: 3.29.20+163', 'versão')
    pub.write_text(text, encoding='utf-8')

    home = APP / 'lib/screens/home_screen.dart'
    text = home.read_text(encoding='utf-8')
    text = text.replace('Auditar SST • versão 3.29.19', 'Auditar SST • versão 3.29.20')
    text = text.replace('Auditar SST para Windows • versão 3.29.19', 'Auditar SST para Windows • versão 3.29.20')
    home.write_text(text, encoding='utf-8')


def validate() -> None:
    media = (APP / 'lib/services/media_sync_service.dart').read_text(encoding='utf-8')
    hostinger = (APP / 'lib/services/hostinger_media_service.dart').read_text(encoding='utf-8')
    device = (APP / 'lib/services/device_sync_service.dart').read_text(encoding='utf-8')
    checks = {
        'versão': 'version: 3.29.20+163' in (APP / 'pubspec.yaml').read_text(encoding='utf-8'),
        'config Hostinger': 'AUDITAR_MEDIA_HOSTINGER_URL' in hostinger and 'AUDITAR_MEDIA_HOSTINGER_KEY' in hostinger,
        'upload Hostinger': 'HostingerMediaService.uploadPending' in media,
        'download primário Hostinger': 'HostingerMediaService.downloadAsset' in media,
        'fallback Drive': "'action': 'media_download'" in media and "'drive_file_id'" in media,
        'upload Drive preservado': "'action': 'media_upload'" in media,
        'logo imediata': "entityType: 'company_logo'" in media and 'uploadCompanyLogoNow' in media,
        'sincronização estrutural preservada': 'device_sync_push' in device and 'device_sync_pull' in device,
        'IA Executivo preservada': 'Conversar com a IA sobre o Executivo' in (APP / 'lib/screens/report_screen.dart').read_text(encoding='utf-8'),
    }
    missing = [name for name, ok in checks.items() if not ok]
    if missing:
        raise RuntimeError('Validações v3.29.20 falharam: ' + ', '.join(missing))


def main() -> int:
    write_hostinger_service()
    patch_media_service()
    patch_version()
    validate()
    print('v3.29.20+163: Hostinger principal + Google Drive backup/fallback integrados.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

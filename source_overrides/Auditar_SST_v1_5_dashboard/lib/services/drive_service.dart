import 'dart:convert';
import 'dart:io';

import 'package:uuid/uuid.dart';

import '../database.dart';
import 'apps_script_http.dart';
import 'report_file_service.dart';

class DriveConnectResult {
  final String email;
  final String rootFolderId;

  const DriveConnectResult({
    required this.email,
    required this.rootFolderId,
  });
}

class DriveUploadResult {
  final bool uploaded;
  final bool queued;
  final String message;

  const DriveUploadResult({
    required this.uploaded,
    required this.queued,
    required this.message,
  });
}

class _DriveServiceException implements Exception {
  final String message;

  const _DriveServiceException(this.message);

  @override
  String toString() => message;
}

class DriveService {
  static const int _maxReportBytes = 20 * 1024 * 1024;

  static bool _isPermanentAppsScriptUrl(Uri uri) {
    return uri.scheme == 'https' &&
        uri.host == 'script.google.com' &&
        uri.path.startsWith('/macros/s/') &&
        uri.path.endsWith('/exec');
  }

  static Future<Map<String, dynamic>> _request(
    String action, {
    Map<String, Object?> payload = const {},
    Duration timeout = const Duration(seconds: 120),
  }) async {
    final db = AppDatabase.instance;
    final endpoint = (await db.getSetting(
      'management_panel_endpoint',
      fallback: '',
    ))
        .trim();
    final syncKey = (await db.getSetting(
      'management_panel_sync_key',
      fallback: '',
    ))
        .trim();

    if (endpoint.isEmpty || syncKey.isEmpty) {
      throw const _DriveServiceException(
        'Configure e salve primeiro a URL e a chave em Serviços web gratuitos.',
      );
    }

    final endpointUri = Uri.tryParse(endpoint);
    if (endpointUri == null || !_isPermanentAppsScriptUrl(endpointUri)) {
      throw const _DriveServiceException(
        'A URL salva não é a publicação permanente do Apps Script terminada em /exec.',
      );
    }

    final response = await AppsScriptHttp.postJson(
      endpointUri,
      <String, Object?>{
        'action': action,
        'syncKey': syncKey,
        ...payload,
      },
      timeout: timeout,
    );

    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw _DriveServiceException(
        'A Central Online respondeu com erro ${response.statusCode}.',
      );
    }

    Map<String, dynamic> body;
    try {
      body = jsonDecode(utf8.decode(response.bodyBytes))
          as Map<String, dynamic>;
    } catch (_) {
      throw const _DriveServiceException(
        'A Central Online retornou uma resposta inválida.',
      );
    }

    if (body['ok'] != true) {
      final message = '${body['message'] ?? 'Falha no Google Drive.'}';
      if (message == 'Requisição inválida.') {
        throw const _DriveServiceException(
          'Atualize o Código.gs da Central Online para a versão com Google Drive.',
        );
      }
      throw _DriveServiceException(message);
    }

    return body;
  }

  static Future<DriveConnectResult> connect() async {
    final response = await _request(
      'drive_connect',
      timeout: const Duration(seconds: 45),
    );
    final rootFolderId = '${response['folderId'] ?? ''}'.trim();
    if (rootFolderId.isEmpty) {
      throw const _DriveServiceException(
        'A Central Online não confirmou a pasta do Google Drive.',
      );
    }

    final accountLabel = '${response['accountLabel'] ?? ''}'.trim();
    final db = AppDatabase.instance;
    await db.setSetting('drive_enabled', 'true');
    await db.setSetting(
      'drive_account_email',
      accountLabel.isEmpty ? 'Drive da Central Online' : accountLabel,
    );
    await db.setSetting('drive_root_folder_id', rootFolderId);
    await db.setSetting('drive_auto_upload', 'true');

    return DriveConnectResult(
      email: accountLabel.isEmpty
          ? 'Drive da Central Online'
          : accountLabel,
      rootFolderId: rootFolderId,
    );
  }

  static Future<void> disconnect() async {
    final db = AppDatabase.instance;
    await db.setSetting('drive_enabled', 'false');
    await db.setSetting('drive_account_email', '');
    await db.setSetting('drive_root_folder_id', '');
  }

  static Future<String> _uploadLocalPdf({
    required String localPath,
    required String fileName,
    required String companyName,
    required bool interactive,
  }) async {
    final file = File(localPath);
    if (!await file.exists()) {
      throw const _DriveServiceException(
        'Arquivo local do relatório não encontrado.',
      );
    }

    final length = await file.length();
    if (length > _maxReportBytes) {
      throw const _DriveServiceException(
        'O relatório ultrapassa 20 MB e não pode ser enviado automaticamente.',
      );
    }

    final bytes = await file.readAsBytes();
    final response = await _request(
      'drive_upload',
      payload: <String, Object?>{
        'fileName': fileName,
        'companyName': companyName,
        'mimeType': 'application/pdf',
        'contentBase64': base64Encode(bytes),
      },
    );

    final fileId = '${response['fileId'] ?? ''}'.trim();
    if (fileId.isEmpty) {
      throw const _DriveServiceException(
        'O Google Drive não confirmou o envio do relatório.',
      );
    }

    return fileId;
  }

  static Future<DriveUploadResult> saveReportToDrive(
    String inspectionId, {
    bool interactive = true,
  }) async {
    final db = AppDatabase.instance;

    final enabled = await db.getSetting(
      'drive_enabled',
      fallback: 'false',
    );

    if (enabled != 'true') {
      return const DriveUploadResult(
        uploaded: false,
        queued: false,
        message: 'Google Drive não está vinculado.',
      );
    }

    final previous = await db.getDriveUploadForInspection(inspectionId);

    if (previous != null && previous['status'] == 'Enviado') {
      return const DriveUploadResult(
        uploaded: true,
        queued: false,
        message: 'Este relatório já foi salvo no Google Drive.',
      );
    }

    final header = await db.getInspectionHeader(inspectionId);

    if (header == null) {
      throw const _DriveServiceException('Vistoria não encontrada.');
    }

    final localPath = await ReportFileService.savePdfLocally(inspectionId);

    final fileName = File(localPath).uri.pathSegments.last;
    final companyName = '${header['company_name'] ?? 'Sem empresa'}';

    final queueId = previous == null ? const Uuid().v4() : '${previous['id']}';

    try {
      await _uploadLocalPdf(
        localPath: localPath,
        fileName: fileName,
        companyName: companyName,
        interactive: interactive,
      );

      if (previous == null) {
        await db.enqueueDriveUpload(
          id: queueId,
          inspectionId: inspectionId,
          localPath: localPath,
          fileName: fileName,
          companyName: companyName,
          status: 'Enviado',
        );
      } else {
        await db.markDriveUploadSent(queueId);
      }

      return const DriveUploadResult(
        uploaded: true,
        queued: false,
        message: 'Relatório salvo no Google Drive.',
      );
    } catch (e) {
      await db.enqueueDriveUpload(
        id: queueId,
        inspectionId: inspectionId,
        localPath: localPath,
        fileName: fileName,
        companyName: companyName,
        status: 'Pendente',
        lastError: e.toString(),
      );

      return const DriveUploadResult(
        uploaded: false,
        queued: true,
        message:
            'Sem conexão no momento. O relatório ficou salvo no celular e aguardará sincronização.',
      );
    }
  }

  static Future<int> syncPending({bool interactive = false}) async {
    final db = AppDatabase.instance;
    final rows = await db.getPendingDriveUploads();
    var sent = 0;

    for (final row in rows) {
      final id = '${row['id']}';

      try {
        await _uploadLocalPdf(
          localPath: '${row['local_path']}',
          fileName: '${row['file_name']}',
          companyName: '${row['company_name'] ?? 'Sem empresa'}',
          interactive: interactive,
        );

        await db.markDriveUploadSent(id);
        sent++;
      } catch (e) {
        await db.markDriveUploadFailed(id, e.toString());
      }
    }

    return sent;
  }
}

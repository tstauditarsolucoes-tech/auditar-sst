import 'dart:convert';
import 'dart:typed_data';

import 'package:uuid/uuid.dart';

import '../database.dart';
import 'apps_script_http.dart';
import 'auth_service.dart';
import 'report_email_service.dart';
import 'web_service_config.dart';

/// Isolated delivery catalogue and metadata history. No change to push/pull sync.
class DocumentDeliveryService {
  static String _historyKey(String companyId) => 'document_delivery_history_$companyId';

  static bool get _allowed => AuthService.isSignedIn &&
      AuthService.currentUser?.role.toLowerCase() != 'cliente';

  static Future<void> _remember(String companyId, Map<String, dynamic> entry) async {
    final db = AppDatabase.instance;
    final previous = await localHistory(companyId);
    previous.removeWhere((item) => item['requestId'] == entry['requestId']);
    previous.insert(0, entry);
    await db.setSetting(_historyKey(companyId), jsonEncode(previous.take(100).toList()));
  }

  static Future<List<Map<String, dynamic>>> localHistory(String companyId) async {
    if (!_allowed || !AuthService.canAccessCompany(companyId)) return <Map<String, dynamic>>[];
    final raw = await AppDatabase.instance.getSetting(_historyKey(companyId));
    try {
      final decoded = jsonDecode(raw);
      if (decoded is List) {
        return decoded.whereType<Map>().map((item) => Map<String, dynamic>.from(item)).toList();
      }
    } catch (_) {}
    return <Map<String, dynamic>>[];
  }

  /// A positive answer only means that the Central accepted the e-mail;
  /// actual final delivery still depends on the recipient's mail provider.
  static Future<String> send({
    required String companyId,
    required String companyName,
    required String documentId,
    required String category,
    required String title,
    required String to,
    required String cc,
    required String fileName,
    required Uint8List bytes,
  }) async {
    if (!_allowed || !AuthService.canAccessCompany(companyId)) {
      throw StateError('Acesso não autorizado para enviar documentos desta empresa.');
    }
    final requestId = const Uuid().v4();
    final record = <String, dynamic>{
      'requestId': requestId,
      'companyId': companyId,
      'documentId': documentId,
      'category': category,
      'title': title,
      'to': to,
      'cc': cc,
      'fileName': fileName,
      'createdAt': DateTime.now().toIso8601String(),
      'status': 'SENDING',
      'error': '',
    };
    try {
      final result = await ReportEmailService.send(
        companyId: companyId,
        companyName: companyName,
        inspectionId: documentId,
        requestId: requestId,
        to: to,
        cc: cc,
        fileName: fileName,
        bytes: bytes,
      );
      record['status'] = 'SENT';
      record['sentAt'] = DateTime.now().toIso8601String();
      try { await _remember(companyId, record); } catch (_) {}
      return result;
    } catch (error) {
      record['status'] = 'FAILED';
      record['error'] = '$error';
      try { await _remember(companyId, record); } catch (_) {}
      rethrow;
    }
  }

  static Future<List<Map<String, dynamic>>> history(String companyId) async {
    final cached = await localHistory(companyId);
    if (!_allowed || !AuthService.canAccessCompany(companyId)) return <Map<String, dynamic>>[];
    try {
      final db = AppDatabase.instance;
      final endpoint = (await db.getSetting('management_panel_endpoint',
        fallback: WebServiceConfig.endpoint)).trim();
      final key = (await db.getSetting('management_panel_sync_key',
        fallback: WebServiceConfig.syncKey)).trim();
      final uri = Uri.tryParse(endpoint);
      if (uri == null || uri.scheme != 'https' ||
          uri.host != 'script.google.com' || !uri.path.endsWith('/exec') ||
          key.isEmpty) return cached;
      final response = await AppsScriptHttp.postJson(uri, {
        'action': 'report_email_history',
        'authToken': AuthService.sessionToken,
        'syncKey': key,
        'companyId': companyId,
        'limit': 100,
      }, timeout: const Duration(seconds: 35));
      if (response.statusCode < 200 || response.statusCode >= 300) return cached;
      final decoded = jsonDecode(utf8.decode(response.bodyBytes));
      if (decoded is! Map || decoded['ok'] != true || decoded['items'] is! List) return cached;
      final fromCentral = <Map<String, dynamic>>[];
      for (final item in (decoded['items'] as List).whereType<Map>()) {
        fromCentral.add(Map<String, dynamic>.from(item));
      }
      final seen = <String>{};
      // Cached entries include human-friendly category/title. Keep those when the
      // central row is the same request ID but has only fixed legacy columns.
      return [...cached, ...fromCentral].where((item) {
        final id = '${item['requestId'] ?? ''}';
        return id.isNotEmpty && seen.add(id);
      }).toList()..sort((a, b) =>
          '${b['createdAt'] ?? ''}'.compareTo('${a['createdAt'] ?? ''}'));
    } catch (_) { return cached; }
  }
}
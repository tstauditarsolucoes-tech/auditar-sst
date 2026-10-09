import 'dart:convert';
import 'dart:typed_data';

import '../database.dart';
import '../models.dart';
import 'report_email_service.dart';

/// Local delivery ledger. The Central also records every accepted send in
/// EnviosRelatorios. This cache does not modify structured or media sync.
class DocumentDeliveryService {
  static String _key(String companyId) => 'document_delivery_history_v1_' + companyId;

  static Future<List<Map<String, dynamic>>> history(String companyId) async {
    final raw = await AppDatabase.instance.getSetting(_key(companyId));
    if (raw.isEmpty) return <Map<String, dynamic>>[];
    try {
      final data = jsonDecode(raw);
      return data is List
          ? data.whereType<Map>().map((item) => Map<String, dynamic>.from(item)).toList()
          : <Map<String, dynamic>>[];
    } catch (_) {
      return <Map<String, dynamic>>[];
    }
  }

  static Future<String> send({
    required Company company,
    required String documentId,
    required String documentType,
    required String title,
    required String fileName,
    required Uint8List bytes,
    required String to,
    required String cc,
  }) async {
    // The server is the authority for success: no SENT entry on failure.
    final message = await ReportEmailService.send(
      companyId: company.id,
      companyName: company.name,
      inspectionId: documentId,
      to: to,
      cc: cc,
      fileName: fileName,
      bytes: bytes,
    );
    final item = <String, dynamic>{
      'companyId': company.id,
      'documentId': documentId,
      'documentType': documentType,
      'title': title,
      'fileName': fileName,
      'to': to.trim(),
      'cc': cc.trim(),
      'sentAt': DateTime.now().toUtc().toIso8601String(),
      'status': 'SENT',
    };
    try {
      final records = await history(company.id);
      records.insert(0, item);
      await AppDatabase.instance.setSetting(
        _key(company.id), jsonEncode(records.take(300).toList()),
      );
    } catch (_) {
      // The Gmail send succeeded; local ledger failure cannot undo it.
    }
    return message;
  }
}

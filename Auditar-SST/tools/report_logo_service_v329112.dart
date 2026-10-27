import 'dart:async';
import 'dart:io';

import 'package:pdf/widgets.dart' as pw;

import '../database.dart';
import 'media_sync_service.dart';

/// Busca a logo no cadastro atual e, se necessário, tenta recuperar o backup.
/// Não altera a sincronização estruturada ou exclui informações da empresa.
class ReportLogoService {
  static final Set<String> _attemptedOnlineRecovery = <String>{};

  static Future<pw.MemoryImage?> forCompany(
    Map<String, Object?> header,
  ) async {
    final companyId = (header['company_id'] ?? '').toString().trim();
    final fromHeader = (header['company_logo_path'] ?? '').toString().trim();

    final first = await _localImage(fromHeader);
    if (first != null) return first;

    final companies = await AppDatabase.instance.getCompanies(onlyActive: false);
    for (final company in companies) {
      if (company.id != companyId) continue;
      final image = await _localImage(company.logoPath ?? '');
      if (image != null) return image;
      break;
    }

    if (companyId.isEmpty || !_attemptedOnlineRecovery.add(companyId)) {
      return null;
    }

    try {
      await MediaSyncService.restoreCompanyLogos(
        companyIds: <String>[companyId],
      ).timeout(const Duration(seconds: 6));

      final refreshed = await AppDatabase.instance.getCompanies(onlyActive: false);
      for (final company in refreshed) {
        if (company.id != companyId) continue;
        return await _localImage(company.logoPath ?? '');
      }
    } catch (_) {
      // Sem backup/rede: o cabeçalho mantém a imagem oficial de SST.
    }
    return null;
  }

  static Future<pw.MemoryImage?> _localImage(String path) async {
    if (path.trim().isEmpty) return null;
    try {
      final file = File(path);
      if (!await file.exists()) return null;
      final bytes = await file.readAsBytes();
      if (bytes.isEmpty) return null;
      return pw.MemoryImage(bytes);
    } catch (_) {
      return null;
    }
  }
}

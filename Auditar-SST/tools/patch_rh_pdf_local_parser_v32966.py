#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/Auditar_SST_v1_5_dashboard')
svc = root / 'lib/services/worker_import_service.dart'
text = svc.read_text(encoding='utf-8')

old = """        final normalized = _normalizeExtractedRhText(extracted);
        if (normalized.length >= 80) {
          uploadBytes = await _buildLightweightRhPdf(normalized);
        }
"""
new = """        final normalized = _normalizeExtractedRhText(extracted);
        if (normalized.length >= 80) {
          final localTable = _parseExtractedRhText(normalized);
          if (localTable != null) {
            return localTable;
          }
          uploadBytes = await _buildLightweightRhPdf(normalized);
        }
"""
if new not in text:
    if old not in text:
        raise SystemExit('Bloco de extracao local v3.29.65 nao encontrado.')
    text = text.replace(old, new, 1)

anchor = """  static Future<Uint8List> _buildLightweightRhPdf(String text) async {
"""
helper = r'''  static List<List<String>>? parseExtractedRhTextForTesting(String text) =>
      _parseExtractedRhText(text);

  static List<List<String>>? _parseExtractedRhText(String text) {
    final normalizedText = _normalizeExtractedRhText(text);
    if (normalizedText.isEmpty) return null;

    final expectedMatch = RegExp(
      r'Total\s+Geral\s*:\s*(\d+)\s+empregado',
      caseSensitive: false,
    ).firstMatch(normalizedText);
    final expectedTotal =
        expectedMatch == null ? null : int.tryParse(expectedMatch.group(1)!);

    final datePattern = RegExp(r'\b\d{2}/\d{2}/\d{4}\b');
    final allocationPattern = RegExp(r'\d{3}\.\d{2}\s*-\s*');

    final rows = <List<String>>[
      const ['Nome', 'Cargo', 'Setor'],
    ];
    final identities = <String>{};

    for (final rawLine in normalizedText.split('\n')) {
      final line = rawLine.replaceAll(RegExp(r'\s+'), ' ').trim();
      if (line.isEmpty) continue;

      final lower = line.toLowerCase();
      if (lower.startsWith('listagem de empregados') ||
          lower.startsWith('empresa:') ||
          lower.startsWith('mês/ano:') ||
          lower.startsWith('mes/ano:') ||
          lower.startsWith('nome admissao') ||
          lower.startsWith('nome admissão') ||
          lower.startsWith('total geral:') ||
          lower == 'continua...' ||
          lower == 'fim' ||
          lower == 'fortes pessoal') {
        continue;
      }

      final dateMatch = datePattern.firstMatch(line);
      if (dateMatch == null || dateMatch.start <= 1) continue;

      final name = line.substring(0, dateMatch.start).trim();
      final afterDate = line.substring(dateMatch.end).trim();
      if (name.length < 3 || afterDate.isEmpty) continue;

      final allocationMatch = allocationPattern.firstMatch(afterDate);
      if (allocationMatch == null) continue;

      final role = afterDate.substring(0, allocationMatch.start).trim();
      final sector = afterDate.substring(allocationMatch.start).trim();
      if (role.isEmpty || sector.isEmpty) continue;

      final identity = _normalize(name);
      if (identity.isEmpty || !identities.add(identity)) continue;

      rows.add([name, role, sector]);
    }

    final count = rows.length - 1;
    if (count < 2) return null;

    // Se o relatório trouxer total, a leitura local só é aceita se estiver completa.
    // Assim uma linha perdida jamais pode desativar trabalhador por engano.
    if (expectedTotal != null && expectedTotal > 0 && count != expectedTotal) {
      return null;
    }

    return rows;
  }

'''
if 'parseExtractedRhTextForTesting' not in text:
    if anchor not in text:
        raise SystemExit('Ancora helper PDF nao encontrada.')
    text = text.replace(anchor, helper + anchor, 1)

svc.write_text(text, encoding='utf-8', newline='\n')

pub = root / 'pubspec.yaml'
p = pub.read_text(encoding='utf-8')
p, n = re.subn(
    r'^version:\s*[^\n]+',
    'version: 3.29.66+208',
    p,
    count=1,
    flags=re.M,
)
if n != 1:
    raise SystemExit('Versao nao encontrada.')
pub.write_text(p, encoding='utf-8', newline='\n')

print('Android v3.29.66+208: leitura local deterministica da listagem RH aplicada.')

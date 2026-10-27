#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/Auditar_SST_v1_5_dashboard')
svc = root / 'lib/services/worker_import_service.dart'
text = svc.read_text(encoding='utf-8')

# Imports exclusivos da importacao RH local.
imports_anchor = "import 'package:file_picker/file_picker.dart';\n"
extra_imports = (
    "import 'package:file_picker/file_picker.dart';\n"
    "import 'package:read_pdf_text/read_pdf_text.dart';\n"
    "import 'package:pdf/widgets.dart' as pw;\n"
)
if "package:read_pdf_text/read_pdf_text.dart" not in text:
    if imports_anchor not in text:
        raise SystemExit('Import de file_picker nao encontrado.')
    text = text.replace(imports_anchor, extra_imports, 1)

# Passa o caminho local do arquivo para tentar extracao de texto no aparelho.
old = "    final table = await _readPdf(bytes);\n"
new = "    final table = await _readPdf(bytes, localPath: selected.path);\n"
if old in text:
    text = text.replace(old, new, 1)
elif new not in text:
    raise SystemExit('Chamada _readPdf nao encontrada.')

old_sig = "  static Future<List<List<String>>> _readPdf(Uint8List bytes) async {\n"
new_sig = (
    "  static Future<List<List<String>>> _readPdf(\n"
    "    Uint8List bytes, {\n"
    "    String? localPath,\n"
    "  }) async {\n"
)
if old_sig in text:
    text = text.replace(old_sig, new_sig, 1)
elif new_sig not in text:
    raise SystemExit('Assinatura _readPdf nao encontrada.')

# Antes de consultar a IA, tenta extrair texto no Android/iOS e gerar PDF leve.
try_anchor = "    try {\n      final response = await "
if "_buildLightweightRhPdf" not in text:
    idx = text.find(try_anchor, text.find("static Future<List<List<String>>> _readPdf"))
    if idx < 0:
        raise SystemExit('Inicio da chamada remota nao encontrado.')
    injection = """    Uint8List uploadBytes = bytes;
    if ((Platform.isAndroid || Platform.isIOS) &&
        localPath != null &&
        localPath.trim().isNotEmpty) {
      try {
        final extracted = await ReadPdfText.getPDFtext(localPath)
            .timeout(const Duration(seconds: 20));
        final normalized = _normalizeExtractedRhText(extracted);
        if (normalized.length >= 80) {
          uploadBytes = await _buildLightweightRhPdf(normalized);
        }
      } catch (_) {
        // PDF escaneado, protegido ou sem camada de texto: usa o original.
      }
    }

"""
    text = text[:idx] + injection + text[idx:]

# Troca apenas o base64 do documento para o PDF leve quando existir.
needle = "'document': 'data:application/pdf;base64,${base64Encode(bytes)}',"
replacement = "'document': 'data:application/pdf;base64,${base64Encode(uploadBytes)}',"
if needle in text:
    text = text.replace(needle, replacement, 1)
elif replacement not in text:
    raise SystemExit('Payload PDF nao encontrado.')

# Helper que compacta texto e recria um PDF pequeno usando dependencia ja existente.
helper_anchor = "  static Future<WorkerImportPreview> _prepare({\n"
helper = """  static String _normalizeExtractedRhText(String raw) {
    final lines = raw
        .replaceAll('\\r', '\\n')
        .split('\\n')
        .map((line) => line.replaceAll(RegExp(r'[ \\t]+'), ' ').trim())
        .where((line) => line.isNotEmpty)
        .toList();
    return lines.join('\\n');
  }

  static Future<Uint8List> _buildLightweightRhPdf(String text) async {
    final document = pw.Document(compress: true);
    final safe = text.replaceAll(
      RegExp(r'[^\\u0009\\u000A\\u000D\\u0020-\\u00FF]'),
      ' ',
    );
    document.addPage(
      pw.MultiPage(
        margin: const pw.EdgeInsets.all(18),
        build: (_) => [
          pw.Text(
            safe,
            style: const pw.TextStyle(
              fontSize: 7,
              lineSpacing: 1,
            ),
          ),
        ],
      ),
    );
    return Uint8List.fromList(await document.save());
  }

"""
if helper not in text:
    if helper_anchor not in text:
        raise SystemExit('Ancora _prepare nao encontrada.')
    text = text.replace(helper_anchor, helper + helper_anchor, 1)

svc.write_text(text, encoding='utf-8', newline='\n')

# Dependencia MIT para extracao local de texto via PDFBox Android.
pub = root / 'pubspec.yaml'
ptext = pub.read_text(encoding='utf-8')
if 'read_pdf_text:' not in ptext:
    dep_anchor = '  file_picker: ^10.3.8\n'
    if dep_anchor not in ptext:
        raise SystemExit('Dependencia file_picker nao encontrada.')
    ptext = ptext.replace(
        dep_anchor,
        dep_anchor + '  read_pdf_text: ^0.3.1\n',
        1,
    )
ptext, count = re.subn(
    r'^version:\s*[^\n]+',
    'version: 3.29.65+207',
    ptext,
    count=1,
    flags=re.M,
)
if count != 1:
    raise SystemExit('Versao nao encontrada no pubspec.')
pub.write_text(ptext, encoding='utf-8', newline='\n')

print('Android v3.29.65+207: texto do PDF extraido localmente e reenviado em PDF leve.')

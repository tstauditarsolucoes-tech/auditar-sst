#!/usr/bin/env python3
"""PDF issuance UI only. Never changes synchronization, GS, schema, or AI."""
from pathlib import Path
import hashlib
import sys

root = Path(sys.argv[1])
screen_path = root / "lib/screens/report_screen.dart"
file_path = root / "lib/services/report_file_service.dart"
protected_paths = [
    "lib/database.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/drive_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/services/ai_assistant_service.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
]
protected = {
    item: hashlib.sha256((root / item).read_bytes()).hexdigest()
    for item in protected_paths
}
screen = screen_path.read_text(encoding="utf-8")
service = file_path.read_text(encoding="utf-8")

def once(text, old, new, label):
    if text.count(old) != 1:
        raise RuntimeError("REPORT_PREFLIGHT: expected exactly one " + label)
    return text.replace(old, new, 1)

screen = once(screen, "import 'dart:async';",
              "import 'dart:async';\nimport 'dart:io';\nimport 'dart:typed_data';", "imports")
screen = once(screen, "  bool fullPdfBusy = false;",
    "  bool fullPdfBusy = false;\n  bool reportSaveBusy = false;\n"
    "  String reportProgress = '';\n"
    "  bool get _reportBusy => fullPdfBusy || executivePdfBusy || reportSaveBusy || emailBusy;",
    "busy state")

start = screen.index("  Future<void> _sharePdf({required bool executive}) async {")
end = screen.index("  Future<void> _sendReportByEmail() async {", start)
screen = screen[:start] + r'''  // The PDF generator has already attempted existing media restoration.
  // Missing evidence and incomplete findings must not go unnoticed.
  Future<bool> _reviewBeforeDelivery() async {
    final db = AppDatabase.instance;
    final header = await db.getInspectionHeader(widget.inspectionId);
    final answers = await db.getAnswers(widget.inspectionId);
    final warnings = <String>[];
    if (header == null) {
      warnings.add('Vistoria não encontrada.');
    } else if ((header['company_name'] ?? '').toString().trim().isEmpty) {
      warnings.add('Identificação da empresa não preenchida.');
    }
    if (answers.isEmpty) warnings.add('Nenhum item registrado na vistoria.');
    var missingEvidence = 0;
    var incompleteFindings = 0;
    for (final answer in answers) {
      final finding = answer.status == 'Não Conforme' || answer.status == 'Parcial';
      if (finding &&
          (answer.observation.trim().isEmpty ||
           answer.recommendation.trim().isEmpty)) {
        incompleteFindings++;
      }
      for (final photo in await db.getPhotosForAnswer(answer.id)) {
        if (photo.path.trim().isEmpty || !await File(photo.path).exists()) {
          missingEvidence++;
        }
      }
    }
    if (incompleteFindings > 0) {
      warnings.add(incompleteFindings.toString() +
          ' constatação(ões) sem descrição ou recomendação.');
    }
    if (missingEvidence > 0) {
      warnings.add(missingEvidence.toString() +
          ' fotografia(s) cadastrada(s) indisponíveis neste aparelho. '
          'Confira o backup antes de emitir.');
    }
    if (warnings.isEmpty) return true;
    if (!mounted) return false;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Conferência antes da emissão'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Confira estes pontos antes de enviar ao cliente:'),
              const SizedBox(height: 10),
              ...warnings.map((item) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text('• ' + item),
              )),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('Voltar e corrigir'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('Continuar ciente'),
          ),
        ],
      ),
    );
    return confirmed == true;
  }

  Future<Uint8List?> _prepareReport({required bool executive}) async {
    if (_reportBusy) return null;
    setState(() {
      if (executive) {
        executivePdfBusy = true;
      } else {
        fullPdfBusy = true;
      }
      reportProgress = 'Montando páginas e conferindo fotografias...';
    });
    try {
      final bytes = await PdfService.generateInspectionPdf(
        widget.inspectionId,
        executive: executive,
        includeActionPlan: includeActionPlan,
      );
      if (bytes.length < 1024 ||
          bytes[0] != 0x25 || bytes[1] != 0x50 ||
          bytes[2] != 0x44 || bytes[3] != 0x46) {
        throw StateError('O arquivo gerado não é um PDF válido.');
      }
      if (!mounted) return null;
      setState(() => reportProgress = 'Conferindo o relatório antes da emissão...');
      if (!await _reviewBeforeDelivery()) return null;
      return bytes;
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Não foi possível gerar o PDF: ' + error.toString()),
        ));
      }
      return null;
    } finally {
      if (mounted) {
        setState(() {
          if (executive) {
            executivePdfBusy = false;
          } else {
            fullPdfBusy = false;
          }
          reportProgress = '';
        });
      }
    }
  }

  Future<void> _sharePdf({required bool executive}) async {
    final bytes = await _prepareReport(executive: executive);
    if (bytes == null || !mounted) return;
    final filename = executive
        ? 'Relatorio_Executivo_Auditar_SST.pdf'
        : 'Relatorio_Completo_Auditar_SST.pdf';
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => Scaffold(
          appBar: AppBar(
            title: Text(executive
                ? 'Pré-visualização • Relatório Executivo'
                : 'Pré-visualização • Relatório Completo'),
          ),
          body: PdfPreview(
            build: (format) async => bytes,
            pdfFileName: filename,
            allowPrinting: true,
            allowSharing: true,
          ),
        ),
      ),
    );
  }

''' + screen[end:]
screen = once(screen,
    "  Future<void> _sendReportByEmail() async {\n    if (emailBusy) return;",
    "  Future<void> _sendReportByEmail() async {\n    if (emailBusy) return;\n    if (!await _reviewBeforeDelivery()) return;",
    "email preflight")

start = screen.index("  Future<void> _saveLocal({required bool executive}) async {")
end = screen.index("  Future<void> _saveReportPreferences({required bool value}) async {", start)
screen = screen[:start] + r'''  Future<void> _saveLocal({required bool executive}) async {
    final bytes = await _prepareReport(executive: executive);
    if (bytes == null || !mounted) return;
    setState(() {
      reportSaveBusy = true;
      reportProgress = 'Salvando relatório no aparelho...';
    });
    try {
      final path = await ReportFileService.savePdfLocally(
        widget.inspectionId,
        executive: executive,
        includeActionPlan: includeActionPlan,
        preparedBytes: bytes,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Relatório salvo: ' + path)),
      );
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Não foi possível salvar: ' + error.toString()),
        ));
      }
    } finally {
      if (mounted) {
        setState(() {
          reportSaveBusy = false;
          reportProgress = '';
        });
      }
    }
  }

''' + screen[end:]
screen = once(screen, "        children: [\n          _heroCard(conformity),",
    """        children: [
          if (_reportBusy) ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(reportProgress.isNotEmpty
                        ? reportProgress
                        : 'Preparando relatório. Aguarde...'),
                    const SizedBox(height: 8),
                    const LinearProgressIndicator(),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 10),
          ],
          _heroCard(conformity),""", "visible progress")
screen = once(screen, "busy: fullPdfBusy,\n            onShare:",
              "busy: _reportBusy,\n            onShare:", "full busy indicator")
screen = once(screen, "busy: executivePdfBusy,\n            onShare:",
              "busy: _reportBusy,\n            onShare:", "executive busy indicator")
screen = once(screen, "onPressed: onSave,\n                  icon: const Icon(Icons.download_outlined),",
              "onPressed: busy ? null : onSave,\n                  icon: const Icon(Icons.download_outlined),", "save gating")
screen = once(screen, "onPressed: emailBusy ? null : _sendReportByEmail,",
              "onPressed: _reportBusy ? null : _sendReportByEmail,", "email gating")

service = once(service, "import 'dart:io';",
               "import 'dart:io';\nimport 'dart:typed_data';", "file service import")
service = once(service, "    bool? includeActionPlan,\n  }) async {",
               "    bool? includeActionPlan,\n    Uint8List? preparedBytes,\n  }) async {",
               "prepared bytes parameter")
service = once(service, "    final bytes = await PdfService.generateInspectionPdf(",
               "    final bytes = preparedBytes ?? await PdfService.generateInspectionPdf(",
               "avoid double generation")

screen_path.write_text(screen, encoding="utf-8", newline="\n")
file_path.write_text(service, encoding="utf-8", newline="\n")
changed = [item for item, expected in protected.items()
           if hashlib.sha256((root / item).read_bytes()).hexdigest() != expected]
if changed:
    raise SystemExit("PROTECTED SYNC/GS/DB/AI FILE MODIFIED: " + repr(changed))
print("REPORT_PREVIEW_PREFLIGHT_ISOLATED_OK")

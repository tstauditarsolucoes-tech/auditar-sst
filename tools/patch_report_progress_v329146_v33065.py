#!/usr/bin/env python3
"""Auditar SST v3.29.146 / v3.30.65

Melhoria isolada da UX de geração de relatórios:
- progresso por etapas no card global;
- mantém exclusividade entre Relatório Completo e Executivo;
- não altera o gerador PDF, IA, sincronização, banco, autenticação, mídia,
  Drive ou Google Apps Script.
"""
from pathlib import Path
import hashlib
import sys

if len(sys.argv) < 3:
    raise SystemExit(
        "uso: patch_report_progress_v329146_v33065.py <APP_DIR> <android|windows>"
    )

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
if platform not in ("android", "windows"):
    raise SystemExit("plataforma invalida")


def read(rel):
    return (root / rel).read_text(encoding="utf-8")


def write(rel, value):
    (root / rel).write_text(value, encoding="utf-8", newline="\n")


protected = [
    "lib/database.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/auth_service.dart",
    "lib/services/drive_service.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/ai_assistant_service.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
    "painel_web_google_apps_script/ClientPortal.html",
    "painel_web_google_apps_script/ReportEmail.gs",
]
before = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected
}

rel = "lib/screens/report_screen.dart"
screen = read(rel)

for required in (
    "String? _activeReportFormat;",
    "busy: _activeReportFormat == 'full'",
    "busy: _activeReportFormat == 'executive'",
    "fullPdfBusy = !executive;",
    "executivePdfBusy = executive;",
):
    if required not in screen:
        raise RuntimeError("estado exclusivo de relatório ausente: " + required)

field_anchor = "  String reportProgress = '';\n"
if field_anchor not in screen:
    raise RuntimeError("reportProgress nao localizado")
if "int reportProgressStep = 0;" not in screen:
    screen = screen.replace(
        field_anchor,
        field_anchor + "  int reportProgressStep = 0;\n",
        1,
    )

prepare_anchor = "  Future<Uint8List?> _prepareReport({required bool executive}) async {\n"
helper = """  void _setReportProgress(int step, String message) {
    if (!mounted) return;
    final safeStep = step < 0 ? 0 : (step > 4 ? 4 : step);
    setState(() {
      reportProgressStep = safeStep;
      reportProgress = message;
    });
  }

"""
if helper.strip() not in screen:
    if prepare_anchor not in screen:
        raise RuntimeError("_prepareReport nao localizado")
    screen = screen.replace(prepare_anchor, helper + prepare_anchor, 1)

old_start = """    setState(() {
      _activeReportFormat = executive ? 'executive' : 'full';
      // Exclusividade real: limpa qualquer estado visual residual antes de iniciar.
      fullPdfBusy = !executive;
      executivePdfBusy = executive;
      reportProgress = 'Montando páginas e conferindo fotografias...';
    });
    try {
      final bytes = await PdfService.generateInspectionPdf("""
new_start = """    setState(() {
      _activeReportFormat = executive ? 'executive' : 'full';
      // Exclusividade real: limpa qualquer estado visual residual antes de iniciar.
      fullPdfBusy = !executive;
      executivePdfBusy = executive;
      reportProgressStep = 1;
      reportProgress = '1 de 4 • Preparando informações do relatório...';
    });
    try {
      await Future<void>.delayed(Duration.zero);
      _setReportProgress(2, '2 de 4 • Carregando fotos e evidências...');
      await Future<void>.delayed(Duration.zero);
      _setReportProgress(3, '3 de 4 • Montando páginas e finalizando o PDF...');
      final bytes = await PdfService.generateInspectionPdf("""
if old_start not in screen:
    raise RuntimeError("inicio atual de _prepareReport nao localizado")
screen = screen.replace(old_start, new_start, 1)

old_review = """      if (!mounted) return null;
      setState(
        () => reportProgress = 'Conferindo o relatório antes da emissão...',
      );
      if (!await _reviewBeforeDelivery()) return null;"""
new_review = """      if (!mounted) return null;
      _setReportProgress(
        4,
        '4 de 4 • Conferindo o relatório antes da emissão...',
      );
      if (!await _reviewBeforeDelivery()) return null;"""
if old_review not in screen:
    raise RuntimeError("etapa de conferencia atual nao localizada")
screen = screen.replace(old_review, new_review, 1)

old_final = """          fullPdfBusy = false;
          executivePdfBusy = false;
          _activeReportFormat = null;
          reportProgress = '';"""
new_final = """          fullPdfBusy = false;
          executivePdfBusy = false;
          _activeReportFormat = null;
          reportProgressStep = 0;
          reportProgress = '';"""
if old_final not in screen:
    raise RuntimeError("limpeza final de progresso nao localizada")
screen = screen.replace(old_final, new_final, 1)

old_indicator = "                    const LinearProgressIndicator(),"
new_indicator = """                    LinearProgressIndicator(
                      value:
                          reportProgressStep > 0
                              ? reportProgressStep / 4
                              : null,
                    ),"""
if old_indicator not in screen:
    raise RuntimeError("barra de progresso global nao localizada")
screen = screen.replace(old_indicator, new_indicator, 1)

write(rel, screen)

rel = "pubspec.yaml"
pub = read(rel)
old_version, new_version = (
    ("3.29.145+287", "3.29.146+288")
    if platform == "android"
    else ("3.30.64+251", "3.30.65+252")
)
marker = "version: " + old_version
if pub.count(marker) != 1:
    raise RuntimeError("versao esperada ausente: " + old_version)
write(rel, pub.replace(marker, "version: " + new_version, 1))

changed = [
    name
    for name, digest in before.items()
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

report = read("lib/screens/report_screen.dart")
for required in (
    "int reportProgressStep = 0;",
    "void _setReportProgress(int step, String message)",
    "1 de 4 • Preparando informações do relatório...",
    "2 de 4 • Carregando fotos e evidências...",
    "3 de 4 • Montando páginas e finalizando o PDF...",
    "4 de 4 • Conferindo o relatório antes da emissão...",
    "reportProgressStep / 4",
    "busy: _activeReportFormat == 'full'",
    "busy: _activeReportFormat == 'executive'",
):
    assert required in report, required
assert "version: " + new_version in read("pubspec.yaml")

print("REPORT_STAGED_PROGRESS_OK", platform, new_version)
print("REPORT_EXCLUSIVE_LOADING_PRESERVED_OK")
print("SYNC_DB_AUTH_MEDIA_AI_DRIVE_GS_BYTE_IDENTICAL_OK")

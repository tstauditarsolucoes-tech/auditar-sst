#!/usr/bin/env python3
"""Auditar SST v3.29.142 / v3.30.61

Fix isolated to report_screen.dart:
- exactly one report format can display "Gerando..." at a time;
- stale booleans are cleared at operation start/end;
- inactive format is disabled but keeps its normal label.

Does not modify AI, synchronization, database, auth, media, Drive, or Apps Script.
"""
from pathlib import Path
import hashlib
import re
import sys

if len(sys.argv) < 3:
    raise SystemExit("uso: patch_report_busy_exclusive_v329142_v33061.py <APP_DIR> <android|windows>")

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
]
before = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected
}

rel = "lib/screens/report_screen.dart"
screen = read(rel)

# Add an explicit source of truth for which card owns the visual progress state.
field_anchor = "  String reportProgress = '';\n"
if field_anchor not in screen:
    raise RuntimeError("reportProgress nao localizado")
if "String? _activeReportFormat;" not in screen:
    screen = screen.replace(
        field_anchor,
        field_anchor + "  String? _activeReportFormat;\n",
        1,
    )

# The actual generator must always start with mutually-exclusive booleans.
start = screen.find("  Future<Uint8List?> _prepareReport({required bool executive}) async {")
end = screen.find("  Future<void> _sharePdf({required bool executive}) async {", start)
if start < 0 or end < 0:
    raise RuntimeError("_prepareReport nao localizado")
method = screen[start:end]

old_start = """    setState(() {
      if (executive) {
        executivePdfBusy = true;
      } else {
        fullPdfBusy = true;
      }
      reportProgress = 'Montando páginas e conferindo fotografias...';
    });"""
new_start = """    setState(() {
      _activeReportFormat = executive ? 'executive' : 'full';
      // Exclusividade real: limpa qualquer estado visual residual antes de iniciar.
      fullPdfBusy = !executive;
      executivePdfBusy = executive;
      reportProgress = 'Montando páginas e conferindo fotografias...';
    });"""
if old_start not in method:
    raise RuntimeError("inicio do estado de geracao nao localizado")
method = method.replace(old_start, new_start, 1)

old_final = """        setState(() {
          if (executive) {
            executivePdfBusy = false;
          } else {
            fullPdfBusy = false;
          }
          reportProgress = '';
        });"""
new_final = """        setState(() {
          // Sempre zera os dois estados. Nenhum card pode herdar loading anterior.
          fullPdfBusy = false;
          executivePdfBusy = false;
          _activeReportFormat = null;
          reportProgress = '';
        });"""
if old_final not in method:
    raise RuntimeError("fim do estado de geracao nao localizado")
method = method.replace(old_final, new_final, 1)
screen = screen[:start] + method + screen[end:]

# Visual state comes only from the explicit active format, never from stale booleans.
pairs = [
    (
        "busy: fullPdfBusy,\n            disabled: _reportBusy && !fullPdfBusy,",
        "busy: _activeReportFormat == 'full',\n"
        "            disabled: _reportBusy && _activeReportFormat != 'full',",
    ),
    (
        "busy: executivePdfBusy,\n            disabled: _reportBusy && !executivePdfBusy,",
        "busy: _activeReportFormat == 'executive',\n"
        "            disabled: _reportBusy && _activeReportFormat != 'executive',",
    ),
]
for old, new in pairs:
    if old not in screen:
        raise RuntimeError("card de relatorio esperado nao localizado: " + old.split(",")[0])
    screen = screen.replace(old, new, 1)

write(rel, screen)

# Version only; no migration.
rel = "pubspec.yaml"
pub = read(rel)
old_version, new_version = (
    ("3.29.141+283", "3.29.142+284")
    if platform == "android"
    else ("3.30.60+247", "3.30.61+248")
)
marker = "version: " + old_version
if pub.count(marker) != 1:
    raise RuntimeError("versao esperada ausente: " + old_version)
pub = pub.replace(marker, "version: " + new_version, 1)
write(rel, pub)

changed = [
    name for name, digest in before.items()
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

report = read("lib/screens/report_screen.dart")
assert "String? _activeReportFormat;" in report
assert "fullPdfBusy = !executive;" in report
assert "executivePdfBusy = executive;" in report
assert "fullPdfBusy = false;" in report
assert "executivePdfBusy = false;" in report
assert "_activeReportFormat = null;" in report
assert "busy: _activeReportFormat == 'full'" in report
assert "busy: _activeReportFormat == 'executive'" in report
assert "disabled: _reportBusy && _activeReportFormat != 'full'" in report
assert "disabled: _reportBusy && _activeReportFormat != 'executive'" in report
assert "busy: fullPdfBusy" not in report
assert "busy: executivePdfBusy" not in report
assert "version: " + new_version in read("pubspec.yaml")

print("REPORT_BUSY_EXCLUSIVE_OK", platform, new_version)
print("SYNC_DB_AUTH_MEDIA_AI_GS_BYTE_IDENTICAL_OK")

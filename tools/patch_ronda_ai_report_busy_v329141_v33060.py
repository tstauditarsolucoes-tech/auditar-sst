#!/usr/bin/env python3
"""Auditar SST v3.29.141 / v3.30.60

Fixes two isolated regressions:
1) Ronda photo AI: prefer the fast checklist_photo route that previously
   responded quickly, with the dedicated safety_observation_photo route kept
   as fallback. The user's photo is still the evidence sent to AI.
2) Report screen: "Relatório Completo" and "Relatório Executivo" no longer
   share the same visual loading flag. Generating one format only marks that
   format as "Gerando...".

Protected byte-for-byte: sync, database, auth, transport, media, Drive and all
Google Apps Script files.
"""
from pathlib import Path
import hashlib
import sys

if len(sys.argv) < 3:
    raise SystemExit(
        "uso: patch_ronda_ai_report_busy_v329141_v33060.py "
        "<APP_DIR> <android|windows>"
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
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
]
before = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected
}

# ---------------------------------------------------------------------------
# 1) Ronda photo AI: restore the fast proven checklist photo route first.
# ---------------------------------------------------------------------------
rel = "lib/services/ai_assistant_service.dart"
source = read(rel)
method_start = source.find(
    "  static Future<AiAssistantReply> analyzeSafetyObservationPhoto({"
)
method_end = source.find(
    "  static Future<AiAssistantReply> reviewExpressRound(", method_start
)
if method_start < 0 or method_end < 0:
    raise RuntimeError("analyzeSafetyObservationPhoto nao localizado")

method = source[method_start:method_end]

# Accept only the current v3.29.140 / v3.30.59 shape.
if "'mode': 'safety_observation_photo'" not in method:
    raise RuntimeError("rota dedicada atual da Ronda nao localizada")
if "'rondaDeferred': false" not in method:
    raise RuntimeError("Ronda atual nao esta no caminho rapido esperado")
if "'mode': 'checklist_photo'" in method:
    raise RuntimeError("Ronda ja possui fallback checklist; revisar antes de reaplicar")

call_start = method.find("    final reply = await _send({")
if call_start < 0:
    raise RuntimeError("chamada _send da IA foto nao localizada")

call_end = method.find("\n    });", call_start)
if call_end < 0:
    raise RuntimeError("fim da chamada _send da IA foto nao localizado")
call_end += len("\n    });")
original_call = method[call_start:call_end]

if original_call.count("'mode': 'safety_observation_photo'") != 1:
    raise RuntimeError("payload da IA foto inesperado")

fast_call = original_call.replace(
    "    final reply = await _send({",
    "    final fastReply = await _send({",
    1,
).replace(
    "'mode': 'safety_observation_photo'",
    "'mode': 'checklist_photo'",
    1,
)

fallback_call = original_call.replace(
    "    final reply = await _send({",
    "      reply = await _send({",
    1,
)
fallback_call = "\n".join(
    ("  " + line if line.strip() else line)
    for line in fallback_call.splitlines()
)

replacement = fast_call + r"""

    AiAssistantReply reply = fastReply;
    final fastDescription =
        '${fastReply.result['description'] ?? ''}'.trim();

    // The checklist photo route was the fast, stable field path used before.
    // Keep the dedicated Ronda route only as a fallback so a temporary
    // backend mismatch does not block photo analysis in the field.
    if (!fastReply.success || fastDescription.isEmpty) {
""" + fallback_call + r"""
    }
"""

method = method[:call_start] + replacement + method[call_end:]
source = source[:method_start] + method + source[method_end:]
write(rel, source)

# ---------------------------------------------------------------------------
# 2) Report UI: each card owns its visual busy flag.
# ---------------------------------------------------------------------------
rel = "lib/screens/report_screen.dart"
screen = read(rel)

old_full = "busy: _reportBusy,\n            onShare:"
old_exec = "busy: _reportBusy,\n            onShare:"

# Both cards were intentionally changed to _reportBusy by v3.29.124.
# Restore them in order: first card = full, second card = executive.
first = screen.find(old_full)
if first < 0:
    raise RuntimeError("busy compartilhado do Relatorio Completo nao localizado")
screen = (
    screen[:first]
    + "busy: fullPdfBusy,\n            onShare:"
    + screen[first + len(old_full):]
)

second = screen.find(old_exec, first + 1)
if second < 0:
    raise RuntimeError("busy compartilhado do Relatorio Executivo nao localizado")
screen = (
    screen[:second]
    + "busy: executivePdfBusy,\n            onShare:"
    + screen[second + len(old_exec):]
)

# Keep the global _reportBusy guard for concurrency and e-mail/save safety.
if "bool get _reportBusy =>" not in screen:
    raise RuntimeError("trava global de relatorios ausente")
write(rel, screen)

# ---------------------------------------------------------------------------
# 3) Version bump only. No migration.
# ---------------------------------------------------------------------------
rel = "pubspec.yaml"
pub = read(rel)
old_version, new_version = (
    ("3.29.140+282", "3.29.141+283")
    if platform == "android"
    else ("3.30.59+246", "3.30.60+247")
)
marker = "version: " + old_version
if "version: " + new_version not in pub:
    if pub.count(marker) != 1:
        raise RuntimeError("versao esperada ausente: " + old_version)
    pub = pub.replace(marker, "version: " + new_version, 1)
write(rel, pub)

# ---------------------------------------------------------------------------
# Mandatory guards
# ---------------------------------------------------------------------------
changed = [
    name
    for name, digest in before.items()
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit(
        "PROTECTED_SYNC_DB_AUTH_MEDIA_GS_MODIFIED: " + repr(changed)
    )

ai = read("lib/services/ai_assistant_service.dart")
report = read("lib/screens/report_screen.dart")

a = ai.find("  static Future<AiAssistantReply> analyzeSafetyObservationPhoto({")
b = ai.find("  static Future<AiAssistantReply> reviewExpressRound(", a)
photo_method = ai[a:b]
assert photo_method.find("'mode': 'checklist_photo'") >= 0
assert photo_method.find("'mode': 'safety_observation_photo'") >= 0
assert photo_method.find("'mode': 'checklist_photo'") < photo_method.find(
    "'mode': 'safety_observation_photo'"
)
assert "final fastDescription" in photo_method
assert "busy: fullPdfBusy" in report
assert "busy: executivePdfBusy" in report
assert report.count("busy: _reportBusy") == 0
assert "bool get _reportBusy =>" in report
assert "version: " + new_version in read("pubspec.yaml")

print("RONDA_AI_FAST_PRIMARY_WITH_FALLBACK_OK", platform, new_version)
print("REPORT_FORMAT_BUSY_STATE_SEPARATED_OK")
print("SYNC_DB_AUTH_MEDIA_GS_BYTE_IDENTICAL_OK")

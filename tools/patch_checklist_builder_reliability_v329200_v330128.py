#!/usr/bin/env python3
"""Repair checklist-builder AI timeout and UI recovery without touching core services."""
from pathlib import Path
import hashlib
import re
import sys

if len(sys.argv) < 3:
    raise SystemExit("uso: patch_checklist_builder_reliability_v329200_v330128.py <APP_DIR> <android|windows>")

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
if platform not in ("android", "windows"):
    raise SystemExit("plataforma invalida")

def read(rel):
    return (root / rel).read_text(encoding="utf-8")

def write(rel, value):
    (root / rel).write_text(value, encoding="utf-8", newline="\n")

def replace_once(text, old, new, label):
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: esperado 1 marcador, encontrado {count}")
    return text.replace(old, new, 1)

protected = [
    "lib/database.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/auth_service.dart",
    "lib/services/drive_service.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
    "painel_web_google_apps_script/ClientPortal.html",
    "painel_web_google_apps_script/ReportEmail.gs",
]
before = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in protected}

# Checklist creation may need longer than the default 65 seconds. Only this
# AI mode gets a 120-second window; photo analysis keeps its existing limits.
rel = "lib/services/ai_assistant_service.dart"
ai = read(rel)
timeout_pattern = re.compile(
    r"    final requestTimeout\s*=\s*rondaDeferred\s*\?\s*const Duration\(seconds:\s*90\)"
    r"\s*:\s*aiMode == 'checklist_photo'\s*\|\|\s*aiMode == 'safety_observation_photo'"
    r"\s*\?\s*const Duration\(seconds:\s*50\)"
    r"\s*:\s*aiMode == 'report_review_chat'\s*\?\s*const Duration\(seconds:\s*75\)"
    r"\s*:\s*const Duration\(seconds:\s*65\);",
    re.S,
)
new_timeout = """    final requestTimeout =
        rondaDeferred
            ? const Duration(seconds: 90)
            : aiMode == 'checklist_builder'
                ? const Duration(seconds: 120)
                : aiMode == 'checklist_photo' ||
                    aiMode == 'safety_observation_photo'
                ? const Duration(seconds: 50)
                : aiMode == 'report_review_chat'
                    ? const Duration(seconds: 75)
                    : const Duration(seconds: 65);"""
ai, count = timeout_pattern.subn(lambda _: new_timeout, ai, count=1)
if count != 1:
    if "aiMode == 'checklist_builder'" not in ai or "const Duration(seconds: 120)" not in ai:
        raise RuntimeError("timeout seletivo da IA não localizado; fonte-base inesperada")

old_timeout_reply = """          return const AiAssistantReply(
            success: false,
            message:
                'A análise da foto demorou além do limite da IA. O registro continua salvo; tente novamente em alguns instantes.',
          );"""
new_timeout_reply = """          if (aiMode == 'checklist_builder') {
            return const AiAssistantReply(
              success: false,
              message:
                  'A criação do checklist com IA demorou mais que o limite. Nenhum checklist foi salvo. Aguarde alguns instantes e tente novamente com uma descrição mais curta.',
            );
          }
          return const AiAssistantReply(
            success: false,
            message:
                'A análise da foto demorou além do limite da IA. O registro continua salvo; tente novamente em alguns instantes.',
          );"""
ai = replace_once(ai, old_timeout_reply, new_timeout_reply, "mensagem de timeout específica do criador")
write(rel, ai)

# Clear an old SnackBar (for example from photo analysis) when opening the
# checklist-builder dialog so it cannot be mistaken for the current operation.
rel = "lib/screens/checklist_templates_screen.dart"
screen = read(rel)
start = screen.find("  Future<void> _createChecklistWithAi() async {")
if start < 0:
    raise RuntimeError("método _createChecklistWithAi não localizado")
end = screen.find("  Future<void> _addTemplate() async {", start)
if end < 0:
    raise RuntimeError("fim do método do criador de checklist não localizado")
method = screen[start:end]
if "ScaffoldMessenger.of(context).clearSnackBars();" not in method:
    method = method.replace(
        "  Future<void> _createChecklistWithAi() async {\n",
        "  Future<void> _createChecklistWithAi() async {\n"
        "    ScaffoldMessenger.of(context).clearSnackBars();\n",
        1,
    )

call_pattern = re.compile(
    r"    setState\(\(\) => generatingWithAi = true\);\s*"
    r"final reply\s*=\s*await\s*AiAssistantService\.createChecklist\(request:\s*request\);\s*"
    r"if \(!mounted\) return;\s*"
    r"setState\(\(\) => generatingWithAi = false\);",
    re.S,
)
new_call = """    setState(() => generatingWithAi = true);
    AiAssistantReply reply;
    try {
      reply = await AiAssistantService.createChecklist(request: request);
    } catch (_) {
      if (!mounted) return;
      setState(() => generatingWithAi = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Não foi possível concluir a criação do checklist. Nada foi salvo. Confira a conexão e tente novamente.',
          ),
        ),
      );
      return;
    }
    if (!mounted) return;
    setState(() => generatingWithAi = false);"""
method, count = call_pattern.subn(lambda _: new_call, method, count=1)
if count != 1:
    if "AiAssistantReply reply;" not in method or "Não foi possível concluir a criação do checklist." not in method:
        raise RuntimeError("chamada do criador de checklist não localizada")
screen = screen[:start] + method + screen[end:]
write(rel, screen)

# Version candidates only; no migration, no production publish.
rel = "pubspec.yaml"
pub = read(rel)
old_version, new_version = (
    ("3.29.199+341", "3.29.200+342")
    if platform == "android"
    else ("3.30.127+314", "3.30.128+315")
)
if f"version: {new_version}" not in pub:
    pub = replace_once(pub, f"version: {old_version}", f"version: {new_version}", "versão-base")
write(rel, pub)

changed = [
    name for name, digest in before.items()
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

ai = read("lib/services/ai_assistant_service.dart")
screen = read("lib/screens/checklist_templates_screen.dart")
assert "aiMode == 'checklist_builder'" in ai
assert "const Duration(seconds: 120)" in ai
assert "A criação do checklist com IA demorou mais que o limite." in ai
assert "A análise da foto demorou além do limite da IA." in ai
assert "ScaffoldMessenger.of(context).clearSnackBars();" in screen
assert "AiAssistantReply reply;" in screen
assert "Não foi possível concluir a criação do checklist." in screen
assert f"version: {new_version}" in read("pubspec.yaml")
print("CHECKLIST_BUILDER_RELIABILITY_OK", platform, new_version)
print("SYNC_DB_AUTH_HTTP_MEDIA_DRIVE_APPS_SCRIPT_BYTE_IDENTICAL_OK")

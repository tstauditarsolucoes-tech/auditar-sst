#!/usr/bin/env python3
"""Auditar SST v3.29.150 / v3.30.69

Correções estritamente visuais:
- Central de documentos: título compacto e "Histórico de envios" responsivo;
- Central Inteligente: contraste explícito das abas do AppBar.

Não altera sincronização, banco, autenticação, transporte, mídia, IA ou Apps Script.
"""
from pathlib import Path
import hashlib
import sys

if len(sys.argv) < 3:
    raise SystemExit(
        "uso: patch_visual_polish_v329150_v33069.py <APP_DIR> <android|windows>"
    )

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
if platform not in ("android", "windows"):
    raise SystemExit("plataforma invalida")

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

def read(rel):
    return (root / rel).read_text(encoding="utf-8")

def write(rel, value):
    (root / rel).write_text(value, encoding="utf-8", newline="\n")

def replace_once(text, old, new, label):
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: esperado 1, encontrado {count}")
    return text.replace(old, new, 1)

# Central de documentos: evitar corte do título e do chip em telas estreitas.
rel = "lib/screens/document_dispatch_center_screen.dart"
doc = read(rel)
doc = replace_once(
    doc,
    "appBar:AppBar(title:const Text('Central de documentos e envios'),actions:[",
    "appBar:AppBar(title:const Text('Central de documentos'),actions:[",
    "titulo central documentos",
)
doc = replace_once(
    doc,
    "Expanded(child:ChoiceChip(label:const Text('Histórico de envios'),selected:showHistory,",
    "Expanded(child:ChoiceChip(label:const FittedBox(fit:BoxFit.scaleDown,child:Text('Histórico de envios')),selected:showHistory,",
    "chip historico responsivo",
)
write(rel, doc)

# Central Inteligente: as abas ficam legíveis sobre o AppBar azul.
rel = "lib/screens/field_intelligence_center_screen.dart"
field = read(rel)
field = replace_once(
    field,
    """        bottom: TabBar(
          controller: tabs,
          isScrollable: true,
          tabs: [""",
    """        bottom: TabBar(
          controller: tabs,
          isScrollable: true,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          indicatorColor: Colors.white,
          indicatorWeight: 3,
          tabs: [""",
    "contraste abas central inteligente",
)
write(rel, field)

# Versão isolada para esta revisão visual.
pub_rel = "pubspec.yaml"
pub = read(pub_rel)
old_release, new_release = (
    ("3.29.149+291", "3.29.150+292")
    if platform == "android"
    else ("3.30.68+255", "3.30.69+256")
)
marker = "version: " + old_release
if pub.count(marker) != 1:
    raise RuntimeError("versao esperada ausente: " + old_release)
write(pub_rel, pub.replace(marker, "version: " + new_release, 1))

changed = [
    name
    for name, digest in before.items()
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

print("VISUAL_POLISH_OK", platform, new_release)
print("SYNC_DB_AUTH_MEDIA_AI_DRIVE_GS_BYTE_IDENTICAL_OK")

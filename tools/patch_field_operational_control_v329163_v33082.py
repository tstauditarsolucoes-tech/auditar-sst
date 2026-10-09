#!/usr/bin/env python3
"""Auditar SST v3.29.163 / v3.30.82 — controle operacional de campo.

Adiciona somente UI/leitura:
- indicador Online/Offline discreto na Home;
- central de pendências;
- acesso consolidado ao plano de ação;
- Antes x Depois e recorrências já existentes;
- roteiro "O que conferir hoje".

Não altera schema, sincronização, autenticação, IA, mídia, Drive ou Apps Script.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv) < 3:
    raise SystemExit(
        "uso: patch_field_operational_control_v329163_v33082.py "
        "<APP_DIR> <android|windows>"
    )

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
repo = Path(__file__).resolve().parents[1]
if platform not in ("android", "windows"):
    raise SystemExit("plataforma invalida")


def read(rel):
    return (root / rel).read_text(encoding="utf-8")


def write(rel, value):
    (root / rel).write_text(value, encoding="utf-8", newline="\n")


def once(text, old, new, label):
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: esperado 1, encontrado {count}")
    return text.replace(old, new, 1)


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

copies = [
    (
        "feature_sources/field_operational_priority_service_v329163.dart",
        "lib/services/field_operational_priority_service.dart",
    ),
    (
        "feature_sources/field_connectivity_badge_v329163.dart",
        "lib/widgets/field_connectivity_badge.dart",
    ),
    (
        "feature_sources/field_operational_control_screen_v329163.dart",
        "lib/screens/field_operational_control_screen.dart",
    ),
    (
        "feature_sources/field_operational_priority_test_v329163.dart",
        "test/field_operational_priority_test.dart",
    ),
]
for source, target in copies:
    src = repo / source
    dst = root / target
    if not src.exists():
        raise RuntimeError("fonte ausente: " + source)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)

# Central Inteligente: atalho e um único card de entrada, sem duplicar telas.
rel = "lib/screens/field_intelligence_center_screen.dart"
s = read(rel)

if "import 'field_operational_control_screen.dart';" not in s:
    if "import 'correction_evidence_center_screen.dart';\n" in s:
        s = s.replace(
            "import 'correction_evidence_center_screen.dart';\n",
            "import 'correction_evidence_center_screen.dart';\n"
            "import 'field_operational_control_screen.dart';\n",
            1,
        )
    elif "import 'evidence_backup_screen.dart';\n" in s:
        s = s.replace(
            "import 'evidence_backup_screen.dart';\n",
            "import 'evidence_backup_screen.dart';\n"
            "import 'field_operational_control_screen.dart';\n",
            1,
        )
    else:
        raise RuntimeError("import anchor da Central ausente")

shortcut_anchor = "  List<_Shortcut> get shortcuts => [\n"
shortcut_block = """  List<_Shortcut> get shortcuts => [
    _Shortcut(
      'control',
      'Controle operacional',
      Icons.rule_folder_outlined,
      () => FieldOperationalControlScreen(
        initialCompanyId: selectedCompanyId ?? '',
      ),
    ),
"""
if "'control'," not in s:
    s = once(
        s,
        shortcut_anchor,
        shortcut_block,
        "atalho controle operacional",
    )

if "Online/Offline, pendências" not in s:
    today_pos = s.find("  Widget todayTab() {")
    if today_pos < 0:
        raise RuntimeError("metodo todayTab ausente")
    children_pos = s.find("children: [", today_pos)
    if children_pos < 0:
        raise RuntimeError("lista todayTab ausente")
    insert_pos = s.find("\n", children_pos)
    if insert_pos < 0:
        raise RuntimeError("linha todayTab ausente")
    insert_pos += 1
    control_card = """          Card(
            child: ListTile(
              leading: const Icon(Icons.rule_folder_outlined),
              title: const Text(
                'Controle operacional de campo',
                style: TextStyle(fontWeight: FontWeight.w900),
              ),
              subtitle: const Text(
                'Online/Offline, pendências, plano de ação, Antes × Depois, recorrências e roteiro da visita.',
              ),
              trailing: const Icon(Icons.chevron_right_rounded),
              onTap: () => openPage(
                FieldOperationalControlScreen(
                  initialCompanyId: selectedCompanyId ?? '',
                ),
              ),
            ),
          ),
          const SizedBox(height: 10),
"""
    s = s[:insert_pos] + control_card + s[insert_pos:]

for old_diag in (
    "final version = Platform.isWindows ? '3.30.66' : '3.29.147';",
    "final version = Platform.isWindows ? '3.30.68' : '3.29.149';",
):
    if old_diag in s:
        s = s.replace(
            old_diag,
            "final version = Platform.isWindows ? '3.30.82' : '3.29.163';",
            1,
        )
        break
write(rel, s)

# Home: indicador discreto de conectividade, sem substituir o status de sync.
rel = "lib/screens/home_screen.dart"
s = read(rel)
if "field_connectivity_badge.dart" not in s:
    anchor = "import 'field_intelligence_center_screen.dart';\n"
    if anchor not in s:
        raise RuntimeError("import da Central na Home ausente")
    s = s.replace(
        anchor,
        anchor + "import '../widgets/field_connectivity_badge.dart';\n",
        1,
    )

if "const FieldConnectivityBadge()," not in s:
    actions_anchor = """        actions: [
          IconButton(
            tooltip: 'Busca global',
"""
    actions_new = """        actions: [
          const FieldConnectivityBadge(),
          IconButton(
            tooltip: 'Busca global',
"""
    s = once(
        s,
        actions_anchor,
        actions_new,
        "indicador de conectividade na Home",
    )
write(rel, s)

# Versionamento.
rel = "pubspec.yaml"
pub = read(rel)
old_version, new_version = (
    ("3.29.162+304", "3.29.163+305")
    if platform == "android"
    else ("3.30.81+268", "3.30.82+269")
)
marker = "version: " + old_version
if pub.count(marker) != 1:
    raise RuntimeError("versao base esperada ausente: " + old_version)
pub = pub.replace(marker, "version: " + new_version, 1)
write(rel, pub)

after = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected
}
changed = [name for name in protected if before[name] != after[name]]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

assert "Controle operacional de campo" in read(
    "lib/screens/field_intelligence_center_screen.dart"
)
assert "FieldOperationalControlScreen" in read(
    "lib/screens/field_intelligence_center_screen.dart"
)
assert "const FieldConnectivityBadge()" in read("lib/screens/home_screen.dart")
assert "version: " + new_version in read("pubspec.yaml")

print("FIELD_OPERATIONAL_CONTROL_OK", platform, new_version)
print("SYNC_DB_AUTH_HTTP_MEDIA_DRIVE_AI_GS_BYTE_IDENTICAL_OK")

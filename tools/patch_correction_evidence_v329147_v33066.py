#!/usr/bin/env python3
"""Auditar SST v3.29.147 / v3.30.66

Additive evidence intelligence:
- dedicated Before x After view using existing evidence/completion photos;
- conservative possible-recurrence detection over existing NC rows;
- entry point inside Central Inteligente de Campo;
- no schema, sync, auth, media, Drive, AI or Apps Script changes.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv) < 3:
    raise SystemExit(
        "uso: patch_correction_evidence_v329147_v33066.py "
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
    if text.count(old) != 1:
        raise RuntimeError(
            f"{label}: esperado 1, encontrado {text.count(old)}"
        )
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
        "feature_sources/correction_recurrence_detector_v329147.dart",
        "lib/services/correction_recurrence_detector.dart",
    ),
    (
        "feature_sources/correction_evidence_center_v329147.dart",
        "lib/screens/correction_evidence_center_screen.dart",
    ),
    (
        "feature_sources/correction_recurrence_detector_test_v329147.dart",
        "test/correction_recurrence_detector_test.dart",
    ),
]
for source, target in copies:
    src = repo / source
    dst = root / target
    if not src.exists():
        raise RuntimeError("fonte ausente: " + source)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)

rel = "lib/screens/field_intelligence_center_screen.dart"
s = read(rel)
s = once(
    s,
    "import 'evidence_backup_screen.dart';\n",
    "import 'evidence_backup_screen.dart';\n"
    "import 'correction_evidence_center_screen.dart';\n",
    "Central evidence import",
)

old_block = """        FilledButton.tonalIcon(
          onPressed: () => openPage(EvidenceBackupScreen(company: selectedCompany!)),
          icon: const Icon(Icons.photo_library_outlined),
          label: const Text('Abrir evidências da empresa'),
        ),
        const SizedBox(height: 10),
        const Card(child: Padding(
          padding: EdgeInsets.all(14),
          child: Text(
            'O comparativo Antes × Depois continua dentro do Plano de ação. '
            'As fotos originais e as fotos de correção permanecem vinculadas ao mesmo registro.',
          ),
        )),
        const SizedBox(height: 8),
        FilledButton.tonalIcon(
          onPressed: () => openPage(ActionPlanScreen(companyId: selectedCompanyId)),
          icon: const Icon(Icons.compare_outlined),
          label: const Text('Abrir Antes × Depois das correções'),
        ),"""

new_block = """        FilledButton.tonalIcon(
          onPressed: () => openPage(
            CorrectionEvidenceCenterScreen(company: selectedCompany!),
          ),
          icon: const Icon(Icons.compare_outlined),
          label: const Text('Antes × Depois e recorrências'),
        ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          onPressed: () => openPage(EvidenceBackupScreen(company: selectedCompany!)),
          icon: const Icon(Icons.cloud_done_outlined),
          label: const Text('Conferir proteção e backup das fotos'),
        ),
        const SizedBox(height: 10),
        const Card(child: Padding(
          padding: EdgeInsets.all(14),
          child: Text(
            'A comparação usa as fotos já vinculadas à constatação e à correção. '
            'Possíveis recorrências são sinalizadas para revisão do TST sem alterar o registro original.',
          ),
        )),
        const SizedBox(height: 8),
        TextButton.icon(
          onPressed: () => openPage(ActionPlanScreen(companyId: selectedCompanyId)),
          icon: const Icon(Icons.assignment_turned_in_outlined),
          label: const Text('Abrir plano de ação completo'),
        ),"""
if new_block not in s:
    first_label = "label: const Text('Abrir evidências da empresa'),"
    second_label = "label: const Text('Abrir Antes × Depois das correções'),"
    if s.count(first_label) != 1 or s.count(second_label) != 1:
        raise RuntimeError(
            "Central evidence labels: esperado 1 de cada, encontrados "
            + str((s.count(first_label), s.count(second_label)))
        )
    first_pos = s.index(first_label)
    start = s.rfind("        FilledButton.tonalIcon(", 0, first_pos)
    second_pos = s.index(second_label, first_pos)
    end = s.find("\n      ],", second_pos)
    if start < 0 or end < 0 or start >= end:
        raise RuntimeError("Central evidence block: limites nao encontrados")
    s = s[:start] + new_block + s[end:]

old_diagnostic = (
    "    final version = Platform.isWindows ? '3.30.62' : '3.29.143';"
)
new_diagnostic = (
    "    final version = Platform.isWindows ? '3.30.66' : '3.29.147';"
)
s = once(
    s,
    old_diagnostic,
    new_diagnostic,
    "Central diagnostics version",
)
write(rel, s)

rel = "pubspec.yaml"
pub = read(rel)
old_release, new_release = (
    ("3.29.146+288", "3.29.147+289")
    if platform == "android"
    else ("3.30.65+252", "3.30.66+253")
)
marker = "version: " + old_release
if pub.count(marker) != 1:
    raise RuntimeError("versao esperada ausente: " + old_release)
pub = pub.replace(marker, "version: " + new_release, 1)
write(rel, pub)

changed = [
    name
    for name, digest in before.items()
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

assert (
    "CorrectionEvidenceCenterScreen(company: selectedCompany!)"
    in read("lib/screens/field_intelligence_center_screen.dart")
)
assert (
    "Antes × Depois e recorrências"
    in read("lib/screens/field_intelligence_center_screen.dart")
)
assert "version: " + new_release in read("pubspec.yaml")

print("CORRECTION_EVIDENCE_INTELLIGENCE_OK", platform, new_release)
print("SYNC_DB_AUTH_MEDIA_AI_DRIVE_GS_BYTE_IDENTICAL_OK")

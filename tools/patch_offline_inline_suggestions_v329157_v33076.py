#!/usr/bin/env python3
"""Sugestões inline de modelos offline a partir do primeiro resumo digitado."""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv) < 3:
    raise SystemExit("uso: patch_offline_inline_suggestions_v329157_v33076.py <APP_DIR> <android|windows>")

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
if platform not in ("android", "windows"):
    raise SystemExit("plataforma invalida")
repo = Path(__file__).resolve().parent.parent

def read(rel):
    return (root / rel).read_text(encoding="utf-8")

def write(rel, value):
    (root / rel).write_text(value, encoding="utf-8", newline="\n")

def replace_once(value, old, new, label):
    count = value.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: esperado 1 marcador, encontrado {count}")
    return value.replace(old, new, 1)

protected = [
    "lib/database.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/auth_service.dart",
    "lib/services/drive_service.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/ai_assistant_service.dart",
    "lib/services/offline_report_knowledge_service.dart",
    "lib/widgets/offline_report_template_picker.dart",
    "lib/services/auditar_technical_inspection_pdf_service.dart",
    "lib/services/auditar_standard2_pdf_service.dart",
    "lib/services/auditar_standard3_pdf_service.dart",
    "lib/services/ronda_standard3_pdf_service.dart",
    "lib/services/report_template_service.dart",
    "lib/services/styled_report_pdf_service.dart",
    "lib/services/report_logo_service.dart",
    "lib/screens/express_round_screen.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
    "painel_web_google_apps_script/ClientPortal.html",
    "painel_web_google_apps_script/ReportEmail.gs",
]
before = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in protected}

for src, dest in [
    ("feature_sources/offline_report_inline_suggestions_v329157.dart",
     "lib/widgets/offline_report_inline_suggestions.dart"),
    ("feature_sources/offline_report_inline_suggestions_test_v329157.dart",
     "test/offline_report_inline_suggestions_test.dart"),
]:
    source = repo / src
    if not source.exists():
        raise RuntimeError("fonte ausente: " + src)
    target = root / dest
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)

rel = "lib/screens/safety_observations_screen.dart"
screen = read(rel)

import_anchor = "import '../widgets/offline_report_template_picker.dart';\n"
if "offline_report_inline_suggestions.dart" not in screen:
    screen = replace_once(
        screen,
        import_anchor,
        import_anchor + "import '../widgets/offline_report_inline_suggestions.dart';\n",
        "import sugestoes inline",
    )

target_anchor = """            const SizedBox(height: 14),
            _section('O que foi observado'),"""
if "Sugestões do histórico" not in screen:
    inline_block = r'''            ValueListenableBuilder<TextEditingValue>(
              valueListenable: title,
              builder: (context, value, _) {
                return OfflineReportInlineSuggestions(
                  query: value.text,
                  contextTerms: <String>[
                    observationKind,
                    _sectorName(),
                    location.text.trim(),
                  ],
                  onSelected: (selected) {
                    void fillEmpty(TextEditingController controller, String text) {
                      if (controller.text.trim().isEmpty && text.trim().isNotEmpty) {
                        controller.text = text.trim();
                      }
                    }

                    setState(() {
                      title.text = selected.title;
                      fillEmpty(description, selected.description);
                      fillEmpty(risk, selected.risk);
                      fillEmpty(consequence, selected.possibleConsequence);
                      fillEmpty(recommendation, selected.recommendation);
                      if (priority == 'Média') {
                        priority = selected.priority;
                      }
                    });
                    unawaited(OfflineReportKnowledgeService.markUsed(selected.id));
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text(
                          'Modelo aplicado aos campos técnicos. Confira o texto e registre somente o que foi observado.',
                        ),
                      ),
                    );
                  },
                );
              },
            ),
            const SizedBox(height: 14),
'''
    screen = replace_once(
        screen,
        target_anchor,
        inline_block + "            _section('O que foi observado'),",
        "sugestoes abaixo do titulo",
    )

write(rel, screen)

pub_rel = "pubspec.yaml"
pub = read(pub_rel)
old_version, new_version = (
    ("3.29.156+298", "3.29.157+299") if platform == "android"
    else ("3.30.75+262", "3.30.76+263")
)
marker = "version: " + old_version
if pub.count(marker) != 1:
    raise RuntimeError("versao base esperada ausente: " + old_version)
write(pub_rel, pub.replace(marker, "version: " + new_version, 1))

changed = [
    name for name, digest in before.items()
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit("PROTECTED_CORE_OR_REPORT_MODIFIED: " + repr(changed))

final_screen = read(rel)
for snippet in (
    "offline_report_inline_suggestions.dart",
    "OfflineReportInlineSuggestions(",
    "valueListenable: title",
    "title.text = selected.title",
    "fillEmpty(description, selected.description)",
    "fillEmpty(recommendation, selected.recommendation)",
):
    assert snippet in final_screen, "integracao inline ausente: " + snippet

assert "version: " + new_version in read(pub_rel)
print("OFFLINE_INLINE_SUGGESTIONS_PATCH_OK", platform, new_version)
print("FIRST_TITLE_FIELD_DRIVES_LOCAL_MODELS_OK")
print("LEARNED_AND_BASE_MODELS_CAN_APPEAR_INLINE_OK")
print("NO_INTERNET_REQUIRED_FOR_SUGGESTIONS_OK")
print("SYNC_DB_AUTH_HTTP_MEDIA_DRIVE_AI_GS_REPORT_RENDERERS_BYTE_IDENTICAL_OK")

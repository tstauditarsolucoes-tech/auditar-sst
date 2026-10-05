#!/usr/bin/env python3
"""Auditar SST v3.29.169 / v3.30.88 — baseline consolidada de acabamento e estabilidade.

- Consolida em uma etapa final as melhorias v167/v168.
- Mantem cache curto das sugestoes locais e conferencia paralela de fotos.
- Instala a visao gerencial, planejamento anual de capacitacao e CIPA.
- Uniformiza textos da Home e o identificador visual da versao.
- Nao altera banco, sync, auth, HTTP, midia/Drive, IA, Apps Script ou renderizadores PDF.
"""
from pathlib import Path
import hashlib
import json
import shutil
import sys

if len(sys.argv) < 3:
    raise SystemExit("uso: patch_release_baseline_v329169_v33088.py <APP_DIR> <android|windows>")

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
    "lib/models.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/auth_service.dart",
    "lib/services/drive_service.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/ai_assistant_service.dart",
    "lib/services/offline_report_knowledge_service.dart",
    "lib/services/auditar_technical_inspection_pdf_service.dart",
    "lib/services/auditar_standard2_pdf_service.dart",
    "lib/services/auditar_standard3_pdf_service.dart",
    "lib/services/ronda_standard3_pdf_service.dart",
    "lib/services/express_round_pdf_service.dart",
    "lib/services/report_template_service.dart",
    "lib/services/styled_report_pdf_service.dart",
    "lib/services/report_logo_service.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
    "painel_web_google_apps_script/ClientPortal.html",
    "painel_web_google_apps_script/ReportEmail.gs",
]
before = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected if (root / name).exists()
}

copies = [
    ("feature_sources/offline_report_inline_suggestions_v329167.dart",
     "lib/widgets/offline_report_inline_suggestions.dart"),
    ("feature_sources/offline_report_inline_suggestions_test_v329167.dart",
     "test/offline_report_inline_suggestions_test.dart"),
    ("feature_sources/manager_reports_module_v329169.dart",
     "lib/screens/manager_reports_screen.dart"),
    ("feature_sources/manager_reports_module_test_v329168.dart",
     "test/manager_reports_module_test.dart"),
    ("feature_sources/training_activity_center_v329169.dart",
     "lib/screens/training_activity_center_screen.dart"),
    ("feature_sources/cipa_management_screen_v329168.dart",
     "lib/screens/cipa_management_screen.dart"),
]
for source, target in copies:
    src = repo / source
    dst = root / target
    if not src.exists():
        raise RuntimeError("fonte ausente: " + source)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)

# A conferencia Premium antes do PDF fazia consultas/fotos em serie.
# Mantemos exatamente as mesmas regras, mas executamos as leituras independentes em paralelo.
rel = "lib/screens/report_screen.dart"
s = read(rel)
old_loop = r'''    for (final answer in premiumFindings) {
      qualityPossible += 5;
      if (answer.observation.trim().isNotEmpty) {
        qualityComplete++;
      } else {
        qualityNoDescription++;
      }
      if (answer.riskIdentified.trim().isNotEmpty) {
        qualityComplete++;
      } else {
        qualityNoRisk++;
      }
      if (answer.recommendation.trim().isNotEmpty) {
        qualityComplete++;
      } else {
        qualityNoRecommendation++;
      }
      if (answer.questionReference.trim().isNotEmpty) {
        qualityComplete++;
      } else {
        qualityNoReference++;
      }
      final photos = await db.getPhotosForAnswer(answer.id);
      var hasPhoto = false;
      for (final photo in photos) {
        if (photo.path.trim().isNotEmpty && await File(photo.path).exists()) {
          hasPhoto = true;
          break;
        }
      }
      if (hasPhoto) {
        qualityComplete++;
      } else {
        qualityNoPhoto++;
      }
    }
'''
new_loop = r'''    final qualityRows = await Future.wait(
      premiumFindings.map((answer) async {
        final photos = await db.getPhotosForAnswer(answer.id);
        var hasPhoto = false;
        for (final photo in photos) {
          if (photo.path.trim().isNotEmpty && await File(photo.path).exists()) {
            hasPhoto = true;
            break;
          }
        }
        return <String, bool>{
          'description': answer.observation.trim().isNotEmpty,
          'risk': answer.riskIdentified.trim().isNotEmpty,
          'recommendation': answer.recommendation.trim().isNotEmpty,
          'reference': answer.questionReference.trim().isNotEmpty,
          'photo': hasPhoto,
        };
      }),
    );
    qualityPossible = qualityRows.length * 5;
    for (final row in qualityRows) {
      if (row['description'] == true) {
        qualityComplete++;
      } else {
        qualityNoDescription++;
      }
      if (row['risk'] == true) {
        qualityComplete++;
      } else {
        qualityNoRisk++;
      }
      if (row['recommendation'] == true) {
        qualityComplete++;
      } else {
        qualityNoRecommendation++;
      }
      if (row['reference'] == true) {
        qualityComplete++;
      } else {
        qualityNoReference++;
      }
      if (row['photo'] == true) {
        qualityComplete++;
      } else {
        qualityNoPhoto++;
      }
    }
'''
s = once(s, old_loop, new_loop, "qualidade paralela do relatorio")
write(rel, s)

# Acabamento visual da Home sem esconder funcoes.
home_rel = "lib/screens/home_screen.dart"
home = read(home_rel)
home = home.replace(
    "As funções voltaram a ficar visíveis, sem menus escondidos",
    "Acesse os demais recursos do Auditar SST",
)
import re
release_label = (
    "Auditar SST • versão 3.29.169"
    if platform == "android"
    else "Auditar SST • versão 3.30.88"
)
home = re.sub(
    r"Auditar SST • versão [0-9.]+",
    release_label,
    home,
)
write(home_rel, home)

pub = read("pubspec.yaml")
old_version, new_version = (
    ("3.29.166+308", "3.29.169+311")
    if platform == "android"
    else ("3.30.85+272", "3.30.88+275")
)
marker = "version: " + old_version
if pub.count(marker) != 1:
    raise RuntimeError("versao base esperada ausente: " + old_version)
write("pubspec.yaml", pub.replace(marker, "version: " + new_version, 1))

after = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected if (root / name).exists()
}
changed = [name for name in before if before[name] != after[name]]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

(root / ".auditar_v329169_protected.json").write_text(
    json.dumps(after, indent=2, sort_keys=True),
    encoding="utf-8",
)

widget = read("lib/widgets/offline_report_inline_suggestions.dart")
report = read("lib/screens/report_screen.dart")
assert "_learnedCacheTtl = Duration(seconds: 8)" in widget
assert "...await _learnedSuggestions()" in widget
assert "Outras sugestões locais" not in widget
assert "Icons.offline_bolt_outlined" not in widget
assert "Icons.auto_awesome_outlined" in widget
assert "Future.wait(" in report
assert "premiumFindings.map((answer) async" in report
assert "qualityPossible = qualityRows.length * 5;" in report
manager = read("lib/screens/manager_reports_screen.dart")
training = read("lib/screens/training_activity_center_screen.dart")
cipa = read("lib/screens/cipa_management_screen.dart")
home = read("lib/screens/home_screen.dart")
assert "Resumo para decisão" in manager
assert "CAPACITAÇÃO E CONTROLE PREVENTIVO" in manager
assert "final ncsFuture = db.getNonConformityRows" in manager
assert "Planejamento anual" in training
assert "summaryFuture" in training
assert "Planejamento anual da CIPA" in cipa
assert "Acesse os demais recursos do Auditar SST" in home
assert release_label in home
assert "version: " + new_version in read("pubspec.yaml")

print("RELEASE_BASELINE_OK", platform, new_version)
print("PATCH_CHAIN_V167_V168_CONSOLIDATED_OK")
print("SUGGESTION_SHORT_CACHE_OK")
print("REPORT_PHOTO_PREFLIGHT_PARALLEL_OK")
print("MANAGEMENT_LOAD_PARALLELIZED_OK")
print("TRAINING_LOAD_PARALLELIZED_OK")
print("HOME_VISUAL_VERSION_OK")
print("AI_SYNC_DB_AUTH_HTTP_MEDIA_DRIVE_GS_PDF_RENDERERS_PRESERVED_OK")

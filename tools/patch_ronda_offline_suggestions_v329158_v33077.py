#!/usr/bin/env python3
"""Levar sugestões/modelos offline para a Ronda sem alterar IA ou sincronização."""
from pathlib import Path
import hashlib
import sys

if len(sys.argv) < 3:
    raise SystemExit("uso: patch_ronda_offline_suggestions_v329158_v33077.py <APP_DIR> <android|windows>")

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
if platform not in ("android", "windows"):
    raise SystemExit("plataforma invalida")

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
    "lib/widgets/offline_report_inline_suggestions.dart",
    "lib/widgets/offline_report_template_picker.dart",
    "lib/services/express_round_pdf_service.dart",
    "lib/services/ronda_standard3_pdf_service.dart",
    "lib/services/auditar_standard3_pdf_service.dart",
    "lib/services/report_template_service.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
    "painel_web_google_apps_script/ClientPortal.html",
    "painel_web_google_apps_script/ReportEmail.gs",
]
before = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in protected}

rel = "lib/screens/express_round_screen.dart"
screen = read(rel)

import_anchor = "import '../services/storage_service.dart';\n"
if "offline_report_inline_suggestions.dart" not in screen:
    screen = replace_once(
        screen,
        import_anchor,
        import_anchor
        + "import '../services/offline_report_knowledge_service.dart';\n"
        + "import '../widgets/offline_report_inline_suggestions.dart';\n",
        "imports Ronda offline",
    )

state_anchor = "  String aiTextOriginal = '';\n"
if "String offlineModelId = '';" not in screen:
    screen = replace_once(
        screen,
        state_anchor,
        """  String offlineModelId = '';
  String offlineModelTitle = '';
  String offlineModelRisk = '';
  String offlineModelConsequence = '';
  String offlineModelRecommendation = '';
  String offlineModelSource = '';

""" + state_anchor,
        "estado modelo offline Ronda",
    )

method_anchor = "  Future<void> _saveAndContinue() async {\n"
if "void _applyOfflineRoundSuggestion(" not in screen:
    methods = r'''  void _applyOfflineRoundSuggestion(OfflineInlineSuggestion selected) {
    if (_isConformity) return;
    setState(() {
      if (selected.description.trim().isNotEmpty) {
        description.text = selected.description.trim();
      }
      offlineModelId = selected.id;
      offlineModelTitle = selected.title.trim();
      offlineModelRisk = selected.risk.trim();
      offlineModelConsequence = selected.possibleConsequence.trim();
      offlineModelRecommendation = selected.recommendation.trim();
      offlineModelSource = selected.source;
      if (priority == 'Média' && selected.priority.trim().isNotEmpty) {
        priority = selected.priority;
      }
    });
    unawaited(OfflineReportKnowledgeService.markUsed(selected.id));
    _message(
      'Modelo offline aplicado. Confira o texto e ajuste ao que foi realmente observado.',
    );
  }

  void _clearOfflineRoundModel() {
    offlineModelId = '';
    offlineModelTitle = '';
    offlineModelRisk = '';
    offlineModelConsequence = '';
    offlineModelRecommendation = '';
    offlineModelSource = '';
  }

'''
    screen = replace_once(
        screen,
        method_anchor,
        methods + method_anchor,
        "metodos Ronda offline",
    )

old_title = """    final title =
        aiTitle.isNotEmpty
            ? aiTitle
            : '${categoriesToSave.join(' + ')} · $effectiveDescription';"""
new_title = """    final effectiveTechnicalTitle =
        aiTitle.isNotEmpty
            ? aiTitle
            : (_isConformity ? '' : offlineModelTitle);
    final title =
        effectiveTechnicalTitle.isNotEmpty
            ? effectiveTechnicalTitle
            : '${categoriesToSave.join(' + ')} · $effectiveDescription';"""
if "final effectiveTechnicalTitle" not in screen:
    screen = replace_once(screen, old_title, new_title, "titulo offline Ronda")

replacements = [
    ("          'risk': aiRisk,", "          'risk': _isConformity
              ? aiRisk
              : (aiRisk.isNotEmpty ? aiRisk : offlineModelRisk),"),
    ("          'possibleConsequence': aiConsequence,", "          'possibleConsequence':\n              aiConsequence.isNotEmpty ? aiConsequence : offlineModelConsequence,"),
    ("          'recommendation': aiRecommendation,", "          'recommendation': aiRecommendation.isNotEmpty\n              ? aiRecommendation\n              : offlineModelRecommendation,"),
]
for old, new in replacements:
    if new not in screen:
        screen = replace_once(screen, old, new, "campo tecnico offline Ronda")

payload_anchor = "          'roundType': 'RONDA_EXPRESSA',\n"
if "'offlineModelId': offlineModelId," not in screen:
    screen = replace_once(
        screen,
        payload_anchor,
        payload_anchor
        + "          'offlineModelApplied': offlineModelId.isNotEmpty,\n"
        + "          'offlineModelId': offlineModelId,\n"
        + "          'offlineModelSource': offlineModelSource,\n",
        "metadados offline Ronda",
    )

clear_anchor = """        recurring = false;
        _clearAiState();"""
if "_clearOfflineRoundModel();" not in screen:
    screen = replace_once(
        screen,
        clear_anchor,
        """        recurring = false;
        _clearAiState();
        _clearOfflineRoundModel();""",
        "limpar modelo offline apos salvar",
    )


ui_anchor = """                      const SizedBox(height: 7),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon("""
if "OfflineReportInlineSuggestions(" not in screen:
    ui = r'''                      if (!_isConformity)
                        ValueListenableBuilder<TextEditingValue>(
                          valueListenable: description,
                          builder: (context, value, _) {
                            return OfflineReportInlineSuggestions(
                              query: value.text,
                              contextTerms: <String>[
                                ...selectedCategories,
                                sectorName,
                                location.text.trim(),
                                'Ronda',
                              ],
                              onSelected: _applyOfflineRoundSuggestion,
                            );
                          },
                        ),
                      const SizedBox(height: 7),
'''
    screen = replace_once(
        screen,
        ui_anchor,
        ui + """                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon(""",
        "sugestoes inline Ronda",
    )

write(rel, screen)

pub_rel = "pubspec.yaml"
pub = read(pub_rel)
old_version, new_version = (
    ("3.29.157+299", "3.29.158+300")
    if platform == "android"
    else ("3.30.76+263", "3.30.77+264")
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
    raise SystemExit("PROTECTED_CORE_AI_SYNC_REPORT_MODIFIED: " + repr(changed))

final = read(rel)
for snippet in (
    "OfflineReportInlineSuggestions(",
    "valueListenable: description",
    "_applyOfflineRoundSuggestion",
    "offlineModelId",
    "offlineModelRisk",
    "offlineModelRecommendation",
    "'offlineModelApplied': offlineModelId.isNotEmpty",
    "aiRisk.isNotEmpty ? aiRisk : offlineModelRisk",
):
    assert snippet in final, "Ronda offline incompleta: " + snippet

assert "version: " + new_version in read(pub_rel)
print("RONDA_OFFLINE_SUGGESTIONS_PATCH_OK", platform, new_version)
print("RONDA_FIRST_DESCRIPTION_AUTOSUGGEST_OK")
print("RISK_RECOMMENDATION_OFFLINE_REUSE_OK")
print("AI_SYNC_DB_AUTH_HTTP_MEDIA_DRIVE_GS_REPORTS_BYTE_IDENTICAL_OK")

#!/usr/bin/env python3
"""Biblioteca técnica offline e aprendizado local aprovado."""
from pathlib import Path
import base64
import gzip
import hashlib
import shutil
import sys

if len(sys.argv) < 3:
    raise SystemExit("uso: patch_offline_report_knowledge_v329156_v33075.py <APP_DIR> <android|windows>")

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

def install_source(src, dest):
    source = repo / src
    if not source.exists():
        raise RuntimeError("fonte ausente: " + src)
    target = root / dest
    target.parent.mkdir(parents=True, exist_ok=True)
    if src.endswith(".gz.b64"):
        encoded = source.read_text(encoding="utf-8").strip()
        target.write_bytes(gzip.decompress(base64.b64decode(encoded)))
    else:
        shutil.copyfile(source, target)

for src, dest in [
    ("feature_sources/offline_report_knowledge_service_v329156.dart.gz.b64", "lib/services/offline_report_knowledge_service.dart"),
    ("feature_sources/offline_report_template_picker_v329156.dart.gz.b64", "lib/widgets/offline_report_template_picker.dart"),
    ("feature_sources/offline_report_knowledge_test_v329156.dart", "test/offline_report_knowledge_test.dart"),
]:
    install_source(src, dest)

rel = "lib/screens/safety_observations_screen.dart"
screen = read(rel)

import_anchor = "import '../services/storage_service.dart';\n"
if "offline_report_knowledge_service.dart" not in screen:
    screen = replace_once(
        screen, import_anchor,
        import_anchor + "import '../services/offline_report_knowledge_service.dart';\n" + "import '../widgets/offline_report_template_picker.dart';\n",
        "imports biblioteca offline",
    )

state_anchor = "  bool analyzingTextWithAi = false;\n  String aiTextOriginal = '';"
if "bool aiSuggestionApplied = false;" not in screen:
    screen = replace_once(
        screen, state_anchor,
        "  bool analyzingTextWithAi = false;\n  bool aiSuggestionApplied = false;\n  String aiTextOriginal = '';",
        "estado aprendizado IA",
    )

text_ai_anchor = """    setState(() {
      if (aiTextOriginal.isEmpty) aiTextOriginal = original;
      description.text = revised;
    });"""
if "description.text = revised;\n      aiSuggestionApplied = true;" not in screen:
    screen = replace_once(
        screen, text_ai_anchor,
        """    setState(() {
      if (aiTextOriginal.isEmpty) aiTextOriginal = original;
      description.text = revised;
      aiSuggestionApplied = true;
    });""",
        "marcar IA texto aprovada",
    )

photo_ai_anchor = """    setState(() {
      if (suggestedTitle.isNotEmpty) title.text = suggestedTitle;"""
if "setState(() {\n      aiSuggestionApplied = true;\n      if (suggestedTitle.isNotEmpty)" not in screen:
    screen = replace_once(
        screen, photo_ai_anchor,
        """    setState(() {
      aiSuggestionApplied = true;
      if (suggestedTitle.isNotEmpty) title.text = suggestedTitle;""",
        "marcar IA foto aprovada",
    )

methods_anchor = """  String _sectorName() {
    for (final sector in widget.sectors) {"""
if "Future<void> _useOfflineTemplate()" not in screen:
    methods = r'''  Future<void> _useOfflineTemplate() async {
    final selected = await OfflineReportTemplatePicker.show(
      context,
      contextTerms: <String>[
        observationKind,
        _sectorName(),
        location.text.trim(),
        title.text.trim(),
        description.text.trim(),
      ],
    );
    if (!mounted || selected == null) return;

    final mode = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(selected.title),
        content: const Text(
          'O modelo não traz empresa, local, foto ou trabalhador. Como deseja aplicar os campos técnicos?',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
          OutlinedButton(onPressed: () => Navigator.pop(context, 'empty'), child: const Text('Preencher campos vazios')),
          FilledButton(onPressed: () => Navigator.pop(context, 'replace'), child: const Text('Usar modelo completo')),
        ],
      ),
    );
    if (!mounted || mode == null) return;

    void apply(TextEditingController controller, String value) {
      if (value.trim().isEmpty) return;
      if (mode == 'replace' || controller.text.trim().isEmpty) {
        controller.text = value.trim();
      }
    }

    setState(() {
      apply(title, selected.title);
      apply(description, selected.description);
      apply(risk, selected.risk);
      apply(consequence, selected.possibleConsequence);
      apply(recommendation, selected.recommendation);
      apply(immediateAction, selected.immediateAction);
      if (mode == 'replace' || priority == 'Média') {
        priority = selected.priority;
      }
    });
    unawaited(OfflineReportKnowledgeService.markUsed(selected.id));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Modelo offline aplicado. Confira o local e ajuste o texto antes de salvar.')),
    );
  }

  Future<void> _saveCurrentAsOfflineTemplate() async {
    final currentTitle = title.text.trim();
    final currentDescription = description.text.trim();
    if (currentTitle.isEmpty || currentDescription.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Informe pelo menos o título e a descrição antes de guardar o modelo.')),
      );
      return;
    }
    try {
      final learned = await OfflineReportKnowledgeService.learnFromApprovedFields(
        title: currentTitle,
        description: currentDescription,
        risk: risk.text.trim(),
        possibleConsequence: consequence.text.trim(),
        recommendation: recommendation.text.trim(),
        immediateAction: immediateAction.text.trim(),
        priority: priority,
        source: 'manual_approved',
        companyName: widget.company.name,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(
          learned == null
              ? 'O conteúdo ainda não tem informações suficientes para virar modelo.'
              : 'Modelo técnico salvo neste dispositivo para uso offline.',
        )),
      );
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Não foi possível salvar o modelo local.')),
      );
    }
  }

  Future<void> _learnApprovedAiLocally() async {
    try {
      await OfflineReportKnowledgeService.learnFromApprovedFields(
        title: title.text.trim(),
        description: description.text.trim(),
        risk: risk.text.trim(),
        possibleConsequence: consequence.text.trim(),
        recommendation: recommendation.text.trim(),
        immediateAction: immediateAction.text.trim(),
        priority: priority,
        source: 'ai_approved',
        companyName: widget.company.name,
      );
    } catch (_) {
      // Falha na memória local nunca bloqueia a vistoria já salva.
    }
  }

'''
    screen = replace_once(screen, methods_anchor, methods + methods_anchor, "metodos biblioteca offline")

if "if (aiSuggestionApplied) {\n      unawaited(_learnApprovedAiLocally());" not in screen:
    after_catch_anchor = """      return;
    }
    // Saving is local-first. A slow web panel must never keep the edit screen"""
    screen = replace_once(
        screen, after_catch_anchor,
        """      return;
    }
    if (aiSuggestionApplied) {
      unawaited(_learnApprovedAiLocally());
    }
    // Saving is local-first. A slow web panel must never keep the edit screen""",
        "aprendizado local apos salvar",
    )

ui_anchor = """            const SizedBox(height: 7),
            Align(
              alignment: Alignment.centerLeft,
              child: OutlinedButton.icon(
                onPressed: analyzingTextWithAi ? null : _improveTextWithAi,"""
if "Usar modelo offline" not in screen:
    screen = replace_once(
        screen, ui_anchor,
        """            const SizedBox(height: 7),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                OutlinedButton.icon(
                  onPressed: _useOfflineTemplate,
                  icon: const Icon(Icons.offline_bolt_outlined),
                  label: const Text('Usar modelo offline'),
                ),
                TextButton.icon(
                  onPressed: _saveCurrentAsOfflineTemplate,
                  icon: const Icon(Icons.bookmark_add_outlined),
                  label: const Text('Guardar como modelo'),
                ),
              ],
            ),
            const SizedBox(height: 7),
            Align(
              alignment: Alignment.centerLeft,
              child: OutlinedButton.icon(
                onPressed: analyzingTextWithAi ? null : _improveTextWithAi,""",
        "acoes offline no formulario",
    )

write(rel, screen)

pub_rel = "pubspec.yaml"
pub = read(pub_rel)
old_version, new_version = (
    ("3.29.155+297", "3.29.156+298") if platform == "android"
    else ("3.30.74+261", "3.30.75+262")
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
final_service = read("lib/services/offline_report_knowledge_service.dart")
final_picker = read("lib/widgets/offline_report_template_picker.dart")
for snippet in ("Usar modelo offline","Guardar como modelo","aiSuggestionApplied = true","learnFromApprovedFields"):
    assert snippet in final_screen
for snippet in ("offline_report_knowledge_v1.json","getApplicationSupportDirectory"):
    assert snippet in final_service
for forbidden in ("AppDatabase","DeviceSyncService","AppsScript","companyId","photoPath"):
    assert forbidden not in final_service
assert "OfflineReportTemplatePicker" in final_picker
assert "version: " + new_version in read(pub_rel)

print("OFFLINE_REPORT_KNOWLEDGE_PATCH_OK", platform, new_version)
print("AI_APPROVED_CONTENT_CAN_BECOME_LOCAL_TEMPLATE_OK")
print("NO_COMPANY_PHOTO_LOCATION_IN_TEMPLATE_SCHEMA_OK")
print("SYNC_DB_AUTH_HTTP_MEDIA_DRIVE_AI_GS_REPORT_RENDERERS_BYTE_IDENTICAL_OK")

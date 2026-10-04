#!/usr/bin/env python3
"""Integra regras locais sem IA ao checklist, registro técnico, Ronda e relatório."""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv) < 3:
    raise SystemExit("uso: patch_offline_field_assistant_v329161_v33080.py <APP_DIR> <android|windows>")

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
if platform not in ("android", "windows"):
    raise SystemExit("plataforma invalida")
repo = Path(__file__).resolve().parent.parent

def read(rel):
    return (root / rel).read_text(encoding="utf-8")

def write(rel, value):
    (root / rel).write_text(value, encoding="utf-8", newline="\n")

def once(value, old, new, label):
    count = value.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: esperado 1 marcador, encontrado {count}")
    return value.replace(old, new, 1)

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
    for name in protected
    if (root / name).exists()
}

for src, dest in [
    ("feature_sources/offline_field_rules_service_v329161.dart",
     "lib/services/offline_field_rules_service.dart"),
    ("feature_sources/offline_field_assistant_dialog_v329161.dart",
     "lib/widgets/offline_field_assistant_dialog.dart"),
    ("feature_sources/offline_field_rules_test_v329161.dart",
     "test/offline_field_rules_test.dart"),
]:
    source = repo / src
    if not source.exists():
        raise RuntimeError("fonte ausente: " + src)
    target = root / dest
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)

# Registro técnico / observação.
rel = "lib/screens/safety_observations_screen.dart"
s = read(rel)
anchor = "import '../widgets/offline_report_inline_suggestions.dart';\n"
if "offline_field_assistant_dialog.dart" not in s:
    s = once(
        s, anchor,
        anchor + "import '../widgets/offline_field_assistant_dialog.dart';\n",
        "import assistente registro tecnico",
    )

method_anchor = "  Future<void> _useOfflineTemplate() async {\n"
if "Future<void> _openOfflineFieldAssistant()" not in s:
    methods = r'''  Future<void> _openOfflineFieldAssistant() async {
    final query = description.text.trim().isNotEmpty
        ? description.text.trim()
        : title.text.trim();
    if (query.length < 3) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text(
          'Descreva primeiro a situação para receber sugestões locais.',
        )),
      );
      return;
    }

    final localMatches = await OfflineReportInlineSuggestionService.search(
      query: query,
      contextTerms: <String>[_sectorName(), location.text.trim()],
      limit: 3,
    );
    final possibleRecurrence =
        localMatches.any((item) => item.learned || item.useCount > 0);
    if (!mounted) return;

    final result = await OfflineFieldAssistantDialog.show(
      context,
      text: <String>[
        title.text.trim(),
        description.text.trim(),
        risk.text.trim(),
        consequence.text.trim(),
        _sectorName(),
        location.text.trim(),
      ].where((value) => value.isNotEmpty).join(' '),
      markedRecurring: possibleRecurrence,
    );
    if (!mounted || result == null) return;

    setState(() {
      priority = result.priority;
      if (recommendation.text.trim().isEmpty) {
        recommendation.text = result.actionPlan;
      }
      if (immediateAction.text.trim().isEmpty &&
          (result.priority == 'Alta' || result.priority == 'Crítica')) {
        immediateAction.text = 'Priorizar tratamento: ' +
            result.deadlineSuggestion + '.';
      }
    });

    final nrText = result.nrs.isEmpty
        ? 'confirmar manualmente'
        : result.nrs.join(', ');
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(
        'Assistente sem IA aplicado. Prioridade: ' + result.priority +
        '. NRs sugeridas: ' + nrText + '.',
      )),
    );
  }

'''
    s = once(s, method_anchor, methods + method_anchor,
             "metodo assistente registro tecnico")

ui_anchor = """              children: [
                OutlinedButton.icon(
                  onPressed: _useOfflineTemplate,"""
if "Abrir assistente sem IA" not in s:
    s = once(
        s, ui_anchor,
        """              children: [
                FilledButton.tonalIcon(
                  onPressed: _openOfflineFieldAssistant,
                  icon: const Icon(Icons.offline_bolt_outlined),
                  label: const Text('Abrir assistente sem IA'),
                ),
                OutlinedButton.icon(
                  onPressed: _useOfflineTemplate,""",
        "botao assistente registro tecnico",
    )
write(rel, s)

# Ronda Expressa.
rel = "lib/screens/express_round_screen.dart"
s = read(rel)
anchor = "import '../widgets/offline_report_inline_suggestions.dart';\n"
if "offline_field_assistant_dialog.dart" not in s:
    s = once(
        s, anchor,
        anchor + "import '../widgets/offline_field_assistant_dialog.dart';\n",
        "import assistente Ronda",
    )

method_anchor = "  void _applyOfflineRoundSuggestion(OfflineInlineSuggestion selected) {\n"
if "Future<void> _openRoundOfflineAssistant()" not in s:
    methods = r'''  Future<void> _openRoundOfflineAssistant() async {
    if (_isConformity) {
      _message('O assistente de risco é destinado às não conformidades.');
      return;
    }
    final query = description.text.trim();
    if (query.length < 3) {
      _message('Descreva primeiro a situação encontrada.');
      return;
    }

    final localMatches = await OfflineReportInlineSuggestionService.search(
      query: query,
      contextTerms: <String>[...selectedCategories, sectorName],
      limit: 3,
    );
    final possibleRecurrence = recurring ||
        localMatches.any((item) => item.learned || item.useCount > 0);
    if (!mounted) return;

    final result = await OfflineFieldAssistantDialog.show(
      context,
      text: <String>[
        query,
        ...selectedCategories,
        sectorName,
        location.text.trim(),
        offlineModelRisk,
        offlineModelConsequence,
      ].where((value) => value.trim().isNotEmpty).join(' '),
      markedRecurring: possibleRecurrence,
    );
    if (!mounted || result == null) return;

    setState(() {
      priority = result.priority;
      if (result.possibleRecurrence) recurring = true;
      if (offlineModelRecommendation.trim().isEmpty) {
        offlineModelRecommendation = result.actionPlan;
      }
    });
    final nrText = result.nrs.isEmpty
        ? 'confirmar manualmente'
        : result.nrs.join(', ');
    _message(
      'Assistente sem IA: prioridade ' + result.priority +
      '; NRs sugeridas: ' + nrText + '.',
    );
  }

'''
    s = once(s, method_anchor, methods + method_anchor,
             "metodo assistente Ronda")

ui_anchor = """                          },
                        ),
                      const SizedBox(height: 7),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon("""
if "Matriz e NR sem IA" not in s:
    s = once(
        s, ui_anchor,
        """                          },
                        ),
                      if (!_isConformity) ...[
                        const SizedBox(height: 7),
                        SizedBox(
                          width: double.infinity,
                          child: FilledButton.tonalIcon(
                            onPressed: _openRoundOfflineAssistant,
                            icon: const Icon(Icons.offline_bolt_outlined),
                            label: const Text('Matriz e NR sem IA'),
                          ),
                        ),
                      ],
                      const SizedBox(height: 7),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon(""",
        "botao assistente Ronda",
    )
write(rel, s)

# Checklist - captura rápida.
rel = "lib/screens/checklist_screen.dart"
s = read(rel)
anchor = "import '../services/checklist_field_capture_policy.dart';\n"
if "offline_field_assistant_dialog.dart" not in s:
    s = once(
        s, anchor,
        anchor + "import '../widgets/offline_field_assistant_dialog.dart';\n",
        "import assistente checklist",
    )

method_anchor = "  Widget _fastCaptureCard() {\n"
if "Future<void> _openFastOfflineAssistant()" not in s:
    methods = r'''  Future<void> _openFastOfflineAssistant() async {
    final item = _fastSelected;
    final current = _fastDescription.text.trim();
    if (item == null || current.length < 3) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text(
          'Selecione o item e descreva a NC antes de calcular.',
        )),
      );
      return;
    }

    final result = await OfflineFieldAssistantDialog.show(
      context,
      text: item.text + ' ' + current,
      existingReference: item.reference,
    );
    if (!mounted || result == null) return;
    setState(() => _fastPriority = result.priority);

    final nrText = result.nrs.isEmpty
        ? item.reference
        : result.nrs.join(', ');
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(
        'Prioridade ' + result.priority +
        ' aplicada. Referência sugerida: ' +
        (nrText.trim().isEmpty ? 'confirmar manualmente' : nrText) + '.',
      )),
    );
  }

'''
    s = once(s, method_anchor, methods + method_anchor,
             "metodo assistente checklist")

if "Calcular prioridade e NR sem IA" not in s:
    priority_pos = s.find("labelText: 'Prioridade informada pelo técnico'")
    if priority_pos < 0:
        raise RuntimeError("campo de prioridade da captura rapida nao localizado")
    button_pos = s.find("            FilledButton.icon(", priority_pos)
    if button_pos < 0:
        raise RuntimeError("botao salvar da captura rapida nao localizado")
    button = """            OutlinedButton.icon(
              onPressed: _fastSaving ? null : _openFastOfflineAssistant,
              icon: const Icon(Icons.offline_bolt_outlined),
              label: const Text('Calcular prioridade e NR sem IA'),
            ),
            const SizedBox(height: 12),
"""
    s = s[:button_pos] + button + s[button_pos:]
write(rel, s)

# Relatório - resumo executivo local.
rel = "lib/screens/report_screen.dart"
s = read(rel)
method_anchor = "  String _buildOfflineInspectionConclusion() {\n"
if "String _buildOfflineExecutiveSummary()" not in s:
    methods = r'''  String _buildOfflineExecutiveSummary() {
    final applicable = conformes + naoConformes + parciais;
    final conformity = applicable == 0
        ? 0
        : ((conformes * 100) / applicable).round();
    final pending = naoConformes + parciais;

    return <String>[
      'Resumo executivo da vistoria: $applicable item(ns) aplicável(is), '
          '$conformes conforme(s), $naoConformes não conformidade(s) e '
          '$parciais item(ns) parcial(is).',
      'Índice de conformidade entre os itens aplicáveis: $conformity%.',
      if (pending > 0)
        'Existem $pending item(ns) que exigem correção ou acompanhamento. '
            'Defina responsáveis, prazos e evidências da regularização.',
      if (pending == 0)
        'Não foram registradas pendências entre os itens aplicáveis. '
            'Manter os controles e o acompanhamento preventivo.',
    ].join(' ');
  }

  Future<void> _generateOfflineExecutiveSummary() async {
    final db = AppDatabase.instance;
    final header = await db.getInspectionHeader(widget.inspectionId);
    if (!mounted) return;
    final currentConclusion = (header?['conclusion'] ?? '').toString().trim();
    final controller = TextEditingController(
      text: _buildOfflineExecutiveSummary(),
    );
    final edited = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.summarize_outlined),
            SizedBox(width: 8),
            Expanded(child: Text('Resumo executivo sem IA')),
          ],
        ),
        content: SizedBox(
          width: 720,
          child: TextField(
            controller: controller,
            minLines: 6,
            maxLines: 14,
            textCapitalization: TextCapitalization.sentences,
            decoration: const InputDecoration(
              labelText: 'Resumo executivo',
              alignLabelWithHint: true,
              helperText: 'Gerado localmente. Revise antes de salvar.',
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancelar'),
          ),
          FilledButton.icon(
            onPressed: () =>
                Navigator.pop(dialogContext, controller.text.trim()),
            icon: const Icon(Icons.check),
            label: const Text('Salvar como observação geral'),
          ),
        ],
      ),
    );
    controller.dispose();
    if (!mounted || edited == null) return;

    final finalText = edited.trim().isEmpty
        ? _buildOfflineExecutiveSummary()
        : edited.trim();
    await db.updateInspectionNarrative(
      inspectionId: widget.inspectionId,
      generalNotes: finalText,
      conclusion: currentConclusion,
    );
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text(
        'Resumo executivo sem IA salvo. Revise o relatório antes de emitir.',
      )),
    );
  }

'''
    s = once(s, method_anchor, methods + method_anchor,
             "metodo resumo executivo")

if "Resumo executivo — sem IA" not in s:
    marker = "Conclusão do relatório — sem IA"
    pos = s.find(marker)
    if pos < 0:
        raise RuntimeError("card de conclusao offline nao localizado")
    start = s.rfind("          Card(", 0, pos)
    if start < 0:
        raise RuntimeError("inicio do card offline nao localizado")
    card = r'''          Card(
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
              side: BorderSide(color: AuditarBrand.navy.withOpacity(.22)),
            ),
            child: Padding(
              padding: const EdgeInsets.all(15),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.summarize_outlined, color: AuditarBrand.navy),
                      SizedBox(width: 9),
                      Expanded(
                        child: Text(
                          'Resumo executivo — sem IA',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w800,
                            color: AuditarBrand.navyDark,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Calcula conformidade e pendências usando apenas os dados '
                    'já registrados na vistoria.',
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      onPressed: _generateOfflineExecutiveSummary,
                      icon: const Icon(Icons.summarize_outlined),
                      label: const Text('Gerar resumo sem IA'),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 14),
'''
    s = s[:start] + card + s[start:]
write(rel, s)

# Versão.
pub = read("pubspec.yaml")
old_version, new_version = (
    ("3.29.160+302", "3.29.161+303")
    if platform == "android"
    else ("3.30.79+266", "3.30.80+267")
)
marker = "version: " + old_version
if pub.count(marker) != 1:
    raise RuntimeError("versao base esperada ausente: " + old_version)
write("pubspec.yaml", pub.replace(marker, "version: " + new_version, 1))

changed = [
    name for name, digest in before.items()
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

assert "Abrir assistente sem IA" in read("lib/screens/safety_observations_screen.dart")
assert "Matriz e NR sem IA" in read("lib/screens/express_round_screen.dart")
assert "Calcular prioridade e NR sem IA" in read("lib/screens/checklist_screen.dart")
assert "Resumo executivo — sem IA" in read("lib/screens/report_screen.dart")
assert "version: " + new_version in read("pubspec.yaml")

print("OFFLINE_FIELD_ASSISTANT_PATCH_OK", platform, new_version)
print("NR_PRIORITY_ACTION_RECURRENCE_OFFLINE_OK")
print("CHECKLIST_RONDA_VISTORIA_REPORT_INTEGRATION_OK")
print("AI_SYNC_DB_AUTH_HTTP_MEDIA_DRIVE_GS_REPORT_RENDERERS_PRESERVED_OK")

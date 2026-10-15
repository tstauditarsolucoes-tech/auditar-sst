#!/usr/bin/env python3
"""Adiciona conclusão local/editável à Ronda e à Vistoria sem chamar IA.

Mudança aditiva de UI. Não altera IA, sincronização, banco/schema, autenticação,
HTTP, mídia/Drive, Apps Script ou renderizadores de PDF.
"""
from pathlib import Path
import hashlib
import sys

if len(sys.argv) < 3:
    raise SystemExit("uso: patch_offline_conclusion_v329160_v33079.py <APP_DIR> <android|windows>")

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
    "lib/models.dart",
    "lib/screens/checklist_screen.dart",
    "lib/screens/safety_observations_screen.dart",
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
    "lib/services/styled_report_pdf_service.dart",
    "lib/services/auditar_standard3_pdf_service.dart",
    "lib/services/auditar_standard2_pdf_service.dart",
    "lib/services/report_template_service.dart",
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

# RONDA: botão local que NÃO passa por _prepareRoundConclusion/IA.
rel = "lib/screens/express_round_screen.dart"
round_screen = read(rel)

if "Future<void> _generateRoundConclusionOffline()" not in round_screen:
    anchor = "  String _fallbackRoundConclusion() {\n"
    if anchor not in round_screen:
        raise RuntimeError("fallback de conclusao da Ronda nao localizado")

    methods = r'''  String _buildOfflineRoundConclusion() {
    final parts = <String>[
      'Durante a vistoria na empresa ${widget.company.name}, foram registrados ${roundRecords.length} achado(s), sendo $_nonConformities não conformidade(s) e $_conformities conformidade(s)/boa(s) prática(s).',
      if (_highCritical > 0)
        'Foram identificados $_highCritical registro(s) de prioridade alta ou crítica, que devem receber tratamento prioritário.',
      if (_recurringCount > 0)
        'Também foram sinalizados $_recurringCount problema(s) com possível recorrência, recomendando-se verificar a eficácia das correções anteriores.',
      if (_nonConformities > 0)
        'Recomenda-se executar as correções descritas, definir responsáveis e prazos e registrar evidências da regularização.',
      if (_nonConformities == 0 && _conformities > 0)
        'As condições conformes e boas práticas registradas devem ser mantidas e acompanhadas nas próximas verificações.',
      'O acompanhamento posterior deverá verificar a execução e a eficácia das medidas registradas nesta vistoria.',
    ];
    return parts.join(' ');
  }

  Future<void> _generateRoundConclusionOffline() async {
    if (roundRecords.isEmpty) {
      _message('Registre ao menos um achado antes de gerar a conclusão.');
      return;
    }

    final controller = TextEditingController(
      text: _buildOfflineRoundConclusion(),
    );
    final edited = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.description_outlined),
            SizedBox(width: 8),
            Expanded(child: Text('Conclusão sem IA')),
          ],
        ),
        content: SizedBox(
          width: 680,
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Texto gerado localmente a partir dos registros da Ronda. Não usa internet nem IA. Revise e ajuste antes de salvar no relatório.',
                  style: TextStyle(fontSize: 12.5, color: Colors.black54),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: controller,
                  minLines: 8,
                  maxLines: 16,
                  textCapitalization: TextCapitalization.sentences,
                  decoration: InputDecoration(
                    suffixIcon: ExpandTextButton(controller: controller),
                    labelText: 'Conclusão final',
                    alignLabelWithHint: true,
                  ),
                ),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancelar'),
          ),
          FilledButton.icon(
            onPressed: () => Navigator.pop(dialogContext, controller.text.trim()),
            icon: const Icon(Icons.check_rounded),
            label: const Text('Usar no relatório'),
          ),
        ],
      ),
    );
    controller.dispose();
    if (!mounted || edited == null) return;

    final finalText = edited.trim().isEmpty
        ? _buildOfflineRoundConclusion()
        : edited.trim();
    setState(() => roundAiConclusion = finalText);
    await AppDatabase.instance.setSetting(
      'express_round_conclusion_$roundId',
      finalText,
    );
    if (!mounted) return;
    _message('Conclusão sem IA salva e pronta para o relatório.');
  }

'''
    round_screen = round_screen.replace(anchor, methods + anchor, 1)

if "Gerar conclusão sem IA" not in round_screen:
    marker = "onPressed: reviewingRoundWithAi ? null : _reviewRoundWithAi"
    marker_pos = round_screen.find(marker)
    if marker_pos < 0:
        raise RuntimeError("botao de revisao IA da Ronda nao localizado")
    button_start = round_screen.rfind("          FilledButton", 0, marker_pos)
    if button_start < 0:
        raise RuntimeError("inicio do botao IA da Ronda nao localizado")
    button = r'''          OutlinedButton.icon(
            onPressed: roundRecords.isEmpty ? null : _generateRoundConclusionOffline,
            icon: const Icon(Icons.description_outlined),
            label: const Text('Gerar conclusão sem IA'),
          ),
          const SizedBox(height: 8),
'''
    round_screen = round_screen[:button_start] + button + round_screen[button_start:]

write(rel, round_screen)

# VISTORIA: conclusão local com base nos quantitativos já carregados no app.
rel = "lib/screens/report_screen.dart"
report = read(rel)

if "Future<void> _generateOfflineInspectionConclusion()" not in report:
    anchor = "  Future<void> _reviewReportWithAi() async {\n"
    if anchor not in report:
        raise RuntimeError("revisao final da Vistoria nao localizada")

    methods = r'''  String _buildOfflineInspectionConclusion() {
    final applicable = conformes + naoConformes + parciais;
    final total = applicable + na;
    final conformity = applicable == 0
        ? 0
        : ((conformes * 100) / applicable).round();

    if (naoConformes == 0 && parciais == 0) {
      return 'Na data da vistoria, foram registrados $total item(ns), sem não conformidades ou situações parciais entre os critérios aplicáveis. Recomenda-se manter os controles existentes, as boas práticas observadas e o acompanhamento preventivo das condições avaliadas.';
    }

    final parts = <String>[
      'A vistoria registrou $naoConformes não conformidade(s) e $parciais item(ns) parcial(is), com índice de conformidade de $conformity% entre os critérios aplicáveis.',
      'Recomenda-se executar as correções descritas no relatório, definir responsáveis e prazos e manter registro das evidências de regularização.',
      'Os itens pendentes devem ser verificados em acompanhamento posterior para confirmar a execução e a eficácia das medidas adotadas.',
      'Este relatório retrata as condições observadas na data da vistoria e não representa confirmação de regularização posterior.',
    ];
    return parts.join(' ');
  }

  Future<void> _generateOfflineInspectionConclusion() async {
    final db = AppDatabase.instance;
    final header = await db.getInspectionHeader(widget.inspectionId);
    if (!mounted) return;

    final currentConclusion = '${header?['conclusion'] ?? ''}'.trim();
    final generated = _buildOfflineInspectionConclusion();
    final controller = TextEditingController(text: generated);
    final edited = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.description_outlined),
            SizedBox(width: 8),
            Expanded(child: Text('Conclusão do relatório sem IA')),
          ],
        ),
        content: SizedBox(
          width: 720,
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'A conclusão abaixo foi montada localmente com os resultados da vistoria. Não usa internet nem IA. Revise e edite antes de salvar.',
                  style: TextStyle(fontSize: 12.5, color: Colors.black54),
                ),
                if (currentConclusion.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  const Text(
                    'Já existe uma conclusão salva. Ela só será substituída se você confirmar o novo texto.',
                    style: TextStyle(fontSize: 12, color: Colors.black54),
                  ),
                ],
                const SizedBox(height: 12),
                TextField(
                  controller: controller,
                  minLines: 8,
                  maxLines: 16,
                  textCapitalization: TextCapitalization.sentences,
                  decoration: const InputDecoration(
                    labelText: 'Conclusão final',
                    alignLabelWithHint: true,
                  ),
                ),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancelar'),
          ),
          FilledButton.icon(
            onPressed: () => Navigator.pop(dialogContext, controller.text.trim()),
            icon: const Icon(Icons.check_rounded),
            label: const Text('Salvar conclusão'),
          ),
        ],
      ),
    );
    controller.dispose();
    if (!mounted || edited == null) return;

    final finalText = edited.trim().isEmpty ? generated : edited.trim();
    await db.updateInspectionNarrative(
      inspectionId: widget.inspectionId,
      generalNotes: '${header?['general_notes'] ?? ''}'.trim(),
      conclusion: finalText,
    );
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Conclusão sem IA salva. Revise o PDF antes de emitir.'),
      ),
    );
  }

'''
    report = report.replace(anchor, methods + anchor, 1)

if "Conclusão do relatório — sem IA" not in report:
    marker = "Revisão final com IA"
    marker_pos = report.find(marker)
    if marker_pos < 0:
        raise RuntimeError("card de revisao final com IA nao localizado")
    card_start = report.rfind("          Card(", 0, marker_pos)
    if card_start < 0:
        raise RuntimeError("inicio do card IA da Vistoria nao localizado")

    local_card = r'''          Card(
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
              side: BorderSide(color: AuditarBrand.green.withOpacity(.35)),
            ),
            child: Padding(
              padding: const EdgeInsets.all(15),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.description_outlined, color: AuditarBrand.greenDark),
                      SizedBox(width: 9),
                      Expanded(
                        child: Text(
                          'Conclusão do relatório — sem IA',
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
                    'Gera uma conclusão local a partir dos resultados da vistoria. Não usa internet nem IA e o texto pode ser revisado antes de salvar.',
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      onPressed: _generateOfflineInspectionConclusion,
                      icon: const Icon(Icons.edit_note_outlined),
                      label: const Text('Gerar conclusão sem IA'),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 14),
'''
    report = report[:card_start] + local_card + report[card_start:]

write(rel, report)

pub_rel = "pubspec.yaml"
pub = read(pub_rel)
old_version, new_version = (
    ("3.29.159+301", "3.29.160+302")
    if platform == "android"
    else ("3.30.78+265", "3.30.79+266")
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
    raise SystemExit("PROTECTED_FUNCTIONALITY_MODIFIED: " + repr(changed))

final_round = read("lib/screens/express_round_screen.dart")
final_report = read("lib/screens/report_screen.dart")

assert "_buildOfflineRoundConclusion" in final_round
assert "_generateRoundConclusionOffline" in final_round
assert "Gerar conclusão sem IA" in final_round
assert "express_round_conclusion_$roundId" in final_round
assert "_reviewRoundWithAi" in final_round

assert "_buildOfflineInspectionConclusion" in final_report
assert "_generateOfflineInspectionConclusion" in final_report
assert "Conclusão do relatório — sem IA" in final_report
assert "updateInspectionNarrative" in final_report
assert "_reviewReportWithAi" in final_report
assert "reviewFinalReport" in final_report
assert "version: " + new_version in read(pub_rel)

print("OFFLINE_CONCLUSION_PATCH_OK", platform, new_version)
print("RONDA_LOCAL_CONCLUSION_NO_AI_OK")
print("INSPECTION_LOCAL_CONCLUSION_NO_AI_OK")
print("EXISTING_AI_PATHS_PRESERVED_OK")
print("SYNC_DB_SCHEMA_AUTH_HTTP_MEDIA_DRIVE_GS_REPORT_RENDERERS_BYTE_IDENTICAL_OK")

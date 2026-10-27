from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('app/Auditar_SST_v1_5_dashboard')
screen = root / 'lib/screens/express_round_screen.dart'
pdf = root / 'lib/services/express_round_pdf_service.dart'
ai = root / 'lib/services/ai_assistant_service.dart'
pub = root / 'pubspec.yaml'

s = screen.read_text(encoding='utf-8')

old = "  Map<String, dynamic> roundAiReview = const {};\n"
new = "  Map<String, dynamic> roundAiReview = const {};\n  String roundAiConclusion = '';\n"
assert old in s, 'estado roundAiReview não encontrado'
s = s.replace(old, new, 1)

old = "    final activeRound = storedRound.isEmpty ? uuid.v4() : storedRound;\n"
new = "    final activeRound = storedRound.isEmpty ? uuid.v4() : storedRound;\n    final storedConclusion =\n        (await db.getSetting('express_round_conclusion_$activeRound')).trim();\n"
assert old in s, 'activeRound não encontrado'
s = s.replace(old, new, 1)
old = "      roundRecords = current;\n      loading = false;\n"
new = "      roundRecords = current;\n      roundAiConclusion = storedConclusion;\n      loading = false;\n"
assert old in s, 'setState load não encontrado'
s = s.replace(old, new, 1)

anchor = "  Future<void> _reviewRoundWithAi() async {\n"
assert anchor in s, 'método _reviewRoundWithAi não encontrado'
helpers = r'''  String _fallbackRoundConclusion() {
    final parts = <String>[
      'Durante a Ronda Expressa na empresa ${widget.company.name}, foram registrados ${roundRecords.length} achado(s), sendo $_nonConformities não conformidade(s) e $_conformities conformidade(s)/boa(s) prática(s).',
      if (_highCritical > 0)
        'Foram identificados $_highCritical registro(s) de prioridade alta ou crítica, que requerem atenção prioritária e validação presencial das medidas propostas.',
      if (_recurringCount > 0)
        'Também foram sinalizados $_recurringCount problema(s) recorrente(s), recomendando-se verificar a eficácia das correções anteriores e reforçar o acompanhamento.',
      if (_conformities > 0)
        'As conformidades registradas devem ser mantidas e utilizadas como referência de boas práticas nos setores avaliados.',
      if (_nonConformities > 0)
        'Recomenda-se tratar as não conformidades conforme sua prioridade, definir responsáveis e prazos e acompanhar a efetividade das ações corretivas.',
      'As referências normativas sugeridas pela IA devem ser conferidas pelo responsável técnico antes da emissão definitiva do relatório.',
    ];
    return parts.join(' ');
  }

  String _extractAiConclusion(Map<String, dynamic> data) {
    const keys = [
      'finalConclusion',
      'conclusion',
      'conclusao',
      'conclusaoFinal',
      'executiveSummary',
      'managementSummary',
      'summary',
    ];
    for (final key in keys) {
      final value = data[key];
      if (value is String && value.trim().isNotEmpty) return value.trim();
      if (value is List) {
        final text = value
            .map((item) => '$item'.trim())
            .where((item) => item.isNotEmpty)
            .join(' ');
        if (text.isNotEmpty) return text;
      }
    }
    return '';
  }

  Future<String?> _editRoundConclusion(String initial) async {
    final controller = TextEditingController(
      text: initial.trim().isEmpty ? _fallbackRoundConclusion() : initial.trim(),
    );
    final result = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.auto_awesome_rounded),
            SizedBox(width: 8),
            Expanded(child: Text('Conclusão geral da ronda')),
          ],
        ),
        content: SizedBox(
          width: 680,
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'A IA preparou a conclusão com base nos registros da ronda. Revise e ajuste o texto antes de usar no relatório.',
                  style: TextStyle(fontSize: 12.5, color: Colors.black54),
                ),
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
            label: const Text('Usar no relatório'),
          ),
        ],
      ),
    );
    controller.dispose();
    return result;
  }

  Future<bool> _prepareRoundConclusion({bool showFullReview = false}) async {
    Map<String, dynamic> review = roundAiReview;
    if (review.isEmpty) {
      if (mounted) setState(() => reviewingRoundWithAi = true);
      final reply = await AiAssistantService.reviewExpressRound(
        company: widget.company,
        records: roundRecords,
      );
      if (mounted) setState(() => reviewingRoundWithAi = false);
      if (!mounted) return false;
      if (reply.success) {
        review = Map<String, dynamic>.from(reply.result);
        setState(() => roundAiReview = review);
      } else {
        _message('A IA não respondeu agora. Você pode revisar uma conclusão local antes de gerar o relatório.');
      }
    }

    if (showFullReview && review.isNotEmpty) {
      await showDialog<void>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          title: const Row(
            children: [
              Icon(Icons.auto_awesome_rounded),
              SizedBox(width: 8),
              Expanded(child: Text('Revisão da ronda pela IA')),
            ],
          ),
          content: SizedBox(
            width: 650,
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'A análise abaixo é apoio ao responsável técnico. Revise antes de emitir o PDF.',
                    style: TextStyle(fontSize: 12.5, color: Colors.black54),
                  ),
                  const SizedBox(height: 12),
                  ..._reviewWidgets(review),
                ],
              ),
            ),
          ),
          actions: [
            FilledButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('Continuar para a conclusão'),
            ),
          ],
        ),
      );
      if (!mounted) return false;
    }

    final suggested = roundAiConclusion.trim().isNotEmpty
        ? roundAiConclusion
        : _extractAiConclusion(review);
    final edited = await _editRoundConclusion(suggested);
    if (!mounted || edited == null) return false;
    final finalText = edited.trim().isEmpty ? _fallbackRoundConclusion() : edited.trim();
    setState(() => roundAiConclusion = finalText);
    await AppDatabase.instance.setSetting(
      'express_round_conclusion_$roundId',
      finalText,
    );
    return true;
  }

'''
s = s.replace(anchor, helpers + anchor, 1)

start = s.index("  Future<void> _reviewRoundWithAi() async {\n")
end = s.index("  List<Widget> _reviewWidgets", start)
new_method = r'''  Future<void> _reviewRoundWithAi() async {
    if (roundRecords.isEmpty || reviewingRoundWithAi) return;
    await _prepareRoundConclusion(showFullReview: true);
  }

'''
s = s[:start] + new_method + s[end:]

old = "  Future<void> _shareRoundReport(ExpressRoundReportStyle style) async {\n    if (roundRecords.isEmpty || generatingReport) return;\n    setState(() => generatingReport = true);\n"
new = "  Future<void> _shareRoundReport(ExpressRoundReportStyle style) async {\n    if (roundRecords.isEmpty || generatingReport) return;\n    if (roundAiConclusion.trim().isEmpty) {\n      final prepared = await _prepareRoundConclusion();\n      if (!prepared || !mounted) return;\n    }\n    setState(() => generatingReport = true);\n"
assert old in s, '_shareRoundReport inicial não encontrado'
s = s.replace(old, new, 1)

old = "        aiReview: roundAiReview,\n      );\n"
new = "        aiReview: roundAiReview,\n        aiConclusion: roundAiConclusion,\n      );\n"
assert old in s, 'chamada PDF não encontrada'
s = s.replace(old, new, 1)

old = "              const SizedBox(height: 16),\n              FilledButton.icon(\n"
new = "              const SizedBox(height: 12),\n              if (roundAiConclusion.trim().isNotEmpty) ...[\n                Container(\n                  padding: const EdgeInsets.all(12),\n                  decoration: BoxDecoration(\n                    color: AuditarBrand.greenSoft,\n                    borderRadius: BorderRadius.circular(12),\n                  ),\n                  child: const Row(\n                    children: [\n                      Icon(Icons.check_circle_outline_rounded, color: AuditarBrand.greenDark),\n                      SizedBox(width: 8),\n                      Expanded(child: Text('Conclusão da IA revisada e pronta para entrar no relatório.')),\n                    ],\n                  ),\n                ),\n                const SizedBox(height: 10),\n              ],\n              const SizedBox(height: 4),\n              FilledButton.icon(\n"
assert old in s, 'bloco antes do botão IA não encontrado'
s = s.replace(old, new, 1)

screen.write_text(s, encoding='utf-8')

p = pdf.read_text(encoding='utf-8')
old = "    Map<String, dynamic> aiReview = const {},\n  }) async {\n"
new = "    Map<String, dynamic> aiReview = const {},\n    String aiConclusion = '',\n  }) async {\n"
assert old in p, 'assinatura generate não encontrada'
p = p.replace(old, new, 1)
old = "          if (aiReview.isNotEmpty) ...[\n            pw.SizedBox(height: 14),\n            _aiReviewSection(aiReview),\n          ],\n          pw.SizedBox(height: 22),\n"
new = "          if (aiReview.isNotEmpty) ...[\n            pw.SizedBox(height: 14),\n            _aiReviewSection(aiReview),\n          ],\n          if (aiConclusion.trim().isNotEmpty) ...[\n            pw.SizedBox(height: 14),\n            _finalConclusionSection(aiConclusion),\n          ],\n          pw.SizedBox(height: 22),\n"
assert old in p, 'posição da conclusão no PDF não encontrada'
p = p.replace(old, new, 1)

# A seção de revisão não repete a conclusão, que agora possui bloco próprio.
old = "      if (entry.key == 'automaticChecks' || entry.key == 'metrics') continue;\n"
new = "      if (entry.key == 'automaticChecks' ||\n          entry.key == 'metrics' ||\n          entry.key == 'conclusion' ||\n          entry.key == 'conclusao' ||\n          entry.key == 'finalConclusion' ||\n          entry.key == 'conclusaoFinal') continue;\n"
assert old in p, 'filtro _aiReviewSection não encontrado'
p = p.replace(old, new, 1)

anchor = "  static pw.Widget _labelValue(String label, String value) => pw.Padding(\n"
assert anchor in p, '_labelValue não encontrado'
section = r'''  static pw.Widget _finalConclusionSection(String conclusion) => pw.Container(
        padding: const pw.EdgeInsets.all(10),
        decoration: pw.BoxDecoration(
          border: pw.Border.all(color: PdfColors.grey400),
          borderRadius: pw.BorderRadius.circular(5),
        ),
        child: pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            pw.Text(
              'CONCLUSÃO GERAL DA RONDA',
              style: pw.TextStyle(
                fontSize: 11,
                fontWeight: pw.FontWeight.bold,
                color: navy,
              ),
            ),
            pw.SizedBox(height: 5),
            pw.Text(
              conclusion.trim(),
              style: const pw.TextStyle(fontSize: 9, lineSpacing: 2),
              textAlign: pw.TextAlign.justify,
            ),
            pw.SizedBox(height: 5),
            pw.Text(
              'Texto elaborado com apoio de IA e revisado pelo responsável antes da emissão do relatório.',
              style: const pw.TextStyle(fontSize: 7.2, color: PdfColors.grey600),
            ),
          ],
        ),
      );

'''
p = p.replace(anchor, section + anchor, 1)
pdf.write_text(p, encoding='utf-8')

a = ai.read_text(encoding='utf-8')
old = "Revisar a ronda como apoio ao responsável técnico. Valorizar conformidades registradas e priorizar as não conformidades. Referências normativas devem ser tratadas como prováveis para conferência, sem inventar fatos não observados."
new = "Revisar a ronda como apoio ao responsável técnico. Valorizar conformidades registradas e priorizar as não conformidades. Produzir obrigatoriamente uma conclusão geral em texto corrido, equilibrando principais riscos, pontos críticos, conformidades/boas práticas, recomendações gerais e necessidade de acompanhamento. Referências normativas devem ser tratadas como prováveis para conferência, sem inventar fatos não observados."
assert old in a, 'contexto da IA da ronda não encontrado'
a = a.replace(old, new, 1)
ai.write_text(a, encoding='utf-8')

v = pub.read_text(encoding='utf-8')
assert 'version: 3.29.55+197' in v, 'versão base Android inesperada'
v = v.replace('version: 3.29.55+197', 'version: 3.29.56+198', 1)
pub.write_text(v, encoding='utf-8')

print('Android v3.29.56+198: conclusão final da IA editável e incorporada aos PDFs da Ronda.')

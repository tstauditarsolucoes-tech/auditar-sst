from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
APP = REPO / 'app' / 'Auditar_SST_v1_5_dashboard'


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f'missing {label}')
    return text.replace(old, new, 1)


# IA: cria uma entrada específica para a leitura gerencial do Executivo,
# reaproveitando o modo de IA já compatível com o Code.gs implantado.
p = APP / 'lib/services/ai_assistant_service.dart'
t = p.read_text(encoding='utf-8')
marker = '  static Future<AiAssistantReply> chatAboutFinalReport(\n'
insert = '''  /// Prepara uma leitura gerencial para o Relatório Executivo sem alterar\n  /// números, quantidades, status, prazos ou responsáveis registrados.\n  static Future<AiAssistantReply> analyzeExecutiveReport(\n    String inspectionId,\n  ) async {\n    final reply = await reviewFinalReport(inspectionId);\n    if (!reply.success) return reply;\n\n    final result = Map<String, dynamic>.from(reply.result);\n    result.remove('actionPlanSuggestions');\n    return AiAssistantReply(\n      success: true,\n      message: 'Análise gerencial preparada para o Relatório Executivo.',\n      result: result,\n    );\n  }\n\n'''
t = replace_once(t, marker, insert + marker, 'ai executive method')
p.write_text(t, encoding='utf-8')


# Permite que o salvamento local receba a análise já preparada, sem nova chamada.
p = APP / 'lib/services/report_file_service.dart'
t = p.read_text(encoding='utf-8')
t = replace_once(
    t,
    '''    bool executive = false,\n    bool? includeActionPlan,\n  }) async {''',
    '''    bool executive = false,\n    bool? includeActionPlan,\n    Map<String, dynamic>? executiveAiAnalysis,\n  }) async {''',
    'report file signature',
)
t = replace_once(
    t,
    '''      executive: executive,\n      includeActionPlan: includeActionPlan,\n    );''',
    '''      executive: executive,\n      includeActionPlan: includeActionPlan,\n      executiveAiAnalysis: executiveAiAnalysis,\n    );''',
    'report file pass ai',
)
p.write_text(t, encoding='utf-8')


# PDF Executivo: resumo universal do que providenciar + bloco gerencial de IA.
p = APP / 'lib/services/pdf_service.dart'
t = p.read_text(encoding='utf-8')
t = replace_once(
    t,
    '''    bool executive = false,\n    bool? includeActionPlan,\n  }) async {''',
    '''    bool executive = false,\n    bool? includeActionPlan,\n    Map<String, dynamic>? executiveAiAnalysis,\n  }) async {''',
    'pdf signature',
)

old = '''    final highPriorityActions = pendingActions.where((action) {\n      final priority = action.priority.toLowerCase();\n      return priority.contains('alta') ||\n          priority.contains('grave') ||\n          priority.contains('crítica') ||\n          priority.contains('critica');\n    }).toList();\n'''
new = old + '''    final executiveProvisionGroups = _buildExecutiveProvisionGroups(\n      issues: issueAnswers,\n      ncByAnswer: ncByAnswer,\n      actionsByAnswer: actionsByAnswer,\n    );\n    final aiCriticalSummary = executive\n        ? '${executiveAiAnalysis?['criticalSummary'] ?? ''}'.trim()\n        : '';\n    final aiConclusion = executive\n        ? '${executiveAiAnalysis?['conclusion'] ?? ''}'.trim()\n        : '';\n    final rawAiLimitations = executiveAiAnalysis?['limitations'];\n    final aiLimitations = executive && rawAiLimitations is List\n        ? rawAiLimitations\n            .map((item) => '$item'.trim())\n            .where((item) => item.isNotEmpty)\n            .take(6)\n            .toList()\n        : <String>[];\n'''
t = replace_once(t, old, new, 'pdf ai vars')

old = '''        _executiveOperationalMetrics(\n          issueCount: issueAnswers.length,\n          pendingCount: pendingActions.length,\n          completedCount: completedActionsExecutive.length,\n          overdueCount: overdueActions.length,\n          highPriorityCount: highPriorityActions.length,\n          isExtinguisherReport: isExtinguisherReport,\n          maintenanceRechargeCount: maintenanceRechargeCount,\n          replacementCount: replacementCount,\n          brokenSealCount: brokenSealCount,\n          missingSignCount: missingSignCount,\n          incompatibleSignCount: incompatibleSignCount,\n          obstructedAccessCount: obstructedAccessCount,\n        ),\n        pw.SizedBox(height: 16),\n        _sectionHeader(\n          'QUADRO DE PROVIDÊNCIAS',\n'''
new = '''        _executiveOperationalMetrics(\n          issueCount: issueAnswers.length,\n          pendingCount: pendingActions.length,\n          completedCount: completedActionsExecutive.length,\n          overdueCount: overdueActions.length,\n          highPriorityCount: highPriorityActions.length,\n          isExtinguisherReport: isExtinguisherReport,\n          maintenanceRechargeCount: maintenanceRechargeCount,\n          replacementCount: replacementCount,\n          brokenSealCount: brokenSealCount,\n          missingSignCount: missingSignCount,\n          incompatibleSignCount: incompatibleSignCount,\n          obstructedAccessCount: obstructedAccessCount,\n        ),\n        pw.SizedBox(height: 16),\n        _sectionHeader(\n          'O QUE A EMPRESA PRECISA PROVIDENCIAR',\n          subtitle:\n              'Agrupamento automático das providências abertas. As quantidades são calculadas somente a partir dos registros da vistoria.',\n        ),\n        pw.SizedBox(height: 8),\n        _executiveProvisionSummary(executiveProvisionGroups),\n        if (executiveAiAnalysis != null &&\n            (aiCriticalSummary.isNotEmpty ||\n                aiConclusion.isNotEmpty ||\n                aiLimitations.isNotEmpty)) ...[\n          pw.SizedBox(height: 16),\n          _sectionHeader(\n            'ANÁLISE GERENCIAL POR IA',\n            subtitle:\n                'A IA interpreta os dados já registrados. Quantidades, status, prazos e responsáveis não são inventados nem alterados pela IA.',\n          ),\n          pw.SizedBox(height: 8),\n          _executiveAiAnalysisCard(\n            criticalSummary: aiCriticalSummary,\n            conclusion: aiConclusion,\n            limitations: aiLimitations,\n          ),\n        ],\n        pw.SizedBox(height: 16),\n        _sectionHeader(\n          'QUADRO DE PROVIDÊNCIAS',\n'''
t = replace_once(t, old, new, 'pdf executive new sections')

t = replace_once(
    t,
    r"      r'\b(\d{1,3})\s*(?:extintor(?:es)?|equipamento(?:s)?|unidade(?:s)?)\b',",
    r"      r'\b(\d{1,3})\s*(?:extintor(?:es)?|equipamento(?:s)?|unidade(?:s)?|item(?:s)?|ponto(?:s)?|placa(?:s)?|maquina(?:s)?|máquina(?:s)?|escada(?:s)?|trabalhador(?:es)?|colaborador(?:es)?|pessoa(?:s)?)\b',",
    'quantity regex',
)

marker = '  static pw.Widget _executiveOperationalMetrics({\n'
helpers = r'''  static bool _isExecutiveCompleted(String status) {
    final normalized = _normalizeForSearch(status);
    return normalized.contains('conclu') ||
        normalized.contains('resolvid') ||
        normalized.contains('fechad');
  }

  static String _executiveProvisionCategory(String value) {
    final text = _normalizeForSearch(value);

    bool hasAny(List<String> terms) =>
        terms.any((term) => text.contains(_normalizeForSearch(term)));

    if (hasAny(const [
      'bloquear', 'bloqueio', 'interditar', 'interdição', 'isolar',
      'retirar de uso', 'suspender uso',
    ])) {
      return 'Bloqueio / isolamento';
    }
    if (hasAny(const [
      'treinamento', 'treinar', 'capacitar', 'capacitação', 'dds',
      'orientar trabalhador', 'reciclagem',
    ])) {
      return 'Treinamento / orientação';
    }
    if (hasAny(const [
      'epi', 'capacete', 'botina', 'luva', 'óculos', 'oculos',
      'respirador', 'protetor auricular',
    ])) {
      return 'EPI / fornecimento';
    }
    if (hasAny(const [
      'sinalização', 'sinalizacao', 'placa', 'demarcar', 'identificar',
      'identificação', 'rotular', 'faixa',
    ])) {
      return 'Sinalização / identificação';
    }
    if (hasAny(const [
      'pgr', 'pcmso', 'ltcat', 'laudo', 'procedimento', 'pop',
      'ordem de serviço', 'documento', 'registro documental',
    ])) {
      return 'Adequação documental';
    }
    if (hasAny(const [
      'limpeza', 'limpar', 'organização', 'organizacao', 'organizar',
      'higienizar',
    ])) {
      return 'Limpeza / organização';
    }
    if (hasAny(const [
      'substituir', 'substituição', 'substituicao', 'trocar', 'troca de',
    ])) {
      return 'Substituição';
    }
    if (hasAny(const [
      'instalar', 'instalação', 'instalacao', 'guarda-corpo', 'corrimão',
      'corrimao', 'proteção coletiva', 'protecao coletiva',
      'proteção física', 'protecao fisica', 'barreira', 'grade de proteção',
    ])) {
      return 'Instalação / proteção coletiva';
    }
    if (hasAny(const [
      'manutenção', 'manutencao', 'reparar', 'reparo', 'consertar',
      'corrigir', 'ajustar', 'recarga', 'revisar equipamento',
    ])) {
      return 'Manutenção / reparo';
    }
    if (hasAny(const [
      'comprar', 'adquirir', 'aquisição', 'aquisicao', 'fornecer',
      'disponibilizar',
    ])) {
      return 'Compra / fornecimento';
    }
    return 'Outras providências';
  }

  static Map<String, int> _buildExecutiveProvisionGroups({
    required List<InspectionAnswer> issues,
    required Map<String, NonConformity> ncByAnswer,
    required Map<String, List<ActionPlan>> actionsByAnswer,
  }) {
    final totals = <String, int>{};

    for (final answer in issues) {
      final linked = actionsByAnswer[answer.id] ?? <ActionPlan>[];
      final pending = linked
          .where((action) => !_isExecutiveCompleted(action.status))
          .toList();
      final nc = ncByAnswer[answer.id];

      if (linked.isNotEmpty && pending.isEmpty) continue;
      if (linked.isEmpty && nc != null && _isExecutiveCompleted(nc.status)) {
        continue;
      }

      final action = pending.isEmpty ? null : pending.first;
      final source = [
        action?.correctiveAction ?? '',
        answer.recommendation,
        nc?.recommendation ?? '',
        answer.observation,
        nc?.description ?? '',
        answer.questionText,
      ].where((value) => value.trim().isNotEmpty).join(' ');
      final category = _executiveProvisionCategory(source);
      final quantity = _quantityForIssue(answer, linked);
      totals[category] = (totals[category] ?? 0) + quantity;
    }

    final entries = totals.entries.toList()
      ..sort((a, b) {
        final countCompare = b.value.compareTo(a.value);
        return countCompare != 0 ? countCompare : a.key.compareTo(b.key);
      });
    return {for (final entry in entries) entry.key: entry.value};
  }

  static pw.Widget _executiveProvisionSummary(Map<String, int> groups) {
    if (groups.isEmpty) {
      return _emptyState(
        'Nenhuma providência aberta foi identificada para agrupamento.',
        positive: true,
      );
    }

    return pw.Container(
      width: double.infinity,
      padding: const pw.EdgeInsets.all(10),
      decoration: pw.BoxDecoration(
        color: PdfColors.grey50,
        border: pw.Border.all(color: _line),
        borderRadius: pw.BorderRadius.circular(7),
      ),
      child: pw.Column(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: groups.entries
            .map(
              (entry) => pw.Padding(
                padding: const pw.EdgeInsets.only(bottom: 4),
                child: pw.Row(
                  children: [
                    pw.Container(
                      width: 22,
                      alignment: pw.Alignment.center,
                      padding: const pw.EdgeInsets.symmetric(vertical: 3),
                      decoration: pw.BoxDecoration(
                        color: _greenSoft,
                        borderRadius: pw.BorderRadius.circular(4),
                      ),
                      child: pw.Text(
                        '${entry.value}',
                        style: pw.TextStyle(
                          fontSize: 8,
                          fontWeight: pw.FontWeight.bold,
                          color: _green,
                        ),
                      ),
                    ),
                    pw.SizedBox(width: 7),
                    pw.Expanded(
                      child: pw.Text(
                        entry.key,
                        style: pw.TextStyle(
                          fontSize: 7.4,
                          fontWeight: pw.FontWeight.bold,
                          color: _navy,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            )
            .toList(),
      ),
    );
  }

  static pw.Widget _executiveAiAnalysisCard({
    required String criticalSummary,
    required String conclusion,
    required List<String> limitations,
  }) {
    final children = <pw.Widget>[];
    if (criticalSummary.isNotEmpty) {
      children.add(_detailLine('IA · O que merece sua atenção', criticalSummary));
    }
    if (conclusion.isNotEmpty) {
      children.add(_detailLine('Síntese gerencial', conclusion));
    }
    if (limitations.isNotEmpty) {
      children.add(pw.SizedBox(height: 3));
      children.add(
        pw.Text(
          'Pontos a conferir pelo técnico:',
          style: pw.TextStyle(
            fontSize: 7,
            fontWeight: pw.FontWeight.bold,
            color: _navy,
          ),
        ),
      );
      children.add(pw.SizedBox(height: 2));
      for (final item in limitations) {
        children.add(
          pw.Padding(
            padding: const pw.EdgeInsets.only(bottom: 2),
            child: pw.Text(
              '• $item',
              style: const pw.TextStyle(fontSize: 6.8, color: _grey),
            ),
          ),
        );
      }
    }
    children.add(pw.SizedBox(height: 4));
    children.add(
      pw.Text(
        'A análise por IA é apoio gerencial e deve ser conferida pelo profissional responsável antes da emissão.',
        style: const pw.TextStyle(fontSize: 6.5, color: _grey),
      ),
    );

    return pw.Container(
      width: double.infinity,
      padding: const pw.EdgeInsets.all(10),
      decoration: pw.BoxDecoration(
        color: PdfColors.blue50,
        border: pw.Border.all(color: _navy, width: .5),
        borderRadius: pw.BorderRadius.circular(7),
      ),
      child: pw.Column(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: children,
      ),
    );
  }

'''
t = replace_once(t, marker, helpers + marker, 'pdf helpers')
p.write_text(t, encoding='utf-8')


# Tela de relatórios: opção de IA, preparação/caching e fallback sem bloquear PDF.
p = APP / 'lib/screens/report_screen.dart'
t = p.read_text(encoding='utf-8')
t = replace_once(
    t,
    '''  bool executivePdfBusy = false;\n  bool aiReviewBusy = false;''',
    '''  bool executivePdfBusy = false;\n  bool executiveAiEnabled = true;\n  bool executiveAiBusy = false;\n  Map<String, dynamic>? executiveAiAnalysis;\n  String executiveAiStatus = '';\n  bool aiReviewBusy = false;''',
    'report ai states',
)
t = replace_once(
    t,
    """    final auto = await db.getSetting('drive_auto_upload', fallback: 'true');\n    final header = await db.getInspectionHeader(widget.inspectionId);""",
    """    final auto = await db.getSetting('drive_auto_upload', fallback: 'true');\n    final executiveAi = await db.getSetting(\n      'executive_ai_enabled',\n      fallback: 'true',\n    );\n    final header = await db.getInspectionHeader(widget.inspectionId);""",
    'load ai setting',
)
t = replace_once(
    t,
    '''      autoUpload = auto == 'true';\n      includeActionPlan = (header?['include_action_plan'] is int)''',
    '''      autoUpload = auto == 'true';\n      executiveAiEnabled = executiveAi == 'true';\n      includeActionPlan = (header?['include_action_plan'] is int)''',
    'assign ai setting',
)

marker = '  Future<void> _sharePdf({required bool executive}) async {\n'
methods = '''  Future<void> _setExecutiveAiEnabled(bool value) async {\n    await AppDatabase.instance.setSetting(\n      'executive_ai_enabled',\n      value ? 'true' : 'false',\n    );\n    if (!mounted) return;\n    setState(() {\n      executiveAiEnabled = value;\n      if (!value) executiveAiStatus = '';\n    });\n  }\n\n  Future<Map<String, dynamic>?> _prepareExecutiveAi({\n    bool notify = true,\n  }) async {\n    if (!executiveAiEnabled) return null;\n    if (executiveAiAnalysis != null) return executiveAiAnalysis;\n    if (executiveAiBusy) return null;\n\n    setState(() {\n      executiveAiBusy = true;\n      executiveAiStatus = 'Analisando os dados gerenciais com IA...';\n    });\n\n    try {\n      final reply = await AiAssistantService.analyzeExecutiveReport(\n        widget.inspectionId,\n      ).timeout(\n        const Duration(seconds: 35),\n        onTimeout: () => const AiAssistantReply(\n          success: false,\n          message:\n              'A IA excedeu o tempo desta análise. O PDF pode ser gerado normalmente sem a camada de IA.',\n        ),\n      );\n\n      if (!mounted) return reply.success ? reply.result : null;\n      if (reply.success) {\n        final analysis = Map<String, dynamic>.from(reply.result);\n        setState(() {\n          executiveAiAnalysis = analysis;\n          executiveAiStatus = 'Análise gerencial por IA pronta para o PDF.';\n        });\n        if (notify) {\n          ScaffoldMessenger.of(context).showSnackBar(\n            const SnackBar(\n              content: Text(\n                'Análise gerencial pronta. O Relatório Executivo incluirá a seção de IA.',\n              ),\n            ),\n          );\n        }\n        return analysis;\n      }\n\n      setState(() {\n        executiveAiStatus =\n            'IA indisponível nesta tentativa. O Executivo continuará disponível sem IA.';\n      });\n      if (notify) {\n        ScaffoldMessenger.of(context).showSnackBar(\n          SnackBar(content: Text(reply.message)),\n        );\n      }\n      return null;\n    } finally {\n      if (mounted) setState(() => executiveAiBusy = false);\n    }\n  }\n\n'''
t = replace_once(t, marker, methods + marker, 'report ai methods')

t = replace_once(
    t,
    '''    try {\n      final bytes = await PdfService.generateInspectionPdf(\n        widget.inspectionId,\n        executive: executive,\n        includeActionPlan: includeActionPlan,\n      );''',
    '''    try {\n      Map<String, dynamic>? aiAnalysis;\n      if (executive && executiveAiEnabled) {\n        aiAnalysis = executiveAiAnalysis ??\n            await _prepareExecutiveAi(notify: false);\n        if (aiAnalysis == null && mounted) {\n          ScaffoldMessenger.of(context).showSnackBar(\n            const SnackBar(\n              content: Text(\n                'A IA não ficou disponível. O Relatório Executivo será gerado com os dados calculados pelo sistema, sem a análise por IA.',\n              ),\n            ),\n          );\n        }\n      }\n\n      final bytes = await PdfService.generateInspectionPdf(\n        widget.inspectionId,\n        executive: executive,\n        includeActionPlan: includeActionPlan,\n        executiveAiAnalysis: aiAnalysis,\n      );''',
    'share ai pdf',
)

t = replace_once(
    t,
    '''  Future<void> _saveLocal({required bool executive}) async {\n    try {\n      final path = await ReportFileService.savePdfLocally(\n        widget.inspectionId,\n        executive: executive,\n        includeActionPlan: includeActionPlan,\n      );''',
    '''  Future<void> _saveLocal({required bool executive}) async {\n    try {\n      Map<String, dynamic>? aiAnalysis;\n      if (executive && executiveAiEnabled) {\n        aiAnalysis = executiveAiAnalysis ??\n            await _prepareExecutiveAi(notify: false);\n      }\n      final path = await ReportFileService.savePdfLocally(\n        widget.inspectionId,\n        executive: executive,\n        includeActionPlan: includeActionPlan,\n        executiveAiAnalysis: aiAnalysis,\n      );''',
    'save local ai',
)

old = '''                  SwitchListTile.adaptive(\n                    contentPadding: EdgeInsets.zero,\n                    value: includeActionPlan,\n                    title: const Text('Incluir plano de ação no relatório'),\n                    subtitle: const Text(\n                      'Desative quando quiser um PDF mais direto.',\n                    ),\n                    onChanged: (value) => _saveReportPreferences(value: value),\n                  ),\n                  if (reportSignatureMode == 'gov') ...['''
new = '''                  SwitchListTile.adaptive(\n                    contentPadding: EdgeInsets.zero,\n                    value: includeActionPlan,\n                    title: const Text('Incluir plano de ação no relatório'),\n                    subtitle: const Text(\n                      'Desative quando quiser um PDF mais direto.',\n                    ),\n                    onChanged: (value) => _saveReportPreferences(value: value),\n                  ),\n                  const Divider(height: 18),\n                  SwitchListTile.adaptive(\n                    contentPadding: EdgeInsets.zero,\n                    value: executiveAiEnabled,\n                    title: const Text(\n                      'Incluir análise gerencial por IA no Executivo',\n                    ),\n                    subtitle: const Text(\n                      'A IA organiza prioridades e a leitura gerencial. Quantidades, status, prazos e responsáveis continuam vindo dos registros do sistema.',\n                    ),\n                    onChanged: executiveAiBusy\n                        ? null\n                        : (value) => _setExecutiveAiEnabled(value),\n                  ),\n                  if (executiveAiEnabled) ...[\n                    const SizedBox(height: 4),\n                    SizedBox(\n                      width: double.infinity,\n                      child: OutlinedButton.icon(\n                        onPressed: executiveAiBusy || executiveAiAnalysis != null\n                            ? null\n                            : () => _prepareExecutiveAi(),\n                        icon: executiveAiBusy\n                            ? const SizedBox(\n                                width: 17,\n                                height: 17,\n                                child: CircularProgressIndicator(strokeWidth: 2),\n                              )\n                            : const Icon(Icons.psychology_alt_outlined),\n                        label: Text(\n                          executiveAiBusy\n                              ? 'Preparando análise gerencial...'\n                              : executiveAiAnalysis != null\n                                  ? 'Análise gerencial pronta'\n                                  : 'Preparar análise gerencial com IA',\n                        ),\n                      ),\n                    ),\n                    if (executiveAiStatus.isNotEmpty) ...[\n                      const SizedBox(height: 6),\n                      Text(\n                        executiveAiStatus,\n                        style: TextStyle(\n                          color: executiveAiAnalysis != null\n                              ? Colors.green.shade800\n                              : Colors.grey.shade700,\n                          fontSize: 12,\n                          fontWeight: FontWeight.w600,\n                        ),\n                      ),\n                    ],\n                  ],\n                  if (reportSignatureMode == 'gov') ...['''
t = replace_once(t, old, new, 'ai switch ui')

t = replace_once(
    t,
    """                    ? 'Versão gerencial com quantitativos, quadro de providências, fotos das pendências, responsáveis, prazos, resolvidos e conclusão.'\n                    : 'Versão gerencial com quantitativos, quadro de providências, fotos das pendências e conclusão.',""",
    """                    ? 'Versão gerencial com quantitativos, resumo do que providenciar, análise por IA, quadro de providências, fotos, responsáveis, prazos, resolvidos e conclusão.'\n                    : 'Versão gerencial com quantitativos, resumo do que providenciar, análise por IA, fotos das pendências e conclusão.',""",
    'executive subtitle',
)
p.write_text(t, encoding='utf-8')


# Nova versão sem alterar a base funcional anterior.
p = APP / 'pubspec.yaml'
t = p.read_text(encoding='utf-8')
t = replace_once(t, 'version: 3.29.17+160', 'version: 3.29.18+161', 'version')
p.write_text(t, encoding='utf-8')

p = APP / 'lib/screens/home_screen.dart'
t = p.read_text(encoding='utf-8')
t = t.replace('Auditar SST • versão 3.29.17', 'Auditar SST • versão 3.29.18')
t = t.replace(
    'Auditar SST para Windows • versão 3.29.17',
    'Auditar SST para Windows • versão 3.29.18',
)
p.write_text(t, encoding='utf-8')


# Validação estrutural antes de chamar Flutter.
checks = {
    'versão': 'version: 3.29.18+161' in (APP / 'pubspec.yaml').read_text(encoding='utf-8'),
    'método IA executivo': 'analyzeExecutiveReport' in (APP / 'lib/services/ai_assistant_service.dart').read_text(encoding='utf-8'),
    'opção IA executivo': 'executiveAiEnabled' in (APP / 'lib/screens/report_screen.dart').read_text(encoding='utf-8'),
    'resumo universal': 'O QUE A EMPRESA PRECISA PROVIDENCIAR' in (APP / 'lib/services/pdf_service.dart').read_text(encoding='utf-8'),
    'bloco IA PDF': 'ANÁLISE GERENCIAL POR IA' in (APP / 'lib/services/pdf_service.dart').read_text(encoding='utf-8'),
    'passagem da IA': 'executiveAiAnalysis' in (APP / 'lib/services/report_file_service.dart').read_text(encoding='utf-8'),
}
missing = [name for name, ok in checks.items() if not ok]
if missing:
    raise RuntimeError('Validações v3.29.18 falharam: ' + ', '.join(missing))

print('v3.29.18+161: Relatório Executivo universal com análise gerencial por IA aplicado.')

#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    print('uso: patch_executive_report_v32914.py <raiz-do-app>', file=sys.stderr)
    raise SystemExit(2)

root = Path(sys.argv[1]).resolve()
if not root.exists():
    raise RuntimeError(f'raiz inválida: {root}')
pdf = root/'lib/services/pdf_service.dart'
report = root/'lib/screens/report_screen.dart'
pub = root/'pubspec.yaml'
text = pdf.read_text()

old = """    // v3.29.5: em outro dispositivo o caminho local antigo pode não existir.\n    // A mídia estruturada já é sincronizada pelo app; aqui apenas garantimos,\n    // sob demanda, que os bytes disponíveis no Drive sejam baixados antes de\n    // renderizar o relatório completo. Em modo offline o relatório continua.\n    if (!executive) {\n      try {\n        await MediaSyncService.downloadMissing();\n      } catch (_) {\n        // Mantém a geração offline e o comportamento anterior se não houver rede.\n      }\n    }\n"""
new = """    // v3.29.14: tanto o relatório completo quanto o executivo tentam\n    // recuperar a mídia sincronizada antes de renderizar. Isso garante que a\n    // gerência receba as evidências fotográficas também quando o PDF é gerado\n    // em outro dispositivo. Em modo offline o relatório continua normalmente.\n    try {\n      await MediaSyncService.downloadMissing();\n    } catch (_) {\n      // Mantém a geração offline se não houver rede ou Drive disponível.\n    }\n"""
assert old in text
text = text.replace(old, new, 1)

old = """    final ncByAnswer = <String, NonConformity>{\n      for (final nc in ncs) nc.answerId: nc,\n    };\n"""
new = """    final ncByAnswer = <String, NonConformity>{\n      for (final nc in ncs) nc.answerId: nc,\n    };\n    final issueAnswers = answers\n        .where((e) => e.status == 'Não Conforme' || e.status == 'Parcial')\n        .toList();\n    final actionsByAnswer = <String, List<ActionPlan>>{};\n    for (final action in actions) {\n      actionsByAnswer.putIfAbsent(action.answerId, () => <ActionPlan>[]).add(action);\n    }\n    final pendingActions =\n        actions.where((action) => action.status != 'Concluído').toList();\n    final completedActionsExecutive =\n        actions.where((action) => action.status == 'Concluído').toList();\n    final now = DateTime.now();\n    final overdueActions = pendingActions.where((action) {\n      final due = action.dueDate;\n      if (due == null) return false;\n      return due.isBefore(DateTime(now.year, now.month, now.day));\n    }).toList();\n    final highPriorityActions = pendingActions.where((action) {\n      final priority = action.priority.toLowerCase();\n      return priority.contains('alta') ||\n          priority.contains('grave') ||\n          priority.contains('crítica') ||\n          priority.contains('critica');\n    }).toList();\n    final isExtinguisherReport = _normalizeForSearch(\n      '$checklist $sector $area',\n    ).contains('extintor');\n    final maintenanceRechargeCount = _sumIssueQuantitiesMatching(\n      issueAnswers,\n      actionsByAnswer,\n      const ['recarga', 'manutencao', 'manutenção', 'encaminhar para inspecao', 'encaminhar para inspeção'],\n    );\n    final replacementCount = _sumIssueQuantitiesMatching(\n      issueAnswers,\n      actionsByAnswer,\n      const ['substituir', 'substituicao', 'substituição', 'trocar o extintor', 'troca do extintor'],\n    );\n    final brokenSealCount = _sumIssueQuantitiesMatching(\n      issueAnswers,\n      actionsByAnswer,\n      const ['lacre rompido', 'lacre violado', 'ruptura do lacre'],\n    );\n    final missingSignCount = _sumIssueQuantitiesMatching(\n      issueAnswers,\n      actionsByAnswer,\n      const ['sem placa', 'ausencia de placa', 'ausência de placa', 'falta de placa', 'sem sinalizacao', 'sem sinalização'],\n    );\n    final incompatibleSignCount = _sumIssueQuantitiesMatching(\n      issueAnswers,\n      actionsByAnswer,\n      const ['placa incompativel', 'placa incompatível', 'placa nao corresponde', 'placa não corresponde', 'sinalizacao incompativel', 'sinalização incompatível'],\n    );\n    final obstructedAccessCount = _sumIssueQuantitiesMatching(\n      issueAnswers,\n      actionsByAnswer,\n      const ['obstruido', 'obstruído', 'obstrucao', 'obstrução', 'acesso bloqueado', 'acesso parcialmente bloqueado', 'dificuldade de acesso'],\n    );\n"""
assert old in text
text = text.replace(old, new, 1)

old = """      _inspectionDataCard(\n        reportNumber: reportNumber,\n        companyName: companyName,\n        cnpj: '${header['company_cnpj'] ?? ''}',\n        worksite: worksite,\n        address: '${header['worksite_address'] ?? ''}',\n        sector: sector,\n        area: area,\n        checklist: checklist,\n        dateText: dateText,\n        technicianName: technicianName,\n      ),\n      pw.SizedBox(height: 20),\n      _sectionHeader(\n"""
new = """      _inspectionDataCard(\n        reportNumber: reportNumber,\n        companyName: companyName,\n        cnpj: '${header['company_cnpj'] ?? ''}',\n        worksite: worksite,\n        address: '${header['worksite_address'] ?? ''}',\n        sector: sector,\n        area: area,\n        checklist: checklist,\n        dateText: dateText,\n        technicianName: technicianName,\n      ),\n      if (executive) ...[\n        pw.SizedBox(height: 20),\n        _sectionHeader(\n          'QUANTITATIVO OPERACIONAL',\n          subtitle: isExtinguisherReport\n              ? 'Quantidades para decisão da gerência. Os números são calculados a partir dos registros da vistoria.'\n              : 'Situação das providências registradas para acompanhamento da gerência.',\n        ),\n        pw.SizedBox(height: 8),\n        _executiveOperationalMetrics(\n          issueCount: issueAnswers.length,\n          pendingCount: pendingActions.length,\n          completedCount: completedActionsExecutive.length,\n          overdueCount: overdueActions.length,\n          highPriorityCount: highPriorityActions.length,\n          isExtinguisherReport: isExtinguisherReport,\n          maintenanceRechargeCount: maintenanceRechargeCount,\n          replacementCount: replacementCount,\n          brokenSealCount: brokenSealCount,\n          missingSignCount: missingSignCount,\n          incompatibleSignCount: incompatibleSignCount,\n          obstructedAccessCount: obstructedAccessCount,\n        ),\n        pw.SizedBox(height: 16),\n        _sectionHeader(\n          'QUADRO DE PROVIDÊNCIAS',\n          subtitle: issueAnswers.isEmpty\n              ? 'Nenhuma providência pendente foi identificada.'\n              : 'Onde está o problema, o que foi encontrado, o que deve ser feito, quantidade, prioridade e status.',\n        ),\n        pw.SizedBox(height: 8),\n        _executiveIssueTable(\n          issues: issueAnswers,\n          ncByAnswer: ncByAnswer,\n          actionsByAnswer: actionsByAnswer,\n          fallbackSector: sector,\n          fallbackArea: area,\n        ),\n        if (isExtinguisherReport) ...[\n          pw.SizedBox(height: 5),\n          pw.Text(\n            'Nota: quando um único registro reunir mais de um equipamento, informe a quantidade no texto da ocorrência. Para contagem física exata, prefira registrar cada extintor separadamente.',\n            style: const pw.TextStyle(fontSize: 6.8, color: _grey),\n          ),\n        ],\n      ],\n      pw.SizedBox(height: 20),\n      _sectionHeader(\n"""
assert old in text
text = text.replace(old, new, 1)

old = """    final issues =\n        answers\n            .where((e) => e.status == 'Não Conforme' || e.status == 'Parcial')\n            .toList();\n\n    if (issues.isEmpty) {\n"""
new = """    final issues = issueAnswers;\n\n    if (issues.isEmpty) {\n"""
assert old in text
text = text.replace(old, new, 1)

old = """        final nc = ncByAnswer[answer.id];\n\n        body.add(\n          _issueCard(\n            answer: answer,\n            index: index + 1,\n            nc: nc,\n            executive: executive,\n          ),\n        );\n"""
new = """        final nc = ncByAnswer[answer.id];\n        final linkedActions = actionsByAnswer[answer.id] ?? <ActionPlan>[];\n        final primaryAction = linkedActions.isEmpty ? null : linkedActions.first;\n        final executiveLocation = _executiveLocation(\n          primaryAction,\n          sector,\n          area,\n        );\n\n        body.add(\n          _issueCard(\n            answer: answer,\n            index: index + 1,\n            nc: nc,\n            executive: executive,\n            executiveAction: primaryAction,\n            executiveLocation: executiveLocation,\n            executiveQuantity: _quantityForIssue(answer, linkedActions),\n          ),\n        );\n"""
assert old in text
text = text.replace(old, new, 1)

old = """              caption: answer.status == 'Não Conforme'\n                  ? (nc?.code.isNotEmpty == true\n                      ? '${nc!.code} - Evidência principal'\n                      : 'NC ${index + 1} - Evidência principal')\n                  : 'Item parcial ${index + 1} - Evidência principal',\n"""
new = """              caption: answer.status == 'Não Conforme'\n                  ? (nc?.code.isNotEmpty == true\n                      ? '${nc!.code} - Evidência principal - $executiveLocation'\n                      : 'NC ${index + 1} - Evidência principal - $executiveLocation')\n                  : 'Item parcial ${index + 1} - Evidência principal - $executiveLocation',\n"""
assert old in text
text = text.replace(old, new, 1)

start = text.index("    if (includeActionPlanInPdf && executive) {")
end = text.index("\n\n    // O relatório executivo para aqui", start)
new_block = """    if (includeActionPlanInPdf && executive) {\n      body.add(pw.SizedBox(height: 8));\n      body.add(\n        _sectionHeader(\n          'O QUE FICOU PENDENTE',\n          subtitle: 'Providências ainda abertas, com local, responsável, urgência, prazo e status.',\n        ),\n      );\n      body.add(pw.SizedBox(height: 8));\n\n      if (pendingActions.isEmpty) {\n        body.add(\n          _emptyState(\n            issueAnswers.isEmpty\n                ? 'Nenhuma ação corretiva necessária para esta vistoria.'\n                : 'Não há plano de ação pendente cadastrado para os itens identificados.',\n            positive: issueAnswers.isEmpty,\n          ),\n        );\n      } else {\n        for (var i = 0; i < pendingActions.length; i++) {\n          body.add(_actionCard(pendingActions[i], i + 1, executive: true));\n          body.add(pw.SizedBox(height: 8));\n        }\n      }\n\n      if (completedActionsExecutive.isNotEmpty) {\n        body.add(pw.SizedBox(height: 10));\n        body.add(\n          _sectionHeader(\n            'O QUE JÁ FOI RESOLVIDO',\n            subtitle: 'Ações registradas como concluídas para demonstrar a evolução das correções.',\n          ),\n        );\n        body.add(pw.SizedBox(height: 8));\n        for (var i = 0; i < completedActionsExecutive.length; i++) {\n          body.add(_actionCard(completedActionsExecutive[i], i + 1, executive: true));\n          body.add(pw.SizedBox(height: 8));\n        }\n      }\n    }"""
text = text[:start] + new_block + text[end:]

old = """  static pw.Widget _issueCard({\n    required InspectionAnswer answer,\n    required int index,\n    required NonConformity? nc,\n    required bool executive,\n  }) {\n"""
new = """  static pw.Widget _issueCard({\n    required InspectionAnswer answer,\n    required int index,\n    required NonConformity? nc,\n    required bool executive,\n    ActionPlan? executiveAction,\n    String executiveLocation = '',\n    int executiveQuantity = 1,\n  }) {\n"""
assert old in text
text = text.replace(old, new, 1)

old = """          pw.SizedBox(height: 7),\n          _detailLine(\n            executive ? 'O que foi encontrado' : 'Situação encontrada',\n            answer.observation.isEmpty ? 'Não informada.' : answer.observation,\n          ),\n"""
new = """          pw.SizedBox(height: 7),\n          if (executive) ...[\n            _detailLine(\n              'Local',\n              executiveLocation.trim().isEmpty\n                  ? 'Local exato não informado.'\n                  : executiveLocation.trim(),\n            ),\n            _detailLine('Quantidade', '$executiveQuantity'),\n          ],\n          _detailLine(\n            executive ? 'O que foi encontrado' : 'Situação encontrada',\n            answer.observation.isEmpty ? 'Não informada.' : answer.observation,\n          ),\n"""
assert old in text
text = text.replace(old, new, 1)

old = """          if (answer.recommendation.isNotEmpty)\n            _detailLine(\n              executive ? 'O que deve ser feito' : 'Recomendação técnica',\n              answer.recommendation,\n            ),\n"""
new = """          if (answer.recommendation.isNotEmpty ||\n              (executiveAction?.correctiveAction.trim().isNotEmpty ?? false))\n            _detailLine(\n              executive ? 'O que deve ser feito' : 'Recomendação técnica',\n              executive &&\n                      (executiveAction?.correctiveAction.trim().isNotEmpty ?? false)\n                  ? executiveAction!.correctiveAction.trim()\n                  : answer.recommendation,\n            ),\n          if (executive && executiveAction != null) ...[\n            if (executiveAction.responsible.trim().isNotEmpty)\n              _detailLine('Responsável', executiveAction.responsible.trim()),\n            _detailLine(\n              'Prazo',\n              executiveAction.dueDate == null\n                  ? 'Não definido'\n                  : DateFormat('dd/MM/yyyy').format(executiveAction.dueDate!),\n            ),\n            _detailLine('Status', executiveAction.status),\n          ],\n"""
assert old in text
text = text.replace(old, new, 1)

old = """          if (nc != null && executive)\n            _detailLine('Prioridade', nc.classification),\n"""
new = """          if (executive && (executiveAction != null || nc != null))\n            _detailLine(\n              'Prioridade',\n              executiveAction?.priority.trim().isNotEmpty == true\n                  ? executiveAction!.priority.trim()\n                  : nc!.classification,\n            ),\n"""
assert old in text
text = text.replace(old, new, 1)

marker = """  static pw.Widget _detailLine(String label, String value) {\n"""
assert marker in text
helpers = r'''  static String _normalizeForSearch(String value) {
    return value
        .toLowerCase()
        .replaceAll('á', 'a')
        .replaceAll('à', 'a')
        .replaceAll('ã', 'a')
        .replaceAll('â', 'a')
        .replaceAll('é', 'e')
        .replaceAll('ê', 'e')
        .replaceAll('í', 'i')
        .replaceAll('ó', 'o')
        .replaceAll('ô', 'o')
        .replaceAll('õ', 'o')
        .replaceAll('ú', 'u')
        .replaceAll('ç', 'c');
  }

  static String _issueSearchText(
    InspectionAnswer answer,
    List<ActionPlan> actions,
  ) {
    return _normalizeForSearch([
      answer.questionText,
      answer.questionCategory,
      answer.observation,
      answer.riskIdentified,
      answer.recommendation,
      ...actions.expand((action) => [
            action.nonConformity,
            action.correctiveAction,
            action.locationDetail,
          ]),
    ].join(' '));
  }

  static int _quantityForIssue(
    InspectionAnswer answer,
    List<ActionPlan> actions,
  ) {
    final raw = [
      answer.observation,
      answer.recommendation,
      ...actions.expand((action) => [
            action.nonConformity,
            action.correctiveAction,
          ]),
    ].join(' ');
    final match = RegExp(
      r'\b(\d{1,3})\s*(?:extintor(?:es)?|equipamento(?:s)?|unidade(?:s)?)\b',
      caseSensitive: false,
    ).firstMatch(raw);
    if (match != null) {
      final parsed = int.tryParse(match.group(1) ?? '');
      if (parsed != null && parsed > 0) return parsed;
    }
    return 1;
  }

  static int _sumIssueQuantitiesMatching(
    List<InspectionAnswer> issues,
    Map<String, List<ActionPlan>> actionsByAnswer,
    List<String> terms,
  ) {
    final normalizedTerms = terms.map(_normalizeForSearch).toList();
    var total = 0;
    for (final answer in issues) {
      final linked = actionsByAnswer[answer.id] ?? <ActionPlan>[];
      final haystack = _issueSearchText(answer, linked);
      if (normalizedTerms.any(haystack.contains)) {
        total += _quantityForIssue(answer, linked);
      }
    }
    return total;
  }

  static String _executiveLocation(
    ActionPlan? action,
    String sector,
    String area,
  ) {
    final exact = action?.locationDetail.trim() ?? '';
    if (exact.isNotEmpty) return exact;
    final normalizedArea = _normalizeForSearch(area.trim());
    if (area.trim().isNotEmpty &&
        area.trim() != '-' &&
        normalizedArea != 'local visitado') {
      return area.trim();
    }
    final normalizedSector = _normalizeForSearch(sector.trim());
    if (sector.trim().isNotEmpty &&
        sector.trim() != '-' &&
        normalizedSector != 'local visitado') {
      return sector.trim();
    }
    return 'Local exato não informado';
  }

  static String _compactExecutiveText(String value, {int max = 170}) {
    final clean = value.trim().replaceAll(RegExp(r'\s+'), ' ');
    if (clean.length <= max) return clean.isEmpty ? '-' : clean;
    return '${clean.substring(0, max - 1).trimRight()}…';
  }

  static pw.Widget _executiveOperationalMetrics({
    required int issueCount,
    required int pendingCount,
    required int completedCount,
    required int overdueCount,
    required int highPriorityCount,
    required bool isExtinguisherReport,
    required int maintenanceRechargeCount,
    required int replacementCount,
    required int brokenSealCount,
    required int missingSignCount,
    required int incompatibleSignCount,
    required int obstructedAccessCount,
  }) {
    final items = <List<Object>>[
      ['Irregularidades', issueCount, _red],
      ['Pendentes', pendingCount, _amber],
      ['Resolvidas', completedCount, _green],
      ['Vencidas', overdueCount, _red],
      ['Alta prioridade', highPriorityCount, _red],
    ];
    if (isExtinguisherReport) {
      items.addAll([
        ['Recarga / manutenção', maintenanceRechargeCount, _navy],
        ['Substituição indicada', replacementCount, _amber],
        ['Lacre rompido', brokenSealCount, _red],
        ['Sem placa', missingSignCount, _amber],
        ['Placa incompatível', incompatibleSignCount, _amber],
        ['Acesso obstruído', obstructedAccessCount, _red],
      ]);
    }
    return pw.Wrap(
      spacing: 7,
      runSpacing: 7,
      children: items.map((item) {
        final label = item[0] as String;
        final value = item[1] as int;
        final color = item[2] as PdfColor;
        return pw.Container(
          width: 154,
          padding: const pw.EdgeInsets.symmetric(horizontal: 9, vertical: 8),
          decoration: pw.BoxDecoration(
            color: _softFor(color),
            border: pw.Border.all(color: color, width: 0.6),
            borderRadius: pw.BorderRadius.circular(6),
          ),
          child: pw.Row(
            children: [
              pw.Text(
                '$value',
                style: pw.TextStyle(
                  fontSize: 16,
                  fontWeight: pw.FontWeight.bold,
                  color: color,
                ),
              ),
              pw.SizedBox(width: 7),
              pw.Expanded(
                child: pw.Text(
                  label,
                  style: pw.TextStyle(
                    fontSize: 7.4,
                    fontWeight: pw.FontWeight.bold,
                    color: _navy,
                  ),
                ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }

  static pw.Widget _executiveIssueTable({
    required List<InspectionAnswer> issues,
    required Map<String, NonConformity> ncByAnswer,
    required Map<String, List<ActionPlan>> actionsByAnswer,
    required String fallbackSector,
    required String fallbackArea,
  }) {
    if (issues.isEmpty) {
      return _emptyState('Nenhuma providência registrada.', positive: true);
    }
    final rows = <pw.Widget>[
      pw.Container(
        padding: const pw.EdgeInsets.symmetric(horizontal: 7, vertical: 5),
        color: _navy,
        child: pw.Row(
          children: [
            pw.SizedBox(width: 92, child: _executiveTableHeader('LOCAL')),
            pw.SizedBox(width: 28, child: _executiveTableHeader('QTD.')),
            pw.Expanded(flex: 3, child: _executiveTableHeader('SITUAÇÃO / PROVIDÊNCIA')),
            pw.SizedBox(width: 72, child: _executiveTableHeader('PRIORIDADE / STATUS')),
          ],
        ),
      ),
    ];
    for (final answer in issues) {
      final linked = actionsByAnswer[answer.id] ?? <ActionPlan>[];
      final action = linked.isEmpty ? null : linked.first;
      final nc = ncByAnswer[answer.id];
      final location = _executiveLocation(action, fallbackSector, fallbackArea);
      final problem = answer.observation.trim().isNotEmpty
          ? answer.observation
          : (nc?.description ?? 'Não informado');
      final measure = action?.correctiveAction.trim().isNotEmpty == true
          ? action!.correctiveAction
          : (answer.recommendation.trim().isNotEmpty
              ? answer.recommendation
              : (nc?.recommendation ?? 'Não informada'));
      final priority = action?.priority.trim().isNotEmpty == true
          ? action!.priority
          : (nc?.classification ?? '-');
      final status = action?.status.trim().isNotEmpty == true
          ? action!.status
          : (nc?.status ?? answer.status);
      rows.add(
        pw.Container(
          padding: const pw.EdgeInsets.symmetric(horizontal: 7, vertical: 6),
          decoration: const pw.BoxDecoration(
            border: pw.Border(
              left: pw.BorderSide(color: _line),
              right: pw.BorderSide(color: _line),
              bottom: pw.BorderSide(color: _line),
            ),
          ),
          child: pw.Row(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.SizedBox(
                width: 92,
                child: pw.Text(location, style: const pw.TextStyle(fontSize: 6.8)),
              ),
              pw.SizedBox(
                width: 28,
                child: pw.Text(
                  '${_quantityForIssue(answer, linked)}',
                  textAlign: pw.TextAlign.center,
                  style: pw.TextStyle(fontSize: 7, fontWeight: pw.FontWeight.bold),
                ),
              ),
              pw.Expanded(
                flex: 3,
                child: pw.Column(
                  crossAxisAlignment: pw.CrossAxisAlignment.start,
                  children: [
                    pw.Text(
                      _compactExecutiveText(problem),
                      style: pw.TextStyle(fontSize: 6.8, fontWeight: pw.FontWeight.bold),
                    ),
                    pw.SizedBox(height: 2),
                    pw.Text(
                      'Fazer: ${_compactExecutiveText(measure, max: 190)}',
                      style: const pw.TextStyle(fontSize: 6.6),
                    ),
                  ],
                ),
              ),
              pw.SizedBox(width: 7),
              pw.SizedBox(
                width: 72,
                child: pw.Column(
                  crossAxisAlignment: pw.CrossAxisAlignment.start,
                  children: [
                    pw.Text(priority, style: pw.TextStyle(fontSize: 6.7, fontWeight: pw.FontWeight.bold, color: _red)),
                    pw.SizedBox(height: 2),
                    pw.Text(status, style: const pw.TextStyle(fontSize: 6.4, color: _grey)),
                  ],
                ),
              ),
            ],
          ),
        ),
      );
    }
    return pw.Column(children: rows);
  }

  static pw.Widget _executiveTableHeader(String text) {
    return pw.Text(
      text,
      style: pw.TextStyle(
        fontSize: 6.2,
        fontWeight: pw.FontWeight.bold,
        color: PdfColors.white,
      ),
    );
  }

'''
text = text.replace(marker, helpers + marker, 1)

pdf.write_text(text)

rt = report.read_text()
old = """            subtitle: includeActionPlan\n                ? 'Versão mais curta para gerência, com indicadores, o que foi encontrado, o que precisa ser feito e conclusão.'\n                : 'Versão mais curta para gerência, com indicadores, o que foi encontrado e conclusão.',\n"""
new = """            subtitle: includeActionPlan\n                ? 'Versão gerencial com quantitativos, quadro de providências, fotos das pendências, responsáveis, prazos, resolvidos e conclusão.'\n                : 'Versão gerencial com quantitativos, quadro de providências, fotos das pendências e conclusão.',\n"""
assert old in rt
report.write_text(rt.replace(old,new,1))

pt = pub.read_text()
assert 'version: 3.29.13+156' in pt
pub.write_text(pt.replace('version: 3.29.13+156','version: 3.29.14+157',1))

print('v3.29.14: relatório executivo gerencial com quantitativos, providências e fotos aplicado')

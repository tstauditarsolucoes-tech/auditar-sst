#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) < 2:
    raise SystemExit("uso: patch_reports_management_v32988_v33015.py <APP_DIR> [android|windows]")

root = Path(sys.argv[1])
platform = (sys.argv[2] if len(sys.argv) > 2 else "android").lower()

def read(rel):
    return (root / rel).read_text(encoding="utf-8")

def write(rel, text):
    (root / rel).write_text(text, encoding="utf-8", newline="\n")

def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise RuntimeError("âncora não localizada: " + label)
    return text.replace(old, new, 1)

def replace_dart_method(text, signature, replacement):
    start = text.find(signature)
    if start < 0:
        raise RuntimeError("método não localizado: " + signature)

    paren = text.find("(", start)
    if paren < 0:
        raise RuntimeError("parâmetros não localizados: " + signature)

    depth = 0
    quote = None
    escape = False
    line_comment = False
    block_comment = False
    close_paren = None
    i = paren
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if line_comment:
            if ch == "\n":
                line_comment = False
            i += 1
            continue
        if block_comment:
            if ch == "*" and nxt == "/":
                block_comment = False
                i += 2
                continue
            i += 1
            continue
        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
            i += 1
            continue
        if ch == "/" and nxt == "/":
            line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            block_comment = True
            i += 2
            continue
        if ch in ("'", '"'):
            quote = ch
            i += 1
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                close_paren = i
                break
        i += 1

    if close_paren is None:
        raise RuntimeError("fim dos parâmetros não localizado: " + signature)

    brace = text.find("{", close_paren)
    if brace < 0:
        raise RuntimeError("abertura do corpo não localizada: " + signature)

    depth = 0
    quote = None
    escape = False
    line_comment = False
    block_comment = False
    i = brace
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if line_comment:
            if ch == "\n":
                line_comment = False
            i += 1
            continue
        if block_comment:
            if ch == "*" and nxt == "/":
                block_comment = False
                i += 2
                continue
            i += 1
            continue
        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
            i += 1
            continue
        if ch == "/" and nxt == "/":
            line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            block_comment = True
            i += 2
            continue
        if ch in ("'", '"'):
            quote = ch
            i += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[:start] + replacement.rstrip() + text[i + 1:]
        i += 1

    raise RuntimeError("fim do método não localizado: " + signature)

# 1. Biblioteca de modelos.
rel = "lib/services/report_template_service.dart"
t = read(rel)
for old, new in [
    ("name: 'Padrão Auditar atual',", "name: 'Auditar Gerencial Padrão',"),
    ("description: 'Modelo que já funciona hoje. Mantido intacto como padrão e fallback.',",
     "description: 'Modelo institucional equilibrado para apresentação à gerência, com resumo, evidências, prioridades, conclusão e anexo técnico.',"),
    ("headerTitle: 'RELATÓRIO DE INSPEÇÃO SST',", "headerTitle: 'RELATÓRIO GERENCIAL DE SST',"),
    ("footerText: 'Auditar SST - Segurança do Trabalho',", "footerText: 'Auditar SST • Relatório gerencial de segurança do trabalho',"),
    ("Curto, visual e direto para gestores, com resumo, prioridades e evidências.",
     "Leitura executiva para gestores: indicadores, pontos críticos, prioridades, evidências e plano de ação."),
    ("Valoriza as evidências: foto, problema, risco, correção e prioridade.",
     "Modelo gerencial fotográfico: evidência em destaque, situação encontrada, risco, correção e prioridade."),
    ("Leitura rápida para obras, com destaque visual para risco, prioridade e correção.",
     "Modelo gerencial para obras: riscos prioritários, evidências, responsáveis, prazos e correções."),
    ("Visual limpo e técnico, com mais espaço para texto, referência normativa e checklist.",
     "Modelo técnico de leitura limpa, com resumo gerencial e anexo detalhado de critérios e referências."),
    ("Focado em máquinas e equipamentos, com leitura técnica e destaque para não conformidades.",
     "Modelo gerencial NR-12: máquinas, proteções, riscos críticos, referências, evidências e ações prioritárias."),
    ("Modelo visual em duas colunas: foto à esquerda e análise técnica à direita, com conclusão e assinatura no fechamento.",
     "Modelo gerencial em duas colunas: evidência à esquerda e síntese técnica à direita, com prioridade, conclusão e assinatura."),
]:
    t = t.replace(old, new)
t = t.replace("useLegacyRenderer: true,", "useLegacyRenderer: false,", 1)
write(rel, t)

# 2. Renderer geral.
rel = "lib/services/styled_report_pdf_service.dart"
s = read(rel)

anchor = """    final company = '${header['company_name'] ?? '-'}'.trim();
"""
insert = """    issueData.sort(
      (a, b) => _priorityRank(_priorityForIssue(b))
          .compareTo(_priorityRank(_priorityForIssue(a))),
    );
    final criticalCount = issueData
        .where((item) => _priorityRank(_priorityForIssue(item)) >= 3)
        .length;

    final company = '${header['company_name'] ?? '-'}'.trim();
"""
s = replace_once(s, anchor, insert, "ordenação gerencial")
s = s.replace(
    """          conformes: conformes,
          parciais: parciais,
          naoConformes: naoConformes,
""",
    """          criticalCount: criticalCount,
          parciais: parciais,
          naoConformes: naoConformes,
""",
    1,
)
s = s.replace(
    ": _automaticConclusion(naoConformes, parciais, conformity),",
    ": _automaticConclusion(naoConformes, parciais, conformity, criticalCount),",
    1,
)

old_checklist = """    if (!executive && template.showChecklistDetails) {
      widgets.add(pw.SizedBox(height: 6));
      widgets.add(_sectionTitle('Checklist da vistoria', primary));
      widgets.add(pw.SizedBox(height: 8));
      for (final answer in answers) {
        widgets.add(_checklistLine(answer, primary));
      }
    }

"""
s = s.replace(old_checklist, "", 1)

annex = """    if (!executive && template.showChecklistDetails) {
      widgets.addAll([
        pw.NewPage(),
        _sectionTitle('Anexo técnico — Checklist detalhado', primary),
        pw.SizedBox(height: 5),
        pw.Text(
          'Critérios avaliados e respectivos status. Esta seção complementa a síntese gerencial das páginas anteriores.',
          style: pw.TextStyle(
            fontSize: 8.5,
            color: PdfColors.grey700,
            lineSpacing: 1.8,
          ),
        ),
        pw.SizedBox(height: 9),
      ]);
      for (final answer in answers) {
        widgets.add(_checklistLine(answer, primary));
      }
    }

"""
s = replace_once(s, "    doc.addPage(\n      pw.MultiPage(\n", annex + "    doc.addPage(\n      pw.MultiPage(\n", "anexo técnico")

summary_method = r'''  static pw.Widget _summaryGrid({
    required int conformity,
    required int criticalCount,
    required int parciais,
    required int naoConformes,
    required PdfColor primary,
    required PdfColor secondary,
  }) {
    return pw.Row(
      children: [
        _metric('$conformity%', 'Conformidade', primary),
        pw.SizedBox(width: 7),
        _metric('$naoConformes', 'Não conformes', PdfColors.red700),
        pw.SizedBox(width: 7),
        _metric('$parciais', 'Parciais', PdfColors.orange700),
        pw.SizedBox(width: 7),
        _metric(
          '$criticalCount',
          'Alta / crítica',
          criticalCount > 0 ? PdfColors.red800 : secondary,
        ),
      ],
    );
  }'''
s = replace_dart_method(s, "  static pw.Widget _summaryGrid(", summary_method)

issue_method = r'''  static pw.Widget _issueBlock(
    int number,
    _IssueData data,
    ReportTemplateDefinition template,
    PdfColor primary,
    PdfColor secondary,
    bool includePlan,
    bool executive,
  ) {
    final a = data.answer;
    final action = data.actions.isEmpty ? null : data.actions.first;
    final priority = _priorityForIssue(data);
    final problem = a.observation.trim().isNotEmpty
        ? a.observation.trim()
        : (data.nc?.description.trim().isNotEmpty == true
            ? data.nc!.description.trim()
            : 'Situação registrada durante a vistoria.');
    final risk = a.riskIdentified.trim().isNotEmpty
        ? a.riskIdentified.trim()
        : (data.nc?.riskIdentified.trim().isNotEmpty == true
            ? data.nc!.riskIdentified.trim()
            : 'Risco associado à condição identificada deve ser confirmado no local.');
    final recommendation = a.recommendation.trim().isNotEmpty
        ? a.recommendation.trim()
        : (data.nc?.recommendation.trim().isNotEmpty == true
            ? data.nc!.recommendation.trim()
            : 'Programar a adequação e registrar a evidência de conclusão.');
    final reference = a.questionReference.trim();
    final criterion = a.questionText.trim();
    final title = _issueTitle(data);
    final photographic = template.id == 'auditar_fotografico';

    return pw.Container(
      padding: const pw.EdgeInsets.all(11),
      decoration: pw.BoxDecoration(
        color: PdfColors.white,
        border: pw.Border.all(color: PdfColors.grey300, width: .8),
        borderRadius: const pw.BorderRadius.all(pw.Radius.circular(4)),
      ),
      child: pw.Column(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: [
          pw.Row(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Container(
                width: 28,
                height: 28,
                alignment: pw.Alignment.center,
                decoration: pw.BoxDecoration(color: primary, shape: pw.BoxShape.circle),
                child: pw.Text(
                  '$number',
                  style: pw.TextStyle(
                    color: PdfColors.white,
                    fontWeight: pw.FontWeight.bold,
                    fontSize: 9,
                  ),
                ),
              ),
              pw.SizedBox(width: 8),
              pw.Expanded(
                child: pw.Column(
                  crossAxisAlignment: pw.CrossAxisAlignment.start,
                  children: [
                    pw.Text(
                      title,
                      style: pw.TextStyle(
                        fontSize: 11.2,
                        fontWeight: pw.FontWeight.bold,
                        color: primary,
                      ),
                    ),
                    if (criterion.isNotEmpty && !executive) ...[
                      pw.SizedBox(height: 2),
                      pw.Text(
                        'Critério avaliado: $criterion',
                        maxLines: 2,
                        style: pw.TextStyle(fontSize: 6.9, color: PdfColors.grey600),
                      ),
                    ],
                  ],
                ),
              ),
              pw.SizedBox(width: 6),
              _priorityChip(priority),
            ],
          ),
          pw.SizedBox(height: 9),
          if (photographic && data.photos.isNotEmpty) ...[
            _photos(
              data.photos,
              template.photoColumns,
              primary,
              caption: _issueCaption(data),
            ),
            pw.SizedBox(height: 9),
          ],
          _labelValue('Situação encontrada', problem),
          _labelValue('Risco', risk),
          _labelValue('Correção recomendada', recommendation),
          if (reference.isNotEmpty) _labelValue('Referência', reference),
          if (includePlan && action != null) ...[
            pw.SizedBox(height: 3),
            pw.Container(
              width: double.infinity,
              padding: const pw.EdgeInsets.all(7),
              decoration: pw.BoxDecoration(
                color: PdfColors.grey100,
                border: pw.Border(left: pw.BorderSide(color: secondary, width: 3)),
              ),
              child: pw.Column(
                crossAxisAlignment: pw.CrossAxisAlignment.start,
                children: [
                  pw.Text(
                    'ENCAMINHAMENTO',
                    style: pw.TextStyle(
                      fontSize: 7,
                      fontWeight: pw.FontWeight.bold,
                      color: primary,
                    ),
                  ),
                  pw.SizedBox(height: 3),
                  _labelValue('Ação definida', action.correctiveAction),
                  _labelValue('Responsável', action.responsible.isEmpty ? '-' : action.responsible),
                  _labelValue(
                    'Prazo',
                    action.dueDate == null
                        ? '-'
                        : DateFormat('dd/MM/yyyy').format(action.dueDate!),
                  ),
                  _labelValue('Status', action.status),
                ],
              ),
            ),
          ],
          if (!photographic && data.photos.isNotEmpty) ...[
            pw.SizedBox(height: 8),
            _photos(
              data.photos,
              template.photoColumns,
              primary,
              caption: _issueCaption(data),
            ),
          ],
        ],
      ),
    );
  }'''
s = replace_dart_method(s, "  static pw.Widget _issueBlock(", issue_method)

photos_method = r'''  static pw.Widget _photos(
    List<pw.MemoryImage> images,
    int columns,
    PdfColor primary, {
    String caption = '',
  }) {
    final cols = columns.clamp(1, 3).toInt();
    final width = cols == 1 ? 490.0 : (cols == 2 ? 241.0 : 158.0);
    final height = cols == 1 ? 235.0 : (cols == 2 ? 150.0 : 105.0);
    return pw.Column(
      crossAxisAlignment: pw.CrossAxisAlignment.start,
      children: [
        pw.Wrap(
          spacing: 7,
          runSpacing: 7,
          children: images.map((image) => pw.Container(
            width: width,
            height: height,
            decoration: pw.BoxDecoration(
              border: pw.Border.all(color: PdfColors.grey400, width: .5),
            ),
            child: pw.Image(image, fit: pw.BoxFit.cover),
          )).toList(),
        ),
        if (caption.trim().isNotEmpty) ...[
          pw.SizedBox(height: 4),
          pw.Text(
            caption,
            style: pw.TextStyle(
              fontSize: 6.7,
              fontStyle: pw.FontStyle.italic,
              color: PdfColors.grey600,
            ),
          ),
        ],
      ],
    );
  }'''
s = replace_dart_method(s, "  static pw.Widget _photos(", photos_method)

helpers = r'''  static String _priorityForIssue(_IssueData data) {
    final action = data.actions.isEmpty ? null : data.actions.first;
    if (action?.priority.trim().isNotEmpty == true) return action!.priority.trim();
    if (data.nc?.classification.trim().isNotEmpty == true) {
      return data.nc!.classification.trim();
    }
    return 'Média';
  }

  static int _priorityRank(String value) {
    final normalized = value.toLowerCase();
    if (normalized.contains('crít') ||
        normalized.contains('crit') ||
        normalized.contains('grave') ||
        normalized.contains('imedi')) {
      return 4;
    }
    if (normalized.contains('alta')) return 3;
    if (normalized.contains('média') || normalized.contains('media')) return 2;
    return 1;
  }

  static String _issueTitle(_IssueData data) {
    var source = data.nc?.description.trim() ?? '';
    if (source.isEmpty) source = data.answer.observation.trim();
    if (source.isEmpty) source = data.answer.questionCategory.trim();
    if (source.isEmpty) source = 'Situação identificada';
    source = source
        .replaceAll(RegExp(r'\s+'), ' ')
        .replaceFirst(RegExp(r'^(foi|foram)\s+(identificado|identificada|identificados|identificadas|constatado|constatada|observado|observada)\s+', caseSensitive: false), '')
        .replaceFirst(RegExp(r'^durante a vistoria,?\s*', caseSensitive: false), '')
        .trim();
    var title = source.split(RegExp(r'[.;]')).first.trim();
    if (title.length > 72) title = '${title.substring(0, 69).trim()}...';
    return title.isEmpty ? 'SITUAÇÃO IDENTIFICADA' : title.toUpperCase();
  }

  static String _issueCaption(_IssueData data) {
    var source = data.answer.observation.trim();
    if (source.isEmpty) source = data.nc?.description.trim() ?? '';
    if (source.isEmpty) return 'Registro fotográfico da condição observada.';
    source = source.replaceAll(RegExp(r'\s+'), ' ');
    var sentence = source.split(RegExp(r'(?<=[.!?])\s+')).first.trim();
    if (sentence.length > 105) {
      sentence = '${sentence.substring(0, 102).trim()}...';
    }
    if (!RegExp(r'[.!?]$').hasMatch(sentence)) sentence = '$sentence.';
    return sentence;
  }

'''
if helpers not in s:
    s = replace_once(s, "  static String _automaticConclusion(", helpers + "  static String _automaticConclusion(", "helpers gerenciais")

conclusion_method = r'''  static String _automaticConclusion(
    int nc,
    int partial,
    int conformity,
    int criticalCount,
  ) {
    if (nc == 0 && partial == 0) {
      return 'Na data da vistoria, não foram registradas não conformidades ou situações parciais nos critérios avaliados. Recomenda-se manter os controles existentes, o acompanhamento preventivo e os registros de verificação.';
    }
    final criticalText = criticalCount > 0
        ? ' Foram identificados $criticalCount item(ns) de prioridade alta/crítica, que devem receber tratamento prioritário e controle do risco antes da continuidade das atividades afetadas, quando aplicável.'
        : '';
    return 'A vistoria registrou $nc não conformidade(s) e $partial item(ns) parcial(is), com índice de conformidade de $conformity%.$criticalText '
        'Os demais itens devem ser programados, corrigidos e posteriormente verificados, com registro das evidências de conclusão. '
        'Este relatório retrata as condições observadas na data da vistoria e não constitui confirmação de regularização posterior.';
  }'''
s = replace_dart_method(s, "  static String _automaticConclusion(", conclusion_method)
write(rel, s)

# 3. Renderer Performance.
rel = "lib/services/performance_report_pdf_service.dart"
p = read(rel)

old_conclusion = """    final customConclusion = '${header['conclusion'] ?? ''}'.trim();
    final hasImmediate = issues.any(
      (item) => _isImmediate(_priorityFor(item)),
    );
    final conclusion = customConclusion.isNotEmpty
        ? customConclusion
        : _defaultConclusion(hasImmediate);
"""
new_conclusion = """    final customConclusion = '${header['conclusion'] ?? ''}'.trim();
    final nonConformCount =
        issueAnswers.where((item) => item.status == 'Não Conforme').length;
    final partialCount =
        issueAnswers.where((item) => item.status == 'Parcial').length;
    final criticalCount = issues
        .where((item) => _priorityRank(_priorityFor(item)) >= 3)
        .length;
    final considered =
        answers.where((item) => item.status != 'Não se aplica' && item.status != 'N/A').length;
    final conformes = answers.where((item) => item.status == 'Conforme').length;
    final conformity =
        considered == 0 ? 0 : (conformes / considered * 100).round();
    issues.sort(
      (a, b) => _priorityRank(_priorityFor(b))
          .compareTo(_priorityRank(_priorityFor(a))),
    );
    final conclusion = customConclusion.isNotEmpty
        ? customConclusion
        : _defaultConclusion(
            nonConformCount,
            partialCount,
            criticalCount,
            conformity,
          );
"""
p = replace_once(p, old_conclusion, new_conclusion, "conclusão performance")

p = replace_once(
    p,
    """    final body = <pw.Widget>[];
    if (issues.isEmpty) {
""",
    """    final body = <pw.Widget>[
      _managementSummary(
        conformity: conformity,
        nonConformCount: nonConformCount,
        partialCount: partialCount,
        criticalCount: criticalCount,
      ),
      pw.SizedBox(height: 9),
    ];
    if (issues.isEmpty) {
""",
    "resumo performance",
)

issue_perf = r'''  static pw.Widget _issueRow(_PerformanceIssue issue) {
    final problem = _problemFor(issue);
    final risk = _riskFor(issue);
    final correction = _correctionFor(issue);
    final priority = _priorityFor(issue);
    final title = _titleFor(issue);
    final criterion = issue.answer.questionText.trim();
    final fine = _fineForReport(issue.answer);

    return pw.Table(
      border: pw.TableBorder.all(color: _border, width: .55),
      columnWidths: const {
        0: pw.FlexColumnWidth(47),
        1: pw.FlexColumnWidth(53),
      },
      children: [
        pw.TableRow(
          verticalAlignment: pw.TableCellVerticalAlignment.middle,
          children: [
            pw.Container(
              padding: const pw.EdgeInsets.all(7),
              constraints: const pw.BoxConstraints(minHeight: 178),
              child: pw.Column(
                mainAxisAlignment: pw.MainAxisAlignment.center,
                children: [
                  pw.Container(
                    width: double.infinity,
                    height: 148,
                    color: PdfColors.grey100,
                    child: issue.photo != null
                        ? pw.Image(issue.photo!, fit: pw.BoxFit.cover)
                        : pw.Center(
                            child: pw.Text(
                              'EVIDÊNCIA NÃO ANEXADA',
                              style: pw.TextStyle(
                                color: PdfColors.grey500,
                                fontSize: 8,
                                fontWeight: pw.FontWeight.bold,
                              ),
                            ),
                          ),
                  ),
                  pw.SizedBox(height: 5),
                  pw.Text(
                    _captionFor(issue),
                    maxLines: 3,
                    textAlign: pw.TextAlign.center,
                    style: pw.TextStyle(
                      fontSize: 6.4,
                      fontStyle: pw.FontStyle.italic,
                      color: PdfColors.grey600,
                    ),
                  ),
                ],
              ),
            ),
            pw.Container(
              padding: const pw.EdgeInsets.fromLTRB(9, 9, 9, 8),
              constraints: const pw.BoxConstraints(minHeight: 178),
              child: pw.Column(
                crossAxisAlignment: pw.CrossAxisAlignment.start,
                mainAxisAlignment: pw.MainAxisAlignment.center,
                children: [
                  pw.Text(
                    title,
                    style: pw.TextStyle(
                      fontSize: 10.5,
                      fontWeight: pw.FontWeight.bold,
                      color: _blue,
                    ),
                  ),
                  if (criterion.isNotEmpty) ...[
                    pw.SizedBox(height: 2),
                    pw.Text(
                      'Critério avaliado: $criterion',
                      maxLines: 2,
                      style: pw.TextStyle(fontSize: 6.2, color: PdfColors.grey600),
                    ),
                  ],
                  pw.SizedBox(height: 7),
                  _technicalLine('Situação', problem),
                  _technicalLine('Risco', risk),
                  _technicalLine('Correção', correction),
                  if (issue.answer.questionReference.trim().isNotEmpty)
                    _technicalLine('Referência', issue.answer.questionReference.trim()),
                  if (fine.isNotEmpty)
                    _technicalLine('Multa (referência)', fine, labelColor: _orange),
                  pw.SizedBox(height: 3),
                  pw.Text(
                    'PRIORIDADE: ${priority.toUpperCase()}',
                    style: pw.TextStyle(
                      fontSize: 8.2,
                      fontWeight: pw.FontWeight.bold,
                      color: _priorityColor(priority),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ],
    );
  }'''
p = replace_dart_method(p, "  static pw.Widget _issueRow(", issue_perf)

perf_helpers = r'''  static pw.Widget _managementSummary({
    required int conformity,
    required int nonConformCount,
    required int partialCount,
    required int criticalCount,
  }) {
    pw.Widget metric(String value, String label, PdfColor color) {
      return pw.Expanded(
        child: pw.Container(
          padding: const pw.EdgeInsets.symmetric(horizontal: 8, vertical: 7),
          decoration: pw.BoxDecoration(
            color: PdfColors.grey100,
            border: pw.Border(top: pw.BorderSide(color: color, width: 2.5)),
          ),
          child: pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Text(
                value,
                style: pw.TextStyle(
                  fontSize: 13,
                  fontWeight: pw.FontWeight.bold,
                  color: color,
                ),
              ),
              pw.Text(label, style: const pw.TextStyle(fontSize: 6.5)),
            ],
          ),
        ),
      );
    }
    return pw.Row(
      children: [
        metric('$conformity%', 'Conformidade', _blue),
        pw.SizedBox(width: 5),
        metric('$nonConformCount', 'Não conformes', _red),
        pw.SizedBox(width: 5),
        metric('$partialCount', 'Parciais', _orange),
        pw.SizedBox(width: 5),
        metric('$criticalCount', 'Alta / crítica', criticalCount > 0 ? _red : _green),
      ],
    );
  }

  static int _priorityRank(String value) {
    final normalized = value.toLowerCase();
    if (normalized.contains('crít') ||
        normalized.contains('crit') ||
        normalized.contains('grave') ||
        normalized.contains('imedi')) {
      return 4;
    }
    if (normalized.contains('alta')) return 3;
    if (normalized.contains('média') || normalized.contains('media')) return 2;
    return 1;
  }

  static String _titleFor(_PerformanceIssue issue) {
    var source = issue.nc?.description.trim() ?? '';
    if (source.isEmpty) source = issue.answer.observation.trim();
    if (source.isEmpty) source = issue.answer.questionCategory.trim();
    if (source.isEmpty) source = 'Situação identificada';
    source = source
        .replaceAll(RegExp(r'\s+'), ' ')
        .replaceFirst(RegExp(r'^(foi|foram)\s+(identificado|identificada|identificados|identificadas|constatado|constatada|observado|observada)\s+', caseSensitive: false), '')
        .replaceFirst(RegExp(r'^durante a vistoria,?\s*', caseSensitive: false), '')
        .trim();
    var title = source.split(RegExp(r'[.;]')).first.trim();
    if (title.length > 66) title = '${title.substring(0, 63).trim()}...';
    return title.toUpperCase();
  }

'''
p = replace_once(p, "  static String _captionFor(", perf_helpers + "  static String _captionFor(", "helpers performance")

caption_method = r'''  static String _captionFor(_PerformanceIssue issue) {
    var source = issue.answer.observation.trim();
    if (source.isEmpty) source = issue.nc?.description.trim() ?? '';
    if (source.isEmpty) return 'Registro fotográfico da condição observada.';
    source = source.replaceAll(RegExp(r'\s+'), ' ');
    var caption = source.split(RegExp(r'(?<=[.!?])\s+')).first.trim();
    if (caption.length > 96) {
      caption = '${caption.substring(0, 93).trim()}...';
    }
    if (!RegExp(r'[.!?]$').hasMatch(caption)) caption = '$caption.';
    return caption;
  }'''
p = replace_dart_method(p, "  static String _captionFor(", caption_method)

perf_conclusion = r'''  static String _defaultConclusion(
    int nonConformCount,
    int partialCount,
    int criticalCount,
    int conformity,
  ) {
    if (nonConformCount == 0 && partialCount == 0) {
      return 'Na data da vistoria, não foram registradas não conformidades ou situações parciais nos critérios avaliados. Recomenda-se manter os controles existentes e o acompanhamento preventivo.';
    }
    final priorityText = criticalCount > 0
        ? ' Foram identificados $criticalCount item(ns) de prioridade alta/crítica, que exigem tratamento prioritário e controle do risco antes da continuidade das atividades afetadas, quando aplicável.'
        : '';
    return 'A vistoria registrou $nonConformCount não conformidade(s) e $partialCount item(ns) parcial(is), com índice de conformidade de $conformity%.$priorityText '
        'Os demais itens devem ser programados, corrigidos e posteriormente verificados em nova visita, com registro das evidências de conclusão. '
        'Este relatório registra as condições encontradas na data da vistoria e não representa confirmação de regularização posterior.';
  }'''
p = replace_dart_method(p, "  static String _defaultConclusion(", perf_conclusion)
write(rel, p)

# 4. Versão.
rel = "pubspec.yaml"
pub = read(rel)
version = "3.30.15+202" if platform == "windows" else "3.29.88+230"
pub, count = re.subn(
    r"(?m)^version:\s*[^\r\n]+",
    "version: " + version,
    pub,
    count=1,
)
if count != 1:
    raise RuntimeError("versão não localizada")
write(rel, pub)

# 5. Guardas.
templates = read("lib/services/report_template_service.dart")
styled = read("lib/services/styled_report_pdf_service.dart")
performance = read("lib/services/performance_report_pdf_service.dart")
for name in [
    "Auditar Gerencial Padrão",
    "Auditar Executivo",
    "Performance - Foto + Descrição",
    "Auditar Fotográfico",
    "Auditar Obra",
    "Auditar Técnico Clean",
    "Auditar NR-12",
]:
    assert name in templates, "modelo ausente: " + name

for marker in [
    "Alta / crítica",
    "Anexo técnico — Checklist detalhado",
    "Critério avaliado:",
    "Situação encontrada",
    "Correção recomendada",
    "_issueTitle",
]:
    assert marker in styled, "renderer gerencial sem " + marker

for marker in [
    "_managementSummary",
    "_titleFor",
    "Critério avaliado:",
    "Alta / crítica",
    "não representa confirmação de regularização posterior",
]:
    assert marker in performance, "performance gerencial sem " + marker

assert f"version: {version}" in read("pubspec.yaml")
print("REPORTS_MANAGEMENT_REFINEMENT_OK", platform, version)

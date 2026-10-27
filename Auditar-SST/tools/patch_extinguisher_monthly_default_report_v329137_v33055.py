#!/usr/bin/env python3
from pathlib import Path
import re, sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/Auditar_SST_v1_5_dashboard')
extp = root/'lib/screens/extinguishers_screen.dart'
tplp = root/'lib/services/report_template_service.dart'
pdfp = root/'lib/services/styled_report_pdf_service.dart'

ext = extp.read_text(encoding='utf-8')
tpl = tplp.read_text(encoding='utf-8')
pdf = pdfp.read_text(encoding='utf-8')

def once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Marcador ausente: {label}')
    return text.replace(old, new, 1)

# -------- Extintores: inspeção mensal sem tocar em sync/banco --------
# Adiciona ação no menu de cada extintor.
old_select = """                                    if (value == 'edit') _edit(record);
                                    if (value == 'photo') {
"""
new_select = """                                    if (value == 'edit') _edit(record);
                                    if (value == 'monthly') {
                                      _openMonthlyInspection(record);
                                    }
                                    if (value == 'photo') {
"""
ext = once(ext, old_select, new_select, 'acao inspecao mensal')

old_items = """                                  itemBuilder: (_) => [
                                    const PopupMenuItem(
                                      value: 'edit',
                                      child: Text('Editar'),
                                    ),
"""
new_items = """                                  itemBuilder: (_) => [
                                    const PopupMenuItem(
                                      value: 'edit',
                                      child: Text('Editar'),
                                    ),
                                    const PopupMenuItem(
                                      value: 'monthly',
                                      child: ListTile(
                                        contentPadding: EdgeInsets.zero,
                                        leading: Icon(Icons.fact_check_outlined),
                                        title: Text('Inspeção mensal'),
                                      ),
                                    ),
"""
ext = once(ext, old_items, new_items, 'menu inspecao mensal')

# Insere os métodos antes do build principal.
build_anchor = "  @override\n  Widget build(BuildContext context) {\n"
methods = r'''  String _monthKey(DateTime date) =>
      '${date.year.toString().padLeft(4, '0')}-${date.month.toString().padLeft(2, '0')}';

  Future<SstRecord?> _monthlyInspectionFor(SstRecord extinguisher, DateTime month) async {
    final all = await AppDatabase.instance.getSstRecords(
      type: 'EXTINTOR_INSPECAO_MENSAL',
      companyId: widget.company.id,
    );
    final key = _monthKey(month);
    for (final item in all) {
      if ('${item.payload['extinguisherId'] ?? ''}' == extinguisher.id &&
          '${item.payload['referenceMonth'] ?? ''}' == key) {
        return item;
      }
    }
    return null;
  }

  Future<void> _openMonthlyInspection(SstRecord extinguisher) async {
    final now = DateTime.now();
    final existing = await _monthlyInspectionFor(extinguisher, now);
    if (!mounted) return;

    final p = extinguisher.payload;
    final checks = <String, String>{
      'Validade': '${existing?.payload['validity'] ?? 'Conforme'}',
      'Pressão / manômetro': '${existing?.payload['pressure'] ?? 'Conforme'}',
      'Lacre e pino': '${existing?.payload['seal'] ?? 'Conforme'}',
      'Sinalização': '${existing?.payload['signage'] ?? 'Conforme'}',
      'Acesso livre': '${existing?.payload['access'] ?? 'Conforme'}',
      'Mangueira / bico': '${existing?.payload['hose'] ?? 'Conforme'}',
      'Condição geral': '${existing?.payload['condition'] ?? 'Conforme'}',
    };
    final observation = TextEditingController(
      text: '${existing?.payload['observation'] ?? ''}',
    );
    String overall = '${existing?.payload['result'] ?? 'Conforme'}';
    String operationalStatus = '${existing?.payload['operationalStatus'] ?? 'Em operação'}';

    final saved = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
          title: const Text('Inspeção mensal do extintor'),
          content: SizedBox(
            width: 620,
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(extinguisher.title,
                      style: const TextStyle(fontWeight: FontWeight.w800)),
                  const SizedBox(height: 4),
                  Text(
                    '${p['location'] ?? p['local'] ?? 'Local não informado'} • ${_monthKey(now)}',
                    style: TextStyle(color: Colors.grey.shade700),
                  ),
                  const SizedBox(height: 14),
                  ...checks.keys.map((label) => Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: DropdownButtonFormField<String>(
                      value: checks[label],
                      decoration: InputDecoration(labelText: label),
                      items: const [
                        DropdownMenuItem(value: 'Conforme', child: Text('Conforme')),
                        DropdownMenuItem(value: 'Não conforme', child: Text('Não conforme')),
                        DropdownMenuItem(value: 'Não se aplica', child: Text('Não se aplica')),
                      ],
                      onChanged: (value) => setLocal(
                        () => checks[label] = value ?? 'Conforme',
                      ),
                    ),
                  )),
                  DropdownButtonFormField<String>(
                    value: operationalStatus,
                    decoration: const InputDecoration(labelText: 'Situação do extintor'),
                    items: const [
                      DropdownMenuItem(value: 'Em operação', child: Text('Em operação')),
                      DropdownMenuItem(value: 'Em manutenção/recarga', child: Text('Em manutenção/recarga')),
                      DropdownMenuItem(value: 'Não localizado', child: Text('Não localizado')),
                      DropdownMenuItem(value: 'Substituído', child: Text('Substituído')),
                    ],
                    onChanged: (value) => setLocal(
                      () => operationalStatus = value ?? 'Em operação',
                    ),
                  ),
                  const SizedBox(height: 10),
                  DropdownButtonFormField<String>(
                    value: overall,
                    decoration: const InputDecoration(labelText: 'Resultado final'),
                    items: const [
                      DropdownMenuItem(value: 'Conforme', child: Text('Conforme')),
                      DropdownMenuItem(value: 'Não conforme', child: Text('Não conforme')),
                      DropdownMenuItem(value: 'Não localizado', child: Text('Não localizado')),
                    ],
                    onChanged: (value) => setLocal(
                      () => overall = value ?? 'Conforme',
                    ),
                  ),
                  const SizedBox(height: 10),
                  TextField(
                    controller: observation,
                    maxLines: 3,
                    decoration: const InputDecoration(
                      labelText: 'Observação',
                      hintText: 'Preencha quando houver irregularidade.',
                    ),
                  ),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Cancelar'),
            ),
            FilledButton.icon(
              onPressed: () => Navigator.pop(dialogContext, true),
              icon: const Icon(Icons.save_outlined),
              label: const Text('Salvar inspeção'),
            ),
          ],
        ),
      ),
    );

    if (saved != true) {
      observation.dispose();
      return;
    }

    final key = _monthKey(now);
    final payload = <String, dynamic>{
      'extinguisherId': extinguisher.id,
      'referenceMonth': key,
      'validity': checks['Validade'],
      'pressure': checks['Pressão / manômetro'],
      'seal': checks['Lacre e pino'],
      'signage': checks['Sinalização'],
      'access': checks['Acesso livre'],
      'hose': checks['Mangueira / bico'],
      'condition': checks['Condição geral'],
      'operationalStatus': operationalStatus,
      'result': overall,
      'observation': observation.text.trim(),
      'extinguisherTitle': extinguisher.title,
      'extinguisherLocation': '${p['location'] ?? p['local'] ?? ''}',
    };
    observation.dispose();

    final record = SstRecord(
      id: existing?.id ??
          'ext-month-${extinguisher.id}-${key.replaceAll('-', '')}',
      companyId: widget.company.id,
      sectorId: extinguisher.sectorId,
      type: 'EXTINTOR_INSPECAO_MENSAL',
      title: 'Inspeção mensal • ${extinguisher.title}',
      date: now,
      priority: overall == 'Conforme' ? 'Baixa' : 'Alta',
      payload: payload,
    );
    await AppDatabase.instance.upsertSstRecord(record);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          overall == 'Conforme'
              ? 'Inspeção mensal salva como conforme.'
              : 'Inspeção mensal salva com pendência.',
        ),
      ),
    );
  }

'''
ext = once(ext, build_anchor, methods + build_anchor, 'metodos inspecao mensal')

# -------- Modelo padrão inspirado no relatório Vitapan --------
old_current = r"""  static const ReportTemplateDefinition currentTemplate = ReportTemplateDefinition(
    id: currentTemplateId,
    name: 'Padrão Auditar atual',
    description: 'Modelo que já funciona hoje. Mantido intacto como padrão e fallback.',
    primaryColor: '#0B2E4F',
    secondaryColor: '#178A3D',
    headerTitle: 'RELATÓRIO DE INSPEÇÃO SST',
    headerStyle: 'classico',
    logoMode: 'ambas',
    footerText: 'Auditar SST - Segurança do Trabalho',
    photoColumns: 2,
    signatureStyle: 'app',
    showCover: true,
    showSummary: true,
    showChecklistDetails: true,
    isBuiltIn: true,
    useLegacyRenderer: true,
  );
"""
new_current = r"""  static const ReportTemplateDefinition currentTemplate = ReportTemplateDefinition(
    id: currentTemplateId,
    name: 'Auditar Vistoria Técnica',
    description: 'Modelo padrão Auditar: fotos à esquerda, situação, risco, correção e prioridade em leitura direta.',
    primaryColor: '#173E57',
    secondaryColor: '#178A3D',
    headerTitle: 'RELATÓRIO DE VISTORIA TÉCNICA',
    headerStyle: 'compacto',
    logoMode: 'ambas',
    footerText: 'Auditar Soluções • Medicina Ocupacional e Segurança do Trabalho',
    photoColumns: 2,
    signatureStyle: 'app',
    showCover: false,
    showSummary: false,
    showChecklistDetails: false,
    isBuiltIn: true,
    useLegacyRenderer: false,
  );
"""
tpl = once(tpl, old_current, new_current, 'modelo padrao')

# Identificação básica antes dos pontos de atenção.
old_points = """    widgets.add(_sectionTitle('Pontos de atenção', primary));
"""
new_points = """    if (template.id == ReportTemplateService.currentTemplateId) {
      widgets.add(_technicalIdentification(
        company: company,
        cnpj: '${header['company_cnpj'] ?? header['cnpj'] ?? ''}'.trim(),
        activity: '${header['company_activity'] ?? header['activity'] ?? ''}'.trim(),
        sector: sector,
        dateText: dateText,
        primary: primary,
      ));
      widgets.add(pw.SizedBox(height: 12));
    }
    widgets.add(_sectionTitle(
      template.id == ReportTemplateService.currentTemplateId
          ? 'REGISTROS DA VISTORIA'
          : 'Pontos de atenção',
      primary,
    ));
"""
pdf = once(pdf, old_points, new_points, 'identificacao tecnica')

# Troca o bloco de achado para o layout foto à esquerda / texto à direita.
old_return = """    return pw.Container(
      padding: const pw.EdgeInsets.all(11),
      decoration: pw.BoxDecoration(border: pw.Border.all(color: PdfColors.grey300, width: .8)),
      child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
"""
new_return = """    if (template.id == ReportTemplateService.currentTemplateId) {
      return _technicalIssueBlock(
        number: number,
        data: data,
        problem: problem,
        risk: risk,
        recommendation: recommendation,
        priority: priority,
        primary: primary,
      );
    }

    return pw.Container(
      padding: const pw.EdgeInsets.all(11),
      decoration: pw.BoxDecoration(border: pw.Border.all(color: PdfColors.grey300, width: .8)),
      child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
"""
pdf = once(pdf, old_return, new_return, 'layout tecnico dos achados')

helper_anchor = """  static pw.Widget _photos(List<pw.MemoryImage> images, int columns, PdfColor primary) {
"""
helpers = r'''  static pw.Widget _technicalIdentification({
    required String company,
    required String cnpj,
    required String activity,
    required String sector,
    required String dateText,
    required PdfColor primary,
  }) {
    pw.Widget line(String label, String value) => pw.Padding(
      padding: const pw.EdgeInsets.only(bottom: 4),
      child: pw.RichText(
        text: pw.TextSpan(children: [
          pw.TextSpan(
            text: '$label: ',
            style: pw.TextStyle(
              fontSize: 8.5,
              fontWeight: pw.FontWeight.bold,
              color: primary,
            ),
          ),
          pw.TextSpan(
            text: value.trim().isEmpty ? 'Não informado' : value.trim(),
            style: const pw.TextStyle(fontSize: 8.5),
          ),
        ]),
      ),
    );
    return pw.Container(
      width: double.infinity,
      padding: const pw.EdgeInsets.all(9),
      decoration: pw.BoxDecoration(
        border: pw.Border.all(color: PdfColors.grey500, width: .7),
      ),
      child: pw.Column(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: [
          pw.Text(
            'IDENTIFICAÇÃO DA EMPRESA',
            style: pw.TextStyle(
              fontSize: 10,
              fontWeight: pw.FontWeight.bold,
              color: primary,
            ),
          ),
          pw.SizedBox(height: 7),
          pw.Row(children: [
            pw.Expanded(child: line('EMPRESA', company)),
            pw.SizedBox(width: 12),
            pw.Expanded(child: line('CNPJ', cnpj)),
          ]),
          pw.Row(children: [
            pw.Expanded(child: line('ATIVIDADE', activity)),
            pw.SizedBox(width: 12),
            pw.Expanded(child: line('DATA', dateText)),
          ]),
          if (sector.trim().isNotEmpty) line('SETOR / ÁREA', sector),
        ],
      ),
    );
  }

  static pw.Widget _technicalIssueBlock({
    required int number,
    required _IssueData data,
    required String problem,
    required String risk,
    required String recommendation,
    required String priority,
    required PdfColor primary,
  }) {
    final photos = data.photos.take(3).toList();
    final normalized = priority.toLowerCase();
    final priorityColor =
        normalized.contains('imedi') || normalized.contains('alta') || normalized.contains('grave')
            ? PdfColors.red700
            : normalized.contains('baixa')
                ? PdfColors.green700
                : PdfColors.orange700;

    pw.Widget photoPane() {
      if (photos.isEmpty) {
        return pw.Container(
          height: 150,
          alignment: pw.Alignment.center,
          color: PdfColors.grey100,
          child: pw.Text('Sem fotografia', style: pw.TextStyle(fontSize: 8, color: PdfColors.grey600)),
        );
      }
      if (photos.length == 1) {
        return pw.Image(photos.first, height: 170, width: 220, fit: pw.BoxFit.contain);
      }
      return pw.Wrap(
        spacing: 5,
        runSpacing: 5,
        alignment: pw.WrapAlignment.center,
        children: photos.map((image) => pw.Container(
          width: photos.length == 2 ? 105 : 98,
          height: photos.length == 2 ? 145 : 95,
          child: pw.Image(image, fit: pw.BoxFit.cover),
        )).toList(),
      );
    }

    return pw.Container(
      decoration: pw.BoxDecoration(
        border: pw.Border.all(color: PdfColors.grey500, width: .7),
      ),
      child: pw.Row(
        crossAxisAlignment: pw.CrossAxisAlignment.stretch,
        children: [
          pw.Container(
            width: 230,
            padding: const pw.EdgeInsets.all(8),
            alignment: pw.Alignment.center,
            child: photoPane(),
          ),
          pw.Container(width: .7, color: PdfColors.grey500),
          pw.Expanded(
            child: pw.Padding(
              padding: const pw.EdgeInsets.all(10),
              child: pw.Column(
                crossAxisAlignment: pw.CrossAxisAlignment.start,
                children: [
                  pw.Text(
                    '${number.toString().padLeft(2, '0')}. ${data.answer.questionText.toUpperCase()}',
                    style: pw.TextStyle(
                      fontSize: 10.5,
                      fontWeight: pw.FontWeight.bold,
                      color: primary,
                    ),
                  ),
                  pw.SizedBox(height: 8),
                  _labelValue('Situação', problem),
                  _labelValue('Risco', risk),
                  _labelValue('Correção', recommendation),
                  pw.SizedBox(height: 5),
                  pw.Text(
                    'PRIORIDADE: ${priority.toUpperCase()}',
                    style: pw.TextStyle(
                      fontSize: 8.5,
                      fontWeight: pw.FontWeight.bold,
                      color: priorityColor,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

'''
pdf = once(pdf, helper_anchor, helpers + helper_anchor, 'helpers modelo tecnico')

extp.write_text(ext, encoding='utf-8', newline='\n')
tplp.write_text(tpl, encoding='utf-8', newline='\n')
pdfp.write_text(pdf, encoding='utf-8', newline='\n')

assert "value: 'monthly'" in ext
assert "EXTINTOR_INSPECAO_MENSAL" in ext
assert "Inspeção mensal do extintor" in ext
assert "name: 'Auditar Vistoria Técnica'" in tpl
assert "useLegacyRenderer: false" in tpl
assert "_technicalIssueBlock(" in pdf
assert "IDENTIFICAÇÃO DA EMPRESA" in pdf
print('EXTINTORES_MENSAIS_E_RELATORIO_PADRAO_OK')

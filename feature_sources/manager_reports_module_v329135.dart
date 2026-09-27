import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';

import '../database.dart';
import '../models.dart';
import '../services/document_delivery_service.dart';
import '../services/report_recipients.dart';

/// Gerencial: somente leitura dos registros existentes. Sem novas tabelas,
/// transporte, endpoints, publicacao automatica ou alteracao do GS.
enum ManagerReportKind { pending, activities, resolved, monthly }

extension ManagerReportKindLabel on ManagerReportKind {
  String get label {
    switch (this) {
      case ManagerReportKind.pending: return 'Pendências e plano de ação';
      case ManagerReportKind.activities: return 'Atividades realizadas';
      case ManagerReportKind.resolved: return 'Não conformidades resolvidas';
      case ManagerReportKind.monthly: return 'Acompanhamento gerencial';
    }
  }
}

class ManagerReportPeriod {
  final DateTime from;
  final DateTime through;
  const ManagerReportPeriod(this.from, this.through);
  bool contains(DateTime? date) {
    if (date == null) return false;
    final day = DateTime(date.year, date.month, date.day);
    final start = DateTime(from.year, from.month, from.day);
    final end = DateTime(through.year, through.month, through.day);
    return !day.isBefore(start) && !day.isAfter(end);
  }
  String get label => DateFormat('dd/MM/yyyy').format(from) +
      ' a ' + DateFormat('dd/MM/yyyy').format(through);
}

class ManagerReportDataset {
  final List<Map<String, Object?>> ncs;
  final List<Map<String, Object?>> actions;
  final List<Map<String, Object?>> inspections;
  final List<SstRecord> activities;
  const ManagerReportDataset(this.ncs, this.actions, this.inspections, this.activities);
}

class ManagerReportService {
  static String value(Map<String, Object?> row, String key) =>
      (row[key] ?? '').toString().trim();
  static DateTime? date(Map<String, Object?> row, String key) =>
      DateTime.tryParse(value(row, key));
  static bool closed(Map<String, Object?> row) {
    final text = value(row, 'status').toLowerCase();
    return text == 'concluída' || text == 'concluida' ||
        text == 'concluído' || text == 'concluido' ||
        text == 'resolvida' || text == 'resolvido';
  }
  static bool overdue(Map<String, Object?> row, DateTime now) {
    if (closed(row)) return false;
    if (value(row, 'status').toLowerCase() == 'vencida') return true;
    final due = date(row, 'next_due_date') ?? date(row, 'due_date');
    return due != null && DateTime(due.year, due.month, due.day)
        .isBefore(DateTime(now.year, now.month, now.day));
  }
  static List<Map<String, Object?>> selectNcs(
      List<Map<String, Object?>> rows, ManagerReportKind kind,
      ManagerReportPeriod period, String filter, DateTime now) {
    if (kind == ManagerReportKind.activities) return const [];
    return rows.where((row) {
      final done = closed(row);
      if (kind == ManagerReportKind.pending && done) return false;
      if (kind == ManagerReportKind.resolved &&
          (!done || !period.contains(date(row, 'verified_at')))) return false;
      // Backlog persists independently of the date of the original visit.
      if (kind == ManagerReportKind.monthly && done &&
          !period.contains(date(row, 'verified_at'))) return false;
      if (filter == 'Pendentes' && done) return false;
      if (filter == 'Atrasadas' && !overdue(row, now)) return false;
      if (filter == 'Resolvidas' && !done) return false;
      return true;
    }).toList(growable: false);
  }
  static List<Map<String, Object?>> selectActions(
      List<Map<String, Object?>> rows, ManagerReportKind kind,
      ManagerReportPeriod period, String filter, DateTime now) {
    if (kind == ManagerReportKind.activities) return const [];
    return rows.where((row) {
      final done = closed(row);
      if (kind == ManagerReportKind.pending && done) return false;
      if (kind == ManagerReportKind.resolved &&
          (!done || !period.contains(date(row, 'completion_date')))) return false;
      if (kind == ManagerReportKind.monthly && done &&
          !period.contains(date(row, 'completion_date'))) return false;
      if (filter == 'Pendentes' && done) return false;
      if (filter == 'Atrasadas' && !overdue(row, now)) return false;
      if (filter == 'Resolvidas' && !done) return false;
      return true;
    }).toList(growable: false);
  }

  static Future<ManagerReportDataset> load(Company company) async {
    final db = AppDatabase.instance;
    final ncs = await db.getNonConformityRows(
        companyId: company.id, includeClosed: true);
    final actions = await db.getPendingActions(
        companyId: company.id, includeCompleted: true);
    final inspections = await db.getInspectionHistory(companyId: company.id);
    final activities = <SstRecord>[];
    for (final type in const [
      'DDS', 'TREINAMENTO_SESSAO', 'INTEGRACAO',
      'OBSERVACAO_SEGURANCA', 'CIPA_REUNIAO'
    ]) {
      activities.addAll(await db.getSstRecords(type: type, companyId: company.id));
    }
    return ManagerReportDataset(ncs, actions, inspections, activities);
  }

  static const navy = PdfColor(0.07, 0.20, 0.27);
  static const green = PdfColor(0.06, 0.45, 0.37);
  static const pale = PdfColor(0.94, 0.97, 0.96);
  static const muted = PdfColor(0.35, 0.43, 0.47);

  static pw.Widget _text(String value, {double size = 9, bool bold = false,
      PdfColor color = navy}) => pw.Text(
    value.isEmpty ? 'Não informado' : value,
    style: pw.TextStyle(fontSize: size, color: color,
        fontWeight: bold ? pw.FontWeight.bold : pw.FontWeight.normal,
        lineSpacing: 2),
  );
  static pw.Widget _line(String label, String data) => pw.Padding(
    padding: const pw.EdgeInsets.only(bottom: 4),
    child: pw.RichText(text: pw.TextSpan(children: [
      pw.TextSpan(text: label + '  ', style: pw.TextStyle(
          fontSize: 8.5, color: navy, fontWeight: pw.FontWeight.bold)),
      pw.TextSpan(text: data.isEmpty ? 'Não informado' : data,
          style: const pw.TextStyle(fontSize: 8.5, color: muted)),
    ])),
  );
  static pw.Widget _section(String title) => pw.Padding(
    padding: const pw.EdgeInsets.only(top: 15, bottom: 9),
    child: pw.Container(padding: const pw.EdgeInsets.symmetric(vertical: 7, horizontal: 9),
      color: pale, child: _text(title, size: 11, bold: true)));
  static String _short(String value, {int max = 1100}) =>
      value.length > max ? value.substring(0, max) + ' [texto abreviado]' : value;
  static String _date(DateTime? d) =>
      d == null ? 'Não informada' : DateFormat('dd/MM/yyyy').format(d);

  static Future<pw.MemoryImage?> _photo(String path) async {
    if (path.trim().isEmpty) return null;
    try {
      final file = File(path);
      if (!await file.exists() || await file.length() == 0 ||
          await file.length() > 12 * 1024 * 1024) return null;
      return pw.MemoryImage(await file.readAsBytes());
    } catch (_) { return null; }
  }
  static Future<List<pw.Widget>> _evidence(String answerId, String actionId,
      bool includePhotos) async {
    if (!includePhotos) return [];
    final db = AppDatabase.instance;
    final blocks = <pw.Widget>[];
    final original = answerId.isEmpty ? <EvidencePhoto>[] :
        await db.getPhotosForAnswer(answerId);
    final after = actionId.isEmpty ? <CompletionPhoto>[] :
        await db.getCompletionPhotos(actionId);
    var any = false;
    for (final entry in [
      if (original.isNotEmpty) ('Antes / constatação', original.first.path),
      if (after.isNotEmpty) ('Depois / correção', after.first.path),
    ]) {
      final image = await _photo(entry.$2);
      if (image == null) {
        blocks.add(_line(entry.$1, 'Fotografia cadastrada indisponível neste aparelho.'));
      } else {
        any = true;
        blocks.add(pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [_text(entry.$1, size: 8, bold: true),
              pw.SizedBox(height: 4), pw.Image(image, height: 135,
                  width: 230, fit: pw.BoxFit.contain), pw.SizedBox(height: 6)]));
      }
    }
    if (!any && original.isEmpty && after.isEmpty) {
      blocks.add(_line('Evidência', 'Nenhuma fotografia associada a este registro.'));
    }
    return blocks;
  }

  static pw.Widget _recordHeader(String title, String subtitle) => pw.Column(
    crossAxisAlignment: pw.CrossAxisAlignment.start,
    children: [
      _text(title, bold: true, size: 9.5),
      pw.SizedBox(height: 3),
      _text(subtitle, size: 8, color: muted),
      pw.SizedBox(height: 7),
    ],
  );

  static Future<Uint8List> generate({
    required Company company,
    required ManagerReportDataset dataset,
    required ManagerReportKind kind,
    required ManagerReportPeriod period,
    required String status,
    required bool includePhotos,
  }) async {
    final now = DateTime.now();
    final ncs = selectNcs(dataset.ncs, kind, period, status, now);
    final actions = selectActions(dataset.actions, kind, period, status, now);
    final inspections = dataset.inspections.where((r) =>
        period.contains(date(r, 'date'))).toList();
    final activities = dataset.activities.where((r) =>
        period.contains(r.date) && r.type != 'RONDA_RASCUNHO').toList();
    final distinctRound = <String>{};
    final activityRows = <(String, String, DateTime)>[];
    if (kind == ManagerReportKind.activities || kind == ManagerReportKind.monthly) {
      for (final r in inspections) {
        activityRows.add(('Vistoria', value(r, 'area').isEmpty
            ? value(r, 'checklist_type') : value(r, 'area'),
            date(r, 'date') ?? now));
      }
      for (final r in activities) {
        final isRound = r.type == 'OBSERVACAO_SEGURANCA' &&
            ((r.payload['roundType'] ?? '') == 'RONDA_EXPRESSA' ||
             (r.payload['roundId'] ?? '').toString().isNotEmpty);
        final group = (r.payload['roundId'] ?? '').toString();
        if (isRound && group.isNotEmpty && !distinctRound.add(group)) continue;
        final type = r.type == 'DDS' ? 'DDS' :
            r.type == 'TREINAMENTO_SESSAO' ? 'Treinamento' :
            r.type == 'INTEGRACAO' ? 'Integração' :
            r.type == 'CIPA_REUNIAO' ? 'Reunião CIPA' :
            isRound ? 'Vistoria rápida' : 'Registro de SST';
        activityRows.add((type, r.title, r.date));
      }
      activityRows.sort((a, b) => b.$3.compareTo(a.$3));
    }

    final doc = pw.Document();
    pw.MemoryImage? logo;
    try {
      final bytes = await rootBundle.load('assets/branding/auditar_icon.png');
      logo = pw.MemoryImage(bytes.buffer.asUint8List());
    } catch (_) {}
    final pages = <pw.Widget>[
      pw.Container(
        padding: const pw.EdgeInsets.all(17),
        decoration: const pw.BoxDecoration(color: navy),
        child: pw.Row(children: [
          if (logo != null) pw.Image(logo, height: 36, width: 36),
          if (logo != null) pw.SizedBox(width: 11),
          pw.Expanded(child: pw.Column(
              crossAxisAlignment: pw.CrossAxisAlignment.start,
              children: [
                pw.Text('AUDITAR SST', style: pw.TextStyle(color: PdfColors.white,
                    fontSize: 18, fontWeight: pw.FontWeight.bold)),
                pw.Text('SEGURANÇA E SAÚDE DO TRABALHO',
                    style: const pw.TextStyle(color: PdfColors.white, fontSize: 8)),
              ])),
        ]),
      ),
      pw.SizedBox(height: 16),
      _text('RELATÓRIO GERENCIAL • ' + kind.label.toUpperCase(),
          size: 14, bold: true),
      pw.SizedBox(height: 10),
      _line('Empresa', company.name),
      if ((company.cnpj ?? '').isNotEmpty) _line('CNPJ', company.cnpj!),
      _line('Período de referência', period.label),
      _line('Emissão', DateFormat('dd/MM/yyyy HH:mm').format(now)),
      _line('Filtro de situação', status),
      _line('Critério', 'Pendências mostram o estoque aberto atual, inclusive de visitas anteriores. '
          'Atividades e conclusões consideram o período selecionado.'),
      _section('VISÃO GERAL'),
      pw.Wrap(spacing: 10, runSpacing: 7, children: [
        _metric('NCs na seleção', ncs.length),
        _metric('Ações na seleção', actions.length),
        if (kind == ManagerReportKind.activities || kind == ManagerReportKind.monthly)
          _metric('Atividades no período', activityRows.length),
        _metric('NCs vencidas na seleção',
            ncs.where((r) => overdue(r, now)).length),
      ]),
    ];

    if (kind == ManagerReportKind.pending || kind == ManagerReportKind.monthly ||
        kind == ManagerReportKind.resolved) {
      pages.add(_section(kind == ManagerReportKind.resolved
          ? 'NÃO CONFORMIDADES CONCLUÍDAS E VERIFICADAS'
          : 'NÃO CONFORMIDADES • SITUAÇÃO ATUAL'));
      if (ncs.isEmpty) pages.add(_text('Nenhuma NC encontrada para este filtro.', color: muted));
      for (final nc in ncs) {
        final code = value(nc, 'code');
        final id = value(nc, 'id');
        final associated = actions.where((a) => value(a, 'nc_id') == id).toList();
        pages.add(_recordHeader(code.isEmpty ? 'Não conformidade' : code,
            value(nc, 'sector_name') + '  •  ' + value(nc, 'classification') +
            '  •  ' + value(nc, 'status')));
        pages.add(_line('Situação identificada', _short(value(nc, 'description'))));
        pages.add(_line('Correção recomendada', _short(value(nc, 'recommendation'))));
        pages.add(_line('Origem', _date(date(nc, 'inspection_date'))));
        if (closed(nc)) {
          pages.add(_line('Verificada em', _date(date(nc, 'verified_at'))));
          pages.add(_line('Verificada por', value(nc, 'verified_by')));
        } else {
          pages.add(_line('Prazo previsto', _date(date(nc, 'next_due_date'))));
        }
        for (final action in associated) {
          pages.add(_line('Plano de ação', _short(value(action, 'corrective_action'))));
          pages.add(_line('Responsável', value(action, 'responsible')));
          pages.add(_line('Prazo', _date(date(action, 'due_date'))));
          pages.add(_line('Situação da ação', value(action, 'status')));
          if (closed(action)) {
            pages.add(_line('Correção registrada em', _date(date(action, 'completion_date'))));
            pages.add(_line('Registro da execução', _short(value(action, 'completion_note'))));
            pages.add(_line('Executada por', value(action, 'completed_by')));
          }
        }
        pages.addAll(await _evidence(value(nc, 'answer_id'),
            associated.isEmpty ? '' : value(associated.first, 'id'), includePhotos));
        pages.add(pw.Divider(color: PdfColors.grey300));
      }
      // Actions with no linked NC must not disappear from the management report.
      final linkedIds = ncs.map((e) => value(e, 'id')).toSet();
      final standalone = actions.where((a) => value(a, 'nc_id').isEmpty ||
          !linkedIds.contains(value(a, 'nc_id'))).toList();
      if (standalone.isNotEmpty) {
        pages.add(_section('AÇÕES REGISTRADAS'));
        for (final action in standalone) {
          pages.add(_recordHeader(_short(value(action, 'non_conformity'), max: 150),
              value(action, 'area') + ' • ' + value(action, 'status')));
          pages.add(_line('Ação necessária', _short(value(action, 'corrective_action'))));
          pages.add(_line('Responsável', value(action, 'responsible')));
          pages.add(_line('Prazo', _date(date(action, 'due_date'))));
          if (closed(action)) {
            pages.add(_line('Correção registrada em',
                _date(date(action, 'completion_date'))));
            pages.add(_line('Execução', _short(value(action, 'completion_note'))));
          }
          pages.addAll(await _evidence(value(action, 'answer_id'),
              value(action, 'id'), includePhotos));
          pages.add(pw.Divider(color: PdfColors.grey300));
        }
      }
    }
    if (kind == ManagerReportKind.activities || kind == ManagerReportKind.monthly) {
      pages.add(_section('ATIVIDADES REGISTRADAS NO PERÍODO'));
      if (activityRows.isEmpty) pages.add(_text(
        'Não há atividades cadastradas neste intervalo.', color: muted));
      for (final row in activityRows) {
        pages.add(pw.Padding(padding: const pw.EdgeInsets.only(bottom: 8),
            child: _line(_date(row.$3) + ' • ' + row.$1, _short(row.$2, max: 450))));
      }
      pages.add(_line('Observação',
          'A lista apresenta registros disponíveis. Não comprova atividades externas '
          'que não tenham sido cadastradas no aplicativo.'));
    }
    pages.add(_section('ENCAMINHAMENTO À GERÊNCIA'));
    pages.add(_text(kind == ManagerReportKind.activities
        ? 'Documento de acompanhamento das atividades registradas no período.'
        : 'Programar as ações pendentes, confirmar responsáveis e prazos, '
          'registrar evidências da execução e submeter as correções à verificação.',
        color: muted));
    pages.add(pw.SizedBox(height: 13));
    pages.add(_text('Documento gerado a partir dos registros disponíveis no Auditar SST. '
        'Situações marcadas como concluídas e verificadas são distintas de ações '
        'apenas informadas como executadas.', size: 7.5, color: muted));
    doc.addPage(pw.MultiPage(
      maxPages: 500,
      pageFormat: PdfPageFormat.a4,
      margin: const pw.EdgeInsets.fromLTRB(34, 31, 34, 39),
      footer: (context) => pw.Row(
        mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
        children: [_text('AUDITAR SST  •  ' + company.name, size: 7, color: muted),
          _text('Página ' + context.pageNumber.toString() + ' de ' +
              context.pagesCount.toString(), size: 7, color: muted)]),
      build: (context) => pages,
    ));
    return doc.save();
  }

  static pw.Widget _metric(String title, int count) => pw.Container(
      width: 108, padding: const pw.EdgeInsets.all(10),
      decoration: pw.BoxDecoration(color: pale,
          borderRadius: pw.BorderRadius.circular(7)),
      child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [_text(count.toString(), size: 18, bold: true, color: green),
            _text(title, size: 7, color: muted)]));
}

class ManagerReportsScreen extends StatefulWidget {
  final Company company;
  const ManagerReportsScreen({super.key, required this.company});
  @override
  State<ManagerReportsScreen> createState() => _ManagerReportsScreenState();
}

class _ManagerReportsScreenState extends State<ManagerReportsScreen> {
  ManagerReportKind kind = ManagerReportKind.pending;
  String periodChoice = 'Mês atual';
  String status = 'Todas';
  bool includePhotos = true;
  bool busy = false;
  bool sending = false;
  String progress = '';
  ManagerReportDataset? data;
  DateTime? from;
  DateTime? through;

  ManagerReportPeriod get period {
    final now = DateTime.now();
    if (periodChoice == 'Visita atual') {
      final dates = <DateTime>[
        if (data != null) ...data!.inspections
            .map((r) => ManagerReportService.date(r, 'date'))
            .whereType<DateTime>(),
        if (data != null) ...data!.activities
            .where((r) => r.type == 'OBSERVACAO_SEGURANCA')
            .map((r) => r.date),
      ]..sort((a, b) => b.compareTo(a));
      final recent = dates.isEmpty ? now : dates.first;
      return ManagerReportPeriod(recent, recent);
    }
    if (periodChoice == 'Esta semana') {
      return ManagerReportPeriod(
          DateTime(now.year, now.month, now.day).subtract(
              Duration(days: now.weekday - 1)), now);
    }
    if (periodChoice == 'Personalizado' && from != null && through != null) {
      return ManagerReportPeriod(from!, through!);
    }
    return ManagerReportPeriod(DateTime(now.year, now.month, 1), now);
  }
  @override
  void initState() { super.initState(); _load(); }
  Future<void> _load() async {
    setState(() {busy = true; progress = 'Consultando registros da empresa...';});
    try {
      final loaded = await ManagerReportService.load(widget.company);
      if (mounted) setState(() => data = loaded);
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Não foi possível consultar os registros: ' + e.toString())));
    } finally {
      if (mounted) setState(() { busy = false; progress = ''; });
    }
  }
  Future<void> _dateSelect(bool start) async {
    final now = DateTime.now();
    final result = await showDatePicker(context: context,
        initialDate: (start ? from : through) ?? now,
        firstDate: DateTime(2010), lastDate: DateTime(now.year + 2));
    if (result == null || !mounted) return;
    setState(() { if (start) { from = result; } else { through = result; } });
  }
  Future<void> _emailReport(
      BuildContext previewContext, Uint8List bytes, String fileName) async {
    if (sending) return;
    if (bytes.length > 7500000) {
      if (previewContext.mounted) {
        ScaffoldMessenger.of(previewContext).showSnackBar(const SnackBar(
          content: Text('O envio direto aceita PDF de até 7 MB. Use o compartilhamento do PDF.'),
        ));
      }
      return;
    }
    final primary = widget.company.reportEmail.trim();
    final additional = widget.company.secondaryReportEmail.trim();
    final validation = ReportRecipients.validationError(primary, additional);
    if (validation != null || primary.isEmpty) {
      if (previewContext.mounted) {
        ScaffoldMessenger.of(previewContext).showSnackBar(SnackBar(
          content: Text(validation ??
              'Cadastre os destinatários na edição da empresa.'),
        ));
      }
      return;
    }
    final recipients = ReportRecipients.parse(primary, additional);
    final confirmed = await showDialog<bool>(
      context: previewContext,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Enviar relatório gerencial?'),
        content: Text(
          'Documento: ' + kind.label +
          '\nEmpresa: ' + widget.company.name +
          '\nDestinatários: ' + recipients.join(', ') +
          '\n\nO envio será registrado no histórico de documentos da empresa.',
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Cancelar')),
          FilledButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('Confirmar envio')),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    setState(() => sending = true);
    try {
      final result = await DocumentDeliveryService.send(
        companyId: widget.company.id,
        companyName: widget.company.name,
        documentId: 'gerencial:' + kind.name + ':' +
            DateTime.now().millisecondsSinceEpoch.toString(),
        category: 'Relatório gerencial',
        title: kind.label + ' • ' + period.label,
        to: primary,
        cc: additional,
        fileName: fileName,
        bytes: bytes,
      );
      if (previewContext.mounted) {
        ScaffoldMessenger.of(previewContext).showSnackBar(
          SnackBar(content: Text(result)),
        );
      }
    } catch (error) {
      if (previewContext.mounted) {
        ScaffoldMessenger.of(previewContext).showSnackBar(
          SnackBar(content: Text('Envio não confirmado: ' + error.toString())),
        );
      }
    } finally {
      if (mounted) setState(() => sending = false);
    }
  }

  Future<void> _generate() async {
    if (busy || data == null) return;
    if (periodChoice == 'Personalizado' &&
        (from == null || through == null || from!.isAfter(through!))) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Informe data inicial e final válidas.')));
      return;
    }
    setState(() { busy = true; progress = 'Preparando PDF e conferindo evidências...'; });
    try {
      final bytes = await ManagerReportService.generate(
          company: widget.company, dataset: data!, kind: kind,
          period: period, status: status, includePhotos: includePhotos);
      if (!mounted) return;
      if (bytes.length < 1024 ||
          bytes[0] != 0x25 || bytes[1] != 0x50 ||
          bytes[2] != 0x44 || bytes[3] != 0x46) {
        throw StateError('O documento gerado não é um PDF válido.');
      }
      final name = 'Auditar_Gerencial_' + kind.name + '_' +
          DateFormat('yyyyMMdd').format(DateTime.now()) + '.pdf';
      setState(() { busy = false; progress = ''; });
      await Navigator.of(context).push(MaterialPageRoute<void>(
          builder: (previewContext) => Scaffold(
            appBar: AppBar(
              title: Text(kind.label),
              actions: [
                IconButton(
                  tooltip: 'Enviar aos e-mails cadastrados da empresa',
                  icon: const Icon(Icons.mark_email_read_outlined),
                  onPressed: () => _emailReport(previewContext, bytes, name),
                ),
              ],
            ),
            body: PdfPreview(
                build: (format) async => bytes,
                pdfFileName: name,
                allowPrinting: true, allowSharing: true),
          )));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Falha na geração: ' + e.toString())));
    } finally {
      if (mounted) setState(() { busy = false; progress = ''; });
    }
  }
  @override
  Widget build(BuildContext context) {
    const navyColor = Color(0xFF123B4B);
    return Scaffold(
      appBar: AppBar(title: const Text('Relatórios gerenciais')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        Card(color: navyColor, child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('AUDITAR SST • GERÊNCIA', style: TextStyle(
                  color: Color(0xFFA0E9D0), fontWeight: FontWeight.bold)),
              const SizedBox(height: 7),
              Text(widget.company.name, style: const TextStyle(
                  color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
              const SizedBox(height: 6),
              const Text('Informações objetivas para acompanhamento de '
                  'pendências, correções e serviços registrados.',
                  style: TextStyle(color: Colors.white70)),
            ]))),
        const SizedBox(height: 16),
        DropdownButtonFormField<ManagerReportKind>(
          value: kind, decoration: const InputDecoration(
              labelText: 'Tipo de relatório', border: OutlineInputBorder()),
          isExpanded: true,
          items: ManagerReportKind.values.map((e) =>
              DropdownMenuItem(value: e, child: Text(e.label))).toList(),
          onChanged: busy ? null : (v) { if (v != null) setState(() => kind = v); },
        ),
        const SizedBox(height: 13),
        DropdownButtonFormField<String>(
          value: periodChoice,
          decoration: const InputDecoration(labelText: 'Período',
              border: OutlineInputBorder()),
          items: const ['Visita atual', 'Esta semana', 'Mês atual', 'Personalizado']
              .map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
          onChanged: busy ? null : (v) {
            if (v != null) setState(() => periodChoice = v);
          },
        ),
        if (periodChoice == 'Personalizado') ...[
          const SizedBox(height: 9),
          Wrap(spacing: 8, runSpacing: 8, children: [
            OutlinedButton.icon(onPressed: busy ? null : () => _dateSelect(true),
                icon: const Icon(Icons.event), label: Text(from == null ?
                    'Data inicial' : DateFormat('dd/MM/yyyy').format(from!))),
            OutlinedButton.icon(onPressed: busy ? null : () => _dateSelect(false),
                icon: const Icon(Icons.event), label: Text(through == null ?
                    'Data final' : DateFormat('dd/MM/yyyy').format(through!))),
          ]),
        ],
        const SizedBox(height: 13),
        DropdownButtonFormField<String>(
          value: status,
          decoration: const InputDecoration(
              labelText: 'Filtro de situação', border: OutlineInputBorder()),
          items: const ['Todas', 'Pendentes', 'Atrasadas', 'Resolvidas']
              .map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
          onChanged: busy ? null : (v) {
            if (v != null) setState(() => status = v);
          },
        ),
        SwitchListTile.adaptive(
          title: const Text('Incluir fotografias disponíveis'),
          subtitle: const Text('Registros sem foto continuam no relatório.'),
          value: includePhotos, onChanged: busy ? null :
              (v) => setState(() => includePhotos = v),
        ),
        const SizedBox(height: 6),
        if (data != null) Card(
            child: Padding(padding: const EdgeInsets.all(13), child: Text(
                'Base consultada: ' + data!.ncs.length.toString() +
                ' NCs, ' + data!.actions.length.toString() + ' ações, ' +
                data!.inspections.length.toString() + ' vistorias e ' +
                data!.activities.length.toString() + ' registros SST.'))),
        const SizedBox(height: 8),
        if (busy) Column(children: [
          Text(progress), const SizedBox(height: 8),
          const LinearProgressIndicator(), const SizedBox(height: 8),
        ]),
        FilledButton.icon(
          onPressed: busy || data == null ? null : _generate,
          icon: const Icon(Icons.picture_as_pdf_outlined),
          label: const Text('Gerar, conferir e compartilhar PDF'),
        ),
        const SizedBox(height: 8),
        TextButton.icon(onPressed: busy ? null : _load,
            icon: const Icon(Icons.refresh), label: const Text('Atualizar dados')),
        const SizedBox(height: 8),
        const Text('Os relatórios utilizam os registros existentes. A correção '
            'informada e a NC verificada são situações distintas. O PDF só é '
            'compartilhado após sua conferência; não é publicado '
            'automaticamente para os clientes.',
            style: TextStyle(fontSize: 12, color: Colors.black54)),
      ]),
    );
  }
}

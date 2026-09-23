import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/services.dart' show rootBundle;
import 'package:intl/intl.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import '../database.dart';
import '../models.dart';
import 'report_template_service.dart';

/// Built-in institutional renderer inspired by the supplied Auditar inspection PDF.
/// All statements come from the selected inspection; no fabricated test results.
class AuditarStandard2PdfService {
  static const _navy = PdfColor(0.10, 0.19, 0.36);
  static const _green = PdfColor(0.0, 0.56, 0.21);
  static const _line = PdfColor(0.58, 0.61, 0.65);
  static const _yellow = PdfColor(1, 0.95, 0.44);
  static const _contact =
      '(86) 3221-1549  |  (86) 99400-6110  |  (86) 99552-3432';

  static Future<Uint8List> generateInspectionPdf(
    String inspectionId, {
    required Map<String, Object?> header,
    required ReportTemplateDefinition template,
    bool executive = false,
    bool? includeActionPlan,
  }) async {
    final db = AppDatabase.instance;
    final answers = await db.getAnswers(inspectionId);
    final ncs = await db.getNonConformitiesForInspection(inspectionId);
    final actions = await db.getActionsForInspection(inspectionId);
    final byAnswer = <String, NonConformity>{
      for (final item in ncs) item.answerId: item,
    };
    final actionsByAnswer = <String, List<ActionPlan>>{};
    for (final item in actions) {
      actionsByAnswer.putIfAbsent(item.answerId, () => <ActionPlan>[]).add(item);
    }
    final logo = await _asset('assets/branding/sst_green_official.png');
    final companyLogo = await _image(
      (header['company_logo_path'] ?? '').toString(),
    );
    final technicianSign = await _image(
      (header['technician_signature_path'] ?? '').toString(),
    );
    final companySign = await _image(
      (header['responsible_signature_path'] ?? '').toString(),
    );

    final companies = await db.getCompanies(onlyActive: false);
    final companyId = (header['company_id'] ?? '').toString();
    Company? companyRecord;
    for (final entry in companies) {
      if (entry.id == companyId) {
        companyRecord = entry;
        break;
      }
    }
    final company = _filled([
      header['company_name'],
      companyRecord?.name,
    ]);
    final cnpj = _filled([header['company_cnpj'], companyRecord?.cnpj]);
    final address = _filled([
      header['worksite_address'],
      [
        companyRecord?.city ?? '',
        companyRecord?.uf ?? '',
      ].where((e) => e.trim().isNotEmpty).join(' - '),
    ]);
    final rawDate = DateTime.tryParse((header['date'] ?? '').toString());
    final date = rawDate == null ? '-' : DateFormat('dd/MM/yyyy').format(rawDate);
    final number = (header['report_number'] ?? '').toString().trim();
    final worksite = (header['worksite_name'] ?? '').toString().trim();
    final sector = (header['sector_name'] ?? '').toString().trim();
    final technician = (header['technician_name'] ?? '').toString().trim();
    final responsible = (header['responsible_name'] ?? '').toString().trim();
    final includePlan = includeActionPlan ??
        ((header['include_action_plan'] ?? '1').toString() != '0');

    final widgets = <pw.Widget>[
      pw.Center(
        child: pw.Text(
          'RELATÓRIO DE INSPEÇÃO DE SEGURANÇA DO TRABALHO',
          style: pw.TextStyle(
            fontSize: 12,
            fontWeight: pw.FontWeight.bold,
            color: _navy,
          ),
        ),
      ),
      pw.SizedBox(height: 3),
      pw.Center(
        child: pw.Text(
          'CONFORMIDADES / NÃO CONFORMIDADES',
          style: pw.TextStyle(fontSize: 10, fontWeight: pw.FontWeight.bold),
        ),
      ),
      pw.SizedBox(height: 14),
      _identityField('EMPRESA', company),
      _identityField('CNPJ', cnpj),
      _identityField('ENDEREÇO', address),
      if (worksite.isNotEmpty) _identityField('OBRA / UNIDADE', worksite),
      if (sector.isNotEmpty) _identityField('SETOR / ÁREA', sector),
      _identityField('DATA DA VISTORIA', date),
      if (number.isNotEmpty) _identityField('RELATÓRIO', number),
      pw.SizedBox(height: 16),
    ];

    var shown = 0;
    for (final answer in answers) {
      if (answer.status == 'Não se aplica' ||
          answer.status == 'N/A' ||
          answer.status == 'NSA') {
        continue;
      }
      final nc = byAnswer[answer.id];
      final linked = actionsByAnswer[answer.id] ?? const <ActionPlan>[];
      final photos = await db.getPhotosForAnswer(answer.id);
      final images = <pw.MemoryImage>[];
      for (final photo in photos) {
        final image = await _image(photo.path);
        if (image != null) images.add(image);
      }
      // A conforming, undocumented yes/no answer belongs in checklist data,
      // not as a fabricated detailed inspection paragraph.
      if (answer.status == 'Conforme' &&
          answer.observation.trim().isEmpty &&
          images.isEmpty) {
        continue;
      }
      shown++;
      final title = _filled([
        answer.questionCategory,
        answer.questionText,
        'ITEM AVALIADO ' + shown.toString(),
      ]);
      if (images.isNotEmpty) {
        for (var start = 0; start < images.length; start += 3) {
          final end = start + 3 < images.length ? start + 3 : images.length;
          widgets.add(_gallery(images.sublist(start, end)));
        }
      }
      widgets.add(_banner(title));
      if (answer.questionText.trim().isNotEmpty &&
          answer.questionText.trim() != title) {
        widgets.add(_paragraph('IDENTIFICAÇÃO DO ITEM AVALIADO',
            answer.questionText.trim()));
      }
      final situation = answer.observation.trim().isNotEmpty
          ? answer.observation.trim()
          : 'Resultado registrado na vistoria: ' + answer.status + '.';
      widgets.add(_paragraph('INSPEÇÃO REALIZADA', situation));
      if (nc != null && nc.description.trim().isNotEmpty) {
        widgets.add(
            _paragraph('NÃO CONFORMIDADES IDENTIFICADAS', nc.description));
      }
      final correction = _filled([
        nc?.recommendation,
        answer.recommendation,
        if (includePlan && linked.isNotEmpty) linked.first.correctiveAction,
      ]);
      if (correction.isNotEmpty) {
        widgets.add(_paragraph('MEDIDAS DE CORREÇÃO NECESSÁRIAS', correction));
      }
      if (answer.questionReference.trim().isNotEmpty) {
        widgets.add(_smallLine(
            'Referência: ' + answer.questionReference.trim()));
      }
      widgets.add(pw.SizedBox(height: 13));
    }
    if (shown == 0) {
      widgets.add(_paragraph('INSPEÇÃO REALIZADA',
          'Nenhum item com descrição ou evidência fotográfica foi registrado para este modelo.'));
    }

    final conclusion = (header['conclusion'] ?? '').toString().trim();
    widgets.addAll([
      pw.SizedBox(height: 12),
      _banner('CONCLUSÃO'),
      pw.Text(
        conclusion.isNotEmpty
            ? conclusion
            : 'Este relatório documenta as condições registradas na data da vistoria. '
              'As pendências identificadas devem ser acompanhadas e verificadas '
              'em nova inspeção. O documento não confirma regularização posterior.',
        style: const pw.TextStyle(fontSize: 9.5, lineSpacing: 2.0),
        textAlign: pw.TextAlign.justify,
      ),
      pw.SizedBox(height: 26),
      pw.Row(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: [
          _signature('RESPONSÁVEL TÉCNICO', technician, technicianSign),
          pw.SizedBox(width: 22),
          _signature('RESPONSÁVEL PELA EMPRESA', responsible, companySign),
        ],
      ),
    ]);

    final document = pw.Document(
      title: 'Padrão Auditar 2 - ' + company,
      author: 'Auditar Soluções',
    );
    document.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.fromLTRB(31, 20, 31, 38),
        maxPages: 300,
        header: (_) => _header(logo, companyLogo, company),
        footer: (context) => _footer(context),
        build: (_) => widgets,
      ),
    );
    return document.save();
  }

  static String _filled(List<Object?> values) {
    for (final raw in values) {
      final text = (raw ?? '').toString().trim();
      if (text.isNotEmpty && text.toLowerCase() != 'null') return text;
    }
    return '';
  }

  static pw.Widget _header(
    pw.MemoryImage? logo,
    pw.MemoryImage? companyLogo,
    String company,
  ) {
    return pw.Container(
      padding: const pw.EdgeInsets.only(bottom: 7),
      margin: const pw.EdgeInsets.only(bottom: 9),
      decoration: const pw.BoxDecoration(
        border: pw.Border(bottom: pw.BorderSide(color: _line, width: .55)),
      ),
      child: pw.Row(
        crossAxisAlignment: pw.CrossAxisAlignment.center,
        children: [
          _logo(logo, 52),
          pw.SizedBox(width: 9),
          pw.Expanded(
            child: pw.Column(
              children: [
                pw.Text('AUDITAR SOLUÇÕES',
                    style: pw.TextStyle(
                      color: _green,
                      fontSize: 10,
                      fontWeight: pw.FontWeight.bold,
                    )),
                pw.Text('MEDICINA OCUPACIONAL E SEGURANÇA DO TRABALHO',
                    textAlign: pw.TextAlign.center,
                    style: const pw.TextStyle(fontSize: 5.7)),
                pw.SizedBox(height: 3),
                pw.Text('CNPJ: 31.576.433/0001-13',
                    style: pw.TextStyle(
                      color: _navy, fontWeight: pw.FontWeight.bold,
                      fontSize: 7.0)),
                pw.Text('Rua Olavo Bilac, nº 1543 - Centro (Sul), Teresina/PI',
                    textAlign: pw.TextAlign.center,
                    style: const pw.TextStyle(fontSize: 6.3)),
              ],
            ),
          ),
          pw.SizedBox(width: 9),
          _logo(companyLogo ?? logo, 52),
        ],
      ),
    );
  }

  static pw.Widget _logo(pw.MemoryImage? image, double size) {
    return pw.SizedBox(
      width: size,
      height: size,
      child: image == null
          ? pw.SizedBox()
          : pw.Image(image, fit: pw.BoxFit.contain),
    );
  }

  static pw.Widget _identityField(String label, String value) {
    return pw.Table(
      border: pw.TableBorder.all(color: _line, width: .55),
      columnWidths: const {
        0: pw.FixedColumnWidth(94),
        1: pw.FlexColumnWidth(),
      },
      children: [
        pw.TableRow(children: [
          pw.Padding(
            padding: const pw.EdgeInsets.all(5),
            child: pw.Text(label + ':',
                style: pw.TextStyle(fontSize: 8, fontWeight: pw.FontWeight.bold)),
          ),
          pw.Padding(
            padding: const pw.EdgeInsets.all(5),
            child: pw.Text(value.isEmpty ? 'Não informado' : value,
                style: const pw.TextStyle(fontSize: 8)),
          ),
        ]),
      ],
    );
  }

  static pw.Widget _banner(String label) {
    return pw.Container(
      width: double.infinity,
      padding: const pw.EdgeInsets.symmetric(vertical: 5, horizontal: 7),
      decoration: const pw.BoxDecoration(
        color: _yellow,
        border: pw.Border(
          top: pw.BorderSide(color: _line, width: .5),
          bottom: pw.BorderSide(color: _line, width: .5),
        ),
      ),
      child: pw.Center(
        child: pw.Text(label.toUpperCase(),
            style: pw.TextStyle(
              color: _navy, fontSize: 9.3, fontWeight: pw.FontWeight.bold,
            ),
            textAlign: pw.TextAlign.center),
      ),
    );
  }

  static pw.Widget _gallery(List<pw.MemoryImage> images) {
    return pw.Container(
      height: 133,
      padding: const pw.EdgeInsets.all(5),
      decoration: pw.BoxDecoration(border: pw.Border.all(color: _line, width: .5)),
      child: pw.Row(
        children: [
          for (var i = 0; i < images.length; i++) ...[
            if (i > 0) pw.SizedBox(width: 5),
            pw.Expanded(
              child: pw.Image(images[i], fit: pw.BoxFit.contain),
            ),
          ],
        ],
      ),
    );
  }

  static pw.Widget _paragraph(String title, String content) {
    return pw.Padding(
      padding: const pw.EdgeInsets.only(top: 7, bottom: 2),
      child: pw.Column(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: [
          pw.Text(title,
              style: pw.TextStyle(
                  fontSize: 8.9, fontWeight: pw.FontWeight.bold, color: _navy)),
          pw.SizedBox(height: 3),
          pw.Text(content, style: const pw.TextStyle(
              fontSize: 9.1, lineSpacing: 1.9),
              textAlign: pw.TextAlign.justify),
        ],
      ),
    );
  }

  static pw.Widget _smallLine(String value) => pw.Padding(
    padding: const pw.EdgeInsets.only(top: 3),
    child: pw.Text(value,
        style: const pw.TextStyle(fontSize: 7.1, color: PdfColors.grey700)),
  );

  static pw.Widget _signature(
    String label,
    String name,
    pw.MemoryImage? image,
  ) {
    return pw.Expanded(
      child: pw.Column(
        children: [
          pw.SizedBox(
            height: 39,
            child: image == null
                ? pw.SizedBox()
                : pw.Image(image, fit: pw.BoxFit.contain),
          ),
          pw.Container(height: .7, color: _navy),
          pw.SizedBox(height: 5),
          pw.Text(label,
              textAlign: pw.TextAlign.center,
              style: pw.TextStyle(
                  fontSize: 7.6, fontWeight: pw.FontWeight.bold)),
          pw.Text(name.isEmpty ? 'Nome e assinatura' : name,
              textAlign: pw.TextAlign.center,
              style: const pw.TextStyle(fontSize: 7.2)),
        ],
      ),
    );
  }

  static pw.Widget _footer(pw.Context context) => pw.Container(
        alignment: pw.Alignment.center,
        padding: const pw.EdgeInsets.symmetric(vertical: 5),
        decoration: const pw.BoxDecoration(color: _green),
        child: pw.Row(
          children: [
            pw.Expanded(
              child: pw.Text(_contact,
                  textAlign: pw.TextAlign.center,
                  style: const pw.TextStyle(
                      fontSize: 7.0, color: PdfColors.white)),
            ),
            pw.Text(
              context.pageNumber.toString() + '/' + context.pagesCount.toString(),
              style: const pw.TextStyle(
                  fontSize: 6.5, color: PdfColors.white),
            ),
          ],
        ),
      );

  static Future<pw.MemoryImage?> _asset(String path) async {
    try {
      final data = await rootBundle.load(path);
      return pw.MemoryImage(data.buffer.asUint8List());
    } catch (_) {
      return null;
    }
  }

  static Future<pw.MemoryImage?> _image(String path) async {
    if (path.trim().isEmpty) return null;
    try {
      final file = File(path);
      if (!await file.exists()) return null;
      return pw.MemoryImage(await file.readAsBytes());
    } catch (_) {
      return null;
    }
  }
}
// Build marker: extinguisher monthly PDF compile fix included.
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/services.dart' show rootBundle;
import 'package:intl/intl.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import '../database.dart';
import '../models.dart';
import 'report_logo_service.dart';
import 'report_template_service.dart';

/// Padrão Auditar 3 baseado no modelo de vistoria técnica aprovado
/// pelo usuário: cabeçalho institucional, identificação da empresa e achados
/// em duas colunas (evidências à esquerda; texto técnico à direita).
///
/// O serviço não inventa risco, prioridade ou conclusão. Só imprime campos
/// presentes nos registros da vistoria.
class AuditarStandard3PdfService {
  static const _navy = PdfColor(0.08, 0.20, 0.29);
  static const _green = PdfColor(0.05, 0.48, 0.24);
  static const _red = PdfColor(0.72, 0.08, 0.08);
  static const _amber = PdfColor(0.62, 0.42, 0.05);
  static const _line = PdfColor(0.55, 0.58, 0.60);

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

    final ncByAnswer = <String, NonConformity>{
      for (final item in ncs) item.answerId: item,
    };
    final actionsByAnswer = <String, List<ActionPlan>>{};
    for (final item in actions) {
      actionsByAnswer.putIfAbsent(item.answerId, () => <ActionPlan>[]).add(item);
    }

    final companies = await db.getCompanies(onlyActive: false);
    final companyId = _first([header['company_id']]);
    Company? companyRecord;
    for (final entry in companies) {
      if (entry.id == companyId) {
        companyRecord = entry;
        break;
      }
    }

    final company = _first([
      header['company_name'],
      companyRecord?.name,
      'Empresa',
    ]);
    final cnpj = _first([header['company_cnpj'], companyRecord?.cnpj]);
    final locality = [
      if ((companyRecord?.city ?? '').trim().isNotEmpty)
        companyRecord!.city!.trim(),
      if ((companyRecord?.uf ?? '').trim().isNotEmpty)
        companyRecord!.uf!.trim(),
    ].join('/');
    final fullAddress = _first([header['worksite_address']]);
    final issueLocation = _first([
      header['sector_name'],
      header['area'],
      header['worksite_name'],
    ]);
    final rawDate = DateTime.tryParse('${header['date'] ?? ''}');
    final dateText =
        rawDate == null ? '-' : DateFormat('dd/MM/yyyy').format(rawDate);
    final technician = _first([header['technician_name']]);
    final registration = _first([
      header['technician_registration'],
      header['professional_registration'],
    ]);
    final conclusion = _first([header['conclusion']]);

    final auditarLogo = await _asset('assets/branding/auditar_logo.jpg') ??
        await _asset('assets/branding/auditar_icon.png');

    // No lado direito aparece SOMENTE a logo cadastrada da empresa.
    // Se não houver logo, o espaço fica vazio. Não repetir a logo Auditar.
    final companyLogo = await ReportLogoService.forCompany(header);

    final techSignature =
        await _fileImage('${header['technician_signature_path'] ?? ''}');

    final issueData = <_IssueData>[];
    for (final answer in answers) {
      if (answer.status == 'Não se aplica' ||
          answer.status == 'N/A' ||
          answer.status == 'NSA' ||
          answer.status == 'Conforme') {
        continue;
      }
      final nc = ncByAnswer[answer.id];
      final linked = actionsByAnswer[answer.id] ?? const <ActionPlan>[];
      final photos = await db.getPhotosForAnswer(answer.id);
      final images = <pw.MemoryImage>[];
      for (final photo in photos.take(4)) {
        final image = await _fileImage(photo.path);
        if (image != null) images.add(image);
      }

      final situation = _first([
        nc?.description,
        answer.observation,
      ]);
      final risk = _first([
        nc?.riskIdentified,
        answer.riskIdentified,
      ]);
      final correction = _first([
        nc?.recommendation,
        answer.recommendation,
        if (linked.isNotEmpty) linked.first.correctiveAction,
      ]);
      final priority = _first([
        if (linked.isNotEmpty) linked.first.priority,
        nc?.classification,
      ]);

      // Itens conformes sem texto nem foto permanecem no checklist original,
      // mas não ocupam espaço no relatório fotográfico/técnico.
      if (answer.status == 'Conforme' &&
          situation.isEmpty &&
          correction.isEmpty &&
          images.isEmpty) {
        continue;
      }

      issueData.add(
        _IssueData(
          title: _first([
            answer.questionText,
            answer.questionCategory,
            nc?.description,
            'Item identificado',
          ]),
          caption: _first([answer.questionText, answer.questionCategory]),
          location: issueLocation,
          situation: situation,
          risk: risk,
          correction: correction,
          priority: priority,
          reference: answer.questionReference.trim(),
          status: answer.status.trim(),
          photos: images,
        ),
      );
    }

    final references = <String>[];
    for (final issue in issueData) {
      final value = issue.reference.trim();
      if (value.isEmpty) continue;
      if (!references.any((item) => item.toLowerCase() == value.toLowerCase())) {
        references.add(value);
      }
    }

    final doc = pw.Document(
      title: 'Relatório de Vistoria Técnica - $company',
      subject: 'Padrão Auditar 3',
      author: 'Auditar Soluções',
    );

    final widgets = <pw.Widget>[
      _identityBox(
        company: company,
        cnpj: cnpj,
        locality: locality,
        dateText: dateText,
        fullAddress: fullAddress,
      ),
      pw.SizedBox(height: 10),
    ];

    if (issueData.isEmpty) {
      widgets.add(
        pw.Container(
          padding: const pw.EdgeInsets.all(14),
          decoration: pw.BoxDecoration(
            border: pw.Border.all(color: _line, width: .6),
          ),
          child: pw.Text(
            'Nenhum item com descrição ou evidência fotográfica foi registrado para este relatório.',
            style: pw.TextStyle(fontSize: 9),
          ),
        ),
      );
    } else {
      for (var index = 0; index < issueData.length; index++) {
        widgets.add(_issueBlock(issueData[index], index + 1));
      }
    }

    widgets.addAll([
      pw.SizedBox(height: 14),
      pw.Text(
        'CONCLUSÃO',
        style: pw.TextStyle(
          color: _navy,
          fontWeight: pw.FontWeight.bold,
          fontSize: 12,
        ),
      ),
      pw.SizedBox(height: 6),
      pw.Text(
        conclusion.isNotEmpty
            ? conclusion
            : 'Priorizar as correções descritas nos itens identificados, acompanhando a execução das medidas recomendadas. '
                'Verificar as correções em nova visita.',
        textAlign: pw.TextAlign.justify,
        style: const pw.TextStyle(fontSize: 9, lineSpacing: 2),
      ),
      pw.SizedBox(height: 7),
      pw.Text(
        'Relatório elaborado com os registros fotográficos e as informações registradas na vistoria. '
        'Não confirma regularização posterior.',
        textAlign: pw.TextAlign.justify,
        style: const pw.TextStyle(fontSize: 7.7, lineSpacing: 1.6),
      ),
      if (references.isNotEmpty) ...[
        pw.SizedBox(height: 6),
        pw.RichText(
          text: pw.TextSpan(
            children: [
              pw.TextSpan(
                text: 'Referências gerais: ',
                style: pw.TextStyle(
                  fontSize: 7.7,
                  fontWeight: pw.FontWeight.bold,
                ),
              ),
              pw.TextSpan(
                text: references.join('; '),
                style: const pw.TextStyle(fontSize: 7.7),
              ),
            ],
          ),
        ),
      ],
      pw.SizedBox(height: 34),
      _technicalResponsible(
        name: technician,
        registration: registration,
        signature: techSignature,
      ),
      pw.SizedBox(height: 8),
    ]);

    doc.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        maxPages: 400,
        margin: const pw.EdgeInsets.fromLTRB(22, 18, 22, 34),
        header: (context) => _header(
          auditarLogo: auditarLogo,
          companyLogo: companyLogo,
          company: company,
          cnpj: cnpj,
          dateText: dateText,
        ),
        footer: (context) => _footer(context, auditarLogo),
        build: (_) => widgets,
      ),
    );

    return doc.save();
  }

  static pw.Widget _header({
    required pw.MemoryImage? auditarLogo,
    required pw.MemoryImage? companyLogo,
    required String company,
    required String cnpj,
    required String dateText,
  }) =>
      pw.Column(
        children: [
          pw.Row(
            crossAxisAlignment: pw.CrossAxisAlignment.center,
            children: [
              _logo(auditarLogo, 72, 47),
              pw.Expanded(
                child: pw.Column(
                  children: [
                    pw.Text(
                      'RELATÓRIO DE VISTORIA TÉCNICA',
                      textAlign: pw.TextAlign.center,
                      style: pw.TextStyle(
                        color: _navy,
                        fontSize: 12,
                        fontWeight: pw.FontWeight.bold,
                      ),
                    ),
                    pw.SizedBox(height: 2),
                    pw.Text(
                      company.toUpperCase(),
                      textAlign: pw.TextAlign.center,
                      style: pw.TextStyle(
                        color: _navy,
                        fontSize: 11,
                        fontWeight: pw.FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
              _logo(companyLogo, 70, 50),
            ],
          ),
          pw.SizedBox(height: 6),
          pw.Text(
            [
              company.toUpperCase(),
              if (cnpj.isNotEmpty) 'CNPJ: $cnpj',
            ].join('  |  '),
            textAlign: pw.TextAlign.center,
            style: pw.TextStyle(
              fontSize: 7.4,
              fontWeight: pw.FontWeight.bold,
            ),
          ),
          pw.SizedBox(height: 7),
          pw.Container(height: .6, color: _line),
          pw.SizedBox(height: 8),
        ],
      );

  static pw.Widget _identityBox({
    required String company,
    required String cnpj,
    required String locality,
    required String dateText,
    required String fullAddress,
  }) =>
      pw.Container(
        decoration: pw.BoxDecoration(
          border: pw.Border.all(color: _line, width: .6),
        ),
        padding: const pw.EdgeInsets.all(8),
        child: pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            pw.Text(
              'IDENTIFICAÇÃO DA EMPRESA',
              style: pw.TextStyle(
                color: _navy,
                fontSize: 9,
                fontWeight: pw.FontWeight.bold,
              ),
            ),
            pw.SizedBox(height: 6),
            pw.Row(
              children: [
                pw.Expanded(child: _labelValue('RAZÃO SOCIAL', company)),
                pw.SizedBox(width: 10),
                pw.Expanded(child: _labelValue('CNPJ', cnpj)),
              ],
            ),
            pw.SizedBox(height: 4),
            pw.Row(
              children: [
                pw.Expanded(child: _labelValue('LOCALIDADE', locality)),
                pw.SizedBox(width: 10),
                pw.Expanded(child: _labelValue('DATA DA VISTORIA', dateText)),
              ],
            ),
            pw.SizedBox(height: 4),
            _labelValue('ENDEREÇO COMPLETO', fullAddress),
          ],
        ),
      );

  static pw.Widget _issueBlock(_IssueData issue, int number) {
    final statusColor = _statusColor(issue.status);
    return pw.Container(
      constraints: const pw.BoxConstraints(minHeight: 205),
      margin: const pw.EdgeInsets.only(bottom: 0),
      decoration: pw.BoxDecoration(
        border: pw.Border.all(color: _line, width: .55),
      ),
      child: pw.Row(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: [
          pw.Expanded(
            flex: 49,
            child: pw.Container(
              padding: const pw.EdgeInsets.all(8),
              decoration: const pw.BoxDecoration(
                border: pw.Border(
                  right: pw.BorderSide(color: _line, width: .55),
                ),
              ),
              child: _evidence(issue),
            ),
          ),
          pw.Expanded(
            flex: 51,
            child: pw.Padding(
              padding: const pw.EdgeInsets.all(9),
              child: pw.Column(
                crossAxisAlignment: pw.CrossAxisAlignment.start,
                children: [
                  pw.Text(
                    '${number.toString().padLeft(2, '0')}. ${issue.title.toUpperCase()}',
                    style: pw.TextStyle(
                      color: _navy,
                      fontSize: 9.5,
                      fontWeight: pw.FontWeight.bold,
                    ),
                  ),
                  pw.SizedBox(height: 7),
                  _paragraph(
                    'Local',
                    issue.location.isEmpty ? 'Não informado' : issue.location,
                  ),
                  if (issue.situation.isNotEmpty)
                    _paragraph('Situação', issue.situation),
                  if (issue.risk.isNotEmpty)
                    _paragraph('Risco', issue.risk),
                  if (issue.correction.isNotEmpty)
                    _paragraph('Correção', issue.correction),
                  pw.SizedBox(height: 5),
                  if (issue.priority.isNotEmpty)
                    pw.Text(
                      'PRIORIDADE: ${issue.priority.toUpperCase()}',
                      style: pw.TextStyle(
                        color: _priorityColor(issue.priority),
                        fontSize: 8.2,
                        fontWeight: pw.FontWeight.bold,
                      ),
                    ),
                  if (issue.priority.isEmpty)
                    pw.Text(
                      'STATUS: ${issue.status.isEmpty ? 'REGISTRADO' : issue.status.toUpperCase()}',
                      style: pw.TextStyle(
                        color: statusColor,
                        fontSize: 8.2,
                        fontWeight: pw.FontWeight.bold,
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

  static pw.Widget _evidence(_IssueData issue) {
    if (issue.photos.isEmpty) {
      return pw.Column(
        mainAxisAlignment: pw.MainAxisAlignment.center,
        children: [
          pw.Container(
            height: 125,
            alignment: pw.Alignment.center,
            decoration: pw.BoxDecoration(
              color: PdfColors.grey100,
              border: pw.Border.all(color: PdfColors.grey300),
            ),
            child: pw.Text(
              'Sem fotografia associada',
              style: pw.TextStyle(fontSize: 8, color: PdfColors.grey600),
            ),
          ),
          if (issue.caption.isNotEmpty) ...[
            pw.SizedBox(height: 5),
            pw.Text(
              issue.caption,
              textAlign: pw.TextAlign.center,
              style: const pw.TextStyle(
                fontSize: 6.6,
                color: PdfColors.grey700,
              ),
            ),
          ],
        ],
      );
    }

    final photos = issue.photos.take(3).toList();
    return pw.Column(
      mainAxisAlignment: pw.MainAxisAlignment.center,
      children: [
        if (photos.length == 1)
          pw.SizedBox(
            height: 150,
            child: pw.Image(photos.first, fit: pw.BoxFit.contain),
          )
        else ...[
          pw.SizedBox(
            height: 102,
            child: pw.Image(photos.first, fit: pw.BoxFit.contain),
          ),
          pw.SizedBox(height: 5),
          pw.Row(
            children: [
              for (var i = 1; i < photos.length; i++) ...[
                if (i > 1) pw.SizedBox(width: 5),
                pw.Expanded(
                  child: pw.SizedBox(
                    height: 70,
                    child: pw.Image(photos[i], fit: pw.BoxFit.contain),
                  ),
                ),
              ],
            ],
          ),
        ],
        if (issue.caption.isNotEmpty) ...[
          pw.SizedBox(height: 5),
          pw.Text(
            issue.caption,
            textAlign: pw.TextAlign.center,
            style: const pw.TextStyle(
              fontSize: 6.6,
              color: PdfColors.grey700,
            ),
          ),
        ],
      ],
    );
  }

  static pw.Widget _paragraph(String label, String value) => pw.Padding(
        padding: const pw.EdgeInsets.only(bottom: 5),
        child: pw.RichText(
          text: pw.TextSpan(
            children: [
              pw.TextSpan(
                text: '$label: ',
                style: pw.TextStyle(
                  fontSize: 8.1,
                  fontWeight: pw.FontWeight.bold,
                ),
              ),
              pw.TextSpan(
                text: value,
                style: const pw.TextStyle(fontSize: 8.1, lineSpacing: 1.7),
              ),
            ],
          ),
        ),
      );

  static pw.Widget _technicalResponsible({
    required String name,
    required String registration,
    required pw.MemoryImage? signature,
  }) =>
      pw.Center(
        child: pw.SizedBox(
          width: 240,
          child: pw.Column(
            children: [
              pw.SizedBox(
                height: 42,
                child: signature == null
                    ? pw.SizedBox()
                    : pw.Image(signature, fit: pw.BoxFit.contain),
              ),
              pw.Container(height: .7, color: _navy),
              pw.SizedBox(height: 5),
              pw.Text(
                'TÉCNICO EM SEGURANÇA DO TRABALHO',
                style: pw.TextStyle(
                  fontSize: 8,
                  fontWeight: pw.FontWeight.bold,
                ),
              ),
              pw.Text(
                [name, registration].where((e) => e.trim().isNotEmpty).join(' • ').isEmpty
                    ? 'Nome e registro profissional'
                    : [name, registration]
                        .where((e) => e.trim().isNotEmpty)
                        .join(' • '),
                style: const pw.TextStyle(fontSize: 7.4),
                textAlign: pw.TextAlign.center,
              ),
            ],
          ),
        ),
      );

  static pw.Widget _footer(
    pw.Context context,
    pw.MemoryImage? auditarLogo,
  ) =>
      pw.Row(
        crossAxisAlignment: pw.CrossAxisAlignment.end,
        children: [
          pw.Expanded(child: pw.SizedBox()),
          _logo(auditarLogo, 64, 26),
          pw.Expanded(
            child: pw.Align(
              alignment: pw.Alignment.centerRight,
              child: pw.Text(
                'Página ${context.pageNumber}/${context.pagesCount}',
                style: const pw.TextStyle(
                  fontSize: 6.8,
                  color: PdfColors.grey700,
                ),
              ),
            ),
          ),
        ],
      );

  static pw.Widget _logo(
    pw.MemoryImage? image,
    double width,
    double height,
  ) =>
      pw.SizedBox(
        width: width,
        height: height,
        child: image == null
            ? pw.SizedBox()
            : pw.Image(image, fit: pw.BoxFit.contain),
      );

  static pw.Widget _labelValue(String label, String value) => pw.RichText(
        text: pw.TextSpan(
          children: [
            pw.TextSpan(
              text: '$label: ',
              style: pw.TextStyle(
                fontSize: 7.4,
                fontWeight: pw.FontWeight.bold,
              ),
            ),
            pw.TextSpan(
              text: value.isEmpty ? 'Não informado' : value,
              style: const pw.TextStyle(fontSize: 7.4),
            ),
          ],
        ),
      );

  static PdfColor _priorityColor(String value) {
    final priority = value.toLowerCase();
    if (priority.contains('imediat') ||
        priority.contains('crític') ||
        priority.contains('critic')) {
      return _red;
    }
    if (priority.contains('alta')) return _amber;
    if (priority.contains('média') ||
        priority.contains('media')) {
      return _amber;
    }
    return _navy;
  }

  static PdfColor _statusColor(String value) {
    final status = value.toLowerCase();
    if (status.contains('não conforme') || status.contains('nao conforme')) {
      return _red;
    }
    if (status.contains('parcial')) return _amber;
    if (status.contains('conforme')) return _green;
    return _navy;
  }

  static String _first(List<Object?> values) {
    for (final raw in values) {
      final value = '${raw ?? ''}'.trim();
      if (value.isNotEmpty && value.toLowerCase() != 'null') return value;
    }
    return '';
  }

  static Future<pw.MemoryImage?> _asset(String path) async {
    try {
      final data = await rootBundle.load(path);
      return pw.MemoryImage(data.buffer.asUint8List());
    } catch (_) {
      return null;
    }
  }

  static Future<pw.MemoryImage?> _fileImage(String path) async {
    if (path.trim().isEmpty) return null;
    try {
      final file = File(path);
      if (!await file.exists() || await file.length() == 0) return null;
      return pw.MemoryImage(await file.readAsBytes());
    } catch (_) {
      return null;
    }
  }
}

class _IssueData {
  final String title;
  final String caption;
  final String location;
  final String situation;
  final String risk;
  final String correction;
  final String priority;
  final String reference;
  final String status;
  final List<pw.MemoryImage> photos;

  const _IssueData({
    required this.title,
    required this.caption,
    required this.location,
    required this.situation,
    required this.risk,
    required this.correction,
    required this.priority,
    required this.reference,
    required this.status,
    required this.photos,
  });
}

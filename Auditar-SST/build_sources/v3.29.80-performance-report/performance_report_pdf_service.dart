import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/services.dart' show rootBundle;
import 'package:intl/intl.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import '../database.dart';
import '../models.dart';
import 'report_template_service.dart';

class PerformanceReportPdfService {
  static const PdfColor _blue = PdfColor(0.08, 0.31, 0.46);
  static const PdfColor _green = PdfColor(0.02, 0.55, 0.22);
  static const PdfColor _orange = PdfColor(0.85, 0.43, 0.03);
  static const PdfColor _red = PdfColor(0.74, 0.08, 0.08);
  static const PdfColor _grey = PdfColor(0.42, 0.42, 0.42);
  static const PdfColor _border = PdfColor(0.43, 0.43, 0.43);

  static Future<Uint8List> generateInspectionPdf(
    String inspectionId, {
    required Map<String, Object?> header,
    required ReportTemplateDefinition template,
    bool executive = false,
    bool? includeActionPlan,
  }) async {
    final db = AppDatabase.instance;
    final answers = await db.getAnswers(inspectionId);
    final actions = await db.getActionsForInspection(inspectionId);
    final ncs = await db.getNonConformitiesForInspection(inspectionId);

    final ncByAnswer = <String, NonConformity>{
      for (final nc in ncs) nc.answerId: nc,
    };
    final actionsByAnswer = <String, List<ActionPlan>>{};
    for (final action in actions) {
      actionsByAnswer
          .putIfAbsent(action.answerId, () => <ActionPlan>[])
          .add(action);
    }

    final issueAnswers = answers
        .where((e) => e.status == 'Não Conforme' || e.status == 'Parcial')
        .toList();

    final issues = <_PerformanceIssue>[];
    for (final answer in issueAnswers) {
      pw.MemoryImage? photo;
      final photos = await db.getPhotosForAnswer(answer.id);
      if (photos.isNotEmpty) {
        photo = await _fileImage(photos.first.path);
      }
      issues.add(
        _PerformanceIssue(
          answer: answer,
          nc: ncByAnswer[answer.id],
          action: (actionsByAnswer[answer.id] ?? const <ActionPlan>[])
              .firstOrNull,
          photo: photo,
        ),
      );
    }

    final company = _firstNonEmpty([
      header['company_name'],
      header['company'],
      '-',
    ]);
    final worksite = _firstNonEmpty([
      header['worksite_name'],
      header['unit_name'],
      header['site_name'],
      company,
    ]);
    final location = _firstNonEmpty([
      header['location'],
      header['city'],
      header['city_state'],
      header['sector_name'],
      header['area'],
      company,
    ]);

    final rawDate = DateTime.tryParse('${header['date'] ?? ''}');
    final dateText =
        rawDate == null ? '-' : DateFormat('dd/MM/yyyy').format(rawDate);

    final companyLogo = await _fileImage(
      '${header['company_logo_path'] ?? ''}',
    );
    final auditarLogo = await _assetImage('assets/branding/auditar_icon.png');
    final techSignature = await _fileImage(
      '${header['technician_signature_path'] ?? ''}',
    );

    final customConclusion = '${header['conclusion'] ?? ''}'.trim();
    final hasImmediate = issues.any(
      (item) => _isImmediate(_priorityFor(item)),
    );
    final conclusion = customConclusion.isNotEmpty
        ? customConclusion
        : _defaultConclusion(hasImmediate);

    final doc = pw.Document(
      title: template.headerTitle,
      author: 'Auditar SST',
      subject: 'Relatório de vistoria de segurança do trabalho',
    );

    final body = <pw.Widget>[];
    if (issues.isEmpty) {
      body.add(
        pw.Container(
          width: double.infinity,
          padding: const pw.EdgeInsets.all(16),
          decoration: pw.BoxDecoration(
            border: pw.Border.all(color: _border, width: .6),
          ),
          child: pw.Text(
            'Nenhuma não conformidade ou situação parcial foi registrada nesta vistoria.',
            style: const pw.TextStyle(fontSize: 10),
          ),
        ),
      );
    } else {
      for (final issue in issues) {
        body.add(_issueRow(issue));
        body.add(pw.SizedBox(height: 6));
      }
    }

    body.addAll([
      pw.SizedBox(height: 4),
      pw.Text(
        'CONCLUSÃO',
        style: pw.TextStyle(
          fontSize: 12.5,
          fontWeight: pw.FontWeight.bold,
          color: _blue,
        ),
      ),
      pw.SizedBox(height: 6),
      pw.Text(
        conclusion,
        style: const pw.TextStyle(
          fontSize: 9.3,
          lineSpacing: 1.9,
        ),
        textAlign: pw.TextAlign.justify,
      ),
      pw.SizedBox(height: 24),
      _technicalSignature(
        header: header,
        image: techSignature,
        signatureStyle: template.signatureStyle,
      ),
      pw.SizedBox(height: 6),
    ]);

    doc.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.fromLTRB(14, 16, 14, 28),
        header: (_) => _header(
          template: template,
          companyLogo: companyLogo,
          company: company,
          worksite: worksite,
          dateText: dateText,
          location: location,
        ),
        footer: (_) => _footer(auditarLogo),
        build: (_) => body,
      ),
    );

    return doc.save();
  }

  static pw.Widget _header({
    required ReportTemplateDefinition template,
    required pw.MemoryImage? companyLogo,
    required String company,
    required String worksite,
    required String dateText,
    required String location,
  }) {
    final titleLine = template.headerTitle.trim().isEmpty
        ? 'RELATÓRIO PERFORMANCE'
        : template.headerTitle.trim().toUpperCase();
    final secondLine =
        worksite.trim().isEmpty ? company.toUpperCase() : worksite.toUpperCase();

    return pw.Container(
      margin: const pw.EdgeInsets.only(bottom: 8),
      child: pw.Column(
        children: [
          pw.Row(
            crossAxisAlignment: pw.CrossAxisAlignment.center,
            children: [
              pw.SizedBox(
                width: 92,
                height: 52,
                child: companyLogo != null
                    ? pw.Image(companyLogo, fit: pw.BoxFit.contain)
                    : pw.Column(
                        mainAxisAlignment: pw.MainAxisAlignment.center,
                        children: [
                          pw.Text(
                            company.toUpperCase(),
                            maxLines: 2,
                            textAlign: pw.TextAlign.center,
                            style: pw.TextStyle(
                              fontSize: 7,
                              fontWeight: pw.FontWeight.bold,
                              color: _grey,
                            ),
                          ),
                        ],
                      ),
              ),
              pw.Expanded(
                child: pw.Column(
                  children: [
                    pw.Text(
                      titleLine,
                      textAlign: pw.TextAlign.center,
                      style: pw.TextStyle(
                        fontSize: 12.5,
                        fontWeight: pw.FontWeight.bold,
                        color: _blue,
                      ),
                    ),
                    pw.SizedBox(height: 1),
                    pw.Text(
                      secondLine,
                      maxLines: 2,
                      textAlign: pw.TextAlign.center,
                      style: pw.TextStyle(
                        fontSize: 11.2,
                        fontWeight: pw.FontWeight.bold,
                        color: _blue,
                      ),
                    ),
                  ],
                ),
              ),
              pw.SizedBox(
                width: 92,
                height: 58,
                child: pw.Center(child: _sstBadge()),
              ),
            ],
          ),
          pw.SizedBox(height: 6),
          pw.Text(
            'Vistoria realizada em $dateText  |  $location',
            style: pw.TextStyle(
              fontSize: 7.8,
              fontWeight: pw.FontWeight.bold,
            ),
            textAlign: pw.TextAlign.center,
          ),
          pw.SizedBox(height: 7),
        ],
      ),
    );
  }

  static pw.Widget _sstBadge() {
    return pw.Container(
      width: 50,
      height: 50,
      decoration: pw.BoxDecoration(
        shape: pw.BoxShape.circle,
        color: _green,
        border: pw.Border.all(color: _green, width: 1.2),
      ),
      child: pw.Stack(
        alignment: pw.Alignment.center,
        children: [
          pw.Container(
            width: 42,
            height: 42,
            decoration: pw.BoxDecoration(
              shape: pw.BoxShape.circle,
              border: pw.Border.all(color: PdfColors.white, width: 1.2),
            ),
          ),
          pw.Column(
            mainAxisAlignment: pw.MainAxisAlignment.center,
            children: [
              pw.Text(
                '+',
                style: pw.TextStyle(
                  color: PdfColors.white,
                  fontSize: 24,
                  fontWeight: pw.FontWeight.bold,
                ),
              ),
              pw.Text(
                'SST',
                style: pw.TextStyle(
                  color: PdfColors.white,
                  fontSize: 6.5,
                  fontWeight: pw.FontWeight.bold,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  static pw.Widget _issueRow(_PerformanceIssue issue) {
    final problem = _problemFor(issue);
    final risk = _riskFor(issue);
    final correction = _correctionFor(issue);
    final priority = _priorityFor(issue);
    final title = issue.answer.questionText.trim().isEmpty
        ? 'SITUAÇÃO IDENTIFICADA'
        : issue.answer.questionText.trim().toUpperCase();
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
              constraints: const pw.BoxConstraints(minHeight: 166),
              child: pw.Column(
                mainAxisAlignment: pw.MainAxisAlignment.center,
                children: [
                  pw.Container(
                    width: double.infinity,
                    height: 142,
                    color: PdfColors.grey100,
                    child: issue.photo != null
                        ? pw.Image(issue.photo!, fit: pw.BoxFit.cover)
                        : pw.Center(
                            child: pw.Column(
                              mainAxisAlignment: pw.MainAxisAlignment.center,
                              children: [
                                pw.Text(
                                  'SEM FOTO',
                                  style: pw.TextStyle(
                                    color: PdfColors.grey500,
                                    fontSize: 9,
                                    fontWeight: pw.FontWeight.bold,
                                  ),
                                ),
                                pw.SizedBox(height: 2),
                                pw.Text(
                                  'Evidência não anexada',
                                  style: const pw.TextStyle(
                                    color: PdfColors.grey500,
                                    fontSize: 6.5,
                                  ),
                                ),
                              ],
                            ),
                          ),
                  ),
                  pw.SizedBox(height: 5),
                  pw.Text(
                    _captionFor(issue.answer),
                    maxLines: 2,
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
              constraints: const pw.BoxConstraints(minHeight: 166),
              child: pw.Column(
                crossAxisAlignment: pw.CrossAxisAlignment.start,
                mainAxisAlignment: pw.MainAxisAlignment.center,
                children: [
                  pw.Text(
                    title,
                    style: pw.TextStyle(
                      fontSize: 10.3,
                      fontWeight: pw.FontWeight.bold,
                      color: _blue,
                    ),
                  ),
                  pw.SizedBox(height: 7),
                  _technicalLine('Situação', problem),
                  _technicalLine('Risco', risk),
                  _technicalLine('Correção', correction),
                  if (fine.isNotEmpty)
                    _technicalLine(
                      'Multa (referência)',
                      fine,
                      labelColor: _orange,
                    ),
                  pw.SizedBox(height: 3),
                  pw.RichText(
                    text: pw.TextSpan(
                      children: [
                        pw.TextSpan(
                          text: 'PRIORIDADE: ',
                          style: pw.TextStyle(
                            fontSize: 8.2,
                            fontWeight: pw.FontWeight.bold,
                            color: _priorityColor(priority),
                          ),
                        ),
                        pw.TextSpan(
                          text: priority.toUpperCase(),
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
            ),
          ],
        ),
      ],
    );
  }

  static pw.Widget _technicalLine(
    String label,
    String value, {
    PdfColor? labelColor,
  }) {
    return pw.Padding(
      padding: const pw.EdgeInsets.only(bottom: 3),
      child: pw.RichText(
        text: pw.TextSpan(
          children: [
            pw.TextSpan(
              text: '$label: ',
              style: pw.TextStyle(
                fontSize: 7.8,
                fontWeight: pw.FontWeight.bold,
                color: labelColor ?? PdfColors.black,
              ),
            ),
            pw.TextSpan(
              text: value.trim().isEmpty ? '-' : value.trim(),
              style: const pw.TextStyle(
                fontSize: 7.8,
                color: PdfColors.black,
              ),
            ),
          ],
        ),
      ),
    );
  }

  static pw.Widget _technicalSignature({
    required Map<String, Object?> header,
    required pw.MemoryImage? image,
    required String signatureStyle,
  }) {
    final name = _firstNonEmpty([
      header['technician_name'],
      'Nome e registro profissional',
    ]);
    final registration = _firstNonEmpty([
      header['technician_registration'],
      header['professional_registration'],
      header['technician_registry'],
      '',
    ]);

    return pw.Center(
      child: pw.SizedBox(
        width: 260,
        child: pw.Column(
          children: [
            if (signatureStyle == 'app' && image != null)
              pw.SizedBox(
                height: 42,
                child: pw.Image(image, fit: pw.BoxFit.contain),
              )
            else
              pw.SizedBox(height: 30),
            pw.Container(height: .7, color: PdfColors.grey700),
            pw.SizedBox(height: 4),
            pw.Text(
              'RESPONSÁVEL TÉCNICO',
              style: pw.TextStyle(
                fontSize: 8.2,
                fontWeight: pw.FontWeight.bold,
              ),
            ),
            pw.Text(
              registration.isEmpty ? name : '$name - $registration',
              textAlign: pw.TextAlign.center,
              style: const pw.TextStyle(fontSize: 7.3),
            ),
          ],
        ),
      ),
    );
  }

  static pw.Widget _footer(pw.MemoryImage? auditarLogo) {
    return pw.Container(
      height: 28,
      alignment: pw.Alignment.center,
      child: auditarLogo == null
          ? pw.Text(
              'Auditar Soluções',
              style: pw.TextStyle(
                color: _green,
                fontSize: 7,
                fontWeight: pw.FontWeight.bold,
              ),
            )
          : pw.Image(auditarLogo, height: 24, fit: pw.BoxFit.contain),
    );
  }

  static String _problemFor(_PerformanceIssue issue) {
    final answer = issue.answer;
    if (answer.observation.trim().isNotEmpty) {
      return answer.observation.trim();
    }
    if (issue.nc?.description.trim().isNotEmpty == true) {
      return issue.nc!.description.trim();
    }
    return 'Situação observada durante a vistoria.';
  }

  static String _riskFor(_PerformanceIssue issue) {
    final answer = issue.answer;
    if (answer.riskIdentified.trim().isNotEmpty) {
      return answer.riskIdentified.trim();
    }
    if (issue.nc?.riskIdentified.trim().isNotEmpty == true) {
      return issue.nc!.riskIdentified.trim();
    }
    return 'Avaliar os riscos associados à condição identificada.';
  }

  static String _correctionFor(_PerformanceIssue issue) {
    final answer = issue.answer;
    if (answer.recommendation.trim().isNotEmpty) {
      return answer.recommendation.trim();
    }
    if (issue.nc?.recommendation.trim().isNotEmpty == true) {
      return issue.nc!.recommendation.trim();
    }
    if (issue.action?.correctiveAction.trim().isNotEmpty == true) {
      return issue.action!.correctiveAction.trim();
    }
    return 'Providenciar a correção da condição identificada.';
  }

  static String _priorityFor(_PerformanceIssue issue) {
    if (issue.action?.priority.trim().isNotEmpty == true) {
      return issue.action!.priority.trim();
    }
    if (issue.nc?.classification.trim().isNotEmpty == true) {
      return issue.nc!.classification.trim();
    }
    return 'Média';
  }

  static bool _isImmediate(String value) {
    final normalized = value.toLowerCase();
    return normalized.contains('imedi') ||
        normalized.contains('crít') ||
        normalized.contains('crit') ||
        normalized.contains('grave');
  }

  static PdfColor _priorityColor(String value) {
    final normalized = value.toLowerCase();
    if (_isImmediate(value)) return _red;
    if (normalized.contains('alta')) return _orange;
    if (normalized.contains('baixa')) return _green;
    return _blue;
  }

  static String _captionFor(InspectionAnswer answer) {
    var source = answer.observation.trim();
    if (source.isEmpty) source = answer.questionText.trim();
    if (source.isEmpty) return 'Registro fotográfico da vistoria.';
    source = source.replaceAll(RegExp(r'\s+'), ' ');
    final firstSentence = source.split(RegExp(r'(?<=[.!?])\s+')).first.trim();
    var caption = firstSentence;
    if (caption.length > 90) {
      caption = '${caption.substring(0, 87).trim()}...';
    }
    if (!RegExp(r'[.!?]$').hasMatch(caption)) {
      caption = '$caption.';
    }
    return caption;
  }

  static String _defaultConclusion(bool hasImmediate) {
    final first = hasImmediate
        ? 'Os itens classificados com prioridade imediata devem ser corrigidos antes da retomada das atividades relacionadas. '
        : '';
    return '${first}Os demais itens devem ser programados, corrigidos e posteriormente verificados em nova visita. '
        'Este relatório registra as condições encontradas na data da vistoria e não representa confirmação de regularização posterior.';
  }

  static String _fineForReport(InspectionAnswer answer) {
    final raw = answer.occurrencesJson.trim();
    if (raw.isEmpty) return '';
    try {
      final decoded = jsonDecode(raw);
      if (decoded is! Map) return '';
      final fine = decoded['fine'];
      if (fine is! Map || fine['showInReport'] != true) return '';

      int? cents;
      final rawCents = fine['amountCents'];
      if (rawCents is num && rawCents > 0) {
        cents = rawCents.round();
      } else {
        var legacy = '${fine['amount'] ?? ''}'.trim();
        legacy = legacy.replaceAll('R\$', '').replaceAll(' ', '');
        if (legacy.contains(',')) {
          legacy = legacy.replaceAll('.', '').replaceAll(',', '.');
        }
        final value = double.tryParse(legacy);
        if (value != null && value > 0) {
          cents = (value * 100).round();
        }
      }
      if (cents == null) return '';

      final amount = NumberFormat.currency(
        locale: 'pt_BR',
        symbol: 'R\$',
        decimalDigits: 2,
      ).format(cents / 100);
      final basis = '${fine['basis'] ?? ''}'.trim();
      return basis.isEmpty ? amount : '$amount - $basis';
    } catch (_) {
      return '';
    }
  }

  static String _firstNonEmpty(List<Object?> values) {
    for (final value in values) {
      final text = '${value ?? ''}'.trim();
      if (text.isNotEmpty) return text;
    }
    return '';
  }

  static Future<pw.MemoryImage?> _assetImage(String asset) async {
    try {
      final data = await rootBundle.load(asset);
      return pw.MemoryImage(data.buffer.asUint8List());
    } catch (_) {
      return null;
    }
  }

  static Future<pw.MemoryImage?> _fileImage(String path) async {
    if (path.trim().isEmpty) return null;
    try {
      final file = File(path);
      if (!await file.exists()) return null;
      final bytes = await file.readAsBytes();
      if (bytes.isEmpty) return null;
      return pw.MemoryImage(bytes);
    } catch (_) {
      return null;
    }
  }
}

class _PerformanceIssue {
  final InspectionAnswer answer;
  final NonConformity? nc;
  final ActionPlan? action;
  final pw.MemoryImage? photo;

  const _PerformanceIssue({
    required this.answer,
    required this.nc,
    required this.action,
    required this.photo,
  });
}

extension _FirstOrNull<T> on List<T> {
  T? get firstOrNull => isEmpty ? null : first;
}

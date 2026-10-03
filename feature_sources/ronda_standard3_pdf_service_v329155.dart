import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/services.dart' show rootBundle;
import 'package:intl/intl.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import '../database.dart';
import '../models.dart';
import 'report_logo_service.dart';

/// Renderer exclusivo da Ronda para o Padrão Auditar 3.
///
/// A coleta, os registros e a IA permanecem intocados. Este serviço apenas
/// apresenta os dados já existentes no mesmo padrão visual aprovado para
/// a vistoria técnica.
class RondaStandard3PdfService {
  static const _navy = PdfColor(0.08, 0.20, 0.29);
  static const _green = PdfColor(0.05, 0.48, 0.24);
  static const _red = PdfColor(0.72, 0.08, 0.08);
  static const _amber = PdfColor(0.62, 0.42, 0.05);
  static const _line = PdfColor(0.56, 0.63, 0.68);

  static Future<Uint8List> generate({
    required Company company,
    required List<SstRecord> records,
    String conclusion = '',
  }) async {
    final sorted = [...records]..sort((a, b) => a.date.compareTo(b.date));

    // Usa o cadastro completo da empresa quando o objeto aberto na Ronda
    // estiver resumido. Somente leitura; não altera banco ou sincronização.
    final companies = await AppDatabase.instance.getCompanies(onlyActive: false);
    Company? registeredCompany;
    for (final item in companies) {
      if (item.id == company.id) {
        registeredCompany = item;
        break;
      }
    }

    final companyName = _first([
      registeredCompany?.name,
      company.name,
      'Empresa',
    ]);
    final cnpj = _first([
      registeredCompany?.cnpj,
      company.cnpj,
    ]);
    final locality = [
      if ((registeredCompany?.city ?? company.city ?? '').trim().isNotEmpty)
        (registeredCompany?.city ?? company.city)!.trim(),
      if ((registeredCompany?.uf ?? company.uf ?? '').trim().isNotEmpty)
        (registeredCompany?.uf ?? company.uf)!.trim(),
    ].join('/');
    final dateText = sorted.isEmpty
        ? DateFormat('dd/MM/yyyy').format(DateTime.now())
        : DateFormat('dd/MM/yyyy').format(sorted.first.date);
    final fullAddress = sorted.isEmpty
        ? ''
        : _first([
            sorted.first.payload['worksiteAddress'],
            sorted.first.payload['companyAddress'],
            sorted.first.payload['address'],
          ]);

    final auditarLogo = await _asset('assets/branding/auditar_logo.jpg') ??
        await _asset('assets/branding/auditar_icon.png');
    final companyLogo = await ReportLogoService.forCompany(<String, Object?>{
      'company_id': company.id,
      'company_logo_path': registeredCompany?.logoPath ?? company.logoPath,
    });

    final issues = <_RoundIssue>[];
    final references = <String>[];
    final seenRecordIds = <String>{};

    for (final record in sorted) {
      if (record.id.trim().isNotEmpty && !seenRecordIds.add(record.id.trim())) {
        continue;
      }
      final p = record.payload;
      final conformity = _isConformity(p);
      if (conformity) continue;

      final categories = _stringList(p['categories']);
      final title = _compactTitle(_publicText(_first([
        p['aiTitle'],
        p['title'],
        record.title,
        categories.isNotEmpty ? categories.join(' + ') : null,
        p['description'],
        'Não conformidade',
      ])));
      final situation = _publicText(_first([
        p['description'],
        p['aiDescription'],
        p['observation'],
        p['nonConformity'],
      ]));
      final risk = _first([
        p['risk'],
        p['riskIdentified'],
        p['possibleConsequence'],
      ]);
      final correction = _first([
        p['recommendation'],
        p['correctiveAction'],
        p['immediateAction'],
      ]);
      final priority = _first([
        p['priority'],
        record.priority,
      ]);
      final location = _first([
        p['location'],
        p['locationDetail'],
        p['sectorName'],
        p['area'],
      ]);

      final photos = <pw.MemoryImage>[];
      for (final key in const ['photoPath', 'photoPath2']) {
        final image = await _fileImage('${p[key] ?? ''}');
        if (image != null) photos.add(image);
      }

      for (final value in [
        ..._stringList(p['likelyReferences']),
        ..._stringList(p['references']),
      ]) {
        if (!references.any((e) => e.toLowerCase() == value.toLowerCase())) {
          references.add(value);
        }
      }

      issues.add(_RoundIssue(
        title: title,
        caption: _first([
          p['caption'],
          p['photoCaption'],
          _captionFromTitle(title),
        ]),
        location: location,
        situation: situation,
        risk: risk,
        correction: correction,
        priority: priority,
        photos: photos,
      ));
    }

    final compactReferences = _compactReferences(references);
    final compactConclusion = _compactConclusion(conclusion);

    final doc = pw.Document(
      title: 'Relatório de Vistoria Técnica - $companyName',
      subject: 'Padrão Auditar 3',
      author: 'Auditar Soluções',
    );

    final body = <pw.Widget>[
      _identityBox(
        company: companyName,
        cnpj: cnpj,
        locality: locality,
        fullAddress: fullAddress,
        dateText: dateText,
      ),
      pw.SizedBox(height: 10),
    ];

    if (issues.isEmpty) {
      body.add(
        pw.Container(
          padding: const pw.EdgeInsets.all(14),
          decoration: pw.BoxDecoration(
            border: pw.Border.all(color: _line, width: .6),
          ),
          child: pw.Text(
            'Nenhuma não conformidade com dados suficientes foi registrada para este relatório.',
            style: pw.TextStyle(fontSize: 9),
          ),
        ),
      );
    } else {
      for (var i = 0; i < issues.length; i++) {
        body.add(_issueBlock(issues[i], i + 1));
      }
    }

    body.addAll([
      pw.SizedBox(height: 14),
      pw.Text(
        'CONCLUSÃO',
        style: pw.TextStyle(
          color: _navy,
          fontWeight: pw.FontWeight.bold,
          fontSize: 11.5,
        ),
      ),
      pw.SizedBox(height: 6),
      pw.Text(
        compactConclusion.isNotEmpty
            ? compactConclusion
            : 'Priorizar as correções descritas nos itens identificados e verificar sua execução em acompanhamento posterior.',
        textAlign: pw.TextAlign.justify,
        style: const pw.TextStyle(fontSize: 8.8, lineSpacing: 1.9),
      ),
      pw.SizedBox(height: 7),
      pw.Text(
        'Relatório elaborado com os registros fotográficos e as informações registradas na vistoria. Não confirma regularização posterior.',
        textAlign: pw.TextAlign.justify,
        style: const pw.TextStyle(fontSize: 7.9, lineSpacing: 1.6),
      ),
      if (compactReferences.isNotEmpty) ...[
        pw.SizedBox(height: 6),
        pw.RichText(
          text: pw.TextSpan(children: [
            pw.TextSpan(
              text: 'Referências gerais: ',
              style: pw.TextStyle(fontSize: 7.9, fontWeight: pw.FontWeight.bold),
            ),
            pw.TextSpan(
              text: compactReferences.join('; '),
              style: const pw.TextStyle(fontSize: 7.9),
            ),
          ]),
        ),
      ],
      pw.SizedBox(height: 34),
      _technicalResponsible(),
      pw.SizedBox(height: 8),
    ]);

    doc.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        maxPages: 400,
        margin: const pw.EdgeInsets.fromLTRB(16, 16, 16, 34),
        header: (context) => _header(
          auditarLogo: auditarLogo,
          companyLogo: companyLogo,
          company: companyName,
          cnpj: cnpj,
        ),
        footer: (context) => _footer(context, auditarLogo),
        build: (_) => body,
      ),
    );

    return doc.save();
  }

  static bool _isConformity(Map<String, dynamic> p) {
    final kind = _first([p['observationKind'], p['findingType']]).toLowerCase();
    return kind.contains('conformidade') && !kind.contains('não') && !kind.contains('nao');
  }

  static pw.Widget _header({
    required pw.MemoryImage? auditarLogo,
    required pw.MemoryImage? companyLogo,
    required String company,
    required String cnpj,
  }) =>
      pw.Column(children: [
        pw.Row(
          crossAxisAlignment: pw.CrossAxisAlignment.center,
          children: [
            pw.Container(
              width: 118,
              alignment: pw.Alignment.centerLeft,
              child: _auditarBrand(auditarLogo, 112, 58),
            ),
            pw.Expanded(
              child: pw.Column(children: [
                pw.Text(
                  'RELATÓRIO DE VISTORIA TÉCNICA',
                  textAlign: pw.TextAlign.center,
                  style: pw.TextStyle(
                    color: _navy,
                    fontSize: 13.2,
                    fontWeight: pw.FontWeight.bold,
                  ),
                ),
                pw.SizedBox(height: 2),
                pw.Text(
                  company.toUpperCase(),
                  textAlign: pw.TextAlign.center,
                  style: pw.TextStyle(
                    color: _navy,
                    fontSize: 11.4,
                    fontWeight: pw.FontWeight.bold,
                  ),
                ),
              ]),
            ),
            pw.Container(
              width: 118,
              alignment: pw.Alignment.centerRight,
              child: _logo(companyLogo, 82, 58),
            ),
          ],
        ),
        pw.SizedBox(height: 5),
        if (cnpj.isNotEmpty)
          pw.Text(
            '${company.toUpperCase()}  |  CNPJ: $cnpj',
            textAlign: pw.TextAlign.center,
            style: pw.TextStyle(fontSize: 8.2, fontWeight: pw.FontWeight.bold),
          ),
        pw.SizedBox(height: cnpj.isNotEmpty ? 8 : 4),
        pw.Container(height: .6, color: _line),
        pw.SizedBox(height: 8),
      ]);

  static pw.Widget _identityBox({
    required String company,
    required String cnpj,
    required String locality,
    required String fullAddress,
    required String dateText,
  }) =>
      pw.Container(
        decoration: pw.BoxDecoration(
          border: pw.Border.all(color: _line, width: .6),
        ),
        padding: const pw.EdgeInsets.all(10),
        child: pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            pw.Text(
              'IDENTIFICAÇÃO DA EMPRESA',
              style: pw.TextStyle(
                color: _navy,
                fontSize: 9.8,
                fontWeight: pw.FontWeight.bold,
              ),
            ),
            pw.SizedBox(height: 6),
            pw.Row(children: [
              pw.Expanded(child: _labelValue('RAZÃO SOCIAL', company)),
              pw.SizedBox(width: 10),
              pw.Expanded(child: _labelValue('CNPJ', cnpj)),
            ]),
            pw.SizedBox(height: 4),
            pw.Row(children: [
              pw.Expanded(child: _labelValue('LOCALIDADE', locality)),
              pw.SizedBox(width: 10),
              pw.Expanded(child: _labelValue('DATA DA VISTORIA', dateText)),
            ]),
            pw.SizedBox(height: 4),
            _labelValue('ENDEREÇO COMPLETO', fullAddress),
          ],
        ),
      );

  static pw.Widget _issueBlock(_RoundIssue issue, int number) {
    return pw.Container(
      constraints: const pw.BoxConstraints(minHeight: 218),
      decoration: pw.BoxDecoration(
        border: pw.Border.all(color: _line, width: .55),
      ),
      child: pw.Row(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: [
          pw.Expanded(
            flex: 48,
            child: pw.Container(
              padding: const pw.EdgeInsets.fromLTRB(11, 10, 11, 9),
              decoration: const pw.BoxDecoration(
                border: pw.Border(
                  right: pw.BorderSide(color: _line, width: .55),
                ),
              ),
              child: _evidence(issue),
            ),
          ),
          pw.Expanded(
            flex: 52,
            child: pw.Padding(
              padding: const pw.EdgeInsets.fromLTRB(11, 10, 11, 9),
              child: pw.Column(
                crossAxisAlignment: pw.CrossAxisAlignment.start,
                children: [
                  pw.Text(
                    '${number.toString().padLeft(2, '0')}. ${issue.title.toUpperCase()}',
                    style: pw.TextStyle(
                      color: _navy,
                      fontSize: 10.2,
                      fontWeight: pw.FontWeight.bold,
                    ),
                  ),
                  pw.SizedBox(height: 7),
                  _paragraph('Local', issue.location.isEmpty ? 'Não informado' : issue.location),
                  if (issue.situation.isNotEmpty) _paragraph('Situação', issue.situation),
                  if (issue.risk.isNotEmpty) _paragraph('Risco', issue.risk),
                  if (issue.correction.isNotEmpty) _paragraph('Correção', issue.correction),
                  if (issue.priority.isNotEmpty) ...[
                    pw.SizedBox(height: 5),
                    pw.Text(
                      'PRIORIDADE: ${issue.priority.toUpperCase()}',
                      style: pw.TextStyle(
                        color: _priorityColor(issue.priority),
                        fontSize: 8.8,
                        fontWeight: pw.FontWeight.bold,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  static pw.Widget _evidence(_RoundIssue issue) {
    if (issue.photos.isEmpty) {
      return pw.Column(
        mainAxisAlignment: pw.MainAxisAlignment.center,
        children: [
          pw.Container(
            height: 145,
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
              textAlign: pw.TextAlign.left,
              style: const pw.TextStyle(fontSize: 7.0, color: PdfColors.grey700),
            ),
          ],
        ],
      );
    }

    return pw.Column(
      mainAxisAlignment: pw.MainAxisAlignment.center,
      children: [
        if (issue.photos.length == 1)
          pw.SizedBox(
            height: 160,
            child: pw.Image(issue.photos.first, fit: pw.BoxFit.contain),
          )
        else
          pw.Row(children: [
            for (var i = 0; i < issue.photos.length && i < 2; i++) ...[
              if (i > 0) pw.SizedBox(width: 5),
              pw.Expanded(
                child: pw.SizedBox(
                  height: 154,
                  child: pw.Image(issue.photos[i], fit: pw.BoxFit.contain),
                ),
              ),
            ],
          ]),
        if (issue.caption.isNotEmpty) ...[
          pw.SizedBox(height: 5),
          pw.Align(
            alignment: pw.Alignment.centerLeft,
            child: pw.Text(
              issue.caption,
              textAlign: pw.TextAlign.left,
              style: const pw.TextStyle(fontSize: 7.0, color: PdfColors.grey700),
            ),
          ),
        ],
      ],
    );
  }

  static pw.Widget _paragraph(String label, String value) => pw.Padding(
        padding: const pw.EdgeInsets.only(bottom: 5),
        child: pw.RichText(
          text: pw.TextSpan(children: [
            pw.TextSpan(
              text: '$label: ',
              style: pw.TextStyle(fontSize: 8.7, fontWeight: pw.FontWeight.bold),
            ),
            pw.TextSpan(
              text: value,
              style: const pw.TextStyle(fontSize: 8.7, lineSpacing: 1.85),
            ),
          ]),
        ),
      );

  static pw.Widget _technicalResponsible() => pw.Center(
        child: pw.SizedBox(
          width: 220,
          child: pw.Column(children: [
            pw.SizedBox(height: 42),
            pw.Container(height: .7, color: _navy),
            pw.SizedBox(height: 5),
            pw.Text(
              'TÉCNICO EM SEGURANÇA DO TRABALHO',
              style: pw.TextStyle(fontSize: 8.4, fontWeight: pw.FontWeight.bold),
            ),
            pw.Text(
              'Nome e registro profissional',
              style: const pw.TextStyle(fontSize: 8.0),
              textAlign: pw.TextAlign.center,
            ),
          ]),
        ),
      );

  static pw.Widget _footer(pw.Context context, pw.MemoryImage? auditarLogo) =>
      pw.Row(
        crossAxisAlignment: pw.CrossAxisAlignment.end,
        children: [
          pw.Expanded(child: pw.SizedBox()),
          _auditarBrand(auditarLogo, 92, 42),
          pw.Expanded(
            child: pw.Align(
              alignment: pw.Alignment.centerRight,
              child: pw.Text(
                'Página ${context.pageNumber}/${context.pagesCount}',
                style: const pw.TextStyle(fontSize: 7.0, color: PdfColors.grey700),
              ),
            ),
          ),
        ],
      );

  static pw.Widget _labelValue(String label, String value) => pw.RichText(
        text: pw.TextSpan(children: [
          pw.TextSpan(
            text: '$label: ',
            style: pw.TextStyle(fontSize: 8.0, fontWeight: pw.FontWeight.bold),
          ),
          pw.TextSpan(
            text: value.isEmpty ? 'Não informado' : value,
            style: const pw.TextStyle(fontSize: 8.0),
          ),
        ]),
      );

  static pw.Widget _auditarBrand(
    pw.MemoryImage? image,
    double width,
    double height,
  ) =>
      pw.SizedBox(
        width: width,
        height: height,
        child: image == null
            ? pw.SizedBox()
            : pw.Image(image, fit: pw.BoxFit.cover),
      );

  static pw.Widget _logo(pw.MemoryImage? image, double width, double height) =>
      pw.SizedBox(
        width: width,
        height: height,
        child: image == null ? pw.SizedBox() : pw.Image(image, fit: pw.BoxFit.contain),
      );

  static PdfColor _priorityColor(String value) {
    final p = value.toLowerCase();
    if (p.contains('imediat') || p.contains('crític') || p.contains('critic')) {
      return _red;
    }
    if (p.contains('alta') || p.contains('média') || p.contains('media')) {
      return _amber;
    }
    return _green;
  }

  static String _publicText(String value) => value
      .replaceAll(
        RegExp(r'ronda expressa', caseSensitive: false),
        'vistoria',
      )
      .trim();

  static String _captionFromTitle(String title) {
    var value = title
        .replaceAll(RegExp(r'^[0-9]{1,2}[.)-]?\s*'), '')
        .replaceAll(RegExp(r'\s+'), ' ')
        .trim();
    if (value.isEmpty) return '';
    if (value.length > 76) {
      final cut = value.substring(0, 76);
      final lastSpace = cut.lastIndexOf(' ');
      value = cut.substring(0, lastSpace > 52 ? lastSpace : 76).trim();
    }
    value = value.toLowerCase();
    value = '${value[0].toUpperCase()}${value.substring(1)}';
    if (!RegExp(r'[.!?]$').hasMatch(value)) value = '$value.';
    return value;
  }

  static String _compactConclusion(String value) {
    final source = _publicText(value)
        .replaceAll(RegExp(r'\s+'), ' ')
        .trim();
    if (source.isEmpty) return '';

    final parts = source
        .split(RegExp(r'(?<=[.!?])\s+'))
        .map((item) => item.trim())
        .where((item) => item.isNotEmpty)
        .where((item) {
          final lower = item.toLowerCase();
          return !lower.contains('caráter estritamente consultivo') &&
              !lower.contains('carater estritamente consultivo') &&
              !lower.contains('cabendo a decisão técnica') &&
              !lower.contains('cabendo a decisao tecnica');
        })
        .toList();

    final selected = <String>[];
    var length = 0;
    for (final sentence in parts) {
      if (selected.length >= 4) break;
      if (length + sentence.length > 760 && selected.isNotEmpty) break;
      selected.add(sentence);
      length += sentence.length;
    }
    return selected.join(' ').trim();
  }

  static String _compactTitle(String value) {
    final clean = value
        .replaceAll(RegExp(r'\s+'), ' ')
        .replaceAll(RegExp(r'^[^·]{1,18}\s*·\s*'), '')
        .replaceAll(
          RegExp(
            r'\s*,?\s*conforme (?:apontado|informado) pelo técnico\.?$',
            caseSensitive: false,
          ),
          '',
        )
        .trim()
        .replaceAll(RegExp(r'[.,;:]+$'), '');
    if (clean.length <= 92) return clean;
    final cut = clean.substring(0, 92);
    final lastSpace = cut.lastIndexOf(' ');
    return '${cut.substring(0, lastSpace > 64 ? lastSpace : 92).trim()}...';
  }
  static List<String> _compactReferences(List<String> values) {
    final standards = <String>[];
    var fireDepartment = false;

    void add(String value) {
      if (!standards.any((e) => e.toLowerCase() == value.toLowerCase())) {
        standards.add(value);
      }
    }

    for (final raw in values) {
      final text = raw.trim();
      if (text.isEmpty) continue;

      for (final match in RegExp(
        r'\\bNR[- ]?(\\d{1,2})\\b',
        caseSensitive: false,
      ).allMatches(text)) {
        add('NR-${match.group(1)}');
      }
      for (final match in RegExp(
        r'\\bNBR\\s*(\\d{4,5})\\b',
        caseSensitive: false,
      ).allMatches(text)) {
        add('NBR ${match.group(1)}');
      }
      final lower = text.toLowerCase();
      if (lower.contains('corpo de bombeiros') ||
          lower.contains('instrução técnica') ||
          lower.contains('instrucao tecnica')) {
        fireDepartment = true;
      }
    }

    int numberOf(String value) =>
        int.tryParse(RegExp(r'\\d+').firstMatch(value)?.group(0) ?? '') ?? 99999;

    standards.sort((a, b) {
      if (a.startsWith('NR-') && b.startsWith('NR-')) {
        return numberOf(a).compareTo(numberOf(b));
      }
      if (a.startsWith('NR-')) return -1;
      if (b.startsWith('NR-')) return 1;
      return a.compareTo(b);
    });

    if (fireDepartment) add('exigências aplicáveis do Corpo de Bombeiros');
    return standards;
  }

  static String _first(List<Object?> values) {
    for (final raw in values) {
      final value = '${raw ?? ''}'.trim();
      if (value.isNotEmpty && value.toLowerCase() != 'null') return value;
    }
    return '';
  }

  static List<String> _stringList(dynamic raw) {
    if (raw is! List) return const [];
    return raw
        .map((e) => '${e ?? ''}'.trim())
        .where((e) => e.isNotEmpty && e.toLowerCase() != 'null')
        .toList();
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

class _RoundIssue {
  final String title;
  final String caption;
  final String location;
  final String situation;
  final String risk;
  final String correction;
  final String priority;
  final List<pw.MemoryImage> photos;

  const _RoundIssue({
    required this.title,
    required this.caption,
    required this.location,
    required this.situation,
    required this.risk,
    required this.correction,
    required this.priority,
    required this.photos,
  });
}

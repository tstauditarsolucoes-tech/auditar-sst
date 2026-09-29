import 'dart:typed_data';

import 'package:intl/intl.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import '../models.dart';

class ExtinguisherInspectionPdfService {
  static const _navy = PdfColor(0.07, 0.20, 0.32);
  static const _green = PdfColor(0.05, 0.48, 0.24);
  static const _red = PdfColor(0.75, 0.10, 0.10);
  static const _amber = PdfColor(0.70, 0.45, 0.05);
  static const _line = PdfColor(0.72, 0.75, 0.77);

  static String _monthKey(DateTime value) =>
      '${value.year}-${value.month.toString().padLeft(2, '0')}';

  static String _value(Map<String, dynamic> map, Iterable<String> keys) {
    for (final key in keys) {
      final value = '${map[key] ?? ''}'.trim();
      if (value.isNotEmpty) return value;
    }
    return '';
  }

  static String _location(SstRecord item) => _value(
        item.payload,
        const ['location', 'local', 'localizacao', 'setor'],
      ).isEmpty
          ? item.title
          : _value(
              item.payload,
              const ['location', 'local', 'localizacao', 'setor'],
            );

  static String _type(SstRecord item) {
    final value = _value(
      item.payload,
      const ['tipo', 'type', 'agent', 'agente'],
    );
    return value.isEmpty ? 'Extintor' : value;
  }

  static SstRecord? _inspectionFor(
    List<SstRecord> inspections,
    SstRecord extinguisher,
    String monthKey,
  ) {
    SstRecord? result;
    for (final item in inspections) {
      if ('${item.payload['extinguisherId'] ?? ''}' == extinguisher.id &&
          '${item.payload['monthKey'] ?? ''}' == monthKey) {
        result = item;
      }
    }
    return result;
  }

  static PdfColor _statusColor(String status) {
    final normalized = status.toLowerCase();
    if (normalized.contains('não conforme') ||
        normalized.contains('nao conforme') ||
        normalized.contains('não localizado') ||
        normalized.contains('nao localizado')) {
      return _red;
    }
    if (normalized == 'conforme') return _green;
    return _amber;
  }

  static pw.Widget _header(String title, Company company) => pw.Column(
        crossAxisAlignment: pw.CrossAxisAlignment.stretch,
        children: [
          pw.Text(
            'AUDITAR SOLUÇÕES',
            textAlign: pw.TextAlign.center,
            style: pw.TextStyle(
              fontSize: 15,
              fontWeight: pw.FontWeight.bold,
              color: _navy,
            ),
          ),
          pw.SizedBox(height: 2),
          pw.Text(
            title,
            textAlign: pw.TextAlign.center,
            style: pw.TextStyle(
              fontSize: 12,
              fontWeight: pw.FontWeight.bold,
              color: _navy,
            ),
          ),
          pw.SizedBox(height: 4),
          pw.Text(
            company.name,
            textAlign: pw.TextAlign.center,
            style: const pw.TextStyle(fontSize: 9),
          ),
          if ((company.cnpj ?? '').trim().isNotEmpty)
            pw.Text(
              'CNPJ: ${company.cnpj}',
              textAlign: pw.TextAlign.center,
              style: const pw.TextStyle(fontSize: 8),
            ),
          pw.SizedBox(height: 8),
          pw.Container(height: 1, color: _line),
          pw.SizedBox(height: 10),
        ],
      );

  static Future<Uint8List> generateMonthly({
    required Company company,
    required List<SstRecord> extinguishers,
    required List<SstRecord> inspections,
    required DateTime month,
  }) async {
    final key = _monthKey(month);
    final rows = <List<String>>[];
    var regular = 0;
    var irregular = 0;
    var pending = 0;

    for (final extinguisher in extinguishers) {
      final inspection = _inspectionFor(inspections, extinguisher, key);
      final status = '${inspection?.payload['result'] ?? 'Pendente'}';
      if (status == 'Conforme') {
        regular++;
      } else if (status == 'Pendente') {
        pending++;
      } else {
        irregular++;
      }
      rows.add([
        extinguisher.title,
        _location(extinguisher),
        _type(extinguisher),
        status,
        '${inspection?.payload['serviceStatus'] ?? ''}',
        '${inspection?.payload['observation'] ?? ''}',
      ]);
    }

    final doc = pw.Document(
      title:
          'Inspeção mensal de extintores - ${month.month.toString().padLeft(2, '0')}/${month.year}',
      author: 'Auditar Soluções',
    );

    doc.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4.landscape,
        margin: const pw.EdgeInsets.all(28),
        footer: (context) => pw.Row(
          mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
          children: [
            const pw.Text(
              'Auditar SST • Inspeção mensal de extintores',
              style: pw.TextStyle(fontSize: 7, color: PdfColors.grey700),
            ),
            pw.Text(
              'Página ${context.pageNumber} de ${context.pagesCount}',
              style: const pw.TextStyle(fontSize: 7, color: PdfColors.grey700),
            ),
          ],
        ),
        build: (_) => [
          _header(
            'INSPEÇÃO MENSAL DE EXTINTORES • ${month.month.toString().padLeft(2, '0')}/${month.year}',
            company,
          ),
          pw.Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _metric('Cadastrados', extinguishers.length, _navy),
              _metric('Conformes', regular, _green),
              _metric('Irregulares', irregular, _red),
              _metric('Pendentes', pending, _amber),
            ],
          ),
          pw.SizedBox(height: 14),
          pw.Table(
            border: pw.TableBorder.all(color: _line, width: .5),
            columnWidths: const {
              0: pw.FlexColumnWidth(1.5),
              1: pw.FlexColumnWidth(1.6),
              2: pw.FlexColumnWidth(.9),
              3: pw.FlexColumnWidth(.9),
              4: pw.FlexColumnWidth(1.0),
              5: pw.FlexColumnWidth(2.1),
            },
            children: [
              pw.TableRow(
                decoration: const pw.BoxDecoration(color: PdfColors.grey200),
                children: [
                  for (final value in const [
                    'Identificação',
                    'Local',
                    'Tipo',
                    'Resultado',
                    'Situação',
                    'Observação',
                  ])
                    _cell(value, bold: true),
                ],
              ),
              for (final row in rows)
                pw.TableRow(
                  children: [
                    for (var i = 0; i < row.length; i++)
                      i == 3
                          ? _statusCell(row[i])
                          : _cell(row[i].isEmpty ? '—' : row[i]),
                  ],
                ),
            ],
          ),
          pw.SizedBox(height: 14),
          pw.Text(
            'Documento gerado a partir dos registros cadastrados no Auditar SST. '
            'Extintores sem inspeção registrada no mês permanecem como pendentes.',
            style: const pw.TextStyle(fontSize: 7.5, color: PdfColors.grey700),
          ),
        ],
      ),
    );

    return doc.save();
  }

  static Future<Uint8List> generateAnnualSheet({
    required Company company,
    required SstRecord extinguisher,
    required List<SstRecord> inspections,
    required int year,
  }) async {
    final byMonth = <int, SstRecord>{};
    for (final item in inspections) {
      final key = '${item.payload['monthKey'] ?? ''}';
      final parts = key.split('-');
      if (parts.length != 2) continue;
      final y = int.tryParse(parts[0]);
      final m = int.tryParse(parts[1]);
      if (y == year && m != null && m >= 1 && m <= 12) {
        byMonth[m] = item;
      }
    }

    final doc = pw.Document(
      title: 'Ficha anual de inspeção - ${extinguisher.title} - $year',
      author: 'Auditar Soluções',
    );
    doc.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.fromLTRB(30, 28, 30, 36),
        footer: (context) => pw.Row(
          mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
          children: [
            const pw.Text(
              'Auditar SST • Ficha anual de extintor',
              style: pw.TextStyle(fontSize: 7, color: PdfColors.grey700),
            ),
            pw.Text(
              'Página ${context.pageNumber} de ${context.pagesCount}',
              style: const pw.TextStyle(fontSize: 7, color: PdfColors.grey700),
            ),
          ],
        ),
        build: (_) => [
          _header('FICHA ANUAL DE INSPEÇÃO DE EXTINTOR • $year', company),
          pw.Table(
            border: pw.TableBorder.all(color: _line, width: .5),
            columnWidths: const {
              0: pw.FixedColumnWidth(110),
              1: pw.FlexColumnWidth(),
            },
            children: [
              _identity('Identificação', extinguisher.title),
              _identity('Local', _location(extinguisher)),
              _identity('Tipo', _type(extinguisher)),
            ],
          ),
          pw.SizedBox(height: 14),
          pw.Table(
            border: pw.TableBorder.all(color: _line, width: .5),
            columnWidths: const {
              0: pw.FixedColumnWidth(48),
              1: pw.FixedColumnWidth(78),
              2: pw.FlexColumnWidth(),
              3: pw.FlexColumnWidth(),
            },
            children: [
              pw.TableRow(
                decoration: const pw.BoxDecoration(color: PdfColors.grey200),
                children: [
                  _cell('Mês', bold: true),
                  _cell('Resultado', bold: true),
                  _cell('Situação do equipamento', bold: true),
                  _cell('Observação', bold: true),
                ],
              ),
              for (var month = 1; month <= 12; month++)
                pw.TableRow(
                  children: [
                    _cell(DateFormat('MMM', 'pt_BR').format(DateTime(year, month)).toUpperCase()),
                    _statusCell(
                      '${byMonth[month]?.payload['result'] ?? 'Pendente'}',
                    ),
                    _cell(
                      '${byMonth[month]?.payload['serviceStatus'] ?? '—'}',
                    ),
                    _cell(
                      '${byMonth[month]?.payload['observation'] ?? '—'}',
                    ),
                  ],
                ),
            ],
          ),
          pw.SizedBox(height: 18),
          pw.Text(
            'Checklist utilizado: validade, pressão/indicador, lacre e pino, '
            'sinalização, acesso livre, mangueira/bico e condição geral. '
            'Quando o extintor não é localizado, o resultado é registrado de forma específica.',
            style: const pw.TextStyle(fontSize: 8, lineSpacing: 2),
          ),
        ],
      ),
    );
    return doc.save();
  }

  static pw.Widget _metric(String label, int value, PdfColor color) =>
      pw.Container(
        width: 105,
        padding: const pw.EdgeInsets.all(9),
        decoration: pw.BoxDecoration(
          border: pw.Border.all(color: color, width: .8),
          borderRadius: pw.BorderRadius.circular(5),
        ),
        child: pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            pw.Text(
              '$value',
              style: pw.TextStyle(
                fontSize: 16,
                color: color,
                fontWeight: pw.FontWeight.bold,
              ),
            ),
            pw.Text(label, style: const pw.TextStyle(fontSize: 7.5)),
          ],
        ),
      );

  static pw.TableRow _identity(String label, String value) => pw.TableRow(
        children: [
          _cell(label, bold: true),
          _cell(value.isEmpty ? 'Não informado' : value),
        ],
      );

  static pw.Widget _statusCell(String value) => pw.Container(
        padding: const pw.EdgeInsets.all(6),
        child: pw.Text(
          value,
          style: pw.TextStyle(
            fontSize: 7.5,
            fontWeight: pw.FontWeight.bold,
            color: _statusColor(value),
          ),
        ),
      );

  static pw.Widget _cell(String value, {bool bold = false}) => pw.Padding(
        padding: const pw.EdgeInsets.all(6),
        child: pw.Text(
          value,
          style: pw.TextStyle(
            fontSize: 7.5,
            fontWeight: bold ? pw.FontWeight.bold : pw.FontWeight.normal,
          ),
        ),
      );
}

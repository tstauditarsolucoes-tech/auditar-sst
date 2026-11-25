import 'dart:typed_data';
import 'package:flutter/services.dart' show rootBundle;
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'sst_risk_documents_models.dart';

/// PDFs sao SEMPRE minutas, jamais permissao emitida ou liberacao de trabalho.
class SstRiskDocumentPdf {
  const SstRiskDocumentPdf._();

  static const navy = PdfColor(0.08, 0.21, 0.34);
  static const pale = PdfColor(0.94, 0.97, 0.96);

  static Future<pw.MemoryImage?> _logo() async {
    try {
      final asset = await rootBundle.load('assets/branding/auditar_logo.jpg');
      if (asset.lengthInBytes > 0 && asset.lengthInBytes < 2500000) {
        return pw.MemoryImage(asset.buffer.asUint8List());
      }
    } catch (_) {
      // Sem logo, o PDF mantém identificação textual da Auditar.
    }
    return null;
  }


  static pw.Widget line(String label, String value) => pw.Padding(
    padding: const pw.EdgeInsets.only(bottom: 5),
    child: pw.RichText(text: pw.TextSpan(children: [
      pw.TextSpan(text: label + ': ',
          style: pw.TextStyle(fontWeight: pw.FontWeight.bold,
              fontSize: 9, color: navy)),
      pw.TextSpan(text: value.isEmpty ? 'Não informado' : value,
          style: const pw.TextStyle(fontSize: 9)),
    ])),
  );

  static pw.Widget section(String title) => pw.Container(
    padding: const pw.EdgeInsets.all(8),
    margin: const pw.EdgeInsets.only(top: 12, bottom: 7),
    decoration: const pw.BoxDecoration(color: pale),
    child: pw.Text(title, style: pw.TextStyle(
      color: navy, fontWeight: pw.FontWeight.bold, fontSize: 12)),
  );

  static Future<Uint8List> generate({
    required String companyName,
    required String companyId,
    required SstRiskDocDraft draft,
  }) async {
    if (draft.companyId != companyId || !draft.canExportDraft) {
      throw StateError('Documento incompleto ou empresa divergente.');
    }
    final logo = await _logo();
    final pdf = pw.Document(compress: true);
    final widgets = <pw.Widget>[
      if (logo != null) pw.Image(logo,
        width: 140, height: 58, fit: pw.BoxFit.contain),
      pw.Text('AUDITAR SOLUÇÕES | SST',
          style: pw.TextStyle(color: navy, fontSize: 13,
              fontWeight: pw.FontWeight.bold)),
      pw.SizedBox(height: 8),
      pw.Text(draft.kind.title, style: pw.TextStyle(
          color: navy, fontSize: 17, fontWeight: pw.FontWeight.bold)),
      pw.SizedBox(height: 6),
      pw.Container(
        padding: const pw.EdgeInsets.all(9),
        decoration: pw.BoxDecoration(
          border: pw.Border.all(color: PdfColors.red700, width: 1.2),
        ),
        child: pw.Text(
          'MINUTA PARA CONFERÊNCIA TÉCNICA - NÃO AUTORIZA INÍCIO '
          'DE TRABALHO. Emissão do PDF não comprova aprovação, '
          'treinamento, inspeção, eficácia de controles ou vigência de PT.',
          style: pw.TextStyle(
              color: PdfColors.red800,
              fontSize: 9, fontWeight: pw.FontWeight.bold),
        ),
      ),
      section('Identificação'),
      line('Empresa', companyName),
      line('ID do rascunho', draft.id),
      line('Atividade', draft.activity),
      line('Local ou setor', draft.sector),
      line('Data de elaboração', draft.date),
      line('Elaborado por (informado)', draft.preparedBy),
      line('Condições impeditivas', draft.blockers),
      line('Emergência e resgate', draft.emergency),
      if (draft.kind == SstRiskDocKind.pt) ...[
        section('Condições da PT - aprovação pendente'),
        line('Equipe informada', draft.team),
        line('Fim de validade proposto', draft.validUntil),
        line('Responsável a consultar para autorização', draft.authorizer),
        line('Referência à AR/APR existente', draft.referenceAr),
        pw.Text(
          'A pessoa indicada NÃO assinou, aprovou nem liberou '
          'a execução por meio deste arquivo. Uma PT verdadeira '
          'exige checagem presencial, autorização válida, '
          'vigência aplicável, comunicação à equipe e encerramento '
          'conforme procedimento e norma pertinente.',
          style: pw.TextStyle(fontSize: 9, fontWeight: pw.FontWeight.bold),
        ),
      ],
      section(draft.kind == SstRiskDocKind.pt
          ? 'Conferência de perigos e controles (informada)'
          : 'Análise das etapas e controles'),
    ];
    for (var i = 0; i < draft.items.length; i++) {
      final row = draft.items[i];
      widgets.add(section('ETAPA ' + (i + 1).toString()));
      widgets.add(line('Etapa / atividade', row.step));
      widgets.add(line('Perigo', row.hazard));
      widgets.add(line('Possível consequência', row.consequence));
      widgets.add(line('Controles informados', row.controls));
      widgets.add(line('Responsável proposto', row.owner));
      widgets.add(line('Probabilidade x severidade (escala ilustrativa 1-5)',
          row.probability.toString() + ' x ' +
          row.severity.toString() + ' = ' + row.illustrativeScore.toString()));
      widgets.add(pw.Text(
        'Pontuação apenas orientativa. Método, critério, aceitabilidade '
        'e riscos residuais exigem validação; não libera trabalho.',
        style: const pw.TextStyle(fontSize: 8),
      ));
    }
    widgets.add(section('Conferência antes da formalização'));
    widgets.add(pw.Text(
      'Verificar presencialmente a atividade, os controles, '
      'os requisitos das NRs aplicáveis, os responsáveis e os '
      'documentos complementares. Não alterar informações já '
      'aprovadas sem novo processo de autorização.',
      style: const pw.TextStyle(fontSize: 9),
    ));
    pdf.addPage(pw.MultiPage(
      pageFormat: PdfPageFormat.a4,
      margin: const pw.EdgeInsets.fromLTRB(36, 38, 36, 36),
      build: (_) => widgets,
      footer: (_) => pw.Container(
        alignment: pw.Alignment.center,
        padding: const pw.EdgeInsets.only(top: 8),
        child: pw.Text(
          'AUDITAR SST - MINUTA NÃO AUTORIZADA - Revisão técnica obrigatória',
          style: const pw.TextStyle(fontSize: 8, color: PdfColors.grey600),
        ),
      ),
    ));
    return pdf.save();
  }
}

import 'dart:typed_data';
import 'dart:convert';
import 'package:flutter/services.dart' show rootBundle;

import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import 'sst_pet_nr33_models.dart';
import 'sst_document_signature_models.dart';

/// Impressao offline de MINUTA para conferencia; nunca uma PET emitida.
/// A NR-33 exige assinaturas efetivas de supervisor e vigia, procedimento
/// para validade/encerramento e acesso permanente ao vigia na PET digital.
class SstPetNr33Pdf {
  const SstPetNr33Pdf._();

  static const navy = PdfColor(0.08, 0.21, 0.35);
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


  static pw.Widget heading(String label) => pw.Container(
    margin: const pw.EdgeInsets.only(top: 11, bottom: 6),
    padding: const pw.EdgeInsets.all(7),
    decoration: const pw.BoxDecoration(color: pale),
    child: pw.Text(label, style: pw.TextStyle(
      color: navy, fontWeight: pw.FontWeight.bold, fontSize: 11)),
  );

  static pw.Widget textLine(String label, String value) => pw.Padding(
    padding: const pw.EdgeInsets.only(bottom: 5),
    child: pw.RichText(text: pw.TextSpan(children: [
      pw.TextSpan(text: label + ': ', style: pw.TextStyle(
        fontSize: 9, fontWeight: pw.FontWeight.bold, color: navy)),
      pw.TextSpan(text: value.isEmpty ? 'Não informado' : value,
        style: const pw.TextStyle(fontSize: 9)),
    ])),
  );

  static Future<Uint8List> generate({
    required String companyName,
    required String companyId,
    required String userId,
    required SstPetDraft draft,
    List<SstHandwrittenMark> signatures = const [],
  }) async {
    if (draft.companyId != companyId || draft.userId != userId ||
        !draft.readyForReviewPdf) {
      throw StateError('Minuta PET incompleta ou fora desta empresa/conta');
    }
    final snapshot = sstDocumentFingerprint(draft.toJson());
    if (signatures.any((m) => !m.isCurrent(snapshot))) {
      throw StateError('Assinatura desatualizada: revisar nova versão');
    }
    final logo = await _logo();
    final doc = pw.Document(compress: true);
    final contents = <pw.Widget>[
      if (logo != null) pw.Image(logo,
        width: 140, height: 58, fit: pw.BoxFit.contain),
      pw.Text('AUDITAR SOLUÇÕES | SST', style: pw.TextStyle(
        color: navy, fontSize: 12, fontWeight: pw.FontWeight.bold)),
      pw.SizedBox(height: 6),
      pw.Text('PET - Permissão de Entrada e Trabalho (NR-33)',
        style: pw.TextStyle(
          color: navy, fontSize: 16, fontWeight: pw.FontWeight.bold)),
      pw.SizedBox(height: 6),
      pw.Container(
        padding: const pw.EdgeInsets.all(9),
        decoration: pw.BoxDecoration(border: pw.Border.all(
          color: PdfColors.red700, width: 1.5)),
        child: pw.Text(
          'MINUTA / RASCUNHO PARA CONFERÊNCIA - NÃO É PET EMITIDA. '
          'ENTRADA PROIBIDA COM ESTE DOCUMENTO. Não há validação '
          'presencial, assinatura certificada, comunicação ao vigia, '
          'monitoramento real nem autorização de entrada pelo aplicativo.',
          style: pw.TextStyle(
            color: PdfColors.red800,
            fontSize: 9, fontWeight: pw.FontWeight.bold),
        ),
      ),
      heading('Rastreamento interno da minuta'),
      textLine('Empresa', companyName),
      textLine('Identificador do rascunho', draft.id),
      textLine('Referência de modelo', 'NR-33 33.5.6 e Anexo II; adaptar '
        'ao espaço, ao procedimento e aos riscos reais da organização'),
    ];
    String? lastGroup;
    for (final field in PetTemplate.fields) {
      if (lastGroup != field.group) {
        contents.add(heading(field.group));
        lastGroup = field.group;
      }
      contents.add(textLine(field.label, draft.value(field.key)));
    }
    contents.add(heading('Checklist de preparação informado'));
    for (final item in PetTemplate.checks) {
      contents.add(textLine(item.label,
          draft.status(item.key).label));
      if (draft.note(item.key).isNotEmpty) {
        contents.add(textLine('Justificativa / observação',
            draft.note(item.key)));
      }
    }
    if (draft.readings.isNotEmpty) {
      contents.add(heading('Leituras atmosféricas complementares - INFORMADAS'));
      for (final reading in draft.readings) {
        contents.add(textLine('Data/hora e ponto',
            reading.dateTime + ' / ' + reading.point));
        contents.add(textLine('O₂ (% vol.)', reading.oxygen));
        contents.add(textLine('Inflamáveis (% LIE)', reading.lel));
        contents.add(textLine('Tóxicos (valor e unidade)', reading.toxic));
        contents.add(textLine('Detector e testes', reading.detector));
        contents.add(textLine('Responsável pela medição', reading.measuredBy));
        contents.add(pw.Text(
          'Leitura apenas informada, NÃO validada pelo aplicativo. '
          'Não comprova atmosfera segura ou monitoramento contínuo.',
          style: const pw.TextStyle(fontSize: 8),
        ));
      }
    }
    contents.add(heading('Rubricas manuscritas de CIÊNCIA — NÃO certificadas'));
    if (signatures.isEmpty) {
      contents.add(textLine('Rubricas desta versão', 'Não registradas'));
    }
    for (final mark in signatures) {
      contents.add(textLine('Papel de ciência', mark.roleLabel));
      contents.add(textLine('Nome declarado', mark.declaredName));
      contents.add(textLine('Função declarada', mark.declaredFunction));
      contents.add(textLine('Horário registrado em UTC', mark.signedAt));
      contents.add(pw.Image(
        pw.MemoryImage(base64Decode(mark.pngBase64)),
        width: 190, height: 67, fit: pw.BoxFit.contain,
      ));
    }
    contents.add(heading('Limites, assinaturas e encerramento'));
    contents.add(pw.Text(
      'Assinatura digital certificada do supervisor: NÃO IMPLEMENTADA.\n'
      'Assinatura digital certificada do vigia: NÃO IMPLEMENTADA.\n'
      'Data/hora reais de emissão e encerramento: NÃO VERIFICADAS.\n'
      'As rubricas acima são apenas registros manuais de ciência '
      'da minuta. NÃO constituem emissão de PET, aprovação ou '
      'autorização de entrada. A NR-33 exige certificação de '
      'assinatura e acesso permanente pelo vigia em PET digital. '
      'Esta minuta não satisfaz tais requisitos.',
      style: const pw.TextStyle(fontSize: 9),
    ));
    contents.add(pw.SizedBox(height: 8));
    contents.add(pw.Text(
      'AVISO: não liberar entrada sem PET válida, supervisor, vigia, '
      'avaliação atmosférica prévia e monitoramento contínuo, controles '
      'implantados, capacitação e resgate conforme NR-33. Os valores de '
      'O₂ e LIE são somente números informados pelo usuário; '
      'o aplicativo não julga atmosfera segura nem avalia toxicidade.',
      style: pw.TextStyle(fontSize: 9,
          color: PdfColors.red800, fontWeight: pw.FontWeight.bold),
    ));

    doc.addPage(pw.MultiPage(
      pageFormat: PdfPageFormat.a4,
      margin: const pw.EdgeInsets.fromLTRB(36, 38, 36, 38),
      build: (_) => contents,
      footer: (_) => pw.Container(
        padding: const pw.EdgeInsets.only(top: 8),
        alignment: pw.Alignment.center,
        child: pw.Text('AUDITAR SST | PET NR-33 | MINUTA NÃO AUTORIZADA',
          style: const pw.TextStyle(fontSize: 8, color: PdfColors.grey600)),
      ),
    ));
    return doc.save();
  }
}

import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/services.dart' show rootBundle;
import 'package:intl/intl.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import 'sst_report_center_models.dart';

/// PDF local de campo: nunca deduz ensaios, conformidade ou evidências.
class SstFieldReportPdfService {
  const SstFieldReportPdfService._();

  static const ink=PdfColor(0.09,0.22,0.31);
  static const green=PdfColor(0.08,0.43,0.31);
  static const muted=PdfColor(0.37,0.43,0.47);
  static const paper=PdfColor(0.95,0.97,0.96);

  static Future<pw.MemoryImage?> _branding() async {
    try {
      final asset=await rootBundle.load('assets/branding/auditar_logo.jpg');
      if(asset.lengthInBytes>0&&asset.lengthInBytes<2500000) {
        return pw.MemoryImage(asset.buffer.asUint8List());
      }
    } catch (_) {}
    return null;
  }

  static Future<pw.MemoryImage?> _storedImage(String path) async {
    if(path.isEmpty)return null;
    try {
      final file=File(path);
      if(!await file.exists())return null;
      final length=await file.length();
      if(length<100||length>10*1024*1024)return null;
      return pw.MemoryImage(await file.readAsBytes());
    } catch (_) {return null;}
  }

  static String _pdfText(String input) =>
      input.replaceAll('•','-').replaceAll('—','-')
          .replaceAll('–','-');

  static String _date(String raw) {
    final date=DateTime.tryParse(raw);
    return date==null?raw:DateFormat('dd/MM/yyyy').format(date);
  }

  static pw.Widget _line(String label,String value) => pw.Padding(
    padding:const pw.EdgeInsets.only(bottom:6),
    child:pw.RichText(text:pw.TextSpan(children:[
      pw.TextSpan(text:'$label  ',
        style:pw.TextStyle(fontSize:9,color:ink,
          fontWeight:pw.FontWeight.bold)),
      pw.TextSpan(text:_pdfText(value.isEmpty?'Não informado':value),
        style:const pw.TextStyle(fontSize:9,color:muted)),
    ])),
  );

  static pw.Widget _sectionTitle(String title) => pw.Container(
    padding:const pw.EdgeInsets.symmetric(horizontal:9,vertical:7),
    margin:const pw.EdgeInsets.only(top:10,bottom:7),
    decoration:const pw.BoxDecoration(color:paper),
    child:pw.Text(_pdfText(title),style:pw.TextStyle(color:ink,fontSize:11,
      fontWeight:pw.FontWeight.bold)),
  );

  static Future<Uint8List> generate({
    required String companyName,
    required String companyId,
    required SstFieldDraft draft,
  }) async {
    if(draft.companyId!=companyId) {
      throw StateError('Rascunho não pertence à empresa selecionada.');
    }
    if(!draft.hasEnoughForPdf) {
      throw StateError('Informe técnico, data e dados essenciais; '
          'descreva cada item não conforme ou apurado antes de gerar.');
    }
    final model=SstFieldTemplates.of(draft.kind);
    final doc=pw.Document(compress:true);
    final logo=await _branding();

    final entries=<pw.Widget>[];
    final checked=model.questions.where((q)=>draft.answer(q.id).isReviewed);
    for(final question in checked){
      final answer=draft.answer(question.id);
      final photos=<pw.MemoryImage>[];
      for(final p in answer.photoPaths.take(2)){
        final image=await _storedImage(p);
        if(image==null) {
          throw StateError('Uma foto selecionada não está acessível '
            'neste aparelho. Recupere ou substitua a imagem antes de '
            'gerar o PDF; nenhuma evidência será omitida sem aviso.');
        }
        photos.add(image);
      }
      entries.add(pw.Container(
        margin:const pw.EdgeInsets.only(bottom:9),
        padding:const pw.EdgeInsets.all(10),
        decoration:pw.BoxDecoration(
          border:pw.Border.all(color:const PdfColor(0.84,0.87,0.88)),
          borderRadius:const pw.BorderRadius.all(pw.Radius.circular(4)),
        ),
        child:pw.Column(
          crossAxisAlignment:pw.CrossAxisAlignment.start,
          children:[
            pw.Text(question.group.toUpperCase(),
              style:pw.TextStyle(color:green,fontSize:8,
                fontWeight:pw.FontWeight.bold)),
            pw.SizedBox(height:4),
            pw.Text(_pdfText(question.title),style:pw.TextStyle(
              fontSize:10.5,color:ink,fontWeight:pw.FontWeight.bold)),
            pw.SizedBox(height:4),
            pw.Text('Verificação: '+answer.status.label(
              investigation:draft.kind==SstFieldReportKind.incident),
              style:pw.TextStyle(
                fontSize:9,color:answer.status==SstFieldStatus.nonConforming?
                  const PdfColor(0.65,0.12,0.12):ink,
                fontWeight:pw.FontWeight.bold)),
            if(answer.observation.trim().isNotEmpty)...[
              pw.SizedBox(height:6),
              _line('Situação / evidência relatada:',answer.observation.trim()),
            ],
            if(answer.recommendation.trim().isNotEmpty)...[
              pw.SizedBox(height:4),
              _line('Medida recomendada pelo técnico:',
                answer.recommendation.trim()),
            ],
            if(photos.isNotEmpty)...[
              pw.SizedBox(height:7),
              pw.Wrap(spacing:8,runSpacing:8,children:[
                for(final photo in photos)
                  pw.Container(
                    width:photos.length==1?410:240,
                    height:photos.length==1?222:160,
                    decoration:pw.BoxDecoration(border:pw.Border.all(
                      color:const PdfColor(0.80,0.82,0.84))),
                    child:pw.Image(photo,fit:pw.BoxFit.contain)),
              ]),
            ],
          ],
        ),
      ));
    }

    final signature=await _storedImage(draft.signaturePath);
    if(draft.signaturePath.trim().isNotEmpty && signature==null) {
      throw StateError('A assinatura selecionada não está acessível '
        'neste aparelho. Recupere ou assine novamente antes de exportar.');
    }
    doc.addPage(pw.MultiPage(
      pageFormat:PdfPageFormat.a4,
      margin:const pw.EdgeInsets.fromLTRB(28,28,28,37),
      footer:(context)=>pw.Row(
        mainAxisAlignment:pw.MainAxisAlignment.spaceBetween,
        children:[
          pw.Text('Auditar SST - Registro técnico de campo',
            style:const pw.TextStyle(color:muted,fontSize:8)),
          pw.Text('Página ${context.pageNumber}/${context.pagesCount}',
            style:const pw.TextStyle(color:muted,fontSize:8)),
        ],
      ),
      build:(context)=>[
        pw.Row(mainAxisAlignment:pw.MainAxisAlignment.spaceBetween,
          crossAxisAlignment:pw.CrossAxisAlignment.center,children:[
          if(logo!=null)pw.Image(logo,height:48,width:145,fit:pw.BoxFit.contain),
          pw.Text('RELATÓRIO SST',
            style:pw.TextStyle(fontSize:18,color:ink,
              fontWeight:pw.FontWeight.bold)),
        ]),
        pw.SizedBox(height:12),
        pw.Text(_pdfText(model.title),style:pw.TextStyle(
          fontSize:15,color:green,fontWeight:pw.FontWeight.bold)),
        pw.SizedBox(height:6),
        pw.Text(
          draft.isPartial?'RASCUNHO PARCIAL - ITENS PENDENTES DE VERIFICAÇÃO':
          'REGISTRO PARA REVISÃO TÉCNICA',
          style:pw.TextStyle(
            color:draft.isPartial?const PdfColor(0.66,0.34,0.08):muted,
            fontSize:8.5,fontWeight:pw.FontWeight.bold)),
        _sectionTitle('Identificação'),
        _line('Empresa:',companyName),
        _line('Setor / local:',draft.location),
        _line('Máquina / frente / atividade:',draft.asset),
        _line('Técnico responsável:',draft.technician),
        _line('Data informada da vistoria:',_date(draft.date)),
        _line('Referência temática:',model.reference),
        if(draft.kind==SstFieldReportKind.incident)...[
          _sectionTitle('Informações iniciais da ocorrência'),
          _line('Data e hora relatadas:',_date(draft.eventTime)),
          _line('Descrição factual fornecida pelo técnico:',
            draft.eventNarrative),
          pw.Text('A investigação deve diferenciar fatos confirmados, '
            'informações recebidas e hipóteses. Este relatório não substitui '
            'CAT, perícia ou outros documentos legais.',
            style:const pw.TextStyle(fontSize:8.5,color:muted)),
        ],
        _sectionTitle('Síntese dos itens analisados'),
        _line('Itens do roteiro:',model.questions.length.toString()),
        _line('Itens verificados:',draft.reviewed.toString()),
        _line('Itens não verificados:',
          (model.questions.length-draft.reviewed).toString()),
        if(draft.kind!=SstFieldReportKind.incident)
          _line('Itens marcados não conformes:',
            draft.nonConformities.toString()),
        _sectionTitle('Registros por tema'),
        ...entries,
        _sectionTitle('Assinatura e responsabilidade'),
        pw.Text('As descrições, fotografias, constatações e recomendações '
          'são de responsabilidade do profissional que as revisou. '
          'Não foram geradas medições, testes funcionais ou conclusões '
          'automáticas.',style:const pw.TextStyle(fontSize:8.5,color:muted)),
        pw.SizedBox(height:24),
        if(signature!=null)
          pw.Image(signature,height:70,width:210,fit:pw.BoxFit.contain)
        else
          pw.Container(height:26),
        pw.SizedBox(height:5),
        pw.Container(width:220,child:pw.Divider(color:ink,thickness:0.6)),
        pw.Text(_pdfText(draft.technician),
          style:const pw.TextStyle(fontSize:9,color:ink)),
        pw.Text('Assinatura do técnico responsável',
          style:const pw.TextStyle(fontSize:8,color:muted)),
      ],
    ));
    return doc.save();
  }
}

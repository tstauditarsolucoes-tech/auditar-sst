import 'dart:io';

import 'package:flutter/material.dart';
import 'package:printing/printing.dart';

import '../database.dart';
import '../models.dart';
import '../services/auth_service.dart';
import '../services/sst_report_center_history.dart';
import '../services/sst_report_center_models.dart';
import '../services/sst_report_center_pdf.dart';

/// Visita histórica consultável e imprimível; jamais editada no lugar.
class SstFieldArchivedReportScreen extends StatefulWidget {
  const SstFieldArchivedReportScreen({
    super.key,required this.company,required this.userId,
    required this.kind,required this.visitId,required this.history,
  });
  final Company company;
  final String userId,visitId;
  final SstFieldReportKind kind;
  final SstFieldReportHistory history;
  @override
  State<SstFieldArchivedReportScreen> createState()=>
    _SstFieldArchivedReportScreenState();
}

class _SstFieldArchivedReportScreenState
    extends State<SstFieldArchivedReportScreen> {
  SstFieldVisitArchive? archive;
  String? error;
  bool loading=true,printing=false;
  bool get authorized=>AppDatabase.activeUserId.toString()==widget.userId &&
    AuthService.canAccessCompany(widget.company.id);

  @override
  void initState(){super.initState();_load();}

  Future<void> _load() async {
    if(!authorized) {
      if(mounted)setState((){
        loading=false;error='Conta sem acesso ao histórico desta empresa.';
      });
      return;
    }
    try{
      final loaded=await widget.history.open(
        companyId:widget.company.id,userId:widget.userId,
        kind:widget.kind,id:widget.visitId);
      if(mounted&&authorized)setState((){
        archive=loaded;loading=false;
      });
    }catch(_){
      if(mounted)setState((){
        loading=false;error='Não foi possível abrir esta visita local. '
          'O histórico não foi alterado.';
      });
    }
  }

  Future<void> _print()async {
    if(printing||!authorized||archive==null)return;
    setState(()=>printing=true);
    try{
      final value=archive!.draft;
      final bytes=await SstFieldReportPdfService.generate(
        companyName:widget.company.name,
        companyId:widget.company.id,draft:value);
      if(!mounted||!authorized)return;
      await Printing.layoutPdf(onLayout:(_)=>bytes,
        name:'Auditar_SST_Visita_${widget.visitId}.pdf');
    }catch(_){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content:Text(
          'Não foi possível gerar o PDF da visita. Verifique as imagens locais.')));
    }finally{if(mounted)setState(()=>printing=false);}
  }

  @override
  Widget build(BuildContext context){
    final value=archive?.draft;
    final model=SstFieldTemplates.of(widget.kind);
    return Scaffold(
      appBar:AppBar(title:const Text('Visita arquivada • somente leitura')),
      body:loading?const Center(child:CircularProgressIndicator()):
      !authorized?const Center(child:Text('Sem acesso a esta visita.')):
      value==null?Center(child:Text(error??'Visita não encontrada.')):
      SafeArea(child:Center(child:ConstrainedBox(
        constraints:const BoxConstraints(maxWidth:760),
        child:ListView(padding:const EdgeInsets.all(14),children:[
          Text(model.title,style:Theme.of(context).textTheme.titleLarge),
          Text(widget.company.name),
          const SizedBox(height:8),
          const Text('Histórico local preservado. As informações abaixo '
            'não podem ser alteradas nesta tela. Para nova inspeção, '
            'inicie outro rascunho no modelo original.'),
          const SizedBox(height:8),
          ListTile(title:const Text('Data informada da visita'),
            subtitle:Text(value.date)),
          ListTile(title:const Text('Local / setor'),
            subtitle:Text(value.location.isEmpty?'Não informado':value.location)),
          ListTile(title:const Text('Responsável'),
            subtitle:Text(value.technician)),
          ListTile(title:const Text('Itens analisados'),
            subtitle:Text('${value.reviewed}/${model.questions.length}'
              '${value.isPartial?" - relatório parcial":""}')),
          if(widget.kind==SstFieldReportKind.incident)...[
            ListTile(title:const Text('Data/hora do evento'),
              subtitle:Text(value.eventTime)),
            ListTile(title:const Text('Descrição fornecida'),
              subtitle:Text(value.eventNarrative)),
          ],
          for(final question in model.questions)
            if(value.answer(question.id).isReviewed)
              Card(child:Padding(padding:const EdgeInsets.all(12),
                child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
                  Text(question.title,
                    style:const TextStyle(fontWeight:FontWeight.bold)),
                  Text(value.answer(question.id).status.label(
                    investigation:widget.kind==SstFieldReportKind.incident)),
                  if(value.answer(question.id).observation.isNotEmpty)
                    Text('Observação: ${value.answer(question.id).observation}'),
                  if(value.answer(question.id).recommendation.isNotEmpty)
                    Text('Recomendação: '
                      '${value.answer(question.id).recommendation}'),
                  if(value.answer(question.id).photoPaths.isNotEmpty)
                    Wrap(spacing:8,runSpacing:8,children:[
                      for(final path in value.answer(question.id).photoPaths)
                        SizedBox(width:135,height:95,
                          child:Image.file(File(path),fit:BoxFit.contain,
                            errorBuilder:(_,error,stack)=>const Center(
                              child:Text('Foto local indisponível')))),
                    ]),
                ]),
              )),
          const SizedBox(height:12),
          FilledButton.icon(
            onPressed:authorized&&!printing&&value.hasEnoughForPdf?
              _print:null,
            icon:const Icon(Icons.picture_as_pdf_outlined),
            label:Text(printing?'Preparando PDF...':
              'Gerar PDF da visita arquivada')),
          const Text('Fotos e assinatura continuam no armazenamento '
            'deste dispositivo. O histórico não é sincronizado.'),
        ]),
      ))),
    );
  }
}

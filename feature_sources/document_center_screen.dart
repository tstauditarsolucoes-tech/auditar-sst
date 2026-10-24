import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:printing/printing.dart';
import '../database.dart';
import '../models.dart';
import '../services/document_delivery_service.dart';
import '../services/dds_pdf_service.dart';
import '../services/express_round_pdf_service.dart';
import '../services/facial_confirmation_service.dart';
import '../services/improvement_pdf_service.dart';
import '../services/media_sync_service.dart';
import '../services/nc_pdf_service.dart';
import '../services/pdf_service.dart';
import '../services/safety_observation_pdf_service.dart';
import '../services/training_record_pdf_service.dart';
import 'training_records_screen.dart';

class _DocumentEntry {
  final String id, type, title, fileName;
  final DateTime date;
  final Future<Uint8List> Function() pdf;
  final Widget? Function()? open;
  const _DocumentEntry(this.id, this.type, this.title, this.fileName, this.date, this.pdf, [this.open]);
}

/// On-device document index backed by the existing records and PDF generators.
/// Uses the existing report_email_send endpoint. No sync schema changes.
class DocumentCenterScreen extends StatefulWidget {
  final Company company;
  const DocumentCenterScreen({super.key, required this.company});
  @override State<DocumentCenterScreen> createState() => _DocumentCenterState();
}
class _DocumentCenterState extends State<DocumentCenterScreen> {
  List<_DocumentEntry> entries = [];
  List<Map<String,dynamic>> sent = [];
  final Set<String> chosen = {};
  bool loading = true, busy = false;
  String search = '', category = 'Todos', progress = '';
  @override void initState() {super.initState(); _load();}
  DateTime _date(Object? data) => DateTime.tryParse((data ?? '').toString()) ?? DateTime.now();
  String _filename(String type, String id) => type+'_'+id.replaceAll(RegExp(r'[^A-Za-z0-9_-]'),'_')+'.pdf';

  Future<Uint8List> _trainingPdf(SstRecord record) async {
    final rawPeople = record.payload['participants'];
    final rawPhotos = record.payload['photos'];
    final people = rawPeople is List ? rawPeople.whereType<Map>().map((e) => Map<String,dynamic>.from(e)).toList() : <Map<String,dynamic>>[];
    final photos = rawPhotos is List ? rawPhotos.whereType<Map>().map((e) => Map<String,dynamic>.from(e)).toList() : <Map<String,dynamic>>[];
    try {
      await MediaSyncService.restoreTrainingRecordMedia(
        companyId: widget.company.id,
        photoIds: photos.map((e) => (e['id'] ?? '').toString()),
        signatureIds: people.map((e) => (e['signatureId'] ?? '').toString()),
      ).timeout(const Duration(seconds:45));
    } catch (_) {}
    final signatures = <String,String>{};
    final gallery = <String>[];
    for (final item in people) {
      final id = (item['signatureId'] ?? '').toString().trim();
      if (id.isEmpty) continue;
      final face = (item['confirmationMethod'] ?? '').toString() == 'face';
      final path = face
        ? await FacialConfirmationService.localPath(
            companyId: widget.company.id, entityType: 'training_face_signature', confirmationId: id)
        : await MediaSyncService.trainingRecordMediaLocalPath(
            companyId: widget.company.id, entityType: 'training_record_signature', entityId: id);
      if (path != null && path.isNotEmpty) signatures[id] = path;
    }
    for (final item in photos) {
      final id = (item['id'] ?? '').toString().trim();
      if (id.isEmpty) continue;
      final path = await MediaSyncService.trainingRecordMediaLocalPath(
        companyId: widget.company.id, entityType: 'training_record_photo', entityId: id);
      if (path != null && path.isNotEmpty) gallery.add(path);
    }
    return TrainingRecordPdfService.generate(
      company: widget.company, record: record, participants: people,
      signaturePaths: signatures, photoPaths: gallery);
  }

  Future<void> _load() async {
    if (mounted) setState(() => loading = true);
    final db = AppDatabase.instance, id = widget.company.id;
    try {
      final inspections = await db.getInspectionHistory(companyId:id);
      final observations = await db.getSstRecords(type:'OBSERVACAO_SEGURANCA', companyId:id);
      final dds = await db.getSstRecords(type:'DDS', companyId:id);
      final trainings = await db.getSstRecords(type:'TREINAMENTO_SESSAO', companyId:id);
      final improvements = await db.getSstRecords(type:'MELHORIA', companyId:id);
      final ncs = await db.getNonConformityRows(companyId:id, includeClosed:true);
      final sectors = await db.getSectors(id, onlyActive:false);
      final items = <_DocumentEntry>[];
      for (final row in inspections) {
        final recordId = (row['id'] ?? '').toString();
        if (recordId.isEmpty) continue;
        final title = (row['area'] ?? row['checklist_type'] ?? 'Vistoria').toString();
        items.add(_DocumentEntry('inspection:'+recordId,'Vistorias',title,
          _filename('Relatorio_Vistoria',recordId),_date(row['date']),
          () => PdfService.generateInspectionPdf(recordId)));
      }
      final grouped = <String,List<SstRecord>>{}, ordinary = <SstRecord>[];
      for (final record in observations) {
        final round = (record.payload['roundId'] ?? '').toString().trim();
        if (round.isEmpty) {ordinary.add(record);}
        else {grouped.putIfAbsent(round,()=> <SstRecord>[]).add(record);}
      }
      for (final group in grouped.entries) {
        final round = group.key, records = group.value;
        items.add(_DocumentEntry('round:'+round,'Rondas expressas',
          'Ronda expressa • '+records.length.toString()+' registros',
          _filename('Ronda_Expressa',round),records.first.date,() async {
            try {await MediaSyncService.restoreRoundMedia(
              companyId:id,roundId:round).timeout(const Duration(seconds:18));} catch (_) {}
            final all = await db.getSstRecords(type:'OBSERVACAO_SEGURANCA',companyId:id);
            final current = all.where((e) => (e.payload['roundId'] ?? '').toString()==round).toList();
            if (current.isEmpty) throw StateError('Ronda não encontrada.');
            return ExpressRoundPdfService.generate(company:widget.company,
              records:current,sectors:sectors,style:ExpressRoundReportStyle.photographic);
          }));
      }
      if (ordinary.isNotEmpty) {
        items.add(_DocumentEntry('observations:all','Atos e condições',
          'Relatório de atos e condições inseguras',
          _filename('Atos_Condicoes',id),ordinary.first.date,
          () => SafetyObservationPdfService.generate(
            company:widget.company,records:ordinary,sectors:sectors)));
        for (final record in ordinary) {
          items.add(_DocumentEntry('observation:'+record.id,'Atos e condições',
            record.title,_filename('Registro_Seguranca',record.id),record.date,
            () => SafetyObservationPdfService.generate(
              company:widget.company,records:[record],sectors:sectors)));
        }
      }
      for (final record in dds) {
        items.add(_DocumentEntry('dds:'+record.id,'DDS',record.title,
          _filename('Ficha_DDS',record.id),record.date,
          () => DdsPdfService.generate(record)));
      }
      for (final record in trainings) {
        items.add(_DocumentEntry('training:'+record.id,'Treinamentos',record.title,
          _filename('Ficha_Treinamento',record.id),record.date,
          () => _trainingPdf(record),
          () => TrainingRecordDetailScreen(company:widget.company,recordId:record.id)));
      }
      if (improvements.isNotEmpty) {
        items.add(_DocumentEntry('improvements:all','Melhorias','Relatório de melhorias',
          _filename('Relatorio_Melhorias',id),improvements.first.date,
          () => ImprovementPdfService.generate(
            company:widget.company,records:improvements,sectors:sectors)));
      }
      for (final row in ncs) {
        final ncId = (row['id'] ?? '').toString();
        if (ncId.isEmpty) continue;
        items.add(_DocumentEntry('nc:'+ncId,'Não conformidades',
          (row['description'] ?? 'Não conformidade').toString(),
          _filename('Ficha_NC',ncId),_date(row['inspection_date']),
          () => NcPdfService.generate(ncId)));
      }
      items.sort((a,b)=>b.date.compareTo(a.date));
      final history = await DocumentDeliveryService.history(id);
      if (!mounted) return;
      setState(() { entries=items;sent=history;chosen.removeWhere(
        (value)=>!items.any((i)=>i.id==value));loading=false; });
    } catch(error) {
      if (!mounted) return;
      setState(()=>loading=false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Documentos: '+error.toString())));
    }
  }
  List<_DocumentEntry> get visible {
    final text=search.trim().toLowerCase();
    return entries.where((e)=>
      (category=='Todos'||e.type==category) &&
      (text.isEmpty||e.title.toLowerCase().contains(text)||e.type.toLowerCase().contains(text))).toList();
  }
  Future<void> _preview(_DocumentEntry entry) async {
    if(busy)return;
    setState((){busy=true;progress='Preparando PDF...';});
    try{
      final bytes=await entry.pdf();
      await Printing.layoutPdf(onLayout:(_)=>bytes,name:entry.fileName);
    } catch(error) {
      if(mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(error.toString())));
    } finally {
      if(mounted)setState((){busy=false;progress='';});
    }
  }
  Future<void> _send(List<_DocumentEntry> documents) async {
    if(busy||documents.isEmpty)return;
    final to=TextEditingController(text:widget.company.reportEmail);
    final cc=TextEditingController(text:widget.company.secondaryReportEmail);
    final approved=await showDialog<bool>(context:context,builder:(context)=>AlertDialog(
      title:Text('Enviar '+documents.length.toString()+' PDF(s)?'),
      content:Column(mainAxisSize:MainAxisSize.min,children:[
        Text('Empresa: '+widget.company.name),
        const SizedBox(height:12),
        TextField(controller:to,decoration:const InputDecoration(labelText:'Para')),
        TextField(controller:cc,decoration:const InputDecoration(labelText:'Cópia (opcional)')),
        const SizedBox(height:10),
        const Text('Cada PDF será enviado separadamente. Confirme os destinatários.'),
      ]),
      actions:[
        TextButton(onPressed:()=>Navigator.pop(context,false),child:const Text('Cancelar')),
        FilledButton(onPressed:()=>Navigator.pop(context,true),child:const Text('Enviar')),
      ],
    ));
    if(approved!=true||!mounted){to.dispose();cc.dispose();return;}
    final recipient=to.text.trim(),copy=cc.text.trim();
    to.dispose();cc.dispose();
    if(recipient.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Informe o destinatário.')));
      return;
    }
    setState((){busy=true;progress='Preparando envios...';});
    var count=0;String? error;
    for(final document in documents){
      try{
        if(mounted)setState(()=>progress='Enviando '+(count+1).toString()+'/'+documents.length.toString());
        final bytes=await document.pdf();
        await DocumentDeliveryService.send(company:widget.company,
          documentId:document.id,documentType:document.type,title:document.title,
          fileName:document.fileName,bytes:bytes,to:recipient,cc:copy);
        count++;
      }catch(e){error=e.toString();break;}
    }
    final history=await DocumentDeliveryService.history(widget.company.id);
    if(!mounted)return;
    setState((){sent=history;busy=false;progress='';chosen.clear();});
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      duration:const Duration(seconds:8),
      content:Text(error==null
        ? count.toString()+' envio(s) confirmados pela Central.'
        : count.toString()+' envio(s) confirmados. Interrompido: '+error+
          '. Confira o Gmail antes de repetir.')));
  }
  @override Widget build(BuildContext context){
    final categories=<String>{'Todos',...entries.map((e)=>e.type)}.toList();
    final picked=entries.where((e)=>chosen.contains(e.id)).toList();
    return DefaultTabController(length:2,child:Scaffold(
      appBar:AppBar(title:Text('Documentos • '+widget.company.name),
        bottom:const TabBar(tabs:[
          Tab(icon:Icon(Icons.folder_outlined),text:'Documentos'),
          Tab(icon:Icon(Icons.mark_email_read_outlined),text:'Histórico'),
        ]),
        actions:[IconButton(tooltip:'Atualizar',onPressed:busy?null:_load,icon:const Icon(Icons.refresh))]),
      body:loading?const Center(child:CircularProgressIndicator()):TabBarView(children:[
        Column(children:[
          Padding(padding:const EdgeInsets.all(12),child:Column(children:[
            TextField(onChanged:(value)=>setState(()=>search=value),
              decoration:const InputDecoration(labelText:'Pesquisar documento',
                prefixIcon:Icon(Icons.search),border:OutlineInputBorder())),
            const SizedBox(height:8),
            SingleChildScrollView(scrollDirection:Axis.horizontal,child:Row(children:
              categories.map((e)=>Padding(padding:const EdgeInsets.only(right:5),
                child:ChoiceChip(label:Text(e),selected:category==e,
                  onSelected:(_)=>setState(()=>category=e)))).toList())),
          ])),
          if(busy)Column(children:[const LinearProgressIndicator(),Text(progress)]),
          if(chosen.isNotEmpty)FilledButton.icon(
            onPressed:busy?null:()=>_send(picked),icon:const Icon(Icons.send),
            label:Text('Enviar selecionados ('+chosen.length.toString()+')')),
          Expanded(child:visible.isEmpty
            ? const Center(child:Text('Nenhum documento nesta categoria.'))
            : ListView.builder(itemCount:visible.length,itemBuilder:(context,index){
                final item=visible[index];
                return Card(margin:const EdgeInsets.symmetric(horizontal:12,vertical:4),
                  child:ListTile(
                    leading:Checkbox(value:chosen.contains(item.id),
                      onChanged:busy?null:(value)=>setState((){
                        if(value==true){chosen.add(item.id);}else{chosen.remove(item.id);}
                      })),
                    title:Text(item.title,maxLines:2,overflow:TextOverflow.ellipsis),
                    subtitle:Text(item.type+' • '+DateFormat('dd/MM/yyyy').format(item.date)),
                    trailing:PopupMenuButton<String>(enabled:!busy,
                      onSelected:(value){
                        if(value=='preview')_preview(item);
                        if(value=='send')_send([item]);
                        if(value=='open'&&item.open!=null){
                          final page=item.open!();
                          if(page!=null)Navigator.push(context,MaterialPageRoute(builder:(_)=>page));
                        }
                      },
                      itemBuilder:(_)=>[
                        const PopupMenuItem(value:'preview',child:Text('Visualizar PDF')),
                        const PopupMenuItem(value:'send',child:Text('Enviar por e-mail')),
                        if(item.open!=null)const PopupMenuItem(value:'open',child:Text('Abrir ficha original')),
                      ]),
                  ));
              })),
        ]),
        sent.isEmpty?const Center(child:Padding(padding:EdgeInsets.all(25),
          child:Text('Sem envio confirmado neste dispositivo.\n'
            'O histórico da Central permanece na aba EnviosRelatorios da planilha.',
            textAlign:TextAlign.center)))
        :ListView.builder(itemCount:sent.length,itemBuilder:(context,index){
          final item=sent[index],at=_date(item['sentAt']).toLocal();
          return ListTile(leading:const Icon(Icons.mark_email_read,color:Colors.green),
            title:Text((item['title']??'Documento').toString()),
            subtitle:Text((item['documentType']??'PDF').toString()+' • '+
              DateFormat('dd/MM/yyyy HH:mm').format(at)+'\nPara: '+(item['to']??'').toString()),
            trailing:const Icon(Icons.check_circle_outline,color:Colors.green));
        }),
      ]),
    ));
  }
}

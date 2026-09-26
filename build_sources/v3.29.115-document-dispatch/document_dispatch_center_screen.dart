import 'dart:typed_data';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:file_picker/file_picker.dart';
import 'package:printing/printing.dart';

import '../brand.dart';
import '../database.dart';
import '../models.dart';
import '../services/dds_pdf_service.dart';
import '../services/auth_service.dart';
import '../services/document_delivery_service.dart';
import '../services/express_round_pdf_service.dart';
import '../services/facial_confirmation_service.dart';
import '../services/improvement_pdf_service.dart';
import '../services/media_sync_service.dart';
import '../services/nc_pdf_service.dart';
import '../services/pdf_service.dart';
import '../services/report_template_service.dart';
import '../services/safety_observation_pdf_service.dart';
import '../services/training_record_pdf_service.dart';

class _DocumentEntry {
  final String id;
  final String category;
  final String title;
  final String fileName;
  final DateTime date;
  final Future<Uint8List> Function() pdf;
  const _DocumentEntry(this.id, this.category, this.title,
      this.fileName, this.date, this.pdf);
}

/// Catalogue of existing PDF generators plus per-company dispatch timeline.
class DocumentDispatchCenterScreen extends StatefulWidget {
  final String? companyId;
  const DocumentDispatchCenterScreen({super.key, this.companyId});

  @override
  State<DocumentDispatchCenterScreen> createState() => _DocumentDispatchCenterScreenState();
}

class _DocumentDispatchCenterScreenState extends State<DocumentDispatchCenterScreen> {
  List<Company> companies = [];
  Company? company;
  List<_DocumentEntry> documents = [];
  List<Map<String, dynamic>> history = [];
  final Set<String> selected = {};
  bool loading = true;
  bool sending = false;
  bool showHistory = false;
  String search = '';

  @override
  void initState() {
    super.initState();
    _loadCompanies();
  }

  Future<void> _loadCompanies() async {
    if (!AuthService.isSignedIn ||
        AuthService.currentUser?.role.toLowerCase() == 'cliente') {
      if (mounted) setState(() => loading = false);
      return;
    }
    final all = (await AppDatabase.instance.getCompanies(onlyActive: false))
        .where((c) => AuthService.canAccessCompany(c.id)).toList();
    final selectedId = widget.companyId;
    Company? chosen;
    for (final c in all) {
      if (c.id == selectedId) {chosen = c; break;}
    }
    chosen ??= all.isEmpty ? null : all.first;
    if (!mounted) return;
    setState(() {companies = all; company = chosen;});
    await _reload();
  }

  String _filename(String prefix, String identifier) =>
      '${prefix}_${identifier.replaceAll(RegExp(r'[^A-Za-z0-9_-]'), '_')}.pdf';

  List<Map<String, dynamic>> _maps(Object? value) => value is List
      ? value.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList()
      : <Map<String, dynamic>>[];

  Future<Uint8List> _trainingPdf(Company c, SstRecord record) async {
    final participants = _maps(record.payload['participants']);
    final photos = _maps(record.payload['photos']);
    try {
      await MediaSyncService.restoreTrainingRecordMedia(
        companyId: c.id,
        photoIds: photos.map((p) => '${p['id'] ?? ''}'),
        signatureIds: participants.map((p) => '${p['signatureId'] ?? ''}'),
      ).timeout(const Duration(seconds: 35));
    } catch (_) {}
    final signatures = <String, String>{};
    for (final p in participants) {
      final id = '${p['signatureId'] ?? ''}'.trim();
      if (id.isEmpty) continue;
      final method = '${p['confirmationMethod'] ?? 'signature'}';
      final path = method == 'face'
          ? await FacialConfirmationService.localPath(
              companyId: c.id, entityType: 'training_face_signature', confirmationId: id)
          : await MediaSyncService.trainingRecordMediaLocalPath(
              companyId: c.id, entityType: 'training_record_signature', entityId: id);
      if (path != null && path.isNotEmpty) signatures[id] = path;
    }
    final paths = <String>[];
    for (final p in photos) {
      final id = '${p['id'] ?? ''}'.trim();
      if (id.isEmpty) continue;
      final path = await MediaSyncService.trainingRecordMediaLocalPath(
          companyId: c.id, entityType: 'training_record_photo', entityId: id);
      if (path != null && path.isNotEmpty) paths.add(path);
    }
    return TrainingRecordPdfService.generate(company: c, record: record,
      participants: participants, signaturePaths: signatures, photoPaths: paths);
  }

  Future<void> _reload() async {
    final c = company;
    if (c == null) {
      if (mounted) setState(() {documents = []; history = []; loading = false;});
      return;
    }
    setState(() {loading = true; selected.clear();});
    final db = AppDatabase.instance;
    final items = <_DocumentEntry>[];
    final inspectionRows = await db.getInspectionHistory(companyId: c.id);
    for (final row in inspectionRows) {
      final id = '${row['id'] ?? ''}';
      if (id.isEmpty) continue;
      final date = DateTime.tryParse('${row['date'] ?? ''}') ?? DateTime.now();
      final label = '${row['area'] ?? row['checklist_type'] ?? 'Vistoria'}'.trim();
      items.add(_DocumentEntry('inspection:$id','Vistoria', 'Vistoria • $label',
        _filename('Vistoria_${c.name}', id), date,
        () => PdfService.generateInspectionPdf(id)));
      items.add(_DocumentEntry('executive:$id','Relatório executivo','Resumo executivo • $label',
        _filename('Executivo_${c.name}', id), date,
        () => PdfService.generateInspectionPdf(id, executive: true)));
    }
    final dds = await db.getSstRecords(type: 'DDS', companyId: c.id);
    for (final record in dds) {
      items.add(_DocumentEntry('dds:${record.id}', 'DDS', 'Ficha de DDS • ${record.title}',
          _filename('Ficha_DDS', record.id), record.date,
          () => DdsPdfService.generate(record)));
    }
    final trainings = await db.getSstRecords(type: 'TREINAMENTO_SESSAO', companyId: c.id);
    for (final record in trainings) {
      items.add(_DocumentEntry('training:${record.id}', 'Treinamento',
          'Ficha de treinamento • ${record.title}', _filename('Ficha_Treinamento', record.id),
          record.date, () => _trainingPdf(c, record)));
    }
    final sectors = await db.getSectors(c.id, onlyActive: false);
    final observations = await db.getSstRecords(type:'OBSERVACAO_SEGURANCA', companyId: c.id);
    final rounds = <String,List<SstRecord>>{};
    for (final record in observations) {
      final roundId = '${record.payload['roundId'] ?? ''}'.trim();
      if (roundId.isNotEmpty) {
        rounds.putIfAbsent(roundId, () => <SstRecord>[]).add(record);
      } else {
        final kind = '${record.payload['observationKind'] ?? 'Condição insegura'}';
        items.add(_DocumentEntry('observation:${record.id}',kind,
          '$kind • ${record.title}', _filename('Registro_Seguranca',record.id),
          record.date, () => SafetyObservationPdfService.generate(
            company:c, records:[record], sectors:sectors)));
      }
    }
    final template = await ReportTemplateService.selectedForCompany(c.id);
    for (final group in rounds.entries) {
      final records = group.value;
      items.add(_DocumentEntry('round:${group.key}', 'Ronda Expressa',
        'Ronda Expressa • ${records.length} registro(s)',
        _filename('Ronda_Expressa',group.key), records.first.date,
        () => ExpressRoundPdfService.generate(company:c, records:records, sectors:sectors,
          style:ExpressRoundReportStyle.photographic, template:template)));
    }
    final improvements = await db.getSstRecords(type:'MELHORIA', companyId:c.id);
    if (improvements.isNotEmpty) {
      items.add(_DocumentEntry('improvements:${c.id}','Melhorias',
        'Relatório de melhorias',_filename('Melhorias',c.id),DateTime.now(),
        () => ImprovementPdfService.generate(company:c, records:improvements,sectors:sectors)));
    }
    final ncs = await db.getNonConformityRows(companyId:c.id,includeClosed:true);
    for (final row in ncs) {
      final id = '${row['id'] ?? ''}';
      if (id.isEmpty) continue;
      items.add(_DocumentEntry('nc:$id','Não conformidade',
        'NC • ${row['code'] ?? id}',_filename('Ficha_NC',id),
        DateTime.tryParse('${row['created_at'] ?? ''}') ?? DateTime.now(),
        () => NcPdfService.generate(id)));
    }
    items.sort((a,b)=>b.date.compareTo(a.date));
    // The combined safety report uses the existing PDF generator, including
    // cases where the records were created in different screens.
    if (observations.isNotEmpty) {
      items.add(_DocumentEntry('safety:${c.id}', 'Atos e condições inseguras',
        'Relatório de atos e condições', _filename('Atos_Condicoes', c.id), DateTime.now(),
        () => SafetyObservationPdfService.generate(
          company: c, records: observations, sectors: sectors)));
    }
    final sent = await DocumentDeliveryService.history(c.id);
    if (!mounted || company?.id != c.id) return;
    setState(() { documents = items; history = sent; loading = false; });
  }

  Future<void> _sendSelected() async {
    final c = company;
    if (c == null || sending || selected.isEmpty) return;
    if (c.reportEmail.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:
        Text('Cadastre o e-mail de relatórios na ficha da empresa.')));
      return;
    }
    final targets = documents.where((d) => selected.contains(d.id)).toList();
    if (targets.length > 10) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:
        Text('Selecione até 10 documentos por envio para evitar bloqueio por limite do Gmail.')));
      return;
    }
    final ok = await showDialog<bool>(context:context,builder:(dialogContext)=>AlertDialog(
      title:Text('Enviar ${targets.length} documento(s)?'),
      content:Text('Empresa: ${c.name}\nPara: ${c.reportEmail}\n'
        '${c.secondaryReportEmail.trim().isEmpty ? '' : 'Cópia: ${c.secondaryReportEmail}\n'}'
        'Cada documento será enviado em um e-mail individual, com seu PDF anexado.'),
      actions:[TextButton(onPressed:()=>Navigator.pop(dialogContext,false),child:const Text('Cancelar')),
      FilledButton(onPressed:()=>Navigator.pop(dialogContext,true),child:const Text('Confirmar envio'))]));
    if (ok != true || !mounted) return;
    setState(()=>sending=true);
    var successful=0;
    final errors=<String>[];
    for (final item in targets) {
      try {
        final bytes=await item.pdf();
        await DocumentDeliveryService.send(companyId:c.id,companyName:c.name,
          documentId:item.id,category:item.category,title:item.title,
          to:c.reportEmail,cc:c.secondaryReportEmail,fileName:item.fileName,bytes:bytes);
        successful++;
      } catch(error) { errors.add('${item.title}: $error'); }
    }
    if (mounted) {
      setState(()=>sending=false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(
        '$successful de ${targets.length} envio(s) confirmado(s) pela Central.'
        '${errors.isEmpty ? '' : ' Primeiro erro: ${errors.first}'}')));
      await _reload();
    }
  }

  Future<void> _sendReadyPdf() async {
    final c = company;
    if (c == null || sending) return;
    if (c.reportEmail.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:
        Text('Cadastre o e-mail de relatórios na empresa.')));
      return;
    }
    try {
      final picked = await FilePicker.platform.pickFiles(
        type: FileType.custom, allowedExtensions: const ['pdf'],
        allowMultiple: true, withData: false,
      );
      if (picked == null || picked.files.isEmpty || !mounted) return;
      if (picked.files.length > 10) throw StateError('Selecione até 10 PDFs de cada vez.');
      final files = picked.files;
      final confirmed = await showDialog<bool>(context: context,
        builder: (dialogContext) => AlertDialog(
          title: Text('Enviar ${files.length} PDF(s)?'),
          content: Text('Empresa: ${c.name}\nPara: ${c.reportEmail}\n'
            'Os arquivos existentes serão encaminhados individualmente como anexos.'),
          actions: [TextButton(onPressed: () => Navigator.pop(dialogContext,false),
              child: const Text('Cancelar')),
            FilledButton(onPressed: () => Navigator.pop(dialogContext,true),
              child: const Text('Confirmar'))],
        ),
      );
      if (confirmed != true || !mounted) return;
      setState(() => sending = true);
      var accepted = 0;
      final errors = <String>[];
      for (final f in files) {
        try {
          if (f.size <= 0 || f.size > 7500000) {
            throw StateError('Arquivo vazio ou acima de 7 MB.');
          }
          final path = f.path;
          if (path == null || path.isEmpty) {
            throw StateError('Arquivo indisponível para leitura.');
          }
          final bytes = await File(path).readAsBytes();
          final name = f.name;
          if (bytes.length < 5 || bytes.length > 7500000 ||
              !name.toLowerCase().endsWith('.pdf') ||
              String.fromCharCodes(bytes.take(4)) != '%PDF') {
            throw StateError('Arquivo inválido ou não é um PDF de até 7 MB.');
          }
          await DocumentDeliveryService.send(
            companyId: c.id, companyName: c.name,
            documentId: 'pdf:${DateTime.now().microsecondsSinceEpoch}',
            category: 'PDF avulso', title: name, to: c.reportEmail,
            cc: c.secondaryReportEmail, fileName: name, bytes: bytes);
          accepted++;
        } catch (error) {errors.add('${f.name}: $error');}
      }
      if (!mounted) return;
      setState(() => sending = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(
        '$accepted de ${files.length} PDF(s) aceito(s) pela Central.'
        '${errors.isEmpty ? '' : ' Primeiro erro: ${errors.first}'}')));
      await _reload();
    } catch (error) {
      if (mounted) {
        setState(() => sending = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Não foi possível enviar o PDF: $error')));
      }
    }
  }

  Future<void> _preview(_DocumentEntry entry) async {
    try {
      final bytes=await entry.pdf();
      await Printing.layoutPdf(onLayout:(_)=>bytes,name:entry.fileName);
    } catch(error) {
      if(mounted) ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content:Text('Não foi possível abrir o documento: $error')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final displayed=documents.where((d)=>search.isEmpty ||
      ('${d.category} ${d.title}').toLowerCase().contains(search.toLowerCase())).toList();
    return Scaffold(
      appBar:AppBar(title:const Text('Central de documentos e envios'),actions:[
        IconButton(tooltip:'Atualizar histórico',onPressed:sending?null:_reload,
          icon:const Icon(Icons.refresh_rounded))]),
      body: companies.isEmpty && !loading
        ? const Center(child: Text('Nenhuma empresa disponível para esta conta.'))
        : Column(children:[
        Padding(padding:const EdgeInsets.fromLTRB(16,12,16,6),child:DropdownButtonFormField<String>(
          value:company?.id,
          decoration:const InputDecoration(labelText:'Empresa',border:OutlineInputBorder()),
          items:companies.map((c)=>DropdownMenuItem(value:c.id,child:Text(c.name,
            overflow:TextOverflow.ellipsis))).toList(),
          onChanged:sending?null:(id){setState(()=>company=companies.firstWhere((c)=>c.id==id));_reload();})),
        Padding(padding:const EdgeInsets.symmetric(horizontal:16),child:Row(children:[
          Expanded(child:ChoiceChip(label:const Text('Documentos'),selected:!showHistory,
            onSelected:(_)=>setState(()=>showHistory=false))),
          const SizedBox(width:12),
          Expanded(child:ChoiceChip(label:const Text('Histórico de envios'),selected:showHistory,
            onSelected:(_)=>setState(()=>showHistory=true))),
        ])),
        if(!showHistory) Padding(padding:const EdgeInsets.fromLTRB(16,6,16,4),child:
          TextField(onChanged:(value)=>setState(()=>search=value),
            decoration:const InputDecoration(prefixIcon:Icon(Icons.search),hintText:'Buscar vistoria, DDS, treinamento, NC...',
              border:OutlineInputBorder(),isDense:true))),
        if (!showHistory) Padding(padding: const EdgeInsets.symmetric(horizontal:16,vertical:4),
          child: SizedBox(width:double.infinity,child:OutlinedButton.icon(
            onPressed:sending?null:_sendReadyPdf,
            icon:const Icon(Icons.upload_file_outlined),
            label:const Text('Enviar PDF pronto (PGR, LTCAT, PGRSS, laudos...)')))),
        if(!showHistory && selected.isNotEmpty)
          Padding(padding:const EdgeInsets.symmetric(horizontal:16,vertical:4),child:
            SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:sending?null:_sendSelected,
              icon:const Icon(Icons.mark_email_read_outlined),
              label:Text(sending?'Enviando...':'Enviar ${selected.length} selecionado(s)')))),
        Expanded(child:loading?const Center(child:CircularProgressIndicator()):
          showHistory
            ? history.isEmpty?const Center(child:Text('Nenhum envio registrado para esta empresa.'))
              :ListView.builder(itemCount:history.length,itemBuilder:(context,index){
                final r=history[index];final sent='${r['status'] ?? ''}'=='SENT';
                return ListTile(leading:Icon(sent?Icons.mark_email_read_outlined:Icons.error_outline,
                  color:sent?AuditarBrand.greenDark:Colors.orange),
                  title:Text('${r['title'] ?? r['fileName'] ?? 'Documento'}'),
                  subtitle:Text('${r['to'] ?? ''}\n${r['createdAt'] ?? ''}'
                    '${'${r['error'] ?? ''}'.isEmpty ? '' : '\n${r['error']}'}'),
                  isThreeLine:true,trailing:Text(sent?'ENVIADO':'FALHOU'));
              })
            :displayed.isEmpty?const Center(child:Text('Nenhum documento gerável para esta empresa.'))
              :ListView.builder(itemCount:displayed.length,itemBuilder:(context,index){
                final d=displayed[index];final checked=selected.contains(d.id);
                return Card(margin:const EdgeInsets.symmetric(horizontal:12,vertical:4),child:
                  ListTile(leading:Checkbox(value:checked,onChanged:sending?null:(value)=>setState((){
                    if(value==true){selected.add(d.id);}else{selected.remove(d.id);}
                  })),title:Text(d.title),subtitle:Text('${d.category} • ${DateFormat('dd/MM/yyyy').format(d.date)}'),
                    onTap:sending?null:()=>setState(()=>checked?selected.remove(d.id):selected.add(d.id)),
                    trailing:IconButton(tooltip:'Visualizar PDF',icon:const Icon(Icons.picture_as_pdf_outlined),
                      onPressed:sending?null:()=>_preview(d))));
              })),
      ]),
    );
  }
}
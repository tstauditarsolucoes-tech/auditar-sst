import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:printing/printing.dart';
import 'package:signature/signature.dart';

import '../database.dart';
import '../models.dart';
import '../services/auth_service.dart';
import '../services/offline_sst_deep_catalog_v2.dart';
import '../services/sst_report_center_models.dart';
import '../services/sst_report_center_pdf.dart';
import 'manager_reports_screen.dart';
import 'express_round_screen.dart';
import 'new_inspection_screen.dart';

/// Entrada única, vinculada à empresa atual, sem criar base de dados paralela.
class SstReportCenterScreen extends StatelessWidget {
  const SstReportCenterScreen({super.key,required this.company});
  final Company company;

  static IconData _icon(SstFieldReportKind kind) {
    switch(kind){
      case SstFieldReportKind.nr12:return Icons.precision_manufacturing_outlined;
      case SstFieldReportKind.nr18:return Icons.construction_outlined;
      case SstFieldReportKind.nr10:return Icons.bolt_outlined;
      case SstFieldReportKind.nr35:return Icons.health_and_safety_outlined;
      case SstFieldReportKind.incident:return Icons.assignment_late_outlined;
      case SstFieldReportKind.monthly:return Icons.assessment_outlined;
    }
  }

  @override
  Widget build(BuildContext context) {
    final allowed=AuthService.canAccessCompany(company.id);
    return Scaffold(
      appBar:AppBar(title:const Text('Central de Relatórios SST')),
      body:SafeArea(child:Center(child:ConstrainedBox(
        constraints:const BoxConstraints(maxWidth:760),
        child:ListView(padding:const EdgeInsets.all(14),children:[
          Text(company.name,style:Theme.of(context).textTheme.titleLarge),
          const SizedBox(height:8),
          const Text('Escolha o modelo. Os roteiros de inspeção são preenchidos '
            'offline, com rascunho por empresa e usuário. Os PDFs usam somente '
            'dados revisados. Os registros de vistoria existentes não são alterados.'),
          const SizedBox(height:12),
          Card(child:Padding(padding:const EdgeInsets.all(12),
            child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
              Text('Registros que já existem no Auditar SST',
                style:Theme.of(context).textTheme.titleMedium),
              const SizedBox(height:8),
              Wrap(spacing:8,runSpacing:8,children:[
                OutlinedButton.icon(
                  onPressed:allowed?()=>Navigator.of(context).push(
                    MaterialPageRoute<void>(builder:(_)=>
                      ExpressRoundScreen(company:company))):null,
                  icon:const Icon(Icons.add_a_photo_outlined),
                  label:const Text('Ronda Expressa')),
                OutlinedButton.icon(
                  onPressed:allowed?()=>Navigator.of(context).push(
                    MaterialPageRoute<void>(builder:(_)=>
                      NewInspectionScreen(initialCompany:company,
                        fieldMode:true))):null,
                  icon:const Icon(Icons.fact_check_outlined),
                  label:const Text('Vistoria')),
              ]),
            ]),
          )),
          const SizedBox(height:10),
          if(!allowed)const Card(child:ListTile(
            leading:Icon(Icons.lock_outlined),
            title:Text('Sem permissão para esta empresa'),
          )),
          for(final model in SstFieldTemplates.models)
            Card(child:ListTile(
              leading:Icon(_icon(model.kind),size:28),
              title:Text(model.title,
                style:const TextStyle(fontWeight:FontWeight.w700)),
              subtitle:Text(model.subtitle),
              trailing:const Icon(Icons.chevron_right),
              enabled:allowed,
              onTap:allowed?()=>Navigator.of(context).push(
                MaterialPageRoute<void>(builder:(_)=>
                  SstFieldReportScreen(company:company,model:model))):null,
            )),
          Card(child:ListTile(
            leading:const Icon(Icons.assessment_outlined,size:28),
            title:const Text('Relatório gerencial mensal',
              style:TextStyle(fontWeight:FontWeight.w700)),
            subtitle:const Text('Usa os registros já existentes de NC, '
              'ações, inspeções e atividades da empresa.'),
            trailing:const Icon(Icons.chevron_right),
            enabled:allowed,
            onTap:allowed?()=>Navigator.of(context).push(
              MaterialPageRoute<void>(builder:(_)=>
                ManagerReportsScreen(company:company,
                  initialKind:ManagerReportKind.monthly))):null,
          )),
          const Padding(padding:EdgeInsets.all(8),
            child:Text('Os modelos são roteiros de campo. A referência à NR '
              'não significa enquadramento automático. Inspeções elétricas '
              'não são laudos ou medições; investigação não substitui CAT.')),
        ]),
      ))),
    );
  }
}

class SstFieldDraftStore {
  const SstFieldDraftStore._();
  static String key(String companyId,String userId,SstFieldReportKind kind)=>
    'field_report_v1_'+Uri.encodeComponent(userId)+'_'+
      Uri.encodeComponent(companyId)+'_'+kind.name;
  static Future<SstFieldDraft> load(String companyId,
    String userId,SstFieldReportKind kind) async {
    final raw=await AppDatabase.instance.getSetting(key(companyId,userId,kind));
    if(raw.trim().isEmpty)return SstFieldDraft(
      kind:kind,companyId:companyId,
      date:DateTime.now().toIso8601String(),
    );
    final decoded=jsonDecode(raw);
    if(decoded is! Map)throw const FormatException('Rascunho local inválido');
    return SstFieldDraft.fromJson(
      Map<String,dynamic>.from(decoded),
      expectedKind:kind,expectedCompanyId:companyId);
  }
  static Future<void> save(SstFieldDraft draft,String userId)=>
    AppDatabase.instance.setSetting(
      key(draft.companyId,userId,draft.kind),jsonEncode(draft.toJson()));
}

/// Anotações e fotos locais não criam NC, CAT, assinatura de laudo ou
/// atualização em registros existentes. Só a ação do técnico gera o PDF.
class SstFieldReportScreen extends StatefulWidget {
  const SstFieldReportScreen({
    super.key,required this.company,required this.model,
  });
  final Company company;
  final SstFieldTemplate model;
  @override
  State<SstFieldReportScreen> createState()=>_SstFieldReportScreenState();
}
class _SstFieldReportScreenState extends State<SstFieldReportScreen> {
  late SstFieldDraft draft=SstFieldDraft(
    kind:widget.model.kind,companyId:widget.company.id);
  bool loading=true,exporting=false,saveFailed=false;
  int outstanding=0;
  String? error,ownerUser;
  Future<void> pending=Future<void>.value();
  bool get isIncident=>widget.model.kind==SstFieldReportKind.incident;
  bool get authorized=>ownerUser!=null&&
    ownerUser==AppDatabase.activeUserId.toString()&&
    AuthService.canAccessCompany(widget.company.id);
  @override
  void initState(){super.initState();_load();}

  Future<void> _load()async {
    if(!AuthService.canAccessCompany(widget.company.id)){
      if(mounted)setState((){
        loading=false;error='Sem acesso à empresa selecionada.';
      });
      return;
    }
    final uid=AppDatabase.activeUserId.toString();
    try {
      final current=await SstFieldDraftStore.load(
        widget.company.id,uid,widget.model.kind);
      if(mounted)setState((){
        ownerUser=uid;draft=current;loading=false;error=null;
      });
    } catch (_) {
      if(mounted)setState((){
        loading=false;error='O rascunho não pôde ser aberto. '
          'Nenhum registro existente foi sobrescrito.';
      });
    }
  }

  void _update(SstFieldDraft next){
    if(!authorized)return;
    final uid=ownerUser!;
    setState((){
      draft=next;outstanding++;error=null;saveFailed=false;
    });
    pending=pending.then((_)async {
      if(uid!=AppDatabase.activeUserId.toString()||
         !AuthService.canAccessCompany(widget.company.id)){
        throw StateError('A conta ou empresa ativa mudou.');
      }
      await SstFieldDraftStore.save(next,uid);
    }).catchError((_){
      if(mounted)setState((){
        saveFailed=true;
        error='Erro ao salvar rascunho local. '
          'Não feche sem conferir o salvamento.';
      });
    }).whenComplete((){
      if(mounted)setState(()=>outstanding--);
    });
  }

  Future<String?> _textDialog(String title,String label,
      String current,{int max=1600,int min=0}) async {
    final input=TextEditingController(text:current);
    final result=await showDialog<String>(
      context:context,builder:(dialog)=>StatefulBuilder(
        builder:(context,refresh)=>AlertDialog(
          title:Text(title),
          content:ConstrainedBox(
            constraints:const BoxConstraints(maxWidth:520),
            child:SingleChildScrollView(child:TextField(
              controller:input,maxLength:max,maxLines:5,
              autofocus:true,onChanged:(_)=>refresh((){}),
              decoration:InputDecoration(
                labelText:label,border:const OutlineInputBorder()),
            ))),
          actions:[
            TextButton(onPressed:()=>Navigator.pop(dialog),
              child:const Text('Cancelar')),
            FilledButton(
              onPressed:input.text.trim().length<min?null:
                ()=>Navigator.pop(dialog,input.text.trim()),
              child:const Text('Salvar')),
          ],
        ),
      ),
    );
    WidgetsBinding.instance.addPostFrameCallback((_)=>input.dispose());
    return result;
  }

  Future<void> _editQuestion(SstFieldQuestion q) async {
    if(!authorized)return;
    final before=draft.answer(q.id);
    final note=TextEditingController(text:before.observation);
    final recommendation=TextEditingController(text:before.recommendation);
    final changed=await showDialog<bool>(
      context:context,builder:(dialog)=>StatefulBuilder(
        builder:(context,refresh){
          final matches=OfflineSstDeepCatalog.matches(note.text);
          return AlertDialog(
            title:Text(q.title),
            content:SizedBox(width:520,child:SingleChildScrollView(
              child:Column(mainAxisSize:MainAxisSize.min,
                crossAxisAlignment:CrossAxisAlignment.stretch,children:[
                Text(q.prompt),
                const SizedBox(height:12),
                TextField(controller:note,maxLines:5,maxLength:1800,
                  onChanged:(_)=>refresh((){}),
                  decoration:const InputDecoration(
                    labelText:'Situação realmente verificada / fontes',
                    border:OutlineInputBorder(),
                  )),
                if(!isIncident && matches.isNotEmpty)
                  Align(alignment:Alignment.centerLeft,
                    child:TextButton.icon(
                      onPressed:()async{
                        final selected=matches.first;
                        final confirm=await showDialog<bool>(
                          context:dialog,builder:(c)=>AlertDialog(
                            title:const Text('Utilizar esta recomendação?'),
                            content:SingleChildScrollView(child:Text(
                              (selected['title']??'')+'\n\n'+
                              (selected['recommendation']??'')+
                              '\n\nReferência temática: '+
                              (selected['nr']??'')+
                              '\nConfira antes de registrar.')),
                            actions:[
                              TextButton(onPressed:()=>Navigator.pop(c,false),
                                child:const Text('Cancelar')),
                              FilledButton(onPressed:()=>Navigator.pop(c,true),
                                child:const Text('Usar após revisão')),
                            ],
                          ));
                        if(confirm==true){
                          recommendation.text=selected['recommendation']??'';
                          refresh((){});
                        }
                      },
                      icon:const Icon(Icons.lightbulb_outline),
                      label:const Text('Sugestão offline de recomendação'),
                    )),
                TextField(controller:recommendation,maxLines:4,maxLength:1200,
                  decoration:InputDecoration(
                    labelText:isIncident?'Medida preventiva / encaminhamento':
                      'Recomendação do técnico (editável)',
                    border:const OutlineInputBorder(),
                  )),
              ]))),
            actions:[
              TextButton(onPressed:()=>Navigator.pop(dialog,false),
                child:const Text('Cancelar')),
              FilledButton(
                onPressed:()=>Navigator.pop(dialog,true),
                child:const Text('Salvar texto revisado')),
            ],
          );
        }));
    final revisedNote=note.text.trim();
    final revisedRecommendation=recommendation.text.trim();
    WidgetsBinding.instance.addPostFrameCallback((_){
      note.dispose();recommendation.dispose();
    });
    if(changed==true&&mounted&&authorized) {
      _update(draft.update(q.id,before.copyWith(
        observation:revisedNote,recommendation:revisedRecommendation)));
    }
  }

  Future<Directory> _mediaFolder()async {
    final root=await getApplicationDocumentsDirectory();
    // IDs permanecem no armazenamento privado, sem upload.
    final key=[ownerUser!,widget.company.id,widget.model.kind.name]
      .map((s)=>s.replaceAll(RegExp(r'[^a-zA-Z0-9_-]'),'_')).join('_');
    final folder=Directory(root.path+'/auditar_sst_field_reports/'+key);
    if(!await folder.exists())await folder.create(recursive:true);
    return folder;
  }

  Future<void> _addPhoto(SstFieldQuestion question,ImageSource source)async {
    if(!authorized)return;
    final before=draft.answer(question.id);
    if(before.photoPaths.length>=2){
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content:Text('Limite de duas fotos por item. Remova uma antes.')));
      return;
    }
    try {
      final file=await ImagePicker().pickImage(
        source:source,maxWidth:1600,imageQuality:75);
      if(file==null||!mounted||!authorized)return;
      final folder=await _mediaFolder();
      final timestamp=DateTime.now().microsecondsSinceEpoch;
      final target=File(folder.path+'/'+question.id+'_'+
        timestamp.toString()+'.jpg');
      await File(file.path).copy(target.path);
      if(await target.length()>7*1024*1024) {
        await target.delete();
        throw StateError('A fotografia excedeu 7 MB.');
      }
      if(!mounted||!authorized){
        await target.delete();
        return;
      }
      final now=draft.answer(question.id);
      _update(draft.update(question.id,now.copyWith(
        photoPaths:[...now.photoPaths,target.path])));
    } catch (_) {
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content:Text('Não foi possível anexar a foto. '
          'Confira o arquivo e a permissão da câmera.')));
    }
  }

  void _removePhoto(SstFieldQuestion question,String path){
    if(!authorized)return;
    final before=draft.answer(question.id);
    _update(draft.update(question.id,before.copyWith(
      photoPaths:before.photoPaths.where((p)=>p!=path).toList())));
    // Preservar o arquivo até possível recuperação, sem excluir evidências.
  }

  Future<void> _sign()async {
    if(!authorized)return;
    final controller=SignatureController(
      penStrokeWidth:3,penColor:Colors.black,
      exportBackgroundColor:Colors.white,
    );
    final accepted=await showDialog<bool>(context:context,
      builder:(dialog)=>AlertDialog(
        title:const Text('Assinatura do técnico'),
        content:SizedBox(width:420,height:240,child:Column(children:[
          const Text('Assine somente após revisar o conteúdo. '
            'A assinatura não substitui habilitação ou responsabilidade legal.'),
          const SizedBox(height:8),
          Expanded(child:Signature(
            controller:controller,backgroundColor:Colors.white)),
        ])),
        actions:[
          TextButton(onPressed:()=>controller.clear(),
            child:const Text('Limpar')),
          TextButton(onPressed:()=>Navigator.pop(dialog,false),
            child:const Text('Cancelar')),
          FilledButton(onPressed:()=>Navigator.pop(dialog,true),
            child:const Text('Utilizar assinatura')),
        ],
      ));
    try {
      if(accepted==true&&mounted&&authorized&&controller.isNotEmpty) {
        final bytes=await controller.toPngBytes();
        if(bytes==null||bytes.isEmpty)throw StateError('Assinatura vazia.');
        final folder=await _mediaFolder();
        final path=folder.path+'/assinatura_tecnico.png';
        await File(path).writeAsBytes(bytes,flush:true);
        if(mounted&&authorized)_update(draft.copyWith(signaturePath:path));
      }
    } catch (_) {
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content:Text('Não foi possível salvar a assinatura.')));
    } finally {
      controller.dispose();
    }
  }

  Future<void> _export()async{
    if(exporting||!authorized)return;
    setState(()=>exporting=true);
    try {
      await pending;
      if(!authorized||saveFailed||!draft.hasEnoughForPdf)throw StateError(
        'Preencha técnico, data e ao menos um item; descreva '
        'situações não conformes ou informações de ocorrência antes do PDF.');
      final bytes=await SstFieldReportPdfService.generate(
        companyName:widget.company.name,
        companyId:widget.company.id,draft:draft);
      if(!mounted||!authorized)return;
      final name='Auditar_SST_'+widget.model.kind.name+'_'+
        DateTime.now().year.toString()+'.pdf';
      await Printing.layoutPdf(onLayout:(_)=>bytes,name:name);
    } catch (e) {
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content:Text(e.toString())));
    } finally {if(mounted)setState(()=>exporting=false);}
  }

  Widget _questionCard(SstFieldQuestion question){
    final answer=draft.answer(question.id);
    final values=isIncident?
      <SstFieldStatus>[SstFieldStatus.notChecked,
        SstFieldStatus.documented,SstFieldStatus.notApplicable]:
      <SstFieldStatus>[SstFieldStatus.notChecked,
        SstFieldStatus.conforming,SstFieldStatus.nonConforming,
        SstFieldStatus.notApplicable];
    final needsDetail=answer.status==SstFieldStatus.nonConforming ||
        (isIncident&&answer.status==SstFieldStatus.documented);
    return Card(child:Padding(padding:const EdgeInsets.all(13),
      child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
        Text(question.group.toUpperCase(),
          style:TextStyle(color:Theme.of(context).colorScheme.primary,
            fontSize:11,fontWeight:FontWeight.bold)),
        const SizedBox(height:3),
        Text(question.title,
          style:const TextStyle(fontWeight:FontWeight.w700,fontSize:16)),
        const SizedBox(height:4),
        Text(question.prompt),
        const SizedBox(height:12),
        DropdownButtonFormField<SstFieldStatus>(
          key:ValueKey('sst-report-status-'+question.id),
          value:answer.status,isExpanded:true,
          decoration:const InputDecoration(
            labelText:'Resultado da verificação',border:OutlineInputBorder()),
          items:values.map((v)=>DropdownMenuItem(
            value:v,child:Text(v.label(investigation:isIncident)))).toList(),
          onChanged:authorized?(v){
            if(v!=null)_update(draft.update(
              question.id,answer.copyWith(status:v)));
          }:null,
        ),
        if(needsDetail&&answer.observation.trim().length<8)
          const Padding(padding:EdgeInsets.only(top:8),
            child:Text('Descreva o fato observado antes de gerar o PDF.',
              style:TextStyle(fontWeight:FontWeight.w700))),
        if(answer.observation.isNotEmpty)...[
          const SizedBox(height:8),
          Text('Observação: '+answer.observation,
            maxLines:5,overflow:TextOverflow.ellipsis),
        ],
        if(answer.recommendation.isNotEmpty)
          Text('Recomendação: '+answer.recommendation,
            maxLines:4,overflow:TextOverflow.ellipsis),
        const SizedBox(height:6),
        Wrap(spacing:6,runSpacing:6,children:[
          OutlinedButton.icon(
            onPressed:authorized?()=>_editQuestion(question):null,
            icon:const Icon(Icons.edit_note_outlined),
            label:Text(answer.observation.isEmpty?
              'Registrar observação':'Editar texto'),
          ),
          if(answer.photoPaths.length<2)...[
            OutlinedButton.icon(
              onPressed:authorized?()=>_addPhoto(
                question,ImageSource.gallery):null,
              icon:const Icon(Icons.photo_library_outlined),
              label:const Text('Anexar foto'),
            ),
            if(!Platform.isWindows)OutlinedButton.icon(
              onPressed:authorized?()=>_addPhoto(
                question,ImageSource.camera):null,
              icon:const Icon(Icons.camera_alt_outlined),
              label:const Text('Câmera'),
            ),
          ],
        ]),
        if(answer.photoPaths.isNotEmpty)
          Padding(padding:const EdgeInsets.only(top:8),
            child:Wrap(spacing:10,runSpacing:10,children:[
              for(final path in answer.photoPaths)
                Column(mainAxisSize:MainAxisSize.min,children:[
                  SizedBox(width:135,height:96,
                    child:Image.file(File(path),fit:BoxFit.cover,
                      errorBuilder:(_,__,___)=>const Center(
                        child:Text('Foto não localizada')))),
                  TextButton(
                    onPressed:authorized?()=>_removePhoto(question,path):null,
                    child:const Text('Remover vínculo')),
                ]),
            ]),
          ),
      ]),
    ));
  }

  @override
  Widget build(BuildContext context){
    if(loading)return Scaffold(
      appBar:AppBar(title:Text(widget.model.title)),
      body:const Center(child:CircularProgressIndicator()));
    if(ownerUser==null)return Scaffold(
      appBar:AppBar(title:Text(widget.model.title)),
      body:Center(child:Padding(padding:const EdgeInsets.all(20),
        child:Text(error??'Não foi possível abrir o relatório.'))));
    return PopScope(
      canPop:outstanding==0&&!exporting&&!saveFailed,
      onPopInvokedWithResult:(didPop,result){
        if(!didPop)ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content:Text('Salvando o rascunho local; confira '
            'o indicador antes de sair.')));
      },
      child:Scaffold(
        appBar:AppBar(title:Text(widget.model.title),
          actions:[IconButton(
            onPressed:authorized?()async{
              await Clipboard.setData(ClipboardData(text:
                'Roteiro: '+widget.model.title+'\nEmpresa: '+
                widget.company.name+'\nVerificados: '+
                draft.reviewed.toString()+'\nPendentes: '+
                (widget.model.questions.length-draft.reviewed).toString()));
              if(context.mounted)ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content:Text('Resumo copiado.')));
            }:null,
            tooltip:'Copiar resumo',icon:const Icon(Icons.copy_outlined),
          )]),
        body:SafeArea(child:Center(child:ConstrainedBox(
          constraints:const BoxConstraints(maxWidth:760),
          child:ListView(padding:const EdgeInsets.all(12),children:[
            Text(widget.company.name,
              style:Theme.of(context).textTheme.titleLarge),
            const SizedBox(height:4),
            Text(widget.model.subtitle),
            const SizedBox(height:8),
            const Text('Roteiro de campo orientativo. Não cria NC, laudo, '
              'CAT, medição ou conclusão automaticamente.'),
            if(outstanding>0)const LinearProgressIndicator(),
            if(error!=null)Text(error!,style:TextStyle(
              color:Theme.of(context).colorScheme.error)),
            Card(child:Padding(padding:const EdgeInsets.all(12),
              child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
                Text('Dados do relatório',
                  style:Theme.of(context).textTheme.titleMedium),
                for(final field in <(String,String,String)>[
                  ('Local / setor',draft.location,'location'),
                  ('Máquina / atividade / frente',draft.asset,'asset'),
                  ('Técnico responsável',draft.technician,'technician'),
                  ('Data da vistoria',draft.date,'date'),
                  if(isIncident)...[
                    ('Data e hora informadas do evento',draft.eventTime,'eventTime'),
                    ('Narrativa factual do evento',draft.eventNarrative,'eventNarrative'),
                  ],
                ])
                  ListTile(
                    contentPadding:EdgeInsets.zero,
                    title:Text(field.$1),
                    subtitle:Text(field.$2.isEmpty?'Não informado':field.$2),
                    trailing:const Icon(Icons.edit_outlined),
                    enabled:authorized,
                    onTap:()async {
                      final value=await _textDialog(field.$1,
                        'Informe apenas o que foi conferido',field.$2,
                        max:field.$3=='eventNarrative'?2400:200,
                        min:field.$3=='eventNarrative'?20:0);
                      if(value==null||!mounted||!authorized)return;
                      switch(field.$3){
                        case 'location':_update(draft.copyWith(location:value));break;
                        case 'asset':_update(draft.copyWith(asset:value));break;
                        case 'technician':_update(draft.copyWith(technician:value));break;
                        case 'date':_update(draft.copyWith(date:value));break;
                        case 'eventTime':_update(draft.copyWith(eventTime:value));break;
                        case 'eventNarrative':_update(draft.copyWith(eventNarrative:value));break;
                      }
                    }),
                const Divider(),
                Text('Verificados: '+draft.reviewed.toString()+
                  '/'+widget.model.questions.length.toString()+
                  (isIncident?'':' • Não conformes: '+
                     draft.nonConformities.toString())),
                if(draft.isPartial)
                  const Text('O PDF será identificado como parcial enquanto '
                    'houver itens não verificados.'),
              ]))),
            for(final question in widget.model.questions)
              _questionCard(question),
            Card(child:Padding(padding:const EdgeInsets.all(14),
              child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
                const Text('Finalização',
                  style:TextStyle(fontWeight:FontWeight.w800,fontSize:16)),
                const SizedBox(height:8),
                const Text('Revise fatos, fotografias e recomendações. '
                  'A assinatura só é inserida se você assinar nesta tela.'),
                OutlinedButton.icon(
                  onPressed:authorized?_sign:null,
                  icon:const Icon(Icons.draw_outlined),
                  label:Text(draft.signaturePath.isEmpty?
                    'Assinar relatório':'Atualizar assinatura')),
                const SizedBox(height:8),
                FilledButton.icon(
                  onPressed:authorized&&outstanding==0&&!exporting&&
                    !saveFailed&&draft.hasEnoughForPdf?_export:null,
                  icon:const Icon(Icons.picture_as_pdf_outlined),
                  label:Text(exporting?'Gerando PDF...':
                    'Revisar e gerar PDF offline')),
                if(!draft.hasEnoughForPdf)
                  const Text('Para liberar o PDF: informe técnico e data, '
                    'revise algum item e descreva situações não conformes '
                    'ou fatos apurados. No caso de acidente, informe '
                    'data/hora e uma narrativa factual.'),
                const SizedBox(height:8),
                Text('Referência temática: '+widget.model.reference),
              ]))),
          ]),
        ))),
      ),
    );
  }
}

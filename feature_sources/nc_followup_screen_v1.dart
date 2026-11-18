import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import '../database.dart';
import '../models.dart';
import '../services/auth_service.dart';
import '../services/nc_followup.dart';

String ncField(Map<String,dynamic> row,List<String> keys) {
  for(final key in keys) {
    final value=(row[key]??'').toString().trim();
    if(value.isNotEmpty)return value;
  }
  return '';
}

class NcFollowupListScreen extends StatefulWidget {
  const NcFollowupListScreen({super.key,required this.company});
  final Company company;
  @override State<NcFollowupListScreen> createState()=>_NcFollowupListState();
}
class _NcFollowupListState extends State<NcFollowupListScreen> {
  late Future<List<Map<String,dynamic>>> result;
  @override void initState(){super.initState();_refresh();}
  void _refresh(){result=_load();}
  Future<List<Map<String,dynamic>>> _load()async{
    if(!AuthService.canAccessCompany(widget.company.id)) {
      throw StateError('Sem permissão para esta empresa');
    }
    final records=await AppDatabase.instance.getNonConformityRows(
      includeClosed:false).timeout(const Duration(seconds:12));
    final seen=<String>{};
    final filtered=<Map<String,dynamic>>[];
    for(final record in records){
      final row=Map<String,dynamic>.from(record);
      final companyId=ncField(row,['company_id','companyId','empresa_id']);
      final ncId=ncField(row,['id','nc_id','ncId']);
      if(companyId!=widget.company.id||ncId.isEmpty||!seen.add(ncId))continue;
      filtered.add(row);
    }
    return filtered;
  }
  @override Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:const Text('Acompanhar NC existente'),
      actions:[IconButton(tooltip:'Atualizar',icon:const Icon(Icons.refresh),
        onPressed:()=>setState(_refresh))]),
    body:SafeArea(child:FutureBuilder<List<Map<String,dynamic>>>(
      future:result,builder:(context,snap){
        if(!snap.hasData&&!snap.hasError){
          return const Center(child:CircularProgressIndicator());
        }
        if(snap.hasError){
          return Center(child:Column(mainAxisSize:MainAxisSize.min,children:[
            const Text('Falha na consulta. Nenhuma NC foi alterada.'),
            FilledButton(onPressed:()=>setState(_refresh),
                child:const Text('Tentar novamente')),
          ]));
        }
        final rows=snap.data!;
        return ListView(padding:const EdgeInsets.all(16),children:[
          Text(widget.company.name,style:Theme.of(context).textTheme.titleLarge),
          const SizedBox(height:10),
          const Text('Selecione um problema já registrado para acompanhar '
            'sem gerar outra NC. O histórico é local e não sincroniza.'),
          const SizedBox(height:15),
          Text('NCs encontradas: '+rows.length.toString(),
            style:Theme.of(context).textTheme.titleMedium),
          if(rows.isEmpty)const Card(child:Padding(
            padding:EdgeInsets.all(16),
            child:Text('Nenhuma NC aberta identificada neste aparelho. '
              'Isso NÃO comprova ausência de riscos ou pendências.'))),
          for(final row in rows)Card(child:ListTile(
            contentPadding:const EdgeInsets.all(14),
            title:Text(ncField(row,['description','title','descricao'])
              .isEmpty?'NC sem descrição':
              ncField(row,['description','title','descricao']),
              style:const TextStyle(fontWeight:FontWeight.bold,fontSize:16)),
            subtitle:Text('NC '+ncField(row,['id','nc_id','ncId'])+' • '+
              ncField(row,['sector','sector_name','setor'])),
            trailing:const Icon(Icons.chevron_right),
            onTap:()async{
              await Navigator.of(context).push(MaterialPageRoute<void>(
                builder:(_)=>NcFollowupDetailScreen(
                  company:widget.company,nc:row)));
              if(mounted)setState(_refresh);
            },
          )),
        ]);
      },
    )),
  );
}

class NcFollowupDetailScreen extends StatefulWidget {
  const NcFollowupDetailScreen({
    super.key,required this.company,required this.nc,
  });
  final Company company;
  final Map<String,dynamic> nc;
  @override State<NcFollowupDetailScreen> createState()=>_NcFollowupDetailState();
}
class _NcFollowupDetailState extends State<NcFollowupDetailScreen> {
  late final NcFollowupLedger ledger;
  late final String ncId,userId;
  late Future<List<NcFollowupEvent>> history;
  bool saving=false;

  bool get allowed=>AuthService.canAccessCompany(widget.company.id)&&
    AppDatabase.activeUserId.toString()==userId&&userId!='null'&&
    ncField(widget.nc,['company_id','companyId','empresa_id'])==widget.company.id;
  @override void initState(){
    super.initState();
    ncId=ncField(widget.nc,['id','nc_id','ncId']);
    userId=AppDatabase.activeUserId.toString();
    ledger=NcFollowupLedger(read:AppDatabase.instance.getSetting,
      write:AppDatabase.instance.setSetting);
    _reload();
  }
  void _reload(){history=_load();}
  Future<List<NcFollowupEvent>> _load()async{
    if(!allowed||ncId.isEmpty)throw StateError('Acesso não autorizado');
    return ledger.list(widget.company.id,ncId,userId);
  }

  Future<String?> ask(String title,String hint)async{
    final form=GlobalKey<FormState>();
    String description='';
    return showDialog<String>(context:context,builder:(ctx)=>AlertDialog(
      title:Text(title),
      content:Form(key:form,child:TextFormField(
        maxLength:1000,minLines:2,maxLines:5,
        decoration:InputDecoration(labelText:'Observação',hintText:hint),
        onChanged:(value)=>description=value,
        validator:(v)=>(v??'').trim().length<8?
          'Descreva a situação (mínimo 8 caracteres).':null,
      )),
      actions:[
        TextButton(onPressed:()=>Navigator.pop(ctx),
          child:const Text('Cancelar')),
        FilledButton(onPressed:(){
          if(form.currentState!.validate()){
            Navigator.pop(ctx,description.trim());
          }
        },child:const Text('Salvar')),
      ],
    ));
  }

  Future<bool> save(NcFollowupKind kind,String note,{String? photo})async{
    if(saving||!allowed)return false;
    setState(()=>saving=true);
    try{
      await ledger.append(NcFollowupEvent(
        id:NcFollowupLedger.newId(),companyId:widget.company.id,
        ncId:ncId,authorId:userId,
        at:DateTime.now().toUtc().toIso8601String(),
        kind:kind,note:note,photoPath:photo,
      ));
      if(mounted){
        setState(_reload);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content:Text('Salvo no aparelho. A NC oficial não foi encerrada.')));
      }
      return true;
    }catch(_){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content:Text('Erro ao salvar. Histórico anterior preservado.')));
      return false;
    }finally{if(mounted)setState(()=>saving=false);}
  }

  Future<void> report(NcFollowupKind kind)async{
    if(saving||!allowed)return;
    final isCorrection=kind==NcFollowupKind.correctionReported;
    final note=await ask(
      isCorrection?'Informar correção':'Problema continua',
      isCorrection?'Descreva a adequação para validação do TST.':
        'O que continua sem correção nesta nova visita?');
    if(note!=null&&allowed)await save(kind,note);
  }

  Future<void> attachPhoto()async{
    if(saving||!allowed)return;
    String? stored;
    try{
      final picked=await ImagePicker().pickImage(
        source:ImageSource.camera,maxWidth:1400,imageQuality:75);
      if(picked==null||!allowed)return;
      final input=File(picked.path);
      if(await input.length()>2000000)throw StateError('Foto acima de 2 MB');
      final note=await ask('Anexar foto','O que a fotografia demonstra?');
      if(note==null||!allowed)return;
      final dir=await getApplicationDocumentsDirectory();
      final safe=[userId,widget.company.id,ncId]
        .map((s)=>s.replaceAll(RegExp(r'[^a-zA-Z0-9_-]'),'_')).join('_');
      final folder=Directory(dir.path+'/auditar_nc_followup_local/'+safe);
      await folder.create(recursive:true);
      stored=folder.path+'/'+NcFollowupLedger.newId()+'.jpg';
      await input.copy(stored);
      if(!await save(NcFollowupKind.photo,note,photo:stored)){
        await File(stored).delete();
      }
    }catch(_){
      if(stored!=null&&await File(stored).exists()){
        await File(stored).delete();
      }
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content:Text('Não foi possível anexar a foto.')));
    }
  }

  void showPlan(){
    final plan=ncField(widget.nc,
      ['action','recommendation','corrective_action','recomendacao']);
    final owner=ncField(widget.nc,['responsible','responsavel']);
    final due=ncField(widget.nc,['dueDate','due_date','prazo']);
    showDialog<void>(context:context,builder:(ctx)=>AlertDialog(
      title:const Text('Plano de ação'),
      content:SingleChildScrollView(child:Column(
        crossAxisAlignment:CrossAxisAlignment.start,
        mainAxisSize:MainAxisSize.min,children:[
          Text(plan.isEmpty?'Plano não encontrado no registro local.':plan),
          if(owner.isNotEmpty)Text('Responsável: '+owner),
          if(due.isNotEmpty)Text('Prazo: '+due),
          const SizedBox(height:10),
          const Text('Consulta apenas. O plano oficial não foi modificado.'),
        ],
      )),
      actions:[TextButton(onPressed:()=>Navigator.pop(ctx),
        child:const Text('Fechar'))],
    ));
  }

  String label(NcFollowupKind kind){
    switch(kind){
      case NcFollowupKind.persists:return 'Pendência mantida';
      case NcFollowupKind.photo:return 'Foto de acompanhamento';
      case NcFollowupKind.correctionReported:
        return 'Correção informada — aguarda validação';
    }
  }

  @override Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:const Text('Acompanhamento de NC')),
    body:SafeArea(child:FutureBuilder<List<NcFollowupEvent>>(
      future:history,builder:(context,snap){
        if(!snap.hasData&&!snap.hasError){
          return const Center(child:CircularProgressIndicator());
        }
        if(snap.hasError){
          return Center(child:Column(mainAxisSize:MainAxisSize.min,children:[
            const Text('Falha no histórico local. Nenhum dado foi alterado.'),
            FilledButton(onPressed:()=>setState(_reload),
              child:const Text('Tentar novamente')),
          ]));
        }
        final events=snap.data!;
        return ListView(padding:const EdgeInsets.all(16),children:[
          Card(child:Padding(padding:const EdgeInsets.all(16),
            child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
              const Chip(label:Text('NC existente • pendente')),
              Text(ncField(widget.nc,['description','title','descricao']),
                style:Theme.of(context).textTheme.titleLarge),
              Text(widget.company.name+' • '+
                ncField(widget.nc,['sector','sector_name','setor'])),
              Text('NC: '+ncId+' • '+events.length.toString()+
                ' acompanhamentos locais'),
            ]),
          )),
          const SizedBox(height:12),
          Text('Histórico',style:Theme.of(context).textTheme.titleMedium),
          if(events.isEmpty)const Card(child:Padding(
            padding:EdgeInsets.all(14),
            child:Text('Sem acompanhamentos nesta tela. '
              'Vistorias anteriores não são apagadas.'))),
          for(final e in events.reversed)Card(child:Padding(
            padding:const EdgeInsets.all(14),
            child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
              Text(label(e.kind),style:const TextStyle(
                fontSize:16,fontWeight:FontWeight.bold)),
              Text(e.at.replaceFirst('T',' ').split('.').first),
              const SizedBox(height:6),
              Text(e.note,style:const TextStyle(fontSize:16)),
              if(e.photoPath!=null&&File(e.photoPath!).existsSync())
                Image.file(File(e.photoPath!),height:150,fit:BoxFit.contain),
            ]),
          )),
          const SizedBox(height:12),
          FilledButton.icon(
            onPressed:saving||!allowed?null:
              ()=>report(NcFollowupKind.persists),
            icon:const Icon(Icons.note_add_outlined),
            label:const Text('Registrar acompanhamento')),
          const SizedBox(height:8),
          OutlinedButton.icon(onPressed:saving||!allowed?null:attachPhoto,
            icon:const Icon(Icons.camera_alt_outlined),
            label:const Text('Anexar foto')),
          const SizedBox(height:8),
          OutlinedButton.icon(onPressed:showPlan,
            icon:const Icon(Icons.assignment_outlined),
            label:const Text('Ver plano de ação')),
          const SizedBox(height:8),
          OutlinedButton.icon(onPressed:saving||!allowed?null:
              ()=>report(NcFollowupKind.correctionReported),
            icon:const Icon(Icons.fact_check_outlined),
            label:const Text('Informar correção para validação')),
          const SizedBox(height:14),
          const Text('A NC só pode ser encerrada pelo fluxo oficial de '
            'validação técnica. Dados locais, sem sincronização com a Central.',
            style:TextStyle(fontSize:13)),
        ]);
      },
    )),
  );
}

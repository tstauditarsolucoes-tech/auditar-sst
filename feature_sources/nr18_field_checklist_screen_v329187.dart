import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../database.dart';
import '../models.dart';
import '../services/auth_service.dart';
import 'express_round_screen.dart';
import 'new_inspection_screen.dart';

/// Orientative NR-18 field prompts. NOT a substitute for a PGR, legal audit,
/// professional assessment, or an NC record in the SST database.
/// References point to sections, not unverified clause-by-clause requirements.
class Nr18FieldTopic {
  const Nr18FieldTopic(this.id,this.title,this.section,this.prompt,this.phases);
  final String id,title,section,prompt;
  final List<String> phases;
  bool appliesTo(String phase)=>phases.isEmpty||phases.contains(phase);
}
class Nr18FieldCatalog {
  static const topics=<Nr18FieldTopic>[
    Nr18FieldTopic('pgr','PGR e planejamento','18.4',
      'Conferir PGR da obra, medidas de prevenção e compatibilidade com as atividades em execução.',[]),
    Nr18FieldTopic('areas','Áreas de vivência','18.5',
      'Verificar condições de instalações sanitárias, água potável, higiene e espaços de apoio conforme a obra.',[]),
    Nr18FieldTopic('eletrica','Instalações elétricas','18.6',
      'Verificar quadros, proteções, cabos, instalações temporárias e acesso de pessoas autorizadas.',[]),
    Nr18FieldTopic('ordem','Organização e circulação','18.13',
      'Observar isolamento de áreas, armazenamento, sinalização e rotas de circulação seguras.',[]),
    Nr18FieldTopic('quedas','Bordas, vãos e aberturas','18.9',
      'Observar proteção coletiva de bordas, vãos, aberturas no piso e áreas com risco de queda.',[]),
    Nr18FieldTopic('acessos','Escadas, rampas e passarelas','18.8',
      'Inspecionar acessos, superfícies, estabilidade, proteção e passagens em uso.',[]),
    Nr18FieldTopic('andaimes','Andaimes e plataformas','18.12',
      'Avaliar estabilidade, base e apoios, travamentos/diagonais, acesso, piso e proteções segundo o tipo de andaime.',
      ['Estrutura','Alvenaria','Instalações','Acabamento','Entrega']),
    Nr18FieldTopic('escavacao','Escavações e fundações','18.7',
      'Observar estabilidade do solo, acesso, isolamento, interferências e medidas de proteção nas escavações.',
      ['Fundação','Estrutura']),
    Nr18FieldTopic('formas','Formas e escoramentos','18.7',
      'Verificar atividades de montagem, apoio, escoramento, estabilidade e circulação na concretagem.',
      ['Fundação','Estrutura']),
    Nr18FieldTopic('demolicao','Demolições e desmontagens','18.7',
      'Verificar planejamento, isolamento, queda de materiais e proteção das pessoas expostas.',
      ['Planejamento','Estrutura','Acabamento','Outros']),
    Nr18FieldTopic('maquinas','Máquinas e ferramentas','18.10',
      'Verificar proteções, condição de uso, manutenção e operação segura de equipamentos e ferramentas.',[]),
    Nr18FieldTopic('elevacao','Movimentação de cargas','18.11',
      'Observar isolamento, movimentação de cargas, transporte de pessoas e riscos de queda de materiais.',[]),
    Nr18FieldTopic('sinalizacao','Sinalização e frentes simultâneas','18.13',
      'Avaliar orientação, isolamento e circulação de trabalhadores em frentes com riscos diferentes.',[]),
    Nr18FieldTopic('capac','Capacitação e orientação','18.14',
      'Conferir orientação e capacitação exigíveis para atividades e equipamentos efetivamente presentes.',[]),
    Nr18FieldTopic('altura','Trabalho em altura','18.9 / NR-35',
      'Verificar se o trabalho em altura possui planejamento, prevenção e proteção compatíveis com o risco.',
      ['Estrutura','Alvenaria','Instalações','Acabamento','Entrega']),
    Nr18FieldTopic('ferragens','Cortes e materiais expostos','18.7',
      'Observar peças, armaduras, pontas, materiais cortantes e queda de materiais na frente de serviço.',
      ['Fundação','Estrutura','Alvenaria','Acabamento']),
  ];
  static const stages=<String>['Planejamento','Fundação','Estrutura','Alvenaria',
    'Instalações','Acabamento','Entrega','Outros'];
  static List<Nr18FieldTopic> forStage(String stage)=>
    topics.where((t)=>t.appliesTo(stage)).toList();
}

enum Nr18FieldStatus { notChecked, compliant, nonCompliant, notApplicable }
extension Nr18FieldStatusText on Nr18FieldStatus {
  String get label {
    switch(this){
      case Nr18FieldStatus.notChecked:return 'Não verificado';
      case Nr18FieldStatus.compliant:return 'Conforme';
      case Nr18FieldStatus.nonCompliant:return 'Não conforme';
      case Nr18FieldStatus.notApplicable:return 'Não se aplica';
    }
  }
}
class Nr18FieldAnswer {
  const Nr18FieldAnswer({this.status=Nr18FieldStatus.notChecked,this.note=''});
  final Nr18FieldStatus status;
  final String note;
  Map<String,dynamic> toMap()=>{'status':status.name,'note':note};
  factory Nr18FieldAnswer.fromMap(Map<dynamic,dynamic> map) {
    final raw=(map['status']??'').toString();
    final status=Nr18FieldStatus.values.where((s)=>s.name==raw)
      .firstOrNull??Nr18FieldStatus.notChecked;
    return Nr18FieldAnswer(status:status,note:(map['note']??'').toString());
  }
}

class Nr18FieldDraft {
  Nr18FieldDraft({this.stage='Planejamento',this.updatedAt='',Map<String,Nr18FieldAnswer>? answers})
      : answers=Map<String,Nr18FieldAnswer>.of(answers??{});
  final String stage,updatedAt;
  final Map<String,Nr18FieldAnswer> answers;
  Nr18FieldAnswer answer(String id)=>answers[id]??const Nr18FieldAnswer();
  Nr18FieldDraft updated(String id,Nr18FieldAnswer value,String stage,String at){
    final next=Map<String,Nr18FieldAnswer>.of(answers);
    next[id]=value;
    return Nr18FieldDraft(stage:stage,updatedAt:at,answers:next);
  }
  int count(Nr18FieldStatus status)=>Nr18FieldCatalog.topics
    .where((t)=>answer(t.id).status==status).length;
  int get checked=>Nr18FieldCatalog.topics.length-count(Nr18FieldStatus.notChecked);
  String get summaryStatus=>'Não conformes: '+count(Nr18FieldStatus.nonCompliant).toString()+
    ' • Não verificados: '+count(Nr18FieldStatus.notChecked).toString();
  Map<String,dynamic> toMap()=>{
    'schemaVersion':1,'stage':stage,'updatedAt':updatedAt,
    'answers':{for(final e in answers.entries)e.key:e.value.toMap()},
  };
  factory Nr18FieldDraft.fromMap(Map<String,dynamic> raw){
    final records=<String,Nr18FieldAnswer>{};
    final payload=raw['answers'];
    if(payload is Map){
      final allowed=Nr18FieldCatalog.topics.map((t)=>t.id).toSet();
      for(final e in payload.entries){
        if(allowed.contains(e.key)&&e.value is Map){
          records[e.key.toString()]=Nr18FieldAnswer.fromMap(e.value as Map);
        }
      }
    }
    final stage=(raw['stage']??'').toString();
    return Nr18FieldDraft(
      stage:Nr18FieldCatalog.stages.contains(stage)?stage:'Planejamento',
      updatedAt:(raw['updatedAt']??'').toString(),
      answers:records);
  }
  String summary(String company) {
    final lines=<String>[
      'ROTEIRO DE CAMPO - NR-18 (triagem técnica)',
      'Obra: '+company,
      'Etapa: '+stage,
      'Atualizado: '+updatedAt,
      summaryStatus,
      'Situações registradas pelo técnico (não substitui vistoria formal):',
    ];
    for(final item in Nr18FieldCatalog.topics){
      final record=answer(item.id);
      if(record.status==Nr18FieldStatus.notChecked && record.note.trim().isEmpty)continue;
      lines.add('- '+item.title+' ('+item.section+'): '+record.status.label);
      if(record.note.trim().isNotEmpty)lines.add('  Observação: '+record.note.trim());
    }
    lines.add('Para fotos, NC oficial, plano de ação e PDF, utilizar os módulos SST existentes.');
    return lines.join('\n');
  }
}

class Nr18FieldDraftStore {
  static String key(String companyId,String userId)=>
    'nr18_field_draft_v1_'+Uri.encodeComponent(userId)+'_'+Uri.encodeComponent(companyId);
  static Future<Nr18FieldDraft> load(String companyId,String userId)async{
    final raw=await AppDatabase.instance.getSetting(key(companyId,userId));
    if(raw.isEmpty)return Nr18FieldDraft();
    final decoded=jsonDecode(raw);
    if(decoded is! Map)throw const FormatException('Roteiro NR-18 local inválido.');
    return Nr18FieldDraft.fromMap(Map<String,dynamic>.from(decoded));
  }
  static Future<void> save(String companyId,String userId,Nr18FieldDraft draft)=>
    AppDatabase.instance.setSetting(key(companyId,userId),jsonEncode(draft.toMap()));
}

class Nr18FieldItemCard extends StatelessWidget {
  const Nr18FieldItemCard({super.key,required this.topic,required this.answer,
    required this.onStatus,required this.onNote,required this.enabled});
  final Nr18FieldTopic topic;
  final Nr18FieldAnswer answer;
  final ValueChanged<Nr18FieldStatus> onStatus;
  final VoidCallback onNote;
  final bool enabled;
  @override
  Widget build(BuildContext context)=>Card(child:Padding(padding:const EdgeInsets.all(12),
    child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
      Text(topic.title,style:Theme.of(context).textTheme.titleMedium),
      Text('Referência: NR-18, seção '+topic.section,style:Theme.of(context).textTheme.bodySmall),
      const SizedBox(height:6),
      Text(topic.prompt),
      const SizedBox(height:8),
      DropdownButton<Nr18FieldStatus>(
        isExpanded:true,value:answer.status,
        onChanged:enabled?(value){if(value!=null)onStatus(value);}:null,
        items:Nr18FieldStatus.values.map((value)=>DropdownMenuItem(
          value:value,child:Text(value.label))).toList(),
      ),
      if(answer.status==Nr18FieldStatus.nonCompliant&&answer.note.trim().isEmpty)
        const Text('Descreva o fato observado antes de formalizar a NC.',
          style:TextStyle(fontWeight:FontWeight.bold)),
      if(answer.note.trim().isNotEmpty)
        Text('Observação: '+answer.note,maxLines:5,overflow:TextOverflow.ellipsis),
      Align(alignment:Alignment.centerRight,
        child:TextButton.icon(
          onPressed:enabled?onNote:null,
          icon:const Icon(Icons.edit_note),
          label:Text(answer.note.isEmpty?'Adicionar observação':'Editar observação'))),
    ])));
}

class Nr18FieldChecklistScreen extends StatefulWidget {
  const Nr18FieldChecklistScreen({super.key,required this.company,required this.phase});
  final Company company;
  final String phase;
  @override
  State<Nr18FieldChecklistScreen> createState()=>_Nr18FieldChecklistScreenState();
}
class _Nr18FieldChecklistScreenState extends State<Nr18FieldChecklistScreen>{
  Nr18FieldDraft draft=Nr18FieldDraft();
  bool loading=true,showAll=false,onlyUnresolved=false;
  int writes=0;
  String? error;
  String? openedUser;
  Future<void> tail=Future<void>.value();
  String get stage=>Nr18FieldCatalog.stages.contains(widget.phase)?
      widget.phase:'Outros';
  bool get authorized=>AuthService.canAccessCompany(widget.company.id)&&
    openedUser==AppDatabase.activeUserId.toString();
  @override
  void initState(){super.initState();_load();}
  Future<void> _load()async{
    if(!AuthService.canAccessCompany(widget.company.id)){
      if(mounted)setState((){loading=false;error='Sem acesso a esta obra.';});
      return;
    }
    final uid=AppDatabase.activeUserId.toString();
    try{
      final value=await Nr18FieldDraftStore.load(widget.company.id,uid);
      if(!mounted)return;
      setState((){draft=value;openedUser=uid;loading=false;});
    }catch(_){
      if(mounted)setState((){loading=false;error='Não foi possível abrir o roteiro local. Nenhum registro foi substituído.';});
    }
  }
  void _update(String id,Nr18FieldAnswer answer){
    if(!authorized)return;
    final at=DateTime.now().toLocal().toIso8601String();
    final value=draft.updated(id,answer,stage,at);
    setState((){draft=value;writes++;});
    final uid=openedUser!;
    // Serialize writes so fast changes cannot replace a newer local answer.
    tail=tail.catchError((_){})
      .then((_)async{
        if(uid!=AppDatabase.activeUserId.toString())throw StateError('Conta alterada.');
        await Nr18FieldDraftStore.save(widget.company.id,uid,value);
      }).catchError((_){
        if(mounted)setState(()=>error='Erro ao salvar roteiro local. Confira o armazenamento.');
      }).whenComplete((){
        if(mounted)setState(()=>writes--);
      });
  }
  Future<void> _editNote(Nr18FieldTopic item)async{
    if(!authorized)return;
    final controller=TextEditingController(text:draft.answer(item.id).note);
    final value=await showDialog<String>(context:context,builder:(dialog)=>AlertDialog(
      title:Text(item.title),
      content:SingleChildScrollView(child:TextField(controller:controller,
        autofocus:true,maxLength:800,maxLines:5,
        decoration:const InputDecoration(
          labelText:'Fato observado (sem conclusões automáticas)',
          border:OutlineInputBorder()))),
      actions:[
        TextButton(onPressed:()=>Navigator.pop(dialog),child:const Text('Cancelar')),
        FilledButton(onPressed:()=>Navigator.pop(dialog,controller.text.trim()),
          child:const Text('Salvar observação')),
      ],
    ));
    WidgetsBinding.instance.addPostFrameCallback((_)=>controller.dispose());
    if(value==null||!mounted||!authorized)return;
    final previous=draft.answer(item.id);
    _update(item.id,Nr18FieldAnswer(status:previous.status,note:value));
  }
  void _open(Widget screen){
    if(!authorized)return;
    Navigator.of(context).push(MaterialPageRoute(builder:(_)=>screen));
  }
  @override
  Widget build(BuildContext context){
    final topics=Nr18FieldCatalog.topics.where((item){
      if(onlyUnresolved)return draft.answer(item.id).status==
        Nr18FieldStatus.nonCompliant||draft.answer(item.id).status==
          Nr18FieldStatus.notChecked;
      return showAll||item.appliesTo(stage)||
        draft.answer(item.id).status==Nr18FieldStatus.nonCompliant;
    }).toList();
    return PopScope(
      canPop:writes==0,
      onPopInvokedWithResult:(didPop,result){
        if(!didPop&&writes>0)ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content:Text('Salvando roteiro local. Confira o indicador e volte novamente.')));
      },
      child:Scaffold(
        appBar:AppBar(title:const Text('Roteiro NR-18')),
        body:loading?const Center(child:CircularProgressIndicator()):
          error!=null&&openedUser==null?Center(child:Text(error!)):
          Align(alignment:Alignment.topCenter,child:ConstrainedBox(
          constraints:const BoxConstraints(maxWidth:800),
          child:ListView(padding:const EdgeInsets.all(14),children:[
            Text(widget.company.name,style:Theme.of(context).textTheme.titleLarge),
            Text('Etapa atual: '+stage),
            const SizedBox(height:8),
            const Text('Triagem orientativa para o TST. Não gera automaticamente NC, laudo ou declaração de conformidade.'),
            if(writes>0)const LinearProgressIndicator(),
            if(error!=null)Text(error!,style:const TextStyle(fontWeight:FontWeight.bold)),
            Card(child:Padding(padding:const EdgeInsets.all(12),
              child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
                Text(draft.summaryStatus,style:Theme.of(context).textTheme.titleMedium),
                Text('Verificados: '+draft.checked.toString()+' / '+
                  Nr18FieldCatalog.topics.length.toString()+
                  ' • registros locais por obra e técnico'),
                const SizedBox(height:8),
                Wrap(spacing:8,runSpacing:8,children:[
                  OutlinedButton.icon(onPressed:authorized?()async{
                    await Clipboard.setData(ClipboardData(text:draft.summary(widget.company.name)));
                    if(context.mounted)ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content:Text('Resumo NR-18 copiado.')));
                  }:null,icon:const Icon(Icons.copy_outlined),label:const Text('Copiar resumo')),
                  OutlinedButton.icon(
                    onPressed:authorized?()=>_open(ExpressRoundScreen(company:widget.company)):null,
                    icon:const Icon(Icons.add_a_photo_outlined),
                    label:const Text('Ronda com fotos')),
                  OutlinedButton.icon(
                    onPressed:authorized?()=>_open(NewInspectionScreen(
                      initialCompany:widget.company,fieldMode:true)):null,
                    icon:const Icon(Icons.fact_check_outlined),
                    label:const Text('Abrir Vistoria')),
                ]),
                const Text('Para registrar irregularidades e evidências oficiais, use a Ronda/Vistoria. Este roteiro não altera seus dados.'),
              ]))),
            SwitchListTile(title:const Text('Mostrar todos os temas da NR-18'),
              value:showAll,onChanged:(v)=>setState(()=>showAll=v)),
            SwitchListTile(title:const Text('Mostrar apenas não verificados e não conformes'),
              value:onlyUnresolved,onChanged:(v)=>setState(()=>onlyUnresolved=v)),
            if(topics.isEmpty)const Padding(padding:EdgeInsets.all(16),
              child:Text('Nenhum item correspondente ao filtro.')),
            for(final item in topics)Nr18FieldItemCard(
              key:ValueKey('nr18-'+item.id),topic:item,answer:draft.answer(item.id),
              enabled:authorized,
              onStatus:(v)=>_update(item.id,
                Nr18FieldAnswer(status:v,note:draft.answer(item.id).note)),
              onNote:()=>_editNote(item)),
            const SizedBox(height:12),
            const Text('Referência temática: NR-18, redação oficial atualizada em maio de 2026. Confirmar exigências específicas com o texto vigente e as demais NRs aplicáveis.'),
          ]))),
      ),
    );
  }
}

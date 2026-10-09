import 'dart:convert';
import 'package:flutter/material.dart';
import '../database.dart';
import '../services/auth_service.dart';
import '../services/apps_script_http.dart';
import 'action_plan_screen.dart';

/// Caixa de entrada isolada: não altera registros, mídias ou sincronização SST.
class ClientTreatmentInboxScreen extends StatefulWidget {
  const ClientTreatmentInboxScreen({super.key,this.companyId='',this.companyName=''});
  final String companyId,companyName;
  @override
  State<ClientTreatmentInboxScreen> createState()=>_ClientTreatmentInboxScreenState();
}
class _ClientTreatmentInboxScreenState extends State<ClientTreatmentInboxScreen> {
  List<Map<String,dynamic>> threads=[];
  Map<String,dynamic> summary={};
  bool busy=true;
  String error='',filter='Todas';

  Future<Map<String,dynamic>> request(String mode,{
    String companyId='',String topicId='',Map<String,dynamic>? record}) async {
    final user=AuthService.currentUser,token=AuthService.sessionToken;
    if(!AuthService.isSignedIn||user==null||
       user.role.toLowerCase()=='cliente'||token.isEmpty)
      throw StateError('Acesso reservado à equipe Auditar.');
    if(companyId.isNotEmpty&&!AuthService.canAccessCompany(companyId))
      throw StateError('Acesso à empresa não autorizado.');
    final endpoint=(await AppDatabase.instance.getSetting(
      'management_panel_endpoint')).trim();
    if(!endpoint.startsWith('https://'))
      throw StateError('Central não configurada para conexão segura.');
    final response=await AppsScriptHttp.postJson(Uri.parse(endpoint),{
      'action':'client_treatment_v2','authToken':token,'mode':mode,
      if(companyId.isNotEmpty)'companyId':companyId,
      if(topicId.isNotEmpty)'topicId':topicId,
      if(record!=null)'record':record,
    },timeout:const Duration(seconds:25));
    if(response.statusCode!=200)throw StateError('Central indisponível.');
    final parsed=jsonDecode(response.body);
    if(parsed is! Map)throw StateError('Resposta inválida da Central.');
    final body=Map<String,dynamic>.from(parsed);
    if(body['ok']!=true)throw StateError((body['message']??
      'Tratativas não implantadas na Central.').toString());
    if(token!=AuthService.sessionToken||user.id!=AuthService.currentUser?.id)
      throw StateError('A conta foi alterada. Atualize a consulta.');
    return body;
  }

  @override
  void initState(){super.initState();load();}
  Future<void> load() async {
    if(mounted)setState((){busy=true;error='';});
    try {
      final body=await request('inbox',companyId:widget.companyId);
      final found=<Map<String,dynamic>>[];
      for(final value in body['threads'] is List?body['threads'] as List:const []){
        if(value is! Map)continue;
        final row=Map<String,dynamic>.from(value);
        if(AuthService.canAccessCompany((row['companyId']??'').toString()))
          found.add(row);
      }
      if(mounted)setState((){
        threads=found;
        summary=body['summary'] is Map?
          Map<String,dynamic>.from(body['summary'] as Map):{};
        busy=false;
      });
    } catch(e) {
      if(mounted)setState((){
        error=e.toString().replaceFirst('Bad state: ','');busy=false;
      });
    }
  }
  int count(String key)=>summary[key] is num?(summary[key] as num).toInt():0;
  bool visible(Map<String,dynamic> row) {
    final status=(row['status']??'').toString();
    if(filter=='Todas')return true;
    if(filter=='Em atraso')return row['overdue']==true;
    if(filter=='Concluídas')return status=='Concluída';
    return status==filter;
  }
  Future<void> open(Map<String,dynamic> row) async {
    final id=(row['companyId']??'').toString();
    if(!AuthService.canAccessCompany(id))return;
    await Navigator.of(context).push(MaterialPageRoute(
      builder:(_)=>_TreatmentConversation(
        companyId:id,topicId:(row['topicId']??'').toString(),
        title:(row['title']??'Tratativa').toString(),request:request)));
    if(mounted)await load();
  }
  Future<void> startNew() async {
    if(widget.companyId.isEmpty)return;
    try {
      final response=await request('topics',companyId:widget.companyId);
      final topics=<Map<String,dynamic>>[];
      for(final value in response['topics'] is List?response['topics'] as List:const []){
        if(value is Map)topics.add(Map<String,dynamic>.from(value));
      }
      if(!mounted)return;
      final chosen=await showModalBottomSheet<Map<String,dynamic>>(
        context:context,isScrollControlled:true,
        builder:(dialog)=>SafeArea(child:ListView(
          shrinkWrap:true,padding:const EdgeInsets.all(15),
          children:[
            const Text('Iniciar tratativa',style:TextStyle(
              fontSize:18,fontWeight:FontWeight.bold)),
            const Text('Selecione uma ocorrência publicada ou a conversa geral.'),
            const SizedBox(height:8),
            for(final item in topics)ListTile(
              leading:const Icon(Icons.forum_outlined),
              title:Text((item['title']??'Ocorrência').toString()),
              subtitle:Text((item['sector']??'').toString()),
              onTap:()=>Navigator.of(dialog).pop(item)),
          ])));
      if(chosen!=null&&mounted)await open({
        'companyId':widget.companyId,
        'topicId':chosen['id'],
        'title':chosen['title'],
      });
    }catch(e){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content:Text('Não foi possível carregar os assuntos: '+e.toString())));
    }
  }

  @override
  Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:Text(widget.companyId.isEmpty?
      'Caixa de entrada Auditar':'Tratativas • '+widget.companyName),
      actions:[IconButton(icon:const Icon(Icons.refresh),
        tooltip:'Atualizar',onPressed:busy?null:load)]),
    body:busy?const Center(child:CircularProgressIndicator()):
      RefreshIndicator(onRefresh:load,child:ListView(
      padding:const EdgeInsets.all(14),children:[
        const Text('Comunicação SST',style:TextStyle(
          fontSize:19,fontWeight:FontWeight.w800)),
        const Text('Mensagens por ocorrência, sem alterar as constatações originais.'),
        const SizedBox(height:10),
        if(widget.companyId.isNotEmpty)OutlinedButton.icon(
          onPressed:startNew,icon:const Icon(Icons.add_comment_outlined),
          label:const Text('Iniciar tratativa da empresa')),
        Wrap(spacing:7,runSpacing:7,children:[
          Chip(label:Text('Auditar: '+count('awaitingAuditar').toString())),
          Chip(label:Text('Cliente: '+count('awaitingClient').toString())),
          Chip(label:Text('Verificar: '+count('awaitingVerification').toString())),
          Chip(label:Text('Vencidos: '+count('overdue').toString())),
        ]),
        const SizedBox(height:10),
        SingleChildScrollView(scrollDirection:Axis.horizontal,child:Row(
          children:[for(final label in const ['Todas','Aguardando Auditar',
            'Aguardando cliente','Aguardando verificação','Em atraso','Concluídas'])
            Padding(padding:const EdgeInsets.only(right:6),
              child:ChoiceChip(label:Text(label),selected:filter==label,
                onSelected:(_)=>setState(()=>filter=label)))])),
        if(error.isNotEmpty)Card(child:Padding(padding:const EdgeInsets.all(14),
          child:Column(children:[Text(error),
            OutlinedButton(onPressed:load,child:const Text('Tentar novamente'))]))),
        if(error.isEmpty&&threads.where(visible).isEmpty)
          const Padding(padding:EdgeInsets.all(24),
            child:Text('Nenhuma conversa encontrada neste filtro.')),
        for(final row in threads.where(visible))
          Card(child:ListTile(
            leading:Icon(row['overdue']==true?
              Icons.event_busy_outlined:Icons.forum_outlined),
            title:Text((row['title']??'Conversa').toString(),maxLines:2,
              overflow:TextOverflow.ellipsis),
            subtitle:Text([
              (row['companyName']??'').toString(),
              (row['status']??'').toString(),
              (row['lastMessage']??'').toString(),
              if((row['dueDate']??'').toString().isNotEmpty)
                'Prazo: '+row['dueDate'].toString()
            ].where((x)=>x.isNotEmpty).join('\n'),
              maxLines:5,overflow:TextOverflow.ellipsis),
            isThreeLine:true,
            trailing:const Icon(Icons.chevron_right),onTap:()=>open(row))),
        const SizedBox(height:12),
        const Text('Indicadores atualizados ao consultar a Central. '
          'Este recurso ainda não envia notificações push.',
          style:TextStyle(fontSize:12)),
      ]))),
  );
}
typedef TreatmentRequest=Future<Map<String,dynamic>> Function(
 String mode,{String companyId,String topicId,Map<String,dynamic>? record});
class _TreatmentConversation extends StatefulWidget {
  const _TreatmentConversation({required this.companyId,required this.topicId,
    required this.title,required this.request});
  final String companyId,topicId,title;
  final TreatmentRequest request;
  @override
  State<_TreatmentConversation> createState()=>_TreatmentConversationState();
}
class _TreatmentConversationState extends State<_TreatmentConversation> {
  final note=TextEditingController(),responsible=TextEditingController(),
    date=TextEditingController(),actionId=TextEditingController();
  List<Map<String,dynamic>> events=[];
  bool loading=true,sending=false;
  String type='mensagem',verification='vistoria_in_loco',error='';
  static const types={
    'mensagem':'Mensagem',
    'resposta_tecnica':'Parecer técnico',
    'solicitar_verificacao':'Solicitar verificação',
    'revisao_tecnica':'Revisão técnica',
    'encaminhamento':'Encaminhamento',
    'reuniao':'Reunião de alinhamento',
    'vinculo_acao':'Vincular ação existente',
    'eficacia_confirmada':'Verificação de eficácia',
  };
  @override
  void initState(){super.initState();load();}
  @override
  void dispose(){note.dispose();responsible.dispose();date.dispose();actionId.dispose();super.dispose();}
  Future<void> load() async {
    setState((){loading=true;error='';});
    try {
      final response=await widget.request('list',
        companyId:widget.companyId,topicId:widget.topicId);
      if(mounted)setState((){
        events=[for(final r in response['events'] is List?
          response['events'] as List:const [])
          if(r is Map)Map<String,dynamic>.from(r)];
        loading=false;
      });
    }catch(e){if(mounted)setState((){
      error=e.toString().replaceFirst('Bad state: ','');loading=false;
    });}
  }
  void quick(String next,String text){
    setState(()=>type=next);note.text=text;
  }
  Future<void> send() async {
    if(sending||note.text.trim().isEmpty)return;
    setState(()=>sending=true);
    try {
      await widget.request('post',companyId:widget.companyId,
        topicId:widget.topicId,record:{
        'requestId':'app_'+DateTime.now().microsecondsSinceEpoch.toString()+
          '_'+(AuthService.currentUser?.id??'user')
            .replaceAll(RegExp(r'[^a-zA-Z0-9_-]'),'_'),
        'type':type,'message':note.text.trim(),
        'responsible':responsible.text.trim(),
        'dueDate':date.text.trim(),
        'actionId':type=='vinculo_acao'?actionId.text.trim():'',
        if(type=='eficacia_confirmada')'verificationMethod':verification,
      });
      note.clear();responsible.clear();date.clear();actionId.clear();
      if(mounted)setState(()=>type='mensagem');
      await load();
    }catch(e){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content:Text('Não enviado: '+e.toString())));
    }finally{if(mounted)setState(()=>sending=false);}
  }
  @override
  Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:Text(widget.title,maxLines:2,
      overflow:TextOverflow.ellipsis),
      actions:[IconButton(onPressed:loading?null:load,
        icon:const Icon(Icons.refresh))]),
    body:ListView(padding:const EdgeInsets.all(14),children:[
      if(loading)const LinearProgressIndicator(),
      if(error.isNotEmpty)Text(error),
      for(final row in events)Card(child:Padding(padding:const EdgeInsets.all(12),
        child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
          Text((row['author']??'Participante').toString()+
            (row['role']=='cliente'?' • Empresa':' • Auditar'),
            style:const TextStyle(fontWeight:FontWeight.bold)),
          Text((row['at']??'').toString(),
            style:const TextStyle(fontSize:12)),
          const SizedBox(height:6),
          Text((row['message']??'').toString()),
          if((row['actionId']??'').toString().isNotEmpty)
            Text('Ação: '+row['actionId'].toString()),
        ]))),
      const SizedBox(height:8),
      Text('Registrar resposta',style:Theme.of(context).textTheme.titleMedium),
      Wrap(spacing:6,runSpacing:6,children:[
        ActionChip(label:const Text('Solicitar conferência'),
          onPressed:()=>quick('solicitar_verificacao',
            'Solicitamos conferir a situação durante a operação e informar o resultado.')),
        ActionChip(label:const Text('Ata rápida'),
          onPressed:()=>quick('reuniao',
            'Participantes: \nPontos discutidos: \nDecisões: \nPróximos passos: ')),
        ActionChip(label:const Text('Parecer técnico'),
          onPressed:()=>quick('resposta_tecnica',
            'Após analisar os esclarecimentos, orientamos: ')),
      ]),
      DropdownButtonFormField<String>(key:ValueKey(type),
        initialValue:type,
        items:types.entries.map((x)=>DropdownMenuItem(
          value:x.key,child:Text(x.value))).toList(),
        onChanged:(v){if(v!=null)setState(()=>type=v);},
        decoration:const InputDecoration(labelText:'Tipo',border:OutlineInputBorder())),
      const SizedBox(height:8),
      TextField(controller:note,maxLength:1600,maxLines:4,
        decoration:const InputDecoration(labelText:'Mensagem',
          border:OutlineInputBorder())),
      if(type=='encaminhamento'||type=='reuniao')...[
        TextField(controller:responsible,maxLength:120,
          decoration:const InputDecoration(labelText:'Responsável')),
        TextField(controller:date,
          decoration:const InputDecoration(labelText:'Prazo AAAA-MM-DD')),
      ],
      if(type=='vinculo_acao')
        TextField(controller:actionId,maxLength:120,
          decoration:const InputDecoration(labelText:'ID da ação existente')),
      if(type=='eficacia_confirmada')DropdownButtonFormField<String>(
        initialValue:verification,
        items:const [
          DropdownMenuItem(value:'vistoria_in_loco',child:Text('Vistoria presencial')),
          DropdownMenuItem(value:'teste_funcional',child:Text('Teste funcional')),
          DropdownMenuItem(value:'evidencia_analisada',child:Text('Análise de evidência')),
          DropdownMenuItem(value:'documental',child:Text('Verificação documental')),
        ],
        onChanged:(v){if(v!=null)setState(()=>verification=v);},
        decoration:const InputDecoration(labelText:'Método da verificação')),
      const SizedBox(height:9),
      FilledButton.icon(onPressed:sending?null:send,
        icon:const Icon(Icons.send),
        label:Text(sending?'Enviando...':'Registrar na linha do tempo')),
      OutlinedButton.icon(onPressed:()=>Navigator.of(context).push(
        MaterialPageRoute(builder:(_)=>ActionPlanScreen(companyId:widget.companyId))),
        icon:const Icon(Icons.assignment_outlined),
        label:const Text('Abrir plano de ação')),
      const Text('Os registros originais e o status das NCs permanecem intactos.',
        style:TextStyle(fontSize:12)),
    ]),
  );
}

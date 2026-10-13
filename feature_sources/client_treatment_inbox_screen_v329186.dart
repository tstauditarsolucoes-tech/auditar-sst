import 'dart:convert';
import 'dart:async';
import '../services/treatment_outbox.dart';
import '../services/treatment_outbox_store.dart';
import 'package:flutter/material.dart';
import '../database.dart';
import '../services/auth_service.dart';
import '../services/apps_script_http.dart';
import 'action_plan_screen.dart';

typedef _QueueScope = ({String key,String endpoint,String userId});
Future<_QueueScope> _queueScope() async {
 final user=AuthService.currentUser;
 if(!AuthService.isSignedIn||user==null||!['admin','tecnico'].contains(user.role.toLowerCase()))
  throw TreatmentRejected('Acesso reservado à equipe Auditar.');
 final endpoint=(await AppDatabase.instance.getSetting('management_panel_endpoint')).trim();
 if(!endpoint.startsWith('https://'))throw TreatmentRejected('Configure a Central antes de preparar mensagens.');
 if(user.id!=AuthService.currentUser?.id)throw TreatmentScopeChanged();
 return (key:TreatmentOutbox.scope(endpoint,user.id),endpoint:endpoint,userId:user.id);
}
Future<int> _flushQueue(_QueueScope scope,TreatmentRequest request) =>
 treatmentOutbox.flush(scope.key,(item)async{
  final now=await _queueScope();
  if(now.key!=scope.key)throw TreatmentScopeChanged();
  await request('post',companyId:item['companyId'].toString(),
   topicId:item['topicId'].toString(),expectedEndpoint:scope.endpoint,
   record:Map<String,dynamic>.from(item['record'] as Map));
 });

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
  String error='',filter='Todas',search='';
  List<Map<String,dynamic>> pending=[];
  Timer? _timer;
  String _owner='';
  bool _checking=false;
  int? _lastAwaiting;
  Future<void> retryQueue() async {
    try {final scope=await _queueScope();await treatmentOutbox.retry(scope.key);await load();}
    catch(e){if(mounted)setState(()=>error=e.toString());}
  }
  Future<void> discardPending(Map<String,dynamic> item) async {
    final yes=await showDialog<bool>(context:context,builder:(dialog)=>AlertDialog(
      title:const Text('Remover envio pendente?'),
      content:const Text('Isso remove apenas a tentativa deste aparelho. Não apaga uma mensagem que a Central já tenha recebido.'),
      actions:[TextButton(onPressed:()=>Navigator.pop(dialog,false),child:const Text('Manter')),
        TextButton(onPressed:()=>Navigator.pop(dialog,true),child:const Text('Remover da fila'))]));
    if(yes!=true)return;
    try {final scope=await _queueScope();if(scope.key!=_owner)return;
      await treatmentOutbox.discard(scope.key,item['id'].toString());await load();}
    catch(e){if(mounted)setState(()=>error=e.toString());}
  }

  Future<Map<String,dynamic>> request(String mode,{
    String companyId='',String topicId='',String expectedEndpoint='',Map<String,dynamic>? record}) async {
    final user=AuthService.currentUser,token=AuthService.sessionToken;
    if(!AuthService.isSignedIn||user==null||
       user.role.toLowerCase()=='cliente'||token.isEmpty)
      throw StateError('Acesso reservado à equipe Auditar.');
    if(companyId.isNotEmpty&&!AuthService.canAccessCompany(companyId))
      throw TreatmentRejected('Acesso à empresa não autorizado.');
    final endpoint=(await AppDatabase.instance.getSetting(
      'management_panel_endpoint')).trim();
    if(!endpoint.startsWith('https://'))
      throw StateError('Central não configurada para conexão segura.');
    if(token!=AuthService.sessionToken||user.id!=AuthService.currentUser?.id||
       (expectedEndpoint.isNotEmpty&&endpoint!=expectedEndpoint))throw TreatmentScopeChanged();
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
    if(body['ok']!=true)throw TreatmentRejected((body['message']??
      'Tratativas não implantadas na Central.').toString());
    if(token!=AuthService.sessionToken||user.id!=AuthService.currentUser?.id)
      throw StateError('A conta foi alterada. Atualize a consulta.');
    return body;
  }

  @override
  void initState(){super.initState();load();
    _timer=Timer.periodic(const Duration(seconds:45),(_){
      if(mounted&&!_checking&&ModalRoute.of(context)?.isCurrent==true&&
         WidgetsBinding.instance.lifecycleState==AppLifecycleState.resumed)load(silent:true);
    });
  }
  @override void dispose(){_timer?.cancel();super.dispose();}
  Future<void> load({bool silent=false}) async {
    if(_checking)return;_checking=true;
    if(mounted)setState((){if(!silent)busy=true;error='';});
    try {
      final scope=await _queueScope();
      if(_owner!=scope.key){threads=[];summary={};pending=[];_lastAwaiting=null;_owner=scope.key;}
      await _flushQueue(scope,request);
      final queued=await treatmentOutbox.list(scope.key);
      if((await _queueScope()).key!=scope.key)throw TreatmentScopeChanged();
      if(mounted)setState(()=>pending=queued.where((x)=>
        AuthService.canAccessCompany(x['companyId'].toString())&&
        (widget.companyId.isEmpty||widget.companyId==x['companyId'])).toList());
      final body=await request('inbox',companyId:widget.companyId,expectedEndpoint:scope.endpoint);
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
        final now=count('awaitingAuditar');
        if(silent&&_lastAwaiting!=null&&now>_lastAwaiting!)ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content:Text('Há '+now.toString()+' conversas aguardando a Auditar.')));
        _lastAwaiting=now;
      });
    } catch(e) {
      if(mounted)setState((){
        error=e.toString().replaceFirst('Bad state: ','');busy=false;
      });
    }finally{_checking=false;}
  }
  int count(String key)=>summary[key] is num?(summary[key] as num).toInt():0;
  bool visible(Map<String,dynamic> row) {
    final haystack=[row['companyName'],row['title'],row['lastMessage']].join(' ').toLowerCase();
    if(search.trim().isNotEmpty&&!haystack.contains(search.trim().toLowerCase()))return false;
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
        if(pending.isNotEmpty)Card(child:Padding(padding:const EdgeInsets.all(12),child:Column(
          crossAxisAlignment:CrossAxisAlignment.start,children:[
          Text('Mensagens pendentes: '+pending.length.toString(),style:const TextStyle(fontSize:17,fontWeight:FontWeight.bold)),
          const Text('Guardadas neste aparelho. Tentativas automáticas enquanto esta caixa de entrada estiver aberta.'),
          for(final item in pending)ListTile(
            title:Text(item['title'].toString(),maxLines:2,overflow:TextOverflow.ellipsis),
            subtitle:Text((item['blocked']==true?'Revisar: ':'Aguardando confirmação. ')+(item['error']??'').toString()),
            onTap:()=>showDialog<void>(context:context,builder:(dialog)=>AlertDialog(
              title:Text(item['title'].toString()),content:SingleChildScrollView(child:SelectableText(item['record']['message'].toString())),
              actions:[TextButton(onPressed:()=>Navigator.pop(dialog),child:const Text('Fechar'))])),
            trailing:IconButton(tooltip:'Remover da fila',icon:const Icon(Icons.delete_outline),
              onPressed:()=>discardPending(item))),
          OutlinedButton.icon(onPressed:retryQueue,icon:const Icon(Icons.refresh),label:const Text('Tentar envios novamente')),
        ]))),
        TextField(onChanged:(v)=>setState(()=>search=v),decoration:const InputDecoration(
          labelText:'Buscar empresa, assunto ou mensagem',prefixIcon:Icon(Icons.search),border:OutlineInputBorder())),
        if(widget.companyId.isNotEmpty)OutlinedButton.icon(
          onPressed:()=>open({'companyId':widget.companyId,'topicId':'GERAL','title':'Conversa geral'}),
          icon:const Icon(Icons.edit_note),label:const Text('Escrever conversa geral (também offline)')),
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
      ])),
  );
}
typedef TreatmentRequest=Future<Map<String,dynamic>> Function(
 String mode,{required String companyId,required String topicId,String expectedEndpoint,Map<String,dynamic>? record});
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
  // Messages from this conversation only; kept in the independent encrypted outbox.
  List<Map<String,dynamic>> localPending=[];
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
  Future<void> refreshLocalPending() async {
    try {
      final scope=await _queueScope();
      if (!AuthService.canAccessCompany(widget.companyId)) {
        throw TreatmentRejected('Sem acesso à empresa.');
      }
      final rows=await treatmentOutbox.list(scope.key);
      if(!mounted || (await _queueScope()).key!=scope.key)return;
      setState(()=>localPending=rows.where((entry)=>
        entry['companyId']==widget.companyId &&
        entry['topicId']==widget.topicId).toList());
    }catch(_){
      if(mounted)setState(()=>localPending=[]);
    }
  }
  Future<void> trySendPending() async {
    if(sending)return;
    setState(()=>sending=true);
    try {
      final scope=await _queueScope();
      await _flushQueue(scope,widget.request);
      await refreshLocalPending();
      if(localPending.isEmpty && mounted)await load();
    }catch(e){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content:Text('Não foi possível confirmar os envios: '+e.toString())));
    }finally{
      if(mounted)setState(()=>sending=false);
    }
  }
  @override
  void initState(){super.initState();load();}
  @override
  void dispose(){note.dispose();responsible.dispose();date.dispose();actionId.dispose();super.dispose();}
  Future<void> load() async {
    if(!mounted)return;
    setState((){loading=true;error='';});
    await refreshLocalPending(); // Local messages remain visible even if Central is offline.
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
    if(sending)return;
    setState(()=>type=next);note.text=text;
  }
  Future<void> send() async {
    if(sending||note.text.trim().isEmpty)return;
    if(type=='eficacia_confirmada'&&note.text.trim().length<40){
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Detalhe a verificação em pelo menos 40 caracteres.')));return;
    }
    if(type=='vinculo_acao'&&!RegExp(r'^[a-zA-Z0-9_-]{1,120}$').hasMatch(actionId.text.trim())){
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Informe um ID válido da ação existente.')));return;
    }
    if(date.text.trim().isNotEmpty&&!RegExp(r'^\d{4}-\d{2}-\d{2}$').hasMatch(date.text.trim())){
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Use o prazo no formato AAAA-MM-DD.')));return;
    }
    setState(()=>sending=true);
    bool saved=false;
    try {
      final scope=await _queueScope();
      if(!AuthService.canAccessCompany(widget.companyId))throw TreatmentRejected('Sem acesso à empresa.');
      final queuedId=await treatmentOutbox.enqueue(scope.key,widget.companyId,widget.topicId,widget.title,{
        'type':type,'message':note.text.trim(),'responsible':responsible.text.trim(),
        'dueDate':date.text.trim(),'actionId':type=='vinculo_acao'?actionId.text.trim():'',
        if(type=='eficacia_confirmada')'verificationMethod':verification,
      });
      saved=true;
      await refreshLocalPending();
      if(!mounted)return;
      note.clear();responsible.clear();date.clear();actionId.clear();setState(()=>type='mensagem');
      await _flushQueue(scope,widget.request);
      final remaining=await treatmentOutbox.list(scope.key);
      // Another company's queued message must not change this message's status.
      final thisMessagePending=remaining.any((row)=>row['id']==queuedId);
      await refreshLocalPending();
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(
        thisMessagePending?'Mensagem guardada neste aparelho; envio ainda não confirmado.':
          'Envio confirmado pela Central.')));
      if(mounted&&!thisMessagePending)await load();
    }catch(e){
      if(saved)await refreshLocalPending();
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(
        saved?'Mensagem guardada; confirmação pendente. Consulte a caixa de entrada.':'Não foi possível guardar a mensagem: '+e.toString())));
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
      if(localPending.isNotEmpty)Card(child:Padding(
        padding:const EdgeInsets.all(12),
        child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
          Text('Guardadas neste aparelho • '+localPending.length.toString(),
            style:const TextStyle(fontWeight:FontWeight.bold)),
          const Text('Estas respostas ainda não têm confirmação de recebimento pela Central.'),
          for(final item in localPending.take(20))ListTile(
            dense:true,
            leading:Icon(item['blocked']==true?Icons.report_problem_outlined:Icons.schedule_send_outlined),
            title:Text((item['record'] is Map?
              (item['record'] as Map)['message']:'Mensagem pendente').toString(),
              maxLines:3,overflow:TextOverflow.ellipsis),
            subtitle:Text(item['blocked']==true?
              'Revisão necessária na Caixa de entrada.':
              'Pendente de envio/confirmação.'),
          ),
          if(localPending.length>20)
            const Text('Outras mensagens pendentes podem ser consultadas na Caixa de entrada.'),
          OutlinedButton.icon(onPressed:sending?null:trySendPending,
            icon:const Icon(Icons.sync),
            label:const Text('Tentar enviar pendentes')),
        ]),
      )),
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
      AbsorbPointer(absorbing:sending,child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
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
      TextField(readOnly:sending,controller:note,maxLength:1600,maxLines:4,
        decoration:const InputDecoration(labelText:'Mensagem',
          border:OutlineInputBorder())),
      if(type=='encaminhamento'||type=='reuniao')...[
        TextField(readOnly:sending,controller:responsible,maxLength:120,
          decoration:const InputDecoration(labelText:'Responsável')),
        TextField(readOnly:sending,controller:date,
          decoration:const InputDecoration(labelText:'Prazo AAAA-MM-DD')),
      ],
      if(type=='vinculo_acao')
        TextField(readOnly:sending,controller:actionId,maxLength:120,
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
        label:Text(sending?'Guardando / enviando...':'Registrar mensagem')),
      ])),
      OutlinedButton.icon(onPressed:()=>Navigator.of(context).push(
        MaterialPageRoute(builder:(_)=>ActionPlanScreen(companyId:widget.companyId))),
        icon:const Icon(Icons.assignment_outlined),
        label:const Text('Abrir plano de ação')),
      const Text('Os registros originais e o status das NCs permanecem intactos.',
        style:TextStyle(fontSize:12)),
    ]),
  );
}


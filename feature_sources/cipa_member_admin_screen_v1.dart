import 'dart:convert';
import 'dart:math';

import 'package:flutter/material.dart';

import '../services/apps_script_http.dart';
import '../services/auth_service.dart';
import '../services/web_service_config.dart';
import '../widgets/cipa_manager_metrics_panel.dart';

class CipaAdminMemberOption {
  const CipaAdminMemberOption({
    required this.memberId,required this.workerId,
    required this.name,required this.cipaRole,
  });
  final String memberId,workerId,name,cipaRole;
  String get label=>name+' — '+cipaRole+' da CIPA';
}
class CipaAdminActionOption {
  const CipaAdminActionOption({required this.id,required this.title});
  final String id,title;
}

class CipaAdminDocumentOption {
  const CipaAdminDocumentOption({
    required this.id,required this.title,required this.category,
  });
  final String id,title,category;
  String get label=>title+(category.isEmpty?'':' • '+category);
}

/// Gerenciamento disponível SOMENTE ao administrador. Cada operação é
/// revalidada no Apps Script: não confiar nas seleções desta interface.
class CipaMemberAdminScreen extends StatefulWidget {
  const CipaMemberAdminScreen({super.key,required this.companyId,
    required this.mandateId,required this.members,required this.actions,
    required this.documents});
  final String companyId,mandateId;
  final List<CipaAdminMemberOption> members;
  final List<CipaAdminActionOption> actions;
  final List<CipaAdminDocumentOption> documents;

  @override
  State<CipaMemberAdminScreen> createState()=>_CipaMemberAdminScreenState();
}
class _CipaMemberAdminScreenState extends State<CipaMemberAdminScreen> {
  final email=TextEditingController();
  final tstUserId=TextEditingController();
  final scheduleNote=TextEditingController();
  final noticeTitle=TextEditingController();
  final noticeBody=TextEditingController();
  String? selectedMember,selectedAction,selectedDocument;
  bool confirmNoticeSafe=false,confirmDocumentSafe=false;
  bool busy=false;
  String error='',notice='';
  List<Map<String,dynamic>> accounts=[],inbox=[],notices=[],schedules=[];
  Map<String,dynamic>? metrics;
  DateTime? scheduleDue;
  String scheduleSector='Organização e circulação';
  final Map<String,String> _scheduleRequestIds={};
  final Map<String,String> _pendingReviewIds={};
  final Set<String> publishedDocumentIds={};

  @override
  void initState(){super.initState();_reload();}
  @override
  void dispose(){
    email.dispose();tstUserId.dispose();scheduleNote.dispose();
    noticeTitle.dispose();noticeBody.dispose();super.dispose();
  }

  Future<Map<String,dynamic>> _call(String action,
      [Map<String,dynamic> args=const {}]) async {
    if(!AuthService.isAdmin || AuthService.sessionToken.isEmpty)
      throw StateError('Somente o administrador Auditar pode gerenciar acessos.');
    if(widget.companyId.trim().isEmpty||widget.mandateId.trim().isEmpty)
      throw StateError('Selecione um mandato ativo.');
    final uri=Uri.tryParse(WebServiceConfig.endpoint.trim());
    if(uri==null||uri.scheme!='https')
      throw StateError('Central Online não configurada.');
    final response=await AppsScriptHttp.postJson(uri,{
      'action':action,'authToken':AuthService.sessionToken,
      'companyId':widget.companyId,'mandateId':widget.mandateId,
      ...args,
    });
    if(response.statusCode!=200)
      throw StateError('A Central não respondeu à solicitação.');
    final decoded=jsonDecode(response.body);
    if(decoded is! Map)throw StateError('Resposta inválida da Central.');
    final result=Map<String,dynamic>.from(decoded);
    if(result['ok']!=true)throw StateError(
      (result['message']??result['code']??'Operação não autorizada.').toString());
    return result;
  }

  Future<void> _perform(Future<void> Function() task) async {
    if(busy)return;
    setState((){busy=true;error='';notice='';});
    try {await task();}
    catch(e) {
      if(mounted)setState(()=>error=
        e.toString().replaceFirst('Bad state: ',''));
    } finally {
      if(mounted)setState(()=>busy=false);
    }
  }
  Future<void> _reload() async {
    if(!AuthService.isAdmin || widget.mandateId.isEmpty)return;
    await _perform(() async {
      final saved=await _call('cipa_member_admin_list');
      final pending=await _call('cipa_member_admin_inbox');
      final publication=await _call('cipa_member_admin_publications');
      final calendar=await _call('cipa_schedule_list');
      Map<String,dynamic>? checkedMetrics;
      try {
        final data=await _call('cipa_tst_metrics');
        final scope=data['scope'];
        if(scope is Map&&scope['companyId']==widget.companyId&&
          scope['mandateId']==widget.mandateId)checkedMetrics=data;
      }catch (_) {/* Painel indisponível não bloqueia agenda e vistorias. */}
      if(!mounted)return;
      setState((){
        metrics=checkedMetrics;
        accounts=(saved['accounts'] is List?
          (saved['accounts'] as List).whereType<Map>()
            .map((m)=>Map<String,dynamic>.from(m)).toList():
          <Map<String,dynamic>>[]);
        inbox=(pending['events'] is List?
          (pending['events'] as List).whereType<Map>()
            .map((m)=>Map<String,dynamic>.from(m)).toList():
          <Map<String,dynamic>>[]);
        schedules=(calendar['items'] is List?
          (calendar['items'] as List).whereType<Map>()
            .map((m)=>Map<String,dynamic>.from(m)).toList():
            <Map<String,dynamic>>[]);
        notices=(publication['notices'] is List?
          (publication['notices'] as List).whereType<Map>()
            .map((m)=>Map<String,dynamic>.from(m)).toList():
          <Map<String,dynamic>>[]);
        publishedDocumentIds
          ..clear()
          ..addAll((publication['documents'] is List?
            publication['documents'] as List:const [])
            .whereType<Map>().map((d)=>(d['id']??'').toString())
            .where((id)=>id.isNotEmpty));
      });
    });
  }

  Future<void> _updateTstGrant(String operation) async {
    final id=tstUserId.text.trim();
    if(id.length<3)return;
    await _perform(() async {
      await _call('cipa_tst_review_grant',{
        'userId':id,'operation':operation,
      });
      if(mounted)setState(()=>notice=operation=='grant'?
        'Permissão de resposta solicitada para o TST neste mandato.':
        'Permissão de resposta revogada deste mandato.');
    });
  }

  String _scheduleRequestId(String key)=>
    _scheduleRequestIds.putIfAbsent(key,(){
      final random=Random.secure();
      return 'calendar-'+List<int>.generate(24,(_)=>random.nextInt(256))
        .map((v)=>v.toRadixString(16).padLeft(2,'0')).join();
    });

  Future<void> _scheduleInspection() async {
    if(selectedMember==null||scheduleDue==null||busy)return;
    final due='${scheduleDue!.year.toString().padLeft(4,'0')}-'
      '${scheduleDue!.month.toString().padLeft(2,'0')}-'
      '${scheduleDue!.day.toString().padLeft(2,'0')}';
    final note=scheduleNote.text.trim();
    final key=[selectedMember,scheduleSector,due,note].join('|');
    await _perform(()async {
      await _call('cipa_schedule_create',{
        'memberId':selectedMember,'sector':scheduleSector,
        'dueDate':due,'note':note,
        'requestId':_scheduleRequestId(key),
      });
      _scheduleRequestIds.remove(key);
      if(mounted)setState(()=>notice='Vistoria programada para o integrante.');
    });
    if(mounted&&error.isEmpty)await _reload();
  }

  Future<void> _cancelInspection(String id) async {
    await _perform(()async {
      await _call('cipa_schedule_cancel',{'scheduleId':id});
    });
    if(mounted&&error.isEmpty)await _reload();
  }

  Future<void> _grant() async {
    final selected=widget.members.where((m)=>
      m.memberId==selectedMember).toList();
    if(selected.isEmpty||email.text.trim().isEmpty)return;
    final m=selected.single;
    await _perform(() async {
      await _call('cipa_member_admin_grant',{
        'memberId':m.memberId,
        'workerId':m.workerId,'email':email.text.trim(),
      });
      if(mounted)setState(()=>notice=
        'Acesso cadastrado para '+m.label+'. '
        'O integrante receberá um código somente ao solicitar o login.');
    });
    if(mounted&&error.isEmpty) {
      await _reload();
      if(mounted&&error.isEmpty)setState(()=>notice=
        'Acesso cadastrado e vinculado ao integrante da CIPA.');
    }
  }
  Future<void> _assign() async {
    if(selectedAction==null||selectedMember==null)return;
    await _perform(() async {
      await _call('cipa_member_admin_assign',{
        'memberId':selectedMember,'actionId':selectedAction,
      });
      if(mounted)setState(()=>notice='Ação vinculada ao integrante.');
    });
  }

  Future<void> _publishNotice() async {
    if(!confirmNoticeSafe||noticeTitle.text.trim().length<4||
       noticeBody.text.trim().length<8)return;
    await _perform(()async {
      await _call('cipa_member_admin_publish_notice',{
        'title':noticeTitle.text.trim(),
        'detail':noticeBody.text.trim(),
        'confirmedPublic':true,
      });
      noticeTitle.clear();noticeBody.clear();
      if(mounted)setState(()=>confirmNoticeSafe=false);
    });
    if(mounted&&error.isEmpty)await _reload();
  }

  Future<void> _withdrawNotice(String id) async {
    await _perform(()async {
      await _call('cipa_member_admin_withdraw_notice',{'noticeId':id});
    });
    if(mounted&&error.isEmpty)await _reload();
  }

  Future<void> _publishDocument() async {
    if(!confirmDocumentSafe||selectedDocument==null)return;
    await _perform(()async {
      await _call('cipa_member_admin_publish_document',{
        'documentId':selectedDocument,
        'confirmedSafeMetadata':true,
      });
      if(mounted)setState(()=>confirmDocumentSafe=false);
    });
    if(mounted&&error.isEmpty)await _reload();
  }

  Future<void> _unpublishDocument(String id) async {
    await _perform(()async {
      await _call('cipa_member_admin_unpublish_document',{
        'documentId':id,
      });
    });
    if(mounted&&error.isEmpty)await _reload();
  }

  Future<void> _revoke(String accountId) async {
    await _perform(() async {
      await _call('cipa_member_admin_revoke',{
        'accountId':accountId,
      });
      if(mounted)setState(()=>notice=
        'Acesso revogado. A sessão pessoal existente deixa de funcionar.');
    });
    if(mounted)await _reload();
  }


  String _requestIdForReview(String key) =>
    _pendingReviewIds.putIfAbsent(key,(){
      final r=Random.secure();
      final bytes=List<int>.generate(24,(_)=>r.nextInt(256));
      return 'review-'+bytes.map((b)=>
        b.toRadixString(16).padLeft(2,'0')).join();
    });

  Future<void> _viewPhotos(Map<String,dynamic> event) async {
    if(!AuthService.isAdmin||busy||
       event['companyId']!=widget.companyId||
       event['mandateId']!=widget.mandateId||
       event['kind']!='observation')return;
    final id=(event['id']??'').toString();
    if(id.isEmpty)return;
    final images=<dynamic>[];
    await _perform(()async {
      final info=await _call('cipa_tst_photo_list',{'observationId':id});
      if(info['slots'] is List){
        for(final slot in (info['slots'] as List).whereType<int>().take(2)){
          final pic=await _call('cipa_tst_photo_get',{
            'observationId':id,'slot':slot,
          });
          images.add(base64Decode((pic['jpegBase64']??'').toString()));
        }
      }
    });
    if(!mounted||error.isNotEmpty)return;
    await showDialog<void>(context:context,builder:(dialog)=>AlertDialog(
      title:const Text('Fotos do relato'),
      content:SingleChildScrollView(child:Column(
        mainAxisSize:MainAxisSize.min,
        children:images.isEmpty?[const Text('Nenhuma foto disponível.')]:
          images.map((b)=>Padding(padding:const EdgeInsets.only(bottom:8),
            child:Image.memory(b,width:380,fit:BoxFit.contain))).toList(),
      )),
      actions:[TextButton(onPressed:()=>Navigator.pop(dialog),
        child:const Text('Fechar'))],
    ));
  }

  Future<void> _reviewObservation(Map<String,dynamic> event) async {
    if(busy||!AuthService.isAdmin)return;
    final id=(event['id']??'').toString();
    if(event['kind']!='observation'||id.isEmpty||
        event['companyId']!=widget.companyId||
        event['mandateId']!=widget.mandateId)return;
    String reviewMessage='';
    String status='Em análise';
    final selected=await showDialog<Map<String,String>>(
      context:context,builder:(dialog)=>
      StatefulBuilder(builder:(context,update)=>AlertDialog(
        title:const Text('Orientar integrante da CIPA'),
        content:SingleChildScrollView(child:Column(
          mainAxisSize:MainAxisSize.min,
          crossAxisAlignment:CrossAxisAlignment.stretch,children:[
          const Text('A resposta ficará disponível somente para o '
            'integrante que enviou o relato. Não inclua dados de saúde '
            'nem nomes de outras pessoas.'),
          const SizedBox(height:12),
          DropdownButtonFormField<String>(
            value:status,
            decoration:const InputDecoration(labelText:'Situação'),
            items:const [
              DropdownMenuItem(value:'Em análise',
                child:Text('Em análise')),
              DropdownMenuItem(value:'Orientação enviada',
                child:Text('Orientação enviada')),
            ],
            onChanged:(value)=>update(()=>status=value??'Em análise'),
          ),
          const SizedBox(height:10),
          TextField(maxLength:600,maxLines:4,
            onChanged:(value)=>update(()=>reviewMessage=value),
            decoration:const InputDecoration(
              labelText:'Orientação (opcional em análise)',
              border:OutlineInputBorder())),
          const Text('A orientação não fecha uma não conformidade '
            'nem comprova correção de uma situação.'),
        ])),
        actions:[
          TextButton(onPressed:()=>Navigator.pop(dialog),
            child:const Text('Cancelar')),
          FilledButton(
            onPressed:status=='Orientação enviada'&&
              reviewMessage.trim().length<8?null:
              reviewMessage.trim().isNotEmpty&&reviewMessage.trim().length<8
              ?null:()=>Navigator.pop(dialog,{
                'status':status,'message':reviewMessage.trim()}),
            child:const Text('Registrar devolutiva')),
        ],
      )));
    if(selected==null||!mounted)return;
    final key=[id,selected['status'],selected['message']].join('|');
    await _perform(()async {
      await _call('cipa_member_admin_review_observation',{
        'observationId':id,
        'status':selected['status'],
        'message':selected['message'],
        'requestId':_requestIdForReview(key),
      });
      _pendingReviewIds.remove(key);
      if(mounted)setState(()=>notice='Devolutiva registrada para o membro.');
    });
    if(mounted&&error.isEmpty)await _reload();
  }

  @override
  Widget build(BuildContext context) {
    if(!AuthService.isAdmin)return const Scaffold(
      body:Center(child:Padding(padding:EdgeInsets.all(20),
        child:Text('Acessos individuais são gerenciados apenas pelo '
          'administrador Auditar.'))));
    return Scaffold(
      appBar:AppBar(title:const Text('Acessos da CIPA'),
        actions:[IconButton(onPressed:busy?null:_reload,
          tooltip:'Atualizar',icon:const Icon(Icons.refresh))]),
      body:SafeArea(child:ListView(
        padding:const EdgeInsets.all(12),children:[
          const Card(child:Padding(
            padding:EdgeInsets.all(14),
            child:Text('Cadastre um e-mail para cada integrante. '
              'O acesso ficará limitado à empresa, ao mandato e à pessoa '
              'vinculados. A função aparece junto ao nome do membro. '
              'Não compartilhe o login do técnico ou do administrador.'))),
          if(busy)const LinearProgressIndicator(),
          if(error.isNotEmpty)Card(child:Padding(
            padding:const EdgeInsets.all(10),
            child:Text(error,style:TextStyle(
              color:Theme.of(context).colorScheme.error)))),
          if(notice.isNotEmpty)Card(child:Padding(
            padding:const EdgeInsets.all(10),child:Text(notice))),
          Card(child:Padding(padding:const EdgeInsets.all(14),
            child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,
              children:[
              Text('Autorizar TST para responder vistorias',
                style:Theme.of(context).textTheme.titleMedium),
              const SizedBox(height:6),
              const Text('Somente para esta empresa e mandato. '
                'O TST não recebe acesso ao cadastro administrativo. '
                'Informe o ID da conta técnica já cadastrada.'),
              const SizedBox(height:10),
              TextField(controller:tstUserId,maxLength:120,
                onChanged:(_)=>setState((){}),
                decoration:const InputDecoration(
                  border:OutlineInputBorder(),
                  labelText:'ID do usuário técnico')),
              const SizedBox(height:6),
              Wrap(spacing:10,children:[
                FilledButton.icon(
                  onPressed:busy||tstUserId.text.trim().length<3?
                    null:()=>_updateTstGrant('grant'),
                  icon:const Icon(Icons.verified_user_outlined),
                  label:const Text('Autorizar')),
                OutlinedButton.icon(
                  onPressed:busy||tstUserId.text.trim().length<3?
                    null:()=>_updateTstGrant('revoke'),
                  icon:const Icon(Icons.block),
                  label:const Text('Revogar')),
              ]),
            ]))),
          Card(child:Padding(padding:const EdgeInsets.all(14),
            child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,
              children:[
              Text('Programar vistoria da CIPA',
                style:Theme.of(context).textTheme.titleMedium),
              const Text('Escolha o membro, o tema e a data. '
                'Ele verá essa vistoria em Minha CIPA.'),
              const SizedBox(height:12),
              DropdownButtonFormField<String>(
                isExpanded:true,
                value:selectedMember,
                decoration:const InputDecoration(labelText:'Integrante'),
                items:widget.members.map((m)=>DropdownMenuItem(
                  value:m.memberId,
                  child:Text(m.label,overflow:TextOverflow.ellipsis))).toList(),
                onChanged:busy?null:(v)=>setState(()=>selectedMember=v)),
              const SizedBox(height:12),
              DropdownButtonFormField<String>(
                isExpanded:true,
                value:scheduleSector,
                decoration:const InputDecoration(labelText:'Setor/tema'),
                items:const [
                  'Organização e circulação','Máquinas e equipamentos',
                  'Incêndio e emergência','Ambiente e proteção',
                  'Panificação','Cerâmica','Construção civil',
                  'Laticínios','Logística e depósitos',
                  'Limpeza urbana','Comércio e escritórios',
                ].map((s)=>DropdownMenuItem(
                  value:s,child:Text(s,overflow:TextOverflow.ellipsis)))
                  .toList(),
                onChanged:busy?null:(v)=>setState(()=>
                  scheduleSector=v??'Organização e circulação')),
              const SizedBox(height:12),
              OutlinedButton.icon(
                onPressed:busy?null:() async {
                  final now=DateTime.now();
                  final day=await showDatePicker(
                    context:context,initialDate:now,
                    firstDate:now,lastDate:now.add(const Duration(days:180)));
                  if(day!=null&&mounted)setState(()=>scheduleDue=day);
                },
                icon:const Icon(Icons.event),
                label:Text(scheduleDue==null?'Escolher data':
                  '${scheduleDue!.day}/${scheduleDue!.month}/${scheduleDue!.year}')),
              TextField(controller:scheduleNote,maxLength:180,maxLines:2,
                decoration:const InputDecoration(
                  labelText:'Orientação simples (opcional)')),
              FilledButton.icon(
                onPressed:busy||scheduleDue==null||selectedMember==null?
                  null:_scheduleInspection,
                icon:const Icon(Icons.add_task),
                label:const Text('Programar vistoria')),
              const SizedBox(height:10),
              for(final item in schedules)
                ListTile(
                  title:Text((item['sector']??'Vistoria').toString()),
                  subtitle:Text('Data: ${item['dueDate']}'
                    ' • Membro: ${item['memberId']}'),
                  trailing:TextButton(
                    onPressed:busy?null:()=>
                      _cancelInspection((item['id']??'').toString()),
                    child:const Text('Cancelar')),
                ),
            ]))),
          CipaManagerMetricsPanel(companyId:widget.companyId,
            mandateId:widget.mandateId,serverData:metrics),
          Card(child:Padding(padding:const EdgeInsets.all(12),
            child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,
              children:[
              Text('Acompanhamento dos relatos da CIPA',
                style:Theme.of(context).textTheme.titleMedium),
              const SizedBox(height:10),
              Wrap(spacing:8,runSpacing:8,children:[
                Chip(label:Text('Recebidos: ${inbox.where((e)=>
                  e['kind']=='observation'&&
                  (e['status']??'Recebido')=='Recebido').length}')),
                Chip(label:Text('Em análise: ${inbox.where((e)=>
                  e['kind']=='observation'&&
                  e['status']=='Em análise').length}')),
                Chip(label:Text('Orientações enviadas: ${inbox.where((e)=>
                  e['kind']=='observation'&&
                  e['status']=='Orientação enviada').length}')),
              ]),
              const Text('Contagem dos registros desta consulta. '
                'A orientação não encerra não conformidades.',
                style:TextStyle(fontSize:12)),
            ]))),
          Card(child:ExpansionTile(
            title:Text('Central de Vistorias e Relatos (${inbox.length})'),
            subtitle:const Text('Receber, conferir e orientar o membro'),
            children:inbox.reversed.take(80).map((event){
              final isObservation=event['kind']=='observation';
              final guided=(event['detail']??'').toString()
                .startsWith('VISTORIA ORIENTADA DA CIPA');
              return ListTile(
                title:Text(isObservation?
                  (guided?'Vistoria orientada':'Situação observada'):
                  (event['kind']??'Registro').toString()),
                subtitle:Text([
                  (event['location']??'').toString(),
                  (event['detail']??'').toString(),
                  if(isObservation)
                    'Situação: ${event['status']??'Recebido'}',
                  if((event['feedback']??'').toString().isNotEmpty)
                    'Orientação: ${event['feedback']}',
                ].where((s)=>s.isNotEmpty).join('\n')),
                trailing:isObservation?Wrap(
                  spacing:4,children:[
                    TextButton(onPressed:busy?null:()=>_viewPhotos(event),
                      child:const Text('Ver fotos')),
                    TextButton(onPressed:busy?null:()=>_reviewObservation(event),
                      child:const Text('Orientar')),
                  ]):null,
              );
            }).toList(),
          )),
          Card(child:Padding(padding:const EdgeInsets.all(14),
            child:Column(
              crossAxisAlignment:CrossAxisAlignment.stretch,
              children:[
                Text('Cadastrar acesso individual',
                  style:Theme.of(context).textTheme.titleMedium),
                const SizedBox(height:12),
                DropdownButtonFormField<String>(
                  isExpanded:true,value:selectedMember,
                  decoration:const InputDecoration(labelText:'Integrante da CIPA'),
                  items:widget.members.map((m)=>
                    DropdownMenuItem(value:m.memberId,
                      child:Text(m.label,overflow:TextOverflow.ellipsis)))
                      .toList(),
                  onChanged:busy?null:(v)=>setState(()=>selectedMember=v)),
                const SizedBox(height:10),
                TextField(controller:email,enabled:!busy,
                  onChanged:(_)=>setState((){}),
                  keyboardType:TextInputType.emailAddress,
                  decoration:const InputDecoration(
                    labelText:'E-mail individual do integrante')),
                const SizedBox(height:12),
                FilledButton.icon(
                  onPressed:busy||selectedMember==null||email.text.trim().isEmpty
                    ?null:_grant,
                  icon:const Icon(Icons.person_add_alt_outlined),
                  label:const Text('Autorizar acesso')),
              ]))),
          Card(child:Padding(padding:const EdgeInsets.all(14),
            child:Column(
              crossAxisAlignment:CrossAxisAlignment.stretch,
              children:[
                Text('Vincular tarefa a integrante',
                  style:Theme.of(context).textTheme.titleMedium),
                const SizedBox(height:8),
                const Text('O vínculo usa o identificador do membro, '
                  'não apenas o nome escrito no plano de ação.'),
                const SizedBox(height:12),
                DropdownButtonFormField<String>(
                  value:selectedAction,isExpanded:true,
                  decoration:const InputDecoration(labelText:'Ação da CIPA'),
                  items:widget.actions.map((a)=>DropdownMenuItem(
                    value:a.id,child:Text(a.title,overflow:TextOverflow.ellipsis)))
                      .toList(),
                  onChanged:busy?null:(v)=>setState(()=>selectedAction=v)),
                const SizedBox(height:12),
                OutlinedButton.icon(
                  onPressed:busy||selectedAction==null||selectedMember==null
                    ?null:_assign,
                  icon:const Icon(Icons.assignment_ind_outlined),
                  label:const Text('Vincular tarefa')),
              ]))),

          Card(child:Padding(padding:const EdgeInsets.all(14),
            child:Column(
              crossAxisAlignment:CrossAxisAlignment.stretch,children:[
                Text('Publicar comunicado da CIPA',
                  style:Theme.of(context).textTheme.titleMedium),
                const SizedBox(height:8),
                const Text('Compartilhe somente informações gerais, '
                  'sem dados pessoais, de saúde ou de acidentes identificáveis.'),
                const SizedBox(height:12),
                TextField(controller:noticeTitle,maxLength:160,enabled:!busy,
                  onChanged:(_)=>setState((){}),
                  decoration:const InputDecoration(
                    labelText:'Título do comunicado')),
                const SizedBox(height:8),
                TextField(controller:noticeBody,maxLength:900,maxLines:4,
                  enabled:!busy,onChanged:(_)=>setState((){}),
                  decoration:const InputDecoration(
                    labelText:'Mensagem para os integrantes')),
                CheckboxListTile(
                  contentPadding:EdgeInsets.zero,
                  title:const Text('Revisei e confirmei que este aviso '
                    'pode ser visto pelos integrantes deste mandato.'),
                  value:confirmNoticeSafe,
                  onChanged:busy?null:(v)=>setState(
                    ()=>confirmNoticeSafe=v==true)),
                FilledButton.icon(
                  icon:const Icon(Icons.campaign_outlined),
                  onPressed:busy||!confirmNoticeSafe||
                      noticeTitle.text.trim().length<4||
                      noticeBody.text.trim().length<8
                    ?null:_publishNotice,
                  label:const Text('Publicar comunicado')),
                const SizedBox(height:12),
                Text('Avisos do mandato',
                  style:Theme.of(context).textTheme.titleSmall),
                for(final n in notices.reversed.take(40))
                  ListTile(
                    contentPadding:EdgeInsets.zero,
                    title:Text((n['title']??'').toString()),
                    subtitle:Text((n['active']==true?
                      'Publicado: ':'Retirado: ')+
                      (n['description']??'').toString(),
                      maxLines:3,overflow:TextOverflow.ellipsis),
                    trailing:n['active']==true?
                      TextButton(onPressed:busy?null:()=>
                          _withdrawNotice((n['id']??'').toString()),
                        child:const Text('Retirar')):null,
                  ),
              ],
            ))),
          Card(child:Padding(padding:const EdgeInsets.all(14),
            child:Column(
              crossAxisAlignment:CrossAxisAlignment.stretch,children:[
                Text('Liberar documento para consulta',
                  style:Theme.of(context).textTheme.titleMedium),
                const SizedBox(height:8),
                const Text('Libere apenas o título e a situação de '
                  'documentos de uso geral. PDFs, anexos e conteúdo '
                  'confidencial não são enviados ao membro.'),
                const SizedBox(height:12),
                DropdownButtonFormField<String>(
                  isExpanded:true,value:selectedDocument,
                  decoration:const InputDecoration(
                    labelText:'Documento do mandato'),
                  items:widget.documents.map((d)=>DropdownMenuItem(
                    value:d.id,
                    child:Text(d.label,overflow:TextOverflow.ellipsis)))
                    .toList(),
                  onChanged:busy?null:(v)=>setState(()=>selectedDocument=v)),
                CheckboxListTile(
                  contentPadding:EdgeInsets.zero,
                  value:confirmDocumentSafe,
                  title:const Text('Confirmei que apenas as informações '
                    'deste documento podem ser compartilhadas.'),
                  onChanged:busy?null:(v)=>setState(
                    ()=>confirmDocumentSafe=v==true)),
                OutlinedButton.icon(
                  icon:const Icon(Icons.visibility_outlined),
                  onPressed:busy||!confirmDocumentSafe||
                    selectedDocument==null?null:_publishDocument,
                  label:const Text('Liberar consulta')),
                const SizedBox(height:12),
                Text('Documentos liberados',
                  style:Theme.of(context).textTheme.titleSmall),
                for(final d in widget.documents.where(
                  (d)=>publishedDocumentIds.contains(d.id)))
                  ListTile(
                    contentPadding:EdgeInsets.zero,
                    title:Text(d.title),
                    subtitle:const Text('Metadados publicados, sem anexo'),
                    trailing:TextButton(
                      onPressed:busy?null:()=>_unpublishDocument(d.id),
                      child:const Text('Retirar')),
                  ),
              ],
            ))),
          Card(child:ExpansionTile(
            initiallyExpanded:true,
            title:Text('Contas individuais (${accounts.length})'),
            children:accounts.map((a){
              final id=(a['id']??'').toString();
              final memberId=(a['memberId']??'').toString();
              final found=widget.members.where((m)=>m.memberId==memberId);
              final name=found.isNotEmpty?found.first.label:'Membro registrado';
              final active=a['active']==true;
              return ListTile(
                title:Text(name),
                subtitle:Text((a['email']??'').toString()+
                  (active?' • Ativo':' • Inativo')),
                trailing:active?TextButton(
                  onPressed:busy?null:()=>_revoke(id),
                  child:const Text('Revogar')):const Icon(Icons.lock_outline),
              );
            }).toList(),
          )),

        ],
      )),
    );
  }
}

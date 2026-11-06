import 'dart:convert';

import 'package:flutter/material.dart';

import '../services/apps_script_http.dart';
import '../services/auth_service.dart';
import '../services/web_service_config.dart';

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
  final noticeTitle=TextEditingController();
  final noticeBody=TextEditingController();
  String? selectedMember,selectedAction,selectedDocument;
  bool confirmNoticeSafe=false,confirmDocumentSafe=false;
  bool busy=false;
  String error='',notice='';
  List<Map<String,dynamic>> accounts=[],inbox=[],notices=[];
  final Set<String> publishedDocumentIds={};

  @override
  void initState(){super.initState();_reload();}
  @override
  void dispose(){
    email.dispose();noticeTitle.dispose();noticeBody.dispose();super.dispose();
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
      if(!mounted)return;
      setState((){
        accounts=(saved['accounts'] is List?
          (saved['accounts'] as List).whereType<Map>()
            .map((m)=>Map<String,dynamic>.from(m)).toList():
          <Map<String,dynamic>>[]);
        inbox=(pending['events'] is List?
          (pending['events'] as List).whereType<Map>()
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
          Card(child:ExpansionTile(
            title:Text('Registros recebidos (${inbox.length})'),
            subtitle:const Text('Relatos para avaliação, sem fechar NC'),
            children:inbox.reversed.take(80).map((event)=>ListTile(
              title:Text((event['kind']??'Registro').toString()),
              subtitle:Text((event['location']??'').toString()+
                '\n'+(event['detail']??'').toString()),
            )).toList(),
          )),
        ],
      )),
    );
  }
}

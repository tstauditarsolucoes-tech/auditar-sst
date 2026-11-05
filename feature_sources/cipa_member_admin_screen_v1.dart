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

/// Gerenciamento disponível SOMENTE ao administrador. Cada operação é
/// revalidada no Apps Script: não confiar nas seleções desta interface.
class CipaMemberAdminScreen extends StatefulWidget {
  const CipaMemberAdminScreen({super.key,required this.companyId,
    required this.mandateId,required this.members,required this.actions});
  final String companyId,mandateId;
  final List<CipaAdminMemberOption> members;
  final List<CipaAdminActionOption> actions;

  @override
  State<CipaMemberAdminScreen> createState()=>_CipaMemberAdminScreenState();
}
class _CipaMemberAdminScreenState extends State<CipaMemberAdminScreen> {
  final email=TextEditingController();
  String? selectedMember,selectedAction;
  bool busy=false;
  String error='',notice='';
  List<Map<String,dynamic>> accounts=[],inbox=[];

  @override
  void initState(){super.initState();_reload();}
  @override
  void dispose(){email.dispose();super.dispose();}

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
    if(mounted)await _reload();
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

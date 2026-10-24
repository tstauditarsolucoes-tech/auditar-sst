import 'package:flutter/material.dart';
import '../models.dart';
import '../services/auth_service.dart';

/// Admin-only, company-scoped client account editor alongside report emails.
/// Reuses existing Central auth routes. Never changes report email recipients.
class CompanyClientAccessSection extends StatefulWidget {
  final Company company;
  final TextEditingController reportEmail;
  final TextEditingController reportRecipient;
  const CompanyClientAccessSection({
    super.key, required this.company,
    required this.reportEmail, required this.reportRecipient,
  });
  @override
  State<CompanyClientAccessSection> createState() =>
      _CompanyClientAccessSectionState();
}
class _CompanyClientAccessSectionState extends State<CompanyClientAccessSection> {
  static const labels = <String, String>{
    'indicadores':'Visualizar indicadores',
    'naoConformidades':'Visualizar não conformidades',
    'acoesCorretivas':'Acompanhar ações corretivas',
    'relatorios':'Consultar relatórios e vistorias',
    'enviarEvidencia':'Enviar evidências de correção',
  };
  static const defaults = <String, bool>{
    'indicadores':true, 'naoConformidades':true,
    'acoesCorretivas':true, 'relatorios':true, 'enviarEvidencia':false,
  };
  final name = TextEditingController();
  final email = TextEditingController();
  final password = TextEditingController();
  List<AuditarUser> clients = const [];
  AuditarUser? editing;
  Map<String,bool> permissions = {...defaults};
  bool loading=true, saving=false, showForm=false, active=true, visible=false;
  String error='', notice='';

  @override
  void initState(){super.initState();_load();}
  @override
  void dispose(){name.dispose();email.dispose();password.dispose();super.dispose();}

  Future<void> _load() async {
    if (!AuthService.isAdmin) {
      if(mounted)setState((){
        loading=false;
        error='Entre como administrador Auditar com a Central Online conectada.';
      });
      return;
    }
    if(mounted)setState((){loading=true;error='';});
    try{
      final users=await AuthService.listUsers();
      if(!mounted)return;
      setState((){
        clients=users.where((u)=>u.role.toLowerCase()=='cliente' &&
            u.companyIds.length==1 && u.companyIds.single==widget.company.id)
          .toList()..sort((a,b)=>a.name.toLowerCase()
                            .compareTo(b.name.toLowerCase()));
        loading=false;
      });
    }catch(e){
      if(mounted)setState((){
        loading=false;error='Não foi possível consultar acessos: '+e.toString();
      });
    }
  }
  void _start([AuditarUser? user]){
    name.text=user?.name??'';
    email.text=user?.email??'';
    password.clear();
    setState((){
      editing=user;permissions={...defaults,...?user?.clientPermissions};
      active=user?.active??true;showForm=true;error='';notice='';visible=false;
    });
  }
  void _cancel(){
    password.clear();
    setState((){showForm=false;editing=null;error='';});
  }
  Future<void> _save() async {
    if(saving||!AuthService.isAdmin)return;
    final person=name.text.trim(),address=email.text.trim(),secret=password.text;
    if(person.length<3){setState(()=>error='Informe o nome do contato.');return;}
    if(!RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(address)){
      setState(()=>error='Informe um e-mail de acesso válido.');return;
    }
    if((editing==null||secret.isNotEmpty)&&secret.length<8){
      setState(()=>error='A senha inicial ou nova senha precisa de 8 caracteres.');
      return;
    }
    final duplicate=clients.any((u)=>
        u.id!=editing?.id && u.email.trim().toLowerCase()==address.toLowerCase());
    if(duplicate){
      setState(()=>error='Este e-mail já possui acesso a esta empresa.');
      return;
    }
    if(editing!=null&&(editing!.role.toLowerCase()!='cliente' ||
        editing!.companyIds.length!=1 ||
        editing!.companyIds.single!=widget.company.id)){
      setState(()=>error='Este acesso não pertence à empresa. Atualize a lista.');
      return;
    }
    setState((){saving=true;error='';notice='';});
    try{
      await AuthService.saveUser(
        userId:editing?.id, name:person, email:address, role:'cliente',
        active:active, allCompanies:false, companyIds:[widget.company.id],
        clientPermissions:permissions, password:secret,
      );
      password.clear();
      if(!mounted)return;
      setState((){
        editing=null;showForm=false;
        notice='Acesso salvo. Os e-mails de envio dos relatórios não mudaram.';
      });
      await _load();
    }catch(e){
      if(mounted)setState(()=>error=e.toString().replaceFirst('Bad state: ',''));
    }finally{
      password.clear();
      if(mounted)setState(()=>saving=false);
    }
  }
  @override
  Widget build(BuildContext context){
    if(!AuthService.isAdmin)return const SizedBox.shrink();
    return Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
      const SizedBox(height:14),const Divider(),const SizedBox(height:8),
      const Text('Acessos da empresa ao Painel Gerencial',
          style:TextStyle(fontWeight:FontWeight.w800)),
      const SizedBox(height:5),
      Text('Cadastre quantas pessoas forem necessárias para entrar no painel de '+
          widget.company.name+
          '. Gerência, diretoria, RH e outros responsáveis podem ter e-mail e senha próprios, todos vinculados ao mesmo ambiente da empresa.',
          style:const TextStyle(fontSize:12)),
      const SizedBox(height:6),
      Text(
        clients.isEmpty
            ? 'Nenhum acesso individual cadastrado nesta empresa.'
            : clients.length.toString()+
              (clients.length==1?' acesso individual cadastrado.':' acessos individuais cadastrados.'),
        style:const TextStyle(fontSize:12,fontWeight:FontWeight.w700),
      ),
      const SizedBox(height:4),
      const Text('Cada pessoa usa seu próprio e-mail e senha. Desativar um acesso não interfere nos demais. O e-mail de login é independente dos destinatários de relatórios.',
          style:TextStyle(fontSize:11.5)),
      const SizedBox(height:4),
      const Text('Publique o painel da empresa antes de liberar acesso. '
          'Somente um administrador Auditar pode cadastrar clientes.',
          style:TextStyle(fontSize:11.5)),
      if(loading)const LinearProgressIndicator(),
      if(!loading&&!showForm)...[
        if(clients.isEmpty&&error.isEmpty)
          const Text('Nenhum acesso cadastrado.',
             style:TextStyle(fontSize:12)),
        ...clients.map((u)=>Card(
          margin:const EdgeInsets.only(bottom:5),
          child:ListTile(
            dense:true,
            leading:Icon(u.active?Icons.verified_user_outlined:
                Icons.lock_outline),
            title:Text(u.name),
            subtitle:Text(u.email+' • '+(u.active?'Ativo':'Inativo')),
            trailing:const Icon(Icons.edit_outlined),
            onTap:saving?null:()=>_start(u),
          ),
        )),
        OutlinedButton.icon(
          onPressed:saving?null:()=>_start(),
          icon:const Icon(Icons.person_add_alt_1_outlined),
          label:Text(clients.isEmpty?'Cadastrar primeiro acesso':'Adicionar outro acesso'),
        ),
        TextButton.icon(
          onPressed:saving?null:_load,
          icon:const Icon(Icons.refresh_outlined),
          label:const Text('Atualizar acessos'),
        ),
      ],
      if(showForm)...[
        Text(editing==null?'Novo acesso individual':'Editar acesso individual',
          style:const TextStyle(fontWeight:FontWeight.w700)),
        const SizedBox(height:8),
        TextField(controller:name,enabled:!saving,
          textCapitalization:TextCapitalization.words,
          decoration:const InputDecoration(labelText:'Nome do contato *')),
        const SizedBox(height:8),
        TextField(controller:email,enabled:!saving,
          keyboardType:TextInputType.emailAddress,autocorrect:false,
          decoration:const InputDecoration(labelText:'E-mail de acesso *')),
        const SizedBox(height:8),
        TextField(controller:password,enabled:!saving,obscureText:!visible,
          decoration:InputDecoration(
            labelText:editing==null?'Senha inicial (mín. 8 caracteres) *':
              'Nova senha (deixe vazia para manter)',
            suffixIcon:IconButton(
              onPressed:saving?null:()=>setState(()=>visible=!visible),
              icon:Icon(visible?Icons.visibility_off_outlined:
                       Icons.visibility_outlined),
            ),
          )),
        SwitchListTile(contentPadding:EdgeInsets.zero,
          title:const Text('Conta ativa'),value:active,
          onChanged:saving?null:(value)=>setState(()=>active=value)),
        const Text('Permissões deste acesso',
          style:TextStyle(fontWeight:FontWeight.w700)),
        const SizedBox(height:3),
        const Text('As permissões podem ser diferentes para gerente, diretoria, RH ou outro responsável.',
          style:TextStyle(fontSize:11.5)),
        ...labels.entries.map((e)=>CheckboxListTile(
          dense:true,contentPadding:EdgeInsets.zero,
          value:permissions[e.key]==true,title:Text(e.value),
          onChanged:saving?null:(v)=>setState(()=>permissions[e.key]=v==true),
        )),
        Wrap(spacing:8,runSpacing:8,children:[
          OutlinedButton(onPressed:saving?null:_cancel,
              child:const Text('Cancelar acesso')),
          FilledButton.icon(
            onPressed:saving?null:_save,
            icon:saving?const SizedBox(width:16,height:16,
              child:CircularProgressIndicator(strokeWidth:2)):
              const Icon(Icons.save_outlined),
            label:Text(saving?'Salvando...':'Salvar acesso'),
          ),
        ]),
      ],
      if(error.isNotEmpty)Padding(padding:const EdgeInsets.only(top:8),
        child:Text(error,style:TextStyle(
          color:Theme.of(context).colorScheme.error))),
      if(notice.isNotEmpty)Padding(padding:const EdgeInsets.only(top:8),
        child:Text(notice,style:const TextStyle(fontSize:12))),
    ]);
  }
}

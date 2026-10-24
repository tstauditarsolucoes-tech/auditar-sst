import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';
import '../database.dart';
import '../models.dart';
import '../services/auth_service.dart';
import '../services/apps_script_http.dart';
import '../services/web_service_config.dart';

/// Agenda online. Não altera o mecanismo de sincronização SST.
class TechnicianAgendaScreen extends StatefulWidget {
  const TechnicianAgendaScreen({super.key});
  @override
  State<TechnicianAgendaScreen> createState()=>_TechnicianAgendaScreenState();
}
class _TechnicianAgendaScreenState extends State<TechnicianAgendaScreen> {
  bool busy=false;
  String error='',filter='Todas';
  List<Map<String,dynamic>> tasks=[];
  List<Company> companies=[];
  List<AuditarUser> technicians=[];
  bool get allowed=>AuthService.isSignedIn&&
    (AuthService.isAdmin||AuthService.currentUser?.role=='tecnico');
  @override void initState(){super.initState();_load();}
  Future<Map<String,dynamic>> _post(Map<String,Object?> payload)async{
    if(!allowed)throw StateError('Acesso não autorizado.');
    final actor=AuthService.currentUser?.id,token=AuthService.sessionToken;
    var endpoint=WebServiceConfig.endpoint.trim();
    if(!endpoint.startsWith('https://')){
      endpoint=(await AppDatabase.instance.getSetting('management_panel_endpoint')).trim();
    }
    if(!endpoint.startsWith('https://'))throw StateError('Central não configurada.');
    final response=await AppsScriptHttp.postJson(Uri.parse(endpoint),
      {'action':'agenda_tecnicos_v1','authToken':token,...payload});
    if(!allowed||actor!=AuthService.currentUser?.id||token!=AuthService.sessionToken)
      throw StateError('A sessão mudou. Atualize a tela.');
    final result=jsonDecode(response.body);
    if(response.statusCode!=200||result is! Map||result['ok']!=true){
      throw StateError(result is Map&&(result['message']??'').toString().isNotEmpty?
        result['message'].toString():'Agenda não habilitada na Central. Homologue a rota.');
    }
    return Map<String,dynamic>.from(result);
  }
  Future<void> _load()async{
    if(!allowed)return;
    setState((){busy=true;error='';});
    try{
      final cs=(await AppDatabase.instance.getCompanies())
        .where((c)=>c.active&&AuthService.canAccessCompany(c.id)).toList();
      List<AuditarUser> us=[];
      if(AuthService.isAdmin)us=(await AuthService.listUsers())
        .where((u)=>u.active&&u.role=='tecnico').toList();
      final resp=await _post({'operation':'list'});
      final raw=resp['tasks'];
      if(mounted)setState((){
        companies=cs;technicians=us;
        tasks=raw is List?raw.whereType<Map>()
          .map((e)=>Map<String,dynamic>.from(e)).toList():[];
        busy=false;
      });
    }catch(e){if(mounted)setState((){
      busy=false;error=e.toString().replaceFirst('Bad state: ','');
    });}
  }
  String label(String s){
    switch(s){
      case 'planned':return 'Programada';
      case 'in_progress':return 'Em andamento';
      case 'blocked':return 'Impedida';
      case 'done':return 'Concluída';
      case 'cancelled':return 'Cancelada';
      default:return s;
    }
  }
  String date(Object? v){
    final d=DateTime.tryParse((v??'').toString())?.toLocal();
    if(d==null)return 'Não informada';
    String z(int x)=>x.toString().padLeft(2,'0');
    return z(d.day)+'/'+z(d.month)+' '+z(d.hour)+':'+z(d.minute);
  }
  Future<DateTime?> _date(DateTime initial)async{
    final d=await showDatePicker(context:context,initialDate:initial,
      firstDate:DateTime(2024),lastDate:DateTime(2100));
    if(d==null||!mounted)return null;
    final time=await showTimePicker(context:context,
      initialTime:TimeOfDay.fromDateTime(initial));
    if(time==null)return null;
    return DateTime(d.year,d.month,d.day,time.hour,time.minute);
  }
  Future<void> _create()async{
    if(!AuthService.isAdmin||companies.isEmpty||technicians.isEmpty)return;
    final title=TextEditingController(),notes=TextEditingController();
    String company=companies.first.id,tech=technicians.first.id;
    DateTime when=DateTime.now().add(const Duration(days:1));
    DateTime due=when.add(const Duration(hours:2));
    final requestId=const Uuid().v4();
    final values=await showDialog<Map<String,Object?>>(context:context,
      builder:(ctx)=>StatefulBuilder(builder:(ctx,rebuild)=>AlertDialog(
        title:const Text('Programar serviço'),
        content:SizedBox(width:520,child:SingleChildScrollView(child:Column(
          mainAxisSize:MainAxisSize.min,children:[
          DropdownButtonFormField<String>(value:company,
            decoration:const InputDecoration(labelText:'Empresa'),
            items:[for(final c in companies)DropdownMenuItem(value:c.id,child:Text(c.name))],
            onChanged:(v){if(v!=null)rebuild(()=>company=v);}),
          DropdownButtonFormField<String>(value:tech,
            decoration:const InputDecoration(labelText:'Técnico'),
            items:[for(final u in technicians)DropdownMenuItem(value:u.id,child:Text(u.name))],
            onChanged:(v){if(v!=null)rebuild(()=>tech=v);}),
          TextField(controller:title,maxLength:140,
            decoration:const InputDecoration(labelText:'Atividade')),
          TextField(controller:notes,maxLines:3,maxLength:1800,
            decoration:const InputDecoration(labelText:'Orientações')),
          OutlinedButton(onPressed:()async{
            final next=await _date(when);
            if(next!=null)rebuild((){
              when=next;if(due.isBefore(when))due=when.add(const Duration(hours:2));
            });
          },child:Text('Início: '+date(when.toUtc().toIso8601String()))),
          OutlinedButton(onPressed:()async{
            final next=await _date(due);
            if(next!=null)rebuild(()=>due=next);
          },child:Text('Prazo: '+date(due.toUtc().toIso8601String()))),
        ]))),
        actions:[
          TextButton(onPressed:()=>Navigator.pop(ctx),child:const Text('Voltar')),
          FilledButton(onPressed:()=>Navigator.pop(ctx,{
            'operation':'create','companyId':company,'technicianId':tech,
            'title':title.text.trim(),'description':notes.text.trim(),
            'scheduledAt':when.toUtc().toIso8601String(),
            'dueAt':due.toUtc().toIso8601String(),'requestId':requestId
          }),child:const Text('Programar'))
        ]
      )));
    title.dispose();notes.dispose();
    if(values==null)return;
    if((values['title']??'').toString().length<4){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content:Text('Informe a atividade com pelo menos 4 caracteres.')));
      return;
    }
    setState(()=>busy=true);
    try{await _post(values);await _load();}
    catch(e){if(mounted)setState((){
      busy=false;error=e.toString().replaceFirst('Bad state: ','');
    });}
  }
  Future<void> _status(Map<String,dynamic> task,String next)async{
    if(!allowed)return;
    final ctl=TextEditingController();
    final required=next=='done'||next=='blocked';
    final reason=await showDialog<String>(context:context,builder:(ctx)=>AlertDialog(
      title:Text(label(next)),
      content:required?TextField(controller:ctl,maxLines:3,maxLength:500,
        decoration:const InputDecoration(labelText:'Justificativa / resumo')):
        const Text('Confirmar a mudança de situação?'),
      actions:[
        TextButton(onPressed:()=>Navigator.pop(ctx),child:const Text('Voltar')),
        FilledButton(onPressed:()=>Navigator.pop(ctx,ctl.text.trim()),
          child:const Text('Confirmar'))
      ]));
    ctl.dispose();
    if(reason==null)return;
    if(required&&reason.length<5){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content:Text('Explique em pelo menos 5 caracteres.')));
      return;
    }
    setState(()=>busy=true);
    try{
      await _post({'operation':'status','taskId':task['id'].toString(),
        'status':next,'reason':reason});
      await _load();
    }catch(e){if(mounted)setState((){
      busy=false;error=e.toString().replaceFirst('Bad state: ','');
    });}
  }
  Widget _task(Map<String,dynamic> t){
    final state=(t['status']??'planned').toString();
    final finalState=state=='done'||state=='cancelled';
    final who=technicians.where((u)=>u.id==t['technicianId'])
      .map((u)=>u.name).join(', ');
    return Card(child:Padding(padding:const EdgeInsets.all(15),child:Column(
      crossAxisAlignment:CrossAxisAlignment.start,children:[
      Text((t['title']??'Serviço').toString(),
        style:const TextStyle(fontSize:16,fontWeight:FontWeight.w800)),
      Text(label(state)+' · '+date(t['scheduledAt'])+' · Prazo '+date(t['dueAt'])),
      if(who.isNotEmpty)Text('Responsável: '+who),
      if((t['description']??'').toString().isNotEmpty)
        Text(t['description'].toString()),
      if((t['lastReason']??'').toString().isNotEmpty)
        Text('Último comentário: '+t['lastReason'].toString()),
      if(!finalState)Wrap(spacing:7,children:[
        if(state!='in_progress')OutlinedButton(
          onPressed:busy?null:()=>_status(t,'in_progress'),
          child:const Text('Iniciar / retomar')),
        OutlinedButton(onPressed:busy?null:()=>_status(t,'blocked'),
          child:const Text('Impedimento')),
        FilledButton(onPressed:busy?null:()=>_status(t,'done'),
          child:const Text('Concluir')),
        if(AuthService.isAdmin)TextButton(onPressed:busy?null:()=>_status(t,'cancelled'),
          child:const Text('Cancelar'))
      ])
    ])));
  }
  @override Widget build(BuildContext context){
    if(!allowed)return Scaffold(appBar:AppBar(title:const Text('Agenda SST')),
      body:const Center(child:Text('Área restrita à equipe Auditar.')));
    final visible=tasks.where((x){
      final status=(x['status']??'').toString();
      if(filter=='Pendentes')return status=='planned'||status=='in_progress';
      if(filter=='Impedidas')return status=='blocked';
      if(filter=='Concluídas')return status=='done';
      return true;
    }).toList();
    return Scaffold(appBar:AppBar(title:const Text('Agenda SST'),actions:[
      if(AuthService.isAdmin)IconButton(tooltip:'Programar atividade',
        onPressed:busy?null:_create,icon:const Icon(Icons.add)),
      IconButton(tooltip:'Atualizar',onPressed:busy?null:_load,
        icon:const Icon(Icons.refresh))
    ]),body:ListView(padding:const EdgeInsets.all(16),children:[
      const Text('Serviços e visitas',style:TextStyle(fontSize:22,fontWeight:FontWeight.w800)),
      const Text('Agenda online: o registro não substitui a vistoria ou a conclusão oficial de NC.'),
      if(busy)const LinearProgressIndicator(),
      if(error.isNotEmpty)Padding(padding:const EdgeInsets.all(14),
        child:Text(error,style:TextStyle(color:Theme.of(context).colorScheme.error))),
      if(AuthService.isAdmin)FilledButton.icon(onPressed:busy?null:_create,
        icon:const Icon(Icons.add_task),label:const Text('Programar serviço')),
      Wrap(spacing:6,children:[
        for(final f in const ['Todas','Pendentes','Impedidas','Concluídas'])
          ChoiceChip(label:Text(f),selected:filter==f,
            onSelected:(_)=>setState(()=>filter=f)),
      ]),
      if(visible.isEmpty)const Padding(padding:EdgeInsets.all(20),
        child:Text('Nenhuma atividade disponível.')),
      for(final t in visible)_task(t),
    ]));
  }
}

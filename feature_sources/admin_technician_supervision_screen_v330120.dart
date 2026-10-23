import 'dart:convert';
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../brand.dart';
import '../database.dart';
import '../services/auth_service.dart';
import '../services/apps_script_http.dart';
import '../services/web_service_config.dart';

/// Supervisão Windows para ADM. Somente leitura; ausência de rota não cria dados fictícios.
class AdminTechnicianSupervisionScreen extends StatefulWidget {
  const AdminTechnicianSupervisionScreen({super.key});
  @override
  State<AdminTechnicianSupervisionScreen> createState() => _AdminTechnicianSupervisionScreenState();
}
class _AdminTechnicianSupervisionScreenState extends State<AdminTechnicianSupervisionScreen> {
  List<Map<String,dynamic>> technicians=[],events=[];
  bool loading=false;
  String error='',search='',selectedId='';
  int days=7;
  Timer? timer;
  bool get allowed => AuthService.isSignedIn && AuthService.isAdmin;
  @override
  void initState(){super.initState();_load();timer=Timer.periodic(const Duration(minutes:2),(_){if(mounted&&!loading)_load();});}
  @override
  void dispose(){timer?.cancel();super.dispose();}
  Future<void> _load() async {
    if(!allowed){if(mounted)setState(()=>error='Área exclusiva do ADM.');return;}
    setState((){loading=true;error='';});
    final token=AuthService.sessionToken,actor=AuthService.currentUser?.id;
    try{
      var endpoint=WebServiceConfig.endpoint.trim();
      if(!endpoint.startsWith('https://'))endpoint=(await AppDatabase.instance.getSetting('management_panel_endpoint')).trim();
      if(!endpoint.startsWith('https://'))throw StateError('Central Online não configurada.');
      final response=await AppsScriptHttp.postJson(Uri.parse(endpoint),
        {'action':'technician_supervision_v1','authToken':token,'days':days,'limit':200});
      if(!allowed||token!=AuthService.sessionToken||actor!=AuthService.currentUser?.id)return;
      if(response.statusCode!=200)throw StateError('Central indisponível.');
      final data=jsonDecode(response.body);
      if(data is! Map || data['ok']!=true)throw StateError('O módulo de supervisão ainda não foi habilitado na Central. Homologue o GS e sua rota.');
      List<Map<String,dynamic>> list(Object? input)=>input is List
       ? input.whereType<Map>().map((x)=>Map<String,dynamic>.from(x)).toList()
       : <Map<String,dynamic>>[];
      if(mounted)setState((){technicians=list(data['technicians']);events=list(data['events']);loading=false;});
    }catch(e){if(mounted)setState((){loading=false;error=e.toString().replaceFirst('Bad state: ','');});}
  }
  String ago(Object? raw){
    final n=raw is num?raw.toInt():null;
    if(n==null)return 'Sem registro';
    if(n<2)return 'Agora há pouco';
    if(n<60)return 'Há '+n.toString()+' min';
    if(n<1440)return 'Há '+(n~/60).toString()+' h';
    return 'Há '+(n~/1440).toString()+' dia(s)';
  }
  String stamp(Object? value){
    final d=DateTime.tryParse((value??'').toString())?.toLocal();
    if(d==null)return 'Sem registro';
    String two(int n)=>n.toString().padLeft(2,'0');
    return two(d.day)+'/'+two(d.month)+'/'+d.year.toString()+' '+two(d.hour)+':'+two(d.minute);
  }
  String action(Map<String,dynamic> e){
    const names={'inspections':'Vistoria','non_conformities':'Não conformidade',
      'action_plans':'Plano de ação','sst_records':'Registro SST',
      'evidence_photos':'Foto de evidência','completion_photos':'Foto de correção',
      'training_controls':'Treinamento','workers':'Trabalhador','sectors':'Setor',
      'worksites':'Obra'};
    final kind=(e['action']??'').toString();
    if(kind=='login')return 'Entrada no aplicativo';
    if(kind=='logout')return 'Saída do aplicativo';
    return (names[e['entityType']]??'Registro')+(kind=='record_delete'?' excluído':' sincronizado');
  }
  String productivity(Map<String,dynamic> t) {
    final p=t['productivity'];
    if(p is! Map)return 'Sem indicadores no período';
    int n(String k){final v=p[k];return v is num?v.toInt():0;}
    return 'Vistorias '+n('inspections').toString()+' · NCs '+
      n('nonConformities').toString()+' · Ações '+
      n('actionPlans').toString()+' · Fotos '+n('photos').toString();
  }
  Future<void> copyReport() async {
    if(!allowed)return;
    final report=<String>[
      'Auditar SST | Atividades da equipe',
      'Período: '+days.toString()+' dia(s)',
      'Eventos sincronizados; não comprova número de serviços distintos nem backup das fotos.',
      for(final t in technicians)
        (t['name']??'Técnico').toString()+' — '+(t['status']??'').toString()+
        ' — '+ago(t['minutesSinceActivity'])+' — '+productivity(t)
    ].join('\\n');
    await Clipboard.setData(ClipboardData(text:report));
    if(mounted)ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content:Text('Resumo copiado para conferência.')));
  }
  Widget tech(Map<String,dynamic> t){
    final id=(t['id']??'').toString(),status=(t['status']??'').toString();
    final current=id==selectedId;
    return Card(color:current?const Color(0xffeaf5ff):Colors.white,child:ListTile(
      onTap:()=>setState(()=>selectedId=current?'':id),
      leading:CircleAvatar(backgroundColor:status=='Ativo recentemente'?const Color(0xffd9f5e5):const Color(0xffedf1f5),
        child:Icon(Icons.engineering_outlined,color:status=='Ativo recentemente'?const Color(0xff18804a):AuditarBrand.navy)),
      title:Text((t['name']??'Técnico').toString(),style:const TextStyle(fontWeight:FontWeight.w700)),
      subtitle:Text(status+' · '+ago(t['minutesSinceActivity'])+'\nÚltima atividade: '+stamp(t['lastActivityAt'])+'\n'+productivity(t),
        style:const TextStyle(fontSize:12)),
      isThreeLine:true,trailing:Icon(current?Icons.check_circle:Icons.chevron_right)));
  }
  @override
  Widget build(BuildContext context){
    if(!allowed)return Scaffold(appBar:AppBar(title:const Text('Atividade dos técnicos')),
      body:const Center(child:Text('Área exclusiva do ADM.')));
    final q=search.toLowerCase().trim();
    final visible=technicians.where((t)=>q.isEmpty||(t['name']??'').toString().toLowerCase().contains(q)
      ||(t['email']??'').toString().toLowerCase().contains(q)).toList();
    final history=events.where((e)=>selectedId.isEmpty||e['userId']==selectedId).take(120).toList();
    final recent=technicians.where((t)=>t['status']=='Ativo recentemente').length;
    Widget logs()=>Card(child:Padding(padding:const EdgeInsets.all(14),child:Column(
      crossAxisAlignment:CrossAxisAlignment.start,children:[
      const Text('Histórico registrado na Central',style:TextStyle(fontSize:17,fontWeight:FontWeight.bold)),
      const SizedBox(height:7),
      const Text('Ações offline aparecem após sincronizar. Ativo recentemente não significa aplicativo aberto.',
        style:TextStyle(fontSize:12)),
      if(history.isEmpty)const Padding(padding:EdgeInsets.all(16),child:Text('Sem registros neste período.')),
      for(final e in history)ListTile(dense:true,leading:const Icon(Icons.history),
        title:Text(action(e)),subtitle:Text((e['userName']??'').toString()+' · '+stamp(e['at'])+
          ((e['companyId']??'').toString().isEmpty?'':' · Empresa '+e['companyId'].toString())),
        trailing:Text((e['platform']??'').toString(),style:const TextStyle(fontSize:11)))
    ])));
    return Scaffold(backgroundColor:AuditarBrand.background,
      appBar:AppBar(title:const Text('Atividade dos técnicos'),actions:[
        IconButton(tooltip:'Atualizar',onPressed:loading?null:_load,icon:const Icon(Icons.refresh))]),
      body:LayoutBuilder(builder:(context,c){
        final wide=c.maxWidth>=980;
        return ListView(padding:const EdgeInsets.all(18),children:[
          const Text('Supervisão da equipe · ADM',style:TextStyle(fontSize:24,fontWeight:FontWeight.w800)),
          const SizedBox(height:7),
          const Text('Ativo recentemente = última comunicação autenticada com a Central em até 15 minutos. Não confirma presença na tela.',
            style:TextStyle(fontSize:12)),
          const SizedBox(height:13),
          Wrap(spacing:10,runSpacing:10,children:[
            Chip(label:Text('Técnicos: '+technicians.length.toString())),
            Chip(label:Text('Ativos recentemente: '+recent.toString())),
            Chip(label:Text('Demais estados: '+(technicians.length-recent).toString()))]),
          if(loading)const LinearProgressIndicator(),
          if(error.isNotEmpty)Padding(padding:const EdgeInsets.symmetric(vertical:12),
            child:Text(error,style:TextStyle(color:Theme.of(context).colorScheme.error))),
          const SizedBox(height:15),
          Wrap(spacing:14,runSpacing:8,crossAxisAlignment:WrapCrossAlignment.center,children:[
            SizedBox(width:310,child:TextField(onChanged:(v)=>setState(()=>search=v),
              decoration:const InputDecoration(labelText:'Buscar técnico',prefixIcon:Icon(Icons.search),border:OutlineInputBorder()))),
            OutlinedButton.icon(onPressed:technicians.isEmpty?null:copyReport,
              icon:const Icon(Icons.copy_outlined),label:const Text('Copiar resumo')),
            DropdownButton<int>(value:days,items:const [
              DropdownMenuItem(value:1,child:Text('24 horas')),DropdownMenuItem(value:7,child:Text('7 dias')),
              DropdownMenuItem(value:30,child:Text('30 dias')),DropdownMenuItem(value:90,child:Text('90 dias'))],
              onChanged:(d){if(d!=null){days=d;_load();}}),
            if(selectedId.isNotEmpty)TextButton(onPressed:()=>setState(()=>selectedId=''),child:const Text('Todos os técnicos'))]),
          const SizedBox(height:12),
          if(wide)Row(crossAxisAlignment:CrossAxisAlignment.start,children:[
            SizedBox(width:370,child:Column(children:visible.map(tech).toList())),
            const SizedBox(width:12),Expanded(child:logs())])
          else ...[...visible.map(tech),const SizedBox(height:12),logs()]
        ]);
      }));
  }
}
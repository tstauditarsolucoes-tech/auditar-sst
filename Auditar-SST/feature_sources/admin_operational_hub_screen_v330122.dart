import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../brand.dart';
import '../database.dart';
import '../models.dart';
import '../services/auth_service.dart';
import 'client_treatment_inbox_screen.dart';
import 'company_portfolio_management_screen.dart';
import 'company_timeline_screen.dart';
import 'correction_evidence_center_screen.dart';
import 'evidence_backup_screen.dart';
import 'field_operational_control_screen.dart';
import 'history_screen.dart';
import 'quick_visit_screen.dart';

class AdminOperationalHubScreen extends StatefulWidget {
  const AdminOperationalHubScreen({super.key});
  @override
  State<AdminOperationalHubScreen> createState()=>_AdminOperationalHubScreenState();
}
class _CompanyPulse {
  const _CompanyPulse(this.company,this.visits,this.ncs,this.critical,
    this.overdue,this.trainings,this.lastVisit,{this.error});
  final Company company;
  final int visits,ncs,critical,overdue,trainings;
  final DateTime? lastVisit;
  final String? error;
  int get score=>critical*3+overdue*2+ncs;
}
class _AdminOperationalHubScreenState extends State<AdminOperationalHubScreen> {
  List<_CompanyPulse> data=[];
  bool busy=true;
  String error='',search='',filter='Todas',selected='';
  bool get adm=>AuthService.isSignedIn&&AuthService.isAdmin;
  @override void initState(){super.initState();_load();}
  bool _done(Map<String,Object?> row){
    final s=(row['status']??'').toString().toLowerCase();
    return s.contains('conclu')||s.contains('resolvid')||s.contains('finaliz');
  }
  Future<_CompanyPulse> _read(Company c) async {
    try {
      final db=AppDatabase.instance;
      final ncs=await db.getNonConformityRows(companyId:c.id,includeClosed:true);
      final actions=await db.getPendingActions(companyId:c.id,includeCompleted:true);
      final visits=await db.getInspectionHistory(companyId:c.id);
      final training=await db.getTrainingSummary(companyId:c.id);
      final open=ncs.where((row)=>!_done(row)).toList();
      final critical=open.where((row){
        final priority=[row['priority'],row['classification'],row['severity']]
          .join(' ').toLowerCase();
        return priority.contains('alta')||priority.contains('crit');
      }).length;
      final now=DateTime.now();
      final today=DateTime(now.year,now.month,now.day);
      final overdue=actions.where((row){
        if(_done(row))return false;
        final due=DateTime.tryParse((row['due_date']??'').toString());
        return due!=null&&DateTime(due.year,due.month,due.day).isBefore(today);
      }).length;
      DateTime? last;
      for(final visit in visits){
        final at=DateTime.tryParse((visit['date']??'').toString());
        if(at!=null&&(last==null||at.isAfter(last)))last=at;
      }
      return _CompanyPulse(c,visits.length,open.length,critical,overdue,
        training['expired']??0,last);
    }catch(_){
      return _CompanyPulse(c,0,0,0,0,0,null,error:'Leitura indisponível');
    }
  }
  Future<void> _load() async {
    if(!adm){if(mounted)setState(()=>busy=false);return;}
    final actor=AuthService.currentUser?.id;
    setState((){busy=true;error='';});
    try {
      final companies=(await AppDatabase.instance.getCompanies())
        .where((c)=>c.active&&AuthService.canAccessCompany(c.id)).toList();
      final values=<_CompanyPulse>[];
      for(var i=0;i<companies.length;i+=4){
        values.addAll(await Future.wait(companies.skip(i).take(4).map(_read)));
        if(!mounted||!adm||actor!=AuthService.currentUser?.id)return;
      }
      values.sort((a,b){
        if(a.error!=null&&b.error==null)return 1;
        if(b.error!=null&&a.error==null)return -1;
        final n=b.score.compareTo(a.score);
        return n!=0?n:a.company.name.compareTo(b.company.name);
      });
      if(mounted&&adm&&actor==AuthService.currentUser?.id)setState((){
        data=values;busy=false;
        if(!data.any((e)=>e.company.id==selected))selected='';
      });
    }catch(_){
      if(mounted)setState((){busy=false;error='Não foi possível carregar os registros locais.';});
    }
  }
  List<_CompanyPulse> get shown=>data.where((e){
    if(search.trim().isNotEmpty&&!e.company.name.toLowerCase()
        .contains(search.trim().toLowerCase()))return false;
    switch(filter){
      case 'Críticas':return e.error==null&&e.critical>0;
      case 'Vencidas':return e.error==null&&e.overdue>0;
      case 'Sem vistoria':return e.error==null&&e.lastVisit==null;
      default:return true;
    }
  }).toList();
  _CompanyPulse? get active {
    for(final p in shown){if(p.company.id==selected)return p;}
    return shown.isEmpty?null:shown.first;
  }
  String stamp(DateTime? d){
    if(d==null)return 'Sem registro';
    String two(int v)=>v.toString().padLeft(2,'0');
    return two(d.day)+'/'+two(d.month)+'/'+d.year.toString();
  }
  Future<void> _copy() async {
    if(!adm)return;
    final lines=<String>[
      'Auditar SST — Central Operacional ADM',
      'Indicadores locais: confirmar atualidade pela sincronização antes de compartilhar.',
      'Empresa;NCs abertas;NCs críticas;Ações vencidas;Vistorias;Última vistoria',
      for(final p in shown)if(p.error==null)
        p.company.name.replaceAll(';',',')+';'+p.ncs.toString()+';'+
        p.critical.toString()+';'+p.overdue.toString()+';'+
        p.visits.toString()+';'+stamp(p.lastVisit)
    ];
    await Clipboard.setData(ClipboardData(text:lines.join('\n')));
    if(mounted)ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content:Text('Resumo gerencial copiado.')));
  }
  Future<void> _go(Widget page)async{
    if(!adm)return;
    await Navigator.of(context).push(MaterialPageRoute(builder:(_)=>page));
    if(mounted)_load();
  }
  Widget _stat(String name,int count,IconData icon)=>Container(
    constraints:const BoxConstraints(minWidth:158),
    padding:const EdgeInsets.all(16),
    decoration:BoxDecoration(color:Colors.white,border:Border.all(color:AuditarBrand.line),
      borderRadius:BorderRadius.circular(14)),
    child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
      Icon(icon,color:AuditarBrand.navy),
      const SizedBox(height:9),
      Text(count.toString(),style:const TextStyle(fontSize:24,fontWeight:FontWeight.w800)),
      Text(name,style:const TextStyle(fontSize:13))
    ]));
  Widget _shortcut(String name,IconData icon,VoidCallback action)=>
    OutlinedButton.icon(icon:Icon(icon,size:19),label:Text(name),onPressed:action);
  Widget _left()=>Column(children:[
    Padding(padding:const EdgeInsets.all(10),child:TextField(
      decoration:const InputDecoration(labelText:'Buscar empresa',
        prefixIcon:Icon(Icons.search),border:OutlineInputBorder()),
      onChanged:(v)=>setState(()=>search=v))),
    SingleChildScrollView(scrollDirection:Axis.horizontal,child:Row(children:[
      for(final f in const ['Todas','Críticas','Vencidas','Sem vistoria'])
        Padding(padding:const EdgeInsets.symmetric(horizontal:3),
          child:ChoiceChip(label:Text(f),selected:filter==f,
            onSelected:(_)=>setState(()=>filter=f)))
    ])),
    Expanded(child:ListView(children:[
      for(final p in shown)Card(
        color:selected==p.company.id?const Color(0xffe6f3fb):Colors.white,
        child:ListTile(
          title:Text(p.company.name,style:const TextStyle(fontWeight:FontWeight.bold)),
          subtitle:Text(p.error??('NCs: '+p.ncs.toString()+
            ' • Vencidas: '+p.overdue.toString()+
            '\nÚltima vistoria: '+stamp(p.lastVisit)),
            style:const TextStyle(fontSize:12)),
          isThreeLine:true,
          leading:Icon(p.critical>0?Icons.warning_amber:Icons.business,
            color:p.critical>0?Colors.deepOrange:AuditarBrand.navy),
          onTap:()=>setState(()=>selected=p.company.id),
          trailing:const Icon(Icons.chevron_right)))
    ]))
  ]);
  Widget _right(_CompanyPulse? p) {
    if(p==null)return const Center(child:Text('Selecione uma empresa.',
      style:TextStyle(fontSize:17)));
    if(p.error!=null)return Center(child:Text(p.error!));
    final c=p.company;
    return ListView(padding:const EdgeInsets.all(20),children:[
      Text(c.name,style:const TextStyle(fontSize:23,fontWeight:FontWeight.w800)),
      Text('Última vistoria: '+stamp(p.lastVisit)),
      const SizedBox(height:15),
      Wrap(spacing:10,runSpacing:10,children:[
        _stat('NCs abertas',p.ncs,Icons.warning_amber_outlined),
        _stat('NCs críticas',p.critical,Icons.priority_high),
        _stat('Ações vencidas',p.overdue,Icons.event_busy),
        _stat('Vistorias',p.visits,Icons.fact_check_outlined),
        _stat('Treinamentos vencidos',p.trainings,Icons.school_outlined)
      ]),
      const SizedBox(height:18),
      const Text('Ações disponíveis',style:TextStyle(fontSize:18,fontWeight:FontWeight.w800)),
      const SizedBox(height:10),
      Wrap(spacing:9,runSpacing:9,children:[
        _shortcut('NCs e prazos',Icons.assignment_late_outlined,
          ()=>_go(FieldOperationalControlScreen(initialCompanyId:c.id))),
        _shortcut('Fotos antes/depois',Icons.compare_outlined,
          ()=>_go(CorrectionEvidenceCenterScreen(company:c))),
        _shortcut('Backup de evidências',Icons.cloud_done,
          ()=>_go(EvidenceBackupScreen(company:c))),
        _shortcut('Linha do tempo',Icons.timeline,
          ()=>_go(CompanyTimelineScreen(company:c))),
        _shortcut('Correções do cliente',Icons.message_outlined,
          ()=>_go(ClientTreatmentInboxScreen(companyId:c.id,companyName:c.name))),
        _shortcut('Relatórios',Icons.description_outlined,
          ()=>_go(HistoryScreen(companyId:c.id)))
      ]),
      const SizedBox(height:20),
      const Text('Atenção: dados existentes neste dispositivo. '
        'Para confirmar os resultados de todos os técnicos, consulte a Central Online. '
        'Uma correção enviada não encerra a NC sem validação técnica. '
        'A confirmação das fotos depende da auditoria de backup.',
        style:TextStyle(fontSize:12.5))
    ]);
  }
  @override Widget build(BuildContext context){
    if(!adm)return Scaffold(appBar:AppBar(title:const Text('Central Operacional')),
      body:const Center(child:Text('Acesso restrito à conta ADM.')));
    return Scaffold(
      appBar:AppBar(title:const Text('Central Operacional ADM'),actions:[
        IconButton(tooltip:'Copiar resumo',onPressed:busy?null:_copy,
          icon:const Icon(Icons.copy_outlined)),
        IconButton(tooltip:'Atualizar',onPressed:busy?null:_load,
          icon:const Icon(Icons.refresh))
      ]),
      body:Column(children:[
        Padding(padding:const EdgeInsets.all(12),child:Wrap(spacing:9,runSpacing:9,children:[
          _shortcut('Carteira de empresas',Icons.business_center,
            ()=>_go(const CompanyPortfolioManagementScreen())),
          _shortcut('Registrar visita',Icons.add_task,
            ()=>_go(const QuickVisitScreen())),
          _shortcut('Comunicação SST',Icons.forum,
            ()=>_go(const ClientTreatmentInboxScreen()))
        ])),
        if(busy)const LinearProgressIndicator(),
        if(error.isNotEmpty)Padding(padding:const EdgeInsets.all(10),child:Text(error)),
        Expanded(child:LayoutBuilder(builder:(context,s){
          if(s.maxWidth>=940)return Row(children:[
            SizedBox(width:360,child:_left()),const VerticalDivider(width:1),
            Expanded(child:_right(active))
          ]);
          return Column(children:[
            SizedBox(height:305,child:_left()),const Divider(height:1),
            Expanded(child:_right(active))
          ]);
        }))
      ]));
  }
}

import 'dart:io';

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:uuid/uuid.dart';

import '../brand.dart';
import '../database.dart';
import '../models.dart';
import '../services/auth_service.dart';
import '../services/media_sync_service.dart';
import 'action_plan_screen.dart';
import 'evidence_backup_screen.dart';
import 'express_round_screen.dart';
import 'history_screen.dart';
import 'non_conformities_screen.dart';
import 'routine_hub_screen.dart';
import 'trainings_screen.dart';
import 'workers_screen.dart';

class SmartSstCenterScreen extends StatefulWidget {
  final String? initialCompanyId;
  const SmartSstCenterScreen({super.key, this.initialCompanyId});
  @override
  State<SmartSstCenterScreen> createState() => _SmartSstCenterScreenState();
}

class _SmartSstCenterScreenState extends State<SmartSstCenterScreen> {
  final _search = TextEditingController();
  final _dateTime = DateFormat('dd/MM/yyyy HH:mm');
  List<Company> companies = <Company>[];
  String? companyId;
  bool loading = true;
  bool searchBusy = false;
  Map<String, int> summary = <String, int>{};
  List<Map<String, Object?>> timeline = <Map<String, Object?>>[];
  List<Map<String, Object?>> recurrences = <Map<String, Object?>>[];
  List<Map<String, Object?>> evidence = <Map<String, Object?>>[];
  List<Map<String, String>> searchHits = <Map<String, String>>[];
  List<SstRecord> auditarActions = <SstRecord>[];
  Set<String> favorites = <String>{'ronda','nc','trainings','history'};

  Company? get selectedCompany {
    final id=companyId;
    if(id==null)return null;
    for(final item in companies){if(item.id==id)return item;}
    return null;
  }

  @override
  void initState(){super.initState();companyId=widget.initialCompanyId;_load();}
  @override
  void dispose(){_search.dispose();super.dispose();}

  Future<void> _load() async {
    if(mounted)setState(()=>loading=true);
    final app=AppDatabase.instance;
    final companyRows=await app.getCompanies();
    if(companyId!=null&&!companyRows.any((c)=>c.id==companyId))companyId=null;
    final saved=(await app.getSetting('smart_sst_center_favorites')).trim();
    if(saved.isNotEmpty){
      favorites=saved.split(',').map((e)=>e.trim()).where((e)=>e.isNotEmpty).toSet();
    }
    final result=await Future.wait<Object>([
      _summary(),_timeline(),_recurrences(),_evidence(),
      app.getSstRecords(type:'ACAO_AUDITAR',companyId:companyId),
    ]);
    if(!mounted)return;
    setState((){
      companies=companyRows;
      summary=result[0] as Map<String,int>;
      timeline=result[1] as List<Map<String,Object?>>;
      recurrences=result[2] as List<Map<String,Object?>>;
      evidence=result[3] as List<Map<String,Object?>>;
      auditarActions=result[4] as List<SstRecord>;
      loading=false;
    });
  }

  List<Object?> get _args=>companyId==null?<Object?>[]:<Object?>[companyId];
  String _companySql(String alias)=>companyId==null?'':' AND '+alias+'.id = ?';
  int _count(List<Map<String,Object?>> rows)=>rows.isEmpty?0:((rows.first['n'] as num?)?.toInt()??0);

  Future<Map<String,int>> _summary() async {
    final db=await AppDatabase.instance.database;
    final workers=await db.rawQuery(
      'SELECT COUNT(*) n FROM workers w JOIN companies c ON c.id=w.company_id WHERE w.active=1'+_companySql('c'),_args);
    final ncs=await db.rawQuery(
      "SELECT COUNT(*) n FROM non_conformities n JOIN inspections i ON i.id=n.inspection_id "
      "JOIN companies c ON c.id=i.company_id WHERE LOWER(COALESCE(n.status,'')) NOT LIKE '%concl%'"+_companySql('c'),_args);
    final overdue=await db.rawQuery(
      "SELECT COUNT(*) n FROM action_plans a JOIN inspections i ON i.id=a.inspection_id "
      "JOIN companies c ON c.id=i.company_id WHERE LOWER(COALESCE(a.status,'')) NOT LIKE '%concl%' "
      "AND COALESCE(a.due_date,'')<>'' AND a.due_date < ?"+_companySql('c'),
      <Object?>[DateTime.now().toIso8601String(),..._args]);
    final training=await db.rawQuery(
      "SELECT COUNT(*) n FROM training_controls t JOIN workers w ON w.id=t.worker_id "
      "JOIN companies c ON c.id=w.company_id WHERE w.active=1 AND COALESCE(t.expiry_date,'')<>'' "
      "AND t.expiry_date <= ?"+_companySql('c'),
      <Object?>[DateTime.now().add(const Duration(days:30)).toIso8601String(),..._args]);
    final month=DateTime(DateTime.now().year,DateTime.now().month,1).toIso8601String();
    final actions=await db.rawQuery(
      "SELECT COUNT(*) n FROM sst_records r JOIN companies c ON c.id=r.company_id "
      "WHERE r.type='ACAO_AUDITAR' AND r.date>=?"+_companySql('c'),
      <Object?>[month,..._args]);
    final media=await db.rawQuery(
      "SELECT COUNT(*) n FROM media_assets m JOIN companies c ON c.id=m.company_id "
      "WHERE COALESCE(m.local_path,'')<>''"+_companySql('c'),_args);
    return <String,int>{
      'workers':_count(workers),'openNcs':_count(ncs),'overdue':_count(overdue),
      'training':_count(training),'auditar':_count(actions),'evidence':_count(media),
    };
  }

  Future<List<Map<String,Object?>>> _timeline() async {
    final db=await AppDatabase.instance.database;
    final rows=<Map<String,Object?>>[];
    final inspectionWhere=companyId==null?'':' WHERE c.id = ?';
    final recordWhere=companyId==null?'':' WHERE c.id = ?';
    final inspections=await db.rawQuery(
      'SELECT i.date,c.name company_name,i.checklist_type title FROM inspections i '
      'JOIN companies c ON c.id=i.company_id'+inspectionWhere+' ORDER BY i.date DESC LIMIT 50',_args);
    for(final r in inspections){
      rows.add(<String,Object?>{'date':r['date'],'company':r['company_name'],'kind':'Vistoria','title':r['title'],'status':''});
    }
    final records=await db.rawQuery(
      'SELECT r.date,c.name company_name,r.type,r.title,r.status FROM sst_records r '
      'LEFT JOIN companies c ON c.id=r.company_id'+recordWhere+' ORDER BY r.date DESC LIMIT 100',_args);
    for(final r in records){
      rows.add(<String,Object?>{
        'date':r['date'],'company':r['company_name'],'kind':_typeLabel('\${r['type']??''}'),
        'title':r['title'],'status':r['status'],
      });
    }
    rows.sort((a,b){
      final da=DateTime.tryParse('\${a['date']??''}')??DateTime(1970);
      final dbb=DateTime.tryParse('\${b['date']??''}')??DateTime(1970);
      return dbb.compareTo(da);
    });
    return rows.take(120).toList();
  }

  Future<List<Map<String,Object?>>> _recurrences() async {
    final db=await AppDatabase.instance.database;
    return db.rawQuery(
      "SELECT c.name company_name,COALESCE(s.name,'Sem setor') sector_name,"
      "MIN(n.description) description,COUNT(*) occurrences,MAX(n.created_at) last_date "
      "FROM non_conformities n JOIN inspections i ON i.id=n.inspection_id "
      "JOIN companies c ON c.id=i.company_id LEFT JOIN sectors s ON s.id=i.sector_id "
      "WHERE TRIM(COALESCE(n.description,''))<>''"+_companySql('c')+
      " GROUP BY c.id,COALESCE(s.id,''),LOWER(TRIM(n.description)) "
      "HAVING COUNT(*)>1 ORDER BY occurrences DESC,last_date DESC LIMIT 50",_args);
  }

  Future<List<Map<String,Object?>>> _evidence() async {
    final db=await AppDatabase.instance.database;
    final where=companyId==null?'':' WHERE c.id = ?';
    return db.rawQuery(
      'SELECT m.entity_type,m.local_path,m.drive_file_id,m.file_name,m.updated_at,c.name company_name '
      'FROM media_assets m JOIN companies c ON c.id=m.company_id'+where+
      ' ORDER BY m.updated_at DESC LIMIT 180',_args);
  }

  Future<void> _runSearch() async {
    final q=_search.text.trim().toLowerCase();
    if(q.isEmpty){if(mounted)setState(()=>searchHits=<Map<String,String>>[]);return;}
    setState(()=>searchBusy=true);
    final db=await AppDatabase.instance.database;
    final like='%'+q+'%';
    final hits=<Map<String,String>>[];
    final cfilter=companyId==null?'':' AND c.id = ?';

    final companiesRows=await db.rawQuery(
      "SELECT c.id,c.name,c.cnpj,c.city,c.uf FROM companies c WHERE c.active=1 AND "
      "(LOWER(c.name) LIKE ? OR LOWER(COALESCE(c.cnpj,'')) LIKE ? OR LOWER(COALESCE(c.city,'')) LIKE ?)"+
      (companyId==null?'':' AND c.id = ?')+" LIMIT 15",
      companyId==null?<Object?>[like,like,like]:<Object?>[like,like,like,companyId]);
    for(final r in companiesRows){
      hits.add({'kind':'Empresa','title':'\${r['name']??''}','subtitle':'\${r['cnpj']??''} • \${r['city']??''}/\${r['uf']??''}','companyId':'\${r['id']??''}','target':''});
    }

    final workers=await db.rawQuery(
      "SELECT w.name,w.role,c.id company_id,c.name company_name FROM workers w JOIN companies c ON c.id=w.company_id "
      "WHERE w.active=1 AND (LOWER(w.name) LIKE ? OR LOWER(COALESCE(w.role,'')) LIKE ? OR LOWER(COALESCE(w.cpf,'')) LIKE ?)"+
      cfilter+" LIMIT 20",
      companyId==null?<Object?>[like,like,like]:<Object?>[like,like,like,companyId]);
    for(final r in workers){
      hits.add({'kind':'Trabalhador','title':'\${r['name']??''}','subtitle':'\${r['role']??''} • \${r['company_name']??''}','companyId':'\${r['company_id']??''}','target':'workers'});
    }

    final ncs=await db.rawQuery(
      "SELECT n.code,n.description,n.status,c.id company_id,c.name company_name FROM non_conformities n "
      "JOIN inspections i ON i.id=n.inspection_id JOIN companies c ON c.id=i.company_id WHERE "
      "(LOWER(COALESCE(n.code,'')) LIKE ? OR LOWER(n.description) LIKE ? OR LOWER(COALESCE(n.recommendation,'')) LIKE ?)"+
      cfilter+" LIMIT 20",
      companyId==null?<Object?>[like,like,like]:<Object?>[like,like,like,companyId]);
    for(final r in ncs){
      hits.add({'kind':'Não conformidade','title':'\${r['code']??''} • \${r['description']??''}','subtitle':'\${r['status']??''} • \${r['company_name']??''}','companyId':'\${r['company_id']??''}','target':'nc'});
    }

    final trainings=await db.rawQuery(
      "SELECT t.code,t.title,w.name worker_name,c.id company_id,c.name company_name FROM training_controls t "
      "JOIN workers w ON w.id=t.worker_id JOIN companies c ON c.id=w.company_id WHERE "
      "(LOWER(COALESCE(t.code,'')) LIKE ? OR LOWER(t.title) LIKE ? OR LOWER(w.name) LIKE ?)"+
      cfilter+" LIMIT 20",
      companyId==null?<Object?>[like,like,like]:<Object?>[like,like,like,companyId]);
    for(final r in trainings){
      hits.add({'kind':'Treinamento','title':'\${r['code']??''} • \${r['title']??''}','subtitle':'\${r['worker_name']??''} • \${r['company_name']??''}','companyId':'\${r['company_id']??''}','target':'trainings'});
    }

    final inspections=await db.rawQuery(
      "SELECT i.checklist_type,i.area,i.report_number,c.id company_id,c.name company_name FROM inspections i "
      "JOIN companies c ON c.id=i.company_id WHERE (LOWER(COALESCE(i.checklist_type,'')) LIKE ? "
      "OR LOWER(COALESCE(i.area,'')) LIKE ? OR LOWER(COALESCE(i.report_number,'')) LIKE ?)"+
      cfilter+" LIMIT 20",
      companyId==null?<Object?>[like,like,like]:<Object?>[like,like,like,companyId]);
    for(final r in inspections){
      hits.add({'kind':'Vistoria','title':'\${r['checklist_type']??''} • \${r['area']??''}','subtitle':'\${r['company_name']??''}','companyId':'\${r['company_id']??''}','target':'history'});
    }

    final records=await db.rawQuery(
      "SELECT r.type,r.title,r.status,c.id company_id,c.name company_name FROM sst_records r "
      "LEFT JOIN companies c ON c.id=r.company_id WHERE (LOWER(r.title) LIKE ? OR LOWER(COALESCE(r.payload,'')) LIKE ?)"+
      (companyId==null?'':' AND c.id = ?')+" LIMIT 30",
      companyId==null?<Object?>[like,like]:<Object?>[like,like,companyId]);
    for(final r in records){
      hits.add({'kind':_typeLabel('\${r['type']??''}'),'title':'\${r['title']??''}','subtitle':'\${r['status']??''} • \${r['company_name']??''}','companyId':'\${r['company_id']??''}','target':'routine'});
    }
    if(!mounted)return;
    setState((){searchHits=hits.take(100).toList();searchBusy=false;});
  }

  Future<void> _toggleFavorite(String key) async {
    final next=Set<String>.from(favorites);
    next.contains(key)?next.remove(key):next.add(key);
    await AppDatabase.instance.setSetting('smart_sst_center_favorites',next.join(','));
    if(mounted)setState(()=>favorites=next);
  }

  void _notice(String message)=>ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(message)));

  Future<void> _open(String key,{String? targetCompanyId}) async {
    final id=targetCompanyId??companyId;
    Company? company;
    if(id!=null){for(final c in companies){if(c.id==id){company=c;break;}}}
    Widget page;
    switch(key){
      case 'ronda':
        if(company==null){_notice('Escolha uma empresa para abrir a Ronda Expressa.');return;}
        page=ExpressRoundScreen(company:company);break;
      case 'nc':page=NonConformitiesScreen(companyId:id);break;
      case 'actions':page=ActionPlanScreen(companyId:id);break;
      case 'workers':page=WorkersScreen(companyId:id);break;
      case 'trainings':page=TrainingsScreen(companyId:id);break;
      case 'history':page=HistoryScreen(companyId:id);break;
      case 'routine':page=RoutineHubScreen(companyId:id);break;
      case 'evidence':
        if(company==null){_notice('Escolha uma empresa para conferir as evidências.');return;}
        page=EvidenceBackupScreen(company:company);break;
      default:return;
    }
    await Navigator.of(context).push(MaterialPageRoute<void>(builder:(_)=>page));
    await _load();
  }

  Future<void> _addAuditarAction() async {
    final company=selectedCompany;
    if(company==null){_notice('Escolha uma empresa antes de registrar a atuação da Auditar.');return;}
    final title=TextEditingController();
    final description=TextEditingController();
    String kind='Visita técnica';
    final saved=await showDialog<bool>(
      context:context,
      builder:(dialogContext)=>StatefulBuilder(
        builder:(context,setDialogState)=>AlertDialog(
          title:const Text('Registrar ação da Auditar'),
          content:SizedBox(width:520,child:SingleChildScrollView(child:Column(
            mainAxisSize:MainAxisSize.min,
            children:[
              DropdownButtonFormField<String>(
                initialValue:kind,decoration:const InputDecoration(labelText:'Tipo de atuação'),
                items:const ['Visita técnica','Inspeção','Orientação','DDS','Treinamento','Reunião','Validação de correção','Acompanhamento','Outro']
                    .map((e)=>DropdownMenuItem<String>(value:e,child:Text(e))).toList(),
                onChanged:(value)=>setDialogState(()=>kind=value??kind),
              ),
              const SizedBox(height:10),
              TextField(controller:title,decoration:const InputDecoration(labelText:'Título')),
              const SizedBox(height:10),
              TextField(controller:description,minLines:3,maxLines:6,decoration:const InputDecoration(labelText:'O que foi realizado')),
              const SizedBox(height:10),
              const Text('Usa o cadastro SST já existente; nenhuma estrutura de sincronização é criada.',style:TextStyle(fontSize:11,color:Colors.blueGrey)),
            ],
          ))),
          actions:[
            TextButton(onPressed:()=>Navigator.pop(dialogContext,false),child:const Text('Cancelar')),
            FilledButton(onPressed:(){if(title.text.trim().isNotEmpty)Navigator.pop(dialogContext,true);},child:const Text('Salvar ação')),
          ],
        ),
      ),
    );
    if(saved!=true)return;
    final record=SstRecord(
      id:const Uuid().v4(),companyId:company.id,type:'ACAO_AUDITAR',
      title:title.text.trim(),date:DateTime.now(),status:'Concluído',priority:'Baixa',
      payload:<String,dynamic>{
        'actionType':kind,'description':description.text.trim(),
        'performedBy':AuthService.currentUser?.name??'','source':'CENTRAL_INTELIGENTE',
      },
    );
    await AppDatabase.instance.upsertSstRecord(record);
    if(!mounted)return;
    _notice('Ação da Auditar registrada.');
    await _load();
  }

  Future<void> _diagnostics() async {
    if(!AuthService.isAdmin){_notice('Diagnóstico disponível apenas para a conta ADM.');return;}
    final app=AppDatabase.instance;
    final db=await app.database;
    final lastSync=await app.getSetting('last_device_sync_success');
    final syncError=await app.getSetting('last_device_sync_error');
    final mediaSuccess=await app.getSetting('media_sync_last_success');
    final mediaError=await app.getSetting('media_sync_last_error');
    final pendingMedia=await MediaSyncService.pendingCount();
    var dirty=0;
    try{
      final rows=await db.rawQuery('SELECT COUNT(*) n FROM device_sync_changes WHERE dirty=1');
      dirty=((rows.first['n'] as num?)?.toInt()??0);
    }catch(_){}
    if(!mounted)return;
    await showDialog<void>(
      context:context,
      builder:(context)=>AlertDialog(
        title:const Text('Diagnóstico técnico • ADM'),
        content:SizedBox(width:560,child:Column(
          mainAxisSize:MainAxisSize.min,
          children:[
            _diag('Versão-alvo',Platform.isWindows?'3.30.62':'3.29.143'),
            _diag('Última sincronização de dados',_settingDate(lastSync)),
            _diag('Alterações locais pendentes','\$dirty'),
            _diag('Mídias pendentes','\$pendingMedia'),
            _diag('Último envio de mídia',_settingDate(mediaSuccess)),
            if(syncError.trim().isNotEmpty)_diag('Erro de dados',syncError),
            if(mediaError.trim().isNotEmpty)_diag('Erro de mídia',mediaError),
            const SizedBox(height:8),
            const Text('Tela somente de leitura. Não força sincronização nem altera registros.',style:TextStyle(fontSize:11,color:Colors.blueGrey)),
          ],
        )),
        actions:[FilledButton(onPressed:()=>Navigator.pop(context),child:const Text('Fechar'))],
      ),
    );
  }

  String _settingDate(String value){
    final d=DateTime.tryParse(value.trim());
    if(d==null)return value.trim().isEmpty?'Não informado':value;
    return _dateTime.format(d.toLocal());
  }

  static String _typeLabel(String type){
    switch(type){
      case 'DDS':return 'DDS';
      case 'TREINAMENTO_SESSAO':return 'Treinamento';
      case 'OBSERVACAO_SEGURANCA':return 'Observação de segurança';
      case 'INCIDENTE':return 'Ocorrência';
      case 'AGENDA':return 'Agenda SST';
      case 'APR_PT':return 'APR / PT';
      case 'EQUIPAMENTO':return 'Equipamento';
      case 'ACAO_AUDITAR':return 'Ação da Auditar';
      default:return type.trim().isEmpty?'Registro SST':type;
    }
  }

  @override
  Widget build(BuildContext context){
    return DefaultTabController(
      length:5,
      child:Scaffold(
        appBar:AppBar(
          title:const Text('Central Inteligente SST'),
          actions:[if(AuthService.isAdmin)IconButton(tooltip:'Diagnóstico técnico',onPressed:_diagnostics,icon:const Icon(Icons.monitor_heart_outlined))],
          bottom:const TabBar(isScrollable:true,tabs:[
            Tab(text:'Hoje'),Tab(text:'Buscar'),Tab(text:'Linha do tempo'),Tab(text:'Recorrências'),Tab(text:'Evidências'),
          ]),
        ),
        floatingActionButton:FloatingActionButton.extended(onPressed:_addAuditarAction,icon:const Icon(Icons.add_task_rounded),label:const Text('Ação Auditar')),
        body:loading?const Center(child:CircularProgressIndicator()):Column(
          children:[
            _companySelector(),
            Expanded(child:TabBarView(children:[_overview(),_searchView(),_timelineView(),_recurrenceView(),_evidenceView()])),
          ],
        ),
      ),
    );
  }

  Widget _companySelector()=>Padding(
    padding:const EdgeInsets.fromLTRB(12,10,12,8),
    child:Row(children:[
      Expanded(child:DropdownButtonFormField<String?>(
        initialValue:companyId,isExpanded:true,
        decoration:const InputDecoration(labelText:'Empresa',isDense:true,prefixIcon:Icon(Icons.business_outlined)),
        items:[
          const DropdownMenuItem<String?>(value:null,child:Text('Todas as empresas autorizadas')),
          ...companies.map((c)=>DropdownMenuItem<String?>(value:c.id,child:Text(c.name,overflow:TextOverflow.ellipsis))),
        ],
        onChanged:(value)async{setState(()=>companyId=value);await _load();if(_search.text.trim().isNotEmpty)await _runSearch();},
      )),
      const SizedBox(width:8),
      IconButton(tooltip:'Atualizar',onPressed:_load,icon:const Icon(Icons.refresh_rounded)),
    ]),
  );

  Widget _overview(){
    final cards=<List<Object>>[
      ['Trabalhadores',summary['workers']??0,Icons.groups_2_outlined,AuditarBrand.navy,'workers'],
      ['NCs abertas',summary['openNcs']??0,Icons.warning_amber_rounded,AuditarBrand.danger,'nc'],
      ['Ações vencidas',summary['overdue']??0,Icons.event_busy_outlined,const Color(0xFFD93025),'actions'],
      ['Treinamentos a verificar',summary['training']??0,Icons.school_outlined,const Color(0xFFF29D18),'trainings'],
      ['Ações Auditar no mês',summary['auditar']??0,Icons.verified_outlined,AuditarBrand.greenDark,''],
      ['Evidências catalogadas',summary['evidence']??0,Icons.photo_library_outlined,const Color(0xFF6A4BBC),'evidence'],
    ];
    return RefreshIndicator(
      onRefresh:_load,
      child:ListView(
        padding:const EdgeInsets.fromLTRB(12,12,12,96),
        children:[
          const Text('O que precisa da sua atenção',style:TextStyle(fontSize:18,fontWeight:FontWeight.w900,color:AuditarBrand.navy)),
          const SizedBox(height:10),
          Wrap(spacing:10,runSpacing:10,children:cards.map((item){
            final color=item[3] as Color;
            final target=item[4] as String;
            return SizedBox(width:205,child:Card(margin:EdgeInsets.zero,child:InkWell(
              onTap:target.isEmpty?null:()=>_open(target),
              child:Padding(padding:const EdgeInsets.all(13),child:Row(children:[
                CircleAvatar(backgroundColor:color.withValues(alpha:.10),foregroundColor:color,child:Icon(item[2] as IconData)),
                const SizedBox(width:10),
                Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
                  Text('\${item[1]}',style:TextStyle(fontSize:22,fontWeight:FontWeight.w900,color:color)),
                  Text(item[0] as String,style:const TextStyle(fontSize:11,fontWeight:FontWeight.w700)),
                ])),
              ])),
            )));
          }).toList()),
          const SizedBox(height:20),
          _heading('Atalhos favoritos','Toque na estrela para fixar ou remover.'),
          const SizedBox(height:8),
          Wrap(spacing:8,runSpacing:8,children:[
            _shortcut('ronda','Ronda',Icons.camera_alt_outlined),
            _shortcut('nc','Não conformidades',Icons.warning_amber_rounded),
            _shortcut('actions','Planos de ação',Icons.task_alt_outlined),
            _shortcut('trainings','Treinamentos',Icons.school_outlined),
            _shortcut('history','Histórico',Icons.history_rounded),
            _shortcut('routine','Rotina SST',Icons.dashboard_outlined),
            _shortcut('evidence','Evidências',Icons.photo_library_outlined),
          ]),
          const SizedBox(height:20),
          _heading('Atuação recente da Auditar','Registros do serviço executado para a empresa.'),
          const SizedBox(height:8),
          if(auditarActions.isEmpty)
            const Card(child:Padding(padding:EdgeInsets.all(18),child:Text('Nenhuma ação da Auditar registrada neste filtro.')))
          else
            ...auditarActions.take(8).map((r)=>Card(child:ListTile(
              leading:const CircleAvatar(child:Icon(Icons.verified_outlined)),
              title:Text(r.title),
              subtitle:Text([
                '\${r.payload['actionType']??''}',_dateTime.format(r.date),
                '\${r.payload['performedBy']??''}','\${r.payload['description']??''}',
              ].where((e)=>e.trim().isNotEmpty).join(' • '),maxLines:3,overflow:TextOverflow.ellipsis),
            ))),
        ],
      ),
    );
  }

  Widget _shortcut(String key,String label,IconData icon){
    final pinned=favorites.contains(key);
    return Material(
      color:pinned?AuditarBrand.greenDark.withValues(alpha:.09):Theme.of(context).colorScheme.surfaceContainerHighest,
      borderRadius:BorderRadius.circular(12),
      child:InkWell(
        borderRadius:BorderRadius.circular(12),onTap:()=>_open(key),
        child:Padding(padding:const EdgeInsets.fromLTRB(11,8,6,8),child:Row(mainAxisSize:MainAxisSize.min,children:[
          Icon(icon,size:18,color:AuditarBrand.navy),const SizedBox(width:6),
          Text(label,style:const TextStyle(fontWeight:FontWeight.w700)),
          IconButton(
            visualDensity:VisualDensity.compact,
            tooltip:pinned?'Remover dos favoritos':'Fixar nos favoritos',
            onPressed:()=>_toggleFavorite(key),
            icon:Icon(pinned?Icons.star_rounded:Icons.star_border_rounded,size:18,color:pinned?const Color(0xFFF29D18):Colors.blueGrey),
          ),
        ])),
      ),
    );
  }

  Widget _searchView()=>ListView(
    padding:const EdgeInsets.fromLTRB(12,12,12,90),
    children:[
      TextField(
        controller:_search,textInputAction:TextInputAction.search,onSubmitted:(_)=>_runSearch(),
        decoration:InputDecoration(
          labelText:'Buscar em todo o app',
          hintText:'Trabalhador, NR, setor, relatório, DDS, treinamento...',
          prefixIcon:const Icon(Icons.search_rounded),
          suffixIcon:searchBusy
              ?const Padding(padding:EdgeInsets.all(12),child:SizedBox(width:18,height:18,child:CircularProgressIndicator(strokeWidth:2)))
              :IconButton(onPressed:_runSearch,icon:const Icon(Icons.arrow_forward_rounded)),
        ),
      ),
      const SizedBox(height:12),
      if(_search.text.trim().isNotEmpty&&searchHits.isEmpty&&!searchBusy)
        const Card(child:Padding(padding:EdgeInsets.all(18),child:Text('Nenhum registro localizado.'))),
      ...searchHits.map((hit)=>Card(child:ListTile(
        leading:CircleAvatar(child:Text((hit['kind']??'?').substring(0,1))),
        title:Text(hit['title']??''),
        subtitle:Text((hit['kind']??'')+' • '+(hit['subtitle']??'')),
        trailing:const Icon(Icons.chevron_right_rounded),
        onTap:()async{
          final kind=hit['kind']??'';
          final cid=hit['companyId']??'';
          if(kind=='Empresa'&&cid.isNotEmpty){setState(()=>companyId=cid);await _load();return;}
          final target=hit['target']??'';
          if(target.isNotEmpty)await _open(target,targetCompanyId:cid.isEmpty?null:cid);
        },
      ))),
    ],
  );

  Widget _timelineView(){
    if(timeline.isEmpty)return const Center(child:Text('Nenhum evento encontrado para este filtro.'));
    return ListView.builder(
      padding:const EdgeInsets.fromLTRB(12,12,12,90),itemCount:timeline.length,
      itemBuilder:(context,index){
        final item=timeline[index];
        final date=DateTime.tryParse('\${item['date']??''}');
        return Card(child:ListTile(
          leading:const CircleAvatar(child:Icon(Icons.history_rounded)),
          title:Text('\${item['title']??'Registro'}'),
          subtitle:Text([
            '\${item['kind']??''}','\${item['company']??''}',
            if(date!=null)_dateTime.format(date.toLocal()),'\${item['status']??''}',
          ].where((e)=>e.trim().isNotEmpty).join(' • ')),
        ));
      },
    );
  }

  Widget _recurrenceView(){
    if(recurrences.isEmpty)return const Center(child:Text('Nenhuma recorrência objetiva foi identificada.'));
    return ListView.builder(
      padding:const EdgeInsets.fromLTRB(12,12,12,90),itemCount:recurrences.length,
      itemBuilder:(context,index){
        final item=recurrences[index];
        return Card(child:ListTile(
          leading:CircleAvatar(
            backgroundColor:const Color(0xFFF29D18).withValues(alpha:.12),
            foregroundColor:const Color(0xFF9A6300),
            child:Text('\${item['occurrences']??0}×',style:const TextStyle(fontSize:11,fontWeight:FontWeight.w900)),
          ),
          title:Text('\${item['description']??''}'),
          subtitle:Text('\${item['company_name']??''} • \${item['sector_name']??''}'),
          trailing:const Icon(Icons.warning_amber_rounded),onTap:()=>_open('nc'),
        ));
      },
    );
  }

  Widget _evidenceView()=>Column(children:[
    if(selectedCompany!=null)Padding(
      padding:const EdgeInsets.fromLTRB(12,10,12,0),
      child:SizedBox(width:double.infinity,child:OutlinedButton.icon(
        onPressed:()=>_open('evidence'),icon:const Icon(Icons.cloud_done_outlined),
        label:const Text('Conferir backup e recuperação de evidências'),
      )),
    ),
    Expanded(child:evidence.isEmpty
        ?const Center(child:Text('Nenhuma evidência catalogada neste filtro.'))
        :GridView.builder(
          padding:const EdgeInsets.fromLTRB(12,12,12,90),
          gridDelegate:const SliverGridDelegateWithMaxCrossAxisExtent(maxCrossAxisExtent:260,childAspectRatio:1.05,crossAxisSpacing:10,mainAxisSpacing:10),
          itemCount:evidence.length,itemBuilder:(context,index)=>_evidenceCard(evidence[index]),
        )),
  ]);

  Widget _evidenceCard(Map<String,Object?> item){
    final path='\${item['local_path']??''}'.trim();
    final local=path.isNotEmpty&&File(path).existsSync();
    final cloud='\${item['drive_file_id']??''}'.trim().isNotEmpty;
    return Card(
      clipBehavior:Clip.antiAlias,
      child:InkWell(
        onTap:local&&_isImage(path)?()=>_showImage(path,'\${item['file_name']??''}'):null,
        child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
          Expanded(child:local&&_isImage(path)
              ?Image.file(File(path),width:double.infinity,fit:BoxFit.cover,errorBuilder:(_,__,___)=>const Center(child:Icon(Icons.broken_image_outlined)))
              :Center(child:Icon(local?Icons.insert_drive_file_outlined:cloud?Icons.cloud_done_outlined:Icons.hide_image_outlined,size:42,color:Colors.blueGrey))),
          Padding(padding:const EdgeInsets.fromLTRB(10,8,10,9),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
            Text(_mediaLabel('\${item['entity_type']??''}'),style:const TextStyle(fontWeight:FontWeight.w800,fontSize:11)),
            Text('\${item['company_name']??''}',maxLines:1,overflow:TextOverflow.ellipsis,style:const TextStyle(fontSize:10.5)),
            Text(cloud?'Backup confirmado':local?'Arquivo local':'Mídia indisponível neste aparelho',
              style:TextStyle(fontSize:10,color:cloud?AuditarBrand.greenDark:local?AuditarBrand.navy:AuditarBrand.danger,fontWeight:FontWeight.w700)),
          ])),
        ]),
      ),
    );
  }

  bool _isImage(String path){
    final lower=path.toLowerCase();
    return lower.endsWith('.jpg')||lower.endsWith('.jpeg')||lower.endsWith('.png')||lower.endsWith('.webp');
  }

  void _showImage(String path,String fileName){
    showDialog<void>(context:context,builder:(context)=>Dialog(child:Column(mainAxisSize:MainAxisSize.min,children:[
      Flexible(child:InteractiveViewer(child:Image.file(File(path)))),
      Padding(padding:const EdgeInsets.all(10),child:Text(fileName.trim().isEmpty?'Evidência fotográfica':fileName)),
    ])));
  }

  String _mediaLabel(String type){
    switch(type){
      case 'evidence_photo':return 'Vistoria';
      case 'completion_photo':return 'Correção / depois';
      case 'round_photo':return 'Ronda';
      case 'training_record_photo':return 'Treinamento / DDS';
      case 'training_record_signature':return 'Assinatura de treinamento';
      case 'dds_signature':return 'Assinatura de DDS';
      case 'extinguisher_photo':return 'Extintor';
      case 'company_logo':return 'Logo da empresa';
      default:return type.replaceAll('_',' ');
    }
  }

  Widget _heading(String title,String subtitle)=>Column(
    crossAxisAlignment:CrossAxisAlignment.start,
    children:[
      Text(title,style:const TextStyle(fontSize:17,fontWeight:FontWeight.w900,color:AuditarBrand.navy)),
      Text(subtitle,style:const TextStyle(fontSize:11,color:Colors.blueGrey)),
    ],
  );

  Widget _diag(String label,String value)=>Padding(
    padding:const EdgeInsets.symmetric(vertical:6),
    child:Row(crossAxisAlignment:CrossAxisAlignment.start,children:[
      Expanded(flex:2,child:Text(label,style:const TextStyle(fontWeight:FontWeight.w700))),
      const SizedBox(width:12),Expanded(flex:3,child:Text(value)),
    ]),
  );
}

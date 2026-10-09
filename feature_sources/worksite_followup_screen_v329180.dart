import 'dart:convert';
import 'package:flutter/material.dart';
import '../database.dart';
import '../models.dart';
import '../services/auth_service.dart';
import '../services/worksite_followup_cloud_service.dart';
import 'express_round_screen.dart';
import 'new_inspection_screen.dart';
import 'field_operational_control_screen.dart';
import 'history_screen.dart';
import 'manager_reports_screen.dart';

/// Metadados isolados por obra/usuário; fotos e registros SST existentes intactos.
class WorksiteFollowup {
  static const phases=['Planejamento','Fundação','Estrutura','Alvenaria',
    'Instalações','Acabamento','Entrega','Outros'];
  static const statuses=['Não iniciada','Em andamento','Pausada','Concluída'];
  const WorksiteFollowup({this.phase='Planejamento',this.status='Não iniciada',
    this.progress=0,this.responsible='',this.nextVisit='',
    this.targetDate='',this.notes='',this.log=const []});
  final String phase,status,responsible,nextVisit,targetDate,notes;
  final int progress;
  final List<WorksiteLog> log;

  factory WorksiteFollowup.fromMap(Map<String,dynamic> value) {
    final p=(value['progress'] is num ? (value['progress'] as num).toInt() : 0);
    final phase=''+(value['phase']??'').toString();
    final status=''+(value['status']??'').toString();
    return WorksiteFollowup(
      phase:phases.contains(phase)?phase:phases.first,
      status:statuses.contains(status)?status:statuses.first,
      progress:p.clamp(0,100),
      responsible:''+(value['responsible']??'').toString(),
      nextVisit:''+(value['nextVisit']??'').toString(),
      targetDate:''+(value['targetDate']??'').toString(),
      notes:''+(value['notes']??'').toString(),
      log:[for(final v in (value['log'] is List ? value['log'] as List : const []))
        if(v is Map) WorksiteLog.fromMap(Map<String,dynamic>.from(v))].take(80).toList()
    );
  }
  Map<String,dynamic> toMap()=>{
    'schemaVersion':1,'phase':phase,'status':status,'progress':progress,
    'responsible':responsible,'nextVisit':nextVisit,'targetDate':targetDate,
    'notes':notes,'log':log.take(80).map((v)=>v.toMap()).toList()
  };
  WorksiteFollowup copyWith({String? phase,String? status,int? progress,
    String? responsible,String? nextVisit,String? targetDate,String? notes,
    List<WorksiteLog>? log})=>WorksiteFollowup(
      phase:phase??this.phase,status:status??this.status,
      progress:progress??this.progress,responsible:responsible??this.responsible,
      nextVisit:nextVisit??this.nextVisit,targetDate:targetDate??this.targetDate,
      notes:notes??this.notes,log:log??this.log);
  static bool validDate(String s) {
    if(s.trim().isEmpty) return true;
    final n=s.trim();
    if(!RegExp(r'^\d{4}-\d{2}-\d{2}$').hasMatch(n)) return false;
    final d=DateTime.tryParse(n);
    return d!=null && d.toIso8601String().startsWith(n);
  }
}
class WorksiteLog {
  const WorksiteLog(this.at,this.type,this.note);
  final String at,type,note;
  factory WorksiteLog.fromMap(Map<String,dynamic> raw)=>WorksiteLog(
    (raw['at']??'').toString(),(raw['type']??'').toString(),
    (raw['note']??'').toString());
  Map<String,dynamic> toMap()=>{'at':at,'type':type,'note':note};
}
class WorksiteFollowupStore {
  WorksiteFollowupStore._();
  static String key(String company,String user)=>
    'worksite_followup_v1_'+Uri.encodeComponent(user)+'_'+Uri.encodeComponent(company);
  static String _key(String company)=>key(company,AppDatabase.activeUserId.toString());
  static Future<WorksiteFollowup> load(String company) async {
    final text=await AppDatabase.instance.getSetting(_key(company));
    if(text.isEmpty) return const WorksiteFollowup();
    final decoded=jsonDecode(text);
    return decoded is Map ? WorksiteFollowup.fromMap(Map<String,dynamic>.from(decoded))
      : const WorksiteFollowup();
  }
  static Future<void> save(String company,WorksiteFollowup record)=>
    AppDatabase.instance.setSetting(_key(company),jsonEncode(record.toMap()));
  static String backupKey(String company)=>_key(company)+'_before_cloud';
}

class WorksiteQuickActions extends StatelessWidget {
  const WorksiteQuickActions({super.key,required this.onRound,
    required this.onInspection,required this.onPending,required this.onHistory});
  final VoidCallback onRound,onInspection,onPending,onHistory;
  @override
  Widget build(BuildContext context)=>Wrap(spacing:8,runSpacing:8,children:[
    FilledButton.icon(onPressed:onRound,icon:const Icon(Icons.add_a_photo_outlined),
      label:const Text('Nova ronda')),
    OutlinedButton.icon(onPressed:onInspection,icon:const Icon(Icons.fact_check_outlined),
      label:const Text('Nova vistoria')),
    OutlinedButton.icon(onPressed:onPending,icon:const Icon(Icons.task_alt),
      label:const Text('Pendências')),
    OutlinedButton.icon(onPressed:onHistory,icon:const Icon(Icons.history),
      label:const Text('Histórico')),
  ]);
}
class WorksiteFollowupScreen extends StatefulWidget {
  const WorksiteFollowupScreen({super.key,required this.company,this.groupName=''});
  final Company company;
  final String groupName;
  @override
  State<WorksiteFollowupScreen> createState()=>_WorksiteFollowupScreenState();
}
class _WorksiteFollowupScreenState extends State<WorksiteFollowupScreen> {
  WorksiteFollowup _record=const WorksiteFollowup();
  late final TextEditingController _responsible,_notes,_nextVisit,_targetDate;
  bool _loading=true,_saving=false,_cloudBusy=false;
  String _cloudMessage='Compartilhamento disponível após implantar o módulo na Central.';
  String? _error;

  @override
  void initState(){
    super.initState();
    _responsible=TextEditingController();
    _notes=TextEditingController();
    _nextVisit=TextEditingController();
    _targetDate=TextEditingController();
    _load();
  }
  @override
  void dispose(){
    _responsible.dispose();_notes.dispose();_nextVisit.dispose();_targetDate.dispose();
    super.dispose();
  }
  Future<void> _load() async {
    if(!AuthService.canAccessCompany(widget.company.id)){
      if(mounted)setState((){_error='Sem acesso à obra.';_loading=false;});
      return;
    }
    try{
      final record=await WorksiteFollowupStore.load(widget.company.id);
      if(!mounted)return;
      _responsible.text=record.responsible;
      _notes.text=record.notes;
      _nextVisit.text=record.nextVisit;
      _targetDate.text=record.targetDate;
      setState((){_record=record;_loading=false;});
    }catch(_){
      if(mounted)setState((){_error='Não foi possível abrir o acompanhamento.';_loading=false;});
    }
  }
  Future<void> _save([WorksiteFollowup? provided]) async {
    if(_saving||!AuthService.canAccessCompany(widget.company.id))return;
    final value=provided??_record.copyWith(
      responsible:_responsible.text.trim(),notes:_notes.text.trim(),
      nextVisit:_nextVisit.text.trim(),targetDate:_targetDate.text.trim());
    if(!WorksiteFollowup.validDate(value.nextVisit)||
       !WorksiteFollowup.validDate(value.targetDate)){
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content:Text('Datas precisam estar no formato AAAA-MM-DD.')));
      return;
    }
    setState(()=>_saving=true);
    try{
      await WorksiteFollowupStore.save(widget.company.id,value);
      if(mounted)setState(()=>_record=value);
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content:Text('Acompanhamento salvo localmente.')));
    }catch(_){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content:Text('Não foi possível salvar. Dados digitados preservados.')));
    }finally{if(mounted)setState(()=>_saving=false);}
  }
  Future<void> _addLog() async {
    final input=TextEditingController();
    var type='Visita';
    final result=await showDialog<WorksiteLog>(context:context,
      builder:(dialog)=>StatefulBuilder(builder:(ctx,redraw)=>AlertDialog(
        title:const Text('Evolução da obra'),
        content:SingleChildScrollView(child:Column(mainAxisSize:MainAxisSize.min,children:[
          DropdownButtonFormField<String>(initialValue:type,
            decoration:const InputDecoration(labelText:'Tipo de registro'),
            items:const ['Visita','Orientação','Avanço','Pendência','Outro']
              .map((v)=>DropdownMenuItem(value:v,child:Text(v))).toList(),
            onChanged:(v){if(v!=null)redraw(()=>type=v);}),
          const SizedBox(height:10),
          TextField(controller:input,maxLength:800,maxLines:4,
            decoration:const InputDecoration(labelText:'Resumo da atividade',
              border:OutlineInputBorder())),
        ])),
        actions:[
          TextButton(onPressed:()=>Navigator.pop(dialog),child:const Text('Cancelar')),
          FilledButton(onPressed:(){
            if(input.text.trim().isEmpty)return;
            Navigator.pop(dialog,WorksiteLog(DateTime.now().toUtc().toIso8601String(),
              type,input.text.trim()));
          },child:const Text('Registrar')),
        ])));
    WidgetsBinding.instance.addPostFrameCallback((_) => input.dispose());
    if(result==null||!mounted)return;
    await _save(_record.copyWith(log:[result,..._record.log].take(80).toList()));
  }

  WorksiteFollowup _currentForm() => _record.copyWith(
    responsible:_responsible.text.trim(),
    notes:_notes.text.trim(),
    nextVisit:_nextVisit.text.trim(),
    targetDate:_targetDate.text.trim());

  void _cloudNotice(String message) {
    if(!mounted)return;
    setState(()=>_cloudMessage=message);
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(message)));
  }

  /// User-initiated push, never an implicit overwrite of a newer remote copy.
  Future<void> _shareWorksite() async {
    if(_saving||_cloudBusy)return;
    final record=_currentForm();
    if(!WorksiteFollowup.validDate(record.nextVisit) ||
       !WorksiteFollowup.validDate(record.targetDate)) {
      _cloudNotice('Confira as datas antes de compartilhar a obra.');
      return;
    }
    setState(()=>_cloudBusy=true);
    try {
      await WorksiteFollowupStore.save(widget.company.id,record);
      if(mounted)setState(()=>_record=record);
      final remote=await WorksiteFollowupCloudService.publish(
        widget.company.id,record.toMap());
      if(remote.conflict) {
        _cloudNotice('Outra pessoa atualizou esta obra. Sua versão local foi preservada. Consulte a Central antes de enviar novamente.');
      } else {
        _cloudNotice('Acompanhamento compartilhado. Revisão '+remote.revision.toString()+'.');
      }
    } catch (_) {
      _cloudNotice('Não foi possível compartilhar. Acompanhamento salvo no aparelho; confira a Central e a conexão.');
    } finally {
      if(mounted)setState(()=>_cloudBusy=false);
    }
  }


  Future<void> _restoreLocalBackup() async {
    if(_saving||_cloudBusy)return;
    setState(()=>_cloudBusy=true);
    try {
      final raw=await AppDatabase.instance.getSetting(
        WorksiteFollowupStore.backupKey(widget.company.id));
      if(raw.isEmpty) {
        _cloudNotice('Ainda não existe uma cópia anterior para restaurar.');
        return;
      }
      final data=jsonDecode(raw);
      if(data is! Map)throw StateError('Cópia anterior inválida.');
      final backup=WorksiteFollowup.fromMap(Map<String,dynamic>.from(data));
      if(!mounted)return;
      final restore=await showDialog<bool>(context:context,builder:(dialog)=>
        AlertDialog(
          title:const Text('Restaurar acompanhamento local?'),
          content:const Text('A cópia anterior será restaurada somente nesta obra. '
            'O acompanhamento atual ficará salvo como cópia de segurança. '
            'Não haverá envio automático à Central.'),
          actions:[
            TextButton(onPressed:()=>Navigator.pop(dialog,false),
              child:const Text('Cancelar')),
            FilledButton(onPressed:()=>Navigator.pop(dialog,true),
              child:const Text('Restaurar cópia')),
          ]));
      if(restore!=true||!mounted)return;
      await AppDatabase.instance.setSetting(
        WorksiteFollowupStore.backupKey(widget.company.id)+'_before_restore',
        jsonEncode(_currentForm().toMap()));
      await WorksiteFollowupStore.save(widget.company.id,backup);
      if(!mounted)return;
      _responsible.text=backup.responsible;
      _notes.text=backup.notes;
      _nextVisit.text=backup.nextVisit;
      _targetDate.text=backup.targetDate;
      setState(()=>_record=backup);
      _cloudNotice('Cópia local restaurada. Nenhum dado foi enviado à Central.');
    } catch (_) {
      _cloudNotice('Não foi possível restaurar a cópia anterior. A versão atual foi mantida.');
    } finally {
      if(mounted)setState(()=>_cloudBusy=false);
    }
  }

  /// Remote import requires explicit confirmation and leaves a local backup.
  Future<void> _receiveWorksite() async {
    if(_saving||_cloudBusy)return;
    setState(()=>_cloudBusy=true);
    try {
      final remote=await WorksiteFollowupCloudService.read(widget.company.id);
      if(!mounted)return;
      if(remote.record==null) {
        _cloudNotice('Nenhum acompanhamento dessa obra encontrado na Central.');
        return;
      }
      final incoming=WorksiteFollowup.fromMap(remote.record!);
      final accepted=await showDialog<bool>(context:context,builder:(dialog)=>
        AlertDialog(
          title:const Text('Usar acompanhamento da Central?'),
          content:Text('Revisão '+remote.revision.toString()+
            ' • '+incoming.phase+' • '+incoming.status+
            '\nAvanço: '+incoming.progress.toString()+
            '%\n\nUma cópia do acompanhamento local será preservada antes de substituir. Fotos e vistorias não serão alteradas.'),
          actions:[
            TextButton(onPressed:()=>Navigator.pop(dialog,false),
              child:const Text('Manter local')),
            FilledButton(onPressed:()=>Navigator.pop(dialog,true),
              child:const Text('Usar versão da Central')),
          ]));
      if(accepted!=true||!mounted)return;
      // Preserve the unsent local form, including edits not yet saved.
      final previous=_currentForm();
      await AppDatabase.instance.setSetting(
        WorksiteFollowupStore.backupKey(widget.company.id),
        jsonEncode(previous.toMap()));
      await WorksiteFollowupStore.save(widget.company.id,incoming);
      await WorksiteFollowupCloudService.adoptRemoteVersion(
        widget.company.id,remote.revision);
      if(!mounted)return;
      _responsible.text=incoming.responsible;
      _notes.text=incoming.notes;
      _nextVisit.text=incoming.nextVisit;
      _targetDate.text=incoming.targetDate;
      setState(()=>_record=incoming);
      _cloudNotice('Versão da Central recebida. Cópia local anterior preservada.');
    } catch (_) {
      _cloudNotice('Não foi possível consultar a Central. Seus dados locais foram preservados.');
    } finally {
      if(mounted)setState(()=>_cloudBusy=false);
    }
  }

  void _open(Widget page){
    if(!AuthService.canAccessCompany(widget.company.id))return;
    Navigator.of(context).push(MaterialPageRoute(builder:(_)=>page));
  }
  Widget _date(String label,TextEditingController ctrl)=>TextField(
    controller:ctrl,keyboardType:TextInputType.datetime,
    decoration:InputDecoration(labelText:label,hintText:'AAAA-MM-DD',
      border:const OutlineInputBorder()));
  @override
  Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:const Text('Acompanhamento da obra')),
    body:_loading?const Center(child:CircularProgressIndicator()):
    _error!=null?Center(child:Text(_error!)):
    Align(alignment:Alignment.topCenter,
      child:ConstrainedBox(constraints:const BoxConstraints(maxWidth:760),
      child:ListView(padding:const EdgeInsets.all(16),children:[
        Text(widget.company.name,style:Theme.of(context).textTheme.titleLarge),
        if(widget.groupName.isNotEmpty)Text(widget.groupName),
        const SizedBox(height:10),
        Card(child:Padding(padding:const EdgeInsets.all(12),child:Column(
          crossAxisAlignment:CrossAxisAlignment.start,children:[
          Text('Etapa: '+_record.phase+' • '+_record.status),
          const SizedBox(height:6),
          Text('Avanço informado: '+_record.progress.toString()+'%'),
          LinearProgressIndicator(value:_record.progress/100),
          const SizedBox(height:4),
          const Text('Percentual preenchido pelo responsável, não inferido do número de visitas.')
        ]))),
        const SizedBox(height:12),
        WorksiteQuickActions(
          onRound:()=>_open(ExpressRoundScreen(company:widget.company)),
          onInspection:()=>_open(NewInspectionScreen(initialCompany:widget.company,fieldMode:true)),
          onPending:()=>_open(FieldOperationalControlScreen(initialCompanyId:widget.company.id)),
          onHistory:()=>_open(HistoryScreen(companyId:widget.company.id))),
        const SizedBox(height:8),
        OutlinedButton.icon(
          onPressed:()=>_open(ManagerReportsScreen(company:widget.company)),
          icon:const Icon(Icons.analytics_outlined),label:const Text('Indicadores e relatórios')),
        const SizedBox(height:16),
        DropdownButtonFormField<String>(
          key:ValueKey('phase-'+_record.phase),
          initialValue:_record.phase,
          decoration:const InputDecoration(labelText:'Etapa atual',border:OutlineInputBorder()),
          items:WorksiteFollowup.phases.map((v)=>DropdownMenuItem(
            value:v,child:Text(v))).toList(),
          onChanged:_saving?null:(v){if(v!=null)_save(_record.copyWith(phase:v));}),
        const SizedBox(height:10),
        DropdownButtonFormField<String>(
          key:ValueKey('status-'+_record.status),initialValue:_record.status,
          decoration:const InputDecoration(labelText:'Situação',border:OutlineInputBorder()),
          items:WorksiteFollowup.statuses.map((v)=>DropdownMenuItem(
            value:v,child:Text(v))).toList(),
          onChanged:_saving?null:(v){if(v!=null)_save(_record.copyWith(status:v));}),
        const SizedBox(height:12),
        Text('Avanço da obra: '+_record.progress.toString()+'%'),
        Slider(value:_record.progress.toDouble(),min:0,max:100,divisions:20,
          label:_record.progress.toString()+'%',
          onChanged:_saving?null:(v)=>setState(()=>
            _record=_record.copyWith(progress:v.round())),
          onChangeEnd:_saving?null:(v)=>_save(_record.copyWith(progress:v.round()))),
        const SizedBox(height:12),
        TextField(controller:_responsible,maxLength:120,
          decoration:const InputDecoration(labelText:'Responsável',
            border:OutlineInputBorder())),
        const SizedBox(height:10),
        _date('Próxima visita',_nextVisit),
        const SizedBox(height:10),
        _date('Previsão de conclusão',_targetDate),
        const SizedBox(height:10),
        TextField(controller:_notes,maxLines:3,maxLength:1000,
          decoration:const InputDecoration(labelText:'Observações',
            border:OutlineInputBorder())),
        FilledButton.icon(onPressed:_saving?null:()=>_save(),
          icon:const Icon(Icons.save_outlined),label:const Text('Salvar acompanhamento')),
        const SizedBox(height:8),
        const SizedBox(height:12),
        Card(child:Padding(padding:const EdgeInsets.all(12),
          child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
            Text('Compartilhar acompanhamento',style:Theme.of(context).textTheme.titleMedium),
            const SizedBox(height:6),
            Text(_cloudMessage),
            const SizedBox(height:8),
            Wrap(spacing:8,runSpacing:8,children:[
              OutlinedButton.icon(
                onPressed:_cloudBusy||_saving?null:_shareWorksite,
                icon:const Icon(Icons.cloud_upload_outlined),
                label:const Text('Enviar para a Central')),
              OutlinedButton.icon(
                onPressed:_cloudBusy||_saving?null:_receiveWorksite,
                icon:const Icon(Icons.cloud_download_outlined),
                label:const Text('Consultar versão da Central')),
              TextButton.icon(
                onPressed:_cloudBusy||_saving?null:_restoreLocalBackup,
                icon:const Icon(Icons.restore_outlined),
                label:const Text('Restaurar cópia local')),
            ]),
            const SizedBox(height:6),
            const Text('O envio é manual nesta etapa. Fora da internet, o registro permanece local. Não altera fotos, relatórios ou a sincronização SST.'),
          ]))),
        const SizedBox(height:8),
        const Text('NCs, fotos e relatórios continuam disponíveis nos módulos SST com a sincronização existente.'),
        const Divider(height:30),
        Row(children:[
          Expanded(child:Text('Diário da obra',style:Theme.of(context).textTheme.titleMedium)),
          TextButton.icon(onPressed:_saving?null:_addLog,
            icon:const Icon(Icons.add),label:const Text('Novo registro')),
        ]),
        if(_record.log.isEmpty)const Padding(
          padding:EdgeInsets.all(12),child:Text('Sem registros no diário.')),
        for(final entry in _record.log)
          Card(child:ListTile(
            title:Text(entry.type),
            subtitle:Text((entry.at.length>=10?entry.at.substring(0,10):entry.at)+
              '\n'+entry.note),isThreeLine:true)),
      ]))),
  );
}

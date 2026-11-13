import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../services/cipa_member_portal_policy.dart';
import '../services/cipa_member_home_alerts.dart';
import '../services/cipa_member_draft_store.dart';
import '../widgets/cipa_member_access_header.dart';
import '../widgets/cipa_member_guided_inspection.dart';

/// UI do membro, independente da gestão interna. Este widget recebe somente
/// dados previamente filtrados no servidor; não consulta o banco de técnicos.
/// Sem sessão autorizada, o portal fica fechado (fail closed).
class CipaMemberPortalScreen extends StatefulWidget {
  const CipaMemberPortalScreen({
    super.key, required this.companyName, required this.mandateLabel,
    this.view, this.sessionVerified=false,
    this.onRefresh, this.onLogout, this.onAcknowledgeMeeting,
    this.onReportProgress, this.onRequestSupport, this.onObserve,
    this.onObserveScheduled, this.onAcknowledgeFeedback,
    this.onObserveWithPhotos,this.onObserveScheduledWithPhotos,
    this.onViewPhotos,this.onObserveDraft,this.onObserveScheduledDraft,
    this.offlineMode=false,this.pendingDraftCount=0,
    this.onEnableOffline,this.onSyncPending,this.onDraftSaved,
    this.onLoadPending,this.lastSync,
  });
  final String companyName,mandateLabel;
  final CipaMemberView? view;
  final bool sessionVerified,offlineMode;
  final int pendingDraftCount;
  final DateTime? lastSync;
  final Future<void> Function()? onEnableOffline,onSyncPending,onDraftSaved;
  final Future<List<CipaStoredDraft>> Function()? onLoadPending;
  final Future<void> Function()? onRefresh,onLogout;
  final Future<void> Function(String id)? onAcknowledgeMeeting;
  final Future<void> Function(String id,String note)? onReportProgress,onRequestSupport;
  final Future<void> Function(String place,String note)? onObserve;
  final Future<void> Function(String scheduleId,String place,String note)?
    onObserveScheduled;
  final Future<void> Function(String observationId,String reviewId)?
    onAcknowledgeFeedback;
  final Future<void> Function(String place,String note,List<Uint8List> photos)?
    onObserveWithPhotos;
  final Future<void> Function(String scheduleId,String place,String note,
    List<Uint8List> photos)? onObserveScheduledWithPhotos;
  final Future<List<Uint8List>> Function(String observationId)? onViewPhotos;
  final Future<void> Function(String place,String note,
    List<Uint8List> photos,String requestId)? onObserveDraft;
  final Future<void> Function(String scheduleId,String place,String note,
    List<Uint8List> photos,String requestId)? onObserveScheduledDraft;

  @override
  State<CipaMemberPortalScreen> createState() => _CipaMemberPortalScreenState();
}
class _CipaMemberPortalScreenState extends State<CipaMemberPortalScreen> {
  bool busy=false;
  bool easyMode=false;
  String error='';
  final Set<String> _confirmedReads={};
  final GlobalKey _meetingsSection=GlobalKey();
  final GlobalKey _tasksSection=GlobalKey();
  final GlobalKey _inspectionsSection=GlobalKey();
  final GlobalKey _observationsSection=GlobalKey();

  void _goTo(GlobalKey section) {
    final target=section.currentContext;
    if(target==null)return;
    Scrollable.ensureVisible(target,
      duration:const Duration(milliseconds:300),
      curve:Curves.easeInOut,
      alignment:0.08,
    );
  }

  Widget _largeAction({
    required String title,required IconData icon,
    required VoidCallback? onPressed,bool primary=false,
  })=>SizedBox(
    width:double.infinity,
    height:easyMode?70:58,
    child:primary
      ?FilledButton.icon(
        onPressed:onPressed,icon:Icon(icon,size:25),
        label:Text(title,style:TextStyle(fontSize:easyMode?20:17,
          fontWeight:FontWeight.w700)),
      )
      :OutlinedButton.icon(
        onPressed:onPressed,icon:Icon(icon,size:25),
        label:Text(title,style:TextStyle(fontSize:easyMode?20:17,
          fontWeight:FontWeight.w700)),
      ),
  );

  Future<void> _submit(Future<void> Function() call) async {
    if(busy||!widget.sessionVerified) return;
    setState(() {busy=true;error='';});
    try {
      try {
        await call();
      } catch (_) {
        if(mounted)setState(()=>error='A operação não foi confirmada. '
          'Confira o histórico antes de tentar novamente.');
        return;
      }
      // Atualizar a lista é separado de enviar. Falha de atualização
      // jamais pode induzir o membro a duplicar um registro recebido.
      if(widget.onRefresh!=null){
        try {
          await widget.onRefresh!();
        } catch (_) {
          if(mounted)setState(()=>error='A operação terminou, mas a lista '
            'não pôde ser atualizada. Confira o histórico quando voltar '
            'a ter conexão; não envie novamente sem conferir.');
        }
      }
    } finally {
      if(mounted)setState(()=>busy=false);
    }
  }

  Future<String?> _askNote(String title,String hint) async {
    final controller=TextEditingController();
    final result=await showDialog<String>(context:context,
      builder:(dialog)=>StatefulBuilder(builder:(context,update)=>AlertDialog(
        title:Text(title),
        content:SingleChildScrollView(child:Column(
          mainAxisSize:MainAxisSize.min,children:[
          Text(hint),const SizedBox(height:12),
          TextField(controller:controller,maxLength:1000,maxLines:4,
            onChanged:(_)=>update((){}),
            decoration:const InputDecoration(border:OutlineInputBorder(),
              labelText:'Descreva com suas palavras')),
        ])),
        actions:[
          TextButton(onPressed:()=>Navigator.pop(dialog),
            child:const Text('Cancelar')),
          FilledButton(onPressed:controller.text.trim().length<8?null:
            ()=>Navigator.pop(dialog,controller.text.trim()),
            child:const Text('Enviar para avaliação')),
        ],
      )));
    controller.dispose();
    return result;
  }

  Future<void> _newObservation() async {
    if(widget.onObserve==null)return;
    final place=TextEditingController(),text=TextEditingController();
    final save=await showDialog<bool>(context:context,builder:(dialog)=>
      StatefulBuilder(builder:(context,update)=>AlertDialog(
        title:const Text('Registrar situação observada'),
        content:SingleChildScrollView(child:Column(
          mainAxisSize:MainAxisSize.min,children:[
          const Text('Não se aproxime de um perigo para registrar. '
            'A equipe técnica analisará a informação.'),
          const SizedBox(height:8),
          TextField(controller:place,maxLength:120,
            onChanged:(_)=>update((){}),
            decoration:const InputDecoration(labelText:'Local')),
          TextField(controller:text,maxLength:1200,maxLines:4,
            onChanged:(_)=>update((){}),
            decoration:const InputDecoration(labelText:'O que você observou?')),
        ])),
        actions:[
          TextButton(onPressed:()=>Navigator.pop(dialog,false),
            child:const Text('Cancelar')),
          FilledButton(onPressed:place.text.trim().isEmpty||
            text.text.trim().length<8?null:()=>Navigator.pop(dialog,true),
            child:const Text('Enviar observação')),
        ],
      )));
    final p=place.text.trim(),v=text.text.trim();
    place.dispose();text.dispose();
    if(save==true&&mounted)await _submit(()=>widget.onObserve!(p,v));
  }

  static bool _isGuidedInspection(CipaMemberItem item) =>
    item.title.toLowerCase().contains('vistoria orientada') ||
    item.description.contains('VISTORIA ORIENTADA DA CIPA');

  Future<void> _guidedInspection({String? initialCategory,
      String? initialPlace,String? scheduleId,String? existingDraftId,
      bool legacyFree=false}) async {
    if(!widget.sessionVerified || busy ||
      (!widget.offlineMode && (scheduleId==null?widget.onObserve==null:
        widget.onObserveScheduled==null)))return;
    final profile=widget.view!.profile;
    final canPersist=widget.offlineMode||(scheduleId==null?
      widget.onObserveDraft!=null:widget.onObserveScheduledDraft!=null);
    CipaMemberDraftStore makeStore(String id)=>CipaMemberDraftStore(
      accountId:profile.userId,companyId:profile.companyId,
      mandateId:profile.mandateId,memberId:profile.memberId,
      scheduleId:scheduleId,
      draftId:scheduleId==null&&!legacyFree?id:null);
    final submitted=await showDialog<bool>(
      context:context,
      barrierDismissible:false,
      builder:(_)=>CipaGuidedInspectionDialog(
        initialCategory:initialCategory,initialPlace:initialPlace,
        draftStoreFactory:canPersist?makeStore:null,
        initialRequestId:existingDraftId,
        offlineDraftMode:widget.offlineMode,
        onSubmitDraft:!canPersist||widget.offlineMode?null:
          (place,note,photos,requestId) async {
          if(!widget.sessionVerified)throw StateError('Sessão inválida');
          if(scheduleId==null){
            final send=widget.onObserveDraft;
            if(send==null)throw StateError('Envio indisponível');
            await send(place,note,photos,requestId);
          }else{
            final send=widget.onObserveScheduledDraft;
            if(send==null)throw StateError('Envio indisponível');
            await send(scheduleId,place,note,photos,requestId);
          }
        },
        memberName:widget.view!.profile.fullName,
        memberRole:widget.view!.profile.cipaRole,
        companyName:widget.companyName,
        mandateLabel:widget.mandateLabel,
        onSendWithPhotos:(widget.onObserveWithPhotos==null&&
          widget.onObserveScheduledWithPhotos==null)?null:
          (place,note,photos) async {
          if(!widget.sessionVerified)throw StateError('Sessão inválida');
          if(scheduleId!=null){
            final sender=widget.onObserveScheduledWithPhotos;
            if(sender==null)throw StateError('Envio bloqueado');
            await sender(scheduleId,place,note,photos);
          }else{
            final sender=widget.onObserveWithPhotos;
            if(sender==null)throw StateError('Envio bloqueado');
            await sender(place,note,photos);
          }
        },
        onSend:(place,note) async {
          if(!widget.sessionVerified) {
            throw StateError('Sessão não autorizada');
          }
          // Sem vínculo, nunca informar que uma vistoria agendada foi realizada.
          if(scheduleId!=null){
            final sendScheduled=widget.onObserveScheduled;
            if(sendScheduled==null)throw StateError('Envio não autorizado');
            await sendScheduled(scheduleId,place,note);
          }else{
            final sendFree=widget.onObserve;
            if(sendFree==null)throw StateError('Envio não autorizado');
            await sendFree(place,note);
          }
        },
      ),
    );
    if(widget.onDraftSaved!=null){
      try {await widget.onDraftSaved!();}catch(_){}
    }
    if(submitted!=true || !mounted)return;
    if(widget.onRefresh!=null) {
      try {
        await widget.onRefresh!();
      } catch (_) {
        if(mounted)ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content:Text('Relato enviado pelo canal '
            'autorizado, mas não foi possível atualizar a lista. '
            'Atualize mais tarde; não reenvie sem conferir.')));
        return;
      }
    }
    if(mounted)ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content:Text('Registro enviado para análise. '
        'Acompanhe em Minhas vistorias.')));
  }

  Future<void> _showPending() async {
    if(busy||widget.onLoadPending==null)return;
    try {
      final entries=await widget.onLoadPending!();
      if(!mounted)return;
      final selected=await showDialog<CipaStoredDraft>(
        context:context,builder:(dialog)=>AlertDialog(
          title:const Text('Vistorias salvas no celular'),
          content:SizedBox(width:460,height:400,child:ListView(
            children:[
              const Text('Os registros abaixo ainda não comprovam envio. '
                'Escolha um rascunho para continuar ou entre com internet '
                'e toque em Enviar vistorias salvas.'),
              const SizedBox(height:12),
              for(final item in entries)Card(child:ListTile(
                leading:Icon(item.warning.isNotEmpty?
                  Icons.error_outline:item.complete?
                    Icons.task_alt_outlined:Icons.edit_note_outlined),
                title:Text(item.displayPlace),
                subtitle:Text(item.warning.isNotEmpty?item.warning:
                  item.complete?'Pronta para enviar':
                    'Incompleta: continuar preenchimento'),
                trailing:item.canResume?
                  const Icon(Icons.chevron_right):null,
                onTap:item.canResume?
                  ()=>Navigator.pop(dialog,item):null,
              )),
            ],
          )),
          actions:[TextButton(onPressed:()=>Navigator.pop(dialog),
            child:const Text('Fechar'))],
        ),
      );
      if(selected!=null&&mounted&&selected.canResume){
        await _guidedInspection(
          scheduleId:selected.scheduleId,
          existingDraftId:selected.draftId,
          legacyFree:selected.isLegacyFree,
          initialCategory:selected.draft?.category,
          initialPlace:selected.draft?.place,
        );
      }
    }catch(_){
      if(mounted)setState(()=>error='Não foi possível consultar os '
        'rascunhos protegidos. Seus dados não foram apagados.');
    }
  }
  Future<void> _viewPhotos(CipaMemberItem item) async {
    final p=widget.view?.profile;
    if(!widget.sessionVerified||busy||p==null||
       item.companyId!=p.companyId||item.mandateId!=p.mandateId||
       item.assignedMemberId!=p.memberId||widget.onViewPhotos==null)return;
    setState(()=>busy=true);
    List<Uint8List> images=[];
    try {
      images=await widget.onViewPhotos!(item.id);
    }catch(_){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content:Text('Não foi possível abrir as fotos.')));
    }finally{if(mounted)setState(()=>busy=false);}
    if(!mounted||images.isEmpty)return;
    await showDialog<void>(context:context,builder:(dialog)=>AlertDialog(
      title:const Text('Fotos desta vistoria'),
      content:SingleChildScrollView(child:Column(
        mainAxisSize:MainAxisSize.min,children:[
          for(final bytes in images)Padding(
            padding:const EdgeInsets.only(bottom:12),
            child:Image.memory(bytes,width:320,fit:BoxFit.contain)),
        ])),
      actions:[TextButton(onPressed:()=>Navigator.pop(dialog),
        child:const Text('Fechar'))],
    ));
  }

  Future<void> _acknowledgeFeedback(CipaMemberItem item) async {
    final callback=widget.onAcknowledgeFeedback;
    final profile=widget.view?.profile;
    if(busy||!widget.sessionVerified||callback==null||profile==null||
      item.companyId!=profile.companyId ||
      item.mandateId!=profile.mandateId ||
      item.assignedMemberId!=profile.memberId ||
      item.status!='Orientação enviada'||item.feedback.isEmpty||
      item.reviewId.isEmpty)return;
    final key='${item.id}|${item.reviewId}';
    setState(() {busy=true;error='';});
    try {
      await callback(item.id,item.reviewId);
      if(mounted)setState(()=>_confirmedReads.add(key));
      if(widget.onRefresh!=null){
        try {
          await widget.onRefresh!();
        } catch (_) {
          // A leitura já foi registrada. Não induzir a repetição do envio.
        }
      }
    } catch (_) {
      if(mounted)setState(()=>error='Leitura não confirmada. '
        'Confira o histórico antes de tentar novamente.');
    } finally {
      if(mounted)setState(()=>busy=false);
    }
  }

  Widget _feedbackReadAction(CipaMemberItem item) {
    final profile=widget.view?.profile;
    if(widget.onAcknowledgeFeedback==null||profile==null||
       item.companyId!=profile.companyId||
       item.mandateId!=profile.mandateId||
       item.assignedMemberId!=profile.memberId||
       item.status!='Orientação enviada'||item.feedback.isEmpty||
       item.reviewId.isEmpty||item.feedbackRead||
       _confirmedReads.contains('${item.id}|${item.reviewId}')) {
      return const SizedBox.shrink();
    }
    return SizedBox(width:double.infinity,child:OutlinedButton.icon(
      icon:const Icon(Icons.mark_chat_read_outlined),
      label:const Text('Li a orientação'),
      onPressed:busy?null:()=>_acknowledgeFeedback(item)));
  }

  void _showTutorial(){
    showDialog<void>(context:context,builder:(dialog)=>AlertDialog(
      title:const Text('Como usar a Minha CIPA'),
      content:const SingleChildScrollView(child:Column(
        mainAxisSize:MainAxisSize.min,
        crossAxisAlignment:CrossAxisAlignment.start,children:[
          ListTile(leading:Icon(Icons.assignment_outlined,size:32),
            title:Text('1. Faça sua vistoria'),
            subtitle:Text('São três perguntas. Observe apenas de um local seguro.')),
          ListTile(leading:Icon(Icons.camera_alt_outlined,size:32),
            title:Text('2. Tire até duas fotos'),
            subtitle:Text('Fotografe a situação, evitando mostrar pessoas.')),
          ListTile(leading:Icon(Icons.save_outlined,size:32),
            title:Text('3. Guarde e envie'),
            subtitle:Text('Se ficar sem internet, guarde o rascunho e envie ao se conectar.')),
          ListTile(leading:Icon(Icons.chat_outlined,size:32),
            title:Text('4. Veja o retorno'),
            subtitle:Text('O TST avalia o registro e informa as orientações.')),
        ],
      )),
      actions:[FilledButton(onPressed:()=>Navigator.pop(dialog),
        child:const Text('Entendi'))],
    ));
  }

  Widget _section(String title,IconData icon,List<CipaMemberItem> items,{
    Widget Function(CipaMemberItem)? actions,String empty='Nenhum registro disponível.',
  })=>Card(child:ExpansionTile(
    initiallyExpanded:items.isNotEmpty,
    leading:Icon(icon),
    title:Text('$title (${items.length})',
      style:const TextStyle(fontWeight:FontWeight.w700)),
    children:[
      if(items.isEmpty)ListTile(title:Text(empty)),
      for(final item in items)
        Column(children:[
          ListTile(title:Text(item.title),
            subtitle:Text([
              if(item.description.isNotEmpty)item.description,
              if(item.status.isNotEmpty)'Situação: ${item.status}',
              if(item.type==CipaMemberItemType.observation &&
                 item.feedback.isNotEmpty)
                'Resposta do técnico: ${item.feedback}',
              if(item.type==CipaMemberItemType.observation&&
                item.feedback.isNotEmpty&&
                (item.feedbackRead ||
                 _confirmedReads.contains('${item.id}|${item.reviewId}')))
                'Leitura confirmada pelo integrante',
              if(item.date!=null)'Data: ${item.date!.day}/${item.date!.month}/${item.date!.year}',
            ].join('\n'))),
          if(actions!=null)Padding(
            padding:const EdgeInsets.fromLTRB(12,0,12,12),
            child:actions(item)),
        ]),
    ],
  ));

  @override
  Widget build(BuildContext context) {
    final view=widget.view;
    if(!widget.sessionVerified || view==null) {
      return Scaffold(appBar:AppBar(title:const Text('Minha CIPA')),
        body:const SafeArea(child:Center(child:Padding(
          padding:EdgeInsets.all(24),
          child:Column(mainAxisSize:MainAxisSize.min,children:[
            Icon(Icons.lock_outline,size:48),
            SizedBox(height:14),
            Text('Acesso pessoal não liberado',
              textAlign:TextAlign.center,
              style:TextStyle(fontSize:20,fontWeight:FontWeight.w800)),
            SizedBox(height:10),
            Text('Somente uma sessão individual validada pela Central '
              'permite abrir o portal. Não use a conta do técnico ou administrador.',
              textAlign:TextAlign.center),
          ]),
        ))));
    }
    final profile=view.profile;
    final inspections=view.observations.where(_isGuidedInspection)
      .toList(growable:false);
    final otherObservations=view.observations.where(
      (item)=>!_isGuidedInspection(item)).toList(growable:false);
    final alerts=CipaHomeAlertBuilder.fromView(view,locallyRead:_confirmedReads);
    return Scaffold(
      appBar:AppBar(title:const Text('Minha CIPA'),actions:[
        IconButton(onPressed:()=>setState(()=>easyMode=!easyMode),
          tooltip:easyMode?'Sair do modo fácil':'Ativar modo fácil',
          icon:Icon(easyMode?Icons.text_decrease:Icons.text_increase)),
        IconButton(onPressed:_showTutorial,tooltip:'Como usar',
          icon:const Icon(Icons.help_outline)),
        if(!widget.offlineMode&&widget.onRefresh!=null)IconButton(
          onPressed:busy?null:()=>_submit(widget.onRefresh!),
          tooltip:'Atualizar',icon:const Icon(Icons.refresh)),
        if(widget.onLogout!=null)IconButton(
          onPressed:busy?null:()=>_submit(widget.onLogout!),
          tooltip:widget.offlineMode?'Fechar dados salvos':'Sair da conta',
          icon:const Icon(Icons.logout)),
      ]),
      body:SafeArea(child:ListView(
        padding:const EdgeInsets.fromLTRB(12,12,12,64),children:[
        CipaMemberAccessHeader(profile:profile,
          companyName:widget.companyName,mandateLabel:widget.mandateLabel),
        Card(child:Padding(padding:const EdgeInsets.all(12),
          child:Column(
            crossAxisAlignment:CrossAxisAlignment.stretch,children:[
              Row(children:[
                Icon(widget.offlineMode?Icons.wifi_off:Icons.cloud_done_outlined),
                const SizedBox(width:8),
                Expanded(child:Text(widget.offlineMode?
                  'Offline: informações protegidas neste aparelho':
                  'Última consulta confirmada pela Central',
                  style:const TextStyle(fontWeight:FontWeight.w700))),
              ]),
              if(widget.lastSync!=null)
                Text('Última atualização: '+
                  widget.lastSync!.toLocal().toString().substring(0,16)),
              if(widget.offlineMode)
                const Text('Você pode consultar informações salvas e '
                  'preencher vistorias. Para enviar, entre com internet. '
                  'As informações podem ter mudado na Central.'),
              if(widget.pendingDraftCount>0)
                Text('Rascunhos no aparelho: '+
                  widget.pendingDraftCount.toString()+
                  '. Ainda não foram confirmados pela Central.'),
              if(widget.onEnableOffline!=null&&!widget.offlineMode)
                OutlinedButton.icon(
                  onPressed:busy?null:()=>_submit(widget.onEnableOffline!),
                  icon:const Icon(Icons.offline_bolt_outlined),
                  label:const Text('Ativar acesso offline com PIN')),
              if(widget.onLoadPending!=null&&
                 widget.pendingDraftCount>0)
                OutlinedButton.icon(
                  onPressed:busy?null:_showPending,
                  icon:const Icon(Icons.folder_open_outlined),
                  label:const Text('Ver rascunhos no celular')),
              if(widget.onSyncPending!=null&&!widget.offlineMode&&
                 widget.pendingDraftCount>0)
                FilledButton.icon(
                  onPressed:busy?null:()=>_submit(widget.onSyncPending!),
                  icon:const Icon(Icons.sync),
                  label:const Text('Enviar vistorias salvas')),
            ],
          ))),
        if(alerts.isNotEmpty)Card(child:Padding(
          padding:const EdgeInsets.all(12),
          child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
            const Text('Seus avisos',style:TextStyle(
              fontWeight:FontWeight.w800,fontSize:17)),
            for(final alert in alerts)ListTile(
              dense:!easyMode,
              leading:Icon(alert.kind==CipaHomeAlertKind.inspection?
                Icons.assignment_outlined:
                alert.kind==CipaHomeAlertKind.meetingTomorrow?
                Icons.event_outlined:Icons.mark_chat_unread_outlined),
              title:Text(alert.message,style:TextStyle(
                fontSize:easyMode?19:16,fontWeight:FontWeight.w600)),
              trailing:const Icon(Icons.chevron_right),
              onTap:()=>_goTo(alert.kind==CipaHomeAlertKind.inspection?
                _inspectionsSection:
                alert.kind==CipaHomeAlertKind.meetingTomorrow?
                _meetingsSection:_observationsSection),
            ),
            const Text('Toque no aviso para ver os detalhes.',
              style:TextStyle(fontSize:13)),
          ]))),
        Card(child:Padding(padding:const EdgeInsets.all(16),
          child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
            Text('O que você quer fazer hoje?',
              style:Theme.of(context).textTheme.titleLarge
                ?.copyWith(fontWeight:FontWeight.w800)),
            const SizedBox(height:5),
            const Text('Para fazer uma vistoria, toque no primeiro botão. '
              'São somente 3 perguntas por setor.',
              style:TextStyle(fontSize:16)),
            const SizedBox(height:14),
            if(widget.onObserve!=null||widget.offlineMode)...[
              _largeAction(
                title:'Fazer vistoria',
                icon:Icons.assignment_outlined,
                onPressed:busy?null:_guidedInspection,
                primary:true,
              ),
              const SizedBox(height:10),
            ],
            _largeAction(
              title:'Minhas tarefas',icon:Icons.fact_check_outlined,
              onPressed:busy?null:()=>_goTo(_tasksSection),
            ),
            const SizedBox(height:10),
            _largeAction(
              title:'Ver reuniões',icon:Icons.event_outlined,
              onPressed:busy?null:()=>_goTo(_meetingsSection),
            ),
            const SizedBox(height:10),
            Text('Você tem '+
              view.pendingActions.toString()+' tarefa(s) em acompanhamento.',
              style:const TextStyle(fontSize:15)),
            const SizedBox(height:4),
            const Text('Você só registra o que viu de um local seguro. '
              'A equipe de SST confere os relatos e as ações.',
              style:TextStyle(fontSize:14)),
          ]))),
        if(busy)const LinearProgressIndicator(),
        if(error.isNotEmpty)Padding(
          padding:const EdgeInsets.all(12),
          child:Text(error,style:TextStyle(color:
            Theme.of(context).colorScheme.error))),
        KeyedSubtree(key:_meetingsSection,
          child:_section('Convocações e reuniões',Icons.event_outlined,view.meetings,
          empty:'Nenhuma convocação liberada para você.',
          actions:(item)=>Align(alignment:Alignment.centerRight,
            child:widget.onAcknowledgeMeeting!=null &&
                 CipaMemberPortalRules.canAcknowledge(profile,item)
              ?TextButton.icon(
                onPressed:busy?null:()=>_submit(
                  ()=>widget.onAcknowledgeMeeting!(item.id)),
                icon:const Icon(Icons.mark_email_read_outlined),
                label:const Text('Confirmar ciência do aviso'))
              :const SizedBox.shrink()))),
        const Padding(padding:EdgeInsets.fromLTRB(16,0,16,10),
          child:Text('Ciência não é presença na reunião nem assinatura da ata.',
            style:TextStyle(fontSize:12))),
        KeyedSubtree(key:_tasksSection,
          child:_section('Minhas tarefas',Icons.task_alt_outlined,view.myActions,
          empty:'Não há ação atribuída ao seu cadastro individual.',
          actions:(item)=>Wrap(spacing:8,runSpacing:8,children:[
            if(widget.onReportProgress!=null &&
               CipaMemberPortalRules.canReportAction(profile,item))
              OutlinedButton.icon(
                onPressed:busy?null:() async {
                  final note=await _askNote('Informar andamento',
                    'Descreva o que mudou. A equipe técnica vai conferir.');
                  if(note!=null&&mounted)await _submit(
                    ()=>widget.onReportProgress!(item.id,note));
                },icon:const Icon(Icons.edit_note_outlined),
                label:const Text('Informar andamento')),
            if(widget.onRequestSupport!=null &&
               CipaMemberPortalRules.canReportAction(profile,item))
              TextButton.icon(
                onPressed:busy?null:() async {
                  final note=await _askNote('Solicitar apoio',
                    'Conte o que está impedindo sua tarefa.');
                  if(note!=null&&mounted)await _submit(
                    ()=>widget.onRequestSupport!(item.id,note));
                },icon:const Icon(Icons.help_outline),
                label:const Text('Preciso de apoio')),
          ]))),
        KeyedSubtree(key:_inspectionsSection,
          child:_section('Vistorias programadas',Icons.calendar_month_outlined,
          view.scheduledInspections,
          empty:'Nenhuma vistoria programada para você.',
          actions:(item)=>(widget.onObserveScheduled==null&&
            !widget.offlineMode)||item.status!='Programada'?
            const SizedBox.shrink():
            SizedBox(width:double.infinity,child:OutlinedButton.icon(
              onPressed:busy?null:()=>_guidedInspection(
                initialCategory:item.title.replaceFirst('Vistoria: ',''),
                scheduleId:item.id),
              icon:const Icon(Icons.play_arrow),
              label:const Text('Iniciar esta vistoria'))))),
        const Padding(padding:EdgeInsets.fromLTRB(16,0,16,10),
          child:Text('Na data programada, use Fazer vistoria. '
            'Evite áreas de risco; o registro será analisado pelo TST.',
            style:TextStyle(fontSize:12))),
        KeyedSubtree(key:_observationsSection,
          child:_section('Minhas vistorias orientadas',
          Icons.fact_check_outlined,inspections,
          empty:'Nenhuma vistoria orientada disponível nesta consulta.',
          actions:(item)=>Wrap(spacing:8,runSpacing:8,children:[
            if(widget.onViewPhotos!=null&&!widget.offlineMode)
              OutlinedButton.icon(onPressed:busy?null:()=>_viewPhotos(item),
                icon:const Icon(Icons.photo_outlined),
                label:const Text('Ver fotos')),
            _feedbackReadAction(item),
          ]))),
        const Padding(padding:EdgeInsets.fromLTRB(16,0,16,10),
          child:Text('A situação mostrada é a que a equipe registrou. '
            'O envio não confirma correção nem encerra ação.',
            style:TextStyle(fontSize:12))),
        Card(child:ExpansionTile(
          initiallyExpanded:false,
          leading:const Icon(Icons.more_horiz,size:28),
          title:const Text('Mais informações',
            style:TextStyle(fontSize:17,fontWeight:FontWeight.w700)),
          subtitle:const Text('Relatos, avisos, treinamentos e documentos'),
          children:[
        if(widget.onObserve!=null)
          Padding(padding:const EdgeInsets.fromLTRB(12,4,12,12),
            child:SizedBox(width:double.infinity,height:52,
              child:OutlinedButton.icon(
                onPressed:busy?null:_newObservation,
                icon:const Icon(Icons.edit_note),
                label:const Text('Avisar uma situação')))),
        _section('Avisos',Icons.notifications_none_outlined,view.notices),
        _section('Meu treinamento',Icons.school_outlined,view.trainings),
        _section('Documentos liberados',Icons.folder_open_outlined,view.documents),
        _section('Outras observações',Icons.visibility_outlined,
          otherObservations,actions:_feedbackReadAction),
        _section('Lembretes',Icons.alarm_outlined,view.reminders),
          ],
        )),
        const Card(child:ExpansionTile(
          initiallyExpanded:false,
          leading:Icon(Icons.help_outline),
          title:Text('Como funciona a minha participação',
            style:TextStyle(fontSize:17,fontWeight:FontWeight.w700)),
          subtitle:Text('Guia rápido em quatro passos'),
          children:[
            ListTile(
              leading:CircleAvatar(child:Text('1')),
              title:Text('Recebi um aviso de reunião'),
              subtitle:Text('Leia data, local e pauta. Confirmar ciência '
                'significa que você viu o aviso, não que esteve presente.')),
            ListTile(
              leading:CircleAvatar(child:Text('2')),
              title:Text('Tenho uma tarefa'),
              subtitle:Text('Leia o que foi combinado. Use Informar andamento '
                'ou Preciso de apoio. O responsável precisa conferir a execução.')),
            ListTile(
              leading:CircleAvatar(child:Text('3')),
              title:Text('Quero fazer uma vistoria'),
              subtitle:Text('Escolha o setor e responda às perguntas '
                'apenas sobre o que pode observar com segurança. '
                'Se não souber, marque Não sei/não verifiquei.')),
            ListTile(
              leading:CircleAvatar(child:Text('4')),
              title:Text('Observei uma situação'),
              subtitle:Text('Informe local e descrição com suas palavras, '
                'sem se expor a riscos. O envio não abre nem encerra '
                'automaticamente uma não conformidade.')),
          ],
        )),
        const Card(child:Padding(padding:EdgeInsets.all(14),
          child:Text('Como participar: observe sem se aproximar de perigos, '
            'registre local e situação, acompanhe sua tarefa e peça apoio. '
            'Não precisa indicar qual NR se aplica. A gestão é responsável '
            'pela avaliação técnica e conclusão de ações.'))),
      ])),
    );
  }
}

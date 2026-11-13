import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:cryptography/cryptography.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'screens/cipa_member_portal_screen.dart';
import 'services/cipa_member_api.dart';
import 'services/cipa_member_draft_store.dart';
import 'services/cipa_member_portal_policy.dart';
import 'services/cipa_member_offline_cache.dart';
import 'services/cipa_member_pending_sync.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const AuditarCipaMemberApp());
}

class AuditarCipaMemberApp extends StatelessWidget {
  const AuditarCipaMemberApp({super.key});
  @override
  Widget build(BuildContext context)=>MaterialApp(
    debugShowCheckedModeBanner:false,
    title:'Minha CIPA',
    theme:ThemeData(
      useMaterial3:true,
      colorScheme:ColorScheme.fromSeed(seedColor:const Color(0xFF17477D)),
      inputDecorationTheme:const InputDecorationTheme(
        border:OutlineInputBorder()),
    ),
    home:const CipaMemberEntryScreen(),
  );
}
class CipaMemberEntryScreen extends StatefulWidget {
  const CipaMemberEntryScreen({super.key});
  @override
  State<CipaMemberEntryScreen> createState()=>_CipaMemberEntryScreenState();
}
class _CipaMemberEntryScreenState extends State<CipaMemberEntryScreen>
    with WidgetsBindingObserver {
  static const endpoint=String.fromEnvironment(
    'AUDITAR_MEMBER_ENDPOINT',defaultValue:'');
  late final CipaMemberApi api=CipaMemberApi(
    endpoint:endpoint,onSessionRevoked:(){
      final person=view??lastOnlineView;
      if(person!=null){
        _draftStoreFor(person).clearAllForMember().catchError((_) {});
      }
      final address=onlineEmail;
      if(address!=null)offlineCache.clear(address).catchError((_) {});
      if(mounted)setState((){
        view=null;offlineUnlocked=false;lastOnlineView=null;
      });
    });
  final email=TextEditingController(),code=TextEditingController(),
    offlinePin=TextEditingController();
  final CipaMemberOfflineCache offlineCache=CipaMemberOfflineCache();
  final CipaMemberPendingSync pendingSync=CipaMemberPendingSync();
  String? onlineEmail;
  CipaMemberView? lastOnlineView;
  DateTime? lastSync;
  bool offlineUnlocked=false;
  int pendingDraftCount=0;
  bool busy=false,requested=false;
  String message='',error='';
  CipaMemberView? view;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if(state==AppLifecycleState.inactive||
       state==AppLifecycleState.hidden||
       state==AppLifecycleState.paused) {
      if(mounted)setState((){
        view=null;offlineUnlocked=false;
      }); // Bloquear tela e exigir novo desbloqueio após retorno.
    } else if(state==AppLifecycleState.resumed&&api.hasSession) {
      _refresh();
    }
  }
  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    email.dispose();code.dispose();offlinePin.dispose();
    api.dispose();super.dispose();
  }
  Future<void> _run(Future<void> Function() work) async {
    if(busy)return;
    setState((){busy=true;error='';});
    try {await work();}
    catch(e) {
      if(mounted)setState(()=>error=e.toString()
          .replaceFirst('Bad state: ',''));
    } finally {
      if(mounted)setState(()=>busy=false);
    }
  }
  Future<void> _start() async {
    final address=email.text.trim();
    if(!RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(address)) {
      setState(()=>error='Informe o e-mail cadastrado na CIPA.');
      return;
    }
    await _run(() async {
      await api.requestCode(address);
      if(mounted)setState((){
        requested=true;
        message='Se este e-mail estiver autorizado, um código '
            'de 8 dígitos será enviado. Confira também a caixa de spam.';
      });
    });
  }
  Future<void> _showWelcomeOnce(CipaMemberView person) async {
    try {
      final p=person.profile;
      final identifier=[p.userId,p.companyId,p.mandateId,p.memberId].join('|');
      final hash=await Sha256().hash(utf8.encode(identifier));
      final key='cipa_guide_v1_'+base64UrlEncode(hash.bytes).replaceAll('=','');
      const secure=FlutterSecureStorage();
      if(await secure.read(key:key)=='seen'||!mounted||!api.hasSession)return;
      await secure.write(key:key,value:'seen');
      if(!mounted||!api.hasSession)return;
      await showDialog<void>(context:context,builder:(dialog)=>AlertDialog(
        title:const Text('Bem-vindo à Minha CIPA'),
        content:const SingleChildScrollView(child:Column(
          mainAxisSize:MainAxisSize.min,children:[
            ListTile(leading:Icon(Icons.assignment_outlined,size:32),
              title:Text('Fazer vistoria'),
              subtitle:Text('Responda três perguntas, sem se aproximar do perigo.')),
            ListTile(leading:Icon(Icons.camera_alt_outlined,size:32),
              title:Text('Tirar foto'),
              subtitle:Text('Você pode adicionar até duas fotos da situação.')),
            ListTile(leading:Icon(Icons.save_outlined,size:32),
              title:Text('Guardar e sair'),
              subtitle:Text('Se estiver sem internet, seu rascunho fica protegido.')),
            ListTile(leading:Icon(Icons.chat_bubble_outline,size:32),
              title:Text('Ver resposta do técnico'),
              subtitle:Text('O TST analisa e orienta; você não precisa validar o risco.')),
          ],
        )),
        actions:[FilledButton(onPressed:()=>Navigator.pop(dialog),
          child:const Text('Entendi'))],
      ));
    }catch (_) {
      // Ausência de cofre seguro não pode impedir o login autorizado.
    }
  }

  Future<void> _verify() async {
    if(!RegExp(r'^\d{8}$').hasMatch(code.text.trim())) {
      setState(()=>error='Informe os 8 dígitos recebidos.');
      return;
    }
    await _run(() async {
      await api.verifyCode(email.text,code.text);
      final current=await api.dashboard();
      if(mounted){
        final address=email.text.trim();
        setState((){
          view=current;lastOnlineView=current;onlineEmail=address;
          offlineUnlocked=false;lastSync=DateTime.now();
          code.clear();offlinePin.clear();
        });
        try{await offlineCache.updateFromServer(address,current);}catch(_){}
        await _loadDraftCount(current);
        await _showWelcomeOnce(current);
      }
    });
  }
  Future<void> _refresh() async {
    if(!api.hasSession) {
      if(mounted)setState(()=>view=null);
      return;
    }
    try {
      final current=await api.dashboard();
      if(mounted){
        setState((){
          view=current;lastOnlineView=current;offlineUnlocked=false;
          lastSync=DateTime.now();
        });
        final address=onlineEmail;
        if(address!=null){
          try{await offlineCache.updateFromServer(address,current);}catch(_){}
        }
        await _loadDraftCount(current);
      }
    } catch (_) {
      if(mounted)setState(()=>view=null);
      rethrow;
    }
  }
  CipaMemberDraftStore _draftStoreFor(CipaMemberView person){
    final p=person.profile;
    return CipaMemberDraftStore(
      accountId:p.userId,companyId:p.companyId,
      mandateId:p.mandateId,memberId:p.memberId);
  }

  Future<void> _logout() async {
    final localView=view??lastOnlineView;
    var count=pendingDraftCount;
    if(localView!=null){
      try {count=await pendingSync.count(localView);}
      catch (_) {count=-1;} // Falha de leitura exige confirmação explícita.
    }
    if(count!=0 && mounted){
      final confirmed=await showDialog<bool>(context:context,
        builder:(dialog)=>AlertDialog(
          title:const Text('Sair e apagar dados locais?'),
          content:Text(count<0?
            'Não foi possível conferir os rascunhos protegidos. '
            'Sair pode apagar registros ainda não enviados. '
            'Para mantê-los, toque em Voltar.':
            'Existem '+count.toString()+
            ' rascunhos ainda no aparelho. Sair da conta apaga '
            'esses rascunhos e o acesso offline. Para manter, '
            'toque em Voltar.'),
          actions:[
            TextButton(onPressed:()=>Navigator.pop(dialog,false),
              child:const Text('Voltar')),
            FilledButton(onPressed:()=>Navigator.pop(dialog,true),
              child:const Text('Sair e apagar')),
          ],
        ));
      if(confirmed!=true)return;
    }
    final current=view??lastOnlineView;
    final address=onlineEmail;
    if(current!=null){
      try {await _draftStoreFor(current).clearAllForMember();}
      catch (_) {/* Não impedir a saída nem expor conteúdo criptografado. */}
    }
    if(address!=null){
      try{await offlineCache.clear(address);}catch(_){}
    }
    await api.logout();
    if(mounted)setState((){
      view=null;lastOnlineView=null;onlineEmail=null;
      offlineUnlocked=false;lastSync=null;pendingDraftCount=0;
      code.clear();offlinePin.clear();requested=false;message='';error='';
    });
  }

  Future<void> _loadDraftCount(CipaMemberView current) async {
    try {
      final n=await pendingSync.count(current);
      if(mounted && view?.profile.userId==current.profile.userId &&
         view?.profile.mandateId==current.profile.mandateId)
        setState(()=>pendingDraftCount=n);
    }catch(_){
      if(mounted)setState(()=>pendingDraftCount=0);
    }
  }

  Future<void> _enableOffline() async {
    final current=view,address=onlineEmail;
    if(current==null||address==null||!api.hasSession)
      throw StateError('Entre com seu código por e-mail primeiro.');
    final pin=TextEditingController(),repeat=TextEditingController();
    String? chosen;
    try {
      chosen=await showDialog<String>(context:context,builder:(dialog)=>
        StatefulBuilder(builder:(context,update)=>AlertDialog(
          title:const Text('Ativar uso offline neste aparelho'),
          content:SingleChildScrollView(child:Column(
            mainAxisSize:MainAxisSize.min,children:[
            const Text('Escolha um PIN de seis números. Só este PIN '
              'abrirá os dados salvos depois de você entrar com '
              'internet ao menos uma vez. Os dados vencem em 24 horas.'),
            const SizedBox(height:12),
            TextField(controller:pin,obscureText:true,
              keyboardType:TextInputType.number,maxLength:6,
              onChanged:(_)=>update((){}),
              decoration:const InputDecoration(labelText:'Meu PIN offline')),
            TextField(controller:repeat,obscureText:true,
              keyboardType:TextInputType.number,maxLength:6,
              onChanged:(_)=>update((){}),
              decoration:const InputDecoration(labelText:'Repetir PIN')),
          ])),
          actions:[
            TextButton(onPressed:()=>Navigator.pop(dialog),
              child:const Text('Cancelar')),
            FilledButton(onPressed:pin.text.length==6&&
                pin.text==repeat.text?()=>Navigator.pop(dialog,pin.text):null,
              child:const Text('Ativar offline')),
          ],
        )));
    }finally{
      pin.dispose();repeat.dispose();
    }
    if(chosen==null||!mounted)return;
    // Ativação só com autorização ainda válida neste instante.
    final fresh=await api.dashboard();
    if(fresh.profile.userId!=current.profile.userId||
       fresh.profile.companyId!=current.profile.companyId||
       fresh.profile.mandateId!=current.profile.mandateId||
       fresh.profile.memberId!=current.profile.memberId)
      throw StateError('Vínculo mudou; entre novamente.');
    await offlineCache.enroll(address,chosen,fresh);
    if(mounted)ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content:Text('Uso offline ativado neste aparelho. '
        'Guarde seu PIN. Validade da consulta: 24 horas.')));
  }

  Future<void> _openOffline() async {
    final address=email.text.trim(),pin=offlinePin.text.trim();
    if(!CipaMemberOfflineCache.validEmail(address)||
       !CipaMemberOfflineCache.validPin(pin)){
      setState(()=>error='Informe o e-mail cadastrado e seu PIN offline '
        'de seis números.');
      return;
    }
    await _run(()async {
      final snapshot=await offlineCache.unlock(address,pin);
      if(!mounted)return;
      setState((){
        view=snapshot.view;offlineUnlocked=true;
        lastSync=snapshot.syncedAt;
        offlinePin.clear();error='';
      });
      await _loadDraftCount(snapshot.view);
    });
  }

  Future<void> _closeOffline() async {
    if(mounted)setState((){
      view=null;offlineUnlocked=false;pendingDraftCount=0;
      offlinePin.clear();
    });
  }

  Future<void> _sendStoredDraft({
    String? scheduleId,required String place,required String note,
    required List<Uint8List> photos,required String requestId,
  }) async {
    if(!api.hasSession)throw StateError('Entre novamente com internet');
    if(scheduleId!=null){
      await api.observeScheduledDraft(scheduleId,place,note,photos,requestId);
    }else{
      await api.observeDraft(place,note,photos,requestId);
    }
  }

  Future<void> _syncPending() async {
    final person=view;
    if(person==null||!api.hasSession||offlineUnlocked)
      throw StateError('Entre com internet para enviar registros.');
    // Conferir mandato de novo antes de tocar nos registros locais.
    final fresh=await api.dashboard();
    if(fresh.profile.userId!=person.profile.userId||
       fresh.profile.companyId!=person.profile.companyId||
       fresh.profile.mandateId!=person.profile.mandateId||
       fresh.profile.memberId!=person.profile.memberId)
      throw StateError('Mandato mudou. Não envie rascunhos antigos.');
    final plan=CipaPendingSyncPlan.fromEntries(await pendingSync.list(fresh));
    if(!mounted)return;
    if(!plan.canSend){
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content:Text('Não há vistoria completa e autorizada para enviar. '
          'Confira os rascunhos pendentes.')));
      return;
    }
    final confirmed=await showDialog<bool>(context:context,
      builder:(dialog)=>AlertDialog(
        title:const Text('Conferir antes de enviar'),
        content:SingleChildScrollView(child:Column(
          mainAxisSize:MainAxisSize.min,
          crossAxisAlignment:CrossAxisAlignment.start,children:[
            Text('Prontas para envio: ${plan.ready}',
              style:const TextStyle(fontWeight:FontWeight.w700,fontSize:18)),
            Text('Fotografias destas vistorias: ${plan.photoCount}'),
            Text('Incompletas: ${plan.incomplete}'),
            Text('Bloqueadas ou não recuperáveis: ${plan.blocked}'),
            const SizedBox(height:10),
            const Text('As vistorias incompletas e bloqueadas NÃO serão '
              'enviadas nem apagadas. O envio pode usar dados móveis. '
              'Confira fotos e relatos antes de continuar.'),
          ])),
        actions:[
          TextButton(onPressed:()=>Navigator.pop(dialog,false),
            child:const Text('Voltar')),
          FilledButton(onPressed:()=>Navigator.pop(dialog,true),
            child:const Text('Confirmar envio')),
        ],
      ));
    if(confirmed!=true||!mounted)return;
    // Vínculo conferido novamente após confirmação do usuário.
    final newest=await api.dashboard();
    if(newest.profile.userId!=fresh.profile.userId||
       newest.profile.companyId!=fresh.profile.companyId||
       newest.profile.mandateId!=fresh.profile.mandateId||
       newest.profile.memberId!=fresh.profile.memberId)
      throw StateError('Vínculo mudou durante o envio. Entre novamente.');
    final report=await pendingSync.sync(newest,_sendStoredDraft);
    if(mounted){
      await _loadDraftCount(fresh);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content:Text('Confirmados pela Central: '+report.sent.toString()+
          '. Pendentes/incompletos: '+report.remaining.toString()+
          '. Falhas: '+report.failed.toString()+'.'),
      ));
    }
  }

  @override
  Widget build(BuildContext context) {
    final person=view;
    if(person!=null) {
      return CipaMemberPortalScreen(
        companyName:person.companyLabel,mandateLabel:person.mandateLabel,
        view:person,sessionVerified:api.hasSession||offlineUnlocked,
        offlineMode:offlineUnlocked,pendingDraftCount:pendingDraftCount,
        lastSync:lastSync,
        onRefresh:offlineUnlocked?null:_refresh,
        onLogout:offlineUnlocked?_closeOffline:_logout,
        onEnableOffline:offlineUnlocked?null:_enableOffline,
        onSyncPending:offlineUnlocked?null:_syncPending,
        onDraftSaved:()=>_loadDraftCount(person),
        onLoadPending:()=>pendingSync.list(person),
        onAcknowledgeMeeting:offlineUnlocked?null:api.acknowledge,
        onReportProgress:offlineUnlocked?null:api.progress,
        onRequestSupport:offlineUnlocked?null:api.support,
        onObserve:offlineUnlocked?null:api.observe,
        onObserveWithPhotos:offlineUnlocked?null:api.observeWithPhotos,
        onObserveDraft:offlineUnlocked?null:api.observeDraft,
        onObserveScheduled:offlineUnlocked?null:api.observeScheduled,
        onObserveScheduledWithPhotos:
          offlineUnlocked?null:api.observeScheduledWithPhotos,
        onObserveScheduledDraft:
          offlineUnlocked?null:api.observeScheduledDraft,
        onViewPhotos:offlineUnlocked?null:api.photosForObservation,
        onAcknowledgeFeedback:offlineUnlocked?null:api.acknowledgeFeedback,
        onLoadMural:offlineUnlocked?null:api.mural,
        onCreateMural:offlineUnlocked?null:api.muralCreate,
        onCommentMural:offlineUnlocked?null:api.muralComment,
        onPhotoMural:offlineUnlocked?null:api.muralPhoto,
        onLoadAvatar:offlineUnlocked?null:api.loadAvatar,
        onSaveAvatar:offlineUnlocked?null:api.saveAvatar,
        onDeleteAvatar:offlineUnlocked?null:api.deleteAvatar,
      );
    }
    return Scaffold(
      appBar:AppBar(title:const Text('Minha CIPA')),
      body:SafeArea(child:Center(
        child:SingleChildScrollView(
          padding:const EdgeInsets.all(18),
          child:ConstrainedBox(constraints:const BoxConstraints(maxWidth:480),
            child:Card(child:Padding(
              padding:const EdgeInsets.all(20),
              child:Column(
                crossAxisAlignment:CrossAxisAlignment.stretch,
                mainAxisSize:MainAxisSize.min,
                children:[
                  const Icon(Icons.groups_outlined,size:48),
                  const SizedBox(height:8),
                  Text('Meu acesso à CIPA',textAlign:TextAlign.center,
                    style:Theme.of(context).textTheme.headlineSmall?.
                      copyWith(fontWeight:FontWeight.w900)),
                  const SizedBox(height:8),
                  const Text('Acesse com seu próprio e-mail. '
                    'O administrador precisa autorizar seu vínculo '
                    'com a empresa e o mandato.',
                    textAlign:TextAlign.center),
                  const SizedBox(height:18),
                  if(!api.configured)
                    const Text('Aplicativo de homologação ainda sem '
                      'Central configurada. Nenhum acesso será liberado.',
                      textAlign:TextAlign.center),
                  TextField(controller:email,
                    enabled:!busy&&api.configured&&!requested,
                    keyboardType:TextInputType.emailAddress,
                    decoration:const InputDecoration(
                      labelText:'Meu e-mail cadastrado',
                      prefixIcon:Icon(Icons.mail_outline))),
                  const SizedBox(height:12),
                  if(requested)...[
                    TextField(controller:code,enabled:!busy,
                      keyboardType:TextInputType.number,
                      maxLength:8,
                      decoration:const InputDecoration(
                        labelText:'Código de 8 dígitos',
                        prefixIcon:Icon(Icons.lock_outline))),
                    const SizedBox(height:10),
                  ],
                  if(busy)const LinearProgressIndicator(),
                  if(message.isNotEmpty)...[
                    const SizedBox(height:8),
                    Text(message,textAlign:TextAlign.center),
                  ],
                  if(error.isNotEmpty)...[
                    const SizedBox(height:8),
                    Text(error,style:TextStyle(
                      color:Theme.of(context).colorScheme.error)),
                  ],
                  const SizedBox(height:16),
                  FilledButton.icon(
                    onPressed:busy||!api.configured?null:
                      requested?_verify:_start,
                    icon:Icon(requested?
                      Icons.verified_user_outlined:Icons.mail_outline),
                    label:Text(requested?'Entrar com código':
                      'Receber código por e-mail')),
                  if(requested)TextButton(
                    onPressed:busy?null:()=>setState((){
                      requested=false;code.clear();message='';error='';
                    }),child:const Text('Trocar e-mail')),
                  const SizedBox(height:10),
                  if(!requested)...[
                    const Divider(height:28),
                    const Text('Sem internet?',
                      style:TextStyle(fontWeight:FontWeight.w700,fontSize:18)),
                    const Text('Se já ativou o modo offline neste aparelho, '
                      'use o seu e-mail e PIN de seis números.'),
                    const SizedBox(height:10),
                    TextField(controller:offlinePin,obscureText:true,
                      enabled:!busy,maxLength:6,
                      keyboardType:TextInputType.number,
                      decoration:const InputDecoration(
                        labelText:'Meu PIN offline',
                        prefixIcon:Icon(Icons.offline_bolt_outlined))),
                    OutlinedButton.icon(
                      onPressed:busy?null:_openOffline,
                      icon:const Icon(Icons.lock_open_outlined),
                      label:const Text('Abrir dados salvos offline')),
                  ],
                  const SizedBox(height:10),
                  const Text('Aplicativo exclusivo dos integrantes: '
                    'sem login de técnico ou sincronização geral da base '
                    'do Auditar SST. O primeiro acesso exige internet.',
                    textAlign:TextAlign.center,
                    style:TextStyle(fontSize:12)),
                ],
              ),
            ))),
        ),
      )),
    );
  }
}

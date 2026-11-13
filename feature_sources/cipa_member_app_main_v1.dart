import 'dart:convert';
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
    title:'Minha CIPA • Auditar',
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

  @override
  Widget build(BuildContext context) {
    final person=view;
    if(person!=null) {
      return CipaMemberPortalScreen(
        companyName:person.companyLabel,mandateLabel:person.mandateLabel,
        view:person,sessionVerified:api.hasSession,
        onRefresh:_refresh,onLogout:_logout,
        onAcknowledgeMeeting:api.acknowledge,
        onReportProgress:api.progress,
        onRequestSupport:api.support,
        onObserve:api.observe,
        onObserveWithPhotos:api.observeWithPhotos,
        onObserveDraft:api.observeDraft,
        onObserveScheduled:api.observeScheduled,
        onObserveScheduledWithPhotos:api.observeScheduledWithPhotos,
        onObserveScheduledDraft:api.observeScheduledDraft,
        onViewPhotos:api.photosForObservation,
        onAcknowledgeFeedback:api.acknowledgeFeedback,
      );
    }
    return Scaffold(
      appBar:AppBar(title:const Text('Minha CIPA • Auditar')),
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
                  const Text('Este acesso não utiliza o login '
                    'de técnico/administrador e não tem sincronização '
                    'completa nem acesso offline.',
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

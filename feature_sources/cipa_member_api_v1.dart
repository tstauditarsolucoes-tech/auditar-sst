import 'dart:convert';
import 'dart:math';
import 'package:http/http.dart' as http;

import 'cipa_member_identity.dart';
import 'cipa_member_portal_policy.dart';

/// Cliente pessoal separado: SEM AuthService, SQLite, syncKey, Drive ou
/// sincronização geral do aplicativo técnico.
class CipaMemberApi {
  CipaMemberApi({required String endpoint,http.Client? client,
    this.onSessionRevoked})
    : _endpoint=Uri.tryParse(endpoint.trim()),
      _client=client??http.Client();

  final Uri? _endpoint;
  final http.Client _client;
  final void Function()? onSessionRevoked;
  final Map<String,String> _pendingIds={};
  String? _token;

  bool get hasSession=>_token!=null;
  bool get configured=>_endpoint!=null &&
    _endpoint!.scheme=='https' && _endpoint!.host=='script.google.com' &&
    _endpoint!.path.startsWith('/macros/s/') &&
    _endpoint!.path.endsWith('/exec');

  Future<Map<String,dynamic>> _call(String action,
      [Map<String,dynamic> fields=const {}]) async {
    if(!configured)throw StateError('A Central da CIPA não foi configurada.');
    final response=await _client.post(_endpoint!,
      headers:const {'Content-Type':'application/json; charset=utf-8'},
      body:jsonEncode({'action':action,...fields}))
      .timeout(const Duration(seconds:25));
    if(response.statusCode<200||response.statusCode>=300) {
      throw StateError('A Central não respondeu corretamente.');
    }
    final decoded=jsonDecode(utf8.decode(response.bodyBytes));
    if(decoded is! Map)throw StateError('Resposta inválida da Central.');
    final result=Map<String,dynamic>.from(decoded);
    if(result['ok']!=true) {
      final code=(result['code']??'').toString();
      if(code=='SESSION_INVALID') {
        _token=null;
        onSessionRevoked?.call();
      }
      throw StateError(code=='FEATURE_DISABLED'?
        'O portal individual ainda não foi habilitado pela Auditar.':
        code=='SESSION_INVALID'?
        'Sua sessão expirou ou foi revogada. Entre novamente.':
        (result['message']??'Operação não concluída.').toString());
    }
    return result;
  }

  Future<void> requestCode(String email) async {
    await _call('cipa_member_begin',{'email':email.trim()});
  }
  Future<void> verifyCode(String email,String code) async {
    final result=await _call('cipa_member_verify',{
      'email':email.trim(),'code':code.trim()});
    final token=(result['sessionToken']??'').toString().trim();
    if(token.length<64)throw StateError('A Central não confirmou a sessão.');
    _token=token; // token somente na memória; não persistir em SQLite.
  }

  static String _str(dynamic value)=>value==null?'':value.toString();
  static DateTime? _date(dynamic value)=>
      value==null?null:DateTime.tryParse(value.toString());

  List<CipaMemberItem> _items(Map<String,dynamic> response,
      String key,CipaMemberItemType type,CipaMemberAccessProfile p) {
    final data=response[key];
    if(data is! List)return const [];
    final result=<CipaMemberItem>[];
    for(final raw in data) {
      if(raw is! Map)continue;
      final r=Map<String,dynamic>.from(raw);
      final id=_str(r['id']),title=_str(r['title']);
      if(id.isEmpty||title.isEmpty)continue;
      result.add(CipaMemberItem(
        id:id,title:title,
        companyId:p.companyId,mandateId:p.mandateId,
        assignedMemberId:p.memberId,
        visibleToAllMembers:type!=CipaMemberItemType.action &&
          type!=CipaMemberItemType.training &&
          type!=CipaMemberItemType.observation,
        type:type,description:_str(r['description']),
        status:_str(r['status']),
        date:_date(r['date']),dueDate:_date(r['dueDate']),
      ));
      if(result.length==100)break;
    }
    return result;
  }

  Future<CipaMemberView> dashboard() async {
    final token=_token;
    if(token==null)throw StateError('Entre com seu código pessoal.');
    final response=await _call('cipa_member_dashboard',
      {'sessionToken':token});
    final raw=response['profile'];
    if(raw is! Map)throw StateError('Identificação não confirmada.');
    final p=Map<String,dynamic>.from(raw);
    final user=_str(p['userId']),company=_str(p['companyId']),
      mandate=_str(p['mandateId']),member=_str(p['memberId']);
    if(user.isEmpty||company.isEmpty||mandate.isEmpty||member.isEmpty)
      throw StateError('O vínculo com a CIPA não foi confirmado.');
    final profile=CipaMemberProfileContract.fromVerifiedMembership(
      authenticatedUserId:user,grantedCompanyId:company,
      grantedMandateId:mandate,grantedMemberId:member,
      membershipUserId:user,membershipCompanyId:company,
      membershipMandateId:mandate,membershipMemberId:member,
      membershipWorkerId:_str(p['workerId']),
      fullName:_str(p['fullName']),cipaRole:_str(p['cipaRole']),
      representation:_str(p['representation']),
      jobTitle:_str(p['jobTitle']),
      userActive:true,mandateActive:true,memberActive:true,
    );
    if(profile==null)throw StateError('Perfil de membro incompatível.');
    final rows=<CipaMemberItem>[
      ..._items(response,'meetings',CipaMemberItemType.meeting,profile),
      ..._items(response,'actions',CipaMemberItemType.action,profile),
      ..._items(response,'notices',CipaMemberItemType.notice,profile),
      ..._items(response,'trainings',CipaMemberItemType.training,profile),
      ..._items(response,'documents',CipaMemberItemType.document,profile),
      ..._items(response,'observations',CipaMemberItemType.observation,profile),
      ..._items(response,'reminders',CipaMemberItemType.reminder,profile),
    ];
    return CipaMemberPortalRules.build(
      verifiedProfile:profile,records:rows,
      companyLabel:_str(response['companyName']).isNotEmpty
        ?_str(response['companyName']):'Empresa vinculada à CIPA',
      mandateLabel:_str(response['mandateTitle']).isNotEmpty
        ?_str(response['mandateTitle']):'Mandato atual');
  }

  String _id(String key) => _pendingIds.putIfAbsent(key,(){
    final random=Random.secure();
    final bytes=List<int>.generate(24,(_)=>random.nextInt(256));
    return 'mobile-'+bytes.map((b)=>b.toRadixString(16).padLeft(2,'0')).join();
  });

  Future<void> send(String kind,String target,String note,
      {String place=''}) async {
    if(_token==null)throw StateError('Entre novamente.');
    if(!['acknowledge','progress','support','observation'].contains(kind))
      throw StateError('Operação não permitida.');
    final clean=note.trim();
    if(clean.length<8||clean.length>1200)
      throw StateError('Descrição obrigatória de 8 a 1200 caracteres.');
    final key=kind+'|'+target+'|'+place.trim()+'|'+clean;
    await _call('cipa_member_event',{
      'sessionToken':_token,'kind':kind,'targetId':target,
      'detail':clean,'location':place.trim(),'requestId':_id(key)});
    _pendingIds.remove(key);
  }
  Future<void> acknowledge(String meeting)=>
    send('acknowledge',meeting,
      'Ciência da convocação registrada; não é presença.');
  Future<void> progress(String action,String text)=>
    send('progress',action,text);
  Future<void> support(String action,String text)=>
    send('support',action,text);
  Future<void> observe(String place,String text)=>
    send('observation','',text,place:place);

  Future<void> logout() async {
    final token=_token;
    _token=null;_pendingIds.clear();
    if(token!=null){
      try {await _call('cipa_member_logout',{'sessionToken':token});}
      catch (_) {/* Descarta a sessão local mesmo sem resposta da rede. */}
    }
  }
  void dispose(){_token=null;_pendingIds.clear();_client.close();}
}

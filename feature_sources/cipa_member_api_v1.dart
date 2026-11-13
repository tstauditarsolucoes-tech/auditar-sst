import 'dart:convert';
import 'dart:math';
import 'dart:typed_data';
import 'package:http/http.dart' as http;

import 'cipa_member_identity.dart';
import 'cipa_member_portal_policy.dart';
import 'cipa_member_mural_model.dart';

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




  Future<void> submitAfterPhoto(String postId,Uint8List jpeg) async {
    if(_token==null)throw StateError('Entre para registrar a foto posterior.');
    if(!RegExp(r'^[A-Za-z0-9_-]{16,120}$').hasMatch(postId)||
       !CipaMuralCodec.validPhoto(jpeg))
      throw StateError('Imagem posterior inválida.');
    await _call('cipa_mural_after_upload',{
      'sessionToken':_token,'postId':postId,
      'jpegBase64':base64Encode(jpeg),
    });
  }
  Future<Uint8List?> afterPhoto(String postId) async {
    if(_token==null)throw StateError('Entre para consultar a foto posterior.');
    if(!RegExp(r'^[A-Za-z0-9_-]{16,120}$').hasMatch(postId))
      throw StateError('Ocorrência não identificada.');
    final reply=await _call('cipa_mural_after_photo',{
      'sessionToken':_token,'postId':postId,
    });
    if(reply['hasPhoto']!=true)return null;
    final encoded=(reply['jpegBase64']??'').toString();
    if(encoded.length>340000)throw StateError('Imagem acima do limite.');
    final bytes=Uint8List.fromList(base64Decode(encoded));
    if(!CipaMuralCodec.validPhoto(bytes))
      throw StateError('Imagem posterior inválida.');
    return bytes;
  }

  Future<void> submitMinutes(String meetingId,String content) async {
    if(_token==null)throw StateError('Entre para enviar sua minuta.');
    if(!RegExp(r'^[A-Za-z0-9_-]{3,150}$').hasMatch(meetingId)||
      content.length<130||content.length>5000||
      !content.startsWith('RASCUNHO EDUCATIVO'))
      throw StateError('Minuta inválida ou sem vínculo de reunião.');
    final key='minuta|'+meetingId+'|'+content;
    await _call('cipa_minutes_submit',{
      'sessionToken':_token,'meetingId':meetingId,
      'content':content,'requestId':_id(key),
    });
    _pendingIds.remove(key);
  }

  Future<List<Map<String,dynamic>>> myMinutes() async {
    if(_token==null)throw StateError('Entre para consultar suas minutas.');
    final reply=await _call('cipa_minutes_list',{'sessionToken':_token});
    final items=reply['minutes'];
    if(items is! List)return const [];
    return items.whereType<Map>()
      .map((r)=>Map<String,dynamic>.from(r)).take(50).toList();
  }

  Future<Uint8List?> loadAvatar() async {
    if(_token==null)throw StateError('Entre para visualizar o perfil.');
    final reply=await _call('cipa_member_avatar_get',{'sessionToken':_token});
    if(reply['hasPhoto']!=true)return null;
    final encoded=(reply['jpegBase64']??'').toString();
    if(encoded.length>210000)throw StateError('Foto acima do limite.');
    final bytes=Uint8List.fromList(base64Decode(encoded));
    if(bytes.length<8||bytes.length>150000||bytes[0]!=255||
      bytes[1]!=216||bytes[2]!=255||bytes[bytes.length-2]!=255||
      bytes.last!=217)throw StateError('Foto inválida.');
    return bytes;
  }
  Future<void> saveAvatar(Uint8List jpeg) async {
    if(_token==null)throw StateError('Entre para alterar seu perfil.');
    if(jpeg.length<8||jpeg.length>150000||jpeg[0]!=255||
      jpeg[1]!=216||jpeg[2]!=255||jpeg[jpeg.length-2]!=255||
      jpeg.last!=217)throw StateError('Foto inválida.');
    await _call('cipa_member_avatar_save',{
      'sessionToken':_token,'jpegBase64':base64Encode(jpeg)});
  }
  Future<void> deleteAvatar() async {
    if(_token==null)throw StateError('Entre para remover sua foto.');
    await _call('cipa_member_avatar_delete',{'sessionToken':_token});
  }

  Future<List<CipaMuralPost>> mural() async {
    if(_token==null)throw StateError('Entre para visualizar o mural.');
    final result=await _call('cipa_mural_list',{'sessionToken':_token});
    return CipaMuralCodec.parsePosts(result['posts']);
  }

  Future<void> muralCreate(String place,String detail,Uint8List? photo,
      {String? durableRequestId}) async {
    if(_token==null)throw StateError('Entre para registrar no mural.');
    final local=place.trim(),note=detail.trim();
    if(local.length<2||local.length>120||note.length<12||note.length>900)
      throw StateError('Informe o local e a situação (12 a 900 letras).');
    if(photo!=null&&!CipaMuralCodec.validPhoto(photo))
      throw StateError('Foto não permitida. Escolha outra.');
    final key='mural-post|'+local+'|'+note+'|'+
      (photo==null?'sem-foto':base64Encode(photo));
    if(durableRequestId!=null&&
      !RegExp(r'^[A-Za-z0-9_-]{16,120}$').hasMatch(durableRequestId))
      throw StateError('Identificador de rascunho inválido.');
    final id=durableRequestId??_id(key);
    await _call('cipa_mural_create',{
      'sessionToken':_token,'requestId':id,
      'place':local,'detail':note,
      if(photo!=null)'jpegBase64':base64Encode(photo),
    });
    _pendingIds.remove(key);
  }

  Future<void> muralComment(String postId,String message) async {
    if(_token==null)throw StateError('Entre para comentar.');
    final note=message.trim();
    if(!RegExp(r'^[A-Za-z0-9_-]{16,120}$').hasMatch(postId)||
       note.length<5||note.length>450)
      throw StateError('Comentário inválido.');
    final key='mural-comment|'+postId+'|'+note;
    await _call('cipa_mural_comment',{
      'sessionToken':_token,'postId':postId,
      'body':note,'requestId':_id(key),
    });
    _pendingIds.remove(key);
  }

  Future<Uint8List?> muralPhoto(String postId) async {
    if(_token==null)throw StateError('Entre para ver a foto.');
    if(!RegExp(r'^[A-Za-z0-9_-]{16,120}$').hasMatch(postId))
      throw StateError('Publicação inválida.');
    final result=await _call('cipa_mural_photo',{
      'sessionToken':_token,'postId':postId,
    });
    if(result['hasPhoto']!=true)return null;
    final raw=(result['jpegBase64']??'').toString();
    if(raw.length>340000)throw StateError('Foto muito grande.');
    final bytes=Uint8List.fromList(base64Decode(raw));
    if(!CipaMuralCodec.validPhoto(bytes))
      throw StateError('Foto inválida.');
    return bytes;
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
      final companyId=_str(r['companyId']);
      final mandateId=_str(r['mandateId']);
      final memberId=_str(r['assignedMemberId']);
      final shared=r['visibleToAllMembers']==true;
      if(companyId!=p.companyId||mandateId!=p.mandateId)continue;
      final privateType=type==CipaMemberItemType.action ||
        type==CipaMemberItemType.meeting ||
        type==CipaMemberItemType.training ||
        type==CipaMemberItemType.observation ||
        type==CipaMemberItemType.reminder ||
        type==CipaMemberItemType.scheduledInspection;
      if(privateType&&memberId!=p.memberId)continue;
      if(!privateType&&!shared)continue;
      result.add(CipaMemberItem(
        id:id,title:title,
        companyId:companyId,mandateId:mandateId,
        assignedMemberId:memberId,
        visibleToAllMembers:shared,
        type:type,description:_str(r['description']),
        feedback:type==CipaMemberItemType.observation?
          _str(r['feedback']):'',
        reviewId:type==CipaMemberItemType.observation?
          _str(r['reviewId']):'',
        feedbackRead:type==CipaMemberItemType.observation&&
          r['feedbackRead']==true,
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
      ..._items(response,'scheduledInspections',
        CipaMemberItemType.scheduledInspection,profile),
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
      {String place='',List<Uint8List> photos=const [],
      String? durableRequestId}) async {
    if(_token==null)throw StateError('Entre novamente.');
    if(!['acknowledge','progress','support','observation'].contains(kind))
      throw StateError('Operação não permitida.');
    if(photos.length>2||photos.any((p)=>p.length>700000))
      throw StateError('Máximo duas fotos comprimidas por vistoria.');
    final clean=note.trim();
    if(clean.length<8||clean.length>1200)
      throw StateError('Descrição obrigatória de 8 a 1200 caracteres.');
    final key=kind+'|'+target+'|'+place.trim()+'|'+clean;
    if(durableRequestId!=null&&
       !RegExp(r'^[A-Za-z0-9_-]{16,120}$').hasMatch(durableRequestId))
      throw StateError('Identificação do rascunho inválida.');
    final eventId=durableRequestId??_id(key);
    await _call('cipa_member_event',{
      'sessionToken':_token,'kind':kind,'targetId':target,
      'detail':clean,'location':place.trim(),'requestId':eventId});
    for(var i=0;i<photos.length;i++){
      final bytes=photos[i];
      await _call('cipa_member_photo_upload',{
        'sessionToken':_token,'observationId':eventId,
        'slot':i+1,'jpegBase64':base64Encode(bytes),
      });
    }
    // Preservar requestId caso o upload falhe, para retry idempotente.
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
  Future<void> observeWithPhotos(String place,String text,
      List<Uint8List> photos)=>
    send('observation','',text,place:place,photos:photos);

  /// Associação obrigatória no servidor ao agendamento pessoal vigente.
  Future<void> observeScheduled(String scheduleId,String place,String text) async {
    if(!scheduleId.startsWith('cipa-inspection-'))
      throw StateError('Agendamento não identificado.');
    await send('observation',scheduleId,text,place:place);
  }

  Future<void> observeScheduledWithPhotos(String scheduleId,String place,
      String text,List<Uint8List> photos) async {
    if(!scheduleId.startsWith('cipa-inspection-'))
      throw StateError('Agendamento não identificado.');
    await send('observation',scheduleId,text,place:place,photos:photos);
  }

  Future<void> observeDraft(String place,String text,
      List<Uint8List> photos,String requestId)=>
    send('observation','',text,place:place,photos:photos,
      durableRequestId:requestId);

  Future<void> observeScheduledDraft(String scheduleId,String place,
      String text,List<Uint8List> photos,String requestId) async {
    if(!scheduleId.startsWith('cipa-inspection-'))
      throw StateError('Agendamento não identificado.');
    await send('observation',scheduleId,text,place:place,photos:photos,
      durableRequestId:requestId);
  }

  Future<List<Uint8List>> photosForObservation(String observationId) async {
    if(_token==null)throw StateError('Entre novamente.');
    final found=await _call('cipa_member_photo_list',{
      'sessionToken':_token,'observationId':observationId});
    final slots=found['slots'];
    if(slots is! List)return const [];
    final images=<Uint8List>[];
    for(final slot in slots.whereType<int>().take(2)){
      final image=await _call('cipa_member_photo_get',{
        'sessionToken':_token,'observationId':observationId,'slot':slot});
      final payload=(image['jpegBase64']??'').toString();
      images.add(base64Decode(payload));
    }
    return images;
  }

  Future<void> acknowledgeFeedback(String observationId,
      String reviewId) async {
    if(_token==null)throw StateError('Entre novamente.');
    if(observationId.isEmpty||reviewId.isEmpty)
      throw StateError('Orientação não identificada.');
    final key='feedback|$observationId|$reviewId';
    await _call('cipa_member_ack_feedback',{
      'sessionToken':_token,'observationId':observationId,
      'reviewId':reviewId,'requestId':_id(key),
    });
    _pendingIds.remove(key);
  }

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

import 'dart:convert';
import 'dart:math';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../services/apps_script_http.dart';
import '../services/auth_service.dart';
import '../services/web_service_config.dart';
import '../widgets/cipa_manager_metrics_panel.dart';
import '../widgets/cipa_mural_moderation_panel.dart';
import '../widgets/cipa_minutes_review_panel.dart';

/// Apenas consultar observações e responder: controle real fica no servidor.
class CipaTstReviewScreen extends StatefulWidget {
  const CipaTstReviewScreen({
    super.key,required this.companyId,required this.mandateId,
  });
  final String companyId,mandateId;
  @override State<CipaTstReviewScreen> createState()=>_CipaTstReviewScreenState();
}
class _CipaTstReviewScreenState extends State<CipaTstReviewScreen> {
  bool busy=false;
  String error='';
  List<Map<String,dynamic>> records=[];
  Map<String,dynamic>? metrics;
  final Map<String,String> retryIds={};
  @override void initState(){super.initState();_reload();}
  Future<Map<String,dynamic>> _call(String action,
      [Map<String,dynamic> params=const {}]) async {
    if(AuthService.sessionToken.isEmpty)throw StateError('Entre novamente.');
    final uri=Uri.tryParse(WebServiceConfig.endpoint.trim());
    if(uri==null||uri.scheme!='https')
      throw StateError('Central não configurada.');
    final res=await AppsScriptHttp.postJson(uri,{
      'action':action,'authToken':AuthService.sessionToken,
      'companyId':widget.companyId,'mandateId':widget.mandateId,...params,
    });
    if(res.statusCode!=200)throw StateError('Central indisponível.');
    final raw=jsonDecode(res.body);
    if(raw is! Map)throw StateError('Resposta inválida.');
    final data=Map<String,dynamic>.from(raw);
    if(data['ok']!=true)throw StateError('Sem autorização para este mandato.');
    return data;
  }
  Future<void> _reload() async {
    if(busy)return;
    setState(() {busy=true;error='';});
    try {
      final data=await _call('cipa_tst_review_inbox');
      final items=data['events'];
      Map<String,dynamic>? checkedMetrics;
      try {
        final report=await _call('cipa_tst_metrics');
        final scope=report['scope'];
        if(scope is Map&&scope['companyId']==widget.companyId&&
           scope['mandateId']==widget.mandateId)checkedMetrics=report;
      }catch (_) {/* Não inferir contagens se a API indisponível. */}
      if(mounted)setState((){
        metrics=checkedMetrics;
        records=items is List?
          items.whereType<Map>().map((e)=>Map<String,dynamic>.from(e))
            .where((e)=>e['companyId']==widget.companyId&&
              e['mandateId']==widget.mandateId).toList():[];
      });
    }catch (_) {
      if(mounted)setState(() {
        records=[];
        error='Acesso não confirmado ou falha na conexão.';
      });
    }finally{if(mounted)setState(()=>busy=false);}
  }
  String _id(String key)=>retryIds.putIfAbsent(key,(){
    final rnd=Random.secure();
    return 'tst-'+List<int>.generate(24,(_)=>rnd.nextInt(256))
      .map((n)=>n.toRadixString(16).padLeft(2,'0')).join();
  });
  Future<void> _viewPhotos(Map<String,dynamic> record) async {
    if(busy||record['companyId']!=widget.companyId||
       record['mandateId']!=widget.mandateId)return;
    final id=(record['id']??'').toString();
    if(id.isEmpty)return;
    setState(()=>busy=true);
    final images=<dynamic>[];
    try {
      final listed=await _call('cipa_tst_photo_list',{'observationId':id});
      if(listed['slots'] is List){
        for(final slot in (listed['slots'] as List).whereType<int>().take(2)){
          final photo=await _call('cipa_tst_photo_get',{
            'observationId':id,'slot':slot,
          });
          images.add(base64Decode((photo['jpegBase64']??'').toString()));
        }
      }
    }catch(_){
      if(mounted)setState(()=>error='Fotos indisponíveis ou acesso revogado.');
    }finally{if(mounted)setState(()=>busy=false);}
    if(!mounted)return;
    await showDialog<void>(context:context,builder:(dialog)=>AlertDialog(
      title:const Text('Fotos da vistoria'),
      content:SingleChildScrollView(child:Column(
        mainAxisSize:MainAxisSize.min,
        children:images.isEmpty?[const Text('Nenhuma foto disponível.')]:
          images.map((b)=>Padding(padding:const EdgeInsets.only(bottom:8),
            child:Image.memory(b,width:380,fit:BoxFit.contain))).toList(),
      )),
      actions:[TextButton(onPressed:()=>Navigator.pop(dialog),
        child:const Text('Fechar'))],
    ));
  }

  Future<void> _reply(Map<String,dynamic> record) async {
    if(busy||record['companyId']!=widget.companyId||
      record['mandateId']!=widget.mandateId)return;
    final id=(record['id']??'').toString();
    if(id.isEmpty)return;
    var status='Em análise',message='';
    final result=await showDialog<Map<String,String>>(
      context:context,builder:(dialog)=>StatefulBuilder(
        builder:(context,update)=>AlertDialog(
          title:const Text('Responder ao integrante'),
          content:SingleChildScrollView(child:Column(
            mainAxisSize:MainAxisSize.min,
            crossAxisAlignment:CrossAxisAlignment.stretch,children:[
            const Text('Somente o integrante verá esta orientação. '
              'Não inclua dados de saúde nem nomes de terceiros.'),
            const SizedBox(height:10),
            DropdownButtonFormField<String>(
              value:status,
              decoration:const InputDecoration(labelText:'Situação'),
              items:const [
                DropdownMenuItem(value:'Em análise',child:Text('Em análise')),
                DropdownMenuItem(value:'Orientação enviada',
                  child:Text('Orientação enviada')),
              ],
              onChanged:(v)=>update(()=>status=v??'Em análise'),
            ),
            TextField(maxLines:3,maxLength:600,
              onChanged:(v)=>update(()=>message=v),
              decoration:const InputDecoration(
                labelText:'Orientação para o membro')),
            const Text('A resposta não encerra uma não conformidade.'),
          ])),
          actions:[
            TextButton(onPressed:()=>Navigator.pop(dialog),
              child:const Text('Cancelar')),
            FilledButton(
              onPressed:(message.trim().isNotEmpty&&message.trim().length<8)||
                (status=='Orientação enviada'&&message.trim().length<8)
                ?null:()=>Navigator.pop(dialog,{
                  'status':status,'message':message.trim(),
                }),
              child:const Text('Registrar resposta')),
          ],
        )));
    if(result==null||!mounted)return;
    final key=[id,result['status'],result['message']].join('|');
    setState(() {busy=true;error='';});
    var success=false;
    try {
      await _call('cipa_tst_review_observation',{
        'observationId':id,'status':result['status'],
        'message':result['message'],'requestId':_id(key),
      });
      retryIds.remove(key);
      success=true;
    }catch (_){
      if(mounted)setState(()=>error='Resposta não confirmada. '
        'Consulte o histórico antes de reenviar.');
    }finally{if(mounted)setState(()=>busy=false);}
    if(success&&mounted)await _reload();
  }
  Widget _observationCard(Map<String,dynamic> record) {
    return Card(
      child:Padding(
        padding:const EdgeInsets.all(12),
        child:Column(
          crossAxisAlignment:CrossAxisAlignment.stretch,
          children:<Widget>[
            Text((record['location']??'Setor não informado').toString(),
              style:Theme.of(context).textTheme.titleMedium),
            Text((record['detail']??'').toString(),maxLines:7,
              overflow:TextOverflow.ellipsis),
            Text('Situação: '+(record['status']??'Recebido').toString()),
            if((record['feedback']??'').toString().isNotEmpty)
              Text('Orientação anterior: '+record['feedback'].toString()),
            const SizedBox(height:8),
            SizedBox(height:50,child:OutlinedButton.icon(
              onPressed:busy?null:()=>_viewPhotos(record),
              icon:const Icon(Icons.photo_outlined),
              label:const Text('Ver fotos'),
            )),
            const SizedBox(height:8),
            SizedBox(height:50,child:FilledButton.icon(
              onPressed:busy?null:()=>_reply(record),
              icon:const Icon(Icons.reply_outlined),
              label:const Text('Responder ao membro'),
            )),
          ],
        ),
      ),
    );
  }

  Future<List<Map<String,dynamic>>> _muralList() async {
    final data=await _call('cipa_mural_moderator_list');
    final rows=data['posts'];
    return rows is List?rows.whereType<Map>()
      .map((row)=>Map<String,dynamic>.from(row)).toList():[];
  }
  Future<void> _muralReview(
    String id,String visibility,String status,bool verified) async {
    await _call('cipa_mural_moderate',{
      'postId':id,'visibility':visibility,'status':status,
      'confirmedByResponsible':verified,
    });
  }
  Future<void> _muralReviewComment(String id,bool approved) async {
    await _call('cipa_mural_moderate_comment',{
      'commentId':id,'visibility':approved?'Aprovado':'Não publicado',
    });
  }
  Future<void> _muralReply(String id,String text,String requestId) async {
    await _call('cipa_mural_reply',{
      'postId':id,'body':text,'requestId':requestId,
    });
  }
  Future<Uint8List?> _muralPhoto(String id) async {
    final data=await _call('cipa_mural_moderator_photo',{'postId':id});
    if(data['hasPhoto']!=true)return null;
    final encoded=(data['jpegBase64']??'').toString();
    if(encoded.length>340000)throw StateError('Foto muito grande.');
    final bytes=Uint8List.fromList(base64Decode(encoded));
    if(bytes.length<8||bytes.length>250000)
      throw StateError('Foto inválida.');
    return bytes;
  }



  Future<Uint8List?> _muralAfterPhoto(String id) async{
    final data=await _call('cipa_mural_after_staff_photo',{'postId':id});
    if(data['hasPhoto']!=true)return null;
    final encoded=(data['jpegBase64']??'').toString();
    if(encoded.length>340000)throw StateError('Foto muito grande.');
    final bytes=Uint8List.fromList(base64Decode(encoded));
    if(bytes.length<8||bytes.length>250000)
      throw StateError('Foto inválida.');
    return bytes;
  }
  Future<void> _muralAfterReview(String id,bool approve)async{
    await _call('cipa_mural_after_moderate',{
      'postId':id,'visibility':approve?'Aprovado':'Não publicado',
    });
  }

  Future<List<Map<String,dynamic>>> _minutesStaffList() async{
    final reply=await _call('cipa_minutes_staff_list');
    final data=reply['minutes'];
    if(data is! List)return const [];
    return data.whereType<Map>()
      .map((row)=>Map<String,dynamic>.from(row)).toList();
  }
  Future<void> _minutesStaffReview(String id,String status,String note) async{
    await _call('cipa_minutes_review',{
      'minuteId':id,'status':status,'note':note,
    });
  }

  @override Widget build(BuildContext context) {
    return Scaffold(
      appBar:AppBar(title:const Text('Vistorias da CIPA'),actions:[
        IconButton(onPressed:busy?null:_reload,
          tooltip:'Atualizar',icon:const Icon(Icons.refresh)),
      ]),
      body:SafeArea(child:ListView(
        padding:const EdgeInsets.all(12),
        children:<Widget>[
          const Text('Relatos para orientação. Não é possível encerrar '
            'não conformidades nesta tela.'),
          if(busy)const LinearProgressIndicator(),
          if(error.isNotEmpty)Text(error),
          CipaMinutesReviewPanel(
            onLoad:_minutesStaffList,onReview:_minutesStaffReview),
          CipaMuralModerationPanel(
            onLoad:_muralList,onReview:_muralReview,
            onCommentReview:_muralReviewComment,
            onReply:_muralReply,onPhoto:_muralPhoto,
            onPhotoAfter:_muralAfterPhoto,
            onReviewAfter:_muralAfterReview),
          CipaManagerMetricsPanel(companyId:widget.companyId,
            mandateId:widget.mandateId,serverData:metrics),
          if(!busy&&records.isEmpty)const Text('Nenhum relato disponível.'),
          ...records.reversed.map(_observationCard),
        ],
      )),
    );
  }
}

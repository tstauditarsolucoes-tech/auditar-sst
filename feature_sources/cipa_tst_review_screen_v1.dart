import 'dart:convert';
import 'dart:math';
import 'package:flutter/material.dart';
import '../services/apps_script_http.dart';
import '../services/auth_service.dart';
import '../services/web_service_config.dart';

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
      if(mounted)setState(()=>records=items is List?
        items.whereType<Map>().map((e)=>Map<String,dynamic>.from(e))
          .where((e)=>e['companyId']==widget.companyId&&
            e['mandateId']==widget.mandateId).toList():[]);
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
  @override Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:const Text('Vistorias da CIPA'),actions:[
      IconButton(onPressed:busy?null:_reload,
        tooltip:'Atualizar',icon:const Icon(Icons.refresh)),
    ]),
    body:SafeArea(child:ListView(
      padding:const EdgeInsets.all(12),children:[
        const Text('Relatos para orientação. Não é possível encerrar '
          'não conformidades nesta tela.'),
        if(busy)const LinearProgressIndicator(),
        if(error.isNotEmpty)Text(error),
        if(!busy&&records.isEmpty)const Text('Nenhum relato disponível.'),
        for(final record in records.reversed)
          Card(child:Padding(padding:const EdgeInsets.all(12),
            child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
              Text((record['location']??'Setor não informado').toString(),
                style:Theme.of(context).textTheme.titleMedium),
              Text((record['detail']??'').toString(),maxLines:7,
                overflow:TextOverflow.ellipsis),
              Text('Situação: ${record['status']??'Recebido'}'),
              if((record['feedback']??'').toString().isNotEmpty)
                Text('Orientação anterior: ${record['feedback']}'),
              const SizedBox(height:8),
              SizedBox(height:50,child:OutlinedButton.icon(
                onPressed:busy?null:()=>_viewPhotos(record),
                icon:const Icon(Icons.photo_outlined),
                label:const Text('Ver fotos')),
              const SizedBox(height:8),
              SizedBox(height:50,child:FilledButton.icon(
                onPressed:busy?null:()=>_reply(record),
                icon:const Icon(Icons.reply_outlined),
                label:const Text('Responder ao membro'))),
            ]))),
      ])),
  );
}

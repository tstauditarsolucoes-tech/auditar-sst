import 'dart:math';
import 'dart:typed_data';
import 'package:flutter/material.dart';

/// Moderador autorizado pelo servidor: ADM ou TST delegado no mandato.
/// A própria tela não confere permissões nem fecha NC, CAT ou ata.
class CipaMuralModerationPanel extends StatefulWidget{
  const CipaMuralModerationPanel({super.key,
    required this.onLoad,required this.onReview,required this.onCommentReview,
    required this.onReply,required this.onPhoto});
  final Future<List<Map<String,dynamic>>> Function() onLoad;
  final Future<void> Function(String postId,String visibility,
    String status,bool confirmed) onReview;
  final Future<void> Function(String id,bool publish) onCommentReview;
  final Future<void> Function(String postId,String text,String requestId)
    onReply;
  final Future<Uint8List?> Function(String postId) onPhoto;
  @override State<CipaMuralModerationPanel> createState()=>
    _CipaMuralModerationPanelState();
}
class _CipaMuralModerationPanelState extends State<CipaMuralModerationPanel>{
  List<Map<String,dynamic>> posts=const [];
  bool busy=false;
  String error='';
  final Map<String,String> replyIds={};
  @override void initState(){super.initState();_refresh();}
  Future<void> _refresh()async{
    if(busy)return;
    setState((){busy=true;error='';});
    try{
      final loaded=await widget.onLoad();
      if(mounted)setState(()=>posts=loaded);
    }catch(_){
      if(mounted)setState(()=>error='Não foi possível consultar '
        'a fila de revisão do mural.');
    }finally{if(mounted)setState(()=>busy=false);}
  }
  Future<void> _work(Future<void> Function() operation)async{
    if(busy)return;
    setState((){busy=true;error='';});
    try{
      await operation();
    }catch(_){
      if(mounted)setState(()=>error='A operação não foi confirmada. '
        'Atualize o mural antes de repetir.');
      return;
    }finally{if(mounted)setState(()=>busy=false);}
    await _refresh();
  }
  Future<void> _resolve(String id)async{
    final confirmed=await showDialog<bool>(context:context,
      builder:(dialog)=>AlertDialog(
        title:const Text('Correção realmente verificada?'),
        content:const Text('Use Resolvido apenas após conferência '
          'da medida pela pessoa responsável. '
          'Este registro não encerra uma não conformidade no SST.'),
        actions:[
          TextButton(onPressed:()=>Navigator.pop(dialog,false),
            child:const Text('Cancelar')),
          FilledButton(onPressed:()=>Navigator.pop(dialog,true),
            child:const Text('Confirmo a verificação')),
        ],
      ));
    if(confirmed==true&&mounted){
      await _work(()=>widget.onReview(id,'Aprovado','Resolvido',true));
    }
  }
  Future<void> _reply(String id)async{
    final text=await showDialog<String>(context:context,
      builder:(_)=>const _CipaMuralReplyDialog());
    if(text==null||!mounted)return;
    final key=id+'|'+text;
    final requestId=replyIds.putIfAbsent(key,(){
      final rng=Random.secure();
      return 'cipa-reply-'+List<int>.generate(24,(_)=>rng.nextInt(256))
        .map((b)=>b.toRadixString(16).padLeft(2,'0')).join();
    });
    await _work(()async{
      await widget.onReply(id,text,requestId);
      replyIds.remove(key);
    });
  }
  Future<void> _photo(String id)async{
    await showDialog<void>(context:context,builder:(dialog)=>AlertDialog(
      title:const Text('Foto para conferência'),
      content:FutureBuilder<Uint8List?>(
        future:widget.onPhoto(id),
        builder:(_,snapshot){
          if(snapshot.connectionState!=ConnectionState.done)
            return const SizedBox(height:100,
              child:Center(child:CircularProgressIndicator()));
          if(snapshot.hasError)return const Text('Foto indisponível.');
          if(snapshot.data==null)return const Text('Sem foto.');
          return Image.memory(snapshot.data!,width:380,fit:BoxFit.contain);
        }),
      actions:[TextButton(onPressed:()=>Navigator.pop(dialog),
        child:const Text('Fechar'))],
    ));
  }
  @override Widget build(BuildContext context)=>Card(
    child:ExpansionTile(
      leading:const Icon(Icons.fact_check_outlined),
      title:const Text('Moderação do Mural da CIPA',
        style:TextStyle(fontWeight:FontWeight.w700)),
      subtitle:const Text('Aprovar, orientar, ocultar e acompanhar'),
      children:[Padding(padding:const EdgeInsets.all(12),
        child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
          const Text('Somente relatos avaliados ficam visíveis '
            'no mural interno da empresa. Fotos e comentários '
            'não devem expor pessoas ou informações pessoais.'),
          Align(alignment:Alignment.centerRight,
            child:TextButton.icon(onPressed:busy?null:_refresh,
              icon:const Icon(Icons.refresh),
              label:const Text('Atualizar fila'))),
          if(busy)const LinearProgressIndicator(),
          if(error.isNotEmpty)Text(error,
            style:TextStyle(color:Theme.of(context).colorScheme.error)),
          if(posts.isEmpty&&!busy)const Text('Nenhum relato disponível.'),
          for(final post in posts)...[
            const Divider(),
            Text((post['place']??'Setor').toString(),
              style:const TextStyle(fontWeight:FontWeight.w700)),
            Text((post['detail']??'').toString()),
            Text('Publicação: '+(post['visibility']??'Pendente').toString()+
              ' • Situação: '+(post['status']??'Recebido').toString()),
            Wrap(spacing:6,runSpacing:6,children:[
              if(post['hasPhoto']==true)
                TextButton.icon(onPressed:busy?null:()=>_photo(
                  (post['id']??'').toString()),
                  icon:const Icon(Icons.photo_outlined),
                  label:const Text('Conferir foto')),
              OutlinedButton(onPressed:busy?null:()=>_work(
                  ()=>widget.onReview((post['id']??'').toString(),
                    'Aprovado','Em análise',false)),
                child:const Text('Aprovar')),
              OutlinedButton(onPressed:busy?null:()=>_work(
                  ()=>widget.onReview((post['id']??'').toString(),
                    'Não publicado','Em análise',false)),
                child:const Text('Não publicar')),
              OutlinedButton(onPressed:busy?null:()=>_work(
                  ()=>widget.onReview((post['id']??'').toString(),
                    'Aprovado','Orientação enviada',false)),
                child:const Text('Orientação enviada')),
              OutlinedButton(onPressed:busy?null:()=>_resolve(
                  (post['id']??'').toString()),
                child:const Text('Confirmar resolvido')),
              if(post['visibility']=='Aprovado')
                TextButton.icon(onPressed:busy?null:()=>_reply(
                    (post['id']??'').toString()),
                  icon:const Icon(Icons.reply_outlined),
                  label:const Text('Responder como SST')),
            ]),
            for(final raw in (post['comments'] is List?
                post['comments'] as List:const []).whereType<Map>())
              Card(child:Padding(padding:const EdgeInsets.all(9),
                child:Column(
                  crossAxisAlignment:CrossAxisAlignment.start,children:[
                    Text('Comentário • '+(raw['visibility']??'').toString(),
                      style:const TextStyle(fontWeight:FontWeight.w700)),
                    Text((raw['body']??'').toString()),
                    if(raw['visibility']=='Pendente')
                      Wrap(spacing:8,children:[
                        TextButton(onPressed:busy?null:()=>_work(
                            ()=>widget.onCommentReview(
                              (raw['id']??'').toString(),true)),
                          child:const Text('Aprovar comentário')),
                        TextButton(onPressed:busy?null:()=>_work(
                            ()=>widget.onCommentReview(
                              (raw['id']??'').toString(),false)),
                          child:const Text('Ocultar comentário')),
                      ]),
                  ]))),
          ],
        ])),
      ],
    ),
  );
}
class _CipaMuralReplyDialog extends StatefulWidget{
  const _CipaMuralReplyDialog();
  @override State<_CipaMuralReplyDialog> createState()=>
    _CipaMuralReplyDialogState();
}
class _CipaMuralReplyDialogState extends State<_CipaMuralReplyDialog>{
  final note=TextEditingController();
  @override void dispose(){note.dispose();super.dispose();}
  @override Widget build(BuildContext context)=>AlertDialog(
    title:const Text('Responder no mural'),
    content:SizedBox(width:380,child:Column(
      mainAxisSize:MainAxisSize.min,children:[
        const Text('A resposta aparecerá como Equipe SST. '
          'Não informe nomes de trabalhadores ou dados de saúde.'),
        const SizedBox(height:10),
        TextField(controller:note,maxLength:450,maxLines:4,
          onChanged:(_)=>setState((){}),
          decoration:const InputDecoration(
            border:OutlineInputBorder(),labelText:'Orientação pública')),
      ])),
    actions:[
      TextButton(onPressed:()=>Navigator.pop(context),
        child:const Text('Cancelar')),
      FilledButton(onPressed:note.text.trim().length<5?
        null:()=>Navigator.pop(context,note.text.trim()),
        child:const Text('Responder')),
    ],
  );
}

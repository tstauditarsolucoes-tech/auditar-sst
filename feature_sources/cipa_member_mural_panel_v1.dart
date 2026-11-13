import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../services/cipa_member_mural_model.dart';

/// Mural de ocorrência, não chat público. Tudo passa por moderação.
class CipaMuralPanel extends StatefulWidget{
  const CipaMuralPanel({super.key,this.offline=false,
    this.onLoad,this.onCreate,this.onComment,this.onPhoto,
    this.onSubmitAfter,this.onPhotoAfter,this.onSaveDraft});
  final bool offline;
  final Future<List<CipaMuralPost>> Function()? onLoad;
  final Future<void> Function(String place,String detail,Uint8List? photo)?
    onCreate;
  final Future<void> Function(String id,String text)? onComment;
  final Future<Uint8List?> Function(String id)? onPhoto;
  final Future<void> Function(String place,String detail,
    Uint8List? photo)? onSaveDraft;
  final Future<void> Function(String id,Uint8List jpeg)? onSubmitAfter;
  final Future<Uint8List?> Function(String id)? onPhotoAfter;
  @override State<CipaMuralPanel> createState()=>_CipaMuralPanelState();
}
class _CipaMuralPanelState extends State<CipaMuralPanel>{
  List<CipaMuralPost> posts=const [];
  String error='';
  bool loading=false,sending=false;
  @override void initState(){
    super.initState();
    if(!widget.offline&&widget.onLoad!=null)_refresh();
  }
  @override void didUpdateWidget(CipaMuralPanel old){
    super.didUpdateWidget(old);
    if(old.offline!=widget.offline ||
       (old.onLoad==null)!=(widget.onLoad==null)){
      posts=const [];
      error='';
      if(!widget.offline&&widget.onLoad!=null)_refresh();
    }
  }
  Future<void> _refresh()async{
    if(widget.onLoad==null||loading||widget.offline)return;
    setState((){loading=true;error='';});
    try{
      final result=await widget.onLoad!();
      if(mounted)setState(()=>posts=result);
    }catch(_){
      if(mounted)setState(()=>error='Não foi possível carregar o mural. '
        'Confira a internet e tente novamente.');
    }finally{if(mounted)setState(()=>loading=false);}
  }
  Future<void> _create()async{
    if(widget.onCreate==null||sending||widget.offline)return;
    final data=await showDialog<_MuralDraft>(context:context,
      builder:(_)=>const _MuralCreateDialog());
    if(data==null||!mounted)return;
    setState(()=>sending=true);
    try{
      await widget.onCreate!(data.place,data.detail,data.photo);
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content:Text('Ocorrência recebida para moderação. '
          'Ainda não está publicada aos colegas.')));
      await _refresh();
    }catch(_){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content:Text('Envio não confirmado. '
          'Atualize o mural antes de tentar novamente.')));
    }finally{if(mounted)setState(()=>sending=false);}
  }
  Future<void> _comment(CipaMuralPost post) async{
    if(widget.onComment==null||sending||widget.offline)return;
    final text=await showDialog<String>(context:context,builder:(_)=>
      const _MuralTextDialog());
    if(text==null||!mounted)return;
    setState(()=>sending=true);
    try{
      await widget.onComment!(post.id,text);
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content:Text('Comentário enviado para moderação.')));
      await _refresh();
    }catch(_){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content:Text('Comentário não confirmado. '
          'Atualize antes de reenviar.')));
    }finally{if(mounted)setState(()=>sending=false);}
  }
  Future<void> _photo(CipaMuralPost post) async{
    if(widget.onPhoto==null||widget.offline)return;
    await showDialog<void>(context:context,builder:(dialog)=>AlertDialog(
      title:const Text('Foto da ocorrência'),
      content:FutureBuilder<Uint8List?>(
        future:widget.onPhoto!(post.id),builder:(context,snapshot){
          if(snapshot.connectionState!=ConnectionState.done)
            return const SizedBox(width:250,height:100,
              child:Center(child:CircularProgressIndicator()));
          if(snapshot.hasError)return const Text(
            'Não foi possível abrir esta foto.');
          if(snapshot.data==null)return const Text('Sem foto.');
          return Image.memory(snapshot.data!,width:380,fit:BoxFit.contain);
        }),
      actions:[TextButton(onPressed:()=>Navigator.pop(dialog),
        child:const Text('Fechar'))],
    ));
  }


  Future<void> _saveLocally() async{
    if(widget.onSaveDraft==null||sending)return;
    final draft=await showDialog<_MuralDraft>(context:context,
      builder:(_)=>const _MuralCreateDialog());
    if(draft==null||!mounted)return;
    setState(()=>sending=true);
    try{
      await widget.onSaveDraft!(draft.place,draft.detail,draft.photo);
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content:Text('Rascunho do mural salvo '
          'de forma protegida neste celular. Ainda não foi enviado.')));
    }catch(_){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content:Text('Não foi possível salvar o '
          'rascunho protegido. Confira o espaço e tente novamente.')));
    }finally{if(mounted)setState(()=>sending=false);}
  }

  Future<void> _submitAfter(CipaMuralPost post)async{
    if(widget.onSubmitAfter==null||sending||widget.offline)return;
    final source=await showModalBottomSheet<ImageSource>(context:context,
      builder:(sheet)=>SafeArea(child:Column(mainAxisSize:MainAxisSize.min,
        children:[
          ListTile(leading:const Icon(Icons.camera_alt_outlined),
            title:const Text('Tirar foto depois'),
            onTap:()=>Navigator.pop(sheet,ImageSource.camera)),
          ListTile(leading:const Icon(Icons.photo_library_outlined),
            title:const Text('Escolher foto depois'),
            onTap:()=>Navigator.pop(sheet,ImageSource.gallery)),
        ])));
    if(source==null||!mounted)return;
    setState(()=>sending=true);
    try {
      final picked=await ImagePicker().pickImage(source:source,
        maxWidth:1200,maxHeight:1200,imageQuality:80,
        requestFullMetadata:false);
      if(picked==null)return;
      final cleaned=CipaMuralCodec.preparePhoto(await picked.readAsBytes());
      if(!mounted)return;
      final confirmed=await showDialog<bool>(context:context,
        builder:(dialog)=>AlertDialog(
          title:const Text('Enviar foto depois?'),
          content:const Text('A foto posterior será analisada antes '
            'de aparecer para os colegas. Não confirma correção '
            'nem encerra automaticamente a ocorrência.'),
          actions:[
            TextButton(onPressed:()=>Navigator.pop(dialog,false),
              child:const Text('Voltar')),
            FilledButton(onPressed:()=>Navigator.pop(dialog,true),
              child:const Text('Enviar para análise')),
          ]));
      if(confirmed!=true||!mounted)return;
      await widget.onSubmitAfter!(post.id,cleaned);
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content:Text('Foto depois enviada para revisão.')));
      await _refresh();
    }catch(_){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content:Text('Foto não confirmada. Atualize '
          'o mural antes de enviar outra.')));
    }finally{if(mounted)setState(()=>sending=false);}
  }
  Future<void> _showAfter(CipaMuralPost post)async{
    final fetch=widget.onPhotoAfter;
    if(fetch==null||widget.offline)return;
    await showDialog<void>(context:context,builder:(dialog)=>AlertDialog(
      title:const Text('Foto depois'),
      content:FutureBuilder<Uint8List?>(
        future:fetch(post.id),builder:(context,snapshot){
          if(snapshot.connectionState!=ConnectionState.done)
            return const SizedBox(height:100,
              child:Center(child:CircularProgressIndicator()));
          if(snapshot.hasError)return const Text('Foto indisponível.');
          if(snapshot.data==null)return const Text('Foto não enviada.');
          return Image.memory(snapshot.data!,width:380,fit:BoxFit.contain);
        }),
      actions:[TextButton(onPressed:()=>Navigator.pop(dialog),
        child:const Text('Fechar'))],
    ));
  }

  @override Widget build(BuildContext context)=>Card(child:Padding(
    padding:const EdgeInsets.all(14),
    child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
      Row(children:[
        const Icon(Icons.dynamic_feed_outlined,size:27),
        const SizedBox(width:8),
        Expanded(child:Text('Mural da CIPA',
          style:Theme.of(context).textTheme.titleLarge?.copyWith(
            fontWeight:FontWeight.w800))),
        if(!widget.offline)IconButton(
          onPressed:loading||sending?null:_refresh,
          tooltip:'Atualizar mural',icon:const Icon(Icons.refresh)),
      ]),
      const Text('Compartilhe situações do dia a dia e acompanhe '
        'respostas. Visível apenas aos integrantes autorizados do '
        'mesmo mandato, após análise do responsável.'),
      const SizedBox(height:8),
      const Text('Evite fotografar pessoas, documentos, dados de saúde '
        'ou entrar em áreas perigosas. Em risco grave ou urgente, '
        'avise imediatamente os responsáveis no local.',
        style:TextStyle(fontSize:12)),
      const SizedBox(height:12),
      if(widget.offline)...[
        const Text('As publicações dos colegas não ficam salvas offline. '
          'Você pode preencher um rascunho privado e enviar depois.',
          style:TextStyle(fontWeight:FontWeight.w700)),
        if(widget.onSaveDraft!=null)
          FilledButton.icon(onPressed:sending?null:_saveLocally,
            icon:const Icon(Icons.save_outlined),
            label:const Text('Salvar ocorrência no celular')),
      ]else...[
        if(widget.onSaveDraft!=null)
          OutlinedButton.icon(onPressed:sending?null:_saveLocally,
            icon:const Icon(Icons.save_outlined),
            label:const Text('Salvar rascunho no celular')),
        const SizedBox(height:8),
        SizedBox(height:54,child:FilledButton.icon(
          onPressed:sending||loading||widget.onCreate==null?null:_create,
          icon:const Icon(Icons.add_a_photo_outlined,size:24),
          label:const Text('Registrar ocorrência',
            style:TextStyle(fontSize:16,fontWeight:FontWeight.w700)))),
        if(loading)const LinearProgressIndicator(),
        if(error.isNotEmpty)Padding(
          padding:const EdgeInsets.all(8),child:Text(error)),
        if(posts.isEmpty&&!loading)const Padding(
          padding:EdgeInsets.all(12),
          child:Text('Nenhuma publicação disponível. '
            'Os relatos passam por análise antes de aparecer para todos.')),
        for(final post in posts)...[
          const Divider(),
          Row(children:[
            const CircleAvatar(child:Icon(Icons.shield_outlined)),
            const SizedBox(width:9),
            Expanded(child:Column(
              crossAxisAlignment:CrossAxisAlignment.start,children:[
                Text(post.isMine?'Minha ocorrência':'Integrante da CIPA',
                  style:const TextStyle(fontWeight:FontWeight.w700)),
                Text(post.place,style:const TextStyle(fontSize:13)),
              ])),
            if(post.visibility!='Aprovado')
              Chip(label:Text(post.visibility=='Pendente'?
                'Aguardando moderação':'Não publicado'))
            else Chip(label:Text(post.status)),
          ]),
          const SizedBox(height:7),
          Text(post.detail),
          if(post.createdAt.isNotEmpty)
            Text(post.createdAt,style:const TextStyle(fontSize:12)),
          if(post.hasPhoto)Align(alignment:Alignment.centerLeft,
            child:TextButton.icon(
              onPressed:widget.onPhoto==null?null:()=>_photo(post),
              icon:const Icon(Icons.photo_outlined),
              label:const Text('Ver foto antes'))),
          if(post.afterStatus.isNotEmpty&&post.isMine)
            Text('Foto depois: '+post.afterStatus,
              style:const TextStyle(fontSize:12)),
          if(post.hasAfter&&widget.onPhotoAfter!=null)
            Align(alignment:Alignment.centerLeft,child:TextButton.icon(
              onPressed:()=>_showAfter(post),
              icon:const Icon(Icons.image_outlined),
              label:const Text('Ver foto depois'))),
          if(post.isMine&&post.visibility=='Aprovado'&&
             (post.afterStatus.isEmpty||
              post.afterStatus=='Não publicado')&&
             widget.onSubmitAfter!=null)
            Align(alignment:Alignment.centerLeft,child:OutlinedButton.icon(
              onPressed:sending?null:()=>_submitAfter(post),
              icon:const Icon(Icons.add_a_photo_outlined),
              label:const Text('Adicionar foto depois'))),
          if(post.visibility=='Aprovado')...[
            for(final comment in post.comments)
              Padding(padding:const EdgeInsets.symmetric(vertical:4),
                child:Row(crossAxisAlignment:CrossAxisAlignment.start,
                  children:[
                    const Icon(Icons.forum_outlined,size:18),
                    const SizedBox(width:6),
                    Expanded(child:Text(comment.authorLabel+': '+
                      comment.body+(comment.visibility=='Aprovado'?'': 
                        ' (aguardando moderação)'))),
                  ])),
            Align(alignment:Alignment.centerRight,
              child:TextButton.icon(
                onPressed:sending||widget.onComment==null?
                  null:()=>_comment(post),
                icon:const Icon(Icons.mode_comment_outlined),
                label:const Text('Comentar'))),
          ],
        ],
        const Text('A postagem não confirma irregularidade ou correção. '
          'Somente os responsáveis validam e atualizam a situação.',
          style:TextStyle(fontSize:12)),
      ],
    ])));
}

class _MuralDraft{
  const _MuralDraft(this.place,this.detail,this.photo);
  final String place,detail;
  final Uint8List? photo;
}
class _MuralCreateDialog extends StatefulWidget{
  const _MuralCreateDialog();
  @override State<_MuralCreateDialog> createState()=>_MuralCreateDialogState();
}
class _MuralCreateDialogState extends State<_MuralCreateDialog>{
  final place=TextEditingController(),detail=TextEditingController();
  Uint8List? photo;
  String error='';
  bool processing=false;
  @override void dispose(){
    place.dispose();detail.dispose();super.dispose();
  }
  Future<void> choose(ImageSource source)async{
    if(processing)return;
    setState((){processing=true;error='';});
    try {
      final image=await ImagePicker().pickImage(source:source,
        maxWidth:1200,maxHeight:1200,imageQuality:80,
        requestFullMetadata:false);
      if(image==null)return;
      final reduced=CipaMuralCodec.preparePhoto(await image.readAsBytes());
      if(mounted)setState(()=>photo=reduced);
    }catch(_){
      if(mounted)setState(()=>error='Foto não aceita. Selecione '
        'uma imagem JPG ou PNG menor e tente novamente.');
    }finally{
      if(mounted)setState(()=>processing=false);
    }
  }
  @override Widget build(BuildContext context)=>AlertDialog(
    title:const Text('Registrar ocorrência'),
    content:SizedBox(width:420,child:SingleChildScrollView(
      child:Column(mainAxisSize:MainAxisSize.min,children:[
        const Text('O registro será analisado antes de aparecer '
          'para os outros integrantes. Não inclua nomes ou fotos de colegas.'),
        const SizedBox(height:12),
        TextField(controller:place,maxLength:120,
          onChanged:(_)=>setState((){}),
          decoration:const InputDecoration(
            labelText:'Local/setor',border:OutlineInputBorder())),
        const SizedBox(height:6),
        TextField(controller:detail,maxLength:900,maxLines:4,
          onChanged:(_)=>setState((){}),
          decoration:const InputDecoration(
            labelText:'O que você observou?',
            border:OutlineInputBorder())),
        Wrap(spacing:8,runSpacing:8,children:[
          OutlinedButton.icon(
            onPressed:processing?null:()=>choose(ImageSource.camera),
            icon:const Icon(Icons.camera_alt_outlined),
            label:const Text('Tirar foto')),
          OutlinedButton.icon(
            onPressed:processing?null:()=>choose(ImageSource.gallery),
            icon:const Icon(Icons.photo_library_outlined),
            label:const Text('Galeria')),
          if(photo!=null)TextButton(
            onPressed:processing?null:()=>setState(()=>photo=null),
            child:const Text('Retirar foto')),
        ]),
        if(photo!=null)Image.memory(photo!,height:140,fit:BoxFit.contain),
        if(processing)const LinearProgressIndicator(),
        if(error.isNotEmpty)Text(error),
        const Text('Não fotografe equipamentos se isso exigir '
          'se aproximar de partes móveis, altura ou áreas proibidas.',
          style:TextStyle(fontSize:12)),
      ]))),
    actions:[
      TextButton(onPressed:()=>Navigator.pop(context),
        child:const Text('Cancelar')),
      FilledButton(
        onPressed:processing||place.text.trim().length<2||
          detail.text.trim().length<12?null:()=>Navigator.pop(
            context,_MuralDraft(place.text.trim(),
              detail.text.trim(),photo)),
        child:const Text('Enviar para análise')),
    ],
  );
}
class _MuralTextDialog extends StatefulWidget{
  const _MuralTextDialog();
  @override State<_MuralTextDialog> createState()=>_MuralTextDialogState();
}
class _MuralTextDialogState extends State<_MuralTextDialog>{
  final controller=TextEditingController();
  @override void dispose(){controller.dispose();super.dispose();}
  @override Widget build(BuildContext context)=>AlertDialog(
    title:const Text('Comentar ocorrência'),
    content:SizedBox(width:420,child:Column(
      mainAxisSize:MainAxisSize.min,children:[
        const Text('O comentário ficará aguardando moderação. '
          'Não inclua nomes ou dados pessoais.'),
        const SizedBox(height:10),
        TextField(controller:controller,maxLength:450,maxLines:3,
          onChanged:(_)=>setState((){}),
          decoration:const InputDecoration(
            labelText:'Sua orientação ou pergunta',
            border:OutlineInputBorder())),
      ])),
    actions:[
      TextButton(onPressed:()=>Navigator.pop(context),
        child:const Text('Cancelar')),
      FilledButton(onPressed:controller.text.trim().length<5?
        null:()=>Navigator.pop(context,controller.text.trim()),
        child:const Text('Enviar comentário')),
    ],
  );
}

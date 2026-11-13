import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../services/cipa_member_identity.dart';
import '../services/cipa_member_avatar_image.dart';

/// Foto de perfil opcional e separada das fotos de inspeção.
/// Somente a conta validada pelo servidor pode carregá-la ou alterá-la.
/// Nunca usada como verificação de identidade ou presença.
class CipaMemberAccessHeader extends StatefulWidget {
  const CipaMemberAccessHeader({
    super.key,required this.profile,required this.companyName,
    required this.mandateLabel,this.onLoadAvatar,this.onSaveAvatar,
    this.onDeleteAvatar,
  });
  final CipaMemberAccessProfile profile;
  final String companyName,mandateLabel;
  final Future<Uint8List?> Function()? onLoadAvatar;
  final Future<void> Function(Uint8List jpeg)? onSaveAvatar;
  final Future<void> Function()? onDeleteAvatar;

  @override State<CipaMemberAccessHeader> createState()=>
    _CipaMemberAccessHeaderState();
}

class _CipaMemberAccessHeaderState extends State<CipaMemberAccessHeader> {
  Uint8List? _photo;
  bool _working=false;
  String _message='';
  int _requestGeneration=0;
  @override void initState(){
    super.initState();
    if(widget.onLoadAvatar!=null)_load();
  }
  @override void didUpdateWidget(CipaMemberAccessHeader old){
    super.didUpdateWidget(old);
    if(old.profile.userId!=widget.profile.userId||
       old.profile.companyId!=widget.profile.companyId||
       old.profile.mandateId!=widget.profile.mandateId||
       old.profile.memberId!=widget.profile.memberId||
       (old.onLoadAvatar!=null)!=(widget.onLoadAvatar!=null)){
      ++_requestGeneration;
      _photo=null;
      _message='';
      if(widget.onLoadAvatar!=null)_load();
    }
  }
  Future<void> _load() async {
    final load=widget.onLoadAvatar;
    if(load==null)return;
    final generation=++_requestGeneration;
    try{
      final result=await load();
      if(mounted&&generation==_requestGeneration)
        setState(()=>_photo=result);
    }catch(_){
      if(mounted&&generation==_requestGeneration)
        setState(()=>_message='A foto não pôde ser carregada.');
    }
  }

  Future<void> _choose(ImageSource source) async {
    if(_working||widget.onSaveAvatar==null)return;
    setState((){_working=true;_message='';});
    try{
      final image=await ImagePicker().pickImage(source:source,
        maxWidth:900,maxHeight:900,imageQuality:80,
        requestFullMetadata:false);
      if(image==null)return;
      final bytes=await image.readAsBytes();
      final compressed=CipaAvatarImage.prepare(bytes);
      await widget.onSaveAvatar!(compressed);
      if(mounted)setState((){
        _photo=compressed;
        _message='Foto do perfil atualizada.';
      });
    }catch(_){
      if(mounted)setState(()=>_message='Não foi possível salvar a foto. '
        'Confira a conexão e tente novamente.');
    }finally{
      if(mounted)setState(()=>_working=false);
    }
  }
  Future<void> _remove()async {
    if(_working||widget.onDeleteAvatar==null)return;
    final ok=await showDialog<bool>(context:context,
      builder:(dialog)=>AlertDialog(
        title:const Text('Remover foto do perfil?'),
        content:const Text('Sua foto será removida do perfil da CIPA. '
          'A foto não é necessária para usar o aplicativo.'),
        actions:[
          TextButton(onPressed:()=>Navigator.pop(dialog,false),
            child:const Text('Cancelar')),
          FilledButton(onPressed:()=>Navigator.pop(dialog,true),
            child:const Text('Remover foto')),
        ],
      ));
    if(ok!=true||!mounted)return;
    setState((){_working=true;_message='';});
    try{
      await widget.onDeleteAvatar!();
      if(mounted)setState((){
        _photo=null;
        _message='Foto removida.';
      });
    }catch(_){
      if(mounted)setState(()=>_message='Não foi possível remover a foto.');
    }finally{
      if(mounted)setState(()=>_working=false);
    }
  }

  @override Widget build(BuildContext context) => Card(
    child:Padding(padding:const EdgeInsets.all(16),
      child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
        const Row(children:[
          Icon(Icons.badge_outlined),SizedBox(width:8),
          Expanded(child:Text('Meu acesso à CIPA',
            style:TextStyle(fontWeight:FontWeight.w800))),
        ]),
        const SizedBox(height:12),
        Row(crossAxisAlignment:CrossAxisAlignment.center,children:[
          Semantics(label:_photo==null?'Perfil sem foto':
            'Foto opcional do perfil',child:CircleAvatar(
            radius:38,
            backgroundImage:_photo==null?null:MemoryImage(_photo!),
            child:_photo==null?const Icon(Icons.person_outline,size:42):null,
          )),
          const SizedBox(width:12),
          Expanded(child:Column(
            crossAxisAlignment:CrossAxisAlignment.start,children:[
              Text(widget.profile.displayName,
                key:const ValueKey('cipa-member-identity-name-role'),
                style:Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight:FontWeight.w900)),
              if(widget.profile.detailLine.isNotEmpty)...[
                const SizedBox(height:4),
                Text(widget.profile.detailLine,
                  key:const ValueKey('cipa-member-job-representation')),
              ],
            ],
          )),
        ]),
        const SizedBox(height:9),
        Text(widget.companyName+' • Mandato: '+widget.mandateLabel,
          style:Theme.of(context).textTheme.bodySmall),
        if(widget.onSaveAvatar!=null)...[
          const SizedBox(height:10),
          const Text('Foto de perfil (opcional). Não é reconhecimento '
            'facial nem comprova presença nas reuniões.',
            style:TextStyle(fontSize:12)),
          const SizedBox(height:7),
          Wrap(spacing:8,runSpacing:8,children:[
            OutlinedButton.icon(
              onPressed:_working?null:()=>_choose(ImageSource.camera),
              icon:const Icon(Icons.camera_alt_outlined),
              label:const Text('Tirar foto')),
            OutlinedButton.icon(
              onPressed:_working?null:()=>_choose(ImageSource.gallery),
              icon:const Icon(Icons.photo_library_outlined),
              label:const Text('Escolher foto')),
            if(_photo!=null&&widget.onDeleteAvatar!=null)
              TextButton.icon(onPressed:_working?null:_remove,
                icon:const Icon(Icons.delete_outline),
                label:const Text('Remover foto')),
          ]),
        ],
        if(_working)const LinearProgressIndicator(),
        if(_message.isNotEmpty)Padding(
          padding:const EdgeInsets.only(top:6),
          child:Text(_message,style:const TextStyle(fontSize:13))),
        const SizedBox(height:8),
        const Text('Ações de membros exigem autorização individual e '
          'validação no servidor. Este cabeçalho não concede acesso.',
          style:TextStyle(fontSize:11.5)),
      ]),
    ));
}

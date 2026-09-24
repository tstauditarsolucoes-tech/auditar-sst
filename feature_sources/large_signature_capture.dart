import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:signature/signature.dart';
import '../brand.dart';

/// Shared capture surface; the calling module still owns and saves its controller.
class LargeSignatureCapturePage extends StatefulWidget {
  final SignatureController controller;
  final String title, signerName, contextLabel, progressLabel;
  const LargeSignatureCapturePage({
    super.key, required this.controller, required this.title,
    required this.signerName, this.contextLabel='', this.progressLabel='',
  });

  static Future<bool> open(BuildContext context, {
    required SignatureController controller, required String title,
    required String signerName, String contextLabel='', String progressLabel='',
  }) async {
    FocusManager.instance.primaryFocus?.unfocus();
    final rotate=Platform.isAndroid;
    if (rotate) {
      await SystemChrome.setPreferredOrientations(const [
        DeviceOrientation.landscapeLeft, DeviceOrientation.landscapeRight,
      ]);
    }
    try {
      if (!context.mounted) return false;
      return await Navigator.of(context).push<bool>(MaterialPageRoute(
        fullscreenDialog:true, builder:(_)=>LargeSignatureCapturePage(
          controller:controller, title:title, signerName:signerName,
          contextLabel:contextLabel, progressLabel:progressLabel,
        ),
      )) ?? false;
    } finally {
      if (rotate) {
        await SystemChrome.setPreferredOrientations(const <DeviceOrientation>[]);
      }
    }
  }

  @override
  State<LargeSignatureCapturePage> createState()=>_LargeSignatureCaptureState();
}

class _LargeSignatureCaptureState extends State<LargeSignatureCapturePage> {
  bool canRedo=false;
  @override void initState() {
    super.initState();
    widget.controller.addListener(_onChange);
  }
  void _onChange(){ if(mounted) setState((){}); }
  @override void dispose() {
    widget.controller.removeListener(_onChange);
    super.dispose();
  }
  void _undo() {
    if(widget.controller.isEmpty)return;
    widget.controller.undo();
    setState(()=>canRedo=true);
  }
  void _redo() {
    if(!canRedo)return;
    widget.controller.redo();
    setState(()=>canRedo=false);
  }
  Future<void> _clear() async {
    if(widget.controller.isEmpty)return;
    final ok=await showDialog<bool>(context:context,builder:(dialog)=>AlertDialog(
      title:const Text('Limpar assinatura?'),
      content:const Text('Os traços desta tentativa serão apagados. '
          'Uma assinatura já salva anteriormente não será alterada.'),
      actions:[
        TextButton(onPressed:()=>Navigator.pop(dialog,false),
          child:const Text('Manter')),
        FilledButton(onPressed:()=>Navigator.pop(dialog,true),
          child:const Text('Limpar traços')),
      ],
    ));
    if(ok==true && mounted) {
      widget.controller.clear();
      setState(()=>canRedo=false);
    }
  }
  @override Widget build(BuildContext context) {
    final short=MediaQuery.sizeOf(context).height<430;
    final name=widget.signerName.trim();
    return Scaffold(backgroundColor:const Color(0xFFF2F5F8),body:SafeArea(
      child:Padding(padding:const EdgeInsets.all(8),child:Column(children:[
        Row(children:[
          IconButton(tooltip:'Voltar sem confirmar',
            onPressed:()=>Navigator.pop(context,false),
            icon:const Icon(Icons.arrow_back_rounded,size:26)),
          Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,
            children:[
              const Text('ASSINANDO AGORA',style:TextStyle(
                fontSize:11,fontWeight:FontWeight.w900,
                color:AuditarBrand.greenDark)),
              Text(name.isEmpty?widget.title:name.toUpperCase(),
                maxLines:short?1:2,overflow:TextOverflow.ellipsis,
                style:TextStyle(fontSize:short?19:23,
                  fontWeight:FontWeight.w900,color:AuditarBrand.navyDark)),
              if(!short && widget.contextLabel.isNotEmpty)
                Text(widget.contextLabel,maxLines:1,
                  overflow:TextOverflow.ellipsis),
            ])),
          if(widget.progressLabel.isNotEmpty)
            Padding(padding:const EdgeInsets.only(left:6),
              child:Text(widget.progressLabel,style:const TextStyle(
                fontWeight:FontWeight.w800,color:AuditarBrand.navy))),
        ]),
        const SizedBox(height:6),
        Expanded(child:Container(
          key:const ValueKey('auditar_large_signature_canvas'),
          decoration:BoxDecoration(color:Colors.white,
            border:Border.all(color:const Color(0xFF93A2B5),width:1.5),
            borderRadius:BorderRadius.circular(14)),
          clipBehavior:Clip.antiAlias,
          child:LayoutBuilder(builder:(context,c)=>Signature(
            controller:widget.controller,width:c.maxWidth,height:c.maxHeight,
            backgroundColor:Colors.white)),
        )),
        const SizedBox(height:5),
        Text(widget.controller.isEmpty
          ?'Use toda a área branca para assinar com o dedo.'
          :'Confira a assinatura e toque em Concluir.',
          style:const TextStyle(fontSize:11,color:Colors.black54)),
        const SizedBox(height:5),
        Row(children:[
          OutlinedButton.icon(onPressed:widget.controller.isEmpty?null:_undo,
            icon:const Icon(Icons.undo_rounded,size:18),
            label:const Text('Desfazer')),
          const SizedBox(width:5),
          OutlinedButton.icon(onPressed:canRedo?_redo:null,
            icon:const Icon(Icons.redo_rounded,size:18),
            label:const Text('Refazer')),
          const SizedBox(width:5),
          OutlinedButton(onPressed:widget.controller.isEmpty?null:_clear,
            child:const Text('Limpar')),
          const SizedBox(width:5),
          Expanded(child:FilledButton.icon(
            onPressed:widget.controller.isEmpty?null:(){
              HapticFeedback.selectionClick();
              Navigator.pop(context,true);
            },
            icon:const Icon(Icons.check_rounded),
            label:const Text('Concluir'),
            style:FilledButton.styleFrom(minimumSize:const Size(0,54)),
          )),
        ]),
      ])),
    )));
  }
}

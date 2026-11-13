import 'package:flutter/material.dart';

/// Minutas recebidas para análise. Não assina nem publica atas.
class CipaMinutesReviewPanel extends StatefulWidget{
  const CipaMinutesReviewPanel({super.key,required this.onLoad,
    required this.onReview});
  final Future<List<Map<String,dynamic>>> Function() onLoad;
  final Future<void> Function(String minuteId,String status,String note)
    onReview;
  @override State<CipaMinutesReviewPanel> createState()=>
    _CipaMinutesReviewPanelState();
}
class _CipaMinutesReviewPanelState extends State<CipaMinutesReviewPanel>{
  List<Map<String,dynamic>> minutes=const [];
  bool busy=false;
  String error='';
  @override void initState(){super.initState();_load();}
  Future<void> _load()async{
    if(busy)return;
    setState((){busy=true;error='';});
    try{
      final found=await widget.onLoad();
      if(mounted)setState(()=>minutes=found);
    }catch(_){
      if(mounted)setState(()=>error='Não foi possível consultar minutas.');
    }finally{if(mounted)setState(()=>busy=false);}
  }
  Future<void> _review(Map<String,dynamic> item) async{
    if(busy)return;
    final result=await showDialog<(String,String)>(
      context:context,builder:(_)=>const _CipaMinutesReviewDialog());
    if(result==null||!mounted)return;
    setState((){busy=true;error='';});
    try {
      await widget.onReview((item['id']??'').toString(),
        result.$1,result.$2);
    }catch(_){
      if(mounted)setState(()=>error='Não foi possível confirmar revisão.');
      return;
    }finally{if(mounted)setState(()=>busy=false);}
    await _load();
  }
  @override Widget build(BuildContext context)=>Card(
    child:ExpansionTile(
      leading:const Icon(Icons.description_outlined),
      title:const Text('Minutas da CIPA para revisão',
        style:TextStyle(fontWeight:FontWeight.w700)),
      subtitle:const Text('Revisar o conteúdo antes da formalização'),
      children:[Padding(padding:const EdgeInsets.all(12),
        child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
          const Text('Documentos enviados pelos integrantes são '
            'minutas educativas: não representam reunião realizada, '
            'lista de presença ou ata assinada.'),
          OutlinedButton.icon(onPressed:busy?null:_load,
            icon:const Icon(Icons.refresh),label:const Text('Atualizar minutas')),
          if(busy)const LinearProgressIndicator(),
          if(error.isNotEmpty)Text(error),
          if(minutes.isEmpty&&!busy)
            const Text('Nenhuma minuta aguardando nesta consulta.'),
          for(final item in minutes)...[
            const Divider(),
            Text('Reunião: '+(item['meetingId']??'').toString(),
              style:const TextStyle(fontWeight:FontWeight.w800)),
            Text('Situação: '+(item['status']??'Recebida').toString()),
            if((item['reviewNote']??'').toString().trim().isNotEmpty)
              Text('Devolutiva: '+(item['reviewNote']??'').toString()),
            OutlinedButton.icon(
              onPressed:()=>showDialog<void>(context:context,
                builder:(dialog)=>AlertDialog(
                  title:const Text('Conteúdo da minuta'),
                  content:SizedBox(width:450,height:380,
                    child:SingleChildScrollView(child:SelectableText(
                      (item['content']??'').toString()))),
                  actions:[FilledButton(onPressed:()=>Navigator.pop(dialog),
                    child:const Text('Fechar'))])),
              icon:const Icon(Icons.visibility_outlined),
              label:const Text('Ler minuta')),
            FilledButton.icon(onPressed:busy?null:()=>_review(item),
              icon:const Icon(Icons.rate_review_outlined),
              label:const Text('Revisar minuta')),
          ],
        ])),
      ],
    ));
}
class _CipaMinutesReviewDialog extends StatefulWidget{
  const _CipaMinutesReviewDialog();
  @override State<_CipaMinutesReviewDialog> createState()=>
    _CipaMinutesReviewDialogState();
}
class _CipaMinutesReviewDialogState
    extends State<_CipaMinutesReviewDialog>{
  String status='Em revisão';
  final note=TextEditingController();
  @override void dispose(){note.dispose();super.dispose();}
  @override Widget build(BuildContext context)=>AlertDialog(
    title:const Text('Registrar revisão da minuta'),
    content:SingleChildScrollView(child:Column(
      mainAxisSize:MainAxisSize.min,children:[
        const Text('Escolha o resultado da revisão. Mesmo pronta '
          'para formalização, a minuta não é uma ata assinada.'),
        const SizedBox(height:12),
        DropdownButtonFormField<String>(
          initialValue:status,
          decoration:const InputDecoration(labelText:'Resultado'),
          items:const [
            DropdownMenuItem(value:'Em revisão',child:Text('Em revisão')),
            DropdownMenuItem(value:'Devolvida',child:Text('Devolvida')),
            DropdownMenuItem(value:'Pronta para formalização',
              child:Text('Pronta para formalização')),
          ],onChanged:(v){if(v!=null)setState(()=>status=v);}),
        const SizedBox(height:12),
        TextField(controller:note,maxLength:600,maxLines:3,
          onChanged:(_)=>setState((){}),
          decoration:const InputDecoration(
            labelText:'Orientação ao integrante',
            border:OutlineInputBorder())),
      ])),
    actions:[
      TextButton(onPressed:()=>Navigator.pop(context),
        child:const Text('Cancelar')),
      FilledButton(onPressed:status=='Devolvida'&&
        note.text.trim().length<8?null:()=>Navigator.pop(
          context,(status,note.text.trim())),
        child:const Text('Salvar revisão')),
    ],
  );
}

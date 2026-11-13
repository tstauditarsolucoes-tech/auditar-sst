import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image/image.dart' as image_codec;
import 'package:image_picker/image_picker.dart';

/// Roteiro educativo de observação visual, sem avaliação normativa automática.
/// O registro somente é enviado por um callback já autorizado pela sessão CIPA.
class CipaGuidedInspection {
  static const questions = <String, List<String>>{
    'Organização e circulação': <String>[
      'Existem obstáculos nas passagens de circulação?',
      'Há piso escorregadio ou abertura sem proteção visível?',
      'Há saída ou rota de emergência obstruída?',
    ],
    'Máquinas e equipamentos': <String>[
      'Há parte móvel de máquina acessível sem proteção aparente?',
      'Há cabos, tomadas ou painéis com dano visível?',
      'Há pessoas perto de máquinas sem separação aparente?',
    ],
    'Incêndio e emergência': <String>[
      'Há extintor com acesso obstruído?',
      'Há placa de emergência ilegível ou danificada?',
      'Há saída de emergência sem acesso livre?',
    ],
    'Ambiente e proteção': <String>[
      'Há atividade observada com proteção pessoal aparentemente ausente?',
      'Há poeira, fumaça ou calor incomum percebido de local seguro?',
      'Há materiais empilhados com risco aparente de queda?',
    ],
  };

  // Cada roteiro contém apenas três perguntas visuais e nenhuma medição.
  // Os textos descrevem situações possíveis, não irregularidades confirmadas.
  static const sectorQuestions = <String,List<String>>{
    'Panificação': <String>[
      'Há máquina com proteção aparentemente ausente?',
      'Há piso escorregadio ou passagem obstruída?',
      'Há extintor com acesso bloqueado?',
    ],
    'Cerâmica': <String>[
      'Há correia ou parte móvel acessível sem proteção visível?',
      'Há passagem perto do forno sem barreira ou aviso visível?',
      'Há canaleta ou abertura sem proteção aparente?',
    ],
    'Construção civil': <String>[
      'Há abertura ou borda elevada sem proteção visível?',
      'Há andaime com peça solta ou base aparentemente instável?',
      'Há circulação com materiais ou entulho obstruindo o caminho?',
    ],
    'Laticínios': <String>[
      'Há máquina com proteção visivelmente ausente?',
      'Há piso molhado na passagem?',
      'Há painel ou cabo elétrico com dano visível?',
    ],
    'Logística e depósitos': <String>[
      'Há materiais empilhados com risco aparente de queda?',
      'Há pedestres circulando perto de veículos sem separação?',
      'Há paletes danificados ou passagens obstruídas?',
    ],
    'Limpeza urbana': <String>[
      'Há operação de veículo sem sinalização aparente?',
      'Há área de trabalho sem isolamento visível de pedestres?',
      'Há ferramentas com proteção aparentemente ausente?',
    ],
    'Comércio e escritórios': <String>[
      'Há saída de emergência bloqueada?',
      'Há cabo elétrico danificado ou tomada com dano visível?',
      'Há piso ou escada com risco aparente de escorregão?',
    ],
  };

  static List<String> questionsFor(String category) =>
    questions[category] ?? sectorQuestions[category] ??
      (throw ArgumentError('Roteiro desconhecido'));

  static const help = <String,String>{
    'Organização e circulação':
      'Observe corredores, pisos e saídas sem entrar em áreas restritas.',
    'Máquinas e equipamentos':
      'Olhe de longe: nunca toque na máquina nem remova proteção.',
    'Incêndio e emergência':
      'Observe o acesso e a identificação, sem manusear equipamentos.',
    'Ambiente e proteção':
      'Não se exponha a poeira, calor, ruído ou áreas de movimentação.',
    'Panificação':
      'Veja máquinas e piso apenas de onde já é permitido circular.',
    'Cerâmica':
      'Não se aproxime de partes móveis nem entre sob ou dentro do forno.',
    'Construção civil':
      'Não suba em andaimes ou escadas para conferir uma situação.',
    'Laticínios':
      'Não abra painéis nem teste sensores ou proteções de máquinas.',
    'Logística e depósitos':
      'Mantenha distância de empilhadeiras e cargas elevadas.',
    'Limpeza urbana':
      'Não se aproxime de veículos em manobra ou áreas isoladas.',
    'Comércio e escritórios':
      'Não toque em instalações elétricas e mantenha rotas livres.',
  };

  static String summary({
    required String place,
    required String category,
    required List<String> answers,
    required String observation,
  }) {
    final questionsForCategory=questionsFor(category);
    if(answers.length!=questionsForCategory.length) {
      throw ArgumentError('Roteiro incompleto');
    }
    final safePlace=place.trim();
    if(safePlace.length<2 || safePlace.length>120) {
      throw ArgumentError('Local inválido');
    }
    const allowed=<String>['Sim','Não','Não sei/não verifiquei'];
    if(answers.any((a)=>!allowed.contains(a))) {
      throw ArgumentError('Resposta inválida');
    }
    if(observation.trim().length>250) {
      throw ArgumentError('Observação muito longa');
    }
    final reported=answers.where((answer)=>answer=='Sim').length;
    final unknown=answers.where((answer)=>
      answer=='Não sei/não verifiquei').length;
    final lines=<String>[
      'VISTORIA ORIENTADA DA CIPA — OBSERVAÇÃO VISUAL',
      'Setor/local: $safePlace',
      'Tema: $category',
      'Situações informadas para conferência: $reported. '
        'Respostas não verificadas: $unknown.',
      for(var i=0;i<answers.length;i++)
        '${questionsForCategory[i]} Resposta: ${answers[i]}.',
      if(observation.trim().isNotEmpty)
        'Observação do membro: ${observation.trim()}',
      'Registro encaminhado para conferência técnica; respostas não '
        'comprovam conformidade, não constituem laudo e não encerram ações.',
    ];
    final result=lines.join('\n');
    if(result.length>1200) {
      throw ArgumentError('Registro ultrapassa limite do servidor');
    }
    return result;
  }
}


class CipaGuidedInspectionDialog extends StatefulWidget {
  const CipaGuidedInspectionDialog({
    super.key,required this.onSend,this.onSendWithPhotos,
    this.initialCategory,this.initialPlace,
    this.memberName='',this.companyName='',
    this.memberRole='',this.mandateLabel='',
  });
  final Future<void> Function(String place,String note) onSend;
  final Future<void> Function(String place,String note,List<Uint8List> photos)?
    onSendWithPhotos;
  final String? initialCategory,initialPlace;
  final String memberName,companyName,memberRole,mandateLabel;

  @override
  State<CipaGuidedInspectionDialog> createState()=>
    _CipaGuidedInspectionDialogState();
}

class _CipaGuidedInspectionDialogState
    extends State<CipaGuidedInspectionDialog> {
  final place=TextEditingController();
  final observation=TextEditingController();
  String category=CipaGuidedInspection.questions.keys.first;
  List<String?> answers=<String?>[];
  int page=0; // 0 identificação, 1..3 perguntas, 4 conferência
  bool sending=false;
  String error='';
  final List<Uint8List> photos=[];
  bool takingPhoto=false;

  @override void initState() {
    super.initState();
    final proposed=widget.initialCategory;
    if(proposed!=null &&
       (CipaGuidedInspection.questions.containsKey(proposed) ||
        CipaGuidedInspection.sectorQuestions.containsKey(proposed))) {
      category=proposed;
    }
    final initial=widget.initialPlace?.trim()??'';
    if(initial.length>=2&&initial.length<=120)place.text=initial;
    _resetAnswers();
  }
  void _resetAnswers() {
    answers=List<String?>.filled(
      CipaGuidedInspection.questionsFor(category).length,null);
  }
  @override void dispose() {
    place.dispose();
    observation.dispose();
    super.dispose();
  }

  void _next() {
    if(sending)return;
    if(page==0&&place.text.trim().length>=2) {
      setState(()=>page=1);
    } else if(page>=1&&page<=3&&answers[page-1]!=null) {
      setState(()=>page=page+1);
    }
  }

  Future<void> _takePhoto() async {
    if(sending||takingPhoto||photos.length>=2||
       widget.onSendWithPhotos==null)return;
    setState(() {takingPhoto=true;error='';});
    XFile? capture;
    try {
      capture=await ImagePicker().pickImage(source:ImageSource.camera,
        maxWidth:1280,maxHeight:1280,imageQuality:75,
        requestFullMetadata:false);
      if(capture==null)return;
      final decoded=image_codec.decodeImage(await capture.readAsBytes());
      if(decoded==null)throw StateError('Imagem não reconhecida');
      // Recriar do zero sem metadados EXIF/GPS da câmera.
      final clean=image_codec.Image(
        width:decoded.width,height:decoded.height);
      image_codec.compositeImage(clean,decoded);
      var output=Uint8List.fromList(
        image_codec.encodeJpg(clean,quality:70));
      if(output.length>700000) {
        final smaller=image_codec.copyResize(clean,width:960);
        output=Uint8List.fromList(
          image_codec.encodeJpg(smaller,quality:60));
      }
      if(output.length>700000)throw StateError('Fotografia muito grande');
      if(mounted)setState(()=>photos.add(output));
    }catch (_) {
      if(mounted)setState(()=>error='Não foi possível preparar a foto. '
        'Tente novamente em um local seguro.');
    }finally{
      // O arquivo do seletor é temporário e não deve virar arquivo do usuário.
      if(capture!=null) {
        try {await File(capture.path).delete();}catch(_){}
      }
      if(mounted)setState(()=>takingPhoto=false);
    }
  }

  Future<void> _send() async {
    if(sending||page!=4||place.text.trim().length<2||
        answers.any((answer)=>answer==null))return;
    setState(() {sending=true;error='';});
    try {
      final note=CipaGuidedInspection.summary(
        place:place.text,category:category,
        answers:answers.cast<String>(),observation:observation.text);
      if(photos.isNotEmpty){
        final upload=widget.onSendWithPhotos;
        if(upload==null)throw StateError('Envio de fotos não habilitado');
        await upload(place.text.trim(),note,List<Uint8List>.from(photos));
      }else{
        await widget.onSend(place.text.trim(),note);
      }
      if(mounted)Navigator.of(context).pop(true);
    } catch (_) {
      if(mounted)setState(()=>error='Envio não confirmado. '
        'Confira a conexão e consulte o histórico antes de tentar novamente.');
    } finally {
      if(mounted)setState(()=>sending=false);
    }
  }

  @override Widget build(BuildContext context) {
    final questions=CipaGuidedInspection.questionsFor(category);
    final step=page;
    final answered=answers.where((a)=>a!=null).length;
    return AlertDialog(
      title:const Text('Minha Vistoria CIPA'),
      content:SizedBox(width:460,child:SingleChildScrollView(
        child:Column(
          mainAxisSize:MainAxisSize.min,
          crossAxisAlignment:CrossAxisAlignment.stretch,
          children:[
            if(step==0)...[
              const Text('Primeiro, confira onde vai observar. '
                'Seu cadastro já vem da sessão individual.'),
              const SizedBox(height:10),
              if(widget.memberName.isNotEmpty)
                Text('Integrante: ${widget.memberName}',
                  style:const TextStyle(fontWeight:FontWeight.w600)),
              if(widget.memberRole.isNotEmpty)
                Text('Função na CIPA: ${widget.memberRole}'),
              if(widget.companyName.isNotEmpty)
                Text('Empresa: ${widget.companyName}'),
              if(widget.mandateLabel.isNotEmpty)
                Text('Mandato: ${widget.mandateLabel}'),
              const SizedBox(height:12),
              TextField(controller:place,maxLength:120,
                onChanged:(_)=>setState((){}),
                decoration:const InputDecoration(
                  labelText:'Setor ou local observado',
                  hintText:'Ex.: Produção — corredor',
                  border:OutlineInputBorder())),
              DropdownButtonFormField<String>(
                isExpanded:true,
                value:category,
                decoration:const InputDecoration(
                  labelText:'Escolha o setor ou tema',
                  border:OutlineInputBorder()),
                items:[
                  for(final name in <String>[
                    ...CipaGuidedInspection.questions.keys,
                    ...CipaGuidedInspection.sectorQuestions.keys,
                  ]) DropdownMenuItem(
                    value:name,
                    child:Text(name,overflow:TextOverflow.ellipsis)),
                ],
                onChanged:sending?null:(next) {
                  if(next==null)return;
                  setState((){category=next;_resetAnswers();});
                }),
              const SizedBox(height:12),
              const Text('Serão apenas 3 perguntas, uma por vez. '
                'Observe somente de um local seguro. Não se aproxime '
                'de máquinas, fornos, instalações elétricas ou bordas.'),
            ],
            if(step>=1&&step<=3)...[
              Text('Pergunta $step de 3',
                style:const TextStyle(fontWeight:FontWeight.w700)),
              const SizedBox(height:10),
              LinearProgressIndicator(value:answered/3),
              const SizedBox(height:20),
              Text(questions[step-1],style:const TextStyle(
                fontWeight:FontWeight.w700,fontSize:20)),
              const SizedBox(height:14),
              for(final answer in const [
                'Sim','Não','Não sei/não verifiquei',
              ]) Card(
                margin:const EdgeInsets.only(bottom:8),
                child:RadioListTile<String>(
                  key:ValueKey('answer-${step-1}-$answer'),
                  contentPadding:const EdgeInsets.symmetric(
                    horizontal:12,vertical:7),
                  title:Text(answer,style:const TextStyle(fontSize:16)),
                  value:answer,groupValue:answers[step-1],
                  onChanged:sending?null:(next)=>
                    setState(()=>answers[step-1]=next),
                )),
              const SizedBox(height:12),
              ExpansionTile(
                tilePadding:EdgeInsets.zero,
                title:const Text('O que observar com segurança?'),
                children:[
                  Padding(padding:const EdgeInsets.all(12),
                    child:Text(CipaGuidedInspection.help[category] ??
                      'Observe apenas de um lugar seguro.')),
                ],
              ),
              if(answers[step-1]=='Sim')
                const Text('Se perceber perigo imediato, afaste-se '
                  'e avise o responsável. Não tente corrigir.'),
            ],
            if(step==4)...[
              const Text('Confira suas respostas',
                style:TextStyle(fontWeight:FontWeight.w700,fontSize:18)),
              const SizedBox(height:8),
              Text('Local: ${place.text.trim()}'),
              Text('Tema: $category'),
              const Divider(),
              for(var i=0;i<questions.length;i++)...[
                Text(questions[i],
                  style:const TextStyle(fontWeight:FontWeight.w600)),
                Text('Resposta: ${answers[i]}'),
                const SizedBox(height:8),
              ],
              if(widget.onSendWithPhotos!=null)...[
                const SizedBox(height:12),
                SizedBox(height:54,child:OutlinedButton.icon(
                  onPressed:takingPhoto||sending||photos.length>=2?
                    null:_takePhoto,
                  icon:const Icon(Icons.camera_alt_outlined,size:26),
                  label:Text(takingPhoto?'Abrindo câmera...':
                    photos.length>=2?'2 fotos adicionadas':'Tirar foto'),
                )),
                Text('Fotos: ${photos.length} de 2. '
                  'Apenas fotos da situação, sem identificar pessoas.'),
                if(photos.isNotEmpty)Wrap(spacing:8,runSpacing:8,
                  children:[
                    for(var i=0;i<photos.length;i++)
                      Column(mainAxisSize:MainAxisSize.min,children:[
                        Image.memory(photos[i],width:110,height:88,
                          fit:BoxFit.cover),
                        TextButton(onPressed:sending?null:()=>
                          setState(()=>photos.removeAt(i)),
                          child:const Text('Remover')),
                      ]),
                  ]),
              ],
              if(answers.contains('Sim'))
                const Text('Uma ou mais situações precisam de avaliação. '
                  'Não se aproxime ou tente corrigir por conta própria.',
                  style:TextStyle(fontWeight:FontWeight.w600)),
              const SizedBox(height:8),
              TextField(controller:observation,maxLength:250,maxLines:3,
                decoration:const InputDecoration(
                  labelText:'Quer acrescentar algo? (opcional)',
                  border:OutlineInputBorder())),
              const Text('A equipe técnica receberá o relato. '
                'As respostas não comprovam conformidade e não encerram '
                'não conformidades. Não inclua nomes ou dados de saúde. '
                'É necessária internet para enviar; não há rascunho offline.',
                style:TextStyle(fontSize:12)),
            ],
            if(error.isNotEmpty)
              Text(error,style:TextStyle(
                color:Theme.of(context).colorScheme.error)),
          ],
        ))),
      actions:[
        TextButton(
          onPressed:sending?null:()=>Navigator.pop(context,false),
          child:const Text('Cancelar')),
        if(step>0)OutlinedButton(
          onPressed:sending?null:()=>setState(()=>page=page-1),
          child:const Text('Voltar')),
        if(step<4)FilledButton(
          onPressed:sending||
            (step==0&&place.text.trim().length<2)||
            (step>=1&&answers[step-1]==null)?null:_next,
          child:Text(step==0?'Começar':step==3?
            'Conferir respostas':'Próxima')),
        if(step==4)FilledButton.icon(
          onPressed:sending||answers.any((a)=>a==null)?null:_send,
          icon:const Icon(Icons.send_outlined),
          label:Text(sending?'Enviando...':'Enviar para análise')),
      ],
    );
  }
}

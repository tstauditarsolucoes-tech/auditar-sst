import 'package:flutter/material.dart';

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
    super.key, required this.onSend,
  });
  final Future<void> Function(String place,String note) onSend;

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
  bool sending=false;
  String error='';

  @override
  void initState() {
    super.initState();
    _resetAnswers();
  }

  void _resetAnswers() {
    answers=List<String?>.filled(
      CipaGuidedInspection.questionsFor(category).length,null);
  }

  @override
  void dispose() {
    place.dispose();
    observation.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    if(sending || place.text.trim().length<2 ||
        answers.any((answer)=>answer==null))return;
    setState(() {sending=true;error='';});
    try {
      final note=CipaGuidedInspection.summary(
        place:place.text,category:category,
        answers:answers.cast<String>(),observation:observation.text);
      await widget.onSend(place.text.trim(),note);
      if(mounted)Navigator.of(context).pop(true);
    } catch (_) {
      if(mounted)setState(()=>error='Envio não confirmado. '
        'Confira a conexão antes de tentar novamente.');
    } finally {
      if(mounted)setState(()=>sending=false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final questions=CipaGuidedInspection.questionsFor(category);
    return AlertDialog(
      title:const Text('Minha Vistoria CIPA'),
      content:SizedBox(width:460,child:SingleChildScrollView(
        child:Column(mainAxisSize:MainAxisSize.min,
          crossAxisAlignment:CrossAxisAlignment.stretch,children:[
          const Text('Observe somente de um local seguro. Não entre em '
            'áreas restritas, não toque em máquinas e não realize testes. '
            'Em perigo imediato, afaste-se e avise o responsável.'),
          const SizedBox(height:12),
          TextField(controller:place,maxLength:120,
            onChanged:(_)=>setState((){}),
            decoration:const InputDecoration(
              labelText:'Setor ou local observado',
              hintText:'Ex.: Produção — corredor do forno',
              border:OutlineInputBorder())),
          DropdownButtonFormField<String>(
            value:category,
            decoration:const InputDecoration(
              labelText:'Escolha o setor ou tema',
              border:OutlineInputBorder()),
            items:[
              for(final name in <String>[
                ...CipaGuidedInspection.questions.keys,
                ...CipaGuidedInspection.sectorQuestions.keys,
              ])
                DropdownMenuItem(value:name,child:Text(name)),
            ],
            onChanged:sending?null:(next) {
              if(next==null)return;
              setState(() {category=next;_resetAnswers();});
            }),
          const SizedBox(height:14),
          const Text('São só 3 perguntas. Marque Sim se observou '
            'a situação de longe, Não se não observou e Não sei quando '
            'não conseguiu verificar.'),
          Card(child:ExpansionTile(
            title:const Text('Como observar com segurança?'),
            children:[Padding(padding:const EdgeInsets.all(12),
              child:Text(CipaGuidedInspection.help[category] ??
                'Observe apenas de um local seguro.'))],
          )),
          const SizedBox(height:8),
          Text('Respondidas: ${answers.where((a)=>a!=null).length} '
            'de ${questions.length}',
            style:const TextStyle(fontWeight:FontWeight.w600)),
          const SizedBox(height:6),
          LinearProgressIndicator(
            value:answers.where((a)=>a!=null).length/questions.length),
          const SizedBox(height:12),
          for(var i=0;i<questions.length;i++)...[
            Text(questions[i],style:const TextStyle(
              fontWeight:FontWeight.w600,fontSize:16)),
            for(final answer in const [
              'Sim','Não','Não sei/não verifiquei',
            ])
              RadioListTile<String>(
                key:ValueKey('answer-$i-$answer'),
                dense:true,contentPadding:EdgeInsets.zero,
                title:Text(answer),
                value:answer,groupValue:answers[i],
                onChanged:sending?null:(next) =>
                  setState(()=>answers[i]=next!)),
            const Divider(),
          ],
          if(answers.contains('Sim'))...[
            const Padding(
              padding:EdgeInsets.symmetric(vertical:8),
              child:Text('Você assinalou pelo menos uma situação para '
                'avaliação. Não tente corrigir ou verificar de perto. '
                'Se perceber perigo imediato, afaste-se e comunique '
                'o responsável conforme o procedimento da empresa.',
                style:TextStyle(fontWeight:FontWeight.w600)),
            ),
          ],
          TextField(controller:observation,maxLength:250,maxLines:3,
            decoration:const InputDecoration(
              labelText:'Algo mais que deseja contar? (opcional)',
              border:OutlineInputBorder())),
          if(error.isNotEmpty)Text(error,
            style:TextStyle(color:Theme.of(context).colorScheme.error)),
          const Text('Este é um registro de participação na CIPA. '
            'O técnico fará a conferência. Nenhuma não conformidade '
            'é aberta ou encerrada automaticamente. Não inclua nomes '
            'de pessoas nem dados de saúde. É necessária conexão para '
            'enviar: este formulário não salva rascunhos offline.',
            style:TextStyle(fontSize:12)),
        ]))),
      actions:[
        TextButton(onPressed:sending?null:()=>Navigator.pop(context,false),
          child:const Text('Cancelar')),
        FilledButton.icon(
          onPressed:sending||place.text.trim().length<2||
            answers.any((answer)=>answer==null)?null:_send,
          icon:const Icon(Icons.send_outlined),
          label:Text(sending?'Enviando...':'Enviar para análise')),
      ],
    );
  }
}

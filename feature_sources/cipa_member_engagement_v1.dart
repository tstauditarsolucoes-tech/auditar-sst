import 'cipa_member_portal_policy.dart';

/// Conteúdo educativo local, sem pontuação competitiva ou certificação NR-5.
/// Um relato enviado é uma contribuição, não uma não conformidade validada.
class CipaMonthlyMission {
  const CipaMonthlyMission(this.title,this.description,this.category);
  final String title,description,category;
}

class CipaMiniLesson {
  const CipaMiniLesson(this.title,this.summary,this.question,
    this.choices,this.correctIndex,this.explanation);
  final String title,summary,question,explanation;
  final List<String> choices;
  final int correctIndex;
}

class CipaMemberImpact {
  const CipaMemberImpact({required this.reports,
    required this.technicalReplies,required this.completedActions,
    required this.missionReported});
  final int reports,technicalReplies,completedActions;
  final bool missionReported;
}

class CipaMemberEngagement {
  const CipaMemberEngagement._();
  static const questionMarker='DÚVIDA DO CIPEIRO PARA ORIENTAÇÃO SST';
  static const questionPlace='Orientação CIPA';
  static const questionTopics=<String>[
    'EPI e proteção','Máquinas e equipamentos',
    'Quedas e circulação','Incêndio e emergência',
    'Reuniões e atribuições da CIPA','Outro assunto',
  ];

  static const _missions=<CipaMonthlyMission>[
    CipaMonthlyMission('Passagens seguras',
      'Observe de local permitido se corredores e saídas estão livres. '
      'Não entre em áreas interditadas.','Organização e circulação'),
    CipaMonthlyMission('Acesso aos extintores',
      'Observe se extintores e saídas estão acessíveis. '
      'Não manuseie equipamentos.','Incêndio e emergência'),
    CipaMonthlyMission('Proteções visíveis',
      'Observe máquinas apenas à distância, sem abrir, tocar ou testar. '
      'Anote situações que precisam de análise.','Máquinas e equipamentos'),
    CipaMonthlyMission('Ambiente e proteção',
      'Observe condições aparentes sem se expor a calor, poeira, '
      'tráfego ou partes móveis.','Ambiente e proteção'),
  ];

  static CipaMonthlyMission missionFor(DateTime date)=>
    _missions[(date.month-1)%_missions.length];

  static const lessons=<CipaMiniLesson>[
    CipaMiniLesson('Qual é meu papel na CIPA?',
      'O integrante escuta colegas, observa situações e ajuda a '
      'acompanhar medidas de prevenção. A avaliação técnica é feita '
      'pelos responsáveis.','Ao perceber um perigo, o que fazer?',
      ['Registrar de um local seguro e comunicar a equipe',
       'Aproximar-se para fazer um teste',
       'Concluir que está tudo irregular'],0,
      'Observe com segurança. Não é preciso definir uma NR nem '
      'confirmar uma infração para pedir avaliação.'),
    CipaMiniLesson('Como observar com segurança?',
      'Não abra painéis, não retire proteções, não suba em locais '
      'altos e não entre em áreas restritas para fotografar.',
      'Se não consigo ver algo com segurança, devo:',
      ['Arriscar uma aproximação',
       'Marcar não verificado e pedir orientação',
       'Informar que a condição está correta'],1,
      'Não se exponha ao risco. Use a opção de não verificado '
      'quando não houver observação segura.'),
    CipaMiniLesson('Como participar da reunião?',
      'Leia a convocação, leve observações e sugestões. '
      'Confirmar ciência do aviso não registra presença '
      'nem assinatura na ata.',
      'Confirmar que li a convocação significa:',
      ['Assinei a ata automaticamente',
       'Estive presente na reunião',
       'Somente que tomei ciência do aviso'],2,
      'A presença e o registro da reunião precisam de procedimentos próprios.'),
    CipaMiniLesson('Como acompanhar uma melhoria?',
      'Envie a situação e veja a resposta técnica. '
      'Uma vistoria enviada não comprova que o risco foi eliminado.',
      'Depois de enviar uma observação, devo:',
      ['Acompanhar a devolutiva da equipe responsável',
       'Marcar a ação como encerrada sem verificação',
       'Ignorar qualquer retorno'],0,
      'A equipe responsável avalia a situação e confirma as providências.'),
  ];

  static bool isQuestion(CipaMemberItem item)=>
    item.type==CipaMemberItemType.observation&&
    (item.description.contains(questionMarker)||
     item.title.contains(questionPlace));

  static String questionText(String topic,String detail){
    if(!questionTopics.contains(topic))throw ArgumentError('Assunto inválido');
    final clean=detail.trim();
    if(clean.length<8||clean.length>950)
      throw ArgumentError('Descreva sua dúvida de 8 a 950 caracteres');
    return '$questionMarker\nAssunto: $topic\nDúvida: $clean\n'
      'Solicitação de orientação, não vistoria técnica nem chamado de emergência.';
  }

  static CipaMemberImpact impact(CipaMemberView view,{DateTime? now}){
    final p=view.profile;
    final reference=now??DateTime.now();
    bool mine(CipaMemberItem item)=>
      item.companyId==p.companyId&&item.mandateId==p.mandateId&&
      item.assignedMemberId==p.memberId;
    final reports=view.observations.where(mine).toList();
    final mission=missionFor(reference);
    final missionReported=reports.any((item)=>
      item.description.contains('VISTORIA ORIENTADA DA CIPA')&&
      item.description.contains('Tema: ${mission.category}')&&
      item.date!=null&&item.date!.year==reference.year&&
      item.date!.month==reference.month);
    return CipaMemberImpact(
      reports:reports.length,
      technicalReplies:reports.where((item)=>
        item.feedback.trim().isNotEmpty&&
        item.status=='Orientação enviada').length,
      completedActions:view.myActions.where((item)=>
        mine(item)&&
        ['Concluída','Resolvida'].contains(item.status)).length,
      missionReported:missionReported,
    );
  }
}

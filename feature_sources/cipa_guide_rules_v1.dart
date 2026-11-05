/// Regras de orientação da CIPA: são indicadores de cadastro e atenção,
/// nunca declaração automática de cumprimento da NR-05.
class CipaGuideSnapshot {
  const CipaGuideSnapshot({
    required this.hasActiveMandate,required this.activeMemberCount,
    required this.registeredElectionCount,required this.hasUpcomingMeeting,
    required this.performedMeetingCount,required this.minutesWithoutMeetingCount,
    required this.trainingNotFoundCount,required this.openActionCount,
    required this.overdueActionCount,required this.requiredDocumentPendingCount,
    required this.observationsAwaitingReviewCount,
  });
  final bool hasActiveMandate;
  final int activeMemberCount;
  final int registeredElectionCount;
  final bool hasUpcomingMeeting;
  final int performedMeetingCount;
  final int minutesWithoutMeetingCount;
  final int trainingNotFoundCount;
  final int openActionCount;
  final int overdueActionCount;
  final int requiredDocumentPendingCount;
  final int observationsAwaitingReviewCount;
}
class CipaGuideStep {
  const CipaGuideStep(this.id,this.title,this.description,this.status,
      this.action,this.tab,{this.attention=false,this.registered=false});
  final String id,title,description,status,action;
  final int tab;
  final bool attention,registered;
}

class CipaGuideRules {
  static List<CipaGuideStep> steps(CipaGuideSnapshot s) => [
    CipaGuideStep('mandate','1. Mandato da CIPA',
      'Registre início, término e situação do mandato. Confira antes o enquadramento da empresa na NR-05.',
      s.hasActiveMandate?'Mandato ativo cadastrado':'Mandato ativo não localizado',
      s.hasActiveMandate?'Conferir mandato':'Cadastrar mandato',1,
      attention:!s.hasActiveMandate,registered:s.hasActiveMandate),
    CipaGuideStep('election','2. Eleição e representação (se aplicável)',
      'Conferir dimensionamento, comissão eleitoral e documentos aplicáveis. Nem todo estabelecimento precisa realizar eleição.',
      s.registeredElectionCount>0?'Eleição registrada':'Conferir se há eleição aplicável',
      'Abrir eleições',6,registered:s.registeredElectionCount>0),
    CipaGuideStep('members','3. Integrantes e funções',
      'Cadastre titulares, suplentes e representantes aplicáveis. A quantidade no app não comprova dimensionamento correto.',
      s.activeMemberCount>0?'${s.activeMemberCount} integrante(s) ativo(s) cadastrado(s)':'Integrantes ativos não localizados',
      s.activeMemberCount>0?'Conferir integrantes':'Cadastrar integrantes',2,
      attention:s.hasActiveMandate&&s.activeMemberCount==0,
      registered:s.activeMemberCount>0),
    CipaGuideStep('training','4. Treinamento dos integrantes',
      'Confira registros, conteúdos e carga horária aplicáveis. Ausência no aplicativo não prova falta de treinamento.',
      s.activeMemberCount==0?'Primeiro cadastre os integrantes':
        s.trainingNotFoundCount>0?'${s.trainingNotFoundCount} treinamento(s) não localizado(s)':'Registros localizados; conferir exigências',
      'Abrir treinamentos',7,
      attention:s.hasActiveMandate&&s.activeMemberCount>0&&s.trainingNotFoundCount>0,
      registered:s.activeMemberCount>0&&s.trainingNotFoundCount==0),
    CipaGuideStep('meeting','5. Reuniões e calendário',
      'Prepare a pauta, agende e acompanhe as reuniões. Agendada não significa realizada.',
      s.hasUpcomingMeeting?'Próxima reunião agendada':'Próxima reunião não localizada',
      s.hasUpcomingMeeting?'Conferir reuniões':'Preparar reunião',3,
      attention:s.hasActiveMandate&&!s.hasUpcomingMeeting,
      registered:s.hasUpcomingMeeting||s.performedMeetingCount>0),
    CipaGuideStep('minutes','6. Atas e decisões',
      'Registre participantes presentes, decisões e encaminhamentos no editor original. Assinatura não é presumida.',
      s.minutesWithoutMeetingCount>0?'${s.minutesWithoutMeetingCount} reunião(ões) sem ata vinculada':
        s.performedMeetingCount>0?'Sem atas pendentes identificadas':'Acompanhar depois da reunião',
      'Abrir atas',4,attention:s.minutesWithoutMeetingCount>0,
      registered:s.performedMeetingCount>0&&s.minutesWithoutMeetingCount==0),
    CipaGuideStep('actions','7. Plano de ação e melhorias',
      'Acompanhe responsáveis, prazos, evidências e pedidos de apoio. Informar andamento não encerra a NC.',
      s.overdueActionCount>0?'${s.overdueActionCount} ação(ões) vencida(s)':
        s.openActionCount>0?'${s.openActionCount} ação(ões) em acompanhamento':'Nenhuma ação aberta cadastrada',
      'Abrir plano de ação',5,attention:s.overdueActionCount>0,
      registered:s.openActionCount>0),
    CipaGuideStep('documents','8. Documentos e histórico',
      'Confira atas, anexos, eleições e documentos exigíveis. O aplicativo não certifica documentação completa.',
      s.requiredDocumentPendingCount>0?'${s.requiredDocumentPendingCount} documento(s) marcado(s) pendente(s)':'Conferir documentação aplicável',
      'Abrir documentos',8,attention:s.requiredDocumentPendingCount>0),
  ];

  static CipaGuideStep recommended(CipaGuideSnapshot s) {
    final items=steps(s);
    if(!s.hasActiveMandate)return items[0];
    if(s.activeMemberCount==0)return items[2];
    if(s.overdueActionCount>0)return items[6];
    if(s.minutesWithoutMeetingCount>0)return items[5];
    if(s.observationsAwaitingReviewCount>0) {
      return CipaGuideStep('participation','Avaliar situações observadas',
        'Confira relatos com segurança sem criar ou fechar automaticamente NC.',
        '${s.observationsAwaitingReviewCount} situação(ões) aguardando avaliação',
        'Abrir participação',10,attention:true);
    }
    if(s.trainingNotFoundCount>0)return items[3];
    if(!s.hasUpcomingMeeting)return items[4];
    if(s.requiredDocumentPendingCount>0)return items[7];
    return const CipaGuideStep('routine','Manter a rotina da CIPA',
      'Observe os ambientes, acompanhe medidas e prepare reuniões. Nada é validado automaticamente.',
      'Acompanhamento contínuo','Abrir roteiro mensal',10);
  }
  static int registeredCount(CipaGuideSnapshot s)=>
    steps(s).where((e)=>e.registered).length;
  static int attentionCount(CipaGuideSnapshot s)=>
    steps(s).where((e)=>e.attention).length;
}

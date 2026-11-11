import 'cipa_meeting_coach_rules_v1.dart';

void check(bool ok,String message) {
  if(!ok)throw StateError('CIPA_COACH_TEST_FAIL: $message');
}
CipaMeetingCoachResult evaluate({
  bool mandate=true,int members=3,
  List<CipaMeetingCoachMeeting> meetings=const [],
  List<CipaMeetingCoachMinutes> minutes=const [],
  List<CipaMeetingCoachAction> actions=const [],
})=>CipaMeetingCoachRules.evaluate(
  hasActiveMandate:mandate,activeMemberCount:members,
  now:DateTime(2026,11,6,9),
  meetings:meetings,minutes:minutes,actions:actions);

CipaMeetingCoachMeeting meet({
  String status='Agendada',String agenda='',String place='',
  String subjects='',String decisions='',
  DateTime? date,List<String> invited=const [],
  List<String> present=const [],
  String id='reuniao-1',
})=>CipaMeetingCoachMeeting(
  id:id,title:'Reunião de novembro',date:date??DateTime(2026,11,10),
  status:status,agenda:agenda,place:place,
  subjects:subjects,decisions:decisions,
  invitedIds:invited,presentIds:present,
);

void main() {
  final noMandate=evaluate(mandate:false,meetings:[
    meet(status:'Realizada',date:DateTime(2026,10,10)),
  ]);
  check(noMandate.selectedMeetingId==null,'não usar dados sem mandato');
  check(noMandate.steps.first.target=='mandate','orientar mandato');
  final empty=evaluate();
  check(empty.steps.any((s)=>s.target=='new_meeting'),
    'reunião não cadastrada precisa orientação');
  final planned=evaluate(meetings:[
    meet(agenda:'Inspeção e plano de ação',place:'Sala',
      invited:['m1','m2']),
  ]);
  check(planned.selectedMeetingId=='reuniao-1','seleção');
  check(planned.steps.every((s)=>s.title!='Conferir presenças'),
    'agendamento não exige presença registrada antecipadamente');
  check(planned.steps.every((s)=>s.title!='Preparar pauta'),
    'não marcar pauta existente como ausente');
  final missing=evaluate(meetings:[meet()]);
  check(missing.attentionCount>=3,'campos não preenchidos');
  check(missing.steps.any((s)=>s.title=='Conferir convidados'),
    'convocação não é presença');
  final old=evaluate(meetings:[
    meet(date:DateTime(2026,11,1)),
  ]);
  check(old.steps.any((s)=>s.title=='Conferir data passada'),
    'data antiga não comprova reunião realizada');
  final done=evaluate(meetings:[
    meet(status:'Realizada',date:DateTime(2026,11,5),
      invited:['m1','m2']),
  ]);
  check(done.steps.any((s)=>s.title=='Conferir presenças'),
    'não inventar presença');
  check(done.steps.any((s)=>s.title=='Elaborar ata'),
    'reunião sem ata precisa revisão');
  final withDraft=evaluate(meetings:[
    meet(status:'Realizada',date:DateTime(2026,11,5),
      invited:['m1'],present:['m1'],
      subjects:'Ações do mês',decisions:'Acompanhar execução'),
  ],minutes:[
    const CipaMeetingCoachMinutes(meetingId:'reuniao-1',status:'Rascunho')
  ]);
  check(withDraft.steps.any((s)=>s.title=='Revisar rascunho da ata'),
    'minuta precisa revisão');
  check(withDraft.steps.any((s)=>
    s.title=='Conferir assinaturas e divulgação'),
    'minuta não certifica assinatura');
  final finalized=evaluate(meetings:[
    meet(status:'Realizada',date:DateTime(2026,11,5),
      invited:['m1'],present:['m1'],
      subjects:'Ações',decisions:'Registrar prazo'),
  ],minutes:[
    const CipaMeetingCoachMinutes(meetingId:'reuniao-1',status:'Finalizada')
  ]);
  check(finalized.steps.any((s)=>
    s.title=='Conferir assinaturas e divulgação'),
    'finalização eletrônica não prova assinatura nem publicação');
  final actions=evaluate(
    meetings:[meet()],
    actions:[
      CipaMeetingCoachAction(status:'Aberta',
        dueDate:DateTime(2026,10,20)),
      CipaMeetingCoachAction(status:'Resolvida',
        dueDate:DateTime(2026,10,10)),
    ]);
  check(actions.steps.any((s)=>s.title.contains('1 ação(ões) vencida(s)')),
    'não contar resolvida como vencida');
  final cancelled=evaluate(meetings:[meet(status:'Cancelada')]);
  check(cancelled.selectedMeetingId==null,'ignorar reunião cancelada');
  final two=evaluate(meetings:[
    meet(id:'antiga',date:DateTime(2026,11,2)),
    meet(id:'futura',date:DateTime(2026,11,7)),
    meet(id:'realizada',status:'Realizada',date:DateTime(2026,11,5))
  ]);
  check(two.selectedMeetingId=='realizada',
    'priorizar reunião realizada sem ata sobre agenda nova');
  final sectors=CipaTopicAdvisor.sectors;
  check(sectors.contains('Cerâmica')&&sectors.contains('Panificação')&&
    sectors.contains('Construção civil'),'setores principais disponíveis');
  for(final sector in sectors){
    final suggestions=CipaTopicAdvisor.suggest(
      sector:sector,openActions:0,overdueActions:0);
    check(suggestions.isNotEmpty,'setor deve ter pauta');
    check(suggestions.any((s)=>s.reason.contains('Tema')||
      s.title.isNotEmpty),'tema visível');
    check(suggestions.every((s)=>s.points.isNotEmpty),
      'cada proposta tem pontos para discutir');
    check(suggestions.every((s)=>s.draftAgenda.contains('PROPOSTA DE PAUTA')&&
      s.draftAgenda.contains('não é ata')),
      'não apresentar sugestão como ata concluída');
    check(!suggestions.any((s)=>s.title.contains('ações pendentes')),
      'não inventar pendências');
  }
  final pending=CipaTopicAdvisor.suggest(
    sector:'Cerâmica',openActions:4,overdueActions:2);
  check(pending.first.title.contains('ações pendentes'),
    'priorizar ações em aberto');
  check(pending.first.reason.contains('4 ação(ões)')&&
    pending.first.reason.contains('2 com prazo vencido'),
    'contagem somente com dados informados');
  check(pending.first.draftAgenda.contains('responsáveis e prazos'),
    'incluir revisão e próximos passos');
  check(pending.any((s)=>s.title.contains('máquinas')),
    'recomendar setor selecionado');
  check(pending.every((s)=>!s.draftAgenda.contains('Estiveram presentes')&&
    !s.draftAgenda.contains('Foi deliberado')),
    'não inventar presença ou decisão');
  var rejected=false;
  try {
    CipaTopicAdvisor.suggest(
      sector:'Cerâmica',openActions:1,overdueActions:2);
  }catch(_){rejected=true;}
  check(rejected,'não aceitar contagem inconsistente');
  rejected=false;
  try {
    CipaTopicAdvisor.suggest(
      sector:'Empresa inexistente',openActions:0,overdueActions:0);
  }catch(_){rejected=true;}
  check(rejected,'não inventar ramo desconhecido');
  print('CIPA_MEETING_COACH_RULES_TOPICS_AND_11_SCENARIOS_OK');
}

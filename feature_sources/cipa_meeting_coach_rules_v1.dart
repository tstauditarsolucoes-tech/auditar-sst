/// Checklist orientativo da CIPA — sem alterar documentos ou provar NR-05.
class CipaMeetingCoachMeeting {
  const CipaMeetingCoachMeeting({
    required this.id,required this.title,required this.date,
    required this.status,this.agenda='',this.place='',
    this.subjects='',this.decisions='',
    this.invitedIds=const [],this.presentIds=const [],
  });
  final String id,title,status,agenda,place,subjects,decisions;
  final DateTime date;
  final List<String> invitedIds,presentIds;
}
class CipaMeetingCoachMinutes {
  const CipaMeetingCoachMinutes({
    required this.meetingId,required this.status,
  });
  final String meetingId,status;
}
class CipaMeetingCoachAction {
  const CipaMeetingCoachAction({
    required this.status,this.dueDate,this.responsible='',
  });
  final String status,responsible;
  final DateTime? dueDate;
}
class CipaMeetingCoachStep {
  const CipaMeetingCoachStep(this.title,this.detail,this.target,{
    this.attention=false,
  });
  final String title,detail,target;
  final bool attention;
}
class CipaMeetingCoachResult {
  const CipaMeetingCoachResult({
    required this.title,required this.summary,
    required this.steps,required this.nextAction,
    this.selectedMeetingId,
  });
  final String title,summary,nextAction;
  final String? selectedMeetingId;
  final List<CipaMeetingCoachStep> steps;
  int get attentionCount=>steps.where((s)=>s.attention).length;
}
class CipaMeetingCoachRules {
  static bool _closed(String s)=>s=='Resolvida'||s=='Concluída'||
    s=='Concluído'||s=='Cancelada'||s=='Arquivada';
  static CipaMeetingCoachResult evaluate({
    required bool hasActiveMandate,
    required int activeMemberCount,
    required DateTime now,
    required Iterable<CipaMeetingCoachMeeting> meetings,
    required Iterable<CipaMeetingCoachMinutes> minutes,
    required Iterable<CipaMeetingCoachAction> actions,
  }) {
    if(!hasActiveMandate) {
      return const CipaMeetingCoachResult(
        title:'Inicie pelo mandato da CIPA',
        summary:'Nenhum mandato ativo localizado neste cadastro.',
        nextAction:'Conferir mandato',
        steps:[CipaMeetingCoachStep('Conferir mandato',
          'Cadastre ou ative o mandato aplicável antes de organizar a reunião.',
          'mandate',attention:true)],
      );
    }
    final all=meetings.where((m)=>
      m.id.trim().isNotEmpty && m.status!='Cancelada').toList();
    final performed=all.where((m)=>m.status=='Realizada').toList();
    final scheduled=all.where((m)=>m.status=='Agendada').toList();
    final minutesList=minutes.toList();
    final overdueSchedule=scheduled.where((m)=>m.date.isBefore(now)).toList()
      ..sort((a,b)=>a.date.compareTo(b.date));
    final missingMinutes=performed.where((m)=>
      !minutesList.any((a)=>a.meetingId==m.id)).toList()
      ..sort((a,b)=>b.date.compareTo(a.date));
    final future=scheduled.where((m)=>!m.date.isBefore(now)).toList()
      ..sort((a,b)=>a.date.compareTo(b.date));
    final recent=performed.toList()
      ..sort((a,b)=>b.date.compareTo(a.date));
    final selected=missingMinutes.isNotEmpty?missingMinutes.first:
      overdueSchedule.isNotEmpty?overdueSchedule.first:
      future.isNotEmpty?future.first:
      recent.isNotEmpty?recent.first:null;
    final steps=<CipaMeetingCoachStep>[];
    if(activeMemberCount==0){
      steps.add(const CipaMeetingCoachStep('Conferir integrantes',
        'Nenhum integrante ativo foi localizado. Verifique o cadastro e '
        'as representações do mandato.', 'members',attention:true));
    }
    if(selected==null) {
      steps.add(const CipaMeetingCoachStep('Preparar próxima reunião',
        'Agende data, horário, pauta e membros convidados. '
        'O aplicativo não determina sozinho a periodicidade aplicável.',
        'new_meeting',attention:true));
    } else if(selected.status=='Agendada'){
      if(selected.date.isBefore(now)){
        steps.add(const CipaMeetingCoachStep('Conferir data passada',
          'A reunião permanece agendada. Confirme se ocorreu, '
          'foi remarcada ou cancelada antes de atualizar.', 'meeting',
          attention:true));
      }else{
        steps.add(const CipaMeetingCoachStep('Conferir convocação',
          'Verifique data, horário e divulgação aos membros. '
          'Convocação não comprova participação.', 'meeting'));
      }
      if(selected.place.trim().isEmpty){
        steps.add(const CipaMeetingCoachStep('Informar local',
          'Confirme local ou participação remota, quando aplicável.',
          'meeting',attention:true));
      }
      if(selected.agenda.trim().isEmpty){
        steps.add(const CipaMeetingCoachStep('Preparar pauta',
          'Inclua situações observadas, ações pendentes e temas preventivos.',
          'meeting',attention:true));
      }
      if(selected.invitedIds.isEmpty) {
        steps.add(const CipaMeetingCoachStep('Conferir convidados',
          'Nenhum convidado foi registrado. Não confundir ciência '
          'da convocação com presença.', 'meeting',attention:true));
      }
      steps.add(const CipaMeetingCoachStep('Depois: registrar o que ocorreu',
        'Após a reunião, informe os presentes, assuntos e decisões '
        'efetivamente registrados. Não preencher antecipadamente.',
        'meeting'));
    }else{
      if(selected.invitedIds.isEmpty||selected.presentIds.isEmpty) {
        steps.add(const CipaMeetingCoachStep('Conferir presenças',
          'Presenças individuais não foram localizadas. '
          'Verifique a lista real antes de emitir a ata.', 'meeting',
          attention:true));
      }
      if(selected.subjects.trim().isEmpty||selected.decisions.trim().isEmpty){
        steps.add(const CipaMeetingCoachStep('Revisar assuntos e decisões',
          'Registre discussões e deliberações que de fato ocorreram.',
          'meeting',attention:true));
      }
      final linked=minutesList.where((a)=>a.meetingId==selected.id).toList();
      if(linked.isEmpty) {
        steps.add(const CipaMeetingCoachStep('Elaborar ata',
          'Nenhuma ata vinculada foi localizada. Confira os fatos '
          'antes de gerar e revisar o rascunho.', 'minutes',attention:true));
      }else{
        if(linked.every((a)=>a.status=='Rascunho')){
          steps.add(const CipaMeetingCoachStep('Revisar rascunho da ata',
            'Confira texto, participantes e decisões no editor de atas.',
            'minutes',attention:true));
        }
        steps.add(const CipaMeetingCoachStep('Conferir assinaturas e divulgação',
          'Confira as assinaturas dos presentes e a disponibilização '
          'da ata e dos encaminhamentos. O aplicativo não presume isso.',
          'minutes'));
      }
    }
    final open=actions.where((a)=>!_closed(a.status)).toList();
    final overdue=open.where((a)=>a.dueDate!=null &&
      a.dueDate!.isBefore(now)).length;
    final withoutResponsible=open.where((a)=>
      a.responsible.trim().isEmpty).length;
    if(overdue>0){
      steps.add(CipaMeetingCoachStep(
        'Acompanhar ${overdue} ação(ões) vencida(s)',
        'Conferir prazo, execução e evidências. '
        'Acompanhamento não fecha uma NC ou ação automaticamente.',
        'actions',attention:true));
    }else if(open.isNotEmpty) {
      steps.add(CipaMeetingCoachStep('Acompanhar ações em aberto',
        '${open.length} ação(ões) em acompanhamento.',
        'actions'));
    }
    if(withoutResponsible>0) {
      steps.add(CipaMeetingCoachStep('Conferir responsáveis',
        '${withoutResponsible} ação(ões) em aberto sem '
        'responsável identificado nos registros.',
        'actions',attention:true));
    }
    return CipaMeetingCoachResult(
      title:selected?.title??'Próxima reunião da CIPA',
      summary:selected==null
        ? 'Nenhuma reunião não cancelada localizada no mandato.'
        : selected.status=='Realizada'
          ? 'Reunião marcada como realizada; conferir registros posteriores.'
          : selected.date.isBefore(now)
            ? 'Data passada com reunião ainda agendada.'
            : 'Reunião agendada. Prepare e confira os dados.',
      selectedMeetingId:selected?.id,
      steps:List.unmodifiable(steps),
      nextAction:selected==null?'Preparar reunião':
        selected.status=='Realizada'?'Conferir reunião e ata':
          'Abrir reunião',
    );
  }
}

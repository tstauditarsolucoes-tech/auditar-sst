part of 'cipa_management_screen.dart';

// Gestão visual, dentro da conta já autenticada. Não substitui login
// individual do integrante nem altera qualquer status de NC ou ação.
extension _CipaFollowup on _CipaManagementScreenState {
  Future<void> _cipaReviewObservation(CipaParticipationEvent observation) async {
    final mandate=activeMandate;
    if(busy || mandate==null || mandate.status!='Ativo' ||
       observation.companyId!=widget.companyId ||
       observation.data['mandateId']!=mandate.id) return;
    final note=await _cipaReason('Conferir situação observada',
      'Descreva o encaminhamento. Registrar conferência não cria NC, '
      'não comprova correção e não altera o registro original.');
    if(note==null || !mounted || activeMandate?.id!=mandate.id) return;
    await _cipaRun(()=>_cipaEvent('observation_review',observation.id,{
      'title':observation.data['title'] ?? 'Situação observada',
      'observationId':observation.id,
      'detail':note,'reviewScope':'administrative_followup_only',
    },mandateId:mandate.id));
  }

  Future<void> _cipaReviewProgress(
      SstRecord action,CipaParticipationEvent report) async {
    final mandate=activeMandate;
    if(busy || mandate==null || mandate.status!='Ativo' ||
       action.companyId!=widget.companyId ||
       action.status=='Resolvida' ||
       _cipaRules.progress(action.id)?.id!=report.id) return;
    final note=await _cipaReason('Conferir andamento informado',
      'Esta conferência não altera o status da ação e não encerra uma NC. '
      'Uma nova atualização técnica exige o procedimento original.');
    if(note==null || !mounted || activeMandate?.id!=mandate.id ||
       _cipaRules.progress(action.id)?.id!=report.id) return;
    await _cipaRun(()=>_cipaEvent('progress_review',action.id,{
      'title':action.title,'reportEventId':report.id,'detail':note,
      'reviewScope':'administrative_followup_only',
    },mandateId:mandate.id));
  }

  Widget _cipaTriageCard() {
    final mandate=activeMandate;
    if(mandate==null) return const Card(child:ListTile(
      leading:Icon(Icons.rule_folder_outlined),
      title:Text('Pendências para avaliação'),
      subtitle:Text('Ative um mandato para acompanhar os registros.')));
    final q=CipaFollowupQueue(_cipaRules);
    final obs=q.pendingObservations(mandate.id);
    final pending=mandateActions.where((a)=>
        a.companyId==widget.companyId && a.status!='Resolvida').toList();
    final progressIds=q.pendingProgressActionIds(pending.map((a)=>a.id));
    final reports=pending.where((a)=>progressIds.contains(a.id)).toList();
    final overdue=pending.where(CipaManagementService.isOverdue).length;
    final noMinutes=pendingMinutesCount;
    final noTraining=pendingTrainingCount;
    final total=obs.length+reports.length+overdue+noMinutes+noTraining;
    final canReview=!_cipaSimpleMode && !busy && mandate.status=='Ativo';

    return Card(child:ExpansionTile(
      initiallyExpanded:true,
      leading:const Icon(Icons.rule_folder_outlined),
      title:const Text('Pendências para avaliação',
        style:TextStyle(fontWeight:FontWeight.w800)),
      subtitle:Text('$total item(ns) para conferir • '
        '${obs.length} relato(s) • ${reports.length} andamento(s)'),
      children:[
        const Padding(padding:EdgeInsets.fromLTRB(16,0,16,10),
          child:Text('Acompanhamento coletivo da conta atual. '
            'Não comprova presença, assinatura, cumprimento da NR-05 '
            'ou resolução técnica. A conferência não fecha uma NC.',
            style:TextStyle(fontSize:12))),
        if(total==0) const ListTile(
          leading:Icon(Icons.check_circle_outline),
          title:Text('Sem pendências nesses indicadores'),
          subtitle:Text('Continue acompanhando o mandato.')),
        if(obs.isNotEmpty) ...[
          ListTile(title:Text('Situações aguardando conferência '
            '(${obs.length})',style:const TextStyle(fontWeight:FontWeight.w700))),
          for(final item in obs.take(12)) ListTile(
            leading:const Icon(Icons.visibility_outlined),
            title:Text('${item.data['location'] ?? 'Local não informado'}'),
            subtitle:Text('${_dateTime.format(item.date)} • '
              '${item.data['detail'] ?? ''}',maxLines:3,
              overflow:TextOverflow.ellipsis),
            trailing:canReview ? TextButton(
              onPressed:()=>_cipaReviewObservation(item),
              child:const Text('Conferir'))
              :const Text('Aguardando gestão')),
          if(obs.length>12) ListTile(title:Text('Outros '
            '${obs.length-12} registro(s) na lista de situações.')),
        ],
        if(reports.isNotEmpty) ...[
          ListTile(title:Text('Andamentos aguardando revisão '
            '(${reports.length})',
            style:const TextStyle(fontWeight:FontWeight.w700))),
          for(final action in reports.take(12))
            Builder(builder:(context) {
              final report=q.pendingProgressReport(action.id);
              if(report==null)return const SizedBox.shrink();
              return ListTile(
                leading:const Icon(Icons.pending_actions_outlined),
                title:Text(action.title),
                subtitle:Text('${_dateTime.format(report.date)} • '
                  '${report.data['detail'] ?? ''}',maxLines:3,
                  overflow:TextOverflow.ellipsis),
                trailing:canReview ? TextButton(
                  onPressed:()=>_cipaReviewProgress(action,report),
                  child:const Text('Conferir'))
                  :const Text('Aguardando gestão'));
            }),
          if(reports.length>12) ListTile(title:Text(
            'Outros ${reports.length-12} informe(s) na lista de ações.')),
        ],
        if(overdue>0) ListTile(
          leading:const Icon(Icons.event_busy_outlined),
          title:Text('$overdue ação(ões) com prazo vencido'),
          subtitle:const Text('Rever responsáveis, prazos e controles.')),
        if(noMinutes>0) ListTile(
          leading:const Icon(Icons.description_outlined),
          title:Text('$noMinutes reunião(ões) realizadas sem ata'),
          subtitle:const Text('Conferir a reunião e elaborar a ata. '
            'Não presumir presença nem assinatura.')),
        if(noTraining>0) ListTile(
          leading:const Icon(Icons.school_outlined),
          title:Text('$noTraining membro(s) sem treinamento localizado'),
          subtitle:const Text('Conferir documentação e requisitos aplicáveis.')),
      ],
    ));
  }
}

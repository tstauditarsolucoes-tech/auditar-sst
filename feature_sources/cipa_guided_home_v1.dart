part of 'cipa_management_screen.dart';

/// Inicialização guiada apenas como camada de interface: todos os botões
/// chamam editores e abas JÁ EXISTENTES. Sem preenchimento de dados fictícios.
extension _CipaGuidedHome on _CipaManagementScreenState {
  CipaGuideSnapshot _cipaGuideSnapshot() {
    final mandate=activeMandate;
    final has=mandate!=null;
    final pendingDocuments=mandateDocuments.where((r)=>
      r.payload['requiredDocument']==true &&
      r.status!='Arquivado' && r.status!='Concluído').length;
    final nextScheduled=mandateMeetings.any((m)=>
      m.status=='Agendada' && m.date.isAfter(DateTime.now()));
    final pendingObs=has
      ? CipaFollowupQueue(_cipaRules).pendingObservations(mandate.id).length
      : 0;
    return CipaGuideSnapshot(
      hasActiveMandate:has,
      activeMemberCount:activeMembers.length,
      registeredElectionCount:elections.length,
      hasUpcomingMeeting:nextScheduled,
      performedMeetingCount:mandateMeetings.where((m)=>
        m.status=='Realizada').length,
      minutesWithoutMeetingCount:pendingMinutesCount,
      trainingNotFoundCount:pendingTrainingCount,
      openActionCount:mandateActions.where((a)=>a.status!='Resolvida').length,
      overdueActionCount:overdueActionsCount,
      requiredDocumentPendingCount:pendingDocuments,
      observationsAwaitingReviewCount:pendingObs,
    );
  }

  Future<void> _cipaOpenGuidedStep(CipaGuideStep step) async {
    if(busy)return;
    if(step.id=='mandate') {
      await _editMandate();
      return;
    }
    if(step.id=='members' && activeMandate==null) {
      _message('Primeiro cadastre ou ative o mandato da CIPA.');
      return;
    }
    if(step.id=='members' && activeMembers.isEmpty) {
      await _editMember();
      return;
    }
    if(step.id=='meeting' && !mandateMeetings.any((m)=>
        m.status=='Agendada' && m.date.isAfter(DateTime.now()))) {
      if(activeMandate==null) {
        _message('Cadastre ou ative um mandato antes de criar reuniões.');
        return;
      }
      await _cipaGuidedMeeting();
      return;
    }
    if(!mounted)return;
    DefaultTabController.of(context).animateTo(step.tab);
  }

  Future<void> _cipaGuideHelp(CipaGuideStep step) =>
    showDialog<void>(context:context,builder:(dialog)=>AlertDialog(
      title:Text(step.title),
      content:SingleChildScrollView(child:Column(
        mainAxisSize:MainAxisSize.min,
        crossAxisAlignment:CrossAxisAlignment.start,
        children:[
          Text(step.description),
          const SizedBox(height:12),
          Text('Situação encontrada no aplicativo: ${step.status}'),
          const SizedBox(height:12),
          const Text('Os registros precisam ser conferidos pela equipe '
            'responsável. Essa orientação não comprova cumprimento da NR-05.'),
        ],
      )),
      actions:[
        TextButton(onPressed:()=>Navigator.of(dialog).pop(),
          child:const Text('Fechar')),
        FilledButton(onPressed:(){
          Navigator.of(dialog).pop();
          _cipaOpenGuidedStep(step);
        },child:Text(step.action)),
      ],
    ));

  Widget _cipaGuidedHome() {
    final snapshot=_cipaGuideSnapshot();
    final steps=CipaGuideRules.steps(snapshot);
    final recommended=CipaGuideRules.recommended(snapshot);
    final count=CipaGuideRules.registeredCount(snapshot);
    final attention=CipaGuideRules.attentionCount(snapshot);
    return Card(
      child:Padding(
        padding:const EdgeInsets.all(14),
        child:Column(
          crossAxisAlignment:CrossAxisAlignment.start,
          children:[
            Row(children:[
              const Icon(Icons.auto_stories_outlined,size:26),
              const SizedBox(width:10),
              Expanded(child:Text('Sua CIPA, passo a passo',
                style:Theme.of(context).textTheme.titleMedium
                  ?.copyWith(fontWeight:FontWeight.w900))),
              IconButton(
                tooltip:'Entenda como utilizar este roteiro',
                onPressed:()=>_cipaGuideHelp(recommended),
                icon:const Icon(Icons.help_outline)),
            ]),
            const SizedBox(height:5),
            const Text('O aplicativo indica o próximo passo. Não é '
              'necessário saber de cor as etapas da CIPA. Você pode '
              'continuar usando todas as abas e formulários originais.'),
            const SizedBox(height:12),
            Text('Registros localizados em $count de 8 etapas • '
              '$attention área(s) para conferir',
              style:const TextStyle(fontWeight:FontWeight.w700)),
            const SizedBox(height:5),
            const Text('Esses números mostram apenas os dados cadastrados, '
              'não conformidade legal. É preciso confirmar as exigências '
              'da NR-05 para cada estabelecimento.',
              style:TextStyle(fontSize:12)),
            const Divider(height:25),
            const Text('O que fazer agora?',
              style:TextStyle(fontSize:17,fontWeight:FontWeight.w900)),
            const SizedBox(height:5),
            Text(recommended.title,
              style:const TextStyle(fontWeight:FontWeight.w800)),
            Text(recommended.status),
            const SizedBox(height:6),
            Text(recommended.description),
            const SizedBox(height:12),
            SizedBox(width:double.infinity,child:FilledButton.icon(
              onPressed:busy?null:()=>_cipaOpenGuidedStep(recommended),
              icon:const Icon(Icons.arrow_forward_outlined),
              label:Text(recommended.action))),
            const SizedBox(height:8),
            ExpansionTile(
              initiallyExpanded:false,
              tilePadding:EdgeInsets.zero,
              title:const Text('Ver todas as 8 etapas',
                style:TextStyle(fontWeight:FontWeight.w700)),
              subtitle:const Text('Abra cada opção para saber o que registrar'),
              children:[
                for(final step in steps)
                  Padding(
                    padding:const EdgeInsets.symmetric(vertical:4),
                    child:Column(
                      crossAxisAlignment:CrossAxisAlignment.start,
                      children:[
                        Row(children:[
                          Icon(step.attention?Icons.pending_actions_outlined:
                            step.registered?Icons.assignment_turned_in_outlined:
                            Icons.info_outline,
                            size:19),
                          const SizedBox(width:8),
                          Expanded(child:Text(step.title,
                            style:const TextStyle(fontWeight:FontWeight.w800))),
                          IconButton(
                            tooltip:'Explicação da etapa',
                            onPressed:()=>_cipaGuideHelp(step),
                            icon:const Icon(Icons.help_outline,size:20)),
                        ]),
                        Padding(padding:const EdgeInsets.only(left:27),
                          child:Text(step.status,
                            style:const TextStyle(fontSize:12))),
                        Padding(padding:const EdgeInsets.only(left:27),
                          child:Text(step.description)),
                        Align(alignment:Alignment.centerRight,
                          child:TextButton.icon(
                            onPressed:busy?null:()=>_cipaOpenGuidedStep(step),
                            icon:const Icon(Icons.chevron_right),
                            label:Text(step.action))),
                        const Divider(),
                      ],
                    ),
                  ),
              ],
            ),
            const SizedBox(height:8),
            const Text('Atalhos do dia',
              style:TextStyle(fontWeight:FontWeight.w800)),
            const SizedBox(height:7),
            Wrap(spacing:8,runSpacing:8,children:[
              OutlinedButton.icon(
                onPressed:busy||activeMandate==null?null:_cipaGuidedMeeting,
                icon:const Icon(Icons.event_note_outlined),
                label:const Text('Preparar reunião')),
              OutlinedButton.icon(
                onPressed:busy||activeMandate==null?null:_cipaNewObservation,
                icon:const Icon(Icons.visibility_outlined),
                label:const Text('Registrar situação')),
              OutlinedButton.icon(
                onPressed:busy||activeMandate==null?null:()=>_editAction(),
                icon:const Icon(Icons.add_task_outlined),
                label:const Text('Nova ação')),
            ]),
            const SizedBox(height:9),
            const Text('Acesso individual dos integrantes ainda não '
              'está disponível. Não compartilhe logins de gestão ou técnico.',
              style:TextStyle(fontSize:12)),
          ],
        ),
      ),
    );
  }
}

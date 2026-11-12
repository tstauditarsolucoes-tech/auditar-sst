part of 'cipa_management_screen.dart';

/// Camada visual de orientação: lê registros existentes, sem criar
/// presença, assinatura, ata ou ação e sem alterar permissões.
extension _CipaMeetingCoachHome on _CipaManagementScreenState {
  CipaMeetingCoachResult _cipaMeetingCoachSnapshot() {
    final mandate=activeMandate;
    return CipaMeetingCoachRules.evaluate(
      hasActiveMandate:mandate!=null,
      activeMemberCount:mandate==null?0:activeMembers.length,
      now:DateTime.now(),
      meetings:mandate==null?const <CipaMeetingCoachMeeting>[]:
        mandateMeetings.where((m)=>
          m.companyId==widget.companyId &&
          (m.payload['mandateId']??'').toString()==mandate.id).map((m)=>
            CipaMeetingCoachMeeting(
              id:m.id,title:m.title,date:m.date,status:m.status,
              agenda:(m.payload['agenda']??'').toString(),
              place:(m.payload['place']??'').toString(),
              subjects:(m.payload['subjects']??'').toString(),
              decisions:(m.payload['decisions']??'').toString(),
              invitedIds:(m.payload['memberIds'] is List?
                (m.payload['memberIds'] as List)
                  .map((e)=>e.toString()).toList():const <String>[]),
              presentIds:(m.payload['presentIds'] is List?
                (m.payload['presentIds'] as List)
                  .map((e)=>e.toString()).toList():const <String>[]),
            )),
      minutes:mandate==null?const <CipaMeetingCoachMinutes>[]:
        mandateMinutes.where((m)=>
          m.companyId==widget.companyId &&
          (m.payload['mandateId']??'').toString()==mandate.id).map((m)=>
            CipaMeetingCoachMinutes(
              meetingId:(m.payload['meetingId']??'').toString(),
              status:m.status,
            )),
      actions:mandate==null?const <CipaMeetingCoachAction>[]:
        mandateActions.where((a)=>
          a.companyId==widget.companyId &&
          (a.payload['mandateId']??'').toString()==mandate.id).map((a)=>
            CipaMeetingCoachAction(
              status:a.status,dueDate:a.dueDate,
              responsible:(a.payload['responsible']??'').toString(),
            )),
    );
  }

  Future<void> _cipaMeetingCoachNavigate(
      String target,String? meetingId) async {
    if(busy||!mounted)return;
    if(target=='mandate') {
      DefaultTabController.of(context).animateTo(1);
      return;
    }
    if(activeMandate==null) {
      _message('Ative um mandato da CIPA antes de continuar.');
      return;
    }
    if(target=='new_meeting') {
      await _cipaGuidedMeeting();
      return;
    }
    if(target=='meeting') {
      final options=mandateMeetings.where((m)=>
        m.id==meetingId &&
        m.companyId==widget.companyId &&
        (m.payload['mandateId']??'').toString()==activeMandate!.id).toList();
      if(options.length==1) {
        await _editMeeting(options.single);
        return;
      }
      DefaultTabController.of(context).animateTo(3);
      return;
    }
    final tab=target=='members'?2:target=='minutes'?4:
      target=='actions'?5:3;
    DefaultTabController.of(context).animateTo(tab);
  }


  Future<void> _cipaSuggestAgendaTheme() async {
    if(busy||!mounted)return;
    final mandate=activeMandate;
    if(mandate==null){
      _message('Ative um mandato da CIPA para preparar uma pauta.');
      return;
    }
    final open=mandateActions.where((action)=>
      action.companyId==widget.companyId &&
      (action.payload['mandateId']??'').toString()==mandate.id &&
      !const ['Resolvida','Concluída','Concluído','Cancelada','Arquivada']
        .contains(action.status)).toList();
    final overdue=open.where((a)=>a.dueDate!=null &&
      a.dueDate!.isBefore(DateTime.now())).length;
    final meeting=_cipaMeetingCoachSnapshot();
    var sector='Geral';
    String? chosenTitle;
    await showDialog<void>(context:context,builder:(dialog)=>
      StatefulBuilder(builder:(ctx,update){
        final suggested=CipaTopicAdvisor.suggest(
          sector:sector,openActions:open.length,overdueActions:overdue);
        final chosen=suggested.firstWhere(
          (s)=>s.title==chosenTitle,orElse:()=>suggested.first);
        return AlertDialog(
          title:const Text('Escolher tema para a pauta'),
          content:SizedBox(width:520,child:SingleChildScrollView(
            child:Column(
              crossAxisAlignment:CrossAxisAlignment.stretch,
              mainAxisSize:MainAxisSize.min,children:[
              const Text('Escolha o setor e um assunto sugerido. '
                'A CIPA decide o que será discutido.'),
              const SizedBox(height:12),
              DropdownButtonFormField<String>(
                isExpanded:true,value:sector,
                decoration:const InputDecoration(
                  labelText:'Ramo ou setor da empresa',
                  border:OutlineInputBorder()),
                items:CipaTopicAdvisor.sectors.map((name)=>
                  DropdownMenuItem(value:name,child:Text(name,
                    overflow:TextOverflow.ellipsis))).toList(),
                onChanged:(value)=>update((){
                  sector=value??'Geral';chosenTitle=null;
                }),
              ),
              const SizedBox(height:12),
              for(final suggestion in suggested)
                RadioListTile<String>(
                  contentPadding:EdgeInsets.zero,
                  title:Text(suggestion.title),
                  subtitle:Text(suggestion.reason),
                  value:suggestion.title,
                  groupValue:chosen.title,
                  onChanged:(value)=>update(()=>chosenTitle=value),
                ),
              const Divider(),
              const Text('Texto sugerido (editável no formulário de reunião)',
                style:TextStyle(fontWeight:FontWeight.w700)),
              const SizedBox(height:8),
              SelectableText(chosen.draftAgenda),
              const SizedBox(height:10),
              const Text('Isto é somente uma PROPOSTA de pauta. '
                'Não preenche uma ata, presenças, decisões ou assinaturas.',
                style:TextStyle(fontSize:12)),
            ]))),
          actions:[
            TextButton(onPressed:()=>Navigator.pop(dialog),
              child:const Text('Voltar')),
            FilledButton.icon(
              onPressed:()async{
                await Clipboard.setData(ClipboardData(text:chosen.draftAgenda));
                if(!ctx.mounted)return;
                Navigator.pop(dialog);
                if(mounted){
                  _message('Proposta copiada. Revise e cole no campo de pauta.');
                  await _cipaMeetingCoachNavigate(
                    meeting.selectedMeetingId==null?'new_meeting':'meeting',
                    meeting.selectedMeetingId);
                }
              },
              icon:const Icon(Icons.copy_outlined),
              label:const Text('Copiar pauta e abrir reunião')),
          ],
        );
      }));
  }

  Widget _cipaMeetingCoachCard() {
    final view=_cipaMeetingCoachSnapshot();
    return Card(child:ExpansionTile(
      initiallyExpanded:false,
      leading:const Icon(Icons.fact_check_outlined),
      title:const Text('Reunião assistida: antes e depois',
        style:TextStyle(fontWeight:FontWeight.w800)),
      subtitle:Text('${view.attentionCount} ponto(s) para conferir • '
        '${view.title}',maxLines:2,overflow:TextOverflow.ellipsis),
      children:[
        Padding(padding:const EdgeInsets.fromLTRB(16,0,16,8),
          child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
            Text(view.summary),
            const SizedBox(height:6),
            const Text('Roteiro baseado apenas no cadastro do mandato. '
              'Dados não localizados precisam de conferência; '
              'isso não prova descumprimento da NR-05. '
              'Ciência não equivale a presença ou assinatura.',
              style:TextStyle(fontSize:12)),
          ])),
        for(final item in view.steps.take(9))
          ListTile(
            leading:Icon(item.attention?
              Icons.warning_amber_outlined:Icons.info_outline,
              color:item.attention?Colors.deepOrange:null),
            title:Text(item.title,
              style:const TextStyle(fontWeight:FontWeight.w700)),
            subtitle:Text(item.detail),
            isThreeLine:true,
            trailing:const Icon(Icons.chevron_right),
            enabled:!busy,
            onTap:()=>_cipaMeetingCoachNavigate(
              item.target,view.selectedMeetingId),
          ),
        Padding(padding:const EdgeInsets.fromLTRB(16,6,16,8),
          child:SizedBox(width:double.infinity,child:OutlinedButton.icon(
            onPressed:busy||activeMandate==null?null:_cipaSuggestAgendaTheme,
            icon:const Icon(Icons.lightbulb_outline),
            label:const Text('Sugerir tema para a pauta da ata'),
          ))),
        Padding(padding:const EdgeInsets.fromLTRB(16,6,16,14),
          child:SizedBox(width:double.infinity,child:FilledButton.icon(
            onPressed:busy?null:()=>_cipaMeetingCoachNavigate(
              view.selectedMeetingId==null?
                (activeMandate==null?'mandate':'new_meeting'):'meeting',
              view.selectedMeetingId),
            icon:const Icon(Icons.edit_calendar_outlined),
            label:Text(view.nextAction),
          ))),
      ],
    ));
  }
}

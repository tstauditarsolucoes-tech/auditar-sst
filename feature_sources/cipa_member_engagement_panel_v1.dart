import 'package:flutter/material.dart';
import '../services/cipa_member_engagement.dart';
import '../services/cipa_member_portal_policy.dart';

/// Quatro portas de entrada simples para participação. Não cria ranking,
/// presença, certificado de NR-5 nem encerramento automático de ações.
class CipaMemberEngagementPanel extends StatefulWidget {
  const CipaMemberEngagementPanel({super.key,required this.view,
    this.offlineMode=false,this.onStartMission,this.onAskTst,
    this.onSeeQuestions,this.now});
  final CipaMemberView view;
  final bool offlineMode;
  final Future<void> Function(String category)? onStartMission;
  final Future<void> Function(String topic,String note)? onAskTst;
  final VoidCallback? onSeeQuestions;
  final DateTime? now;
  @override
  State<CipaMemberEngagementPanel> createState()=>
    _CipaMemberEngagementPanelState();
}

class _CipaMemberEngagementPanelState
    extends State<CipaMemberEngagementPanel> {
  bool _sending=false;
  DateTime get _now=>widget.now??DateTime.now();

  Future<void> _showLessons() async {
    await showDialog<void>(context:context,builder:(dialog)=>AlertDialog(
      title:const Text('Escola do Cipeiro'),
      content:SizedBox(width:430,child:SingleChildScrollView(
        child:Column(mainAxisSize:MainAxisSize.min,children:[
          const Text('Miniaulas gratuitas para apoiar a participação. '
            'Não substituem o treinamento obrigatório da NR-5.'),
          const SizedBox(height:12),
          for(final lesson in CipaMemberEngagement.lessons)
            ListTile(
              leading:const Icon(Icons.menu_book_outlined),
              title:Text(lesson.title),
              subtitle:const Text('Ler e responder uma pergunta'),
              trailing:const Icon(Icons.chevron_right),
              onTap:(){Navigator.pop(dialog);_showLesson(lesson);},
            ),
        ]))),
      actions:[TextButton(onPressed:()=>Navigator.pop(dialog),
        child:const Text('Fechar'))],
    ));
  }

  Future<void> _showLesson(CipaMiniLesson lesson) async {
    int? selected;
    await showDialog<void>(context:context,
      builder:(dialog)=>StatefulBuilder(builder:(ctx,update)=>AlertDialog(
        title:Text(lesson.title),
        content:SizedBox(width:430,child:SingleChildScrollView(
          child:Column(
            crossAxisAlignment:CrossAxisAlignment.stretch,
            mainAxisSize:MainAxisSize.min,children:[
              Text(lesson.summary),
              const SizedBox(height:15),
              Text(lesson.question,style:const TextStyle(
                fontWeight:FontWeight.w700,fontSize:17)),
              const SizedBox(height:10),
              for(var i=0;i<lesson.choices.length;i++)Padding(
                padding:const EdgeInsets.only(bottom:7),
                child:OutlinedButton(
                  onPressed:selected==null?()=>update(()=>selected=i):null,
                  child:Align(alignment:Alignment.centerLeft,
                    child:Text(lesson.choices[i])))),
              if(selected!=null)...[
                const SizedBox(height:8),
                Text(selected==lesson.correctIndex?
                  'Você acertou!':'Veja a orientação correta:',
                  style:const TextStyle(fontWeight:FontWeight.w800)),
                Text(lesson.explanation),
                const Text('Aprendizado educativo, sem nota ou certificado.',
                  style:TextStyle(fontSize:12)),
              ],
            ]))),
        actions:[
          TextButton(onPressed:()=>Navigator.pop(dialog),
            child:const Text('Fechar')),
          if(selected!=null)FilledButton(
            onPressed:(){
              Navigator.pop(dialog);
              _showLessons();
            },child:const Text('Outras miniaulas')),
        ],
      )));
  }

  Future<void> _showImpact() async {
    final impact=CipaMemberEngagement.impact(widget.view,now:_now);
    await showDialog<void>(context:context,builder:(dialog)=>AlertDialog(
      title:const Text('Meu Impacto na Segurança'),
      content:SingleChildScrollView(child:Column(
        mainAxisSize:MainAxisSize.min,
        crossAxisAlignment:CrossAxisAlignment.start,children:[
          Text('Registros pessoais recebidos na última consulta: '
            '${impact.reports}',style:const TextStyle(fontSize:17)),
          const SizedBox(height:9),
          Text('Orientações técnicas disponíveis: '
            '${impact.technicalReplies}',
            style:const TextStyle(fontSize:17)),
          const SizedBox(height:9),
          Text('Tarefas atribuídas com status de conclusão: '
            '${impact.completedActions}',
            style:const TextStyle(fontSize:17)),
          const SizedBox(height:9),
          Text(impact.missionReported?
            'Já existe uma vistoria registrada sobre a missão deste mês.':
            'Nenhuma vistoria registrada para o tema deste mês.'),
          const SizedBox(height:12),
          const Text('Indicadores informativos da Central, não medem '
            'riscos eliminados, frequência ou mérito individual. '
            'Uma ação concluída é informada pela Central, não por este botão.'),
          if(widget.offlineMode)const Text(
            'Consulta offline: números podem estar desatualizados.',
            style:TextStyle(fontWeight:FontWeight.bold)),
        ])),
      actions:[TextButton(onPressed:()=>Navigator.pop(dialog),
        child:const Text('Entendi'))],
    ));
  }

  Future<void> _askTst() async {
    if(widget.offlineMode||widget.onAskTst==null){
      await showDialog<void>(context:context,builder:(dialog)=>AlertDialog(
        title:const Text('Pergunte ao TST'),
        content:const Text('Para enviar uma dúvida, entre com internet '
          'na sua conta individual. Não há envio de perguntas offline. '
          'Em situação urgente, avise imediatamente o responsável local.'),
        actions:[TextButton(onPressed:()=>Navigator.pop(dialog),
          child:const Text('Entendi'))],
      ));
      return;
    }
    final chosen=await showDialog<MapEntry<String,String>>(
      context:context,builder:(_)=>const _CipaAskTstDialog());
    if(chosen==null||!mounted)return;
    setState(()=>_sending=true);
    try {
      await widget.onAskTst!(chosen.key,chosen.value);
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content:Text('Dúvida recebida para análise. '
          'Acompanhe em Minhas dúvidas ao TST.')));
    }catch(_){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content:Text('Envio não confirmado. Confira '
          'Minhas dúvidas antes de tentar novamente.')));
    }finally{if(mounted)setState(()=>_sending=false);}
  }

  Widget _action(String label,IconData icon,VoidCallback? tap)=>
    SizedBox(width:double.infinity,height:56,child:OutlinedButton.icon(
      onPressed:_sending?null:tap,icon:Icon(icon,size:24),
      label:Text(label,style:const TextStyle(
        fontWeight:FontWeight.w700,fontSize:16))));

  @override Widget build(BuildContext context){
    final mission=CipaMemberEngagement.missionFor(_now);
    final impact=CipaMemberEngagement.impact(widget.view,now:_now);
    return Card(child:Padding(padding:const EdgeInsets.all(16),
      child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
        Text('Participe da sua CIPA',
          style:Theme.of(context).textTheme.titleLarge?.copyWith(
            fontWeight:FontWeight.w800)),
        const SizedBox(height:8),
        const Text('Pequenas ações ajudam a prevenir acidentes. '
          'Você não precisa conhecer todas as normas para colaborar.'),
        const SizedBox(height:14),
        Row(children:[const Icon(Icons.flag_outlined),
          const SizedBox(width:8),
          Expanded(child:Text('Missão do mês • ${_now.month}/${_now.year}',
            style:const TextStyle(fontWeight:FontWeight.w700,fontSize:17)))]),
        const SizedBox(height:6),
        Text(mission.title,style:const TextStyle(
          fontWeight:FontWeight.w700,fontSize:16)),
        Text(mission.description),
        const SizedBox(height:8),
        if(impact.missionReported)
          const Text('Já existe relato sobre este tema neste mês. '
            'A análise técnica é independente da missão.'),
        if(widget.onStartMission!=null)
          FilledButton.icon(
            onPressed:_sending?null:()=>widget.onStartMission!(
              mission.category),
            icon:const Icon(Icons.play_arrow_outlined),
            label:const Text('Começar missão')),
        const SizedBox(height:10),
        _action('Escola do Cipeiro',Icons.school_outlined,_showLessons),
        const SizedBox(height:9),
        _action('Pergunte ao TST',Icons.question_answer_outlined,_askTst),
        const SizedBox(height:9),
        _action('Meu Impacto na Segurança',
          Icons.insights_outlined,_showImpact),
        if(widget.onSeeQuestions!=null)...[
          const SizedBox(height:9),
          TextButton.icon(
            onPressed:widget.onSeeQuestions,
            icon:const Icon(Icons.mark_chat_read_outlined),
            label:const Text('Ver minhas dúvidas e respostas')),
        ],
        if(widget.offlineMode)const Padding(
          padding:EdgeInsets.only(top:8),
          child:Text('Offline: missão e aulas disponíveis. '
            'Perguntas ao TST exigem internet e não ficam em fila.',
            style:TextStyle(fontSize:13))),
      ])));
  }
}

/// O TextEditingController vive até o diálogo sair da árvore, evitando
/// o descarte prematuro durante a animação de fechamento do Navigator.
class _CipaAskTstDialog extends StatefulWidget {
  const _CipaAskTstDialog();
  @override State<_CipaAskTstDialog> createState()=>_CipaAskTstDialogState();
}

class _CipaAskTstDialogState extends State<_CipaAskTstDialog> {
  final input=TextEditingController();
  String topic=CipaMemberEngagement.questionTopics.first;
  @override void dispose(){input.dispose();super.dispose();}

  @override Widget build(BuildContext context)=>AlertDialog(
    title:const Text('Pergunte ao TST'),
    content:SizedBox(width:430,child:SingleChildScrollView(
      child:Column(mainAxisSize:MainAxisSize.min,children:[
        const Text('A dúvida será enviada como relato para '
          'análise da equipe SST; não é chat em tempo real. '
          'Evite informar nomes e dados de saúde.'),
        const SizedBox(height:12),
        DropdownButtonFormField<String>(
          initialValue:topic,isExpanded:true,
          decoration:const InputDecoration(labelText:'Assunto'),
          items:[for(final value in CipaMemberEngagement.questionTopics)
            DropdownMenuItem(value:value,child:Text(value,
              overflow:TextOverflow.ellipsis))],
          onChanged:(value){if(value!=null)setState(()=>topic=value);},
        ),
        const SizedBox(height:12),
        TextField(controller:input,maxLength:950,maxLines:4,
          onChanged:(_)=>setState((){}),
          decoration:const InputDecoration(
            labelText:'Escreva sua dúvida',
            hintText:'O que você precisa saber?',
            border:OutlineInputBorder())),
        const Text('Em perigo imediato, comunique a chefia/local '
          'responsável sem aguardar resposta no aplicativo.',
          style:TextStyle(fontSize:12)),
      ]))),
    actions:[
      TextButton(onPressed:()=>Navigator.pop(context),
        child:const Text('Cancelar')),
      FilledButton(onPressed:input.text.trim().length<8?null:()=>
        Navigator.pop(context,MapEntry(topic,input.text.trim())),
        child:const Text('Enviar dúvida')),
    ],
  );
}

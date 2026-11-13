
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/cipa_member_identity.dart';
import '../services/cipa_member_role_meetings.dart';
import '../services/cipa_member_portal_policy.dart';

/// Guia pessoal somente de leitura: não cadastra cargo ou valida ata.
class CipaMeetingRoleCoachPanel extends StatelessWidget {
  const CipaMeetingRoleCoachPanel({super.key,required this.profile,
    this.meetings=const [],this.onSendMinutes,this.onListMinutes});
  final CipaMemberAccessProfile profile;
  final List<CipaMemberItem> meetings;
  final Future<void> Function(String meetingId,String content)? onSendMinutes;
  final Future<List<Map<String,dynamic>>> Function()? onListMinutes;

  void _roleDialog(BuildContext context){
    showDialog<void>(context:context,builder:(ctx)=>AlertDialog(
      title:Text('Minha função: '+profile.cipaRole),
      content:SingleChildScrollView(child:Column(
        mainAxisSize:MainAxisSize.min,
        crossAxisAlignment:CrossAxisAlignment.start,children:[
          Text(CipaRoleGuide.summary(profile.cipaRole),
            style:const TextStyle(fontSize:17)),
          const SizedBox(height:12),
          Text(CipaRoleGuide.hint(profile.cipaRole)),
          const SizedBox(height:12),
          const Text('Por onde começo?',style:TextStyle(
            fontSize:17,fontWeight:FontWeight.w800)),
          for(var i=0;i<CipaRoleGuide.firstSteps(profile.cipaRole).length;i++)
            ListTile(
              leading:CircleAvatar(child:Text((i+1).toString())),
              title:Text(CipaRoleGuide.firstSteps(profile.cipaRole)[i]),
            ),
          const Text('Seu cargo e representação são informados pela Central. '
            'Para corrigir, peça ao administrador para alterar o '
            'cadastro oficial da CIPA. Este guia não muda permissões.',
            style:TextStyle(fontSize:12)),
        ])),
      actions:[FilledButton(onPressed:()=>Navigator.pop(ctx),
        child:const Text('Entendi'))],
    ));
  }

  void _meetingGuide(BuildContext context){
    showDialog<void>(context:context,builder:(ctx)=>
      _CipaMeetingGuideDialog(meetings:meetings,
        onSendMinutes:onSendMinutes));
  }

  void _seeMinutes(BuildContext context){
    if(onListMinutes==null)return;
    showDialog<void>(context:context,builder:(ctx)=>AlertDialog(
      title:const Text('Minhas minutas em revisão'),
      content:SizedBox(width:420,height:300,child:FutureBuilder<
        List<Map<String,dynamic>>>(
        future:onListMinutes!(),builder:(context,snapshot){
          if(!snapshot.hasData&&snapshot.connectionState!=
             ConnectionState.done)return const Center(
               child:CircularProgressIndicator());
          if(snapshot.hasError)return const Text(
            'Não foi possível consultar suas minutas.');
          final rows=snapshot.data??const <Map<String,dynamic>>[];
          if(rows.isEmpty)return const Text(
            'Nenhuma minuta enviada para revisão da Central.');
          return ListView(children:[for(final item in rows)ListTile(
            leading:const Icon(Icons.description_outlined),
            title:Text('Reunião: '+(item['meetingId']??'').toString()),
            subtitle:Text((item['status']??'Recebida').toString()+
              '\n'+(item['reviewNote']??'').toString()),
            isThreeLine:true,
          )]);
        })),
      actions:[FilledButton(onPressed:()=>Navigator.pop(ctx),
        child:const Text('Fechar'))],
    ));
  }

  @override Widget build(BuildContext context)=>Card(
    child:Padding(padding:const EdgeInsets.all(14),child:Column(
      crossAxisAlignment:CrossAxisAlignment.stretch,children:[
        Text('Reuniões e funções da CIPA',
          style:Theme.of(context).textTheme.titleLarge?.copyWith(
            fontWeight:FontWeight.w800)),
        const SizedBox(height:7),
        Text('Seu papel: '+profile.cipaRole,
          style:const TextStyle(fontSize:17)),
        const SizedBox(height:7),
        const Text('Aprenda o que fazer na reunião e como começar '
          'a minuta da ata, mesmo sem experiência.'),
        const SizedBox(height:12),
        OutlinedButton.icon(
          icon:const Icon(Icons.badge_outlined),
          onPressed:()=>_roleDialog(context),
          label:const Text('Entender minha função')),
        const SizedBox(height:10),
        FilledButton.icon(
          icon:const Icon(Icons.menu_book_outlined),
          onPressed:()=>_meetingGuide(context),
          label:const Text('Aprender reunião e ata')),
        if(onListMinutes!=null)...[
          const SizedBox(height:8),
          OutlinedButton.icon(
            onPressed:()=>_seeMinutes(context),
            icon:const Icon(Icons.history_edu_outlined),
            label:const Text('Ver minhas minutas na Central')),
        ],
      ],
    )),
  );
}

/// Etapas simuladas: jamais registra início oficial de reunião.
class _CipaMeetingGuideDialog extends StatefulWidget {
  const _CipaMeetingGuideDialog({required this.meetings,
    required this.onSendMinutes});
  final List<CipaMemberItem> meetings;
  final Future<void> Function(String meetingId,String content)? onSendMinutes;
  @override State<_CipaMeetingGuideDialog> createState()=>
    _CipaMeetingGuideDialogState();
}
class _CipaMeetingGuideDialogState extends State<_CipaMeetingGuideDialog>{
  int page=0;
  static const _headings=[
    '1. Antes da reunião',
    '2. Como abrir a reunião',
    '3. Durante a conversa',
    '4. Como começar a ata',
    '5. Finalizar e conferir',
  ];
  static const _texts=[
    'Confira o calendário, dia, horário, local e pauta; o presidente '
      'convoca os membros. As reuniões ordinárias são normalmente '
      'mensais, observada a exceção prevista para determinadas '
      'ME/EPP de graus de risco 1 e 2.',
    'O presidente (ou vice, quando substituir o presidente) '
      'cumprimenta os presentes e apresenta a pauta. '
      'Confira os participantes de verdade; convocação ou ciência '
      'não confirmam presença.',
    'Debatam situações observadas, ações pendentes e sugestões. '
      'Registrem o que foi decidido, quem acompanhará e prazos. '
      'Nenhum participante precisa inventar informações para a ata.',
    'Os integrantes designam o secretário desta reunião. Ele anota '
      'data, local, presentes reais, pauta, discussões e decisões. '
      'O rascunho precisa de conferência; não é ata oficial.',
    'Confiram o texto com os presentes e providenciem as assinaturas. '
      'As atas devem ser disponibilizadas aos membros e as decisões '
      'comunicadas aos trabalhadores. O app educativo não assina '
      'nem publica documentos.',
  ];
  @override Widget build(BuildContext context)=>AlertDialog(
    title:const Text('Como conduzir uma reunião'),
    content:SizedBox(width:430,child:SingleChildScrollView(
      child:Column(
        crossAxisAlignment:CrossAxisAlignment.stretch,
        mainAxisSize:MainAxisSize.min,children:[
          Text('Etapa '+(page+1).toString()+' de 5',
            style:const TextStyle(fontWeight:FontWeight.w700)),
          const SizedBox(height:10),
          Text(_headings[page],style:const TextStyle(
            fontSize:19,fontWeight:FontWeight.w800)),
          const SizedBox(height:10),
          Text(_texts[page],style:const TextStyle(fontSize:17)),
          const SizedBox(height:16),
          if(page==1)const Card(child:Padding(
            padding:EdgeInsets.all(10),
            child:Text('Sugestão de abertura: “Bom dia. Vamos iniciar '
              'a reunião da CIPA. Confirmaremos os presentes e '
              'apresentaremos os assuntos da pauta.”'))),
          if(page==3)const Text('A ata é iniciada apenas com os '
            'dados reais do encontro. A responsabilidade pela '
            'conferência e assinatura permanece com os participantes.'),
        ]))),
    actions:[
      TextButton(onPressed:()=>Navigator.pop(context),
        child:const Text('Fechar')),
      if(page>0)OutlinedButton(
        onPressed:()=>setState(()=>page--),
        child:const Text('Voltar')),
      if(page<_headings.length-1)FilledButton(
        onPressed:()=>setState(()=>page++),
        child:const Text('Próxima etapa')),
      if(page==_headings.length-1)FilledButton(
        onPressed:(){
          Navigator.pop(context);
          showDialog<void>(context:context,
            builder:(ctx)=>_CipaMinutesPracticeDialog(
              meetings:widget.meetings,
              onSendMinutes:widget.onSendMinutes));
        },
        child:const Text('Montar rascunho da ata')),
    ],
  );
}

class _CipaMinutesPracticeDialog extends StatefulWidget{
  const _CipaMinutesPracticeDialog({required this.meetings,
    required this.onSendMinutes});
  final List<CipaMemberItem> meetings;
  final Future<void> Function(String meetingId,String content)? onSendMinutes;
  @override State<_CipaMinutesPracticeDialog> createState()=>
    _CipaMinutesPracticeDialogState();
}
class _CipaMinutesPracticeDialogState
    extends State<_CipaMinutesPracticeDialog>{
  final place=TextEditingController(),agenda=TextEditingController(),
    discussion=TextEditingController(),decisions=TextEditingController(),
    secretary=TextEditingController(),members=TextEditingController(),
    assignments=TextEditingController();
  DateTime? meetingDate;
  String meetingType='Ordinária',message='';
  String? generated,selectedMeetingId;
  bool submitting=false,submitted=false;
  @override void dispose(){
    for(final ctrl in [place,agenda,discussion,decisions,secretary,
      members,assignments])ctrl.dispose();
    super.dispose();
  }
  Widget _field(String title,TextEditingController ctrl,{int max=600})=>
    Padding(padding:const EdgeInsets.only(bottom:10),child:TextField(
      controller:ctrl,maxLength:max,maxLines:2,
      decoration:InputDecoration(labelText:title,
        border:const OutlineInputBorder()),
    ));

  void _generate(){
    try{
      if(meetingDate==null)throw ArgumentError(
        'Escolha a data real da reunião.');
      final text=CipaMinutesPractice(date:meetingDate!,
        place:place.text,agenda:agenda.text,
        discussion:discussion.text,decisions:decisions.text,
        secretary:secretary.text,presentMembers:members.text,
        responsibleAndDue:assignments.text,meetingType:meetingType)
        .build();
      setState((){generated=text;message='';});
    }catch(e){setState((){
      generated=null;message=e.toString().replaceFirst(
        'Invalid argument(s): ','');
    });}
  }

  Future<void> _submitCentral()async{
    final send=widget.onSendMinutes;
    if(send==null||selectedMeetingId==null||generated==null||submitting)return;
    final confirmed=await showDialog<bool>(context:context,builder:(dialog)=>
      AlertDialog(
        title:const Text('Enviar minuta para revisão?'),
        content:const Text('A minuta será encaminhada à Central para '
          'conferência pela equipe autorizada. Não registra presença, '
          'assinatura ou ata oficial. Confira os dados antes de enviar.'),
        actions:[
          TextButton(onPressed:()=>Navigator.pop(dialog,false),
            child:const Text('Voltar')),
          FilledButton(onPressed:()=>Navigator.pop(dialog,true),
            child:const Text('Confirmar envio')),
        ]));
    if(confirmed!=true||!mounted)return;
    setState((){submitting=true;message='';});
    try{
      await send(selectedMeetingId!,generated!);
      if(mounted)setState((){submitted=true;
        message='Minuta recebida para revisão da Central. '
          'Ainda não é uma ata assinada.';});
    }catch(_){if(mounted)setState(()=>message=
      'Envio não confirmado. Consulte Minhas minutas antes de tentar novamente.');}
    finally{if(mounted)setState(()=>submitting=false);}
  }

  @override Widget build(BuildContext context)=>AlertDialog(
    title:const Text('Como iniciar uma ata — exercício'),
    content:SizedBox(width:430,height:480,child:SingleChildScrollView(
      child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
        const Text('Preencha apenas o que realmente ocorreu. '
          'Este texto é um modelo educativo, não uma ata assinada '
          'nem um registro salvo na Central.',
          style:TextStyle(fontWeight:FontWeight.w700)),
        if(widget.onSendMinutes!=null)...[
          const SizedBox(height:12),
          if(widget.meetings.isEmpty)
            const Text('Nenhuma reunião vinculada à sua conta '
              'está disponível para enviar minuta à Central.'),
          if(widget.meetings.isNotEmpty)DropdownButtonFormField<String>(
            isExpanded:true,value:selectedMeetingId,
            decoration:const InputDecoration(
              labelText:'Reunião vinculada à sua CIPA'),
            items:widget.meetings.map((meeting)=>DropdownMenuItem(
              value:meeting.id,child:Text(meeting.title,
                overflow:TextOverflow.ellipsis))).toList(),
            onChanged:(v)=>setState(()=>selectedMeetingId=v)),
        ],
        const SizedBox(height:12),
        DropdownButtonFormField<String>(
          initialValue:meetingType,
          decoration:const InputDecoration(labelText:'Tipo de reunião'),
          items:const [
            DropdownMenuItem(value:'Ordinária',child:Text('Ordinária')),
            DropdownMenuItem(value:'Extraordinária',child:Text('Extraordinária')),
          ],onChanged:(value){if(value!=null)setState(()=>meetingType=value);}),
        const SizedBox(height:12),
        OutlinedButton.icon(
          onPressed:()async{
            final chosen=await showDatePicker(context:context,
              initialDate:meetingDate??DateTime.now(),
              firstDate:DateTime(2020),lastDate:DateTime.now());
            if(chosen!=null&&mounted)setState(()=>meetingDate=chosen);
          },icon:const Icon(Icons.date_range_outlined),
          label:Text(meetingDate==null?'Escolher data real da reunião':
            'Data: '+meetingDate!.day.toString()+'/' +
              meetingDate!.month.toString()+'/' +
              meetingDate!.year.toString())),
        const SizedBox(height:10),
        _field('Local da reunião',place,max:120),
        _field('Assuntos da pauta',agenda),
        _field('O que foi realmente discutido?',discussion),
        _field('Decisões e encaminhamentos reais',decisions),
        _field('Secretário designado nesta reunião (se souber)',secretary,
          max:120),
        _field('Pessoas realmente presentes (conferir lista)',members),
        _field('Responsáveis e prazos (se houver)',assignments),
        if(message.isNotEmpty)Text(message,
          style:TextStyle(color:Theme.of(context).colorScheme.error)),
        if(generated!=null)...[
          const SizedBox(height:12),
          const Text('Prévia do rascunho educativo:',
            style:TextStyle(fontWeight:FontWeight.w800)),
          SelectableText(generated!),
        ],
      ]))),
    actions:[
      TextButton(onPressed:()=>Navigator.pop(context),
        child:const Text('Fechar')),
      FilledButton(onPressed:_generate,
        child:const Text('Ver rascunho')),
      if(generated!=null&&widget.onSendMinutes!=null)
        FilledButton.icon(onPressed:submitting||submitted||
          selectedMeetingId==null?null:_submitCentral,
          icon:const Icon(Icons.cloud_upload_outlined),
          label:Text(submitted?'Minuta enviada à Central':
            'Enviar minuta para revisão')),
      if(generated!=null)OutlinedButton.icon(
        onPressed:()async{
          await Clipboard.setData(ClipboardData(text:generated!));
          if(mounted)ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content:Text('Rascunho copiado para conferência. '
              'Não é ata oficial e não registra presença.')));
        },icon:const Icon(Icons.copy),label:const Text('Copiar')),
    ],
  );
}

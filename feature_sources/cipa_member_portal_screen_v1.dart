import 'package:flutter/material.dart';
import '../services/cipa_member_portal_policy.dart';
import '../widgets/cipa_member_access_header.dart';
import '../widgets/cipa_member_guided_inspection.dart';

/// UI do membro, independente da gestão interna. Este widget recebe somente
/// dados previamente filtrados no servidor; não consulta o banco de técnicos.
/// Sem sessão autorizada, o portal fica fechado (fail closed).
class CipaMemberPortalScreen extends StatefulWidget {
  const CipaMemberPortalScreen({
    super.key, required this.companyName, required this.mandateLabel,
    this.view, this.sessionVerified=false,
    this.onRefresh, this.onLogout, this.onAcknowledgeMeeting,
    this.onReportProgress, this.onRequestSupport, this.onObserve,
  });
  final String companyName,mandateLabel;
  final CipaMemberView? view;
  final bool sessionVerified;
  final Future<void> Function()? onRefresh,onLogout;
  final Future<void> Function(String id)? onAcknowledgeMeeting;
  final Future<void> Function(String id,String note)? onReportProgress,onRequestSupport;
  final Future<void> Function(String place,String note)? onObserve;

  @override
  State<CipaMemberPortalScreen> createState() => _CipaMemberPortalScreenState();
}
class _CipaMemberPortalScreenState extends State<CipaMemberPortalScreen> {
  bool busy=false;
  String error='';
  final GlobalKey _meetingsSection=GlobalKey();
  final GlobalKey _tasksSection=GlobalKey();

  void _goTo(GlobalKey section) {
    final target=section.currentContext;
    if(target==null)return;
    Scrollable.ensureVisible(target,
      duration:const Duration(milliseconds:300),
      curve:Curves.easeInOut,
      alignment:0.08,
    );
  }

  Widget _largeAction({
    required String title,required IconData icon,
    required VoidCallback? onPressed,bool primary=false,
  })=>SizedBox(
    width:double.infinity,
    height:58,
    child:primary
      ?FilledButton.icon(
        onPressed:onPressed,icon:Icon(icon,size:25),
        label:Text(title,style:const TextStyle(fontSize:17,
          fontWeight:FontWeight.w700)),
      )
      :OutlinedButton.icon(
        onPressed:onPressed,icon:Icon(icon,size:25),
        label:Text(title,style:const TextStyle(fontSize:17,
          fontWeight:FontWeight.w700)),
      ),
  );

  Future<void> _submit(Future<void> Function() call) async {
    if(busy||!widget.sessionVerified) return;
    setState(() {busy=true;error='';});
    try {
      await call();
      if(widget.onRefresh!=null)await widget.onRefresh!();
    } catch (_) {
      if(mounted) setState(()=>error='Não foi possível enviar. Confira a conexão '
        'e tente novamente, sem repetir registros já enviados.');
    } finally {
      if(mounted)setState(()=>busy=false);
    }
  }

  Future<String?> _askNote(String title,String hint) async {
    final controller=TextEditingController();
    final result=await showDialog<String>(context:context,
      builder:(dialog)=>StatefulBuilder(builder:(context,update)=>AlertDialog(
        title:Text(title),
        content:SingleChildScrollView(child:Column(
          mainAxisSize:MainAxisSize.min,children:[
          Text(hint),const SizedBox(height:12),
          TextField(controller:controller,maxLength:1000,maxLines:4,
            onChanged:(_)=>update((){}),
            decoration:const InputDecoration(border:OutlineInputBorder(),
              labelText:'Descreva com suas palavras')),
        ])),
        actions:[
          TextButton(onPressed:()=>Navigator.pop(dialog),
            child:const Text('Cancelar')),
          FilledButton(onPressed:controller.text.trim().length<8?null:
            ()=>Navigator.pop(dialog,controller.text.trim()),
            child:const Text('Enviar para avaliação')),
        ],
      )));
    controller.dispose();
    return result;
  }

  Future<void> _newObservation() async {
    if(widget.onObserve==null)return;
    final place=TextEditingController(),text=TextEditingController();
    final save=await showDialog<bool>(context:context,builder:(dialog)=>
      StatefulBuilder(builder:(context,update)=>AlertDialog(
        title:const Text('Registrar situação observada'),
        content:SingleChildScrollView(child:Column(
          mainAxisSize:MainAxisSize.min,children:[
          const Text('Não se aproxime de um perigo para registrar. '
            'A equipe técnica analisará a informação.'),
          const SizedBox(height:8),
          TextField(controller:place,maxLength:120,
            onChanged:(_)=>update((){}),
            decoration:const InputDecoration(labelText:'Local')),
          TextField(controller:text,maxLength:1200,maxLines:4,
            onChanged:(_)=>update((){}),
            decoration:const InputDecoration(labelText:'O que você observou?')),
        ])),
        actions:[
          TextButton(onPressed:()=>Navigator.pop(dialog,false),
            child:const Text('Cancelar')),
          FilledButton(onPressed:place.text.trim().isEmpty||
            text.text.trim().length<8?null:()=>Navigator.pop(dialog,true),
            child:const Text('Enviar observação')),
        ],
      )));
    final p=place.text.trim(),v=text.text.trim();
    place.dispose();text.dispose();
    if(save==true&&mounted)await _submit(()=>widget.onObserve!(p,v));
  }

  Future<void> _guidedInspection() async {
    if(!widget.sessionVerified || busy || widget.onObserve==null)return;
    await showDialog<bool>(
      context:context,
      barrierDismissible:false,
      builder:(_)=>CipaGuidedInspectionDialog(
        onSend:(place,note) async {
          // Mantém o mesmo fluxo autorizado de observação já existente.
          // Sem confirmação de servidor, o diálogo permanece aberto.
          await widget.onObserve!(place,note);
          if(widget.onRefresh!=null)await widget.onRefresh!();
        },
      ),
    );
  }

  Widget _section(String title,IconData icon,List<CipaMemberItem> items,{
    Widget Function(CipaMemberItem)? actions,String empty='Nenhum registro disponível.',
  })=>Card(child:ExpansionTile(
    initiallyExpanded:items.isNotEmpty,
    leading:Icon(icon),
    title:Text('$title (${items.length})',
      style:const TextStyle(fontWeight:FontWeight.w700)),
    children:[
      if(items.isEmpty)ListTile(title:Text(empty)),
      for(final item in items)
        Column(children:[
          ListTile(title:Text(item.title),
            subtitle:Text([
              if(item.description.isNotEmpty)item.description,
              if(item.status.isNotEmpty)'Situação: ${item.status}',
              if(item.date!=null)'Data: ${item.date!.day}/${item.date!.month}/${item.date!.year}',
            ].join('\n'))),
          if(actions!=null)Padding(
            padding:const EdgeInsets.fromLTRB(12,0,12,12),
            child:actions(item)),
        ]),
    ],
  ));

  @override
  Widget build(BuildContext context) {
    final view=widget.view;
    if(!widget.sessionVerified || view==null) {
      return Scaffold(appBar:AppBar(title:const Text('Minha CIPA')),
        body:const SafeArea(child:Center(child:Padding(
          padding:EdgeInsets.all(24),
          child:Column(mainAxisSize:MainAxisSize.min,children:[
            Icon(Icons.lock_outline,size:48),
            SizedBox(height:14),
            Text('Acesso pessoal não liberado',
              textAlign:TextAlign.center,
              style:TextStyle(fontSize:20,fontWeight:FontWeight.w800)),
            SizedBox(height:10),
            Text('Somente uma sessão individual validada pela Central '
              'permite abrir o portal. Não use a conta do técnico ou administrador.',
              textAlign:TextAlign.center),
          ]),
        ))));
    }
    final profile=view.profile;
    return Scaffold(
      appBar:AppBar(title:const Text('Minha CIPA'),actions:[
        if(widget.onRefresh!=null)IconButton(
          onPressed:busy?null:()=>_submit(widget.onRefresh!),
          tooltip:'Atualizar',icon:const Icon(Icons.refresh)),
        if(widget.onLogout!=null)IconButton(
          onPressed:busy?null:()=>_submit(widget.onLogout!),
          tooltip:'Sair da conta',icon:const Icon(Icons.logout)),
      ]),
      body:SafeArea(child:ListView(
        padding:const EdgeInsets.fromLTRB(12,12,12,64),children:[
        CipaMemberAccessHeader(profile:profile,
          companyName:widget.companyName,mandateLabel:widget.mandateLabel),
        Card(child:Padding(padding:const EdgeInsets.all(16),
          child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
            Text('O que você quer fazer hoje?',
              style:Theme.of(context).textTheme.titleLarge
                ?.copyWith(fontWeight:FontWeight.w800)),
            const SizedBox(height:5),
            const Text('Toque em uma opção. Não precisa conhecer a NR.',
              style:TextStyle(fontSize:16)),
            const SizedBox(height:14),
            _largeAction(
              title:'Ver reuniões',icon:Icons.event_outlined,
              onPressed:busy?null:()=>_goTo(_meetingsSection),
              primary:true,
            ),
            const SizedBox(height:10),
            _largeAction(
              title:'Minhas tarefas',icon:Icons.fact_check_outlined,
              onPressed:busy?null:()=>_goTo(_tasksSection),
              primary:true,
            ),
            if(widget.onObserve!=null)...[
              const SizedBox(height:10),
              _largeAction(
                title:'Fazer vistoria orientada',
                icon:Icons.fact_check_outlined,
                onPressed:busy?null:_guidedInspection,
              ),
              const SizedBox(height:10),
              _largeAction(
                title:'Avisar uma situação',icon:Icons.edit_note_outlined,
                onPressed:busy?null:_newObservation,
              ),
            ],
            const SizedBox(height:10),
            Text('Você tem '+
              view.pendingActions.toString()+' tarefa(s) em acompanhamento.',
              style:const TextStyle(fontSize:15)),
            const SizedBox(height:4),
            const Text('O técnico ou responsável confere os relatos '
              'e valida as ações. Você pode pedir ajuda a qualquer momento.',
              style:TextStyle(fontSize:14)),
          ]))),
        if(busy)const LinearProgressIndicator(),
        if(error.isNotEmpty)Padding(
          padding:const EdgeInsets.all(12),
          child:Text(error,style:TextStyle(color:
            Theme.of(context).colorScheme.error))),
        KeyedSubtree(key:_meetingsSection,
          child:_section('Convocações e reuniões',Icons.event_outlined,view.meetings,
          empty:'Nenhuma convocação liberada para você.',
          actions:(item)=>Align(alignment:Alignment.centerRight,
            child:widget.onAcknowledgeMeeting!=null &&
                 CipaMemberPortalRules.canAcknowledge(profile,item)
              ?TextButton.icon(
                onPressed:busy?null:()=>_submit(
                  ()=>widget.onAcknowledgeMeeting!(item.id)),
                icon:const Icon(Icons.mark_email_read_outlined),
                label:const Text('Confirmar ciência do aviso'))
              :const SizedBox.shrink()))),
        const Padding(padding:EdgeInsets.fromLTRB(16,0,16,10),
          child:Text('Ciência não é presença na reunião nem assinatura da ata.',
            style:TextStyle(fontSize:12))),
        KeyedSubtree(key:_tasksSection,
          child:_section('Minhas tarefas',Icons.task_alt_outlined,view.myActions,
          empty:'Não há ação atribuída ao seu cadastro individual.',
          actions:(item)=>Wrap(spacing:8,runSpacing:8,children:[
            if(widget.onReportProgress!=null &&
               CipaMemberPortalRules.canReportAction(profile,item))
              OutlinedButton.icon(
                onPressed:busy?null:() async {
                  final note=await _askNote('Informar andamento',
                    'Descreva o que mudou. A equipe técnica vai conferir.');
                  if(note!=null&&mounted)await _submit(
                    ()=>widget.onReportProgress!(item.id,note));
                },icon:const Icon(Icons.edit_note_outlined),
                label:const Text('Informar andamento')),
            if(widget.onRequestSupport!=null &&
               CipaMemberPortalRules.canReportAction(profile,item))
              TextButton.icon(
                onPressed:busy?null:() async {
                  final note=await _askNote('Solicitar apoio',
                    'Conte o que está impedindo sua tarefa.');
                  if(note!=null&&mounted)await _submit(
                    ()=>widget.onRequestSupport!(item.id,note));
                },icon:const Icon(Icons.help_outline),
                label:const Text('Preciso de apoio')),
          ]))),
        Card(child:ExpansionTile(
          initiallyExpanded:false,
          leading:const Icon(Icons.more_horiz,size:28),
          title:const Text('Mais informações',
            style:TextStyle(fontSize:17,fontWeight:FontWeight.w700)),
          subtitle:const Text('Avisos, treinamentos, documentos e lembretes'),
          children:[
        _section('Avisos',Icons.notifications_none_outlined,view.notices),
        _section('Meu treinamento',Icons.school_outlined,view.trainings),
        _section('Documentos liberados',Icons.folder_open_outlined,view.documents),
        _section('Minhas observações',Icons.visibility_outlined,view.observations),
        _section('Lembretes',Icons.alarm_outlined,view.reminders),
          ],
        )),
        const Card(child:ExpansionTile(
          initiallyExpanded:false,
          leading:Icon(Icons.help_outline),
          title:Text('Como funciona a minha participação',
            style:TextStyle(fontSize:17,fontWeight:FontWeight.w700)),
          subtitle:Text('Guia rápido em três passos'),
          children:[
            ListTile(
              leading:CircleAvatar(child:Text('1')),
              title:Text('Recebi um aviso de reunião'),
              subtitle:Text('Leia data, local e pauta. Confirmar ciência '
                'significa que você viu o aviso, não que esteve presente.')),
            ListTile(
              leading:CircleAvatar(child:Text('2')),
              title:Text('Tenho uma tarefa'),
              subtitle:Text('Leia o que foi combinado. Use Informar andamento '
                'ou Preciso de apoio. O responsável precisa conferir a execução.')),
            ListTile(
              leading:CircleAvatar(child:Text('3')),
              title:Text('Observei uma situação'),
              subtitle:Text('Informe local e descrição com suas palavras, '
                'sem se expor a riscos. O envio não abre nem encerra '
                'automaticamente uma não conformidade.')),
          ],
        )),
        const Card(child:Padding(padding:EdgeInsets.all(14),
          child:Text('Como participar: observe sem se aproximar de perigos, '
            'registre local e situação, acompanhe sua tarefa e peça apoio. '
            'Não precisa indicar qual NR se aplica. A gestão é responsável '
            'pela avaliação técnica e conclusão de ações.'))),
      ])),
    );
  }
}

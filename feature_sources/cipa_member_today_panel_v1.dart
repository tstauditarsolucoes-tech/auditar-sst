import 'package:flutter/material.dart';
import '../services/cipa_member_today.dart';
import '../services/cipa_member_portal_policy.dart';

/// Cartão inicial por membro. Somente dados devolvidos pela Central ou
/// cache já autorizado; não publica nem assume que tarefa foi concluída.
class CipaTodayPanel extends StatelessWidget {
  const CipaTodayPanel({super.key,required this.view,
    required this.onSelect,this.offlineMode=false,this.now});
  final CipaMemberView view;
  final void Function(CipaTodayTarget) onSelect;
  final bool offlineMode;
  final DateTime? now;

  IconData _icon(CipaTodayTarget target){
    switch(target){
      case CipaTodayTarget.actions:return Icons.fact_check_outlined;
      case CipaTodayTarget.meetings:return Icons.event_available_outlined;
      case CipaTodayTarget.inspections:return Icons.assignment_outlined;
      case CipaTodayTarget.answers:return Icons.mark_chat_unread_outlined;
    }
  }
  @override Widget build(BuildContext context){
    final entries=CipaTodayPlan.fromView(view,now:now);
    return Card(
      child:Padding(padding:const EdgeInsets.all(14),
        child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
          Row(children:[
            const Icon(Icons.today,size:26),
            const SizedBox(width:9),
            Expanded(child:Text('O que preciso fazer hoje?',
              style:Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight:FontWeight.w800))),
          ]),
          const SizedBox(height:6),
          const Text('Tudo o que é importante para sua participação '
            'nesta semana, em uma só lista.'),
          if(offlineMode)const Text('Consulta offline: os dados podem '
            'estar desatualizados. Reconecte para confirmar seus prazos.',
            style:TextStyle(fontSize:12)),
          if(entries.isEmpty)const Padding(
            padding:EdgeInsets.symmetric(vertical:12),
            child:Text('Nenhuma tarefa, reunião, vistoria ou resposta '
              'urgente encontrada nesta consulta.')),
          for(final entry in entries)ListTile(
            contentPadding:EdgeInsets.zero,
            leading:CircleAvatar(child:Icon(_icon(entry.target))),
            title:Text(entry.title,
              style:const TextStyle(fontWeight:FontWeight.w700)),
            subtitle:Text(entry.hint),
            trailing:const Icon(Icons.chevron_right),
            onTap:()=>onSelect(entry.target),
          ),
        ])));
  }
}

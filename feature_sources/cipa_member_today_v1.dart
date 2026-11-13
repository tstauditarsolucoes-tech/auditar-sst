import 'cipa_member_portal_policy.dart';

/// Agenda pessoal em tempo de consulta; não gera presença nem conclui tarefas.
enum CipaTodayTarget { meetings, actions, inspections, answers }

class CipaTodayItem {
  const CipaTodayItem({required this.target,required this.title,
    required this.hint,this.due});
  final CipaTodayTarget target;
  final String title,hint;
  final DateTime? due;
}
class CipaTodayPlan {
  const CipaTodayPlan._();
  static List<CipaTodayItem> fromView(CipaMemberView view,{DateTime? now}) {
    final p=view.profile,clock=now??DateTime.now();
    final start=DateTime(clock.year,clock.month,clock.day);
    final weekEnd=start.add(const Duration(days:7));
    bool mine(CipaMemberItem i)=>
      i.companyId==p.companyId&&i.mandateId==p.mandateId&&
      i.assignedMemberId==p.memberId;
    final results=<CipaTodayItem>[];
    for(final i in view.meetings){
      final day=i.date??i.dueDate;
      if(!(mine(i)||i.visibleToAllMembers)||
        i.companyId!=p.companyId||i.mandateId!=p.mandateId||
        i.status!='Agendada'||day==null||day.isBefore(start)||
        !day.isBefore(weekEnd))continue;
      results.add(CipaTodayItem(target:CipaTodayTarget.meetings,
        title:'Reunião: '+i.title,
        hint:'Leia a pauta e confirme ciência, não presença.',due:day));
    }
    for(final i in view.myActions){
      if(!mine(i)||['Resolvida','Concluída'].contains(i.status))continue;
      final due=i.dueDate;
      final urgent=due==null||due.isBefore(weekEnd);
      if(!urgent)continue;
      results.add(CipaTodayItem(target:CipaTodayTarget.actions,
        title:'Tarefa: '+i.title,
        hint:due!=null&&due.isBefore(start)?
          'Prazo ultrapassado. Informe andamento ou peça apoio.':
          'Confira o prazo e informe seu andamento.',due:due));
    }
    for(final i in view.scheduledInspections){
      if(!mine(i)||i.status!='Programada')continue;
      final due=i.dueDate??i.date;
      if(due!=null&&due.isAfter(weekEnd))continue;
      results.add(CipaTodayItem(target:CipaTodayTarget.inspections,
        title:'Vistoria: '+i.title,
        hint:'Observe somente de um local seguro.',due:due));
    }
    for(final i in view.observations){
      if(!mine(i)||i.status!='Orientação enviada'||i.feedbackRead||
        i.feedback.trim().isEmpty||i.reviewId.isEmpty)continue;
      results.add(CipaTodayItem(target:CipaTodayTarget.answers,
        title:'Nova orientação do TST',
        hint:'Leia a resposta referente à sua vistoria.'));
    }
    const rank={
      CipaTodayTarget.answers:0,CipaTodayTarget.meetings:1,
      CipaTodayTarget.inspections:2,CipaTodayTarget.actions:3
    };
    results.sort((a,b){
      final r=rank[a.target]!.compareTo(rank[b.target]!);
      if(r!=0)return r;
      return (a.due??DateTime(9999)).compareTo(
        b.due??DateTime(9999));
    });
    return List.unmodifiable(results.take(12));
  }
}

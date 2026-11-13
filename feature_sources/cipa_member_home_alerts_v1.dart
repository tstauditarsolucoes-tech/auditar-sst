import 'cipa_member_portal_policy.dart';

/// Avisos calculados somente a partir do painel pessoal autorizado.
/// Nenhuma notificação push é emitida e dados de outra pessoa não são usados.
enum CipaHomeAlertKind { inspection, meetingTomorrow, technicalReply }

class CipaHomeAlert {
  const CipaHomeAlert(this.kind,this.message);
  final CipaHomeAlertKind kind;
  final String message;
}

class CipaHomeAlertBuilder {
  const CipaHomeAlertBuilder._();

  static List<CipaHomeAlert> fromView(CipaMemberView view,{
    DateTime? now,Set<String> locallyRead=const {},
  }) {
    final reference=now??DateTime.now();
    final today=DateTime(reference.year,reference.month,reference.day);
    final tomorrow=today.add(const Duration(days:1));
    final profile=view.profile;
    bool belongs(CipaMemberItem item)=>
      item.companyId==profile.companyId&&
      item.mandateId==profile.mandateId&&
      item.assignedMemberId==profile.memberId;

    final alerts=<CipaHomeAlert>[];
    final pending=view.scheduledInspections.where(
      (item)=>belongs(item)&&item.status=='Programada').toList();
    if(pending.isNotEmpty)alerts.add(CipaHomeAlert(
      CipaHomeAlertKind.inspection,
      pending.length==1?'Você tem uma vistoria programada.':
        'Você tem ${pending.length} vistorias programadas.'));

    // Reunião compartilhada já veio filtrada para a sessão pelo backend.
    final tomorrowMeetings=view.meetings.where((item) {
      if(item.companyId!=profile.companyId||
         item.mandateId!=profile.mandateId||
         !(item.assignedMemberId==profile.memberId||
           item.visibleToAllMembers))return false;
      final date=item.date??item.dueDate;
      if(date==null||item.status!='Agendada')return false;
      final calendarDate=DateTime(date.year,date.month,date.day);
      return calendarDate==tomorrow;
    }).length;
    if(tomorrowMeetings>0)alerts.add(const CipaHomeAlert(
      CipaHomeAlertKind.meetingTomorrow,'Reunião da CIPA amanhã.'));

    final unread=view.observations.where((item)=>
      belongs(item)&&item.status=='Orientação enviada'&&
      item.feedback.trim().isNotEmpty&&item.reviewId.isNotEmpty&&
      !item.feedbackRead&&
      !locallyRead.contains('${item.id}|${item.reviewId}')).length;
    if(unread>0)alerts.add(CipaHomeAlert(
      CipaHomeAlertKind.technicalReply,unread==1?
        'O técnico respondeu a uma vistoria.':
        'Você tem $unread orientações do técnico para ler.'));
    return alerts;
  }
}

import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/cipa_member_identity.dart';
import 'package:auditar_sst/services/cipa_member_portal_policy.dart';
import 'package:auditar_sst/services/cipa_member_today.dart';
import 'package:auditar_sst/services/cipa_member_home_alerts.dart';

void main(){
  test('Hoje reúne tarefas e reunião sem misturar mandatos ou membros',(){
    final profile=CipaMemberProfileContract.fromVerifiedMembership(
      authenticatedUserId:'user-A',grantedCompanyId:'company-A',
      grantedMandateId:'mandate-A',grantedMemberId:'member-A',
      membershipUserId:'user-A',membershipCompanyId:'company-A',
      membershipMandateId:'mandate-A',membershipMemberId:'member-A',
      membershipWorkerId:'worker-A',fullName:'Maria Silva',
      cipaRole:'Titular',representation:'Empregados',
      memberActive:true,mandateActive:true,userActive:true)!;
    final view=CipaMemberPortalRules.build(
      verifiedProfile:profile,records:[
        CipaMemberItem(id:'meeting-today',type:CipaMemberItemType.meeting,
          title:'Reunião mensal',companyId:'company-A',
          mandateId:'mandate-A',assignedMemberId:'member-A',
          date:DateTime(2026,11,13,10),status:'Agendada'),
        CipaMemberItem(id:'action-overdue',type:CipaMemberItemType.action,
          title:'Inspecionar passagem',companyId:'company-A',
          mandateId:'mandate-A',assignedMemberId:'member-A',
          dueDate:DateTime(2026,11,12),status:'Pendente'),
        const CipaMemberItem(id:'inspection',type:CipaMemberItemType.scheduledInspection,
          title:'Setor produção',companyId:'company-A',
          mandateId:'mandate-A',assignedMemberId:'member-A',
          status:'Programada'),
        const CipaMemberItem(id:'reply',type:CipaMemberItemType.observation,
          title:'Orientação técnica',companyId:'company-A',
          mandateId:'mandate-A',assignedMemberId:'member-A',
          status:'Orientação enviada',reviewId:'review-A',
          feedback:'Equipe orientou sobre proteção.'),
        const CipaMemberItem(id:'private-foreign',type:CipaMemberItemType.action,
          title:'Segredo de colega',companyId:'company-A',
          mandateId:'mandate-A',assignedMemberId:'member-B',
          status:'Pendente'),
        const CipaMemberItem(id:'foreign-company',type:CipaMemberItemType.action,
          title:'Segredo de empresa',companyId:'company-B',
          mandateId:'mandate-A',assignedMemberId:'member-A',
          status:'Pendente'),
      ]);
    final items=CipaTodayPlan.fromView(view,now:DateTime(2026,11,13,9));
    expect(items.map((i)=>i.target),[
      CipaTodayTarget.answers,CipaTodayTarget.meetings,
      CipaTodayTarget.inspections,CipaTodayTarget.actions,
    ]);
    expect(items.map((i)=>i.title).join(' '),isNot(contains('Segredo')));
    final alerts=CipaHomeAlertBuilder.fromView(view,
      now:DateTime(2026,11,13,9));
    expect(alerts.map((a)=>a.kind),contains(CipaHomeAlertKind.meetingToday));
    expect(alerts.map((a)=>a.kind),contains(CipaHomeAlertKind.actionOverdue));
    expect(alerts.map((a)=>a.kind),contains(CipaHomeAlertKind.technicalReply));
    expect(alerts.map((a)=>a.message).join(' '),isNot(contains('Segredo')));
  });
}

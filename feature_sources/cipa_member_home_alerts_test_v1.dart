import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/cipa_member_home_alerts.dart';
import 'package:auditar_sst/services/cipa_member_identity.dart';
import 'package:auditar_sst/services/cipa_member_portal_policy.dart';

void main(){
  test('Apenas três avisos pessoais relevantes, sem dados de outro mandato',(){
    final profile=CipaMemberProfileContract.fromVerifiedMembership(
      authenticatedUserId:'user-A',
      grantedCompanyId:'company-A',grantedMandateId:'mandate-A',
      grantedMemberId:'member-A',membershipUserId:'user-A',
      membershipCompanyId:'company-A',membershipMandateId:'mandate-A',
      membershipMemberId:'member-A',membershipWorkerId:'worker-A',
      fullName:'Joana',cipaRole:'Titular',representation:'Empregados',
      userActive:true,memberActive:true,mandateActive:true)!;
    final view=CipaMemberPortalRules.build(verifiedProfile:profile,records:[
      const CipaMemberItem(id:'inspection-A',
        companyId:'company-A',mandateId:'mandate-A',
        assignedMemberId:'member-A',type:CipaMemberItemType.scheduledInspection,
        title:'Vistoria de organização',status:'Programada'),
      const CipaMemberItem(id:'meeting-A',
        companyId:'company-A',mandateId:'mandate-A',
        assignedMemberId:'member-A',type:CipaMemberItemType.meeting,
        title:'Reunião CIPA',status:'Agendada',
        date:null),
      CipaMemberItem(id:'meeting-2',
        companyId:'company-A',mandateId:'mandate-A',
        assignedMemberId:'member-A',type:CipaMemberItemType.meeting,
        title:'Reunião amanhã',status:'Agendada',
        date:DateTime(2026,11,14,10)),
      const CipaMemberItem(id:'review-A',
        companyId:'company-A',mandateId:'mandate-A',
        assignedMemberId:'member-A',type:CipaMemberItemType.observation,
        title:'Registro próprio',status:'Orientação enviada',
        feedback:'Verificar proteção',reviewId:'revision-1'),
      const CipaMemberItem(id:'foreign-inspection',
        companyId:'company-B',mandateId:'mandate-A',
        assignedMemberId:'member-A',type:CipaMemberItemType.scheduledInspection,
        title:'Segredo',status:'Programada'),
      const CipaMemberItem(id:'other-person-reply',
        companyId:'company-A',mandateId:'mandate-A',
        assignedMemberId:'member-B',type:CipaMemberItemType.observation,
        title:'Registro de outro membro',status:'Orientação enviada',
        feedback:'Segredo privado',reviewId:'revision-2'),
    ]);
    final alerts=CipaHomeAlertBuilder.fromView(view,
      now:DateTime(2026,11,13,7));
    expect(alerts.map((a)=>a.kind),[
      CipaHomeAlertKind.inspection,
      CipaHomeAlertKind.meetingTomorrow,
      CipaHomeAlertKind.technicalReply,
    ]);
    expect(alerts.map((a)=>a.message).join(' '),isNot(contains('Segredo')));
    expect(CipaHomeAlertBuilder.fromView(view,
      now:DateTime(2026,11,13,7),
      locallyRead:{'review-A|revision-1'}).length,2);
  });

  test('Relato enviado não gera aviso de vistoria pendente',(){
    final p=CipaMemberProfileContract.fromVerifiedMembership(
      authenticatedUserId:'user-A',
      grantedCompanyId:'company-A',grantedMandateId:'mandate-A',
      grantedMemberId:'member-A',membershipUserId:'user-A',
      membershipCompanyId:'company-A',membershipMandateId:'mandate-A',
      membershipMemberId:'member-A',membershipWorkerId:'worker-A',
      fullName:'Joana',cipaRole:'Titular',representation:'Empregados',
      userActive:true,memberActive:true,mandateActive:true)!;
    final v=CipaMemberPortalRules.build(verifiedProfile:p,records:[
      const CipaMemberItem(id:'inspection-A',
        companyId:'company-A',mandateId:'mandate-A',
        assignedMemberId:'member-A',type:CipaMemberItemType.scheduledInspection,
        title:'Vistoria',status:'Registro enviado'),
    ]);
    expect(CipaHomeAlertBuilder.fromView(v,
      now:DateTime(2026,11,13)).isEmpty,true);
  });
}

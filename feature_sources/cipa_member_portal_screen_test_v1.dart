import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/screens/cipa_member_portal_screen.dart';
import 'package:auditar_sst/services/cipa_member_identity.dart';
import 'package:auditar_sst/services/cipa_member_portal_policy.dart';

CipaMemberAccessProfile profile() =>
  CipaMemberProfileContract.fromVerifiedMembership(
    authenticatedUserId:'user-A',grantedCompanyId:'empresa-A',
    grantedMandateId:'mandato-A',grantedMemberId:'member-A',
    membershipUserId:'user-A',membershipCompanyId:'empresa-A',
    membershipMandateId:'mandato-A',membershipMemberId:'member-A',
    membershipWorkerId:'worker-A',
    fullName:'Maria Silva',cipaRole:'Presidente',
    representation:'Empregador',jobTitle:'Encarregada',
    userActive:true,mandateActive:true,memberActive:true)!;

void main() {
  testWidgets('sem sessão real a tela bloqueia qualquer dado',
    (tester) async {
    final p=profile();
    final view=CipaMemberPortalRules.build(verifiedProfile:p,records:[
      const CipaMemberItem(id:'meeting-A',companyId:'empresa-A',
        mandateId:'mandato-A',type:CipaMemberItemType.meeting,
        title:'Reunião de Teste',visibleToAllMembers:true),
    ]);
    await tester.pumpWidget(MaterialApp(home:CipaMemberPortalScreen(
      companyName:'Empresa de Teste',mandateLabel:'2026',
      view:view,
    )));
    expect(find.text('Acesso pessoal não liberado'),findsOneWidget);
    expect(find.text('Reunião de Teste'),findsNothing);
    expect(find.text('Maria Silva — Presidente da CIPA'),findsNothing);
  });

  testWidgets('tela pessoal lista apenas informações previamente autorizadas',
    (tester) async {
    final p=profile();
    final view=CipaMemberPortalRules.build(verifiedProfile:p,records:[
      const CipaMemberItem(id:'meeting-A',companyId:'empresa-A',
        mandateId:'mandato-A',type:CipaMemberItemType.meeting,
        title:'Reunião de Teste',status:'Agendada',visibleToAllMembers:true),
      const CipaMemberItem(id:'action-A',companyId:'empresa-A',
        mandateId:'mandato-A',type:CipaMemberItemType.action,
        title:'Proteção da esteira',assignedMemberId:'member-A',
        status:'Em andamento'),
      const CipaMemberItem(id:'other-A',companyId:'empresa-B',
        mandateId:'mandato-A',type:CipaMemberItemType.action,
        title:'Ação secreta de outra empresa',assignedMemberId:'member-A'),
      const CipaMemberItem(id:'secret-A',companyId:'empresa-A',
        mandateId:'mandato-A',type:CipaMemberItemType.action,
        title:'Ação de outro membro',assignedMemberId:'member-B'),
    ]);
    await tester.pumpWidget(MaterialApp(home:CipaMemberPortalScreen(
      companyName:'Empresa de Teste',mandateLabel:'2026/2027',
      view:view,sessionVerified:true,
    )));
    expect(find.text('Maria Silva — Presidente da CIPA'),findsOneWidget);
    expect(find.text('Minha CIPA'),findsOneWidget);
    expect(find.text('Reunião de Teste'),findsOneWidget);
    expect(find.text('Proteção da esteira'),findsOneWidget);
    expect(find.text('Ação secreta de outra empresa'),findsNothing);
    expect(find.text('Ação de outro membro'),findsNothing);
    expect(find.text('Encerrar NC'),findsNothing);
    expect(find.text('Gerenciar usuários'),findsNothing);
    expect(find.text('Assinar ata'),findsNothing);
  });
}

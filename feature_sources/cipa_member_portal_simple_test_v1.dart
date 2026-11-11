import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/screens/cipa_member_portal_screen.dart';
import 'package:auditar_sst/services/cipa_member_identity.dart';
import 'package:auditar_sst/services/cipa_member_portal_policy.dart';

CipaMemberView view() {
  final profile=CipaMemberProfileContract.fromVerifiedMembership(
    authenticatedUserId:'user-A',grantedCompanyId:'company-A',
    grantedMandateId:'mandate-A',grantedMemberId:'member-A',
    membershipUserId:'user-A',membershipCompanyId:'company-A',
    membershipMandateId:'mandate-A',membershipMemberId:'member-A',
    membershipWorkerId:'worker-A',
    fullName:'Joana Souza',cipaRole:'Titular',
    representation:'Empregados',jobTitle:'Operadora',
    userActive:true,mandateActive:true,memberActive:true,
  )!;
  return CipaMemberPortalRules.build(verifiedProfile:profile,records:[
    const CipaMemberItem(
      id:'meeting-A',companyId:'company-A',mandateId:'mandate-A',
      type:CipaMemberItemType.meeting,
      title:'Reunião da CIPA',status:'Agendada',
      visibleToAllMembers:true,
    ),
    const CipaMemberItem(
      id:'action-A',companyId:'company-A',mandateId:'mandate-A',
      type:CipaMemberItemType.action,title:'Conferir proteção da máquina',
      assignedMemberId:'member-A',status:'Em andamento',
    ),
    const CipaMemberItem(
      id:'notice-A',companyId:'company-A',mandateId:'mandate-A',
      type:CipaMemberItemType.notice,title:'Comunicado interno',
      visibleToAllMembers:true,
    ),
    const CipaMemberItem(
      id:'outside',companyId:'company-B',mandateId:'mandate-A',
      type:CipaMemberItemType.action,title:'Ação de outra empresa',
      assignedMemberId:'member-A',
    ),
  ]);
}

void main() {
  testWidgets('Mesmo com informações carregadas, oferece três ações simples',
    (tester) async {
    await tester.binding.setSurfaceSize(const Size(400,820));
    await tester.pumpWidget(MaterialApp(
      home:CipaMemberPortalScreen(
        companyName:'Empresa A',mandateLabel:'2026',
        sessionVerified:true,view:view(),
        onObserve:(_,__)async{},
      ),
    ));
    expect(find.text('O que você quer fazer hoje?'),findsOneWidget);
    expect(find.text('Ver reuniões'),findsOneWidget);
    expect(find.text('Minhas tarefas'),findsWidgets);
    expect(find.text('Fazer vistoria'),findsOneWidget);
    // Relato avulso só fica visível após abrir Mais informações.
    expect(find.text('Avisar uma situação'),findsNothing);
    expect(find.text('Comunicado interno'),findsNothing);
    await tester.scrollUntilVisible(find.text('Mais informações'),150);
    await tester.ensureVisible(find.text('Mais informações'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Mais informações'));
    await tester.pumpAndSettle();
    expect(find.text('Avisos (1)'),findsOneWidget);
    expect(find.text('Comunicado interno'),findsOneWidget);
    expect(find.text('Ação de outra empresa'),findsNothing);
    await tester.binding.setSurfaceSize(null);
  });

  testWidgets('Avisar situação mostra linguagem comum e só envia com descrição',
    (tester) async {
    var observations=0;
    await tester.pumpWidget(MaterialApp(home:CipaMemberPortalScreen(
      companyName:'Empresa A',mandateLabel:'2026',view:view(),
      sessionVerified:true,
      onObserve:(place,desc)async {observations++;},
    )));
    await tester.scrollUntilVisible(find.text('Mais informações'),150);
    await tester.ensureVisible(find.text('Mais informações'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Mais informações'));
    await tester.pumpAndSettle();
    final observeButton=find.widgetWithText(OutlinedButton,'Avisar uma situação');
    await tester.ensureVisible(observeButton);
    await tester.pumpAndSettle();
    await tester.tap(observeButton);
    await tester.pumpAndSettle();
    expect(find.text('O que você observou?'),findsOneWidget);
    expect(find.textContaining('Não se aproxime de um perigo'),findsOneWidget);
    expect(observations,0);
    final submit=find.widgetWithText(FilledButton,'Enviar observação');
    expect(tester.widget<FilledButton>(submit).onPressed,isNull);
    await tester.tap(find.text('Cancelar'));
    await tester.pumpAndSettle();
    expect(observations,0);
  });

  testWidgets('Guia da CIPA explica participação sem declarar conformidade',
    (tester) async {
    await tester.binding.setSurfaceSize(const Size(400,820));
    await tester.pumpWidget(MaterialApp(home:CipaMemberPortalScreen(
      companyName:'Empresa A',mandateLabel:'2026',
      sessionVerified:true,view:view(),
    )));
    await tester.scrollUntilVisible(
      find.text('Como funciona a minha participação'),130);
    await tester.tap(find.text('Como funciona a minha participação'));
    await tester.pumpAndSettle();
    expect(find.text('Recebi um aviso de reunião'),findsOneWidget);
    expect(find.text('Tenho uma tarefa'),findsOneWidget);
    expect(find.text('Observei uma situação'),findsOneWidget);
    expect(find.textContaining('não que esteve presente'),findsOneWidget);
    await tester.binding.setSurfaceSize(null);
  });

  testWidgets('Histórico mostra só vistorias próprias autorizadas',
    (tester) async {
    final current=view().profile;
    final allowed=CipaMemberPortalRules.build(
      verifiedProfile:current,records:[
      const CipaMemberItem(
        id:'vistoria-A',companyId:'company-A',mandateId:'mandate-A',
        type:CipaMemberItemType.observation,
        title:'Situação observada • Produção',
        description:'VISTORIA ORIENTADA DA CIPA — OBSERVAÇÃO VISUAL',
        status:'Orientação enviada',
        feedback:'Conferir a passagem com equipe técnica.',
        assignedMemberId:'member-A'),
      const CipaMemberItem(
        id:'vistoria-B',companyId:'company-B',mandateId:'mandate-A',
        type:CipaMemberItemType.observation,
        title:'Vistoria secreta de outra empresa',
        description:'VISTORIA ORIENTADA DA CIPA — OBSERVAÇÃO VISUAL',
        assignedMemberId:'member-A'),
      const CipaMemberItem(
        id:'observacao-A',companyId:'company-A',mandateId:'mandate-A',
        type:CipaMemberItemType.observation,
        title:'Relato informal',
        description:'Piso molhado na passagem',
        assignedMemberId:'member-A'),
    ]);
    await tester.pumpWidget(MaterialApp(home:CipaMemberPortalScreen(
      companyName:'Empresa A',mandateLabel:'2026',
      view:allowed,sessionVerified:true)));
    await tester.scrollUntilVisible(
      find.text('Minhas vistorias orientadas (1)'),140);
    expect(find.text('Minhas vistorias orientadas (1)'),findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Situação observada • Produção'),140);
    expect(find.text('Situação observada • Produção'),findsOneWidget);
    expect(find.textContaining('Resposta do técnico: Conferir'),
      findsOneWidget);
    expect(find.text('Vistoria secreta de outra empresa'),findsNothing);
    expect(find.text('Relato informal'),findsNothing);
  });

  testWidgets('Sem login autorizado, nenhum atalho libera dados',
    (tester) async {
    await tester.pumpWidget(MaterialApp(home:CipaMemberPortalScreen(
      companyName:'Empresa A',mandateLabel:'2026',
      view:view(),
    )));
    expect(find.text('Acesso pessoal não liberado'),findsOneWidget);
    expect(find.text('Ver reuniões'),findsNothing);
    expect(find.text('Conferir proteção da máquina'),findsNothing);
  });
}


import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/cipa_member_identity.dart';
import 'package:auditar_sst/widgets/cipa_member_role_meeting_panel.dart';

CipaMemberAccessProfile profile(String role,String representation)=>
  CipaMemberProfileContract.fromVerifiedMembership(
    authenticatedUserId:'u1',grantedCompanyId:'c1',
    grantedMandateId:'m1',grantedMemberId:'p1',
    membershipUserId:'u1',membershipCompanyId:'c1',
    membershipMandateId:'m1',membershipMemberId:'p1',
    membershipWorkerId:'w1',fullName:'Joana',
    cipaRole:role,representation:representation,
    userActive:true,mandateActive:true,memberActive:true)!;

void main(){
  testWidgets('Presidente vê função verificada e pode abrir guia de reunião',
    (tester)async{
    await tester.binding.setSurfaceSize(const Size(410,850));
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:
      SingleChildScrollView(child:CipaMeetingRoleCoachPanel(
        profile:profile('Presidente','Empregador'))))));
    expect(find.text('Seu papel: Presidente'),findsOneWidget);
    await tester.tap(find.text('Entender minha função'));
    await tester.pumpAndSettle();
    expect(find.text('Minha função: Presidente'),findsOneWidget);
    expect(find.textContaining('Convoca os membros'),findsOneWidget);
    await tester.tap(find.text('Entendi'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Aprender reunião e ata'));
    await tester.pumpAndSettle();
    expect(find.text('1. Antes da reunião'),findsOneWidget);
    await tester.tap(find.text('Próxima etapa'));
    await tester.pumpAndSettle();
    expect(find.text('2. Como abrir a reunião'),findsOneWidget);
    expect(find.textContaining('Bom dia. Vamos iniciar'),findsOneWidget);
    await tester.tap(find.text('Fechar'));
    await tester.pumpAndSettle();
    await tester.binding.setSurfaceSize(null);
  });

  testWidgets('Secretário sabe que precisa ser designado a cada reunião',
    (tester)async{
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:
      SingleChildScrollView(child:CipaMeetingRoleCoachPanel(
        profile:profile('Secretário','Empregados'))))));
    await tester.tap(find.text('Entender minha função'));
    await tester.pumpAndSettle();
    expect(find.text('Minha função: Secretário'),findsOneWidget);
    expect(find.textContaining('CADA reunião'),findsOneWidget);
    await tester.tap(find.text('Entendi'));
    await tester.pumpAndSettle();
  });

  testWidgets('Guia alcança rascunho, sem registrar presença ou assinar',
    (tester)async{
    await tester.binding.setSurfaceSize(const Size(410,850));
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:
      SingleChildScrollView(child:CipaMeetingRoleCoachPanel(
        profile:profile('Titular','Empregados'))))));
    await tester.tap(find.text('Aprender reunião e ata'));
    await tester.pumpAndSettle();
    for(var i=0;i<4;i++){
      await tester.tap(find.text('Próxima etapa'));
      await tester.pumpAndSettle();
    }
    expect(find.text('5. Finalizar e conferir'),findsOneWidget);
    await tester.tap(find.text('Montar rascunho da ata'));
    await tester.pumpAndSettle();
    expect(find.text('Como iniciar uma ata — exercício'),findsOneWidget);
    expect(find.textContaining('não uma ata assinada'),findsOneWidget);
    expect(find.text('Ver rascunho'),findsOneWidget);
    expect(find.text('Copiar'),findsNothing);
    await tester.tap(find.text('Fechar'));
    await tester.pumpAndSettle();
    await tester.binding.setSurfaceSize(null);
  });
}

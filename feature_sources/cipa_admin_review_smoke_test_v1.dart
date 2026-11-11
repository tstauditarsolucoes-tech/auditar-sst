import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:cipa_admin_fixture/screens/cipa_member_admin_screen.dart';
import 'package:cipa_admin_fixture/services/apps_script_http.dart';

void main() {
  testWidgets('TST registra devolutiva com estado e orientação', (tester) async {
    AppsScriptHttp.requests.clear();
    await tester.binding.setSurfaceSize(const Size(700,900));
    await tester.pumpWidget(const MaterialApp(home:CipaMemberAdminScreen(
      companyId:'empresa-A',mandateId:'mandato-A',
      members:[],actions:[],documents:[],
    )));
    await tester.pumpAndSettle();
    await tester.scrollUntilVisible(
      find.text('Central de Vistorias e Relatos (1)'),200,
      scrollable:find.byType(Scrollable).first);
    await tester.tap(find.text('Central de Vistorias e Relatos (1)'));
    await tester.pumpAndSettle();
    await tester.scrollUntilVisible(find.text('Orientar'),150,
      scrollable:find.byType(Scrollable).first);
    await tester.tap(find.text('Orientar'));
    await tester.pumpAndSettle();
    expect(find.text('Orientar integrante da CIPA'),findsOneWidget);
    await tester.tap(find.text('Situação'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Orientação enviada').last);
    await tester.pumpAndSettle();
    final field=find.widgetWithText(TextField,'Orientação (opcional em análise)');
    await tester.enterText(field,'Conferir corredor com responsável do setor.');
    await tester.pump();
    await tester.tap(find.text('Registrar devolutiva'));
    await tester.pumpAndSettle();
    final reviews=AppsScriptHttp.requests.where(
      (r)=>r['action']=='cipa_member_admin_review_observation').toList();
    expect(reviews.length,1);
    expect(reviews.single['companyId'],'empresa-A');
    expect(reviews.single['mandateId'],'mandato-A');
    expect(reviews.single['observationId'],'observation-fixture-A');
    expect(reviews.single['status'],'Orientação enviada');
    expect(reviews.single['message'],
      'Conferir corredor com responsável do setor.');
    expect((reviews.single['requestId'] as String).length,greaterThan(16));
    await tester.binding.setSurfaceSize(null);
  });
}

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:cipa_admin_fixture/screens/cipa_tst_review_screen.dart';
import 'package:cipa_admin_fixture/services/apps_script_http.dart';

void main() {
  testWidgets('Tela TST usa somente rotas de triagem limitadas',
    (tester) async {
    AppsScriptHttp.requests.clear();
    await tester.pumpWidget(const MaterialApp(
      home:CipaTstReviewScreen(
        companyId:'empresa-A',mandateId:'mandato-A')));
    await tester.pumpAndSettle();
    expect(find.text('Vistorias da CIPA'),findsOneWidget);
    expect(find.text('Cadastrar acesso individual'),findsNothing);
    expect(find.text('Autorizar acesso'),findsNothing);
    final actions=AppsScriptHttp.requests.map((x)=>x['action']).toList();
    expect(actions,contains('cipa_tst_review_inbox'));
    expect(actions,isNot(contains('cipa_member_admin_list')));
  });
}

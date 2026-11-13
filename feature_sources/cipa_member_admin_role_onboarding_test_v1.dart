
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:cipa_admin_fixture/screens/cipa_member_admin_screen.dart';

void main(){
  testWidgets('Cadastro permite conferir função e impede cargo divergente',
    (tester)async{
    await tester.binding.setSurfaceSize(const Size(650,950));
    await tester.pumpWidget(const MaterialApp(home:
      CipaMemberAdminScreen(companyId:'empresa-A',mandateId:'mandato-A',
        members:[CipaAdminMemberOption(memberId:'member-1',
          workerId:'worker-1',name:'Joana',cipaRole:'Vice-presidente')],
        actions:[],documents:[])));
    await tester.pumpAndSettle();
    final register=find.text('Cadastrar acesso individual');
    await tester.scrollUntilVisible(register,180,
      scrollable:find.byType(Scrollable).first);
    await tester.pumpAndSettle();
    expect(register,findsOneWidget);
    final memberPicker=find.widgetWithText(
      DropdownButtonFormField<String>,'Integrante da CIPA');
    await tester.ensureVisible(memberPicker);
    await tester.tap(memberPicker);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Joana — Vice-presidente da CIPA').last);
    await tester.pumpAndSettle();
    expect(find.text('Função do integrante na CIPA'),findsOneWidget);
    expect(find.textContaining('Substitui o presidente'),findsOneWidget);
    final rolePicker=find.widgetWithText(
      DropdownButtonFormField<String>,'Função do integrante na CIPA');
    await tester.ensureVisible(rolePicker);
    await tester.tap(rolePicker);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Presidente').last);
    await tester.pumpAndSettle();
    expect(find.textContaining('não corresponde ao'),findsOneWidget);
    final grant=find.widgetWithText(FilledButton,'Autorizar acesso');
    await tester.ensureVisible(grant);
    expect(tester.widget<FilledButton>(grant).onPressed,isNull);
    await tester.binding.setSurfaceSize(null);
  });
}

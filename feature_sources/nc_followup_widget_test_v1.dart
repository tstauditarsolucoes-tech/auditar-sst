import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/models.dart';
import 'package:auditar_sst/database.dart';
import 'package:auditar_sst/screens/nc_followup_screen.dart';

void main() {
  const mine = Company(id: 'empresa-A', name: 'Empresa A');
  setUp(() {
    AppDatabase.activeUserId = 'tst-1';
    AppDatabase.instance.ncRows = [];
    AppDatabase.instance.settings.clear();
  });

  testWidgets('Lista só a NC da empresa autorizada', (tester) async {
    AppDatabase.instance.ncRows = [
      {'id':'nc-1','company_id':'empresa-A','sector':'Produção',
       'description':'Esteira sem proteção'},
      {'id':'nc-2','company_id':'empresa-B','sector':'Expedição',
       'description':'Informação privada de outro cliente'},
    ];
    await tester.pumpWidget(const MaterialApp(
      home: NcFollowupListScreen(company: mine),
    ));
    await tester.pumpAndSettle();
    expect(find.text('Esteira sem proteção'), findsOneWidget);
    expect(find.textContaining('Informação privada'), findsNothing);
    expect(find.text('NCs encontradas: 1'), findsOneWidget);
  });

  testWidgets('Acompanhamento vinculado não cria outra NC', (tester) async {
    AppDatabase.instance.ncRows = [
      {'id':'nc-1','company_id':'empresa-A','sector':'Produção',
       'description':'Esteira sem proteção'},
    ];
    await tester.pumpWidget(const MaterialApp(
      home: NcFollowupListScreen(company: mine),
    ));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Esteira sem proteção'));
    await tester.pumpAndSettle();
    expect(find.text('Acompanhamento de NC'), findsOneWidget);
    await tester.ensureVisible(find.text('Registrar acompanhamento'));
    await tester.tap(find.text('Registrar acompanhamento'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextFormField),
      'Permanece sem proteção após nova visita');
    await tester.tap(find.text('Salvar'));
    await tester.pumpAndSettle();
    expect(find.text('Pendência mantida'), findsOneWidget);
    expect(find.textContaining('1 acompanhamentos locais'), findsOneWidget);
    expect(AppDatabase.instance.ncRows.length, 1);
    expect(AppDatabase.instance.settings.length, 1);
  });

  testWidgets('Correção informada não encerra registro oficial',
      (tester) async {
    AppDatabase.instance.ncRows = [
      {'id':'nc-1','company_id':'empresa-A','sector':'Produção',
       'description':'Esteira sem proteção','status':'Aberta'},
    ];
    await tester.pumpWidget(const MaterialApp(
      home: NcFollowupDetailScreen(company: mine, nc: {
        'id':'nc-1','company_id':'empresa-A','sector':'Produção',
        'description':'Esteira sem proteção','status':'Aberta',
      }),
    ));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('Informar correção para validação'));
    await tester.tap(find.text('Informar correção para validação'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextFormField),
      'A empresa informou instalação da proteção');
    await tester.tap(find.text('Salvar'));
    await tester.pumpAndSettle();
    expect(find.text('Correção informada — aguarda validação'), findsOneWidget);
    expect(AppDatabase.instance.ncRows.single['status'], 'Aberta');
  });

  testWidgets('NC sem ID ou vínculo de empresa não é associada',
      (tester) async {
    AppDatabase.instance.ncRows = [
      {'company_id':'empresa-A','description':'Registro sem ID'},
      {'id':'nc-3','description':'Registro sem empresa'},
    ];
    await tester.pumpWidget(const MaterialApp(
      home: NcFollowupListScreen(company: mine),
    ));
    await tester.pumpAndSettle();
    expect(find.text('NCs encontradas: 0'), findsOneWidget);
    expect(find.textContaining('Registro sem ID'), findsNothing);
  });
}

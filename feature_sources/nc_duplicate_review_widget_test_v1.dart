import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/models.dart';
import 'package:auditar_sst/database.dart';
import 'package:auditar_sst/screens/nc_duplicate_review_screen.dart';

void main() {
  const company=Company(id:'empresa-A',name:'Empresa A');

  setUp((){
    AppDatabase.activeUserId='tst-1';
    AppDatabase.instance.ncRows=[];
    AppDatabase.instance.settings.clear();
  });

  testWidgets('NC semelhante aparece sem exibir outra empresa', (tester)async{
    AppDatabase.instance.ncRows=[
      {'id':'nc1','company_id':'empresa-A','sector':'Produção',
       'description':'Esteira sem proteção','status':'Aberta'},
      {'id':'nc2','company_id':'empresa-B','sector':'Produção',
       'description':'Esteira sem proteção','status':'Aberta'},
      {'id':'nc3','company_id':'empresa-A','sector':'Moagem',
       'description':'Esteira sem proteção','status':'Aberta'},
      {'id':'nc4','company_id':'empresa-A','sector':'Produção',
       'description':'Esteira sem proteção','status':'Resolvida'},
    ];
    await tester.pumpWidget(const MaterialApp(home:
      NcDuplicateReviewScreen(company:company)));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextFormField).first,
      'Esteira transportadora sem proteção');
    await tester.enterText(find.byType(TextFormField).last,'Produção');
    await tester.ensureVisible(find.text('Conferir NCs semelhantes'));
    await tester.tap(find.text('Conferir NCs semelhantes'));
    await tester.pumpAndSettle();
    expect(find.text('Possíveis pendências já cadastradas'),findsOneWidget);
    expect(find.text('NC: nc1 • Produção'),findsOneWidget);
    expect(find.textContaining('nc2'),findsNothing);
    expect(find.textContaining('nc3'),findsNothing);
    expect(find.textContaining('nc4'),findsNothing);
    await tester.ensureVisible(find.text('Acompanhar esta NC'));
    await tester.tap(find.text('Acompanhar esta NC'));
    await tester.pumpAndSettle();
    expect(find.text('Acompanhamento de NC'),findsOneWidget);
    expect(AppDatabase.instance.ncRows.length,4);
  });

  testWidgets('Texto genérico não resulta em correspondência fictícia',
      (tester)async{
    AppDatabase.instance.ncRows=[
      {'id':'nc1','company_id':'empresa-A','sector':'Produção',
       'description':'Esteira sem proteção','status':'Aberta'},
    ];
    await tester.pumpWidget(const MaterialApp(home:
      NcDuplicateReviewScreen(company:company)));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextFormField).first,
      'Guarda corpo inexistente');
    // Ao abrir o teclado no Android, o botão pode ficar abaixo do campo.
    await tester.testTextInput.hide();
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('Conferir NCs semelhantes'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Conferir NCs semelhantes'));
    await tester.pumpAndSettle();
    // Mesmo fora da área visível, resultado e ressalva devem existir
    // na árvore de acessibilidade; SingleChildScrollView não os descarta.
    final noMatch=find.textContaining('Nenhuma correspondência identificada');
    final caveat=find.textContaining('NÃO confirma');
    expect(noMatch,findsOneWidget);
    expect(caveat,findsOneWidget);
    await tester.ensureVisible(noMatch);
    await tester.pumpAndSettle();
    expect(noMatch,findsOneWidget);
  });

  testWidgets('Criar outra Ronda exige confirmação do técnico', (tester)async{
    await tester.pumpWidget(const MaterialApp(home:
      NcDuplicateReviewScreen(company:company)));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('Não é a mesma situação • Nova Ronda'));
    await tester.tap(find.text('Não é a mesma situação • Nova Ronda'));
    await tester.pumpAndSettle();
    expect(find.text('Registrar outra situação?'),findsOneWidget);
    await tester.tap(find.text('Voltar'));
    await tester.pumpAndSettle();
    expect(find.text('Registrar outra situação?'),findsNothing);
    await tester.tap(find.text('Não é a mesma situação • Nova Ronda'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Iniciar nova Ronda'));
    await tester.pumpAndSettle();
    expect(find.text('RONDA_empresa-A'),findsOneWidget);
  });
}

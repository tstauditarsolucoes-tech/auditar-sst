import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../lib/models.dart';
import '../lib/screens/sst_risk_documents_screen.dart';
import '../lib/screens/sst_document_signature_panel.dart';

void main() {
  final company = Company(id: 'company-A', name: 'Empresa fictícia');

  testWidgets('Central permite encontrar APR, AR, PT e PET', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: SstRiskDocsHomeScreen(company: company),
    ));
    expect(find.text('APR, PT, AR e PET'), findsOneWidget);
    expect(find.text('Assistente passo a passo'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('PET - Permissão de Entrada e Trabalho'), 130,
    );
    expect(find.text('PET - Permissão de Entrada e Trabalho'),
        findsOneWidget);
  });

  testWidgets('PET abre em modo minuta não autorizada', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: SstRiskDocsHomeScreen(company: company),
    ));
    final item = find.text('PET - Permissão de Entrada e Trabalho');
    await tester.scrollUntilVisible(item, 130);
    await tester.tap(item);
    await tester.pumpAndSettle();
    expect(find.text('MINUTA - ENTRADA NÃO AUTORIZADA'), findsOneWidget);
    expect(find.textContaining('A entrada depende da'),
        findsWidgets);
  });

  testWidgets('Painel de assinatura declara ciência e não autorização',
      (tester) async {
    await tester.pumpWidget(const MaterialApp(home: Scaffold(
      body: SstDocumentSignaturePanel(
        companyId: 'company-A',
        userId: 'test-user',
        documentKind: 'risk_ar',
        documentId: 'draft-test-001',
        snapshot: '{"revision":"1"}',
        roles: {'author': 'Elaborador — ciência'},
        enabled: true,
      ),
    )));
    await tester.pumpAndSettle();
    expect(find.text('Assinar ciência'), findsOneWidget);
    await tester.tap(find.text('Assinar ciência'));
    await tester.pumpAndSettle();
    expect(find.textContaining('NÃO autoriza PT/PET'), findsWidgets);
    final confirm = find.widgetWithText(FilledButton, 'Registrar ciência');
    expect(confirm, findsOneWidget);
    expect(tester.widget<FilledButton>(confirm).onPressed, isNull);
    await tester.tap(find.text('Cancelar'));
    await tester.pumpAndSettle();
    expect(find.text('Assinar ciência'), findsOneWidget);
  });
}

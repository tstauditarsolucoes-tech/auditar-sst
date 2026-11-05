import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/screens/offline_sst_nrs_browser_screen.dart';

void main() {
  testWidgets('catálogo offline lista modelos e permite pesquisar',
      (tester) async {
    await tester.pumpWidget(
        const MaterialApp(home: OfflineSstNrsBrowserScreen()));
    await tester.pumpAndSettle();
    expect(find.textContaining('345'), findsOneWidget);
    expect(find.text('Norma ou segmento'), findsOneWidget);

    await tester.enterText(find.byType(TextField), 'amassadeira');
    await tester.pumpAndSettle();

    final selected = find.byKey(
        const ValueKey('nr-model-bakery-nr12-ama-grade-ausente'));
    expect(selected, findsOneWidget);
    await tester.tap(selected);
    await tester.pumpAndSettle();
    expect(find.text('Situação para conferência'), findsOneWidget);
    expect(find.text('Recomendação sugerida'), findsOneWidget);
    expect(find.text('Copiar texto'), findsOneWidget);
    expect(find.text('Aplicar não conformidade'), findsNothing);
  });

  testWidgets('modelos de enquadramento permanecem apenas consulta',
      (tester) async {
    await tester.pumpWidget(
        const MaterialApp(home: OfflineSstNrsBrowserScreen()));
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField),
        'Suspeita de exposição a ruído acima do limite');
    await tester.pumpAndSettle();
    expect(find.textContaining('Apenas consulta técnica'), findsWidgets);
    final selected =
        find.byKey(const ValueKey('nr-model-all-nrs-15-01'));
    expect(selected, findsOneWidget);
    await tester.tap(selected);
    await tester.pumpAndSettle();
    expect(find.textContaining('não estabelece insalubridade'), findsOneWidget);
  });
}

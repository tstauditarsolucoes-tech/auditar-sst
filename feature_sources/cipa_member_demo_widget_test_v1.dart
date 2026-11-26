import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_cipa_membro/demo_main.dart';

void main() {
  testWidgets('demonstração informa claramente que usa dados fictícios',
    (tester) async {
      await tester.pumpWidget(const MinhaCipaDemoApp());
      await tester.pumpAndSettle();
      expect(find.text('Minha CIPA — DEMO'), findsOneWidget);
      expect(find.text('Explorar telas da CIPA'),findsOneWidget);
      expect(find.textContaining('inteiramente fictícios'),findsOneWidget);
      await tester.tap(find.text('Explorar telas da CIPA'));
      await tester.pumpAndSettle();
      expect(find.textContaining('Maria Exemplo'),findsWidgets);
      expect(find.textContaining('Empresa Fictícia'),findsWidgets);
      expect(find.byType(Banner),findsOneWidget);
      expect(tester.widget<Banner>(find.byType(Banner)).message,'DEMO');
    });
}

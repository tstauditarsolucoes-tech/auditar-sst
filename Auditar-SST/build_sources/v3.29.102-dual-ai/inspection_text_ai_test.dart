import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/ai_assistant_service.dart';
import 'package:auditar_sst/widgets/inspection_text_ai_review.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('IA texto exige relato antes de fazer chamada de rede', () async {
    final reply = await AiAssistantService.improveInspectionText(
      companyName: 'Empresa teste',
      area: 'Forno',
      observationKind: 'Não conformidade',
      originalText: '  ',
    );
    expect(reply.success, isFalse);
    expect(reply.message, contains('Escreva'));
  });

  testWidgets('revisão permite recusar IA e preserva registro original',
      (tester) async {
    String? result = 'placeholder';
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: Builder(builder: (context) => TextButton(
          onPressed: () async {
            result = await InspectionTextAiReview.show(
              context,
              original: 'Extintor sem lacre.',
              suggested: 'Foi observado extintor sem lacre.',
            );
          },
          child: const Text('Abrir revisão'),
        )),
      ),
    ));
    await tester.tap(find.text('Abrir revisão'));
    await tester.pumpAndSettle();
    expect(find.text('Extintor sem lacre.'), findsOneWidget);
    expect(find.text('IA texto · revisão técnica'), findsOneWidget);
    await tester.tap(find.text('Manter meu texto'));
    await tester.pumpAndSettle();
    expect(result, isNull);
  });
}

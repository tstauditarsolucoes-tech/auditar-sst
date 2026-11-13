import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:cipa_admin_fixture/widgets/cipa_mural_moderation_panel.dart';

void main(){
  testWidgets('Moderador aprova relato e não conclui sem confirmação',
    (tester)async{
    await tester.binding.setSurfaceSize(const Size(760,1000));
    final actions=<String>[];
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:
      SingleChildScrollView(child:CipaMuralModerationPanel(
        onLoad:()async=>[{
          'id':'mural-post-1234567890123456',
          'place':'Produção','detail':'Passagem obstruída',
          'visibility':'Pendente','status':'Recebido','hasPhoto':false,
          'comments':<Object>[],
        }],
        onReview:(id,visibility,status,confirmed)async{
          actions.add('$visibility:$status:$confirmed');
        },
        onCommentReview:(id,publish)async{},
        onReply:(id,text,requestId)async{},
        onPhoto:(id)async=>null,
      )),
    )));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Moderação do Mural da CIPA'));
    await tester.pumpAndSettle();
    expect(find.text('Passagem obstruída'),findsOneWidget);
    await tester.tap(find.text('Aprovar'));
    await tester.pumpAndSettle();
    expect(actions.last,'Aprovado:Em análise:false');
    await tester.tap(find.text('Confirmar resolvido'));
    await tester.pumpAndSettle();
    expect(find.text('Correção realmente verificada?'),findsOneWidget);
    await tester.tap(find.text('Cancelar'));
    await tester.pumpAndSettle();
    expect(actions.length,1);
    await tester.binding.setSurfaceSize(null);
  });
}

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/widgets/cipa_member_mural_panel.dart';
import 'package:auditar_sst/services/cipa_member_mural_model.dart';

const post=CipaMuralPost(
  id:'mural-post-1234567890123456',place:'Produção',
  detail:'Material obstruindo parcialmente um corredor',
  status:'Em análise',visibility:'Aprovado',
  createdAt:'2026-11-13T09:00:00',hasPhoto:false,isMine:false,
  comments:[CipaMuralComment(id:'comment-1',body:'Vamos avaliar.',
    authorLabel:'Equipe SST',visibility:'Aprovado')]);

void main(){
  testWidgets('Mural offline não abre postagem ou comentários',
    (tester)async{
    await tester.pumpWidget(const MaterialApp(home:Scaffold(
      body:SingleChildScrollView(child:CipaMuralPanel(offline:true)))));
    expect(find.textContaining('não ficam salvas offline'),findsOneWidget);
    expect(find.text('Registrar ocorrência'),findsNothing);
  });
  testWidgets('Mural inclui publicação e resposta aprovada',
    (tester)async{
    await tester.pumpWidget(MaterialApp(home:Scaffold(
      body:SingleChildScrollView(child:CipaMuralPanel(
        onLoad:()async=>[post],
        onCreate:(a,b,c)async{},onComment:(a,b)async{},
        onPhoto:(a)async=>null,
      )))));
    await tester.pumpAndSettle();
    expect(find.text('Mural da CIPA'),findsOneWidget);
    expect(find.textContaining('Material obstruindo'),findsOneWidget);
    expect(find.textContaining('Vamos avaliar.'),findsOneWidget);
    expect(find.text('Comentar'),findsOneWidget);
  });
  testWidgets('Formulário não envia sem local e relato',
    (tester)async{
    var submissions=0;
    await tester.pumpWidget(MaterialApp(home:Scaffold(
      body:SingleChildScrollView(child:CipaMuralPanel(
        onLoad:()async=>[],onCreate:(a,b,c)async{submissions++;},
      )))));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Registrar ocorrência'));
    await tester.pumpAndSettle();
    final send=find.widgetWithText(FilledButton,'Enviar para análise');
    expect(tester.widget<FilledButton>(send).onPressed,isNull);
    final fields=find.byType(TextField);
    await tester.enterText(fields.at(0),'Produção');
    await tester.enterText(fields.at(1),
      'Piso com materiais acumulados próximo à passagem.');
    await tester.pumpAndSettle();
    expect(tester.widget<FilledButton>(send).onPressed,isNotNull);
    await tester.tap(send);
    await tester.pumpAndSettle();
    expect(submissions,1);
  });
}

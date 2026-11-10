import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/widgets/cipa_member_guided_inspection.dart';

void main() {
  test('Roteiro cobre quatro temas de observação simples', () {
    expect(CipaGuidedInspection.questions.length,4);
    for(final qs in CipaGuidedInspection.questions.values) {
      expect(qs.length,3);
    }
  });

  test('Resumo mantém respostas incertas e não declara conformidade', () {
    final note=CipaGuidedInspection.summary(
      place:'Produção',category:'Organização e circulação',
      answers:['Sim','Não','Não sei/não verifiquei'],
      observation:'Há materiais no corredor');
    expect(note,contains('Setor/local: Produção'));
    expect(note,contains('Resposta: Não sei/não verifiquei'));
    expect(note,contains('conferência técnica'));
    expect(note,contains('Há materiais no corredor'));
  });

  test('Sim indica relato para conferência e Não sei não inventa falha', () {
    final note=CipaGuidedInspection.summary(
      place:'Oficina',category:'Máquinas e equipamentos',
      answers:['Sim','Não','Não sei/não verifiquei'],
      observation:'Observei de distância segura');
    expect(note,contains('Situações informadas para conferência: 1.'));
    expect(note,contains('Respostas não verificadas: 1.'));
    expect(note,contains('OBSERVAÇÃO VISUAL'));
    expect(note,contains('não encerram ações'));
  });

  test('Não aceita observação que excede limite do campo', () {
    expect(()=>CipaGuidedInspection.summary(
      place:'Setor A',category:'Incêndio e emergência',
      answers:['Sim','Não','Não sei/não verifiquei'],
      observation:List<String>.filled(251,'a').join()),throwsArgumentError);
  });

  test('Roteiro recusa respostas e local inválidos', () {
    expect(()=>CipaGuidedInspection.summary(
      place:'',category:'Organização e circulação',
      answers:['Sim','Sim','Sim'],observation:''),
      throwsArgumentError);
    expect(()=>CipaGuidedInspection.summary(
      place:'Produção',category:'Organização e circulação',
      answers:['Aprovado','Sim','Sim'],observation:''),
      throwsArgumentError);
  });

  testWidgets('Membro consegue enviar observação guiada', (tester) async {
    String? receivedPlace,receivedNote;
    await tester.pumpWidget(MaterialApp(home:Scaffold(
      body:CipaGuidedInspectionDialog(onSend:(place,note) async {
        receivedPlace=place;receivedNote=note;
      }))));
    expect(find.text('Minha Vistoria CIPA'),findsOneWidget);
    expect(find.text('Enviar para análise'),findsOneWidget);
    expect(tester.widget<FilledButton>(
      find.widgetWithText(FilledButton,'Enviar para análise'))
      .onPressed,isNull);
    await tester.enterText(find.byType(TextField).first,'Produção');
    await tester.pump();
    expect(tester.widget<FilledButton>(
      find.widgetWithText(FilledButton,'Enviar para análise'))
      .onPressed,isNull);
    // Nenhuma resposta é preenchida em nome do integrante.
    for(var i=0;i<3;i++) {
      final answer=find.byKey(ValueKey('answer-$i-Não sei/não verifiquei'));
      await tester.ensureVisible(answer);
      await tester.tap(answer);
      await tester.pump();
    }
    expect(find.text('Respondidas: 3 de 3'),findsOneWidget);
    await tester.ensureVisible(find.text('Enviar para análise'));
    await tester.tap(find.text('Enviar para análise'));
    await tester.pumpAndSettle();
    expect(receivedPlace,'Produção');
    expect(receivedNote,contains('OBSERVAÇÃO VISUAL'));
  });
  testWidgets('Falha de rede não fecha diálogo nem confirma o envio',
    (tester) async {
    await tester.pumpWidget(MaterialApp(home:Scaffold(
      body:CipaGuidedInspectionDialog(onSend:(_,__) async {
        throw StateError('Conexão indisponível');
      }))));
    await tester.enterText(find.byType(TextField).first,'Moinho');
    for(var i=0;i<3;i++) {
      final answer=find.byKey(ValueKey('answer-$i-Não sei/não verifiquei'));
      await tester.ensureVisible(answer);
      await tester.tap(answer);
      await tester.pump();
    }
    await tester.tap(find.text('Enviar para análise'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Envio não confirmado'),findsOneWidget);
    expect(find.text('Minha Vistoria CIPA'),findsOneWidget);
  });

}

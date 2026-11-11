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

  test('Setores específicos usam só três perguntas', () {
    expect(CipaGuidedInspection.sectorQuestions.length,7);
    for(final entry in CipaGuidedInspection.sectorQuestions.entries) {
      expect(CipaGuidedInspection.questionsFor(entry.key).length,3,
        reason:entry.key);
      expect(CipaGuidedInspection.help[entry.key],isNotEmpty);
    }
    expect(()=>CipaGuidedInspection.questionsFor('Inexistente'),
      throwsArgumentError);
  });

  test('Registro setorial mantém revisão técnica e limite de 1200', () {
    for(final sector in CipaGuidedInspection.sectorQuestions.keys) {
      final note=CipaGuidedInspection.summary(
        place:'Produção',category:sector,
        answers:['Sim','Não','Não sei/não verifiquei'],
        observation:'Registro visual');
      expect(note,contains('Tema: $sector'));
      expect(note,contains('conferência técnica'));
      expect(note.length,lessThanOrEqualTo(1200));
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
      place:'A',category:'Organização e circulação',
      answers:['Sim','Sim','Sim'],observation:''),
      throwsArgumentError);
    expect(()=>CipaGuidedInspection.summary(
      place:'Produção',category:'Organização e circulação',
      answers:['Aprovado','Sim','Sim'],observation:''),
      throwsArgumentError);
  });

  testWidgets('Vistoria usa uma pergunta por tela e resumo final',
    (tester) async {
    String? receivedPlace,receivedNote;
    await tester.pumpWidget(MaterialApp(home:Scaffold(
      body:CipaGuidedInspectionDialog(
        memberName:'Maria Silva',memberRole:'Titular',
        companyName:'Empresa A',mandateLabel:'2026',
        onSend:(place,note) async {
          receivedPlace=place;receivedNote=note;
        }))));
    expect(find.text('Minha Vistoria CIPA'),findsOneWidget);
    expect(find.text('Integrante: Maria Silva'),findsOneWidget);
    expect(find.text('Função na CIPA: Titular'),findsOneWidget);
    expect(find.text('Empresa: Empresa A'),findsOneWidget);
    expect(find.text('Mandato: 2026'),findsOneWidget);
    expect(find.text('Pergunta 1 de 3'),findsNothing);
    final start=find.widgetWithText(FilledButton,'Começar');
    expect(tester.widget<FilledButton>(start).onPressed,isNull);
    await tester.enterText(find.byType(TextField).first,'Produção');
    await tester.pump();
    await tester.tap(start);
    await tester.pumpAndSettle();
    expect(find.text('Pergunta 1 de 3'),findsOneWidget);
    expect(find.text('Pergunta 2 de 3'),findsNothing);
    for(var i=0;i<3;i++) {
      expect(find.byKey(ValueKey('answer-$i-Sim')),findsOneWidget);
      if(i<2) {
        expect(tester.widget<FilledButton>(
          find.widgetWithText(FilledButton,'Próxima')).onPressed,isNull);
      }
      await tester.tap(find.byKey(ValueKey(
        'answer-$i-Não sei/não verifiquei')));
      await tester.pump();
      await tester.tap(find.text(i==2?'Conferir respostas':'Próxima'));
      await tester.pumpAndSettle();
    }
    expect(find.text('Confira suas respostas'),findsOneWidget);
    expect(find.text('Resposta: Não sei/não verifiquei'),findsNWidgets(3));
    await tester.ensureVisible(find.text('Enviar para análise'));
    await tester.tap(find.text('Enviar para análise'));
    await tester.pumpAndSettle();
    expect(receivedPlace,'Produção');
    expect(receivedNote,contains('OBSERVAÇÃO VISUAL'));
    expect(receivedNote,contains('Respostas não verificadas: 3'));
    expect(receivedNote, isNot(contains('Maria Silva')),
      reason:'O servidor vincula a sessão; não repetir dados pessoais no relato.');
  });

  testWidgets('Vistoria programada preenche setor e permite voltar sem perder resposta',
    (tester) async {
    await tester.pumpWidget(MaterialApp(home:Scaffold(
      body:CipaGuidedInspectionDialog(
        initialCategory:'Cerâmica',initialPlace:'Cerâmica',
        memberName:'Maria',companyName:'Empresa A',
        onSend:(_,__) async {}))));
    final field=tester.widget<TextField>(find.byType(TextField).first);
    expect(field.controller?.text,'Cerâmica');
    await tester.tap(find.text('Começar'));
    await tester.pumpAndSettle();
    expect(find.text('Há correia ou parte móvel acessível sem proteção visível?'),
      findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('answer-0-Sim')));
    await tester.pump();
    await tester.tap(find.text('Próxima'));
    await tester.pumpAndSettle();
    expect(find.text('Pergunta 2 de 3'),findsOneWidget);
    await tester.tap(find.text('Voltar'));
    await tester.pumpAndSettle();
    expect(find.text('Pergunta 1 de 3'),findsOneWidget);
    expect(find.byKey(const ValueKey('answer-0-Sim')),findsOneWidget);
    expect(tester.widget<RadioListTile<String>>(
      find.byKey(const ValueKey('answer-0-Sim'))).groupValue,'Sim');
  });

  testWidgets('Falha de envio mantém revisão aberta e não anuncia sucesso',
    (tester) async {
    await tester.pumpWidget(MaterialApp(home:Scaffold(
      body:CipaGuidedInspectionDialog(onSend:(_,__) async {
        throw StateError('Conexão indisponível');
      }))));
    await tester.enterText(find.byType(TextField).first,'Moinho');
    await tester.tap(find.text('Começar'));
    await tester.pumpAndSettle();
    for(var i=0;i<3;i++) {
      await tester.tap(find.byKey(ValueKey(
        'answer-$i-Não sei/não verifiquei')));
      await tester.pump();
      await tester.tap(find.text(i==2?'Conferir respostas':'Próxima'));
      await tester.pumpAndSettle();
    }
    await tester.ensureVisible(find.text('Enviar para análise'));
    await tester.tap(find.text('Enviar para análise'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Envio não confirmado'),findsOneWidget);
    expect(find.text('Confira suas respostas'),findsOneWidget);
  });
}

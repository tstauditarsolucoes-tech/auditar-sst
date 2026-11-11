import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/models.dart';
import 'package:auditar_sst/database.dart';
import 'package:auditar_sst/screens/visit_type_chooser_screen.dart';
import 'package:auditar_sst/screens/smart_visit_briefing_screen.dart';

void main() {
  const mine=Company(id:'empresa-A',name:'Empresa A');
  setUp((){
    AppDatabase.instance.fail=false;
    AppDatabase.instance.records=[];
  });

  testWidgets('Empresa selecionada abre resumo limitado aos dados locais',
      (tester)async{
    AppDatabase.instance.records=[
      const FakeRecord('a1','empresa-A','Aberta',{
        'roundId':'r1','sector':'Produção',
        'observationKind':'Não conformidade',
        'description':'Proteção de máquina ausente',
      }),
      const FakeRecord('a2','empresa-A','Aberta',{
        'roundId':'r2','sector':'Produção',
        'observationKind':'Não conformidade',
        'description':'Proteção de máquina ausente',
      }),
      const FakeRecord('b1','empresa-B','Aberta',{
        'roundId':'r9','sector':'Expedição',
        'observationKind':'Não conformidade',
        'description':'Informação privada de outra empresa',
      }),
    ];
    await tester.pumpWidget(const MaterialApp(
      home:AuditarVisitTypeChooserScreen(initialCompany:mine),
    ));
    expect(find.text('Preparar Visita Inteligente'),findsOneWidget);
    await tester.tap(find.text('Preparar Visita Inteligente'));
    await tester.pumpAndSettle();
    expect(find.text('Visita Inteligente'),findsOneWidget);
    expect(find.text('Empresa A'),findsOneWidget);
    expect(find.text('Rondas locais'),findsOneWidget);
    expect(find.text('Observações abertas'),findsOneWidget);
    expect(find.text('Possíveis repetições'),findsOneWidget);
    expect(find.text('2'),findsNWidgets(3));
    expect(find.textContaining('Informação privada'),findsNothing);
    await tester.scrollUntilVisible(find.text('Fazer nova ronda'),150);
    await tester.tap(find.text('Fazer nova ronda'));
    await tester.pumpAndSettle();
    expect(find.text('RONDA_empresa-A'),findsOneWidget);
  });

  testWidgets('Sem registros, nunca afirma ausência de riscos', (tester)async{
    await tester.pumpWidget(const MaterialApp(
      home:SmartVisitBriefingScreen(company:mine),
    ));
    await tester.pumpAndSettle();
    expect(find.textContaining('NÃO significa'),findsOneWidget);
    expect(find.text('0'),findsNWidgets(3));
  });

  testWidgets('Falha na consulta não mostra números potencialmente antigos',
      (tester)async{
    AppDatabase.instance.fail=true;
    await tester.pumpWidget(const MaterialApp(
      home:SmartVisitBriefingScreen(company:mine),
    ));
    await tester.pumpAndSettle();
    expect(find.textContaining('Não foi possível consultar'),findsOneWidget);
    expect(find.text('Rondas locais'),findsNothing);
    AppDatabase.instance.fail=false;
    await tester.tap(find.text('Tentar novamente'));
    await tester.pumpAndSettle();
    expect(find.text('Rondas locais'),findsOneWidget);
  });

  testWidgets('Sem empresa selecionada não abre briefing de outra empresa',
      (tester)async{
    await tester.pumpWidget(const MaterialApp(
      home:AuditarVisitTypeChooserScreen(),
    ));
    expect(find.text('Preparar Visita Inteligente'),findsNothing);
    expect(find.text('Checklist completo'),findsOneWidget);
  });
}

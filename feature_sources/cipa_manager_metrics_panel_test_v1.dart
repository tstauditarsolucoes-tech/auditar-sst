import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:cipa_admin_fixture/widgets/cipa_manager_metrics_panel.dart';

Map<String,dynamic> sample({String company='company-A'})=>{
  'ok':true,
  'scope':{'companyId':company,'mandateId':'mandate-A'},
  'metrics':{
    'membersActive':3,'membersParticipating':2,
    'inspectionsScheduled':5,'inspectionsSubmitted':3,
    'inspectionsOverdue':1,'meetingsScheduled':2,
    'meetingsRecorded':1,'correctiveActionsOverdue':4,
    'observationsPendingReview':1,'observationsReplied':2,
  },
};

void main(){
  testWidgets('Mostra indicadores da empresa autorizada sem dados pessoais',
      (tester) async {
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:ListView(children:[
      CipaManagerMetricsPanel(companyId:'company-A',mandateId:'mandate-A',
        serverData:sample()),
    ]))));
    expect(find.text('Indicadores gerenciais da CIPA'),findsOneWidget);
    expect(find.text('2 de 3'),findsOneWidget);
    expect(find.text('3 de 5'),findsOneWidget);
    expect(find.text('Ações com prazo vencido'),findsOneWidget);
    expect(find.byType(LinearProgressIndicator),findsNWidgets(2));
    expect(find.textContaining('Somente'),findsNothing);
  });

  testWidgets('Recusa métricas com empresa errada ou dados inválidos',
      (tester) async {
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:
      CipaManagerMetricsPanel(companyId:'company-A',mandateId:'mandate-A',
        serverData:sample(company:'company-B')))));
    expect(find.textContaining('Indicadores não disponíveis'),findsOneWidget);
    expect(find.byType(LinearProgressIndicator),findsNothing);
  });
}

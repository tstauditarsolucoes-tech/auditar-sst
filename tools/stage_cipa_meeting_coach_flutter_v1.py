#!/usr/bin/env python3
"""Fixture Flutter visual do roteiro CIPA usando o widget e regras reais."""
from pathlib import Path
import shutil
import sys

if len(sys.argv)!=2:
    raise SystemExit("Uso: stage_cipa_meeting_coach_flutter_v1.py <FlutterAPP>")
root=Path(sys.argv[1])
repo=Path(__file__).resolve().parents[1]
assert "name: cipa_meeting_coach_fixture" in (
    root/"pubspec.yaml").read_text(encoding="utf-8")
part=root/"lib/screens/cipa_meeting_coach_home.dart"
rules=root/"lib/services/cipa_meeting_coach_rules.dart"
for target,origin in (
    (part,repo/"feature_sources/cipa_meeting_coach_home_v1.dart"),
    (rules,repo/"feature_sources/cipa_meeting_coach_rules_v1.dart")
):
    target.parent.mkdir(parents=True,exist_ok=True)
    assert not target.exists(), "Não duplicar arquivo"
    shutil.copyfile(origin,target)
screen=root/"lib/screens/cipa_management_screen.dart"
screen.write_text(r"""import 'package:flutter/material.dart';
import '../services/cipa_meeting_coach_rules.dart';
part 'cipa_meeting_coach_home.dart';

class FakeCipaRecord {
  const FakeCipaRecord({
    required this.id,required this.companyId,required this.date,
    required this.title,required this.status,
    this.payload=const {},
    this.dueDate,
  });
  final String id,companyId,title,status;
  final DateTime date;
  final DateTime? dueDate;
  final Map<String,dynamic> payload;
}

class CipaManagementScreen extends StatefulWidget {
  const CipaManagementScreen({super.key,this.hasMandate=false});
  String get companyId=>'company-A';
  final bool hasMandate;
  @override
  State<CipaManagementScreen> createState()=>_CipaManagementScreenState();
}
class _CipaManagementScreenState extends State<CipaManagementScreen> {
  bool busy=false,opened=false;
  String get companyId=>'company-A';
  FakeCipaRecord? get activeMandate=>widget.hasMandate?
    FakeCipaRecord(id:'mandate-A',companyId:companyId,
      date:DateTime(2026,1),title:'CIPA 2026',status:'Ativo'):null;
  List<FakeCipaRecord> get activeMembers=>widget.hasMandate?[
    FakeCipaRecord(id:'m-1',companyId:companyId,date:DateTime(2026,1),
      title:'Membro',status:'Ativo',payload:{'mandateId':'mandate-A'}),
  ]:const [];
  List<FakeCipaRecord> get mandateMeetings=>widget.hasMandate?[
    FakeCipaRecord(id:'meet-A',companyId:companyId,
      title:'Reunião de novembro',date:DateTime(2030,11,16),status:'Agendada',
      payload:{'mandateId':'mandate-A','place':'Sala',
        'agenda':'Pendências de SST','memberIds':['m-1'],
        'presentIds':<String>[]}),
  ]:const [];
  List<FakeCipaRecord> get mandateMinutes=>const [];
  List<FakeCipaRecord> get mandateActions=>const [];
  void _message(String text) {}
  Future<void> _cipaGuidedMeeting()async {
    if(mounted)setState(()=>opened=true);
  }
  Future<void> _editMeeting([FakeCipaRecord? current])async {
    if(mounted)setState(()=>opened=true);
  }
  @override
  Widget build(BuildContext context)=>DefaultTabController(
    length:11,child:Scaffold(
      appBar:AppBar(title:const Text('Gestão da CIPA')),
      body:ListView(children:[
        _cipaMeetingCoachCard(),
        if(opened)const Text('EDITOR_DE_REUNIAO_ABERTO'),
      ]),
    ),
  );
}
""",encoding="utf-8")
test=root/"test/cipa_meeting_coach_widget_test.dart"
test.parent.mkdir(parents=True,exist_ok=True)
test.write_text(r"""import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:cipa_meeting_coach_fixture/screens/cipa_management_screen.dart';

void main(){
  testWidgets('Sem mandato mostra orientação, não inventa reunião',
    (tester)async{
    await tester.pumpWidget(const MaterialApp(
      home:CipaManagementScreen()));
    expect(find.text('Reunião assistida: antes e depois'),findsOneWidget);
    await tester.tap(find.text('Reunião assistida: antes e depois'));
    await tester.pumpAndSettle();
    expect(find.text('Conferir mandato'),findsWidgets);
    expect(find.textContaining('Nenhum mandato ativo'),findsOneWidget);
    expect(find.text('EDITOR_DE_REUNIAO_ABERTO'),findsNothing);
  });
  testWidgets('Com mandato abre o editor original por ação explícita',
    (tester)async{
    await tester.pumpWidget(const MaterialApp(
      home:CipaManagementScreen(hasMandate:true)));
    await tester.tap(find.text('Reunião assistida: antes e depois'));
    await tester.pumpAndSettle();
    expect(find.text('Conferir convocação'),findsOneWidget);
    expect(find.text('Depois: registrar o que ocorreu'),findsOneWidget);
    final open=find.widgetWithText(FilledButton,'Abrir reunião');
    await tester.scrollUntilVisible(open,150);
    await tester.tap(open);
    await tester.pumpAndSettle();
    expect(find.text('EDITOR_DE_REUNIAO_ABERTO'),findsOneWidget);
    expect(find.text('Conferir presenças'),findsNothing);
  });
}
""",encoding="utf-8")
template=root/"test/widget_test.dart"
if template.exists():template.unlink()
print("CIPA_MEETING_COACH_FLUTTER_UI_FIXTURE_READY")

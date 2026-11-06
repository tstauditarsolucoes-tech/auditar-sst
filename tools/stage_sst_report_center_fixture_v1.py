#!/usr/bin/env python3
"""Montar fixture Flutter para validar os seis relatórios sem backend real.

O projeto de testes utiliza exatamente os modelos, UI e PDF reais, com stubs
APENAS de autenticação, banco e tela mensal, evitando modificar dados SST.
"""
from pathlib import Path
import sys

if len(sys.argv)!=2:
    raise SystemExit("Uso: stage_sst_report_center_fixture_v1.py <FlutterAPP>")
app=Path(sys.argv[1])
repo=Path(__file__).resolve().parents[1]
pub=app/"pubspec.yaml"
assert pub.is_file() and "name: auditar_sst" in pub.read_text()
text=pub.read_text(encoding="utf-8")
assert text.count("\ndependencies:\n")==1
deps="""  intl: ^0.20.1
  pdf: ^3.11.1
  printing: ^5.13.4
  image_picker: ^1.1.2
  path_provider: ^2.1.5
  signature: ^5.5.0
"""
text=text.replace("\ndependencies:\n","\ndependencies:\n"+deps,1)
pub.write_text(text,encoding="utf-8")

copies={
    "feature_sources/sst_report_center_models_v1.dart":
       "lib/services/sst_report_center_models.dart",
    "feature_sources/sst_report_center_pdf_v1.dart":
       "lib/services/sst_report_center_pdf.dart",
    "feature_sources/sst_report_center_history_v1.dart":
       "lib/services/sst_report_center_history.dart",
    "feature_sources/sst_report_center_history_screen_v1.dart":
       "lib/screens/sst_report_center_history_screen.dart",
    "feature_sources/sst_report_center_history_test_v1.dart":
       "test/sst_report_center_history_test.dart",
    "feature_sources/sst_report_center_screen_v1.dart":
       "lib/screens/sst_report_center_screen.dart",
    "feature_sources/sst_report_center_models_test_v1.dart":
       "test/sst_report_center_models_test.dart",
}
for from_,to in copies.items():
    path=app/to
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text((repo/from_).read_text(encoding="utf-8"),
      encoding="utf-8")

stubs={
"lib/models.dart":"""class Company {
  const Company({required this.id,required this.name});
  final String id,name;
}
""",
"lib/database.dart":"""class AppDatabase {
  AppDatabase._();
  static final AppDatabase instance=AppDatabase._();
  static String activeUserId='test-user';
  static final Map<String,String> _settings={};
  Future<String> getSetting(String key) async =>_settings[key]??'';
  Future<void> setSetting(String key,String value) async {
    _settings[key]=value;
  }
}
""",
"lib/services/auth_service.dart":"""class AuthService {
  static bool canAccessCompany(String id)=>id=='company-A';
}
""",
"lib/services/offline_sst_deep_catalog_v2.dart":"""class OfflineSstDeepCatalog {
  static List<Map<String,String>> matches(String text)=>const [];
}
""",
"lib/screens/express_round_screen.dart":"""import 'package:flutter/material.dart';
import '../models.dart';
class ExpressRoundScreen extends StatelessWidget {
  const ExpressRoundScreen({super.key,required this.company});
  final Company company;
  @override
  Widget build(BuildContext context)=>const Scaffold(body:Text('Ronda Expressa'));
}
""",
"lib/screens/new_inspection_screen.dart":"""import 'package:flutter/material.dart';
import '../models.dart';
class NewInspectionScreen extends StatelessWidget {
  const NewInspectionScreen({super.key,this.initialCompany,
    this.fieldMode=false});
  final Company? initialCompany;
  final bool fieldMode;
  @override
  Widget build(BuildContext context)=>const Scaffold(body:Text('Vistoria'));
}
""",
"lib/screens/manager_reports_screen.dart":"""import 'package:flutter/material.dart';
import '../models.dart';
enum ManagerReportKind {pending,activities,resolved,monthly}
class ManagerReportsScreen extends StatelessWidget{
  const ManagerReportsScreen({super.key,required this.company,
    this.initialKind=ManagerReportKind.pending});
  final Company company;
  final ManagerReportKind initialKind;
  @override
  Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:const Text('Gerencial mensal')),
    body:Text(initialKind.name),
  );
}
""",
"test/sst_report_center_widget_test.dart":r"""import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/models.dart';
import 'package:auditar_sst/database.dart';
import 'package:auditar_sst/services/sst_report_center_history.dart';
import 'package:auditar_sst/screens/sst_report_center_screen.dart';
import 'package:auditar_sst/services/sst_report_center_models.dart';
import 'package:auditar_sst/services/sst_report_center_pdf.dart';

void main(){
  const company=Company(id:'company-A',name:'Empresa de Teste');
  testWidgets('Central oferece seis modelos e abre relatório mensal existente',
    (tester) async {
    await tester.pumpWidget(const MaterialApp(
      home:SstReportCenterScreen(company:company)));
    for(final text in [
      'Máquinas e equipamentos','Obras e canteiros',
      'Inspeção visual elétrica','Trabalho em altura',
      'Investigação de acidente/incidente','Relatório gerencial mensal',
    ]) {
      await tester.scrollUntilVisible(find.text(text),180);
      expect(find.text(text),findsOneWidget);
    }
    await tester.ensureVisible(find.text('Relatório gerencial mensal'));
    await tester.tap(find.text('Relatório gerencial mensal'));
    await tester.pumpAndSettle();
    expect(find.text('monthly'),findsOneWidget);
  });
  testWidgets('Item não verificado não habilita PDF',
    (tester) async {
    await tester.pumpWidget(const MaterialApp(
      home:SstReportCenterScreen(company:company)));
    await tester.tap(find.text('Máquinas e equipamentos'));
    await tester.pumpAndSettle();
    expect(find.text('Central de Relatórios SST'),findsNothing);
    expect(find.text('Máquinas e equipamentos'),findsOneWidget);
    final button=find.widgetWithText(FilledButton,'Revisar e gerar PDF offline');
    await tester.scrollUntilVisible(button,200);
    expect(tester.widget<FilledButton>(button).onPressed,isNull);
  });

  testWidgets('Arquivar visita preserva histórico e permite abrir em leitura',
      (tester) async {
    final saved=SstFieldDraft(
      kind:SstFieldReportKind.nr12,
      companyId:'company-A',
      technician:'Técnico de Campo',
      date:'2026-11-06',
      location:'Moinho de cavaco',
      answers:{
        'nr12-02':const SstFieldAnswer(
          status:SstFieldStatus.nonConforming,
          observation:'Correia com proteção removida na transmissão.',
          recommendation:'Recompor proteção antes do uso seguro.'),
      },
    );
    await tester.runAsync(()async{
      await AppDatabase.instance.setSetting(
        SstFieldDraftStore.key('company-A','test-user',SstFieldReportKind.nr12),
        jsonEncode(saved.toJson()));
    });
    await tester.pumpWidget(MaterialApp(home:SstFieldReportScreen(
      company:company,model:SstFieldTemplates.of(SstFieldReportKind.nr12))));
    await tester.pumpAndSettle();
    final archive=find.text('Arquivar e iniciar nova visita');
    await tester.ensureVisible(archive);
    await tester.tap(archive);
    await tester.pumpAndSettle();
    final confirm=find.descendant(
      of:find.byType(AlertDialog),
      matching:find.widgetWithText(
        FilledButton,'Arquivar e iniciar nova visita'));
    expect(confirm,findsOneWidget);
    await tester.tap(confirm);
    await tester.pumpAndSettle();
    final archived=find.text('Moinho de cavaco');
    await tester.scrollUntilVisible(archived,180);
    expect(archived,findsOneWidget);
    await tester.tap(archived);
    await tester.pumpAndSettle();
    expect(find.text('Visita arquivada • somente leitura'),findsOneWidget);
    expect(find.textContaining('Correia com proteção removida'),findsWidgets);
    await tester.runAsync(()async{
      final history=SstFieldReportHistory(
        read:AppDatabase.instance.getSetting,
        write:AppDatabase.instance.setSetting);
      final all=await history.list(companyId:'company-A',userId:'test-user',
        kind:SstFieldReportKind.nr12);
      expect(all.length,1);
      final item=await history.open(companyId:'company-A',
        userId:'test-user',kind:SstFieldReportKind.nr12,id:all.first.id);
      expect(item.draft.location,'Moinho de cavaco');
      final fresh=await SstFieldDraftStore.load(
        'company-A','test-user',SstFieldReportKind.nr12);
      expect(fresh.reviewed,0);
    });
  });
  test('PDF local só usa itens realmente revisados e informa parcial',()async{
    final draft=SstFieldDraft(
      kind:SstFieldReportKind.nr12,
      companyId:'company-A',
      technician:'Técnico de teste',
      date:'2026-11-06',
      location:'Produção',
      answers:{
        'nr12-02':const SstFieldAnswer(
          status:SstFieldStatus.nonConforming,
          observation:'Proteção da correia removida no equipamento.',
          recommendation:'Recompor proteção e avaliar acesso seguro.')
      },
    );
    expect(draft.hasEnoughForPdf,isTrue);
    expect(draft.isPartial,isTrue);
    final bytes=await SstFieldReportPdfService.generate(
      companyName:company.name,companyId:company.id,draft:draft);
    expect(bytes,isA<Uint8List>());
    expect(bytes.length,greaterThan(1200));
    expect(String.fromCharCodes(bytes.take(4)),'%PDF');
    await expectLater(SstFieldReportPdfService.generate(
      companyName:company.name,companyId:'company-B',draft:draft),
      throwsStateError);
  });
}
""",
}
for relative,source in stubs.items():
    path=app/relative
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(source,encoding="utf-8")
template=app/"test/widget_test.dart"
if template.exists():template.unlink()
print("SST_REPORT_CENTER_SIX_MODEL_FLUTTER_FIXTURE_READY")

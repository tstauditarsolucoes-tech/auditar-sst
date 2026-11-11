#!/usr/bin/env python3
"""Fixture Flutter isolada: sem clientes reais, rede, Firebase nem credenciais."""
from pathlib import Path
import shutil
import sys

if len(sys.argv)!=2:
    raise SystemExit("Uso: stage_smart_visit_fixture_v1.py <FLUTTER_APP>")
app=Path(sys.argv[1]);repo=Path(__file__).resolve().parents[1]
lib=app/"lib"
for f in ["screens","services"]:
    (lib/f).mkdir(parents=True,exist_ok=True)

sources={
  "feature_sources/smart_visit_briefing_screen_v1.dart":
    "lib/screens/smart_visit_briefing_screen.dart",
  "feature_sources/android_visit_type_chooser_v1.dart":
    "lib/screens/visit_type_chooser_screen.dart",
  "feature_sources/visit_intelligence_v1.dart":
    "lib/services/visit_intelligence.dart",
}
for origin,destination in sources.items():
    shutil.copyfile(repo/origin,app/destination)

(lib/"models.dart").write_text("""
class Company {
  const Company({required this.id,required this.name});
  final String id,name;
}
""",encoding="utf-8")
(lib/"database.dart").write_text("""
class FakeRecord {
  const FakeRecord(this.id,this.companyId,this.status,this.payload);
  final String id,companyId,status;
  final Map<String,Object?> payload;
}
class AppDatabase {
  AppDatabase._();
  static final instance=AppDatabase._();
  bool fail=false;
  List<FakeRecord> records=[];
  Future<List<FakeRecord>> getSstRecords({String? type}) async {
    if(type!='OBSERVACAO_SEGURANCA') {
      throw StateError('Tipo de registro inesperado');
    }
    if(fail)throw StateError('Leitura local indisponível');
    return records;
  }
}
""",encoding="utf-8")
(lib/"screens"/"express_round_screen.dart").write_text("""
import 'package:flutter/material.dart';
import '../models.dart';
class ExpressRoundScreen extends StatelessWidget {
  const ExpressRoundScreen({super.key,required this.company});
  final Company company;
  @override Widget build(BuildContext context)=>
    Scaffold(body:Text('RONDA_'+company.id));
}
""",encoding="utf-8")
(lib/"screens"/"new_inspection_screen.dart").write_text("""
import 'package:flutter/material.dart';
import '../models.dart';
class NewInspectionScreen extends StatelessWidget {
  const NewInspectionScreen({
    super.key,this.initialCompany,this.fieldMode=false,
  });
  final Company? initialCompany;
  final bool fieldMode;
  @override Widget build(BuildContext context)=>
    Scaffold(body:Text('CHECKLIST_'+(initialCompany?.id??'')));
}
""",encoding="utf-8")
(lib/"screens"/"quick_visit_screen.dart").write_text("""
import 'package:flutter/material.dart';
class QuickVisitScreen extends StatelessWidget {
  const QuickVisitScreen({super.key,this.onlyRound=false});
  final bool onlyRound;
  @override Widget build(BuildContext context)=>
    const Scaffold(body:Text('SELECAO_DE_EMPRESA'));
}
""",encoding="utf-8")
(lib/"screens"/"field_quick_screen.dart").write_text("""
import 'package:flutter/material.dart';
class FieldQuickScreen extends StatelessWidget {
  const FieldQuickScreen({super.key});
  @override Widget build(BuildContext context)=>
    const Scaffold(body:Text('VISTORIA_AVULSA'));
}
""",encoding="utf-8")
shutil.copyfile(
  repo/"feature_sources/smart_visit_briefing_widget_test_v1.dart",
  app/"test/smart_visit_briefing_widget_test.dart",
)
widget=app/"test/widget_test.dart"
if widget.exists():widget.unlink()
print("SMART_VISIT_FIXTURE_READY")

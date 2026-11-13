#!/usr/bin/env python3
"""Preparar Flutter fixture do painel administrativo CIPA (sem backend real).

Não altera app de técnico e não usa dados/credenciais. Valida composição de
widgets de gestão num projeto Flutter isolado com funções simuladas.
"""
from pathlib import Path
import shutil
import sys

if len(sys.argv)!=2:
    raise SystemExit("Uso: stage_cipa_admin_ui_flutter_v1.py <flutter-fixture>")
root=Path(sys.argv[1])
repo=Path(__file__).resolve().parents[1]
assert (root/"pubspec.yaml").exists()
assert "name: cipa_admin_fixture" in (root/"pubspec.yaml").read_text()
screen=root/"lib/screens/cipa_member_admin_screen.dart"
screen.parent.mkdir(parents=True,exist_ok=True)
assert not screen.exists()
shutil.copyfile(repo/"feature_sources/cipa_member_admin_screen_v1.dart",screen)
moderator=root/"lib/widgets/cipa_mural_moderation_panel.dart"
moderator.parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(repo/"feature_sources/cipa_mural_moderation_panel_v1.dart",moderator)
for source,destination in [
    ("cipa_member_identity_v1.dart","cipa_member_identity.dart"),
    ("cipa_member_role_meetings_v1.dart","cipa_member_role_meetings.dart"),
]:
    target=root/"lib/services"/destination
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(repo/"feature_sources"/source,target)

files={
  "lib/services/auth_service.dart": """class AuthService {
  static bool get isAdmin => true;
  static String get sessionToken => 'fixture-admin-session';
}
""",
  "lib/services/web_service_config.dart": """class WebServiceConfig {
  static String get endpoint =>
    'https://script.google.com/macros/s/fixture/exec';
}
""",
  "lib/services/apps_script_http.dart": """import 'dart:convert';
class FixtureResponse {
  const FixtureResponse(this.statusCode,this.body);
  final int statusCode;
  final String body;
}
class AppsScriptHttp {
  static Future<FixtureResponse> postJson(Uri uri,Map<String,dynamic> data) async {
    return FixtureResponse(200,jsonEncode({
      'ok':true,'accounts':<Object>[],
      'events':<Object>[],
      'notices':<Object>[],
      'documents':<Object>[]
    }));
  }
}
""",
  "test/cipa_admin_screen_smoke_test.dart": """import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:cipa_admin_fixture/screens/cipa_member_admin_screen.dart';

void main() {
  testWidgets('Painel CIPA mostra cadastro individual e publicações',
      (tester) async {
    await tester.pumpWidget(const MaterialApp(home:
      CipaMemberAdminScreen(
        companyId:'empresa-A',mandateId:'mandato-A',
        members:[CipaAdminMemberOption(
          memberId:'m-1',workerId:'w-1',name:'Ana Santos',
          cipaRole:'Titular')],
        actions:[CipaAdminActionOption(id:'a-1',title:'Verificar extintor')],
        documents:[CipaAdminDocumentOption(id:'d-1',
          title:'Plano da CIPA',category:'Orientações')],
      )));
    await tester.pumpAndSettle();
    expect(find.text('Acessos da CIPA'),findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Cadastrar acesso individual'),150,
      scrollable:find.byType(Scrollable).first);
    expect(find.text('Cadastrar acesso individual'),findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Vincular tarefa a integrante'),180,
      scrollable:find.byType(Scrollable).first);
    expect(find.text('Vincular tarefa a integrante'),findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Publicar comunicado da CIPA'),180,
      scrollable:find.byType(Scrollable).first);
    expect(find.text('Publicar comunicado da CIPA'),findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Liberar documento para consulta'),180,
      scrollable:find.byType(Scrollable).first);
    expect(find.text('Liberar documento para consulta'),findsOneWidget);
    expect(find.text('Gerenciar usuários'),findsNothing);
  });
}
""",
}
for relative,content in files.items():
    target=root/relative
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(content,encoding="utf-8")
template=root/"test/widget_test.dart"
if template.exists():template.unlink()
assert "CipaAdminDocumentOption" in screen.read_text()
assert "cipa_member_admin_publish_notice" in screen.read_text()
print("CIPA_STAFF_ADMIN_FLUTTER_FIXTURE_READY")

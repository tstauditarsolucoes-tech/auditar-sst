#!/usr/bin/env python3
"""Estende a fixture Flutter CIPA com relato de homologação, sem dados reais."""
import pathlib
import shutil
import sys

root=pathlib.Path(sys.argv[1])
service=root/"lib/services/apps_script_http.dart"
content=service.read_text(encoding="utf-8")
old="class AppsScriptHttp {\n  static Future<FixtureResponse> postJson(Uri uri,Map<String,dynamic> data) async {\n"
new="class AppsScriptHttp {\n  static final List<Map<String,dynamic>> requests=[];\n  static Future<FixtureResponse> postJson(Uri uri,Map<String,dynamic> data) async {\n    requests.add(Map<String,dynamic>.from(data));\n"
assert old in content
content=content.replace(old,new)
old_events="'events':<Object>[],"
new_events="""'events':<Object>[
        {'id':'observation-fixture-A','companyId':'empresa-A',
         'mandateId':'mandato-A','memberId':'member-A',
         'kind':'observation','location':'Produção',
         'detail':'VISTORIA ORIENTADA DA CIPA — OBSERVAÇÃO VISUAL',
         'status':'Recebido'},
      ],"""
assert old_events in content
service.write_text(content.replace(old_events,new_events),encoding="utf-8")
shutil.copyfile(pathlib.Path(__file__).resolve().parents[1]/
  "feature_sources/cipa_admin_review_smoke_test_v1.dart",
  root/"test/cipa_admin_review_smoke_test.dart")
print("CIPA_ADMIN_REVIEW_FIXTURE_READY")

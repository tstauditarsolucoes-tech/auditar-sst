#!/usr/bin/env python3
"""Smoke-test the navigation audit's distinction between reachable and unused."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from audit_navigation_inventory_v1 import scan, markdown

with TemporaryDirectory() as tmp:
    root=Path(tmp)
    screens=root/"lib"/"screens"
    screens.mkdir(parents=True)
    (root/"lib"/"main.dart").write_text(
        "import 'screens/home_screen.dart';\nvoid main() {}\n",encoding="utf-8")
    (screens/"home_screen.dart").write_text(
        "import 'records_screen.dart';\n"
        "class HomeScreen extends StatelessWidget {\n"
        "Widget build(context)=>Text('Início');\n"
        "final shortcut=ListTile(title: Text('Pendências'));\n}\n",encoding="utf-8")
    (screens/"records_screen.dart").write_text(
        "class RecordsScreen extends StatefulWidget {\n"
        "final button=Button(label: const Text('Pendências'));\n}\n",encoding="utf-8")
    (screens/"orphan_screen.dart").write_text(
        "class OrphanScreen extends StatelessWidget {}\n",encoding="utf-8")
    (screens/"broken.dart").write_text(
        "import 'does_not_exist.dart';\n"
        "final button=Button(onPressed: () {});\n"
        "void missing()=>throw UnimplementedError();\n",encoding="utf-8")
    (root/"painel_web_google_apps_script").mkdir()
    (root/"painel_web_google_apps_script"/"Code.gs").write_text(
        "if(request.action==='client_treatment_v2'){}\n",encoding="utf-8")
    report=scan(root)
    assert report["screen_file_count"]==3,report
    assert report["statically_reachable_screen_count"]==2,report
    assert len(report["potentially_unreachable_screens"])==1
    assert report["potentially_unreachable_screens"][0]["file"]==\
        "lib/screens/orphan_screen.dart"
    assert report["repeated_navigation_labels"][0]["label"]=="Pendências"
    assert len(report["missing_local_imports"])==1
    assert {i["kind"] for i in report["potentially_inert_handlers"]} == {
        "empty_click_handler", "unimplemented_exception"}
    assert report["backend_route_candidates"][2]["production_deployment_verified"] is False
    assert "não remover" in markdown(report).lower()
    serialized=json.loads(json.dumps(report,ensure_ascii=False))
    assert serialized["screen_file_count"]==3
print("AUDITAR_NAVIGATION_AUDIT_TEST_OK")

#!/usr/bin/env python3
"""Regressão sem dados reais da montagem consolidada e do atalho Windows."""
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile

repo=Path(__file__).resolve().parents[1]
integrator=repo/"tools/integrate_sst_homologation_v1.py"
windows=repo/"tools/patch_windows_smart_visit_v1.py"
with tempfile.TemporaryDirectory(prefix="auditar-integration-guard-") as temp:
    root=Path(temp)
    result=subprocess.run([sys.executable,str(integrator),str(root),"android"],
        text=True,capture_output=True)
    assert result.returncode!=0 and not list(root.rglob("*")), (
        "App incompleto não pode receber patches nem gerar binário.")
    result=subprocess.run([sys.executable,str(integrator),str(root),"web"],
        text=True,capture_output=True)
    assert result.returncode!=0, "Não aplicar estes patches no projeto Web."
    (root/"lib/screens").mkdir(parents=True)
    (root/"lib/services").mkdir(parents=True)
    (root/"painel_web_google_apps_script").mkdir(parents=True)
    quick=root/"lib/screens/quick_visit_screen.dart"
    quick.write_text("""import 'express_round_screen.dart';
class FakeCompanyScreen {
  Widget render(Company c) => Column(children:[
          _action(
            'Nova ronda',
            'Fotos e descrição das situações encontradas',
            Icons.add_a_photo_outlined,
            ExpressRoundScreen(company: c),
          ),
  ]);
}
""",encoding="utf-8")
    protected={
      root/"lib/database.dart":"DATABASE_INALTERADO",
      root/"lib/services/auth_service.dart":"LOGIN_INALTERADO",
      root/"lib/services/device_sync_service.dart":"SYNC_INALTERADO",
      root/"painel_web_google_apps_script/Code.gs":"GS_INALTERADO",
    }
    for p,data in protected.items():p.write_text(data,encoding="utf-8")
    expected={p:hashlib.sha256(p.read_bytes()).hexdigest()
        for p in protected}
    one=subprocess.run([sys.executable,str(windows),str(root)],
      text=True,capture_output=True)
    assert one.returncode==0,(one.stdout,one.stderr)
    assert quick.read_text().count("Preparar Visita Inteligente")==1
    assert (root/"lib/screens/smart_visit_briefing_screen.dart").is_file()
    assert (root/"lib/services/visit_intelligence.dart").is_file()
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==v
        for p,v in expected.items()),"Arquivo protegido foi alterado"
    again=subprocess.run([sys.executable,str(windows),str(root)],
      text=True,capture_output=True)
    assert again.returncode!=0,"Não pode duplicar item no menu"
    assert quick.read_text().count("SmartVisitBriefingScreen(company: c)")==1
    print("SST_INTEGRATION_FAIL_CLOSED_AND_WINDOWS_SMART_VISIT_OK")

#!/usr/bin/env python3
"""Executa o patch contra uma fixture de empresa e gerente; confere núcleo intacto."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import hashlib

repo=Path(__file__).resolve().parents[1]
patch=repo/"tools/patch_sst_report_center_v1.py"
with tempfile.TemporaryDirectory(prefix="auditar-reports-integration-") as tmp:
    root=Path(tmp)
    screens=root/"lib/screens"
    services=root/"lib/services"
    backend=root/"painel_web_google_apps_script"
    for folder in (screens,services,backend):folder.mkdir(parents=True,exist_ok=True)
    company=screens/"company_detail_screen.dart"
    company.write_text("""import 'manager_reports_screen.dart';
class Demo {
  dynamic build() {
    return [
        _shortcut(
          icon: Icons.summarize_outlined,
          title: 'Relatórios gerenciais',
          subtitle: 'Pendências, ações, atividades e correções da empresa',
          onTap: () => _open(ManagerReportsScreen(company: widget.company)),
        ),
    ];
  }
}
""",encoding="utf-8")
    manager=screens/"manager_reports_screen.dart"
    shutil.copyfile(repo/"feature_sources/manager_reports_module_v329169.dart",manager)
    core=services/"auth_service.dart"
    core.write_text("AUTH PROTECTED")
    gs=backend/"Code.gs"
    gs.write_text("GS PROTECTED")
    snapshots={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in (core,gs)}
    result=subprocess.run([sys.executable,str(patch),str(root)],
       text=True,capture_output=True)
    assert result.returncode==0,(result.stdout,result.stderr)
    assert "SST_REPORT_CENTER_SIX_ENTRY_READY" in result.stdout
    assert company.read_text().count("SstReportCenterScreen(company: widget.company)")==1
    assert "ManagerReportKind.monthly" in (
      screens/"sst_report_center_screen.dart").read_text()
    assert manager.read_text().count("kind=widget.initialKind;")==1
    assert len(list(services.glob("sst_report_center_*")))==2
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==d
        for p,d in snapshots.items())
    unchanged={
      p:hashlib.sha256(p.read_bytes()).hexdigest()
      for p in (company,manager)
    }
    duplicate=subprocess.run([sys.executable,str(patch),str(root)],
      text=True,capture_output=True)
    assert duplicate.returncode!=0
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==d
      for p,d in unchanged.items())
    print("SST_REPORT_CENTER_INTEGRATION_SAFE_OK")

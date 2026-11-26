#!/usr/bin/env python3
"""Teste rápido: integração do relatório gerencial formatado e legada.

Funciona em diretório temporário, sem banco, sincronização ou servidor.
"""
from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import tempfile

repo = Path(__file__).resolve().parents[1]
source = (repo / "feature_sources/manager_reports_module_v329169.dart").read_text(encoding="utf-8")
inline = "  void initState() { super.initState(); _load(); }"
assert source.count(inline) == 1

variants = {
    "inline": inline,
    "multiline": "  void initState() {\n    super.initState();\n    _load();\n  }",
    "additional_init": "  void initState() {\n    super.initState();\n    _load();\n    final ignored = 1;\n    assert(ignored == 1);\n  }",
}
for label, replacement in variants.items():
    with tempfile.TemporaryDirectory(prefix="sst-report-manager-format-") as tmp:
        app = Path(tmp)
        screens = app / "lib/screens"
        screens.mkdir(parents=True)
        (app / "lib/services").mkdir(parents=True)
        gs = app / "painel_web_google_apps_script"
        gs.mkdir(parents=True)
        company = screens / "company_detail_screen.dart"
        company.write_text("""import 'manager_reports_screen.dart';
class Demo {
  dynamic build() => [
    _shortcut(
      icon: Icons.summarize_outlined,
      title: 'Relatórios gerenciais',
      subtitle: 'Relatórios e ações gerenciais',
      onTap: () => _open(ManagerReportsScreen(company: widget.company)),
    ),
  ];
}
""", encoding="utf-8")
        manager = screens / "manager_reports_screen.dart"
        manager.write_text(source.replace(inline, replacement, 1), encoding="utf-8")
        auth = app / "lib/services/auth_service.dart"
        auth.write_text("AUTH ORIGINAL", encoding="utf-8")
        data = app / "lib/database.dart"
        data.write_text("BANCO ORIGINAL", encoding="utf-8")
        core = gs / "Code.gs"
        core.write_text("APPS SCRIPT ORIGINAL", encoding="utf-8")
        protected = {p: hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in (auth, data, core)}
        run = subprocess.run([
            sys.executable, str(repo / "tools/patch_sst_report_center_v1.py"),
            str(app),
        ], capture_output=True, text=True)
        assert run.returncode == 0, (label, run.stdout, run.stderr)
        assert "SST_REPORT_CENTER_SIX_ENTRY_READY" in run.stdout
        updated = manager.read_text(encoding="utf-8")
        assert updated.count("kind=widget.initialKind;") == 1, label
        assert updated.count("final ManagerReportKind initialKind;") == 1, label
        assert "_load();" in updated and "super.initState();" in updated
        assert company.read_text().count(
            "SstReportCenterScreen(company: widget.company)") == 1
        assert all(hashlib.sha256(p.read_bytes()).hexdigest() == digest
                   for p, digest in protected.items())
        assert (screens / "sst_risk_documents_screen.dart").is_file()
        assert (screens / "sst_pet_nr33_screen.dart").is_file()
        assert (screens / "sst_document_signature_panel.dart").is_file()
        print("REPORT_MANAGER_INITSTATE_FORMAT_OK", label)

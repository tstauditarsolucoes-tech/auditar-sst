#!/usr/bin/env python3
"""Valida instalação do acesso offline na Biblioteca Técnica sem usar dados reais."""
from pathlib import Path
import subprocess
import sys
import tempfile

repo=Path(__file__).resolve().parents[1]
script=repo/"tools/patch_nrs_browser_entry_v1.py"

with tempfile.TemporaryDirectory(prefix="auditar-nrs-browser-") as temp:
    root=Path(temp)
    screens=root/"lib/screens"
    services=root/"lib/services"
    tests=root/"test"
    for d in (screens,services,tests):d.mkdir(parents=True)
    status=screens/"offline_knowledge_status_screen.dart"
    status.write_bytes(
      (repo/"feature_sources/offline_knowledge_status_screen_v329179.dart").read_bytes())
    (services/"offline_sst_deep_catalog_v2.dart").write_text(
      "class OfflineSstDeepCatalog {}\n",encoding="utf-8")
    (services/"offline_sst_all_nrs_v1.dart").write_text(
      "class OfflineSstAllNrsCatalog {}\n",encoding="utf-8")
    untouched=(services/"offline_sst_deep_catalog_v2.dart").read_bytes()
    result=subprocess.run([sys.executable,str(script),str(root)],
        capture_output=True,text=True)
    assert result.returncode==0,(result.stdout,result.stderr)
    text=status.read_text(encoding="utf-8")
    assert text.count("OfflineSstNrsBrowserScreen()")==1
    assert text.count("Consultar Biblioteca Técnica por NR")==1
    assert "OfflineKnowledgeCloudService.sync();" in text
    assert (screens/"offline_sst_nrs_browser_screen.dart").is_file()
    assert (tests/"offline_sst_nrs_browser_test.dart").is_file()
    assert (services/"offline_sst_deep_catalog_v2.dart").read_bytes()==untouched
    # Confirm that the installation script never installs twice accidentally.
    before={p:p.read_bytes() for p in [
      status,screens/"offline_sst_nrs_browser_screen.dart",
      tests/"offline_sst_nrs_browser_test.dart"]}
    repeated=subprocess.run([sys.executable,str(script),str(root)],
        capture_output=True,text=True)
    assert repeated.returncode!=0
    assert all(p.read_bytes()==v for p,v in before.items())
    print("NR_LIBRARY_DIRECT_ACCESS_SAFE_OK")

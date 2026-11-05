#!/usr/bin/env python3
"""Testa montagem acumulativa da biblioteca em fixture, sem aplicativo real."""
from pathlib import Path
import subprocess
import sys
import tempfile

repo=Path(__file__).resolve().parents[1]

with tempfile.TemporaryDirectory(prefix="auditar-nrs-") as temp:
    root=Path(temp)
    services=root/"lib/services"
    widgets=root/"lib/widgets"
    tests=root/"test"
    for folder in (services,widgets,tests): folder.mkdir(parents=True)
    (services/"offline_sst_deep_catalog_v2.dart").write_bytes(
        (repo/"feature_sources/offline_sst_deep_catalog_v2.dart").read_bytes())
    (tests/"offline_sst_deep_catalog_test.dart").write_bytes(
        (repo/"feature_sources/offline_sst_deep_catalog_test_v2.dart").read_bytes())
    widget="""import '../services/offline_sst_deep_catalog_v2.dart';
class _Fixture {
  void open() {
    const areas = <String>['Todas','NR-12','NR-06','NR-17','NR-18','NR-23','NR-31','NR-35','Outras'];
                    for(final area in areas) Padding(
                      padding:const EdgeInsets.only(right:6),
                      child:ChoiceChip(label:Text(area),selected:selected==area,
                        onSelected:(v) {if(v) refresh(()=>selected=area);}),
                    ),
  }
}
"""
    (widgets/"offline_report_inline_suggestions.dart").write_text(widget,encoding="utf-8")
    original=(services/"offline_sst_deep_catalog_v2.dart").read_bytes()
    # Use the real previous NR-12 patch; catches interference from the new one.
    for name in ("patch_nr12_bakery_library_v1.py","patch_all_nrs_library_v1.py"):
        result=subprocess.run([sys.executable,str(repo/"tools"/name),str(root)],
            capture_output=True,text=True)
        if result.returncode:
            raise AssertionError(name+": "+result.stdout+"\n"+result.stderr)
    final=(services/"offline_sst_deep_catalog_v2.dart").read_text(encoding="utf-8")
    assert "...OfflineSstBakeryNr12Catalog.entries," in final
    assert "...OfflineSstAllNrsCatalog.entries," in final
    assert "e['browseOnly'] != 'true'" in final
    assert "int limit=500" in final
    assert final.count("...OfflineSstAllNrsCatalog.entries,")==1
    assert "PopupMenuButton<String>" in (widgets/"offline_report_inline_suggestions.dart").read_text()
    assert "expect(all.length,345)" in (tests/"offline_sst_deep_catalog_test.dart").read_text()
    assert (services/"offline_sst_bakery_nr12_v1.dart").is_file()
    assert (services/"offline_sst_all_nrs_v1.dart").is_file()
    assert (tests/"offline_sst_all_nrs_test.dart").is_file()
    assert len(original)>50000
    # Fail closed on a duplicate install and keep bytes exactly unchanged.
    snapshot={p:p.read_bytes() for p in [*services.glob("*"),*widgets.glob("*"),*tests.glob("*")]}
    repeat=subprocess.run([sys.executable,str(repo/"tools/patch_all_nrs_library_v1.py"),str(root)],
        capture_output=True,text=True)
    assert repeat.returncode!=0, "Duplicate installation unexpectedly allowed"
    assert all(p.read_bytes()==data for p,data in snapshot.items())
    print("ALL_NRS_SAFE_PATCH_CHAIN_OK")

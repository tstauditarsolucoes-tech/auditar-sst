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
                    ListTile(
                      subtitle:Text((item['nr'] ?? '')+' • '+(item['risk'] ?? '')),
                        onTap:(){
                          final id=item['id'] ?? '';
                        },
                    ),
  }
  static double _score(OfflineInlineSuggestion item, String query, String context) {
    final title = _normalize(item.title);
    return 0;
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
    assert "expect(entries.length, 345)" in (tests/"offline_sst_bakery_nr12_test.dart").read_text()
    widget_final=(widgets/"offline_report_inline_suggestions.dart").read_text()
    assert "Apenas consulta" in widget_final
    assert "item.id.startsWith('all-nrs-15-')" in widget_final
    assert "if (item['browseOnly'] == 'true')" in widget_final
    assert (services/"offline_sst_bakery_nr12_v1.dart").is_file()
    assert (services/"offline_sst_all_nrs_v1.dart").is_file()
    assert (tests/"offline_sst_all_nrs_test.dart").is_file()
    assert len(original)>50000
    # Dart compila os três catálogos unidos e executa a busca real, não
    # apenas verifica substrings do patch ou JSON dos modelos.
    runtime=root/"test/offline_all_nrs_runtime.dart"
    runtime.write_text(r"""import '../lib/services/offline_sst_deep_catalog_v2.dart';
import '../lib/services/offline_sst_all_nrs_v1.dart';
void main() {
  final all=OfflineSstDeepCatalog.entries;
  assert(all.length==345, '145+49+151');
  assert(all.map((e)=>e['id']).toSet().length==345);
  assert(OfflineSstAllNrsCatalog.activeStandards.length==36);
  assert(OfflineSstDeepCatalog.browse(limit:500).length==345);
  assert(OfflineSstDeepCatalog.browse(standard:'Panificação').length==49);
  assert(OfflineSstDeepCatalog.browse(standard:'NR-02').isEmpty);
  assert(OfflineSstDeepCatalog.browse(standard:'NR-27').isEmpty);
  for(final nr in OfflineSstAllNrsCatalog.activeStandards) {
    final items=OfflineSstDeepCatalog.browse(standard:nr);
    assert(items.isNotEmpty, nr);
    assert(items.every((e)=>e['nr']==nr), nr);
  }
  final cases=<String,String>{
    'Amassadeira sem grade':'bakery-nr12-ama-grade-ausente',
    'PGR risco ausente':'all-nrs-01-01',
    'CIPA sem ata':'all-nrs-05-01',
    'Quadro elétrico sem tampa':'all-nrs-10-01',
    'Espaço confinado sem PET':'all-nrs-33-01',
    'Trabalho em altura sem AR':'all-nrs-35-01',
    'Coleta urbana sem sinalização':'all-nrs-38-01',
  };
  for(final e in cases.entries) {
    assert(OfflineSstDeepCatalog.matches(e.key)
        .any((v)=>v['id']==e.value),e.key);
  }
  assert(OfflineSstDeepCatalog.matches(
    'CIPA sem ata, já corrigida').isEmpty);
  assert(OfflineSstDeepCatalog.matches(
    'Máquina funcionando normalmente').isEmpty);
  for(final nr in const {'NR-03','NR-15','NR-16','NR-28'}) {
    final entries=OfflineSstDeepCatalog.browse(standard:nr);
    assert(entries.where((e)=>e['id']!.startsWith('all-nrs-'))
        .every((e)=>e['browseOnly']=='true'),nr);
  }
  assert(OfflineSstDeepCatalog.matches('NR-15 ruído acima do limite sem laudo')
      .where((e)=>e['id']!.startsWith('all-nrs-15-')).isEmpty);
  print('ALL_NRS_INTEGRATED_DART_RUNTIME_OK');
}
""",encoding="utf-8")
    runtime_result=subprocess.run(
        ["dart","--enable-asserts",str(runtime)],
        capture_output=True,text=True)
    if runtime_result.returncode:
        raise AssertionError(
            "Dart runtime falhou: "+runtime_result.stdout+
            "\\n"+runtime_result.stderr)
    print(runtime_result.stdout.strip())
    # Fail closed on a duplicate install and keep bytes exactly unchanged.
    snapshot={p:p.read_bytes() for p in [*services.glob("*"),*widgets.glob("*"),*tests.glob("*")]}
    repeat=subprocess.run([sys.executable,str(repo/"tools/patch_all_nrs_library_v1.py"),str(root)],
        capture_output=True,text=True)
    assert repeat.returncode!=0, "Duplicate installation unexpectedly allowed"
    assert all(p.read_bytes()==data for p,data in snapshot.items())
    print("ALL_NRS_SAFE_PATCH_CHAIN_OK")

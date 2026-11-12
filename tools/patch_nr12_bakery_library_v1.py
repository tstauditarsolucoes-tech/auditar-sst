#!/usr/bin/env python3
"""Android: amplia o acervo offline NR-12 panificação sem alterar o núcleo.

Aplicar APÓS tools/patch_sst_deep_catalog_v2.py e cópia do teste existente.
Não altera sincronização, dados, modelos antigos, IA, PDF, fotos ou NRs antigas.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv)!=2:
    raise SystemExit("Uso: patch_nr12_bakery_library_v1.py <APP_DIR>")
root=Path(sys.argv[1])
repo=Path(__file__).resolve().parents[1]
catalog=root/"lib/services/offline_sst_deep_catalog_v2.dart"
bakery=root/"lib/services/offline_sst_bakery_nr12_v1.dart"
widget=root/"lib/widgets/offline_report_inline_suggestions.dart"
old_test=root/"test/offline_sst_deep_catalog_test.dart"
new_test=root/"test/offline_sst_bakery_nr12_test.dart"
assert catalog.is_file() and widget.is_file() and old_test.is_file(), (
    "Biblioteca detalhada original ausente; não modificar o projeto")
assert not bakery.exists() and not new_test.exists(), (
    "Extensão de panificação já existente; não duplicar entradas")

allowed={catalog,widget,old_test,bakery,new_test}
protected={
    p:hashlib.sha256(p.read_bytes()).hexdigest()
    for folder in (root/"lib",root/"painel_web_google_apps_script")
    if folder.is_dir()
    for p in folder.rglob("*")
    if p.is_file() and p not in allowed
}

def once(source,old,new,context):
    count=source.count(old)
    if count!=1:
        raise RuntimeError(f"{context}: encontrado {count} trecho(s) (esperado 1)")
    return source.replace(old,new,1)

source=catalog.read_text(encoding="utf-8")
source=once(source,
    "class OfflineSstDeepCatalog {",
    "import 'offline_sst_bakery_nr12_v1.dart';\n\n"
    "class OfflineSstDeepCatalog {",
    "import NR-12 Panificação")
source=once(source,
    "  static const entries=<Map<String,String>>[",
    "  static const entries=<Map<String,String>>[\n"
    "    ...OfflineSstBakeryNr12Catalog.entries,",
    "catálogo adicional: sem substituir registros")
source=once(source,
    "static const focusAreas=['NR-12','NR-06'",
    "static const focusAreas=['NR-12','Panificação','NR-06'",
    "categoria específica")
source=once(source,
    "    int limit=150,",
    "    int limit=250,",
    "exibir catálogo ampliado")
source=once(source,
    """      if(standard!='Todas' &&
        !(standard=='Outras' ? !highlighted.contains(nr) : nr==standard)) {
        return false;
      }""",
    """      if(standard=='Panificação') {
        if(!(item['id'] ?? '').startsWith('bakery-nr12-')) return false;
      } else if(standard!='Todas' &&
        !(standard=='Outras' ? !highlighted.contains(nr) : nr==standard)) {
        return false;
      }""",
    "filtro sem misturar NRs")
# The original 145 rows are unchanged; only the 49 imported models are added.
catalog.write_text(source,encoding="utf-8",newline="\n")
shutil.copyfile(repo/"feature_sources/offline_sst_bakery_nr12_v1.dart",bakery)

ui=widget.read_text(encoding="utf-8")
ui=once(ui,
    "'Todas','NR-12','NR-06'",
    "'Todas','NR-12','Panificação','NR-06'",
    "aba Panificação na consulta offline")
widget.write_text(ui,encoding="utf-8",newline="\n")

test=old_test.read_text(encoding="utf-8")
test=once(test,
    "acervo detalhado: 145 casos",
    "acervo detalhado: 194 casos",
    "rótulo do teste")
test=once(test,"expect(all.length,145);","expect(all.length,194);",
          "total de modelos")
test=once(test,"expect(all.map((e)=>e['id']).toSet().length,145);",
          "expect(all.map((e)=>e['id']).toSet().length,194);",
          "unicidade de IDs")
old_test.write_text(test,encoding="utf-8",newline="\n")
shutil.copyfile(
    repo/"feature_sources/offline_sst_bakery_nr12_test_v1.dart",new_test)

for p,digest in protected.items():
    assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,str(p)
assert "OfflineSstBakeryNr12Catalog.entries" in catalog.read_text()
assert "'Panificação'" in widget.read_text()
print("NR12_BAKERY_LIBRARY_READY: 49 casos novos + 145 antigos, apenas Android")
print("CORE_AUTH_SYNC_DB_MEDIA_DRIVE_AI_GS_REPORTS_BYTE_IDENTICAL")

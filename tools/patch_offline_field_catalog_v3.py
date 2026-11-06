#!/usr/bin/env python3
"""Amplia acervo offline existente, sem mudar as telas ou o relatório.

Executar APÓS patch_sst_deep_catalog_v2.py (Android ou Windows).
Preserva os 145 modelos anteriores; acrescenta 59 de campo com segmento,
consulta por palavras e gatilhos tema + falha. Não altera regras de prioridade,
armazenamento, PDF, login, sincronização, IA nem Central.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv) != 2:
    raise SystemExit("Uso: patch_offline_field_catalog_v3.py <APP_DIR>")
root=Path(sys.argv[1])
repo=Path(__file__).resolve().parents[1]
catalog=root/"lib/services/offline_sst_deep_catalog_v2.dart"
added=root/"lib/services/offline_sst_field_catalog_v3.dart"
existing_test=root/"test/offline_sst_deep_catalog_test.dart"
new_test=root/"test/offline_sst_field_catalog_v3_test.dart"
assert catalog.is_file() and existing_test.is_file(), "Instale primeiro biblioteca v2 e testes."
assert not added.exists() and not new_test.exists(), "Biblioteca v3 já instalada."
protected={
    p:hashlib.sha256(p.read_bytes()).hexdigest()
    for folder in (root/"lib",root/"test",root/"painel_web_google_apps_script")
    if folder.is_dir()
    for p in folder.rglob("*")
    if p.is_file() and p not in {catalog,existing_test,added,new_test}
}
def exactly(s,old,new,label):
    n=s.count(old)
    if n!=1:raise RuntimeError(f"{label}: {n} ocorrências; não aplicar")
    return s.replace(old,new,1)

s=catalog.read_text(encoding="utf-8")
s=exactly(s,"class OfflineSstDeepCatalog {",
    "import 'offline_sst_field_catalog_v3.dart';\n\nclass OfflineSstDeepCatalog {",
    "import da nova biblioteca")
s=exactly(s,"static const entries=<Map<String,String>>[",
    "static const _baseEntries=<Map<String,String>>[",
    "acervo anterior")
s=exactly(s,"  ];\n  static const focusAreas=",
    """  ];
  /// Modelos anteriores mantidos + expansão setorial, sem duplicar IDs.
  static final List<Map<String,String>> entries =
      List<Map<String,String>>.unmodifiable(<Map<String,String>>[
    ..._baseEntries,
    ...OfflineSstFieldCatalogV3.entries,
  ]);
  static const focusAreas=""",
    "composição dos acervos")
s=exactly(s,
    "nao verificado|nao confirmado|talvez|suspeita|ja corrigido|regularizado|funcionando normalmente|sem irregularidade",
    "nao verificad[oa]s?|nao confirmad[oa]s?|talvez|suspeita|ja corrigid[oa]s?|regularizad[oa]s?|funcionando normalmente|sem irregularidade",
    "descrições de situação não confirmada (feminino e plural)")
s=exactly(s,"    int limit=150,","    int limit=250,",
    "limite de consulta para todos os modelos")
s=exactly(s,"(item['risk'] ?? '')+' '+(item['recommendation'] ?? '')+' '+nr);",
    "(item['risk'] ?? '')+' '+(item['recommendation'] ?? '')+' '+nr+' '+(item['segment'] ?? ''));",
    "busca também pelo setor")

t=existing_test.read_text(encoding="utf-8")
t=exactly(t,"expect(all.length,145);","expect(all.length,204);",
    "quantidade total esperada")
# A referência nos testes passa a refletir os 145 originais + 59 novos.
t=exactly(t,"acervo detalhado: 145 casos","acervo detalhado: 204 casos",
    "título da regressão")

shutil.copyfile(repo/"feature_sources/offline_sst_field_catalog_v3.dart",added)
shutil.copyfile(repo/"feature_sources/offline_sst_field_catalog_v3_test.dart",new_test)
catalog.write_text(s,encoding="utf-8",newline="\n")
existing_test.write_text(t,encoding="utf-8",newline="\n")
for p,digest in protected.items():
    assert hashlib.sha256(p.read_bytes()).hexdigest()==digest, (
        "Arquivo fora do escopo alterado: "+str(p))
for needle in ["..._baseEntries","...OfflineSstFieldCatalogV3.entries","int limit=250"]:
    assert needle in s,needle
assert "expect(all.length,204)" in t
print("OFFLINE_FIELD_CATALOG_V3_READY_145_PLUS_59_204_NO_CORE_CHANGE")

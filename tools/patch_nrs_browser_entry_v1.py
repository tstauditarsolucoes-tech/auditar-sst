#!/usr/bin/env python3
"""Link direto da Biblioteca Técnica online ao catálogo offline por NR.

Somente UI Android: mantém a Central, fila de aprendizado, autenticação,
sincronização, banco, fotos e fluxos originais byte-a-byte inalterados.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv)!=2:
    raise SystemExit("Uso: patch_nrs_browser_entry_v1.py <APP_DIR>")
root=Path(sys.argv[1])
repo=Path(__file__).resolve().parents[1]
status=root/"lib/screens/offline_knowledge_status_screen.dart"
dest=root/"lib/screens/offline_sst_nrs_browser_screen.dart"
test=root/"test/offline_sst_nrs_browser_test.dart"
catalog=root/"lib/services/offline_sst_deep_catalog_v2.dart"
allnrs=root/"lib/services/offline_sst_all_nrs_v1.dart"
assert all(p.is_file() for p in (status,catalog,allnrs)), (
    "Biblioteca de status e catálogos precisam estar montados")
assert not dest.exists() and not test.exists(), "Tela de consulta já instalada"

allowed={status,dest,test}
protected={
    p:hashlib.sha256(p.read_bytes()).hexdigest()
    for folder in (root/"lib",root/"painel_web_google_apps_script")
    if folder.is_dir()
    for p in folder.rglob("*")
    if p.is_file() and p not in allowed
}
def once(src,old,new,why):
    count=src.count(old)
    if count!=1:
        raise RuntimeError(f"{why}: {count} ocorrências; esperado 1")
    return src.replace(old,new,1)

s=status.read_text(encoding="utf-8")
assert "Future<void> _refreshStatus()" in s, (
    "A tela instalada não fornece atualização de status local; verificar a versão")

s=once(s,
    "import '../services/offline_knowledge_cloud_service.dart';",
    "import '../services/offline_knowledge_cloud_service.dart';\n"
    "import 'offline_sst_nrs_browser_screen.dart';",
    "importar consulta por NR")
s=once(s,
    """            const SizedBox(height:16),
            Card(child:Padding(""",
    """            const SizedBox(height:16),
            Card(child:ListTile(
              leading:const Icon(Icons.menu_book_outlined),
              title:const Text('Consultar Biblioteca Técnica por NR'),
              subtitle:const Text('Modelos embarcados no aplicativo, '
                'disponíveis mesmo sem internet.'),
              trailing:const Icon(Icons.chevron_right),
              onTap:() async {
                await Navigator.of(context).push(
                  MaterialPageRoute(builder:(_)=>
                    const OfflineSstNrsBrowserScreen()));
                // Atualiza os indicadores locais após retornar à biblioteca.
                // Não envia arquivos/credenciais automaticamente à Central.
                if(context.mounted) await _refreshStatus();
              },
            )),
            const SizedBox(height:12),
            Card(child:Padding(""",
    "atalho offline antes do status da nuvem")
status.write_text(s,encoding="utf-8",newline="\n")
shutil.copyfile(
    repo/"feature_sources/offline_sst_nrs_browser_screen_v1.dart",dest)
shutil.copyfile(
    repo/"feature_sources/offline_sst_nrs_browser_test_v1.dart",test)
for p,checksum in protected.items():
    assert hashlib.sha256(p.read_bytes()).hexdigest()==checksum,str(p)
assert "OfflineSstNrsBrowserScreen()" in status.read_text()
print("ALL_NRS_DIRECT_BROWSE_ONLINE_STATUS_UI_OK: CORE UNCHANGED")

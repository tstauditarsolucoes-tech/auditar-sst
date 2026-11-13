#!/usr/bin/env python3
"""Inicializa SQLite FFI nos testes de PDF e isola DBs fictícios de sync.

Somente arquivos test/*.dart do projeto temporário. Nenhuma mudança em
lib/, bases reais, autenticação, sincronização ou relatórios de clientes.
"""
from pathlib import Path
import hashlib
import sys

if len(sys.argv)!=2:
    raise SystemExit("Uso: patch_homologation_flutter_test_fixtures_v20261113.py <APP_DIR>")
root=Path(sys.argv[1]).resolve()
targets=[
  root/"test/ronda_load_50_test.dart",
  root/"test/ronda_report_models_test.dart",
  root/"test/device_sync_roundtrip_test.dart",
]
if not all(x.is_file() for x in targets):
    raise RuntimeError("Fixtures faltando, montagem inesperada; não modificar.")
assert (root/"lib/database.dart").is_file(), "Banco ausente na cópia"
protected=[
    root/"lib/database.dart",
    root/"lib/services/device_sync_service.dart",
    root/"lib/services/auth_service.dart",
    root/"lib/services/media_sync_service.dart",
]
before={p:hashlib.sha256(p.read_bytes()).hexdigest()
        for p in protected if p.is_file()}

def once(source,old,new,label):
    if new in source:return source
    if source.count(old)!=1:
        raise RuntimeError(label+": estrutura alterada; abortando.")
    return source.replace(old,new,1)

for target in targets[:2]:
    c=target.read_text(encoding="utf-8")
    if "import 'package:sqflite/sqflite.dart';" not in c:
        c="import 'package:sqflite/sqflite.dart';\n"+c
    if "import 'package:sqflite_common_ffi/sqflite_ffi.dart';" not in c:
        c="import 'package:sqflite_common_ffi/sqflite_ffi.dart';\n"+c
    c=once(c,
      "  TestWidgetsFlutterBinding.ensureInitialized();",
      "  TestWidgetsFlutterBinding.ensureInitialized();\n"
      "  sqfliteFfiInit();\n"
      "  databaseFactory = databaseFactoryFfi;",
      "Banco de testes PDF não inicializado")
    target.write_text(c,encoding="utf-8",newline="\n")

target=targets[2]
c=target.read_text(encoding="utf-8")
if "import 'package:path/path.dart' as p;" not in c:
    c="import 'package:path/path.dart' as p;\n"+c
c=once(c,
    "    databaseFactory = databaseFactoryFfi;\n\n    supportDir",
    "    databaseFactory = databaseFactoryFfi;\n"
    "    // Limpar APENAS IDs fictícios do teste entre jobs de CI.\n"
    "    // A própria suíte executa novamente em uma cópia temporária.\n"
    "    final fixtureDbRoot = await getDatabasesPath();\n"
    "    for (final fixtureName in const <String>[\n"
    "      'auditar_sst_sync-phone-user.db',\n"
    "      'auditar_sst_sync-pc-user.db',\n"
    "    ]) {\n"
    "      await databaseFactory.deleteDatabase(\n"
    "        p.join(fixtureDbRoot, fixtureName),\n"
    "      );\n"
    "    }\n\n    supportDir",
    "Ponto de limpeza de bancos fictícios não encontrado")
c=once(c,
    "    await AppDatabase.deactivateUser();\n    await central.close();",
    "    await AppDatabase.deactivateUser();\n"
    "    // Ao terminar, não deixar DBs de usuários fictícios no cache de CI.\n"
    "    final fixtureDbRoot = await getDatabasesPath();\n"
    "    for (final fixtureName in const <String>[\n"
    "      'auditar_sst_sync-phone-user.db',\n"
    "      'auditar_sst_sync-pc-user.db',\n"
    "    ]) {\n"
    "      await databaseFactory.deleteDatabase(\n"
    "        p.join(fixtureDbRoot, fixtureName),\n"
    "      );\n"
    "    }\n    await central.close();",
    "Ponto de limpeza após testes não encontrado")
target.write_text(c,encoding="utf-8",newline="\n")
assert all(hashlib.sha256(p.read_bytes()).hexdigest()==h
    for p,h in before.items()),"Arquivo protegido foi alterado."
print("FIXTURE_PDF_SQLITE_FFI_AND_SYNC_ISOLATION_OK")

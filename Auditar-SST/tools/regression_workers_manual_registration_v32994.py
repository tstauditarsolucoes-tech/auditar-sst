#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(sys.argv[1])
version=sys.argv[2]
workers=(root/'lib/screens/workers_screen.dart').read_text(encoding='utf-8')
database=(root/'lib/database.dart').read_text(encoding='utf-8')
pub=(root/'pubspec.yaml').read_text(encoding='utf-8')
for marker in [
    "inactiveWorkers = []",
    "showInactive = false",
    "onlyActive: false",
    "Ver inativos",
    "Não foi possível salvar: $error",
    "Registro não encontrado após salvar.",
    "Trabalhador salvo e confirmado no banco local.",
    "AppDatabase.instance.insertWorker(record)",
    "AppDatabase.instance.updateWorker(record)",
]:
    assert marker in workers, marker
assert "Future<void> insertWorker(Worker worker)" in database
assert "Future<List<Worker>> getWorkers(" in database
assert f"version: {version}" in pub
print('WORKERS_REGRESSION_OK', version)

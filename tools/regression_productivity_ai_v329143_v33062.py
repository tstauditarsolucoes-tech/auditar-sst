#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
ai = (root / 'lib/services/ai_assistant_service.dart').read_text(encoding='utf-8')
home = (root / 'lib/screens/home_screen.dart').read_text(encoding='utf-8')
round_screen = (root / 'lib/screens/express_round_screen.dart').read_text(encoding='utf-8')
search = (root / 'lib/screens/global_search_screen.dart').read_text(encoding='utf-8')
diag = (root / 'lib/screens/admin_diagnostics_screen.dart').read_text(encoding='utf-8')

for snippet in (
    "import 'dart:isolate';",
    '_preparePhotoForAiAsync',
    'maxDimension: single ? 720',
    "'rondaDeferred': false",
    "'rondaDeferred': true",
    "const Duration(seconds: 50)",
    "const Duration(seconds: 90)",
):
    assert snippet in ai, 'AI regression missing: ' + snippet

for snippet in (
    'GlobalSearchScreen',
    'AdminDiagnosticsScreen',
    "title: 'Pesquisa global'",
):
    assert snippet in home, 'Home regression missing: ' + snippet

assert 'IA analisando foto • ${_aiPhotoElapsedSeconds}s' in round_screen
assert "db.getSstRecords(type: 'DDS')" in search
assert 'AuthService.isAdmin' in diag
assert 'somente de leitura' in diag

print('PRODUCTIVITY_AI_REGRESSION_OK')

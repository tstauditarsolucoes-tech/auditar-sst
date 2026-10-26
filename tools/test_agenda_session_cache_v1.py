#!/usr/bin/env python3
"""Verifica cache não persistente e atualização progressiva da Agenda SST.

Roda em código-fonte compartilhado Android/Windows, sem rede, banco ou GS.
"""
from pathlib import Path
import re
import sys

app = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
agenda = (app / "feature_sources/technician_agenda_screen_v330123.dart").read_text(encoding="utf-8")
windows = (app / "tools/patch_windows_recent_loading_v1.py").read_text(encoding="utf-8")

needed = [
    "class _AgendaSessionSnapshot",
    "static _AgendaSessionSnapshot? _lastSnapshot;",
    "AuthService.currentUser?.id",
    "AuthService.sessionToken",
    "_openedSession = _sessionScope();",
    "if (snap.scope != _openedSession)",
    "_lastSnapshot = null;",
    "_restoreSnapshot();",
    "_saveSnapshot();",
    "DateTime.now().difference(_lastSuccess!) >= _refreshInterval",
    "Timer.periodic(_refreshInterval",
    "WidgetsBinding.instance.addObserver(this)",
    "WidgetsBinding.instance.removeObserver(this)",
    "_refreshTimer?.cancel();",
    "ModalRoute.of(context)?.isCurrent",
    "Duration(seconds: 60)",
    "_refreshing = true;",
    "Future.wait<dynamic>([",
    "_post({'operation': 'list'})",
    "if (!mounted || !allowed || _sessionScope() != requestScope) return;",
    "final hasTaskChanges = jsonEncode(tasks) != jsonEncode(incoming);",
    "if (hasTaskChanges) tasks = incoming;",
    "Verificando novidades",
    "Nenhuma atividade disponível.",
    "Consultando atividades",
    "Última atualização:",
    "if(visible.isEmpty && !_refreshing && error.isEmpty)",
    "if(visible.isNotEmpty && error.isNotEmpty)",
    "A Central retornou uma lista inválida.",
]
for marker in needed:
    assert marker in agenda, f"Função de agenda ausente: {marker}"
assert "SharedPreferences" not in agenda, "Não persistir dados da agenda em preferências"
assert "secureStorage" not in agenda, "Não gravar agenda em armazenamento seguro"
assert "_lastSnapshot = null;" in agenda, "Isolamento ao mudar de conta"
assert "if (!allowed || _sessionScope()!=_openedSession)" in agenda
start = agenda.index("  Future<void> _load() async {")
end = agenda.index("  String label(", start)
load = agenda[start:end]
assert len(re.findall(r"\btasks\s*=\s*\[\s*\]", load)) == 0,     "Recarga não deve esvaziar lista existente"
assert "tasks.clear()" not in load
assert "catch (e)" in load and "_saveSnapshot();" in load
assert "if (_lastSuccess!=null)" in agenda, "Mostrar quando a lista foi atualizada"
assert "if(visible.isEmpty && _refreshing)" in agenda,     "Não mostrar falsa ausência de atividades durante consulta"
assert "if \"Future.wait<dynamic>\" in s and \"_saveSnapshot();\" in s:" in windows,     "Patch Windows não pode substituir carregamento com cache"
assert "raise AssertionError(" in windows and "shared agenda cache" in windows

print("AGENDA_CACHE_DE_SESSAO_E_ATUALIZACAO_AUTOMATICA_OK")
print("SEM_PERSISTENCIA_E_SEM_ALTERACAO_DE_SINCRONIZACAO_OK")

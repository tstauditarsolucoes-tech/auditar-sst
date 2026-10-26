#!/usr/bin/env python3
from pathlib import Path
import re
import sys
r=Path(sys.argv[1])
h=(r/'lib/screens/home_screen.dart').read_text(encoding='utf8')
a=(r/'lib/screens/technician_agenda_screen.dart').read_text(encoding='utf8')
assert h.count("title: 'Minha agenda'")==1
assert h.count("const TechnicianAgendaScreen()")==1
for key in ["'operation':'list'","'operation':'status'","'operation':'create'","AuthService.isAdmin"]:
 assert key in a,key
assert 'version: 3.29.195+337' in (r/'pubspec.yaml').read_text(encoding='utf8')
# As tarefas da gestão precisam exibir empresa, técnico, prazo e orientações.
# A agenda do técnico continua disponível sem modificar a rota online.
for marker in (
    'Agenda da equipe · visão ADM',
    'Minhas tarefas e visitas',
    'Empresa: ',
    'Responsável: ',
    'Início previsto: ',
    'Prazo: ',
    'Orientações do serviço:',
    "task['companyId']",
    "task['technicianId']",
):
    assert marker in a, 'Detalhe da tarefa ausente: ' + marker

# Dart format may insert whitespace after the colon; keep semantic assertions.
assert re.search(r"labelText\\s*:\\s*'Nome do serviço'", a), 'Título de serviço ausente'
assert re.search(r"labelText\\s*:\\s*'Orientações para o técnico'", a), 'Orientações do técnico ausentes'

print('ANDROID_AGENDA_329195_REGRESSION_OK')

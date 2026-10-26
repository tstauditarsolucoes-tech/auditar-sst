#!/usr/bin/env python3
from pathlib import Path
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
    "labelText:'Nome do serviço'",
    "labelText:'Orientações para o técnico'",
):
    assert marker in a, 'Detalhe da tarefa ausente: ' + marker

print('ANDROID_AGENDA_329195_REGRESSION_OK')

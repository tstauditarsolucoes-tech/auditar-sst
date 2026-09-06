#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')

def read(rel):
    return (root / rel).read_text(encoding='utf-8')

def write(rel, text):
    (root / rel).write_text(text, encoding='utf-8')

def remove_call_block(text, needle, opener=r'^\s*[A-Za-z_][\w.]*\(\s*$'):
    if needle not in text:
        return text
    pos = text.index(needle)
    starts = list(re.finditer(opener, text[:pos], flags=re.M))
    if not starts:
        raise RuntimeError(f'início do bloco não encontrado: {needle}')
    i = starts[-1].start()
    indent = re.match(r'^(\s*)', text[i:]).group(1)
    end = re.search(r'^' + re.escape(indent) + r'\),\s*$', text[pos:], flags=re.M)
    if not end:
        raise RuntimeError(f'fim do bloco não encontrado: {needle}')
    j = pos + end.end()
    if j < len(text) and text[j:j+1] == '\n':
        j += 1
    return text[:i] + text[j:]

def remove_until_children_close(text, needle):
    if needle not in text:
        return text
    pos = text.index(needle)
    line_start = text.rfind('\n', 0, pos) + 1
    line_end = text.find('\n', line_start)
    line = text[line_start: line_end if line_end >= 0 else len(text)]
    indent = len(line) - len(line.lstrip())
    close_indent = max(indent - 2, 0)
    close = re.search(r'^' + (' ' * close_indent) + r'\],\s*$', text[pos:], flags=re.M)
    if not close:
        raise RuntimeError(f'fechamento children não encontrado: {needle}')
    return text[:line_start] + text[pos + close.start():]

pub = read('pubspec.yaml')
pub, n = re.subn(r'^version:\s*3\.29\.3\+145\s*$', 'version: 3.29.4+146', pub, count=1, flags=re.M)
if n != 1:
    raise RuntimeError('versão base 3.29.3+145 não encontrada')
write('pubspec.yaml', pub)

home = read('lib/screens/home_screen.dart')
home = home.replace('Registros obrigatórios, exames e vencimentos', 'Registros obrigatórios, treinamentos e vencimentos')
home = home.replace('versão 3.29.3', 'versão 3.29.4')
write('lib/screens/home_screen.dart', home)

companies = read('lib/screens/companies_screen.dart')
companies = re.sub(r'^\s*bool\s+medicalAlertsEnabled\s*=.*?;\s*\n?', '', companies, flags=re.M)
companies = remove_call_block(companies, 'Alertas de exames periódicos', r'^\s*SwitchListTile\(\s*$')
companies = re.sub(r'\s*\|\|\s*medicalAlertsEnabled', '', companies)
companies = re.sub(r'medicalAlertsEnabled\s*\|\|\s*', '', companies)
companies = re.sub(r'\n\s*medicalAlertsEnabled\)\s*&&', ') &&', companies)
companies = re.sub(r'medicalAlertsEnabled:\s*medicalAlertsEnabled,', 'medicalAlertsEnabled: false,', companies)
write('lib/screens/companies_screen.dart', companies)

workers = read('lib/screens/workers_screen.dart')
workers = re.sub(r'^\s*DateTime\?\s+(?:lastMedicalExamDate|nextMedicalExamDate)\s*=.*?;\s*\n?', '', workers, flags=re.M)
if 'Saúde ocupacional' in workers:
    pos = workers.index('Saúde ocupacional')
    divs = list(re.finditer(r'^\s*const Divider\([^\n]*\),\s*$', workers[:pos], flags=re.M))
    if not divs:
        raise RuntimeError('início da seção saúde ocupacional não encontrado')
    i = divs[-1].start()
    active_pos = workers.find('Trabalhador ativo', pos)
    if active_pos < 0:
        raise RuntimeError('switch Trabalhador ativo não encontrado')
    active_starts = list(re.finditer(r'^\s*SwitchListTile\(\s*$', workers[:active_pos], flags=re.M))
    if not active_starts:
        raise RuntimeError('início do switch Trabalhador ativo não encontrado')
    j = active_starts[-1].start()
    workers = workers[:i] + workers[j:]
workers = re.sub(r'lastMedicalExamDate:\s*lastMedicalExamDate,', 'lastMedicalExamDate: worker?.lastMedicalExamDate,', workers)
workers = re.sub(r'nextMedicalExamDate:\s*nextMedicalExamDate,', 'nextMedicalExamDate: worker?.nextMedicalExamDate,', workers)
workers = re.sub(r'\n\s*final medicalDue\s*=.*?(?=\n\s*return Scaffold\()', '', workers, count=1, flags=re.S)
workers = workers.replace('maxColumns: 3,', 'maxColumns: 2,', 1)
workers = remove_call_block(workers, 'Periódicos ≤30d', r'^\s*_summaryCard\(\s*$')
workers = re.sub(r'\n\s*final periodic\s*=\s*worker\.nextMedicalExamDate;.*?(?=\n\s*return Card\()', '', workers, count=1, flags=re.S)
workers = remove_until_children_close(workers, 'if (periodicDays != null)')
write('lib/screens/workers_screen.dart', workers)

alerts = read('lib/screens/compliance_alerts_screen.dart')
alerts = re.sub(r'\n\s*List<Worker>\s+get\s+_medicalAlerts\s*\{.*?(?=\n\s*Future<void>\s+_openMatrix\()', '\n', alerts, count=1, flags=re.S)
alerts = re.sub(r'^\s*final medicalAlerts\s*=\s*_medicalAlerts;\s*\n?', '', alerts, flags=re.M)
alerts = alerts.replace('maxColumns: 3,', 'maxColumns: 2,', 1)
alerts = remove_call_block(alerts, "'Periódicos'", r'^\s*_metric\(\s*$')
alerts = remove_until_children_close(alerts, "_sectionTitle('Exames periódicos'")
write('lib/screens/compliance_alerts_screen.dart', alerts)

routine = read('lib/screens/routine_hub_screen.dart')
routine = remove_call_block(routine, 'Exames a verificar', r'^\s*\(\s*$')
write('lib/screens/routine_hub_screen.dart', routine)

mg = read('lib/screens/management_panel_screen.dart')
mg = re.sub(r'^\s*int\s+medicalCriticalCount\s*=\s*0;\s*\n?', '', mg, flags=re.M)
mg = re.sub(r'^\s*final workers\s*=\s*await db\.getWorkers\([^\n]+\);\s*\n?', '', mg, flags=re.M)
mg = re.sub(r'\n\s*final now\s*=\s*DateTime\.now\(\);.*?(?=\n\s*if \(!mounted\) return;)', '', mg, count=1, flags=re.S)
mg = re.sub(r'^\s*medicalCriticalCount\s*=\s*criticalMedicalExams;\s*\n?', '', mg, flags=re.M)
mg = remove_call_block(mg, 'Periódicos críticos', r'^\s*_metric\(\s*$')
mg = mg.replace('treinamentos, periódicos, NCs', 'treinamentos, NCs')
write('lib/screens/management_panel_screen.dart', mg)

ai = read('lib/services/ai_assistant_service.dart')
old = "      final snapshot = await ManagementPanelService.buildSnapshot(company);\n      return _send({\n"
new = "      final snapshot = await ManagementPanelService.buildSnapshot(company);\n      final rawWorkforce = snapshot['workforceSummary'];\n      final workforce = rawWorkforce is Map\n          ? Map<String, Object?>.from(rawWorkforce)\n          : <String, Object?>{};\n      workforce.removeWhere((key, _) => key.startsWith('medical'));\n      return _send({\n"
if old not in ai:
    raise RuntimeError('ponto de filtro da IA não encontrado')
ai = ai.replace(old, new, 1)
ai = ai.replace("'resumoTrabalhadores': snapshot['workforceSummary'],", "'resumoTrabalhadores': workforce,")
write('lib/services/ai_assistant_service.dart', ai)

(root / 'MUDANCAS_V3_29_4_SEM_EXAMES.md').write_text(
    '# Auditar SST v3.29.4 — sem controle de exames no app\n\n'
    '- Retirada somente a parte de exames/periódicos do Android e Windows.\n'
    '- Dados antigos permanecem preservados no banco para compatibilidade.\n'
    '- Painel gerencial web e checklists NR-7 não foram alterados.\n'
    '- Assinatura, relatórios, sincronização e demais funções permanecem iguais.\n',
    encoding='utf-8',
)

files = [
    'lib/screens/companies_screen.dart', 'lib/screens/workers_screen.dart',
    'lib/screens/compliance_alerts_screen.dart', 'lib/screens/routine_hub_screen.dart',
    'lib/screens/management_panel_screen.dart', 'lib/screens/home_screen.dart',
]
visible = '\n'.join(read(f) for f in files)
for term in ['Alertas de exames periódicos', 'Data do último exame', 'Próximo exame periódico',
             'Exames periódicos', 'Periódicos críticos', 'Exames a verificar', 'Periódicos ≤30d']:
    if term in visible:
        raise RuntimeError(f'texto de exames ainda visível: {term}')
if 'Assinar em tela cheia' not in read('lib/screens/signature_screen.dart'):
    raise RuntimeError('assinatura em tela cheia foi perdida')
print('v3.29.4: exames removidos do Android e Windows; demais funções preservadas.')

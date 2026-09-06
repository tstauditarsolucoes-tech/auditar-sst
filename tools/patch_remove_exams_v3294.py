#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')

def read(rel):
    return (root/rel).read_text(encoding='utf-8')

def write(rel, text):
    (root/rel).write_text(text, encoding='utf-8')

def rep(text, old, new, label):
    if old not in text:
        raise RuntimeError(f'marcador não encontrado: {label}')
    return text.replace(old, new, 1)

# Versão
pub = read('pubspec.yaml')
pub = rep(pub, 'version: 3.29.3+145', 'version: 3.29.4+146', 'versão 3.29.3')
write('pubspec.yaml', pub)

# Home: somente retirar referência a exames e atualizar versão.
home = read('lib/screens/home_screen.dart')
home = home.replace("subtitle: 'Registros obrigatórios, exames e vencimentos'", "subtitle: 'Registros obrigatórios, treinamentos e vencimentos'")
home = home.replace('versão 3.29.3', 'versão 3.29.4')
write('lib/screens/home_screen.dart', home)

# Empresas: retirar configuração visual de alertas de exames.
companies = read('lib/screens/companies_screen.dart')
companies = companies.replace("    bool medicalAlertsEnabled = company?.medicalAlertsEnabled ?? false;\n", '')
start = """                        SwitchListTile(\n                          contentPadding: EdgeInsets.zero,\n                          title: const Text('Alertas de exames periódicos'),\n"""
if start in companies:
    i = companies.index(start)
    marker = """                              ),\n                        ),\n"""
    j = companies.find(marker, i)
    if j < 0:
        raise RuntimeError('fim do switch de exames não encontrado')
    companies = companies[:i] + companies[j+len(marker):]
companies = companies.replace("""    if ((monthlyReportEnabled ||\n            trainingAlertsEnabled ||\n            medicalAlertsEnabled) &&\n""", """    if ((monthlyReportEnabled || trainingAlertsEnabled) &&\n""")
companies = companies.replace('      medicalAlertsEnabled: medicalAlertsEnabled,', '      medicalAlertsEnabled: false,')
write('lib/screens/companies_screen.dart', companies)

# Trabalhadores: preservar dados antigos no banco, mas retirar toda a interface de exames.
workers = read('lib/screens/workers_screen.dart')
workers = workers.replace('    DateTime? lastMedicalExamDate = worker?.lastMedicalExamDate;\n', '')
workers = workers.replace('    DateTime? nextMedicalExamDate = worker?.nextMedicalExamDate;\n', '')
health_start = """                      const Divider(height: 22),\n                      const Align(\n                        alignment: Alignment.centerLeft,\n                        child: Text(\n                          'Saúde ocupacional',\n"""
if health_start in workers:
    i = workers.index(health_start)
    active_marker = """                      SwitchListTile(\n                        contentPadding: EdgeInsets.zero,\n                        title: const Text('Trabalhador ativo'),\n"""
    j = workers.find(active_marker, i)
    if j < 0:
        raise RuntimeError('fim da seção saúde ocupacional não encontrado')
    workers = workers[:i] + active_marker + workers[j+len(active_marker):]
workers = workers.replace('                      lastMedicalExamDate: lastMedicalExamDate,', '                      lastMedicalExamDate: worker?.lastMedicalExamDate,')
workers = workers.replace('                      nextMedicalExamDate: nextMedicalExamDate,', '                      nextMedicalExamDate: worker?.nextMedicalExamDate,')
build_med_start = """    final medicalDue =\n        workers.where((worker) {\n"""
if build_med_start in workers:
    i = workers.index(build_med_start)
    scaffold = '    return Scaffold(\n'
    j = workers.find(scaffold, i)
    if j < 0:
        raise RuntimeError('retorno Scaffold de trabalhadores não encontrado')
    workers = workers[:i] + scaffold + workers[j+len(scaffold):]
workers = workers.replace('                      maxColumns: 3,', '                      maxColumns: 2,', 1)
summary_med = """                        _summaryCard(\n                          'Periódicos ≤30d',\n                          medicalDue,\n                          Icons.medical_information_outlined,\n                          medicalDue > 0\n                              ? const Color(0xFFD93025)\n                              : AuditarBrand.greenDark,\n                        ),\n"""
workers = workers.replace(summary_med, '')
periodic_calc_start = """                        final periodic = worker.nextMedicalExamDate;\n                        final now = DateTime.now();\n"""
if periodic_calc_start in workers:
    i = workers.index(periodic_calc_start)
    return_card = '                        return Card(\n'
    j = workers.find(return_card, i)
    if j < 0:
        raise RuntimeError('card de trabalhador não encontrado')
    workers = workers[:i] + return_card + workers[j+len(return_card):]
periodic_ui_start = """                                if (periodicDays != null)\n                                  Text(\n"""
if periodic_ui_start in workers:
    i = workers.index(periodic_ui_start)
    marker = """                                  ),\n                              ],\n"""
    j = workers.find(marker, i)
    if j < 0:
        raise RuntimeError('texto periódico do trabalhador não encontrado')
    workers = workers[:i] + '                              ],\n' + workers[j+len(marker):]
write('lib/screens/workers_screen.dart', workers)

# Alertas SST: manter somente treinamentos/obrigações, sem exames.
alerts = read('lib/screens/compliance_alerts_screen.dart')
getter_start = """  List<Worker> get _medicalAlerts {\n"""
if getter_start in alerts:
    i = alerts.index(getter_start)
    next_fn = '  Future<void> _openMatrix() async {\n'
    j = alerts.find(next_fn, i)
    if j < 0:
        raise RuntimeError('fim do getter de exames não encontrado')
    alerts = alerts[:i] + next_fn + alerts[j+len(next_fn):]
alerts = alerts.replace('    final medicalAlerts = _medicalAlerts;\n', '')
alerts = alerts.replace('                      maxColumns: 3,', '                      maxColumns: 2,', 1)
metric_med = """                        _metric(\n                          'Periódicos',\n                          medicalAlerts.length,\n                          const Color(0xFF6A4BBC),\n                        ),\n"""
alerts = alerts.replace(metric_med, '')
section_start = """                    _sectionTitle('Exames periódicos', medicalAlerts.length),\n"""
if section_start in alerts:
    i = alerts.index(section_start)
    list_close = """                  ],\n                ),\n"""
    j = alerts.find(list_close, i)
    if j < 0:
        raise RuntimeError('fim da seção de exames nos alertas não encontrado')
    alerts = alerts[:i] + list_close + alerts[j+len(list_close):]
write('lib/screens/compliance_alerts_screen.dart', alerts)

# Rotina SST: retirar card de exames.
routine = read('lib/screens/routine_hub_screen.dart')
routine_block = """      (\n        'Exames a verificar',\n        summary['medicalDue'] ?? 0,\n        Icons.medical_information_outlined,\n        const Color(0xFF6A4BBC),\n      ),\n"""
routine = routine.replace(routine_block, '')
write('lib/screens/routine_hub_screen.dart', routine)

# Painel dentro do app: retirar indicador de periódicos e referências textuais.
mg = read('lib/screens/management_panel_screen.dart')
mg = mg.replace('  int medicalCriticalCount = 0;\n', '')
mg = mg.replace('    final workers = await db.getWorkers(companyId: widget.company.id);\n', '')
calc_start = """    final now = DateTime.now();\n    final today = DateTime(now.year, now.month, now.day);\n    final medicalLimit = today.add(const Duration(days: 30));\n    final criticalMedicalExams =\n"""
if calc_start in mg:
    i = mg.index(calc_start)
    set_state = '    if (!mounted) return;\n'
    j = mg.find(set_state, i)
    if j < 0:
        raise RuntimeError('fim do cálculo de exames do painel não encontrado')
    mg = mg[:i] + set_state + mg[j+len(set_state):]
mg = mg.replace('      medicalCriticalCount = criticalMedicalExams;\n', '')
metric = """                        _metric(\n                          'Periódicos críticos',\n                          '$medicalCriticalCount',\n                          Icons.health_and_safety_outlined,\n                          medicalCriticalCount > 0\n                              ? const Color(0xFFF29D18)\n                              : AuditarBrand.greenDark,\n                        ),\n"""
mg = mg.replace(metric, '')
mg = mg.replace('A IA analisa indicadores agregados, treinamentos, periódicos, NCs, ações e setores para sugerir o que deve ser tratado primeiro.', 'A IA analisa indicadores agregados, treinamentos, NCs, ações e setores para sugerir o que deve ser tratado primeiro.')
mg = mg.replace('A empresa verá uma leitura rápida da situação geral, prioridades, treinamentos, periódicos, NCs, ações e vistorias.', 'A empresa verá uma leitura rápida da situação geral, prioridades, treinamentos, NCs, ações e vistorias.')
write('lib/screens/management_panel_screen.dart', mg)

# IA do app: não enviar os campos médicos do resumo de trabalhadores para análise de prioridades.
ai = read('lib/services/ai_assistant_service.dart')
old = """      final snapshot = await ManagementPanelService.buildSnapshot(company);\n      return _send({\n"""
new = """      final snapshot = await ManagementPanelService.buildSnapshot(company);\n      final rawWorkforce = snapshot['workforceSummary'];\n      final workforce = rawWorkforce is Map\n          ? Map<String, Object?>.from(rawWorkforce)\n          : <String, Object?>{};\n      workforce.removeWhere((key, _) => key.startsWith('medical'));\n      return _send({\n"""
ai = rep(ai, old, new, 'filtro de dados médicos da IA')
ai = ai.replace("          'resumoTrabalhadores': snapshot['workforceSummary'],", "          'resumoTrabalhadores': workforce,")
write('lib/services/ai_assistant_service.dart', ai)

(root/'MUDANCAS_V3_29_4_SEM_EXAMES.md').write_text(
    '# Auditar SST v3.29.4 — retirada do controle de exames\n\n'
    '- Android e Windows: removida a parte visual de exames/periódicos.\n'
    '- Cadastro de trabalhador não exibe mais datas de exames.\n'
    '- Tela de trabalhadores não mostra mais alertas de periódicos.\n'
    '- Avisos SST não exibem mais exames periódicos.\n'
    '- Configuração de empresa não oferece mais alertas de exames.\n'
    '- Rotina SST e painel interno não mostram indicadores de exames.\n'
    '- A IA de prioridades deixa de receber indicadores médicos.\n'
    '- Dados antigos permanecem no banco apenas para compatibilidade; não são apagados.\n'
    '- Painel gerencial web e checklists NR-7 não foram alterados nesta versão.\n'
    '- Nenhuma outra função foi removida ou modificada.\n', encoding='utf-8')

screen_files = [
    'lib/screens/companies_screen.dart',
    'lib/screens/workers_screen.dart',
    'lib/screens/compliance_alerts_screen.dart',
    'lib/screens/routine_hub_screen.dart',
    'lib/screens/management_panel_screen.dart',
    'lib/screens/home_screen.dart',
]
visible = '\n'.join(read(p) for p in screen_files)
for forbidden in ['Alertas de exames periódicos', 'Data do último exame', 'Próximo exame periódico', 'Exames periódicos', 'Periódicos críticos', 'Exames a verificar', 'Periódicos ≤30d']:
    if forbidden in visible:
        raise RuntimeError(f'texto de exames ainda visível: {forbidden}')
if 'version: 3.29.4+146' not in read('pubspec.yaml'):
    raise RuntimeError('versão 3.29.4 ausente')
if 'Assinar em tela cheia' not in read('lib/screens/signature_screen.dart'):
    raise RuntimeError('assinatura em tela cheia foi perdida')

print('v3.29.4: controle visual de exames removido do Android e Windows; demais funções preservadas.')

#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Trecho esperado não encontrado: {label}')
    return text.replace(old, new, 1)


def sub_once(text: str, pattern: str, repl: str, label: str) -> str:
    updated, count = re.subn(pattern, repl, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f'Trecho esperado não encontrado: {label}')
    return updated


def hide_collection_item_with_marker(text: str, marker: str, label: str) -> str:
    idx = text.find(marker)
    if idx < 0:
        raise RuntimeError(f'Marcador não encontrado: {label}')
    line_start = text.rfind('\n', 0, idx) + 1
    cursor = line_start
    for _ in range(12):
        prev_start = text.rfind('\n', 0, max(0, cursor - 1)) + 1
        line = text[prev_start:cursor].rstrip('\n')
        stripped = line.strip()
        if stripped == '(' or (stripped.startswith('_') and '(' in stripped) or stripped.startswith('SwitchListTile('):
            if stripped.startswith('if (false)'):
                return text
            indent = line[:len(line) - len(line.lstrip())]
            replacement = indent + 'if (false) ' + line.lstrip()
            return text[:prev_start] + replacement + text[cursor:]
        cursor = prev_start
    raise RuntimeError(f'Início do item não encontrado: {label}')


def hide_children_range(text: str, marker: str, end_marker: str, label: str) -> str:
    idx = text.find(marker)
    if idx < 0:
        raise RuntimeError(f'Marcador inicial não encontrado: {label}')
    start = text.rfind('\n', 0, idx) + 1
    end = text.find(end_marker, idx)
    if end < 0:
        raise RuntimeError(f'Marcador final não encontrado: {label}')
    indent = text[start:idx]
    if not indent.isspace():
        indent = re.match(r'\s*', text[start:]).group(0)
    block = text[start:end]
    wrapped = f'{indent}if (false) ...[\n{block}{indent}],\n'
    return text[:start] + wrapped + text[end:]


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'assemble_v3510.py')],
        cwd=repo,
        check=True,
    )
    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'

    # Versão
    pub = app / 'pubspec.yaml'
    p = pub.read_text(encoding='utf-8')
    p = replace_once(p, 'version: 3.35.1+154', 'version: 3.36.0+155', 'versão')
    pub.write_text(p, encoding='utf-8')

    # Central Auditar: contexto geral visualmente claro e acabamento da home.
    homep = app / 'lib' / 'screens' / 'home_screen.dart'
    home = homep.read_text(encoding='utf-8')
    home = home.replace(
        "subtitle: 'Registros obrigatórios, exames e vencimentos',",
        "subtitle: 'Registros obrigatórios, prazos e vencimentos',",
    )
    home = home.replace('Auditar SST • versão 3.35.0', 'Auditar SST • versão 3.36.0')
    home = home.replace('Auditar SST para Windows • versão 3.35.0', 'Auditar SST para Windows • versão 3.36.0')
    home = replace_once(
        home,
        "          _overviewPanel(desktop: false),\n",
        "          _workspaceHeader(desktop: false),\n          const SizedBox(height: 12),\n          _overviewPanel(desktop: false),\n",
        'cabeçalho mobile da Central Auditar',
    )
    home = sub_once(
        home,
        r"\s*Row\(\n\s*children: \[\n\s*const Expanded\(.*?label: const Text\('Sincronização'\),\n\s*\),\n\s*\],\n\s*\),\n\s*const SizedBox\(height: 18\),",
        "\n                _workspaceHeader(desktop: true),\n                const SizedBox(height: 16),",
        'cabeçalho desktop da Central Auditar',
    )
    home = home.replace("'Visão geral da carteira'", "'Prioridades da carteira'")
    home = home.replace("'Contexto: Geral'", "'Todas as empresas'")
    workspace_method = r'''
  Widget _workspaceHeader({required bool desktop}) {
    return Container(
      padding: EdgeInsets.all(desktop ? 20 : 16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [AuditarBrand.navyDark, AuditarBrand.navy],
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: const [
          BoxShadow(
            color: Color(0x1A0E1A43),
            blurRadius: 18,
            offset: Offset(0, 8),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: desktop ? 52 : 46,
            height: desktop ? 52 : 46,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: .12),
              borderRadius: BorderRadius.circular(15),
              border: Border.all(color: Colors.white.withValues(alpha: .16)),
            ),
            child: const Icon(
              Icons.hub_outlined,
              color: AuditarBrand.green,
              size: 27,
            ),
          ),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Central Auditar',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: desktop ? 23 : 19,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  desktop
                      ? 'Todas as empresas, pendências e atividades de campo em um só lugar.'
                      : 'Todas as empresas e atividades de campo.',
                  style: const TextStyle(
                    color: Colors.white70,
                    fontSize: 12,
                    height: 1.3,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 10),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
            decoration: BoxDecoration(
              color: AuditarBrand.green.withValues(alpha: .14),
              borderRadius: BorderRadius.circular(999),
              border: Border.all(color: AuditarBrand.green.withValues(alpha: .34)),
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.public_rounded, size: 15, color: AuditarBrand.green),
                SizedBox(width: 5),
                Text(
                  'GERAL',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w900,
                    letterSpacing: .4,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

'''
    home = replace_once(home, '  Widget _overviewPanel({required bool desktop}) {', workspace_method + '  Widget _overviewPanel({required bool desktop}) {', 'método do contexto geral')
    homep.write_text(home, encoding='utf-8')

    # Ambiente da empresa: ações mais usadas logo no topo.
    detailp = app / 'lib' / 'screens' / 'company_detail_screen.dart'
    detail = detailp.read_text(encoding='utf-8')
    detail = replace_once(
        detail,
        "import 'management_panel_screen.dart';\n",
        "import 'management_panel_screen.dart';\nimport 'new_inspection_screen.dart';\n",
        'import nova vistoria no ambiente da empresa',
    )
    detail = detail.replace('Ambiente da empresa • $unitCount unidade', 'Empresa selecionada • $unitCount unidade')
    detail = replace_once(
        detail,
        "          const SizedBox(height: 10),\n          ResponsiveWrap(\n            minItemWidth: 138,\n            maxColumns: 3,",
        "          const SizedBox(height: 12),\n          _companyQuickActions(),\n          const SizedBox(height: 12),\n          ResponsiveWrap(\n            minItemWidth: 138,\n            maxColumns: 3,",
        'ações rápidas da empresa',
    )
    company_quick = r'''
  Widget _companyQuickActions() {
    return ResponsiveWrap(
      minItemWidth: 175,
      maxColumns: 3,
      spacing: 9,
      runSpacing: 9,
      children: [
        _shortcut(
          icon: Icons.add_task_rounded,
          title: 'Nova vistoria',
          subtitle: 'Iniciar já vinculada a esta empresa',
          onTap: () => _open(NewInspectionScreen(initialCompany: widget.company)),
        ),
        _shortcut(
          icon: Icons.domain_outlined,
          title: 'Unidades / CNPJs',
          subtitle: unitCount <= 1
              ? '1 unidade cadastrada'
              : '$unitCount unidades cadastradas',
          onTap: () => _open(CompanyUnitsScreen(company: widget.company)),
        ),
        _shortcut(
          icon: Icons.description_outlined,
          title: 'PGR + IA',
          subtitle: pgrCount == 0
              ? 'Cadastrar ou analisar PGR'
              : '$pgrCount PGR cadastrado(s)',
          onTap: () => _open(PgrScreen(company: widget.company)),
        ),
      ],
    );
  }

'''
    detail = replace_once(detail, '  Widget _inspectionsTab() {', company_quick + '  Widget _inspectionsTab() {', 'método de ações rápidas da empresa')
    detailp.write_text(detail, encoding='utf-8')

    # Campo rápido: acabamento visual sem alterar o fluxo.
    fieldp = app / 'lib' / 'screens' / 'field_quick_screen.dart'
    field = fieldp.read_text(encoding='utf-8')
    field = replace_once(
        field,
        "            decoration: BoxDecoration(\n              color: AuditarBrand.navy,\n              borderRadius: BorderRadius.circular(18),\n            ),",
        "            decoration: BoxDecoration(\n              gradient: const LinearGradient(\n                begin: Alignment.topLeft,\n                end: Alignment.bottomRight,\n                colors: [AuditarBrand.navyDark, AuditarBrand.navy],\n              ),\n              borderRadius: BorderRadius.circular(20),\n            ),",
        'cabeçalho do Campo rápido',
    )
    field = field.replace("'Contexto: Campo rápido'", "'Campo rápido'")
    fieldp.write_text(field, encoding='utf-8')

    # Retirar da interface os controles de exames periódicos. Os campos de banco
    # permanecem intactos para não apagar dados legados nem quebrar sincronização.
    routinep = app / 'lib' / 'screens' / 'routine_hub_screen.dart'
    routine = routinep.read_text(encoding='utf-8')
    routine = hide_collection_item_with_marker(routine, "'Exames a verificar'", 'card de exames na rotina')
    routinep.write_text(routine, encoding='utf-8')

    companiesp = app / 'lib' / 'screens' / 'companies_screen.dart'
    companies = companiesp.read_text(encoding='utf-8')
    companies = hide_collection_item_with_marker(companies, "'Alertas de exames periódicos'", 'configuração de alertas de exames')
    companiesp.write_text(companies, encoding='utf-8')

    compliancep = app / 'lib' / 'screens' / 'compliance_alerts_screen.dart'
    compliance = compliancep.read_text(encoding='utf-8')
    start_marker = "                  _sectionTitle('Exames periódicos', medicalAlerts.length),"
    start = compliance.find(start_marker)
    if start < 0:
        raise RuntimeError('Seção de exames periódicos não encontrada')
    close = compliance.find('\n                ],', start)
    if close < 0:
        raise RuntimeError('Fim da seção de exames periódicos não encontrado')
    block = compliance[start:close]
    compliance = compliance[:start] + '                  if (false) ...[\n' + block + '\n                  ],' + compliance[close:]
    compliancep.write_text(compliance, encoding='utf-8')

    workersp = app / 'lib' / 'screens' / 'workers_screen.dart'
    workers = workersp.read_text(encoding='utf-8')
    health_marker = "                          'Saúde ocupacional',"
    health = workers.find(health_marker)
    if health < 0:
        raise RuntimeError('Bloco Saúde ocupacional não encontrado')
    health_start = workers.rfind('                      const Divider(height: 22),', 0, health)
    active_marker = "                        title: const Text('Trabalhador ativo'),"
    active = workers.find(active_marker, health)
    if health_start < 0 or active < 0:
        raise RuntimeError('Limites do bloco Saúde ocupacional não encontrados')
    switch_start = workers.rfind('                      SwitchListTile(', health, active)
    health_block = workers[health_start:switch_start]
    workers = workers[:health_start] + '                      if (false) ...[\n' + health_block + '                      ],\n' + workers[switch_start:]
    workers = hide_collection_item_with_marker(workers, "'Periódicos ≤30d'", 'indicador de periódicos dos trabalhadores')
    workers = workers.replace('                              if (periodicDays != null)\n', '                              if (false && periodicDays != null)\n', 1)
    workersp.write_text(workers, encoding='utf-8')

    # Validações de preservação e interface.
    final_home = homep.read_text(encoding='utf-8')
    final_detail = detailp.read_text(encoding='utf-8')
    final_field = fieldp.read_text(encoding='utf-8')
    checks = {
        'versão 3.36.0': 'version: 3.36.0+155' in pub.read_text(encoding='utf-8'),
        'Central Auditar': 'Central Auditar' in final_home and "'GERAL'" in final_home,
        'Campo rápido': 'FieldQuickScreen' in final_home and 'Vistoria avulsa' in final_field,
        'ações empresa': "title: 'Nova vistoria'" in final_detail and "title: 'Unidades / CNPJs'" in final_detail and "title: 'PGR + IA'" in final_detail,
        'sync v2': "'syncProtocol': 2" in (app / 'lib' / 'services' / 'device_sync_service.dart').read_text(encoding='utf-8'),
        '44 checklists': (app / 'lib' / 'ready_checklists.dart').read_text(encoding='utf-8').count('  ReadyChecklistDefinition(') == 44,
        'assinatura': 'Assinar em tela cheia' in (app / 'lib' / 'screens' / 'signature_screen.dart').read_text(encoding='utf-8'),
        'periodicos ocultos home': 'Registros obrigatórios, exames e vencimentos' not in final_home,
    }
    missing = [name for name, ok in checks.items() if not ok]
    if missing:
        raise RuntimeError('Validações v3.36.0 ausentes: ' + ', '.join(missing))

    print(f'Fonte v3.36.0 montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

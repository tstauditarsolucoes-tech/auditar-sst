#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Trecho esperado não encontrado: {label}')
    return text.replace(old, new, 1)


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    subprocess.run([sys.executable, str(repo / 'tools' / 'assemble_v3800.py')], cwd=repo, check=True)
    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'

    pub = app / 'pubspec.yaml'
    text = pub.read_text(encoding='utf-8')
    text = replace_once(text, 'version: 3.38.0+159', 'version: 3.38.1+160', 'versão 3.38.1')
    pub.write_text(text, encoding='utf-8')

    p = app / 'lib' / 'screens' / 'companies_screen.dart'
    text = p.read_text(encoding='utf-8')
    text = replace_once(
        text,
        '  bool loading = true;\n',
        '  bool loading = true;\n  bool showHidden = false;\n',
        'estado de empresas ocultas',
    )

    old_delete = '''  Future<void> _deleteCompany(Company company) async {\n    final confirm = await showDialog<bool>(\n      context: context,\n      builder:\n          (context) => AlertDialog(\n            title: const Text('Excluir empresa?'),\n            content: Text(\n              'Deseja excluir “${company.name}”? Se ela já tiver vistorias registradas, o aplicativo impedirá a exclusão para preservar o histórico.',\n            ),\n            actions: [\n              TextButton(\n                onPressed: () => Navigator.pop(context, false),\n                child: const Text('Cancelar'),\n              ),\n              FilledButton(\n                onPressed: () => Navigator.pop(context, true),\n                child: const Text('Excluir'),\n              ),\n            ],\n          ),\n    );\n    if (confirm != true) return;\n    final deleted = await AppDatabase.instance.deleteCompanyIfUnused(\n      company.id,\n    );\n    await _load();\n    if (!mounted) return;\n    ScaffoldMessenger.of(context).showSnackBar(\n      SnackBar(\n        content: Text(\n          deleted\n              ? 'Empresa excluída.'\n              : 'A empresa possui vistorias. Desative-a em vez de excluir.',\n        ),\n      ),\n    );\n  }\n'''
    new_hide = '''  Company _companyWithActive(Company company, bool active) {\n    return Company(\n      id: company.id,\n      name: company.name,\n      cnpj: company.cnpj,\n      city: company.city,\n      uf: company.uf,\n      contact: company.contact,\n      phone: company.phone,\n      logoPath: company.logoPath,\n      reportEmail: company.reportEmail,\n      secondaryReportEmail: company.secondaryReportEmail,\n      reportRecipient: company.reportRecipient,\n      monthlyReportEnabled: company.monthlyReportEnabled,\n      trainingAlertsEnabled: company.trainingAlertsEnabled,\n      medicalAlertsEnabled: company.medicalAlertsEnabled,\n      monthlyReportDay: company.monthlyReportDay,\n      active: active,\n    );\n  }\n\n  Future<void> _setCompanyHidden(Company company, bool hidden) async {\n    if (hidden) {\n      final confirm = await showDialog<bool>(\n        context: context,\n        builder: (context) => AlertDialog(\n          title: const Text('Ocultar empresa?'),\n          content: Text(\n            '“${company.name}” será retirada das telas de uso normal, mas nenhum histórico, vistoria, trabalhador ou documento será apagado.',\n          ),\n          actions: [\n            TextButton(\n              onPressed: () => Navigator.pop(context, false),\n              child: const Text('Cancelar'),\n            ),\n            FilledButton(\n              onPressed: () => Navigator.pop(context, true),\n              child: const Text('Ocultar'),\n            ),\n          ],\n        ),\n      );\n      if (confirm != true) return;\n    }\n\n    await AppDatabase.instance.updateCompany(\n      _companyWithActive(company, !hidden),\n    );\n    await _load();\n    if (!mounted) return;\n    ScaffoldMessenger.of(context).showSnackBar(\n      SnackBar(\n        content: Text(hidden ? 'Empresa ocultada.' : 'Empresa reativada.'),\n      ),\n    );\n  }\n'''
    text = replace_once(text, old_delete, new_hide, 'ocultar empresa no lugar de excluir')

    old_filter = '''  List<Company> get _filtered {\n    final q = searchController.text.trim().toLowerCase();\n    if (q.isEmpty) return companies;\n    return companies.where((c) {\n      return c.name.toLowerCase().contains(q) ||\n          (c.city ?? '').toLowerCase().contains(q) ||\n          (c.cnpj ?? '').toLowerCase().contains(q);\n    }).toList();\n  }\n'''
    new_filter = '''  List<Company> get _filtered {\n    final q = searchController.text.trim().toLowerCase();\n    return companies.where((c) {\n      if (!showHidden && !c.active) return false;\n      if (q.isEmpty) return true;\n      return c.name.toLowerCase().contains(q) ||\n          (c.city ?? '').toLowerCase().contains(q) ||\n          (c.cnpj ?? '').toLowerCase().contains(q);\n    }).toList();\n  }\n'''
    text = replace_once(text, old_filter, new_filter, 'filtro das empresas ocultas')

    old_actions = '''        actions: [\n          IconButton(\n            tooltip: 'Nova empresa',\n            onPressed: () => _editCompany(),\n            icon: const Icon(Icons.add_business_rounded),\n          ),\n        ],\n'''
    new_actions = '''        actions: [\n          IconButton(\n            tooltip: showHidden ? 'Ocultar empresas arquivadas' : 'Mostrar ocultas',\n            onPressed: () => setState(() => showHidden = !showHidden),\n            icon: Icon(\n              showHidden ? Icons.visibility_rounded : Icons.visibility_off_rounded,\n            ),\n          ),\n          IconButton(\n            tooltip: 'Nova empresa',\n            onPressed: () => _editCompany(),\n            icon: const Icon(Icons.add_business_rounded),\n          ),\n        ],\n'''
    text = replace_once(text, old_actions, new_actions, 'botão mostrar ocultas')
    text = replace_once(
        text,
        "                        if (value == 'delete') _deleteCompany(company);",
        "                        if (value == 'toggle_active') {\n                          _setCompanyHidden(company, company.active);\n                        }",
        'ação do menu da empresa',
    )
    text = replace_once(
        text,
        "                            const PopupMenuItem(\n                              value: 'delete',\n                              child: Text('Excluir'),\n                            ),",
        "                            PopupMenuItem(\n                              value: 'toggle_active',\n                              child: Text(\n                                company.active ? 'Ocultar empresa' : 'Reativar empresa',\n                              ),\n                            ),",
        'menu ocultar/reativar empresa',
    )
    text = replace_once(
        text,
        '''                        if (company.reportEmail.isNotEmpty)\n                          _miniChip(\n''',
        '''                        if (!company.active)\n                          _miniChip(\n                            Icons.visibility_off_outlined,\n                            'Oculta',\n                            Colors.black54,\n                          ),\n                        if (company.reportEmail.isNotEmpty)\n                          _miniChip(\n''',
        'selo de empresa oculta',
    )
    p.write_text(text, encoding='utf-8')

    p = app / 'lib' / 'screens' / 'sectors_screen.dart'
    text = p.read_text(encoding='utf-8')
    text = replace_once(
        text,
        '''    final result = await AppDatabase.instance.getSectors(\n      widget.company.id,\n      onlyActive: false,\n    );''',
        '''    final result = await AppDatabase.instance.getSectors(\n      widget.company.id,\n    );''',
        'listar apenas setores ativos',
    )

    old_sector_delete = '''  Future<void> _deleteSector(Sector sector) async {\n    final confirm = await showDialog<bool>(\n      context: context,\n      builder: (context) => AlertDialog(\n        title: const Text('Excluir setor?'),\n        content: Text(\n          'Deseja excluir “${sector.name}”? Se já houver vistoria vinculada, '\n          'o aplicativo preservará o setor no histórico e impedirá a exclusão.',\n        ),\n        actions: [\n          TextButton(\n            onPressed: () => Navigator.pop(context, false),\n            child: const Text('Cancelar'),\n          ),\n          FilledButton(\n            onPressed: () => Navigator.pop(context, true),\n            child: const Text('Excluir'),\n          ),\n        ],\n      ),\n    );\n\n    if (confirm != true) return;\n\n    final deleted =\n        await AppDatabase.instance.deleteSectorIfUnused(sector.id);\n\n    await _load();\n\n    if (!mounted) return;\n    ScaffoldMessenger.of(context).showSnackBar(\n      SnackBar(\n        content: Text(\n          deleted\n              ? 'Setor excluído.'\n              : 'Este setor possui vistorias. Desative-o para preservar o histórico.',\n        ),\n      ),\n    );\n  }\n'''
    new_sector_delete = '''  Future<void> _deleteSector(Sector sector) async {\n    final confirm = await showDialog<bool>(\n      context: context,\n      builder: (context) => AlertDialog(\n        title: const Text('Excluir setor?'),\n        content: Text(\n          'Deseja excluir “${sector.name}”? Ele sairá da lista de setores. '\n          'Se já existir histórico vinculado, o aplicativo preservará apenas o registro interno necessário para não quebrar relatórios antigos.',\n        ),\n        actions: [\n          TextButton(\n            onPressed: () => Navigator.pop(context, false),\n            child: const Text('Cancelar'),\n          ),\n          FilledButton(\n            onPressed: () => Navigator.pop(context, true),\n            child: const Text('Excluir'),\n          ),\n        ],\n      ),\n    );\n\n    if (confirm != true) return;\n\n    final deleted = await AppDatabase.instance.deleteSectorIfUnused(sector.id);\n    if (!deleted) {\n      await AppDatabase.instance.updateSector(\n        Sector(\n          id: sector.id,\n          companyId: sector.companyId,\n          name: sector.name,\n          description: sector.description,\n          active: false,\n        ),\n      );\n    }\n\n    await _load();\n\n    if (!mounted) return;\n    ScaffoldMessenger.of(context).showSnackBar(\n      const SnackBar(content: Text('Setor excluído.')),\n    );\n  }\n'''
    text = replace_once(text, old_sector_delete, new_sector_delete, 'exclusão segura de setor')
    p.write_text(text, encoding='utf-8')

    p = app / 'lib' / 'screens' / 'home_screen.dart'
    text = p.read_text(encoding='utf-8').replace('versão 3.38.0', 'versão 3.38.1')
    p.write_text(text, encoding='utf-8')

    print(f'Fonte v3.38.1 mobile montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

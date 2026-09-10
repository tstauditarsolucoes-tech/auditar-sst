#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Trecho esperado não encontrado: {label}')
    return text.replace(old, new, 1)


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'

    # Versão
    pub = app / 'pubspec.yaml'
    text = pub.read_text(encoding='utf-8')
    text = replace_once(text, 'version: 3.29.15+158', 'version: 3.29.16+159', 'versão v3.29.16')
    pub.write_text(text, encoding='utf-8')

    # 1) Campo rápido / vistoria avulsa.
    field = app / 'lib' / 'screens' / 'field_quick_screen.dart'
    field.write_text(r'''import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';

import '../brand.dart';
import '../database.dart';
import '../models.dart';
import 'improvements_screen.dart';
import 'new_inspection_screen.dart';

class FieldQuickScreen extends StatefulWidget {
  const FieldQuickScreen({super.key});

  @override
  State<FieldQuickScreen> createState() => _FieldQuickScreenState();
}

class _FieldQuickScreenState extends State<FieldQuickScreen> {
  final _name = TextEditingController();
  final _cnpj = TextEditingController();
  final _location = TextEditingController();
  bool _busy = false;

  @override
  void dispose() {
    _name.dispose();
    _cnpj.dispose();
    _location.dispose();
    super.dispose();
  }

  Future<void> _startStandaloneInspection() async {
    final name = _name.text.trim();
    if (name.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Informe o cliente ou local da vistoria.')),
      );
      return;
    }

    setState(() => _busy = true);
    try {
      final id = const Uuid().v4();
      final company = Company(
        id: 'field_$id',
        name: name,
        cnpj: _cnpj.text.trim().isEmpty ? null : _cnpj.text.trim(),
        city: _location.text.trim().isEmpty ? null : _location.text.trim(),
        active: false,
      );
      await AppDatabase.instance.insertCompany(company);

      final sector = Sector(
        id: 'field_sector_$id',
        companyId: company.id,
        name: 'Local visitado',
        description: _location.text.trim(),
        active: true,
      );
      await AppDatabase.instance.insertSector(sector);

      if (!mounted) return;
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => NewInspectionScreen(
            initialCompany: company,
            fieldMode: true,
          ),
        ),
      );
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _openStandaloneDialog() async {
    _name.clear();
    _cnpj.clear();
    _location.clear();
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Vistoria avulsa'),
        content: SizedBox(
          width: 460,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: _name,
                autofocus: true,
                decoration: const InputDecoration(
                  labelText: 'Cliente ou local *',
                  hintText: 'Ex.: Obra Alphaville Q13',
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _cnpj,
                decoration: const InputDecoration(
                  labelText: 'CNPJ',
                  hintText: 'Opcional',
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _location,
                decoration: const InputDecoration(
                  labelText: 'Endereço / referência',
                  hintText: 'Opcional',
                ),
              ),
              const SizedBox(height: 10),
              const Text(
                'Esse registro fica como avulso e não aparece na lista de empresas cadastradas.',
                style: TextStyle(fontSize: 11.5, color: Colors.black54),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: _busy
                ? null
                : () async {
                    Navigator.pop(dialogContext);
                    await _startStandaloneInspection();
                  },
            child: const Text('Continuar'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Campo rápido')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [AuditarBrand.navyDark, AuditarBrand.navy],
              ),
              borderRadius: BorderRadius.circular(20),
            ),
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(Icons.location_on_outlined, color: Colors.white),
                    SizedBox(width: 8),
                    Text(
                      'Campo rápido',
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w900,
                        fontSize: 17,
                      ),
                    ),
                  ],
                ),
                SizedBox(height: 6),
                Text(
                  'Use quando a visita ainda não pertence a uma empresa cadastrada.',
                  style: TextStyle(color: Colors.white70),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          _actionCard(
            icon: Icons.fact_check_outlined,
            title: 'Vistoria avulsa',
            subtitle: 'Faça checklist e relatório sem cadastrar a empresa na sua carteira.',
            onTap: _busy ? null : _openStandaloneDialog,
          ),
          _actionCard(
            icon: Icons.business_outlined,
            title: 'Vistoria em empresa cadastrada',
            subtitle: 'Escolha a empresa antes de iniciar a vistoria.',
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const NewInspectionScreen()),
            ),
          ),
          _actionCard(
            icon: Icons.auto_awesome_outlined,
            title: 'Registrar melhoria',
            subtitle: 'Guarde uma melhoria ou oportunidade identificada em campo.',
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const ImprovementsScreen()),
            ),
          ),
        ],
      ),
    );
  }

  Widget _actionCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback? onTap,
  }) {
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
        leading: Container(
          width: 46,
          height: 46,
          decoration: BoxDecoration(
            color: AuditarBrand.navySoft,
            borderRadius: BorderRadius.circular(13),
          ),
          child: Icon(icon, color: AuditarBrand.navy),
        ),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w900)),
        subtitle: Text(subtitle),
        trailing: const Icon(Icons.chevron_right_rounded),
        onTap: onTap,
      ),
    );
  }
}
''', encoding='utf-8')

    # 2) Nova vistoria: aceitar empresa pré-selecionada e modo avulso.
    p = app / 'lib' / 'screens' / 'new_inspection_screen.dart'
    text = p.read_text(encoding='utf-8')
    text = replace_once(
        text,
        "class NewInspectionScreen extends StatefulWidget {\n  const NewInspectionScreen({super.key});",
        "class NewInspectionScreen extends StatefulWidget {\n  final Company? initialCompany;\n  final bool fieldMode;\n\n  const NewInspectionScreen({\n    super.key,\n    this.initialCompany,\n    this.fieldMode = false,\n  });",
        'construtor NewInspectionScreen',
    )
    old_load = """    setState(() {\n      companies = loadedCompanies;\n      templates = loadedTemplates;\n      technicianName.text = defaultTechnician;\n    });\n  }\n"""
    new_load = """    final initial = widget.initialCompany;\n    final availableCompanies = [...loadedCompanies];\n    if (initial != null &&\n        !availableCompanies.any((company) => company.id == initial.id)) {\n      availableCompanies.insert(0, initial);\n    }\n\n    setState(() {\n      companies = availableCompanies;\n      templates = loadedTemplates;\n      technicianName.text = defaultTechnician;\n    });\n\n    if (initial != null) {\n      await _companyChanged(initial);\n    }\n  }\n"""
    text = replace_once(text, old_load, new_load, 'pré-seleção de empresa')
    old_company_set = """    setState(() {\n      sites = results[0] as List<WorkSite>;\n      sectors = results[1] as List<Sector>;\n      pgrDocument = doc;\n      pgrAnalysis = parsedPgr;\n    });\n"""
    new_company_set = """    final loadedSectors = results[1] as List<Sector>;\n    setState(() {\n      sites = results[0] as List<WorkSite>;\n      sectors = loadedSectors;\n      if (widget.fieldMode && loadedSectors.length == 1) {\n        selectedSector = loadedSectors.first;\n      }\n      pgrDocument = doc;\n      pgrAnalysis = parsedPgr;\n    });\n"""
    text = replace_once(text, old_company_set, new_company_set, 'setor automático no modo avulso')
    text = replace_once(
        text,
        "appBar: AppBar(title: const Text('Nova vistoria')),
",
        "appBar: AppBar(\n        title: Text(widget.fieldMode ? 'Vistoria avulsa' : 'Nova vistoria'),\n      ),\n",
        'título da vistoria avulsa',
    )
    marker = """            children: [\n          TextField(\n            controller: technicianName,\n"""
    replacement = """            children: [\n          if (widget.fieldMode) ...[\n            Container(\n              width: double.infinity,\n              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),\n              decoration: BoxDecoration(\n                color: AuditarBrand.navySoft,\n                borderRadius: BorderRadius.circular(12),\n              ),\n              child: const Row(\n                children: [\n                  Icon(Icons.location_on_outlined, color: AuditarBrand.navy),\n                  SizedBox(width: 8),\n                  Expanded(\n                    child: Text(\n                      'Campo rápido • vistoria avulsa',\n                      style: TextStyle(\n                        color: AuditarBrand.navy,\n                        fontWeight: FontWeight.w800,\n                      ),\n                    ),\n                  ),\n                ],\n              ),\n            ),\n            const SizedBox(height: 14),\n          ],\n          TextField(\n            controller: technicianName,\n"""
    if "import '../brand.dart';" not in text:
        text = replace_once(text, "import '../database.dart';\n", "import '../brand.dart';\nimport '../database.dart';\n", 'import da marca')
    text = replace_once(text, marker, replacement, 'faixa do modo avulso')
    p.write_text(text, encoding='utf-8')

    # 3) Home: colocar Campo rápido como acesso real e visível no celular.
    p = app / 'lib' / 'screens' / 'home_screen.dart'
    text = p.read_text(encoding='utf-8')
    text = replace_once(text, "import 'history_screen.dart';\n", "import 'history_screen.dart';\nimport 'field_quick_screen.dart';\n", 'import Campo rápido')
    company_module = """        _ModuleData(\n          title: 'Empresas',\n          subtitle: 'Cadastros, obras, setores e controles por empresa',\n          icon: Icons.business_outlined,\n          color: AuditarBrand.navy,\n          page: () => const CompaniesScreen(),\n        ),\n"""
    field_module = company_module + """        _ModuleData(\n          title: 'Campo rápido',\n          subtitle: 'Vistoria avulsa e registros rápidos fora da carteira',\n          icon: Icons.location_on_outlined,\n          color: const Color(0xFF16836B),\n          page: () => const FieldQuickScreen(),\n        ),\n"""
    text = replace_once(text, company_module, field_module, 'módulo Campo rápido')
    text = replace_once(
        text,
        "          _newInspectionButton(),\n          const SizedBox(height: 18),\n",
        "          _newInspectionButton(),\n          const SizedBox(height: 8),\n          SizedBox(\n            width: double.infinity,\n            child: OutlinedButton.icon(\n              onPressed: () => _open(const FieldQuickScreen()),\n              icon: const Icon(Icons.location_on_outlined),\n              label: const Text('Campo rápido / vistoria avulsa'),\n            ),\n          ),\n          const SizedBox(height: 18),\n",
        'atalho mobile Campo rápido',
    )
    text = text.replace('Auditar SST • versão 3.29.13', 'Auditar SST • versão 3.29.16')
    text = text.replace('Auditar SST para Windows • versão 3.29.13', 'Auditar SST para Windows • versão 3.29.16')
    p.write_text(text, encoding='utf-8')

    # 4) Restaurar o atalho "IA • O que merece sua atenção" dentro da empresa.
    p = app / 'lib' / 'screens' / 'company_detail_screen.dart'
    text = p.read_text(encoding='utf-8')
    ia_card_anchor = """          const SizedBox(height: 8),\n          _shortcut(\n            icon: Icons.report_problem_outlined,\n            title: 'Atos e condições inseguras',\n"""
    ia_card = """          const SizedBox(height: 8),\n          _shortcut(\n            icon: Icons.psychology_alt_outlined,\n            title: 'IA • O que merece sua atenção',\n            subtitle: 'Cruza vistorias, NCs, ações, treinamentos, setores e indicadores da empresa',\n            onTap: () => _open(\n              ManagementPanelScreen(\n                company: widget.company,\n                startAiPriorities: true,\n              ),\n            ),\n          ),\n          const SizedBox(height: 10),\n          _shortcut(\n            icon: Icons.report_problem_outlined,\n            title: 'Atos e condições inseguras',\n"""
    text = replace_once(text, ia_card_anchor, ia_card, 'card IA merece atenção')
    p.write_text(text, encoding='utf-8')

    # 5) Reusar a IA de prioridades que já existe no Painel Gerencial.
    p = app / 'lib' / 'screens' / 'management_panel_screen.dart'
    text = p.read_text(encoding='utf-8')
    text = replace_once(
        text,
        "class ManagementPanelScreen extends StatefulWidget {\n  final Company company;\n\n  const ManagementPanelScreen({\n    super.key,\n    required this.company,\n  });",
        "class ManagementPanelScreen extends StatefulWidget {\n  final Company company;\n  final bool startAiPriorities;\n\n  const ManagementPanelScreen({\n    super.key,\n    required this.company,\n    this.startAiPriorities = false,\n  });",
        'parâmetro de abertura direta da IA',
    )
    text = replace_once(
        text,
        "  void initState() {\n    super.initState();\n    _load();\n  }",
        "  void initState() {\n    super.initState();\n    _load().then((_) {\n      if (widget.startAiPriorities && mounted) {\n        _analyzePriorities();\n      }\n    });\n  }",
        'abertura automática da IA',
    )
    text = text.replace("title: const Text('Prioridades sugeridas pela IA'),", "title: const Text('IA • O que merece sua atenção'),", 1)
    p.write_text(text, encoding='utf-8')

    # Preservações críticas.
    checks = {
        'versão': 'version: 3.29.16+159' in pub.read_text(encoding='utf-8'),
        'campo rápido': 'class FieldQuickScreen' in field.read_text(encoding='utf-8'),
        'avulsa oculta': 'active: false' in field.read_text(encoding='utf-8'),
        'initial company': 'initialCompany' in (app / 'lib' / 'screens' / 'new_inspection_screen.dart').read_text(encoding='utf-8'),
        'field mode': 'fieldMode' in (app / 'lib' / 'screens' / 'new_inspection_screen.dart').read_text(encoding='utf-8'),
        'atalho IA': 'IA • O que merece sua atenção' in (app / 'lib' / 'screens' / 'company_detail_screen.dart').read_text(encoding='utf-8'),
        'IA prioridades preservada': 'analyzeCompanyPriorities' in (app / 'lib' / 'services' / 'ai_assistant_service.dart').read_text(encoding='utf-8'),
        'checklist foto preservado': "'mode': 'checklist_photo'" in (app / 'lib' / 'services' / 'ai_assistant_service.dart').read_text(encoding='utf-8'),
        'revisor preservado': "'mode': 'report_review_chat'" in (app / 'lib' / 'services' / 'ai_assistant_service.dart').read_text(encoding='utf-8'),
        'plano IA preservado': 'AiActionPlanReviewScreen' in (app / 'lib' / 'screens' / 'report_screen.dart').read_text(encoding='utf-8'),
        '44 checklists': (app / 'lib' / 'ready_checklists.dart').read_text(encoding='utf-8').count('  ReadyChecklistDefinition(') == 44,
    }
    missing = [name for name, ok in checks.items() if not ok]
    if missing:
        raise RuntimeError('Validações v3.29.16 falharam: ' + ', '.join(missing))

    print(f'Patch v3.29.16 aplicado em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

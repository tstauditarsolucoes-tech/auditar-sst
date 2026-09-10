#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Trecho esperado não encontrado: {label}')
    return text.replace(old, new, 1)


def main() -> int:
    app = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('app/Auditar_SST_v1_5_dashboard')

    pub = app / 'pubspec.yaml'
    text = pub.read_text(encoding='utf-8')
    text = replace_once(text, 'version: 3.29.15+158', 'version: 3.29.16+159', 'versão 3.29.16')
    pub.write_text(text, encoding='utf-8')

    p = app / 'lib' / 'screens' / 'new_inspection_screen.dart'
    text = p.read_text(encoding='utf-8')
    text = replace_once(
        text,
        "class NewInspectionScreen extends StatefulWidget {\n  const NewInspectionScreen({super.key});",
        "class NewInspectionScreen extends StatefulWidget {\n  final Company? initialCompany;\n  final bool fieldMode;\n\n  const NewInspectionScreen({\n    super.key,\n    this.initialCompany,\n    this.fieldMode = false,\n  });",
        'parâmetros da vistoria avulsa',
    )
    text = replace_once(
        text,
        """    setState(() {\n      companies = loadedCompanies;\n      templates = loadedTemplates;\n      technicianName.text = defaultTechnician;\n    });\n  }\n""",
        """    final initial = widget.initialCompany;\n    final availableCompanies = [...loadedCompanies];\n    if (initial != null &&\n        !availableCompanies.any((company) => company.id == initial.id)) {\n      availableCompanies.insert(0, initial);\n    }\n\n    setState(() {\n      companies = availableCompanies;\n      templates = loadedTemplates;\n      technicianName.text = defaultTechnician;\n    });\n\n    if (initial != null) {\n      await _companyChanged(initial);\n    }\n  }\n""",
        'pré-seleção da empresa temporária',
    )
    text = replace_once(
        text,
        """    if (!mounted) return;\n\n    setState(() {\n      sites = results[0] as List<WorkSite>;\n      sectors = results[1] as List<Sector>;\n      pgrDocument = doc;\n      pgrAnalysis = parsedPgr;\n    });\n  }\n""",
        """    if (!mounted) return;\n\n    final loadedSectors = results[1] as List<Sector>;\n    setState(() {\n      sites = results[0] as List<WorkSite>;\n      sectors = loadedSectors;\n      if (widget.fieldMode && loadedSectors.length == 1) {\n        selectedSector = loadedSectors.first;\n      }\n      pgrDocument = doc;\n      pgrAnalysis = parsedPgr;\n    });\n  }\n""",
        'seleção automática do setor avulso',
    )
    text = replace_once(
        text,
        "return Scaffold(\n      appBar: AppBar(title: const Text('Nova vistoria')),",
        "return Scaffold(\n      appBar: AppBar(\n        title: Text(widget.fieldMode ? 'Vistoria avulsa' : 'Nova vistoria'),\n      ),",
        'título da vistoria avulsa',
    )
    text = replace_once(
        text,
        """          DropdownButtonFormField<Company>(\n            isExpanded: true,\n            value: selectedCompany,\n            decoration: const InputDecoration(\n              labelText: 'Empresa *',\n            ),\n            items: companies\n                .map(\n                  (company) => DropdownMenuItem(\n                    value: company,\n                    child: Text(company.name),\n                  ),\n                )\n                .toList(),\n            onChanged: _companyChanged,\n          ),\n""",
        """          if (widget.fieldMode && selectedCompany != null)\n            Card(\n              margin: EdgeInsets.zero,\n              color: Theme.of(context)\n                  .colorScheme\n                  .primaryContainer\n                  .withValues(alpha: .28),\n              child: ListTile(\n                leading: const Icon(Icons.location_on_outlined),\n                title: const Text(\n                  'Vistoria rápida / avulsa',\n                  style: TextStyle(fontWeight: FontWeight.w900),\n                ),\n                subtitle: Text(\n                  selectedCompany!.name,\n                  maxLines: 2,\n                  overflow: TextOverflow.ellipsis,\n                ),\n              ),\n            )\n          else\n            DropdownButtonFormField<Company>(\n              isExpanded: true,\n              value: selectedCompany,\n              decoration: const InputDecoration(\n                labelText: 'Empresa *',\n              ),\n              items: companies\n                  .map(\n                    (company) => DropdownMenuItem(\n                      value: company,\n                      child: Text(company.name),\n                    ),\n                  )\n                  .toList(),\n              onChanged: _companyChanged,\n            ),\n""",
        'cartão de contexto avulso',
    )
    p.write_text(text, encoding='utf-8')

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

      await AppDatabase.instance.deleteCompanyIfUnused(company.id);
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
                  hintText: 'Ex.: Obra, fazenda ou cliente visitado',
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
                'A vistoria é registrada normalmente, mas o cliente temporário não aparece na sua carteira de empresas.',
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
      appBar: AppBar(title: const Text('Vistoria rápida')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 760),
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Container(
                padding: const EdgeInsets.all(18),
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
                child: const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.flash_on_rounded, color: AuditarBrand.green),
                        SizedBox(width: 9),
                        Expanded(
                          child: Text(
                            'Vistoria rápida / avulsa',
                            style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w900,
                              fontSize: 18,
                            ),
                          ),
                        ),
                      ],
                    ),
                    SizedBox(height: 7),
                    Text(
                      'Registre uma visita na hora, mesmo quando o cliente ainda não está cadastrado no sistema.',
                      style: TextStyle(color: Colors.white70, height: 1.35),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              _actionCard(
                icon: Icons.fact_check_outlined,
                title: 'Vistoria avulsa',
                subtitle: 'Informe só o cliente/local e siga direto para o checklist e relatório.',
                badge: 'RÁPIDA',
                onTap: _busy ? null : _openStandaloneDialog,
              ),
              _actionCard(
                icon: Icons.business_outlined,
                title: 'Vistoria em empresa cadastrada',
                subtitle: 'Use o cadastro normal da empresa, setor e demais dados já existentes.',
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const NewInspectionScreen()),
                ),
              ),
              _actionCard(
                icon: Icons.auto_awesome_outlined,
                title: 'Registrar melhoria',
                subtitle: 'Guarde uma melhoria ou oportunidade identificada durante a visita.',
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const ImprovementsScreen()),
                ),
              ),
              const SizedBox(height: 4),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AuditarBrand.greenSoft,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AuditarBrand.green.withValues(alpha: .24)),
                ),
                child: const Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.info_outline_rounded, color: AuditarBrand.greenDark, size: 20),
                    SizedBox(width: 9),
                    Expanded(
                      child: Text(
                        'Na vistoria avulsa, o relatório continua com fotos, checklist, não conformidades e plano de ação normalmente.',
                        style: TextStyle(fontSize: 12.2, height: 1.35),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _actionCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback? onTap,
    String? badge,
  }) {
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 14),
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: AuditarBrand.navySoft,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Icon(icon, color: AuditarBrand.navy),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            title,
                            style: const TextStyle(fontWeight: FontWeight.w900),
                          ),
                        ),
                        if (badge != null)
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: AuditarBrand.greenSoft,
                              borderRadius: BorderRadius.circular(999),
                            ),
                            child: Text(
                              badge,
                              style: const TextStyle(
                                color: AuditarBrand.greenDark,
                                fontSize: 9.5,
                                fontWeight: FontWeight.w900,
                                letterSpacing: .4,
                              ),
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 3),
                    Text(
                      subtitle,
                      style: const TextStyle(fontSize: 12.2, color: Colors.black54, height: 1.3),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              const Icon(Icons.chevron_right_rounded),
            ],
          ),
        ),
      ),
    );
  }
}
''', encoding='utf-8')

    p = app / 'lib' / 'screens' / 'home_screen.dart'
    text = p.read_text(encoding='utf-8')
    text = replace_once(
        text,
        "import 'dashboard_screen.dart';\n",
        "import 'dashboard_screen.dart';\nimport 'field_quick_screen.dart';\n",
        'import Campo rápido',
    )
    text = replace_once(
        text,
        "  int openNcs = 0;\n",
        "  int openNcs = 0;\n  int companyCount = 0;\n",
        'contador de empresas',
    )
    company_module = """        _ModuleData(\n          title: 'Empresas',\n          subtitle: 'Cadastros, obras, setores e controles por empresa',\n          icon: Icons.business_outlined,\n          color: AuditarBrand.navy,\n          page: () => const CompaniesScreen(),\n        ),\n"""
    text = replace_once(
        text,
        company_module,
        company_module + """        _ModuleData(\n          title: 'Vistoria rápida',\n          subtitle: 'Vistoria avulsa e registros rápidos em campo',\n          icon: Icons.flash_on_rounded,\n          color: const Color(0xFF16836B),\n          page: () => const FieldQuickScreen(),\n        ),\n""",
        'módulo de vistoria rápida',
    )
    text = replace_once(
        text,
        """      final ncRows = await AppDatabase.instance.getNonConformityRows(\n        includeClosed: false,\n      ).timeout(const Duration(seconds: 15));\n""",
        """      final companies = await AppDatabase.instance.getCompanies()\n          .timeout(const Duration(seconds: 15));\n      final ncRows = await AppDatabase.instance.getNonConformityRows(\n        includeClosed: false,\n      ).timeout(const Duration(seconds: 15));\n""",
        'carregar total de empresas',
    )
    text = replace_once(
        text,
        """        routineSummary = routine;\n        openNcs = ncRows.length;\n""",
        """        routineSummary = routine;\n        openNcs = ncRows.length;\n        companyCount = companies.length;\n""",
        'salvar total de empresas',
    )
    text = replace_once(
        text,
        """        children: [\n          _overviewPanel(desktop: false),\n""",
        """        children: [\n          _workspaceHeader(desktop: false),\n          const SizedBox(height: 12),\n          _overviewPanel(desktop: false),\n""",
        'cabeçalho mobile',
    )
    text = replace_once(
        text,
        """          _newInspectionButton(),\n          const SizedBox(height: 18),\n          _sectionHeader(\n            'Coleta em campo',\n            'Acessos principais para usar durante a visita',\n          ),\n""",
        """          _newInspectionButton(),\n          const SizedBox(height: 8),\n          _fieldQuickButton(),\n          const SizedBox(height: 18),\n          _sectionHeader(\n            'Acesso rápido',\n            'Empresas, campo, vistorias e pendências em um só lugar',\n          ),\n""",
        'atalho mobile da vistoria avulsa',
    )
    text = text.replace('Auditar SST • versão 3.29.13', 'Auditar SST • versão 3.29.16')
    text = text.replace('Auditar SST para Windows • versão 3.29.13', 'Auditar SST para Windows • versão 3.29.16')

    desktop_header = """                Row(\n                  children: [\n                    const Expanded(\n                      child: Column(\n                        crossAxisAlignment: CrossAxisAlignment.start,\n                        children: [\n                          Text(\n                            'Central de gestão SST',\n                            style: TextStyle(\n                              color: AuditarBrand.navy,\n                              fontSize: 24,\n                              fontWeight: FontWeight.w900,\n                            ),\n                          ),\n                          SizedBox(height: 4),\n                          Text(\n                            'Empresas, vistorias, pendências e resultados em um só lugar.',\n                            style: TextStyle(color: AuditarBrand.neutral),\n                          ),\n                        ],\n                      ),\n                    ),\n                    OutlinedButton.icon(\n                      onPressed: () => _open(const SettingsScreen()),\n                      icon: const Icon(Icons.sync_rounded),\n                      label: const Text('Sincronização'),\n                    ),\n                  ],\n                ),\n                const SizedBox(height: 18),\n"""
    text = replace_once(
        text,
        desktop_header,
        """                _workspaceHeader(desktop: true),\n                const SizedBox(height: 16),\n""",
        'cabeçalho desktop',
    )

    workspace = r'''
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
    text = replace_once(
        text,
        '  Widget _overviewPanel({required bool desktop}) {',
        workspace + '  Widget _overviewPanel({required bool desktop}) {',
        'método de cabeçalho visual',
    )
    text = replace_once(
        text,
        """              children: [\n                _metric('Vistorias', inspections, Icons.fact_check_outlined, AuditarBrand.info),\n""",
        """              children: [\n                _metric('Empresas', companyCount, Icons.business_outlined, AuditarBrand.navy),\n                _metric('Vistorias', inspections, Icons.fact_check_outlined, AuditarBrand.info),\n""",
        'métrica empresas',
    )
    text = text.replace('maxColumns: desktop ? 5 : 2,', 'maxColumns: desktop ? 6 : 2,', 1)

    field_button = r'''
  Widget _fieldQuickButton() {
    return SizedBox(
      width: double.infinity,
      child: OutlinedButton.icon(
        onPressed: () => _open(const FieldQuickScreen()),
        icon: const Icon(Icons.flash_on_rounded),
        label: const Text('Vistoria rápida / avulsa'),
      ),
    );
  }

'''
    text = replace_once(
        text,
        '  Widget _routinePanel() {',
        field_button + '  Widget _routinePanel() {',
        'botão da vistoria rápida',
    )
    p.write_text(text, encoding='utf-8')

    checks = {
        'versão': 'version: 3.29.16+159' in pub.read_text(encoding='utf-8'),
        'vistoria avulsa': 'class FieldQuickScreen' in field.read_text(encoding='utf-8'),
        'empresa temporária oculta': 'active: false' in field.read_text(encoding='utf-8'),
        'limpeza de contexto abandonado': 'deleteCompanyIfUnused' in field.read_text(encoding='utf-8'),
        'pré-seleção': 'initialCompany' in (app / 'lib' / 'screens' / 'new_inspection_screen.dart').read_text(encoding='utf-8'),
        'modo campo': 'fieldMode' in (app / 'lib' / 'screens' / 'new_inspection_screen.dart').read_text(encoding='utf-8'),
        'layout Central Auditar': 'Central Auditar' in p.read_text(encoding='utf-8'),
        'atalho home': 'Vistoria rápida / avulsa' in p.read_text(encoding='utf-8'),
        'IA checklist preservada': "'mode': 'checklist_photo'" in (app / 'lib' / 'services' / 'ai_assistant_service.dart').read_text(encoding='utf-8'),
        'PGR múltiplo preservado': 'getPgrDocuments' in (app / 'lib' / 'database.dart').read_text(encoding='utf-8'),
        '44 checklists': (app / 'lib' / 'ready_checklists.dart').read_text(encoding='utf-8').count('  ReadyChecklistDefinition(') == 44,
    }
    missing = [name for name, ok in checks.items() if not ok]
    if missing:
        raise RuntimeError('Validações v3.29.16 falharam: ' + ', '.join(missing))

    print('Patch v3.29.16 aplicado: vistoria rápida/avulsa + layout Central Auditar.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

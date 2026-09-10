from pathlib import Path
import re

APP=Path(__file__).resolve().parent.parent / 'app' / 'Auditar_SST_v1_5_dashboard'

def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError('missing '+label)
    return text.replace(old,new,1)

def sub_once(text, pattern, repl, label):
    out,n=re.subn(pattern,repl,text,count=1,flags=re.S)
    if n!=1: raise RuntimeError(f'missing {label} count={n}')
    return out

# version
p=APP/'pubspec.yaml'; t=p.read_text(encoding='utf-8'); t=replace_once(t,'version: 3.29.15+158','version: 3.29.16+159','version'); p.write_text(t, encoding='utf-8')

# Campo rápido / vistoria avulsa: fonte de referência já testada na linha v3.36,
# adaptada para a estrutura atual sem multi-CNPJ.
field_src = (Path(__file__).resolve().parent / 'v32916_field_quick_screen.dart.txt').read_text(encoding='utf-8')
(APP/'lib/screens/field_quick_screen.dart').write_text(field_src, encoding='utf-8')

# new inspection
p=APP/'lib/screens/new_inspection_screen.dart'; t=p.read_text(encoding='utf-8')
t=replace_once(t,"class NewInspectionScreen extends StatefulWidget {\n  const NewInspectionScreen({super.key});", "class NewInspectionScreen extends StatefulWidget {\n  final Company? initialCompany;\n  final bool fieldMode;\n\n  const NewInspectionScreen({\n    super.key,\n    this.initialCompany,\n    this.fieldMode = false,\n  });",'new constructor')
t=replace_once(t,"    setState(() {\n      companies = loadedCompanies;\n      templates = loadedTemplates;\n      technicianName.text = defaultTechnician;\n    });\n  }", "    final initial = widget.initialCompany;\n    final availableCompanies = [...loadedCompanies];\n    if (initial != null &&\n        !availableCompanies.any((company) => company.id == initial.id)) {\n      availableCompanies.insert(0, initial);\n    }\n\n    setState(() {\n      companies = availableCompanies;\n      templates = loadedTemplates;\n      technicianName.text = defaultTechnician;\n    });\n\n    if (initial != null) {\n      await _companyChanged(initial);\n    }\n  }", 'load initial')
t=replace_once(t,"    setState(() {\n      sites = results[0] as List<WorkSite>;\n      sectors = results[1] as List<Sector>;\n      pgrDocument = doc;\n      pgrAnalysis = parsedPgr;\n    });", "    final loadedSectors = results[1] as List<Sector>;\n    setState(() {\n      sites = results[0] as List<WorkSite>;\n      sectors = loadedSectors;\n      if (widget.fieldMode && loadedSectors.length == 1) {\n        selectedSector = loadedSectors.first;\n      }\n      pgrDocument = doc;\n      pgrAnalysis = parsedPgr;\n    });", 'auto sector')
t=replace_once(t,"appBar: AppBar(title: const Text('Nova vistoria')),", "appBar: AppBar(\n        title: Text(widget.fieldMode ? 'Vistoria avulsa' : 'Nova vistoria'),\n      ),", 'appbar')
old_company="""          DropdownButtonFormField<Company>(
            isExpanded: true,
            value: selectedCompany,
            decoration: const InputDecoration(
              labelText: 'Empresa *',
            ),
            items: companies
                .map(
                  (company) => DropdownMenuItem(
                    value: company,
                    child: Text(company.name),
                  ),
                )
                .toList(),
            onChanged: _companyChanged,
          ),
"""
new_company="""          if (widget.fieldMode && selectedCompany != null)
            Card(
              margin: EdgeInsets.zero,
              color: Theme.of(context)
                  .colorScheme
                  .primaryContainer
                  .withValues(alpha: .28),
              child: ListTile(
                leading: const Icon(Icons.location_on_outlined),
                title: const Text(
                  'Campo rápido • vistoria avulsa',
                  style: TextStyle(fontWeight: FontWeight.w900),
                ),
                subtitle: Text(
                  selectedCompany!.name,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            )
          else
            DropdownButtonFormField<Company>(
              isExpanded: true,
              value: selectedCompany,
              decoration: const InputDecoration(
                labelText: 'Empresa *',
              ),
              items: companies
                  .map(
                    (company) => DropdownMenuItem(
                      value: company,
                      child: Text(company.name),
                    ),
                  )
                  .toList(),
              onChanged: _companyChanged,
            ),
"""
t=replace_once(t,old_company,new_company,'company fieldmode')
p.write_text(t, encoding='utf-8')

# home
p=APP/'lib/screens/home_screen.dart'; t=p.read_text(encoding='utf-8')
t=replace_once(t,"import 'dashboard_screen.dart';\n", "import 'dashboard_screen.dart';\nimport 'field_quick_screen.dart';\n",'home import')
t=replace_once(t,"  int openNcs = 0;\n", "  int openNcs = 0;\n  int companyCount = 0;\n",'company count')
marker="""        _ModuleData(
          title: 'Empresas',
          subtitle: 'Cadastros, obras, setores e controles por empresa',
          icon: Icons.business_outlined,
          color: AuditarBrand.navy,
          page: () => const CompaniesScreen(),
        ),
"""
insert=marker+"""        _ModuleData(
          title: 'Campo rápido',
          subtitle: 'Vistoria avulsa e registros rápidos fora da carteira',
          icon: Icons.location_on_outlined,
          color: const Color(0xFF16836B),
          page: () => const FieldQuickScreen(),
        ),
"""
t=replace_once(t,marker,insert,'quick module')
t=replace_once(t,"      if (mounted && result.received > 0) _refresh();", "      if (mounted && result.received > 0) {\n        unawaited(_refresh(showLoading: false));\n      }",'sync refresh')
t=replace_once(t,"  Future<void> _refresh() async {\n    if (mounted) setState(() { loading = true; loadError = ''; });", "  Future<void> _refresh({bool showLoading = true}) async {\n    if (showLoading && mounted) {\n      setState(() {\n        loading = true;\n        loadError = '';\n      });\n    }",'refresh signature')
t=replace_once(t,"      final ncRows = await AppDatabase.instance.getNonConformityRows(\n", "      final companies = await AppDatabase.instance.getCompanies()\n          .timeout(const Duration(seconds: 15));\n      final ncRows = await AppDatabase.instance.getNonConformityRows(\n",'load companies')
t=replace_once(t,"        openNcs = ncRows.length;\n        activeInspection = inProgress;", "        openNcs = ncRows.length;\n        companyCount = companies.length;\n        activeInspection = inProgress;",'set company count')
t=replace_once(t,"    } catch (e) {\n      if (!mounted) return;\n      setState(() {\n        loading = false;\n        loadError = '$e'.replaceFirst('Bad state: ', '').trim();\n      });\n    }", "    } catch (e) {\n      if (!mounted) return;\n      if (showLoading) {\n        setState(() {\n          loading = false;\n          loadError = '$e'.replaceFirst('Bad state: ', '').trim();\n        });\n      }\n    }",'refresh catch')
t=replace_once(t,"    await _refresh();\n  }\n\n  Future<void> _showModules()", "    await _refresh(showLoading: false);\n  }\n\n  Future<void> _showModules()",'open silent')
t=replace_once(t,"            onPressed: _refresh,\n            icon: const Icon(Icons.refresh_rounded),", "            onPressed: () => _refresh(showLoading: false),\n            icon: const Icon(Icons.refresh_rounded),",'refresh button')
t=replace_once(t,"        children: [\n          _overviewPanel(desktop: false),", "        children: [\n          _workspaceHeader(desktop: false),\n          const SizedBox(height: 12),\n          _overviewPanel(desktop: false),",'mobile header')
t=replace_once(t,"          _newInspectionButton(),\n          const SizedBox(height: 18),", "          _newInspectionButton(),\n          const SizedBox(height: 8),\n          _fieldQuickButton(),\n          const SizedBox(height: 18),",'mobile quick button')
t=t.replace("'Coleta em campo',\n            'Acessos principais para usar durante a visita',", "'Acesso rápido',\n            'Carteira de empresas, campo e acompanhamento geral',",1)
start=t.find("                Row(\n                  children: [\n                    const Expanded(\n                      child: Column(")
end=t.find("                _overviewPanel(desktop: true),", start)
if start<0 or end<0: raise RuntimeError('desktop header bounds')
t=t[:start]+"                _workspaceHeader(desktop: true),\n                const SizedBox(height: 16),\n"+t[end:]
t=t.replace('Auditar SST • versão 3.29.13','Auditar SST • versão 3.29.16')
t=t.replace('Auditar SST para Windows • versão 3.29.13','Auditar SST para Windows • versão 3.29.16')
ws="  Widget _workspaceHeader({required bool desktop}) {\n    return Container(\n      padding: EdgeInsets.all(desktop ? 20 : 16),\n      decoration: BoxDecoration(\n        gradient: const LinearGradient(\n          begin: Alignment.topLeft,\n          end: Alignment.bottomRight,\n          colors: [AuditarBrand.navyDark, AuditarBrand.navy],\n        ),\n        borderRadius: BorderRadius.circular(20),\n        boxShadow: const [\n          BoxShadow(\n            color: Color(0x1A0E1A43),\n            blurRadius: 18,\n            offset: Offset(0, 8),\n          ),\n        ],\n      ),\n      child: Row(\n        children: [\n          Container(\n            width: desktop ? 52 : 46,\n            height: desktop ? 52 : 46,\n            decoration: BoxDecoration(\n              color: Colors.white.withValues(alpha: .12),\n              borderRadius: BorderRadius.circular(15),\n              border: Border.all(color: Colors.white.withValues(alpha: .16)),\n            ),\n            child: const Icon(\n              Icons.hub_outlined,\n              color: AuditarBrand.green,\n              size: 27,\n            ),\n          ),\n          const SizedBox(width: 13),\n          Expanded(\n            child: Column(\n              crossAxisAlignment: CrossAxisAlignment.start,\n              children: [\n                Text(\n                  'Central Auditar',\n                  style: TextStyle(\n                    color: Colors.white,\n                    fontSize: desktop ? 23 : 19,\n                    fontWeight: FontWeight.w900,\n                  ),\n                ),\n                const SizedBox(height: 3),\n                Text(\n                  desktop\n                      ? 'Todas as empresas, pendências e atividades de campo em um só lugar.'\n                      : 'Todas as empresas e atividades de campo.',\n                  style: const TextStyle(\n                    color: Colors.white70,\n                    fontSize: 12,\n                    height: 1.3,\n                  ),\n                ),\n              ],\n            ),\n          ),\n          const SizedBox(width: 10),\n          Container(\n            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),\n            decoration: BoxDecoration(\n              color: AuditarBrand.green.withValues(alpha: .14),\n              borderRadius: BorderRadius.circular(999),\n              border: Border.all(color: AuditarBrand.green.withValues(alpha: .34)),\n            ),\n            child: const Row(\n              mainAxisSize: MainAxisSize.min,\n              children: [\n                Icon(Icons.public_rounded, size: 15, color: AuditarBrand.green),\n                SizedBox(width: 5),\n                Text(\n                  'GERAL',\n                  style: TextStyle(\n                    color: Colors.white,\n                    fontSize: 10.5,\n                    fontWeight: FontWeight.w900,\n                    letterSpacing: .4,\n                  ),\n                ),\n              ],\n            ),\n          ),\n        ],\n      ),\n    );\n  }\n\n"
t=replace_once(t,'  Widget _overviewPanel({required bool desktop}) {',ws+'  Widget _overviewPanel({required bool desktop}) {','workspace method')
cur_start=t.find('  Widget _overviewPanel({required bool desktop}) {')
cur_end=t.find('  Widget _metric(',cur_start)
old_overview="  Widget _overviewPanel({required bool desktop}) {\n    final inspections = summary['inspections'] ?? 0;\n    final pending = summary['pending'] ?? 0;\n    final overdue = summary['ncOverdue'] ?? 0;\n\n    return Card(\n      margin: EdgeInsets.zero,\n      child: Padding(\n        padding: EdgeInsets.all(desktop ? 20 : 15),\n        child: Column(\n          crossAxisAlignment: CrossAxisAlignment.start,\n          children: [\n            const Row(\n              children: [\n                Expanded(\n                  child: Text(\n                    'Prioridades da carteira',\n                    style: TextStyle(\n                      color: AuditarBrand.navy,\n                      fontSize: 18,\n                      fontWeight: FontWeight.w900,\n                    ),\n                  ),\n                ),\n                Text(\n                  'Todas as empresas',\n                  style: TextStyle(\n                    color: AuditarBrand.neutral,\n                    fontSize: 11.5,\n                    fontWeight: FontWeight.w800,\n                  ),\n                ),\n              ],\n            ),\n            const SizedBox(height: 12),\n            ResponsiveWrap(\n              minItemWidth: desktop ? 150 : 125,\n              maxColumns: desktop ? 5 : 2,\n              children: [\n                _metric(\n                  'Empresas',\n                  companyCount,\n                  Icons.business_outlined,\n                  AuditarBrand.navy,\n                ),\n                _metric(\n                  'Vistorias',\n                  inspections,\n                  Icons.fact_check_outlined,\n                  AuditarBrand.info,\n                ),\n                _metric(\n                  'NCs abertas',\n                  openNcs,\n                  Icons.warning_amber_rounded,\n                  AuditarBrand.danger,\n                ),\n                _metric(\n                  'Ações pendentes',\n                  pending,\n                  Icons.assignment_outlined,\n                  AuditarBrand.warning,\n                ),\n                _metric(\n                  'Ações vencidas',\n                  overdue,\n                  Icons.event_busy_outlined,\n                  AuditarBrand.danger,\n                ),\n              ],\n            ),\n          ],\n        ),\n      ),\n    );\n  }\n\n"
t=t[:cur_start]+old_overview+t[cur_end:]
field_method="  Widget _fieldQuickButton() {\n    return SizedBox(\n      width: double.infinity,\n      child: OutlinedButton.icon(\n        onPressed: () => _open(const FieldQuickScreen()),\n        icon: const Icon(Icons.location_on_outlined),\n        label: const Text('Campo rápido / vistoria avulsa'),\n      ),\n    );\n  }\n\n"
t=replace_once(t,'  Widget _routinePanel() {',field_method+'  Widget _routinePanel() {','field method')
p.write_text(t, encoding='utf-8')

# company detail simple quick actions
p=APP/'lib/screens/company_detail_screen.dart'; t=p.read_text(encoding='utf-8')
t=replace_once(t,"import 'management_panel_screen.dart';\n", "import 'management_panel_screen.dart';\nimport 'new_inspection_screen.dart';\n",'detail import')
needle="""          const SizedBox(height: 10),
          ResponsiveWrap(
            minItemWidth: 138,
            maxColumns: 3,
"""
repl="""          const SizedBox(height: 12),
          _companyQuickActions(),
          const SizedBox(height: 12),
          ResponsiveWrap(
            minItemWidth: 138,
            maxColumns: 3,
"""
t=replace_once(t,needle,repl,'detail quick placement')
quick="""  Widget _companyQuickActions() {
    return ResponsiveWrap(
      minItemWidth: 175,
      maxColumns: 2,
      spacing: 9,
      runSpacing: 9,
      children: [
        _shortcut(
          icon: Icons.add_task_rounded,
          title: 'Nova vistoria',
          subtitle: 'Iniciar já vinculada a esta empresa',
          onTap: () => _open(
            NewInspectionScreen(initialCompany: widget.company),
          ),
        ),
        _shortcut(
          icon: Icons.description_outlined,
          title: 'PGR + IA',
          subtitle: hasPgr
              ? 'PGR disponível para consulta e análise'
              : 'Cadastrar ou analisar PGR',
          onTap: () => _open(PgrScreen(company: widget.company)),
        ),
      ],
    );
  }

"""
t=replace_once(t,'  Widget _inspectionsTab() {',quick+'  Widget _inspectionsTab() {','quick method')
p.write_text(t, encoding='utf-8')

checks = {
    'version': 'version: 3.29.16+159' in (APP/'pubspec.yaml').read_text(encoding='utf-8'),
    'vistoria avulsa': 'Vistoria avulsa' in (APP/'lib/screens/field_quick_screen.dart').read_text(encoding='utf-8'),
    'avulsa oculta': 'active: false' in (APP/'lib/screens/field_quick_screen.dart').read_text(encoding='utf-8'),
    'field mode': 'fieldMode' in (APP/'lib/screens/new_inspection_screen.dart').read_text(encoding='utf-8'),
    'initial company': 'initialCompany' in (APP/'lib/screens/new_inspection_screen.dart').read_text(encoding='utf-8'),
    'central auditar': 'Central Auditar' in (APP/'lib/screens/home_screen.dart').read_text(encoding='utf-8'),
    'geral': "'GERAL'" in (APP/'lib/screens/home_screen.dart').read_text(encoding='utf-8'),
    'campo rápido home': 'FieldQuickScreen' in (APP/'lib/screens/home_screen.dart').read_text(encoding='utf-8'),
    'ação empresa': "title: 'Nova vistoria'" in (APP/'lib/screens/company_detail_screen.dart').read_text(encoding='utf-8'),
    'IA checklist': "'mode': 'checklist_photo'" in (APP/'lib/services/ai_assistant_service.dart').read_text(encoding='utf-8'),
    'IA revisor': "'mode': 'report_review_chat'" in (APP/'lib/services/ai_assistant_service.dart').read_text(encoding='utf-8'),
    'assinatura tela cheia': 'Assinar em tela cheia' in (APP/'lib/screens/signature_screen.dart').read_text(encoding='utf-8'),
    'assinatura gov': "value: 'gov'" in (APP/'lib/screens/signature_screen.dart').read_text(encoding='utf-8'),
    'sem assinatura': "value: 'none'" in (APP/'lib/screens/signature_screen.dart').read_text(encoding='utf-8'),
    'plano ação opcional': 'includeActionPlan' in (APP/'lib/screens/signature_screen.dart').read_text(encoding='utf-8'),
    '44 checklists': (APP/'lib/ready_checklists.dart').read_text(encoding='utf-8').count('  ReadyChecklistDefinition(') == 44,
}
missing=[name for name, ok in checks.items() if not ok]
if missing:
    raise RuntimeError('Validações v3.29.16 falharam: ' + ', '.join(missing))
print('Patch v3.29.16 aplicado: vistoria avulsa + layout Central Auditar.')

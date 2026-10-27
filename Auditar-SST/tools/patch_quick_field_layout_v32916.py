#!/usr/bin/env python3
from __future__ import annotations

import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
APP = REPO / 'app' / 'Auditar_SST_v1_5_dashboard'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Trecho esperado não encontrado: {label}')
    return text.replace(old, new, 1)


def patch_home() -> None:
    path = APP / 'lib' / 'screens' / 'home_screen.dart'
    text = path.read_text(encoding='utf-8')

    text = replace_once(
        text,
        "import 'dashboard_screen.dart';\n",
        "import 'dashboard_screen.dart';\nimport 'field_quick_screen.dart';\n",
        'import Campo rápido',
    )
    text = replace_once(
        text,
        '  int openNcs = 0;\n',
        '  int openNcs = 0;\n  int companyCount = 0;\n',
        'contador de empresas',
    )
    text = replace_once(
        text,
        """        _ModuleData(\n          title: 'Vistorias',""",
        """        _ModuleData(\n          title: 'Campo rápido',\n          subtitle: 'Vistoria avulsa e registros rápidos fora da carteira',\n          icon: Icons.location_on_outlined,\n          color: const Color(0xFF16836B),\n          page: () => const FieldQuickScreen(),\n        ),\n        _ModuleData(\n          title: 'Vistorias',""",
        'módulo Campo rápido',
    )

    # Mantém a sensação de rapidez: sincronização em segundo plano não apaga a tela.
    text = replace_once(
        text,
        """    _deviceSyncSubscription = DeviceSyncService.events.listen((result) {\n      if (mounted && result.received > 0) _refresh();\n    });""",
        """    _deviceSyncSubscription = DeviceSyncService.events.listen((result) {\n      if (mounted && result.received > 0) {\n        unawaited(_refresh(showLoading: false));\n      }\n    });""",
        'refresh silencioso da sincronização',
    )
    text = replace_once(
        text,
        """  Future<void> _refresh() async {\n    if (mounted) setState(() { loading = true; loadError = ''; });""",
        """  Future<void> _refresh({bool showLoading = true}) async {\n    if (showLoading && mounted) {\n      setState(() {\n        loading = true;\n        loadError = '';\n      });\n    }""",
        'assinatura refresh',
    )
    text = replace_once(
        text,
        """      final result = await AppDatabase.instance.getDashboardSummary()\n          .timeout(const Duration(seconds: 15));\n      final ncRows""",
        """      final result = await AppDatabase.instance.getDashboardSummary()\n          .timeout(const Duration(seconds: 15));\n      final companies = await AppDatabase.instance.getCompanies()\n          .timeout(const Duration(seconds: 15));\n      final ncRows""",
        'carregamento de empresas',
    )
    text = replace_once(
        text,
        """        openNcs = ncRows.length;\n        activeInspection = inProgress;""",
        """        openNcs = ncRows.length;\n        companyCount = companies.length;\n        activeInspection = inProgress;""",
        'atribuição contador empresas',
    )
    text = replace_once(
        text,
        """    } catch (e) {\n      if (!mounted) return;\n      setState(() {\n        loading = false;\n        loadError = '$e'.replaceFirst('Bad state: ', '').trim();\n      });\n    }\n  }""",
        """    } catch (e) {\n      if (!mounted) return;\n      if (showLoading) {\n        setState(() {\n          loading = false;\n          loadError = '$e'.replaceFirst('Bad state: ', '').trim();\n        });\n      }\n    }\n  }""",
        'tratamento refresh silencioso',
    )
    text = replace_once(
        text,
        """    await _refresh();\n  }\n\n  Future<void> _showModules""",
        """    await _refresh(showLoading: false);\n  }\n\n  Future<void> _showModules""",
        'refresh após navegação',
    )
    text = text.replace(
        'onPressed: _refresh,',
        'onPressed: () => _refresh(showLoading: false),',
        1,
    )

    # Hierarquia visual mobile da versão aprovada pelo usuário.
    text = replace_once(
        text,
        """        children: [\n          _overviewPanel(desktop: false),""",
        """        children: [\n          _workspaceHeader(desktop: false),\n          const SizedBox(height: 12),\n          _overviewPanel(desktop: false),""",
        'Central Auditar mobile',
    )
    text = replace_once(
        text,
        """          _newInspectionButton(),\n          const SizedBox(height: 18),\n          _sectionHeader(\n            'Coleta em campo',\n            'Acessos principais para usar durante a visita',\n          ),""",
        """          _newInspectionButton(),\n          const SizedBox(height: 8),\n          _fieldQuickButton(),\n          const SizedBox(height: 18),\n          _sectionHeader(\n            'Acesso rápido',\n            'Carteira de empresas, campo e acompanhamento geral',\n          ),""",
        'ações principais mobile',
    )
    text = text.replace(
        "'Auditar SST • versão 3.29.13'",
        "'Auditar SST • versão 3.29.16'",
        1,
    )
    text = text.replace(
        "'Auditar SST para Windows • versão 3.29.13'",
        "'Auditar SST para Windows • versão 3.29.16'",
        1,
    )

    workspace_marker = '  Widget _overviewPanel({required bool desktop}) {'
    workspace_method = r'''  Widget _workspaceHeader({required bool desktop}) {
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
        workspace_marker,
        workspace_method + workspace_marker,
        'método Central Auditar',
    )

    start = text.index('  Widget _overviewPanel({required bool desktop}) {')
    end = text.index('  Widget _metric(', start)
    overview = r'''  Widget _overviewPanel({required bool desktop}) {
    final inspections = summary['inspections'] ?? 0;
    final pending = summary['pending'] ?? 0;
    final overdue = summary['ncOverdue'] ?? 0;

    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: EdgeInsets.all(desktop ? 20 : 15),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Expanded(
                  child: Text(
                    'Prioridades da carteira',
                    style: TextStyle(
                      color: AuditarBrand.navy,
                      fontSize: 18,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ),
                Text(
                  'Todas as empresas',
                  style: TextStyle(
                    color: AuditarBrand.neutral,
                    fontSize: 11.5,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ResponsiveWrap(
              minItemWidth: desktop ? 150 : 125,
              maxColumns: desktop ? 5 : 2,
              children: [
                _metric('Empresas', companyCount, Icons.business_outlined, AuditarBrand.navy),
                _metric('Vistorias', inspections, Icons.fact_check_outlined, AuditarBrand.info),
                _metric('NCs abertas', openNcs, Icons.warning_amber_rounded, AuditarBrand.danger),
                _metric('Ações pendentes', pending, Icons.assignment_outlined, AuditarBrand.warning),
                _metric('Ações vencidas', overdue, Icons.event_busy_outlined, AuditarBrand.danger),
              ],
            ),
          ],
        ),
      ),
    );
  }

'''
    text = text[:start] + overview + text[end:]

    text = replace_once(
        text,
        '  Widget _routinePanel() {',
        r'''  Widget _fieldQuickButton() {
    return SizedBox(
      width: double.infinity,
      child: OutlinedButton.icon(
        onPressed: () => _open(const FieldQuickScreen()),
        icon: const Icon(Icons.location_on_outlined),
        label: const Text('Campo rápido / vistoria avulsa'),
      ),
    );
  }

  Widget _routinePanel() {''',
        'botão Campo rápido',
    )

    path.write_text(text, encoding='utf-8')


def patch_new_inspection() -> None:
    path = APP / 'lib' / 'screens' / 'new_inspection_screen.dart'
    text = path.read_text(encoding='utf-8')

    text = replace_once(
        text,
        """class NewInspectionScreen extends StatefulWidget {\n  const NewInspectionScreen({super.key});""",
        """class NewInspectionScreen extends StatefulWidget {\n  final Company? initialCompany;\n  final bool fieldMode;\n\n  const NewInspectionScreen({\n    super.key,\n    this.initialCompany,\n    this.fieldMode = false,\n  });""",
        'construtor da Nova vistoria',
    )
    text = replace_once(
        text,
        """    setState(() {\n      companies = loadedCompanies;\n      templates = loadedTemplates;\n      technicianName.text = defaultTechnician;\n    });\n  }""",
        """    final initial = widget.initialCompany;\n    final availableCompanies = [...loadedCompanies];\n    if (initial != null &&\n        !availableCompanies.any((company) => company.id == initial.id)) {\n      availableCompanies.insert(0, initial);\n    }\n\n    setState(() {\n      companies = availableCompanies;\n      templates = loadedTemplates;\n      technicianName.text = defaultTechnician;\n    });\n\n    if (initial != null) {\n      await _companyChanged(initial);\n    }\n  }""",
        'pré-seleção da empresa avulsa',
    )
    text = replace_once(
        text,
        """    setState(() {\n      sites = results[0] as List<WorkSite>;\n      sectors = results[1] as List<Sector>;\n      pgrDocument = doc;\n      pgrAnalysis = parsedPgr;\n    });""",
        """    final loadedSectors = results[1] as List<Sector>;\n    setState(() {\n      sites = results[0] as List<WorkSite>;\n      sectors = loadedSectors;\n      if (widget.fieldMode && loadedSectors.length == 1) {\n        selectedSector = loadedSectors.first;\n      }\n      pgrDocument = doc;\n      pgrAnalysis = parsedPgr;\n    });""",
        'setor automático da vistoria avulsa',
    )
    text = replace_once(
        text,
        "appBar: AppBar(title: const Text('Nova vistoria')),
",
        """appBar: AppBar(\n        title: Text(widget.fieldMode ? 'Vistoria avulsa' : 'Nova vistoria'),\n      ),\n""",
        'título vistoria avulsa',
    )

    old_company = r'''          DropdownButtonFormField<Company>(
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
          ),'''
    new_company = r'''          if (widget.fieldMode && selectedCompany != null)
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
            ),'''
    text = replace_once(text, old_company, new_company, 'empresa no modo avulso')
    path.write_text(text, encoding='utf-8')


def main() -> int:
    patch_home()
    patch_new_inspection()

    source = REPO / 'tools' / 'reference_field_quick_v32916.dart'
    target = APP / 'lib' / 'screens' / 'field_quick_screen.dart'
    shutil.copyfile(source, target)

    pubspec = APP / 'pubspec.yaml'
    pub = pubspec.read_text(encoding='utf-8')
    pub = replace_once(pub, 'version: 3.29.15+158', 'version: 3.29.16+159', 'versão')
    pubspec.write_text(pub, encoding='utf-8')

    home = (APP / 'lib' / 'screens' / 'home_screen.dart').read_text(encoding='utf-8')
    field = target.read_text(encoding='utf-8')
    new_inspection = (APP / 'lib' / 'screens' / 'new_inspection_screen.dart').read_text(encoding='utf-8')
    checklist = (APP / 'lib' / 'screens' / 'checklist_screen.dart').read_text(encoding='utf-8')
    ai = (APP / 'lib' / 'services' / 'ai_assistant_service.dart').read_text(encoding='utf-8')
    pdf = (APP / 'lib' / 'services' / 'pdf_service.dart').read_text(encoding='utf-8')
    pgr = (APP / 'lib' / 'screens' / 'pgr_screen.dart').read_text(encoding='utf-8')
    media = (APP / 'lib' / 'services' / 'media_sync_service.dart').read_text(encoding='utf-8')

    checks = {
        'versão': 'version: 3.29.16+159' in pubspec.read_text(encoding='utf-8'),
        'Central Auditar': 'Central Auditar' in home,
        'Prioridades': 'Prioridades da carteira' in home,
        'Campo rápido home': 'Campo rápido / vistoria avulsa' in home and 'FieldQuickScreen' in home,
        'Vistoria avulsa': 'Vistoria avulsa' in field and 'active: false' in field,
        'modo campo': 'initialCompany' in new_inspection and 'fieldMode' in new_inspection,
        'vistoria rápida checklist': 'Modo vistoria rápida' in checklist,
        'IA 2 tentativas': 'const maxAttempts = 2;' in ai,
        'IA 1024': '1024' in ai,
        'executivo': all(marker in pdf for marker in ('QUANTITATIVO OPERACIONAL', 'QUADRO DE PROVIDÊNCIAS', 'O QUE FICOU PENDENTE', 'O QUE JÁ FOI RESOLVIDO')),
        'PGR múltiplo': 'getPgrDocuments' in pgr and 'Remover PGR' in pgr,
        'logo sincronizada': 'company_logo' in media,
    }
    missing = [name for name, ok in checks.items() if not ok]
    if missing:
        raise RuntimeError('Validações v3.29.16 falharam: ' + ', '.join(missing))

    print('v3.29.16: Campo rápido/vistoria avulsa e layout Central Auditar restaurados; recursos atuais preservados.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

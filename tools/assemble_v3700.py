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
    subprocess.run([sys.executable, str(repo / 'tools' / 'assemble_v3610.py')], cwd=repo, check=True)
    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'

    pub = app / 'pubspec.yaml'
    text = pub.read_text(encoding='utf-8')
    text = replace_once(text, 'version: 3.36.1+156', 'version: 3.37.0+157', 'versão 3.37.0')
    pub.write_text(text, encoding='utf-8')

    reports_screen = r'''import 'package:flutter/material.dart';

import '../brand.dart';
import '../database.dart';
import 'history_screen.dart';
import 'report_screen.dart';

class ReportsCenterScreen extends StatefulWidget {
  const ReportsCenterScreen({super.key});

  @override
  State<ReportsCenterScreen> createState() => _ReportsCenterScreenState();
}

class _ReportsCenterScreenState extends State<ReportsCenterScreen> {
  final searchController = TextEditingController();
  List<Map<String, Object?>> rows = [];
  bool loading = true;
  String filter = 'Todos';

  @override
  void initState() {
    super.initState();
    searchController.addListener(() {
      if (mounted) setState(() {});
    });
    _load();
  }

  @override
  void dispose() {
    searchController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    if (mounted) setState(() => loading = true);
    final result = await AppDatabase.instance.getInspectionHistory();
    if (!mounted) return;
    setState(() {
      rows = result;
      loading = false;
    });
  }

  List<Map<String, Object?>> get filteredRows {
    final q = searchController.text.trim().toLowerCase();
    return rows.where((row) {
      final status = '${row['status'] ?? ''}'.trim();
      if (filter == 'Finalizados' && status != 'Finalizada') return false;
      if (filter == 'Em elaboração' && status != 'Em andamento') return false;
      if (q.isEmpty) return true;
      final haystack = [
        row['company_name'],
        row['report_number'],
        row['worksite_name'],
        row['sector_name'],
        row['area'],
        row['status'],
        row['date'],
      ].map((v) => '$v'.toLowerCase()).join(' ');
      return haystack.contains(q);
    }).toList(growable: false);
  }

  int get finalized => rows.where((r) => '${r['status'] ?? ''}'.trim() == 'Finalizada').length;
  int get drafting => rows.where((r) => '${r['status'] ?? ''}'.trim() == 'Em andamento').length;

  String _date(Object? value) {
    final raw = '$value'.trim();
    if (raw.length >= 10) return raw.substring(0, 10).split('-').reversed.join('/');
    return raw;
  }

  Future<void> _openRow(Map<String, Object?> row) async {
    final status = '${row['status'] ?? ''}'.trim();
    final id = '${row['id'] ?? ''}'.trim();
    if (id.isEmpty) return;
    if (status == 'Finalizada') {
      final number = '${row['report_number'] ?? ''}'.trim();
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => ReportScreen(
            inspectionId: id,
            title: number.isEmpty ? 'Relatório SST' : 'Relatório $number',
          ),
        ),
      );
    } else {
      final companyId = '${row['company_id'] ?? ''}'.trim();
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => HistoryScreen(
            companyId: companyId.isEmpty ? null : companyId,
            resumeLatestDraft: true,
          ),
        ),
      );
    }
    if (mounted) await _load();
  }

  @override
  Widget build(BuildContext context) {
    final visible = filteredRows;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Central de relatórios'),
        actions: [
          IconButton(
            tooltip: 'Atualizar',
            onPressed: _load,
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(18),
              children: [
                Card(
                  margin: EdgeInsets.zero,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Relatórios SST',
                          style: TextStyle(
                            color: AuditarBrand.navy,
                            fontSize: 20,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                        const SizedBox(height: 4),
                        const Text(
                          'Encontre rapidamente vistorias em elaboração e relatórios finalizados.',
                          style: TextStyle(color: AuditarBrand.neutral),
                        ),
                        const SizedBox(height: 14),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: [
                            _summaryChip('Finalizados', finalized, Icons.task_alt_rounded, AuditarBrand.greenDark),
                            _summaryChip('Em elaboração', drafting, Icons.edit_note_rounded, AuditarBrand.warning),
                            _summaryChip('Total', rows.length, Icons.folder_copy_outlined, AuditarBrand.info),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 14),
                TextField(
                  controller: searchController,
                  decoration: InputDecoration(
                    hintText: 'Buscar empresa, número do relatório, obra ou setor...',
                    prefixIcon: const Icon(Icons.search_rounded),
                    suffixIcon: searchController.text.isEmpty
                        ? null
                        : IconButton(
                            onPressed: searchController.clear,
                            icon: const Icon(Icons.close_rounded),
                          ),
                    border: const OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 10),
                Wrap(
                  spacing: 7,
                  children: ['Todos', 'Finalizados', 'Em elaboração']
                      .map(
                        (value) => ChoiceChip(
                          label: Text(value),
                          selected: filter == value,
                          onSelected: (_) => setState(() => filter = value),
                        ),
                      )
                      .toList(growable: false),
                ),
                const SizedBox(height: 14),
                if (visible.isEmpty)
                  const Card(
                    child: Padding(
                      padding: EdgeInsets.all(28),
                      child: Center(child: Text('Nenhum relatório encontrado.')),
                    ),
                  )
                else
                  ...visible.map(_reportCard),
              ],
            ),
    );
  }

  Widget _summaryChip(String label, int value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
      decoration: BoxDecoration(
        color: color.withValues(alpha: .08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: .16)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 19),
          const SizedBox(width: 7),
          Text('$label: $value', style: TextStyle(color: color, fontWeight: FontWeight.w800)),
        ],
      ),
    );
  }

  Widget _reportCard(Map<String, Object?> row) {
    final status = '${row['status'] ?? ''}'.trim();
    final finalizedRow = status == 'Finalizada';
    final company = '${row['company_name'] ?? 'Empresa'}'.trim();
    final number = '${row['report_number'] ?? ''}'.trim();
    final sector = '${row['sector_name'] ?? ''}'.trim();
    final area = '${row['area'] ?? ''}'.trim();
    final site = '${row['worksite_name'] ?? ''}'.trim();
    final location = [site, sector, area].where((v) => v.isNotEmpty).toSet().join(' • ');
    return Card(
      margin: const EdgeInsets.only(bottom: 9),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        leading: Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            color: (finalizedRow ? AuditarBrand.greenDark : AuditarBrand.warning).withValues(alpha: .09),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(
            finalizedRow ? Icons.picture_as_pdf_outlined : Icons.edit_document,
            color: finalizedRow ? AuditarBrand.greenDark : AuditarBrand.warning,
          ),
        ),
        title: Text(
          number.isEmpty ? company : '$number • $company',
          style: const TextStyle(fontWeight: FontWeight.w900),
        ),
        subtitle: Text(
          [if (location.isNotEmpty) location, if (_date(row['date']).isNotEmpty) _date(row['date'])].join(' • '),
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),
        trailing: Chip(
          label: Text(finalizedRow ? 'FINALIZADO' : 'EM ELABORAÇÃO'),
          visualDensity: VisualDensity.compact,
        ),
        onTap: () => _openRow(row),
      ),
    );
  }
}
'''
    (app / 'lib' / 'screens' / 'reports_center_screen.dart').write_text(reports_screen, encoding='utf-8')

    search_screen = r'''import 'package:flutter/material.dart';

import '../brand.dart';
import '../database.dart';
import '../models.dart';
import 'action_plan_screen.dart';
import 'companies_screen.dart';
import 'history_screen.dart';
import 'pgr_screen.dart';
import 'trainings_screen.dart';
import 'workers_screen.dart';

class GlobalSearchScreen extends StatefulWidget {
  const GlobalSearchScreen({super.key});

  @override
  State<GlobalSearchScreen> createState() => _GlobalSearchScreenState();
}

class _GlobalSearchScreenState extends State<GlobalSearchScreen> {
  final controller = TextEditingController();
  final List<_SearchEntry> entries = [];
  bool loading = true;

  @override
  void initState() {
    super.initState();
    controller.addListener(() {
      if (mounted) setState(() {});
    });
    _load();
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    if (mounted) setState(() => loading = true);
    final db = AppDatabase.instance;
    final companies = await db.getCompanies();
    final workers = await db.getWorkers();
    final trainings = await db.getTrainingControls();
    final inspections = await db.getInspectionHistory();
    final actions = await db.getPendingActions(includeCompleted: true);
    final companyById = {for (final company in companies) company.id: company};
    final workerMaps = <String, Map<String, Object?>>{};
    final found = <_SearchEntry>[];

    for (final company in companies) {
      found.add(
        _SearchEntry(
          kind: 'Empresa',
          title: company.name,
          subtitle: 'Cadastro e ambiente da empresa',
          icon: Icons.business_outlined,
          color: AuditarBrand.navy,
          searchText: company.toMap().values.join(' '),
          page: () => const CompaniesScreen(),
        ),
      );
      final docs = await db.getPgrDocuments(company.id);
      for (final doc in docs) {
        final label = '${doc['name'] ?? doc['title'] ?? doc['file_name'] ?? 'PGR'}'.trim();
        found.add(
          _SearchEntry(
            kind: 'PGR',
            title: label.isEmpty ? 'PGR' : label,
            subtitle: company.name,
            icon: Icons.description_outlined,
            color: AuditarBrand.greenDark,
            searchText: '${doc.values.join(' ')} ${company.name}',
            page: () => PgrScreen(company: company),
          ),
        );
      }
    }

    for (final worker in workers) {
      final map = worker.toMap();
      workerMaps['${map['id'] ?? ''}'] = map;
      final companyId = '${map['company_id'] ?? ''}';
      final companyName = companyById[companyId]?.name ?? '';
      final role = '${map['role'] ?? map['job_title'] ?? map['position'] ?? ''}'.trim();
      found.add(
        _SearchEntry(
          kind: 'Trabalhador',
          title: '${map['name'] ?? 'Trabalhador'}',
          subtitle: [companyName, role].where((v) => v.isNotEmpty).join(' • '),
          icon: Icons.person_outline_rounded,
          color: const Color(0xFF3766A6),
          searchText: '${map.values.join(' ')} $companyName',
          page: () => const WorkersScreen(),
        ),
      );
    }

    for (final training in trainings) {
      final worker = workerMaps[training.workerId];
      final companyId = '${worker?['company_id'] ?? ''}';
      final companyName = companyById[companyId]?.name ?? '';
      final workerName = '${worker?['name'] ?? ''}'.trim();
      found.add(
        _SearchEntry(
          kind: 'Treinamento',
          title: [training.code, training.title].where((v) => v.trim().isNotEmpty).join(' • '),
          subtitle: [companyName, workerName].where((v) => v.isNotEmpty).join(' • '),
          icon: Icons.school_outlined,
          color: const Color(0xFF8356B8),
          searchText: '${training.toMap().values.join(' ')} $companyName $workerName',
          page: () => const TrainingsScreen(),
        ),
      );
    }

    for (final row in inspections) {
      final companyId = '${row['company_id'] ?? ''}'.trim();
      final companyName = '${row['company_name'] ?? 'Empresa'}'.trim();
      final number = '${row['report_number'] ?? ''}'.trim();
      final status = '${row['status'] ?? ''}'.trim();
      found.add(
        _SearchEntry(
          kind: 'Vistoria',
          title: number.isEmpty ? companyName : '$number • $companyName',
          subtitle: [status, row['worksite_name'], row['sector_name'], row['area']]
              .map((v) => '$v'.trim())
              .where((v) => v.isNotEmpty)
              .join(' • '),
          icon: Icons.fact_check_outlined,
          color: AuditarBrand.info,
          searchText: row.values.join(' '),
          page: () => HistoryScreen(companyId: companyId.isEmpty ? null : companyId),
        ),
      );
    }

    for (final row in actions) {
      final companyId = '${row['company_id'] ?? row['inspection_company_id'] ?? ''}'.trim();
      final companyName = '${row['company_name'] ?? ''}'.trim();
      final nc = '${row['nc_code'] ?? ''}'.trim();
      final description = '${row['corrective_action'] ?? row['description'] ?? 'Plano de ação'}'.trim();
      found.add(
        _SearchEntry(
          kind: 'Plano de ação / NC',
          title: nc.isEmpty ? description : '$nc • $description',
          subtitle: companyName,
          icon: Icons.assignment_turned_in_outlined,
          color: AuditarBrand.warning,
          searchText: row.values.join(' '),
          page: () => ActionPlanScreen(companyId: companyId.isEmpty ? null : companyId),
        ),
      );
    }

    if (!mounted) return;
    setState(() {
      entries
        ..clear()
        ..addAll(found);
      loading = false;
    });
  }

  List<_SearchEntry> get visible {
    final q = controller.text.trim().toLowerCase();
    if (q.isEmpty) return entries.take(25).toList(growable: false);
    return entries
        .where((entry) => '${entry.kind} ${entry.title} ${entry.subtitle} ${entry.searchText}'.toLowerCase().contains(q))
        .take(80)
        .toList(growable: false);
  }

  Future<void> _open(_SearchEntry entry) async {
    await Navigator.of(context).push(MaterialPageRoute(builder: (_) => entry.page()));
  }

  @override
  Widget build(BuildContext context) {
    final results = visible;
    return Scaffold(
      appBar: AppBar(title: const Text('Busca geral')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 10),
            child: TextField(
              controller: controller,
              autofocus: true,
              decoration: InputDecoration(
                hintText: 'Empresa, trabalhador, vistoria, PGR, treinamento, NC...',
                prefixIcon: const Icon(Icons.search_rounded),
                suffixIcon: controller.text.isEmpty
                    ? null
                    : IconButton(onPressed: controller.clear, icon: const Icon(Icons.close_rounded)),
                border: const OutlineInputBorder(),
              ),
            ),
          ),
          if (loading)
            const Expanded(child: Center(child: CircularProgressIndicator()))
          else if (results.isEmpty)
            const Expanded(child: Center(child: Text('Nenhum resultado encontrado.')))
          else
            Expanded(
              child: ListView.separated(
                padding: const EdgeInsets.fromLTRB(16, 4, 16, 20),
                itemCount: results.length,
                separatorBuilder: (_, __) => const SizedBox(height: 7),
                itemBuilder: (context, index) {
                  final entry = results[index];
                  return Card(
                    margin: EdgeInsets.zero,
                    child: ListTile(
                      leading: Container(
                        width: 42,
                        height: 42,
                        decoration: BoxDecoration(
                          color: entry.color.withValues(alpha: .09),
                          borderRadius: BorderRadius.circular(11),
                        ),
                        child: Icon(entry.icon, color: entry.color),
                      ),
                      title: Text(entry.title, style: const TextStyle(fontWeight: FontWeight.w800)),
                      subtitle: Text(
                        [entry.kind, entry.subtitle].where((v) => v.isNotEmpty).join(' • '),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      trailing: const Icon(Icons.chevron_right_rounded),
                      onTap: () => _open(entry),
                    ),
                  );
                },
              ),
            ),
        ],
      ),
    );
  }
}

class _SearchEntry {
  final String kind;
  final String title;
  final String subtitle;
  final IconData icon;
  final Color color;
  final String searchText;
  final Widget Function() page;

  const _SearchEntry({
    required this.kind,
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.color,
    required this.searchText,
    required this.page,
  });
}
'''
    (app / 'lib' / 'screens' / 'global_search_screen.dart').write_text(search_screen, encoding='utf-8')

    p = app / 'lib' / 'screens' / 'home_screen.dart'
    text = p.read_text(encoding='utf-8')
    text = replace_once(
        text,
        "import 'history_screen.dart';\n",
        "import 'history_screen.dart';\nimport 'global_search_screen.dart';\nimport 'reports_center_screen.dart';\n",
        'imports da Central de Trabalho',
    )
    text = replace_once(
        text,
        "  final GlobalKey _modulesKey = GlobalKey();\n\n  Map<String, int> summary = {};",
        "  final GlobalKey _modulesKey = GlobalKey();\n  final ValueNotifier<String> _homeSyncStatus = ValueNotifier<String>('Sincronização automática ativa');\n\n  Map<String, int> summary = {};",
        'estado de sincronização',
    )
    text = replace_once(
        text,
        "  int companyCount = 0;\n  Map<String, Object?>? activeInspection;",
        "  int companyCount = 0;\n  int finalizedInspections = 0;\n  Map<String, Object?>? activeInspection;",
        'contador de relatórios',
    )
    text = replace_once(
        text,
        "    _deviceSyncSubscription = DeviceSyncService.events.listen((result) {\n      if (mounted && result.received > 0) {\n        unawaited(_refresh(showLoading: false));\n      }\n    });",
        "    _deviceSyncSubscription = DeviceSyncService.events.listen((result) {\n      if (!mounted) return;\n      _homeSyncStatus.value = result.received > 0\n          ? 'Sincronizado • ${result.received} recebido(s)'\n          : 'PC e celular sincronizados';\n      if (result.received > 0) {\n        unawaited(_refresh(showLoading: false));\n      }\n    });",
        'status de sincronização',
    )
    text = replace_once(
        text,
        "    _mobileScrollController.dispose();\n    super.dispose();",
        "    _mobileScrollController.dispose();\n    _homeSyncStatus.dispose();\n    super.dispose();",
        'dispose sync status',
    )
    text = replace_once(
        text,
        "      Map<String, Object?>? inProgress;\n      for (final row in history) {",
        "      Map<String, Object?>? inProgress;\n      var finalizedCount = 0;\n      for (final row in history) {\n        if ('${row['status'] ?? ''}'.trim() == 'Finalizada') {\n          finalizedCount++;\n        }",
        'contagem de finalizadas',
    )
    text = replace_once(
        text,
        "        companyCount = companies.length;\n        activeInspection = inProgress;",
        "        companyCount = companies.length;\n        finalizedInspections = finalizedCount;\n        activeInspection = inProgress;",
        'salvar contagem de relatórios',
    )
    old_actions = """        actions: [\n          IconButton(\n            tooltip: 'Atualizar dados',\n"""
    new_actions = """        actions: [\n          if (Platform.isWindows)\n            IconButton(\n              tooltip: 'Busca geral',\n              onPressed: () => _open(const GlobalSearchScreen()),\n              icon: const Icon(Icons.search_rounded),\n            ),\n          IconButton(\n            tooltip: 'Atualizar dados',\n"""
    text = replace_once(text, old_actions, new_actions, 'busca geral no AppBar')

    old_desktop = """              children: [\n                _workspaceHeader(desktop: true),\n                const SizedBox(height: 16),\n                _overviewPanel(desktop: true),\n                const SizedBox(height: 12),\n                _continueInspectionCard(),\n                const SizedBox(height: 22),\n                _sectionHeader(\n                  'Ações principais',\n                  'Escolha a empresa, entre em campo ou acompanhe as pendências gerais',\n                ),\n                const SizedBox(height: 10),\n                _moduleWrap(\n                  _modules.take(4).toList(),\n                  minWidth: 190,\n                  maxColumns: 4,\n                ),\n                const SizedBox(height: 22),\n                _routinePanel(),\n                const SizedBox(height: 22),\n                _sectionHeader(\n                  'Gestão completa',\n                  'Cadastros, controles, CIPA, checklists e indicadores',\n                ),\n                const SizedBox(height: 10),\n                _moduleWrap(\n                  _modules.skip(4).toList(),\n                  minWidth: 205,\n                  maxColumns: 3,\n                ),\n                const SizedBox(height: 12),\n                _companyResourcesCard(),\n                const SizedBox(height: 20),\n                const Center(\n                  child: Text(\n                    'Auditar SST para Windows • versão 3.36.1',\n                    style: TextStyle(fontSize: 11, color: Colors.black45),\n                  ),\n                ),\n              ],\n"""
    new_desktop = """              children: [\n                _workspaceHeader(desktop: true),\n                const SizedBox(height: 12),\n                _desktopSearchBar(),\n                const SizedBox(height: 14),\n                _desktopWorkCenter(),\n                const SizedBox(height: 16),\n                _overviewPanel(desktop: true),\n                const SizedBox(height: 20),\n                _sectionHeader(\n                  'Atalhos de gestão',\n                  'Os recursos mais usados no PC, sem poluir a tela principal',\n                ),\n                const SizedBox(height: 10),\n                _moduleWrap(\n                  _modules\n                      .where((module) => const {\n                            'Empresas',\n                            'Vistorias',\n                            'Não conformidades',\n                            'Planos de ação',\n                            'Treinamentos',\n                            'Indicadores',\n                          }.contains(module.title))\n                      .toList(),\n                  minWidth: 205,\n                  maxColumns: 3,\n                ),\n                const SizedBox(height: 20),\n                _routinePanel(),\n                const SizedBox(height: 12),\n                _companyResourcesCard(),\n                const SizedBox(height: 20),\n                const Center(\n                  child: Text(\n                    'Auditar SST para Windows • versão 3.37.0',\n                    style: TextStyle(fontSize: 11, color: Colors.black45),\n                  ),\n                ),\n              ],\n"""
    text = replace_once(text, old_desktop, new_desktop, 'novo corpo desktop')

    marker = "\n\n  Widget _workspaceHeader({required bool desktop}) {"
    if marker not in text:
        raise RuntimeError('Marcador para inserir Central de Trabalho não encontrado')
    methods = r'''

  Widget _desktopSearchBar() {
    return Card(
      margin: EdgeInsets.zero,
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => _open(const GlobalSearchScreen()),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
          child: Row(
            children: [
              const Icon(Icons.search_rounded, color: AuditarBrand.navy),
              const SizedBox(width: 10),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Busca geral', style: TextStyle(fontWeight: FontWeight.w900, color: AuditarBrand.navy)),
                    SizedBox(height: 2),
                    Text(
                      'Empresa, trabalhador, vistoria, PGR, treinamento, NC...',
                      style: TextStyle(fontSize: 11.5, color: AuditarBrand.neutral),
                    ),
                  ],
                ),
              ),
              ValueListenableBuilder<String>(
                valueListenable: _homeSyncStatus,
                builder: (context, value, _) => Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
                  decoration: BoxDecoration(
                    color: AuditarBrand.greenSoft,
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.sync_rounded, size: 15, color: AuditarBrand.greenDark),
                      const SizedBox(width: 5),
                      Text(
                        value,
                        style: const TextStyle(fontSize: 10.5, fontWeight: FontWeight.w800, color: AuditarBrand.greenDark),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 6),
              const Icon(Icons.chevron_right_rounded),
            ],
          ),
        ),
      ),
    );
  }

  Widget _desktopWorkCenter() {
    final overdue = summary['ncOverdue'] ?? 0;
    final trainingAttention = (routineSummary['trainingsDue'] ?? 0) +
        (routineSummary['missingRequiredTrainings'] ?? 0);
    final agenda = routineSummary['agendaToday'] ?? 0;
    final hasDraft = activeInspection != null;

    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.space_dashboard_outlined, color: AuditarBrand.navy),
                SizedBox(width: 9),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Central de trabalho',
                        style: TextStyle(color: AuditarBrand.navy, fontSize: 19, fontWeight: FontWeight.w900),
                      ),
                      SizedBox(height: 2),
                      Text(
                        'O que precisa da sua atenção agora',
                        style: TextStyle(color: AuditarBrand.neutral, fontSize: 12),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 13),
            ResponsiveWrap(
              minItemWidth: 175,
              maxColumns: 3,
              spacing: 9,
              runSpacing: 9,
              children: [
                _workTile(
                  title: hasDraft ? 'Continuar vistoria' : 'Nova vistoria',
                  value: hasDraft ? 'EM ANDAMENTO' : 'PRONTO PARA INICIAR',
                  icon: hasDraft ? Icons.play_circle_outline_rounded : Icons.add_task_rounded,
                  color: hasDraft ? AuditarBrand.warning : AuditarBrand.greenDark,
                  onTap: () => _open(
                    hasDraft ? const HistoryScreen(resumeLatestDraft: true) : const NewInspectionScreen(),
                  ),
                ),
                _workTile(
                  title: 'Ações vencidas',
                  value: '$overdue',
                  icon: Icons.event_busy_outlined,
                  color: overdue > 0 ? AuditarBrand.danger : AuditarBrand.greenDark,
                  onTap: () => _open(const ActionPlanScreen()),
                ),
                _workTile(
                  title: 'Treinamentos',
                  value: trainingAttention == 0 ? 'EM DIA' : '$trainingAttention requer atenção',
                  icon: Icons.school_outlined,
                  color: trainingAttention > 0 ? AuditarBrand.warning : AuditarBrand.greenDark,
                  onTap: () => _open(const TrainingsScreen()),
                ),
                _workTile(
                  title: 'Agenda de hoje',
                  value: agenda == 0 ? 'SEM ATIVIDADES' : '$agenda atividade(s)',
                  icon: Icons.today_outlined,
                  color: agenda > 0 ? AuditarBrand.info : AuditarBrand.greenDark,
                  onTap: () => _open(const RoutineHubScreen()),
                ),
                _workTile(
                  title: 'Relatórios',
                  value: '$finalizedInspections finalizado(s)',
                  icon: Icons.folder_copy_outlined,
                  color: AuditarBrand.info,
                  onTap: () => _open(const ReportsCenterScreen()),
                ),
                _workTile(
                  title: 'Empresas',
                  value: '$companyCount na carteira',
                  icon: Icons.business_outlined,
                  color: AuditarBrand.navy,
                  onTap: () => _open(const CompaniesScreen()),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _workTile({
    required String title,
    required String value,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Material(
      color: color.withValues(alpha: .055),
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Container(
          constraints: const BoxConstraints(minHeight: 92),
          padding: const EdgeInsets.all(13),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: color.withValues(alpha: .14)),
          ),
          child: Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: color.withValues(alpha: .10),
                  borderRadius: BorderRadius.circular(11),
                ),
                child: Icon(icon, color: color, size: 22),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(title, style: const TextStyle(fontWeight: FontWeight.w900, color: AuditarBrand.navy)),
                    const SizedBox(height: 4),
                    Text(
                      value,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w800),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right_rounded, size: 20, color: AuditarBrand.neutral),
            ],
          ),
        ),
      ),
    );
  }
'''
    text = text.replace(marker, methods + marker, 1)
    text = text.replace('Auditar SST • versão 3.36.1', 'Auditar SST • versão 3.37.0')
    p.write_text(text, encoding='utf-8')

    checks = {
        'versão': 'version: 3.37.0+157' in pub.read_text(encoding='utf-8'),
        'central trabalho': 'Central de trabalho' in p.read_text(encoding='utf-8'),
        'busca geral': (app / 'lib' / 'screens' / 'global_search_screen.dart').exists(),
        'central relatórios': (app / 'lib' / 'screens' / 'reports_center_screen.dart').exists(),
        'sync v2': "'syncProtocol': 2" in (app / 'lib' / 'services' / 'device_sync_service.dart').read_text(encoding='utf-8'),
        '44 checklists': (app / 'lib' / 'ready_checklists.dart').read_text(encoding='utf-8').count('  ReadyChecklistDefinition(') == 44,
        'assinatura mobile': 'Assinar em tela cheia' in (app / 'lib' / 'screens' / 'signature_screen.dart').read_text(encoding='utf-8'),
        'campo rápido preservado': 'FieldQuickScreen' in p.read_text(encoding='utf-8'),
        'sem periódicos na nova central': 'periódico' not in reports_screen.lower() and 'periódico' not in search_screen.lower(),
    }
    missing = [name for name, ok in checks.items() if not ok]
    if missing:
        raise RuntimeError('Validações v3.37.0 falharam: ' + ', '.join(missing))

    print(f'Fonte v3.37.0 Central de Trabalho montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

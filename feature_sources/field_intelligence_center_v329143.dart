import 'dart:io';

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../brand.dart';
import '../database.dart';
import '../models.dart';
import '../services/auth_service.dart';
import '../services/device_sync_service.dart';
import '../services/media_sync_service.dart';
import 'action_plan_screen.dart';
import 'companies_screen.dart';
import 'evidence_backup_screen.dart';
import 'field_quick_screen.dart';
import 'history_screen.dart';
import 'new_inspection_screen.dart';
import 'non_conformities_screen.dart';
import 'routine_hub_screen.dart';
import 'trainings_screen.dart';
import 'workers_screen.dart';

class FieldIntelligenceCenterScreen extends StatefulWidget {
  const FieldIntelligenceCenterScreen({super.key});

  @override
  State<FieldIntelligenceCenterScreen> createState() =>
      _FieldIntelligenceCenterScreenState();
}

class _FieldIntelligenceCenterScreenState
    extends State<FieldIntelligenceCenterScreen>
    with SingleTickerProviderStateMixin {
  static const _favKey = 'field_center_favorites_v1';
  late final TabController tabs;
  final search = TextEditingController();

  bool loading = true;
  String error = '';
  String companyId = '';
  List<Company> companies = const [];
  List<Worker> workers = const [];
  List<Map<String, Object?>> inspections = const [];
  List<Map<String, Object?>> ncs = const [];
  List<Map<String, Object?>> actions = const [];
  List<TrainingControl> trainings = const [];
  List<SstRecord> dds = const [];
  Map<String, int> trainingSummary = const {};
  int structuredPending = 0;
  int mediaPending = 0;
  String lastSync = '';
  String lastSyncStatus = '';
  String lastSyncError = '';
  String mediaSyncError = '';
  Set<String> favorites = {
    'inspection',
    'quick',
    'history',
    'actions',
    'training',
    'evidence',
  };

  String? get selectedCompanyId => companyId.isEmpty ? null : companyId;

  Company? get selectedCompany {
    for (final company in companies) {
      if (company.id == companyId) return company;
    }
    return null;
  }

  @override
  void initState() {
    super.initState();
    tabs = TabController(length: AuthService.isAdmin ? 4 : 3, vsync: this);
    search.addListener(() {
      if (mounted) setState(() {});
    });
    load();
  }

  @override
  void dispose() {
    tabs.dispose();
    search.dispose();
    super.dispose();
  }

  Future<void> load() async {
    if (mounted) setState(() { loading = true; error = ''; });
    try {
      final db = AppDatabase.instance;
      final fav = await db.getSetting(_favKey);
      final loadedCompanies = await db.getCompanies();
      final cid = selectedCompanyId;
      final loadedWorkers = await db.getWorkers(companyId: cid);
      final loadedInspections = await db.getInspectionHistory(companyId: cid);
      final loadedNcs = await db.getNonConformityRows(companyId: cid);
      final loadedActions = await db.getPendingActions(
        companyId: cid,
        includeCompleted: true,
      );
      final loadedTrainings = await db.getTrainingControls(companyId: cid);
      final loadedDds = await db.getSstRecords(type: 'DDS', companyId: cid);
      final loadedTrainingSummary = await db.getTrainingSummary(companyId: cid);
      int pendingData = 0;
      int pendingMedia = 0;
      try { pendingData = await DeviceSyncService.pendingChangesCount(); } catch (_) {}
      try { pendingMedia = await MediaSyncService.pendingCount(); } catch (_) {}
      final sync = await db.getSetting('last_device_sync_success');
      final syncStatus = await db.getSetting('last_device_sync_status');
      final syncError = await db.getSetting('last_device_sync_error');
      final mediaError = await db.getSetting('media_sync_last_error');
      if (!mounted) return;
      setState(() {
        companies = loadedCompanies;
        workers = loadedWorkers;
        inspections = loadedInspections;
        ncs = loadedNcs;
        actions = loadedActions;
        trainings = loadedTrainings;
        dds = loadedDds;
        trainingSummary = loadedTrainingSummary;
        structuredPending = pendingData;
        mediaPending = pendingMedia;
        lastSync = sync.trim();
        lastSyncStatus = syncStatus.trim();
        lastSyncError = syncError.trim();
        mediaSyncError = mediaError.trim();
        if (fav.trim().isNotEmpty) {
          favorites = fav.split(',').map((e) => e.trim()).where((e) => e.isNotEmpty).toSet();
        }
        loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() { loading = false; error = '$e'; });
    }
  }

  DateTime? dateOf(Object? raw) =>
      raw == null ? null : DateTime.tryParse('$raw');

  int get openNc => ncs.where((row) =>
      !'${row['status'] ?? ''}'.toLowerCase().contains('conclu')).length;

  int get overdueActions {
    final now = DateTime.now();
    return actions.where((row) {
      if ('${row['status'] ?? ''}'.toLowerCase().contains('conclu')) return false;
      final due = dateOf(row['due_date']);
      return due != null && due.isBefore(now);
    }).length;
  }

  int get recentInspections {
    final start = DateTime.now().subtract(const Duration(days: 30));
    return inspections.where((row) {
      final d = dateOf(row['date']);
      return d != null && d.isAfter(start);
    }).length;
  }

  int get recentDds {
    final start = DateTime.now().subtract(const Duration(days: 30));
    return dds.where((record) => record.date.isAfter(start)).length;
  }

  Future<void> openPage(Widget page) async {
    await Navigator.of(context).push(MaterialPageRoute(builder: (_) => page));
    await load();
  }

  List<_Shortcut> get shortcuts => [
    _Shortcut('inspection', 'Nova vistoria', Icons.fact_check_outlined,
      () => NewInspectionScreen(initialCompany: selectedCompany)),
    _Shortcut('quick', 'Vistoria rápida', Icons.flash_on_rounded,
      () => const FieldQuickScreen()),
    _Shortcut('history', 'Histórico', Icons.history_rounded,
      () => HistoryScreen(companyId: selectedCompanyId)),
    _Shortcut('actions', 'Plano de ação', Icons.assignment_turned_in_outlined,
      () => ActionPlanScreen(companyId: selectedCompanyId)),
    _Shortcut('nc', 'Não conformidades', Icons.warning_amber_rounded,
      () => NonConformitiesScreen(companyId: selectedCompanyId)),
    _Shortcut('training', 'Treinamentos', Icons.school_outlined,
      () => TrainingsScreen(companyId: selectedCompanyId)),
    _Shortcut('workers', 'Trabalhadores', Icons.groups_rounded,
      () => WorkersScreen(companyId: selectedCompanyId)),
    _Shortcut('routine', 'Rotina SST', Icons.dashboard_customize_outlined,
      () => RoutineHubScreen(companyId: selectedCompanyId)),
    _Shortcut('companies', 'Empresas', Icons.business_outlined,
      () => const CompaniesScreen()),
    _Shortcut(
      'evidence',
      'Evidências',
      Icons.photo_library_outlined,
      () => EvidenceBackupScreen(company: selectedCompany!),
      enabled: selectedCompany != null,
    ),
  ];

  Future<void> editFavorites() async {
    final draft = {...favorites};
    final result = await showModalBottomSheet<Set<String>>(
      context: context,
      isScrollControlled: true,
      builder: (context) => StatefulBuilder(
        builder: (context, setLocal) => SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(Icons.push_pin_outlined),
                  title: Text('Atalhos favoritos',
                    style: TextStyle(fontWeight: FontWeight.w900)),
                  subtitle: Text('Escolha o que aparece primeiro na sua central.'),
                ),
                Flexible(
                  child: ListView(
                    shrinkWrap: true,
                    children: shortcuts.map((item) => CheckboxListTile(
                      value: draft.contains(item.id),
                      title: Text(item.label),
                      secondary: Icon(item.icon),
                      onChanged: (value) => setLocal(() {
                        value == true ? draft.add(item.id) : draft.remove(item.id);
                      }),
                    )).toList(),
                  ),
                ),
                Row(children: [
                  Expanded(child: OutlinedButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text('Cancelar'),
                  )),
                  const SizedBox(width: 10),
                  Expanded(child: FilledButton(
                    onPressed: () => Navigator.pop(context, draft),
                    child: const Text('Salvar'),
                  )),
                ]),
              ],
            ),
          ),
        ),
      ),
    );
    if (result == null) return;
    final sorted = result.toList()..sort();
    await AppDatabase.instance.setSetting(_favKey, sorted.join(','));
    if (mounted) setState(() => favorites = result);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AuditarBrand.background,
      appBar: AppBar(
        title: const Text('Central Inteligente de Campo'),
        actions: [
          IconButton(
            tooltip: 'Personalizar atalhos',
            onPressed: editFavorites,
            icon: const Icon(Icons.push_pin_outlined),
          ),
          IconButton(
            tooltip: 'Atualizar',
            onPressed: load,
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
        bottom: TabBar(
          controller: tabs,
          isScrollable: true,
          tabs: [
            const Tab(icon: Icon(Icons.space_dashboard_outlined), text: 'Hoje'),
            const Tab(icon: Icon(Icons.search_rounded), text: 'Busca'),
            const Tab(icon: Icon(Icons.photo_library_outlined), text: 'Evidências'),
            if (AuthService.isAdmin)
              const Tab(icon: Icon(Icons.monitor_heart_outlined), text: 'Diagnóstico'),
          ],
        ),
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : error.isNotEmpty
              ? Center(child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text('Falha ao carregar a central: $error'),
                ))
              : Column(children: [
                  companyFilter(),
                  Expanded(child: TabBarView(
                    controller: tabs,
                    children: [
                      todayTab(),
                      searchTab(),
                      evidenceTab(),
                      if (AuthService.isAdmin) diagnosticsTab(),
                    ],
                  )),
                ]),
    );
  }

  Widget companyFilter() => Material(
    color: Colors.white,
    child: Padding(
      padding: const EdgeInsets.all(10),
      child: DropdownButtonFormField<String>(
        value: companyId,
        isExpanded: true,
        decoration: const InputDecoration(
          labelText: 'Empresa acompanhada',
          prefixIcon: Icon(Icons.business_outlined),
          isDense: true,
        ),
        items: [
          const DropdownMenuItem(
            value: '',
            child: Text('Todas as empresas autorizadas'),
          ),
          ...companies.map((company) => DropdownMenuItem(
            value: company.id,
            child: Text(company.name, overflow: TextOverflow.ellipsis),
          )),
        ],
        onChanged: (value) async {
          companyId = value ?? '';
          await load();
        },
      ),
    ),
  );

  Widget todayTab() {
    final favoriteShortcuts = shortcuts
        .where((item) => favorites.contains(item.id))
        .toList();
    return RefreshIndicator(
      onRefresh: load,
      child: ListView(
        padding: const EdgeInsets.all(14),
        children: [
          title(
            'Resumo operacional',
            selectedCompany == null
                ? 'Visão consolidada do trabalho de campo.'
                : 'Visão rápida de ${selectedCompany!.name}.',
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              metric('Vistorias • 30 dias', recentInspections, Icons.fact_check_outlined),
              metric('NCs abertas', openNc, Icons.warning_amber_rounded),
              metric('Ações vencidas', overdueActions, Icons.event_busy_outlined),
              metric('Treinamentos vencidos', trainingSummary['expired'] ?? 0, Icons.school_outlined),
              metric('DDS • 30 dias', recentDds, Icons.record_voice_over_outlined),
              metric('Trabalhadores', workers.length, Icons.groups_rounded),
            ],
          ),
          const SizedBox(height: 16),
          Card(
            child: Column(children: [
              const ListTile(
                leading: Icon(Icons.priority_high_rounded),
                title: Text('O que precisa de atenção',
                  style: TextStyle(fontWeight: FontWeight.w900)),
              ),
              if (overdueActions > 0)
                quickRow('$overdueActions ação(ões) vencida(s)',
                  () => openPage(ActionPlanScreen(companyId: selectedCompanyId))),
              if ((trainingSummary['expired'] ?? 0) > 0)
                quickRow('${trainingSummary['expired']} treinamento(s) vencido(s)',
                  () => openPage(TrainingsScreen(companyId: selectedCompanyId))),
              if (structuredPending + mediaPending > 0)
                quickRow('${structuredPending + mediaPending} item(ns) aguardando envio',
                  AuthService.isAdmin ? () => tabs.animateTo(3) : showQueue),
              if (overdueActions == 0 &&
                  (trainingSummary['expired'] ?? 0) == 0 &&
                  structuredPending + mediaPending == 0)
                const ListTile(
                  leading: Icon(Icons.verified_outlined,
                    color: AuditarBrand.greenDark),
                  title: Text('Sem prioridade imediata detectada.'),
                ),
            ]),
          ),
          const SizedBox(height: 16),
          Row(children: [
            const Expanded(child: Text('Atalhos favoritos',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900))),
            TextButton.icon(
              onPressed: editFavorites,
              icon: const Icon(Icons.tune_rounded),
              label: const Text('Editar'),
            ),
          ]),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: favoriteShortcuts.map((item) => SizedBox(
              width: MediaQuery.sizeOf(context).width < 600 ? 160 : 190,
              child: Card(
                child: ListTile(
                  enabled: item.enabled,
                  onTap: item.enabled ? () => openPage(item.page()) : null,
                  leading: Icon(item.icon),
                  title: Text(item.label,
                    style: const TextStyle(fontSize: 12,
                      fontWeight: FontWeight.w800)),
                ),
              ),
            )).toList(),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Text(
                'Atuação registrada neste recorte: $recentInspections vistoria(s) nos últimos 30 dias, '
                '$recentDds DDS e ${actions.where((row) => '${row['status'] ?? ''}'.toLowerCase().contains('conclu')).length} '
                'ação(ões) concluída(s).',
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget metric(String label, int value, IconData icon) => SizedBox(
    width: MediaQuery.sizeOf(context).width < 600 ? 160 : 190,
    child: Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(children: [
          Icon(icon, color: AuditarBrand.navy),
          const SizedBox(width: 8),
          Expanded(child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('$value', style: const TextStyle(
                fontSize: 20, fontWeight: FontWeight.w900)),
              Text(label, style: const TextStyle(
                fontSize: 10.5, color: AuditarBrand.neutral)),
            ],
          )),
        ]),
      ),
    ),
  );

  Widget quickRow(String label, VoidCallback onTap) => ListTile(
    leading: const Icon(Icons.chevron_right_rounded),
    title: Text(label),
    trailing: TextButton(onPressed: onTap, child: const Text('Abrir')),
  );

  Widget title(String title, String subtitle) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(title, style: const TextStyle(
        fontSize: 18, fontWeight: FontWeight.w900)),
      const SizedBox(height: 3),
      Text(subtitle, style: const TextStyle(color: AuditarBrand.neutral)),
    ],
  );

  List<_Hit> get hits {
    final q = search.text.trim().toLowerCase();
    if (q.length < 2) return const [];
    bool match(String value) => value.toLowerCase().contains(q);
    final list = <_Hit>[];
    final workerMap = {for (final w in workers) w.id: w};
    for (final c in companies) {
      if (match(c.name) || match(c.cnpj ?? '') || match(c.city ?? '')) {
        list.add(_Hit('Empresa', c.name, c.cnpj ?? '', Icons.business_outlined,
          () => WorkersScreen(companyId: c.id)));
      }
    }
    for (final w in workers) {
      if (match(w.name) || match(w.role) || match(w.cpf)) {
        list.add(_Hit('Trabalhador', w.name, w.role, Icons.person_search_outlined,
          () => WorkersScreen(companyId: w.companyId)));
      }
    }
    for (final row in inspections) {
      final company = '${row['company_name'] ?? ''}';
      final area = '${row['area'] ?? ''}';
      final report = '${row['report_number'] ?? ''}';
      if (match(company) || match(area) || match(report)) {
        list.add(_Hit('Vistoria',
          report.isEmpty ? company : report,
          '$company • $area',
          Icons.fact_check_outlined,
          () => HistoryScreen(companyId: selectedCompanyId)));
      }
    }
    for (final row in ncs) {
      final description = '${row['description'] ?? ''}';
      final company = '${row['company_name'] ?? ''}';
      if (match(description) || match(company)) {
        list.add(_Hit('Não conformidade', description, company,
          Icons.warning_amber_rounded,
          () => NonConformitiesScreen(companyId: selectedCompanyId)));
      }
    }
    for (final training in trainings) {
      final worker = workerMap[training.workerId];
      if (match(training.title) ||
          match(training.code) ||
          match(worker?.name ?? '')) {
        list.add(_Hit('Treinamento', training.title,
          worker?.name ?? training.code, Icons.school_outlined,
          () => TrainingsScreen(companyId: worker?.companyId)));
      }
    }
    for (final record in dds) {
      if (match(record.title) || match('${record.payload}')) {
        list.add(_Hit('DDS', record.title,
          DateFormat('dd/MM/yyyy').format(record.date),
          Icons.record_voice_over_outlined,
          () => RoutineHubScreen(companyId: record.companyId)));
      }
    }
    return list.take(40).toList();
  }

  Widget searchTab() {
    final results = hits;
    return ListView(
      padding: const EdgeInsets.all(14),
      children: [
        title('Busca global',
          'Empresa, trabalhador, vistoria, NC, treinamento ou DDS.'),
        const SizedBox(height: 10),
        TextField(
          controller: search,
          decoration: InputDecoration(
            hintText: 'Digite pelo menos 2 caracteres',
            prefixIcon: const Icon(Icons.search_rounded),
            suffixIcon: search.text.isEmpty ? null : IconButton(
              onPressed: search.clear,
              icon: const Icon(Icons.close_rounded),
            ),
          ),
        ),
        const SizedBox(height: 10),
        if (search.text.trim().length < 2)
          const Card(child: Padding(
            padding: EdgeInsets.all(16),
            child: Text('Ex.: nome do trabalhador, NR-35, empresa, setor ou relatório.'),
          ))
        else if (results.isEmpty)
          const Card(child: Padding(
            padding: EdgeInsets.all(16),
            child: Text('Nenhum resultado encontrado neste aparelho.'),
          ))
        else
          Card(child: Column(children: results.map((hit) => ListTile(
            leading: Icon(hit.icon, color: AuditarBrand.navy),
            title: Text(hit.title,
              maxLines: 2, overflow: TextOverflow.ellipsis),
            subtitle: Text('${hit.category} • ${hit.subtitle}',
              maxLines: 2, overflow: TextOverflow.ellipsis),
            trailing: const Icon(Icons.chevron_right_rounded),
            onTap: () => openPage(hit.page()),
          )).toList())),
      ],
    );
  }

  Widget evidenceTab() => ListView(
    padding: const EdgeInsets.all(14),
    children: [
      title('Central de evidências',
        'Use os registros já existentes sem duplicar fotos.'),
      const SizedBox(height: 10),
      if (selectedCompany == null)
        const Card(child: Padding(
          padding: EdgeInsets.all(16),
          child: Text('Selecione uma empresa acima para abrir sua biblioteca protegida de evidências.'),
        ))
      else ...[
        FilledButton.tonalIcon(
          onPressed: () => openPage(EvidenceBackupScreen(company: selectedCompany!)),
          icon: const Icon(Icons.photo_library_outlined),
          label: const Text('Abrir evidências da empresa'),
        ),
        const SizedBox(height: 10),
        const Card(child: Padding(
          padding: EdgeInsets.all(14),
          child: Text(
            'O comparativo Antes × Depois continua dentro do Plano de ação. '
            'As fotos originais e as fotos de correção permanecem vinculadas ao mesmo registro.',
          ),
        )),
        const SizedBox(height: 8),
        FilledButton.tonalIcon(
          onPressed: () => openPage(ActionPlanScreen(companyId: selectedCompanyId)),
          icon: const Icon(Icons.compare_outlined),
          label: const Text('Abrir Antes × Depois das correções'),
        ),
      ],
    ],
  );

  Widget diagnosticsTab() {
    final version = Platform.isWindows ? '3.30.62' : '3.29.143';
    String syncDate = lastSync;
    final parsed = DateTime.tryParse(lastSync);
    if (parsed != null) {
      syncDate = DateFormat('dd/MM/yyyy HH:mm').format(parsed.toLocal());
    }
    return ListView(
      padding: const EdgeInsets.all(14),
      children: [
        title('Diagnóstico técnico ADM',
          'Somente leitura. Não altera fila, banco ou sincronização.'),
        const SizedBox(height: 10),
        Card(child: Column(children: [
          diag('Versão', version, Icons.info_outline_rounded),
          const Divider(height: 1),
          diag('Dados aguardando envio', '$structuredPending', Icons.cloud_sync_outlined),
          const Divider(height: 1),
          diag('Fotos/assinaturas aguardando envio', '$mediaPending', Icons.photo_library_outlined),
          const Divider(height: 1),
          diag('Última sincronização', syncDate.isEmpty ? 'Sem registro' : syncDate, Icons.schedule_rounded),
          const Divider(height: 1),
          diag('Estado', lastSyncStatus.isEmpty ? 'Sem registro' : lastSyncStatus, Icons.sync_alt_rounded),
        ])),
        if (lastSyncError.isNotEmpty || mediaSyncError.isNotEmpty) ...[
          const SizedBox(height: 10),
          Card(child: Padding(
            padding: const EdgeInsets.all(14),
            child: Text([
              if (lastSyncError.isNotEmpty) 'Dados: $lastSyncError',
              if (mediaSyncError.isNotEmpty) 'Evidências: $mediaSyncError',
            ].join('\n\n')),
          )),
        ],
      ],
    );
  }

  Widget diag(String label, String value, IconData icon) => ListTile(
    leading: Icon(icon, color: AuditarBrand.navy),
    title: Text(label, style: const TextStyle(fontWeight: FontWeight.w800)),
    subtitle: Text(value),
  );

  Future<void> showQueue() async {
    if (!mounted) return;
    await showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Fila deste aparelho'),
        content: Text(
          'Dados aguardando envio: $structuredPending\n'
          'Fotos/assinaturas aguardando envio: $mediaPending\n\n'
          'O fluxo de sincronização existente não foi alterado.',
        ),
        actions: [
          FilledButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Fechar'),
          ),
        ],
      ),
    );
  }
}

class _Shortcut {
  final String id;
  final String label;
  final IconData icon;
  final Widget Function() page;
  final bool enabled;
  const _Shortcut(this.id, this.label, this.icon, this.page,
      {this.enabled = true});
}

class _Hit {
  final String category;
  final String title;
  final String subtitle;
  final IconData icon;
  final Widget Function() page;
  const _Hit(this.category, this.title, this.subtitle, this.icon, this.page);
}

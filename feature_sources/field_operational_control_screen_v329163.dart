import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../brand.dart';
import '../database.dart';
import '../models.dart';
import '../services/correction_recurrence_detector.dart';
import '../services/device_sync_service.dart';
import '../services/field_operational_priority_service.dart';
import '../services/media_sync_service.dart';
import 'action_plan_screen.dart';
import 'correction_evidence_center_screen.dart';
import 'new_inspection_screen.dart';
import 'non_conformities_screen.dart';
import 'trainings_screen.dart';

class FieldOperationalControlScreen extends StatefulWidget {
  const FieldOperationalControlScreen({
    super.key,
    this.initialCompanyId = '',
  });

  final String initialCompanyId;

  @override
  State<FieldOperationalControlScreen> createState() =>
      _FieldOperationalControlScreenState();
}

class _FieldOperationalControlScreenState
    extends State<FieldOperationalControlScreen> {
  bool loading = true;
  bool? online;
  String error = '';
  String companyId = '';
  String lastSync = '';
  String lastSyncStatus = '';
  String lastSyncError = '';
  String mediaSyncError = '';

  List<Company> companies = const [];
  List<Map<String, Object?>> ncs = const [];
  List<Map<String, Object?>> actions = const [];
  List<Map<String, Object?>> inspections = const [];
  Map<String, int> trainingSummary = const {};
  List<CorrectionRecurrenceGroup> recurrenceGroups = const [];

  int structuredPending = 0;
  int mediaPending = 0;
  int awaitingAfterEvidence = 0;
  int completeBeforeAfter = 0;

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
    companyId = widget.initialCompanyId;
    unawaited(_load());
  }

  Future<void> _probeNetwork() async {
    bool connected = false;
    try {
      final result = await InternetAddress.lookup('script.google.com')
          .timeout(const Duration(seconds: 3));
      connected = result.isNotEmpty && result.first.rawAddress.isNotEmpty;
    } catch (_) {
      connected = false;
    }
    if (mounted) setState(() => online = connected);
  }

  Future<void> _load() async {
    if (mounted) {
      setState(() {
        loading = true;
        error = '';
        online = null;
      });
    }
    try {
      final db = AppDatabase.instance;
      final loadedCompanies = await db.getCompanies();
      if (companyId.isNotEmpty &&
          !loadedCompanies.any((company) => company.id == companyId)) {
        companyId = '';
      }
      final cid = selectedCompanyId;
      final loadedNcs = await db.getNonConformityRows(companyId: cid);
      final loadedActions = await db.getPendingActions(
        companyId: cid,
        includeCompleted: true,
      );
      final loadedInspections = await db.getInspectionHistory(companyId: cid);
      final loadedTrainingSummary = await db.getTrainingSummary(companyId: cid);

      int pendingData = 0;
      int pendingMedia = 0;
      try {
        pendingData = await DeviceSyncService.pendingChangesCount();
      } catch (_) {}
      try {
        pendingMedia = await MediaSyncService.pendingCount();
      } catch (_) {}

      final sync = await db.getSetting('last_device_sync_success');
      final syncStatus = await db.getSetting('last_device_sync_status');
      final syncError = await db.getSetting('last_device_sync_error');
      final mediaError = await db.getSetting('media_sync_last_error');

      var afterPending = 0;
      var beforeAfter = 0;
      if (cid != null) {
        final actionsByNc = <String, List<Map<String, Object?>>>{};
        final actionsByAnswer = <String, List<Map<String, Object?>>>{};
        for (final action in loadedActions) {
          final ncId = _value(action, 'nc_id');
          final answerId = _value(action, 'answer_id');
          if (ncId.isNotEmpty) {
            (actionsByNc[ncId] ??= <Map<String, Object?>>[]).add(action);
          }
          if (answerId.isNotEmpty) {
            (actionsByAnswer[answerId] ??= <Map<String, Object?>>[]).add(action);
          }
        }

        for (final nc in loadedNcs) {
          final ncId = _value(nc, 'id');
          final answerId = _value(nc, 'answer_id');
          if (answerId.isEmpty) continue;

          var hasBefore = false;
          try {
            final photos = await db.getPhotosForAnswer(answerId);
            hasBefore = photos.any((photo) => photo.path.trim().isNotEmpty);
          } catch (_) {}
          if (!hasBefore) continue;

          final related = <Map<String, Object?>>[
            ...?actionsByNc[ncId],
            ...?actionsByAnswer[answerId],
          ];
          var hasAfter = false;
          for (final action in related) {
            final actionId = _value(action, 'id');
            if (actionId.isEmpty) continue;
            try {
              final photos = await db.getCompletionPhotos(actionId);
              if (photos.any((photo) => photo.path.trim().isNotEmpty)) {
                hasAfter = true;
                break;
              }
            } catch (_) {}
          }
          if (hasAfter) {
            beforeAfter++;
          } else {
            afterPending++;
          }
        }
      }

      if (!mounted) return;
      setState(() {
        companies = loadedCompanies;
        ncs = loadedNcs;
        actions = loadedActions;
        inspections = loadedInspections;
        trainingSummary = loadedTrainingSummary;
        recurrenceGroups = cid == null
            ? const []
            : CorrectionRecurrenceDetector.detect(loadedNcs);
        structuredPending = pendingData;
        mediaPending = pendingMedia;
        awaitingAfterEvidence = afterPending;
        completeBeforeAfter = beforeAfter;
        lastSync = sync.trim();
        lastSyncStatus = syncStatus.trim();
        lastSyncError = syncError.trim();
        mediaSyncError = mediaError.trim();
        loading = false;
      });
      unawaited(_probeNetwork());
    } catch (e) {
      if (!mounted) return;
      setState(() {
        loading = false;
        error = '$e';
      });
      unawaited(_probeNetwork());
    }
  }

  String _value(Map<String, Object?>? row, String key) =>
      row == null ? '' : '${row[key] ?? ''}'.trim();

  bool _isCompleted(Map<String, Object?> row) {
    final status = _value(row, 'status').toLowerCase();
    return status.contains('conclu') ||
        status.contains('resolvid') ||
        status.contains('finaliz');
  }

  int get openNc => ncs.where((row) => !_isCompleted(row)).length;

  int get highCriticalOpen => ncs.where((row) {
        if (_isCompleted(row)) return false;
        final priority = [
          _value(row, 'priority'),
          _value(row, 'classification'),
          _value(row, 'severity'),
        ].join(' ').toLowerCase();
        return priority.contains('alta') ||
            priority.contains('crit') ||
            priority.contains('crít');
      }).length;

  int get openActions => actions.where((row) => !_isCompleted(row)).length;

  int get overdueActions {
    final now = DateTime.now();
    return actions.where((row) {
      if (_isCompleted(row)) return false;
      final raw = _value(row, 'due_date');
      final due = DateTime.tryParse(raw);
      return due != null && due.isBefore(now);
    }).length;
  }

  int? get daysSinceLastInspection {
    DateTime? latest;
    for (final row in inspections) {
      final date = DateTime.tryParse(_value(row, 'date'));
      if (date != null && (latest == null || date.isAfter(latest))) {
        latest = date;
      }
    }
    return latest == null ? null : DateTime.now().difference(latest).inDays;
  }

  List<FieldVisitPriorityItem> get visitPriorities =>
      FieldOperationalPriorityService.build(
        highCriticalOpen: highCriticalOpen,
        overdueActions: overdueActions,
        recurrenceGroups: recurrenceGroups.length,
        expiredTrainings: trainingSummary['expired'] ?? 0,
        awaitingEvidence: awaitingAfterEvidence,
        openNonConformities: openNc,
        pendingSync: structuredPending + mediaPending,
        daysSinceLastInspection: daysSinceLastInspection,
      );

  Future<void> _open(Widget page) async {
    await Navigator.of(context).push(MaterialPageRoute(builder: (_) => page));
    await _load();
  }

  void _requireCompany() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Selecione uma empresa para abrir esta análise.'),
      ),
    );
  }

  void _openPriority(FieldVisitPriorityItem item) {
    switch (item.code) {
      case 'critical_nc':
      case 'open_nc':
        unawaited(_open(NonConformitiesScreen(companyId: selectedCompanyId)));
        break;
      case 'overdue_actions':
        unawaited(_open(ActionPlanScreen(companyId: selectedCompanyId)));
        break;
      case 'training':
        unawaited(_open(TrainingsScreen(companyId: selectedCompanyId)));
        break;
      case 'recurrence':
      case 'evidence':
        final company = selectedCompany;
        if (company == null) {
          _requireCompany();
        } else {
          unawaited(_open(CorrectionEvidenceCenterScreen(company: company)));
        }
        break;
      case 'inspection_due':
        unawaited(_open(NewInspectionScreen(initialCompany: selectedCompany)));
        break;
      case 'sync':
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Fila deste aparelho: $structuredPending dado(s) e '
              '$mediaPending evidência(s) aguardando envio.',
            ),
          ),
        );
        break;
    }
  }

  String get connectionLabel {
    if (online == null) return 'Conferindo conexão';
    return online! ? 'Online' : 'Offline';
  }

  String get lastInspectionLabel {
    final days = daysSinceLastInspection;
    if (days == null) return 'Sem vistoria localizada';
    return days == 0 ? 'Vistoria realizada hoje' : 'Última vistoria há $days dia(s)';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AuditarBrand.background,
      appBar: AppBar(
        title: const Text('Controle operacional de campo'),
        actions: [
          IconButton(
            tooltip: 'Atualizar',
            onPressed: loading ? null : _load,
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : error.isNotEmpty
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Text('Não foi possível montar o controle: $error'),
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView(
                    padding: const EdgeInsets.fromLTRB(14, 14, 14, 30),
                    children: [
                      _companyFilter(),
                      const SizedBox(height: 12),
                      _connectionCard(),
                      const SizedBox(height: 12),
                      _sectionTitle(
                        'Central de pendências',
                        'O que ainda precisa de tratamento ou acompanhamento.',
                      ),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          _metric('NCs abertas', openNc, Icons.warning_amber_rounded),
                          _metric('Alta/Crítica', highCriticalOpen, Icons.priority_high_rounded),
                          _metric('Ações abertas', openActions, Icons.assignment_outlined),
                          _metric('Ações vencidas', overdueActions, Icons.event_busy_outlined),
                          _metric('Trein. vencidos', trainingSummary['expired'] ?? 0, Icons.school_outlined),
                          _metric('Fila de envio', structuredPending + mediaPending, Icons.cloud_upload_outlined),
                        ],
                      ),
                      const SizedBox(height: 10),
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: [
                              FilledButton.tonalIcon(
                                onPressed: () => _open(
                                  ActionPlanScreen(companyId: selectedCompanyId),
                                ),
                                icon: const Icon(Icons.assignment_turned_in_outlined),
                                label: const Text('Abrir plano de ação'),
                              ),
                              OutlinedButton.icon(
                                onPressed: () => _open(
                                  NonConformitiesScreen(companyId: selectedCompanyId),
                                ),
                                icon: const Icon(Icons.list_alt_rounded),
                                label: const Text('Ver NCs'),
                              ),
                              OutlinedButton.icon(
                                onPressed: () => _open(
                                  TrainingsScreen(companyId: selectedCompanyId),
                                ),
                                icon: const Icon(Icons.school_outlined),
                                label: const Text('Treinamentos'),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      _sectionTitle(
                        'Antes × Depois e recorrências',
                        selectedCompany == null
                            ? 'Selecione uma empresa para cruzar evidências e recorrências sem misturar históricos.'
                            : 'Acompanhamento das correções e de problemas que podem ter voltado a ocorrer.',
                      ),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          _metric('Antes + depois', completeBeforeAfter, Icons.compare_outlined),
                          _metric('Aguardando depois', awaitingAfterEvidence, Icons.pending_actions_outlined),
                          _metric('Recorrências', recurrenceGroups.length, Icons.repeat_rounded),
                        ],
                      ),
                      const SizedBox(height: 8),
                      FilledButton.tonalIcon(
                        onPressed: selectedCompany == null
                            ? _requireCompany
                            : () => _open(
                                  CorrectionEvidenceCenterScreen(
                                    company: selectedCompany!,
                                  ),
                                ),
                        icon: const Icon(Icons.compare_outlined),
                        label: const Text('Abrir evidências e recorrências'),
                      ),
                      const SizedBox(height: 16),
                      _sectionTitle(
                        'O que conferir hoje',
                        'Roteiro montado localmente a partir das pendências existentes.',
                      ),
                      const SizedBox(height: 8),
                      ...visitPriorities.map(_priorityCard),
                      const SizedBox(height: 10),
                      Card(
                        child: ListTile(
                          leading: const Icon(Icons.fact_check_outlined),
                          title: Text(lastInspectionLabel),
                          subtitle: const Text(
                            'O roteiro é um apoio operacional e não substitui a avaliação do TST no local.',
                          ),
                          trailing: TextButton(
                            onPressed: () => _open(
                              NewInspectionScreen(initialCompany: selectedCompany),
                            ),
                            child: const Text('Nova vistoria'),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
    );
  }

  Widget _companyFilter() => DropdownButtonFormField<String>(
        value: companyId,
        isExpanded: true,
        decoration: const InputDecoration(
          labelText: 'Empresa',
          prefixIcon: Icon(Icons.business_outlined),
        ),
        items: [
          const DropdownMenuItem(
            value: '',
            child: Text('Todas as empresas autorizadas'),
          ),
          ...companies.map(
            (company) => DropdownMenuItem(
              value: company.id,
              child: Text(
                company.name,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ),
        ],
        onChanged: (value) async {
          companyId = value ?? '';
          await _load();
        },
      );

  Widget _connectionCard() {
    final pending = structuredPending + mediaPending;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  online == true
                      ? Icons.cloud_done_outlined
                      : online == false
                          ? Icons.cloud_off_outlined
                          : Icons.cloud_sync_outlined,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Status do aparelho: $connectionLabel',
                    style: const TextStyle(
                      fontWeight: FontWeight.w900,
                      fontSize: 16,
                    ),
                  ),
                ),
                IconButton(
                  tooltip: 'Testar conexão',
                  onPressed: _probeNetwork,
                  icon: const Icon(Icons.refresh_rounded),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              pending == 0
                  ? 'Sem itens locais aguardando envio.'
                  : '$pending item(ns) aguardando sincronização neste aparelho.',
            ),
            if (lastSync.isNotEmpty)
              Text(
                'Última sincronização registrada: ${_formatDate(lastSync)}',
                style: const TextStyle(fontSize: 12),
              ),
            if (lastSyncStatus.isNotEmpty)
              Text(
                'Situação registrada: $lastSyncStatus',
                style: const TextStyle(fontSize: 12),
              ),
            if (lastSyncError.isNotEmpty || mediaSyncError.isNotEmpty) ...[
              const SizedBox(height: 5),
              Text(
                [
                  if (lastSyncError.isNotEmpty) lastSyncError,
                  if (mediaSyncError.isNotEmpty) mediaSyncError,
                ].join(' • '),
                style: const TextStyle(fontSize: 11.5),
              ),
            ],
            const SizedBox(height: 5),
            const Text(
              'Quando estiver offline, os registros permanecem locais e a fila mostra o que ainda precisa ser enviado.',
              style: TextStyle(fontSize: 11.5, color: AuditarBrand.neutral),
            ),
          ],
        ),
      ),
    );
  }

  String _formatDate(String raw) {
    final date = DateTime.tryParse(raw);
    if (date == null) return raw;
    return DateFormat('dd/MM/yyyy HH:mm').format(date.toLocal());
  }

  Widget _sectionTitle(String title, String subtitle) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            subtitle,
            style: const TextStyle(color: AuditarBrand.neutral),
          ),
        ],
      );

  Widget _metric(String label, int value, IconData icon) => SizedBox(
        width: MediaQuery.sizeOf(context).width < 600 ? 165 : 205,
        child: Card(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Icon(icon, color: AuditarBrand.navy),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '$value',
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      Text(
                        label,
                        style: const TextStyle(
                          fontSize: 10.5,
                          color: AuditarBrand.neutral,
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

  Widget _priorityCard(FieldVisitPriorityItem item) {
    final icon = switch (item.level) {
      FieldVisitPriorityLevel.critical => Icons.dangerous_outlined,
      FieldVisitPriorityLevel.high => Icons.priority_high_rounded,
      FieldVisitPriorityLevel.attention => Icons.notification_important_outlined,
      FieldVisitPriorityLevel.info => Icons.info_outline_rounded,
      FieldVisitPriorityLevel.ok => Icons.verified_outlined,
    };
    final enabled = item.code != 'ok';
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: Icon(icon),
        title: Text(
          item.title,
          style: const TextStyle(fontWeight: FontWeight.w800),
        ),
        subtitle: Text(item.detail),
        trailing: enabled ? const Icon(Icons.chevron_right_rounded) : null,
        onTap: enabled ? () => _openPriority(item) : null,
      ),
    );
  }
}

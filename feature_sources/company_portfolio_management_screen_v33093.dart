import 'dart:async';

import 'package:flutter/material.dart';

import '../brand.dart';
import '../database.dart';
import '../models.dart';
import 'field_operational_control_screen.dart';

/// Visão gerencial multempresa somente leitura.
///
/// Consolida registros já existentes no aparelho. Não cria score legal,
/// não altera banco e não grava informações.
class CompanyPortfolioManagementScreen extends StatefulWidget {
  const CompanyPortfolioManagementScreen({super.key});

  @override
  State<CompanyPortfolioManagementScreen> createState() =>
      _CompanyPortfolioManagementScreenState();
}

class _CompanyPortfolioManagementScreenState
    extends State<CompanyPortfolioManagementScreen> {
  bool loading = true;
  String error = '';
  String search = '';
  String statusFilter = 'Todas';
  List<_CompanyPortfolioRow> rows = const [];

  @override
  void initState() {
    super.initState();
    unawaited(_load());
  }

  Future<void> _load() async {
    if (mounted) {
      setState(() {
        loading = true;
        error = '';
      });
    }

    try {
      final db = AppDatabase.instance;
      final companies = await db.getCompanies();
      final loaded = await Future.wait(
        companies.map((company) => _loadCompany(db, company)),
      );
      loaded.sort((a, b) {
        final byStatus = b.statusRank.compareTo(a.statusRank);
        if (byStatus != 0) return byStatus;
        final byCritical = b.highCritical.compareTo(a.highCritical);
        if (byCritical != 0) return byCritical;
        final byOverdue = b.overdueActions.compareTo(a.overdueActions);
        if (byOverdue != 0) return byOverdue;
        return a.company.name.toLowerCase().compareTo(
              b.company.name.toLowerCase(),
            );
      });

      if (!mounted) return;
      setState(() {
        rows = loaded;
        loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        loading = false;
        error = '$e';
      });
    }
  }

  Future<_CompanyPortfolioRow> _loadCompany(
    AppDatabase db,
    Company company,
  ) async {
    final ncsFuture = db.getNonConformityRows(
      companyId: company.id,
      includeClosed: true,
    );
    final actionsFuture = db.getPendingActions(
      companyId: company.id,
      includeCompleted: true,
    );
    final trainingFuture = db.getTrainingSummary(companyId: company.id);
    final inspectionsFuture = db.getInspectionHistory(companyId: company.id);

    final ncs = await ncsFuture;
    final actions = await actionsFuture;
    final training = await trainingFuture;
    final inspections = await inspectionsFuture;

    bool closed(Map<String, Object?> row) {
      final text = '${row['status'] ?? ''}'.trim().toLowerCase();
      return text.contains('conclu') ||
          text.contains('resolvid') ||
          text.contains('finaliz');
    }

    final openNc = ncs.where((row) => !closed(row)).length;
    final highCritical = ncs.where((row) {
      if (closed(row)) return false;
      final text = [
        '${row['priority'] ?? ''}',
        '${row['classification'] ?? ''}',
        '${row['severity'] ?? ''}',
      ].join(' ').toLowerCase();
      return text.contains('alta') ||
          text.contains('crit') ||
          text.contains('crít');
    }).length;

    final today = DateTime.now();
    final todayOnly = DateTime(today.year, today.month, today.day);
    final overdueActions = actions.where((row) {
      if (closed(row)) return false;
      final raw = '${row['due_date'] ?? ''}'.trim();
      final due = DateTime.tryParse(raw);
      if (due == null) return false;
      return DateTime(due.year, due.month, due.day).isBefore(todayOnly);
    }).length;

    DateTime? lastInspection;
    for (final row in inspections) {
      final date = DateTime.tryParse('${row['date'] ?? ''}'.trim());
      if (date != null &&
          (lastInspection == null || date.isAfter(lastInspection))) {
        lastInspection = date;
      }
    }

    final expiredTraining = training['expired'] ?? 0;
    final missingRequired = training['missingRequired'] ??
        training['missing_required'] ??
        0;

    final noData = inspections.isEmpty &&
        ncs.isEmpty &&
        actions.isEmpty &&
        training.values.every((value) => value == 0);

    late final String status;
    late final int rank;

    final daysWithoutInspection = lastInspection == null
        ? null
        : today.difference(lastInspection).inDays;

    if (noData) {
      status = 'Sem dados';
      rank = 2;
    } else if (highCritical > 0 || overdueActions >= 2) {
      status = 'Prioridade alta';
      rank = 4;
    } else if (overdueActions > 0 ||
        expiredTraining > 0 ||
        missingRequired > 0 ||
        openNc > 0 ||
        (daysWithoutInspection != null && daysWithoutInspection > 30)) {
      status = 'Atenção';
      rank = 3;
    } else {
      status = 'Controlada';
      rank = 1;
    }

    return _CompanyPortfolioRow(
      company: company,
      status: status,
      statusRank: rank,
      openNc: openNc,
      highCritical: highCritical,
      overdueActions: overdueActions,
      expiredTraining: expiredTraining,
      missingRequired: missingRequired,
      lastInspection: lastInspection,
    );
  }

  List<_CompanyPortfolioRow> get filteredRows {
    final needle = search.trim().toLowerCase();
    return rows.where((row) {
      if (statusFilter != 'Todas' && row.status != statusFilter) {
        return false;
      }
      if (needle.isEmpty) return true;
      final cnpj = row.company.cnpj?.toLowerCase() ?? '';
      return row.company.name.toLowerCase().contains(needle) ||
          cnpj.contains(needle);
    }).toList(growable: false);
  }

  int get totalOpenNc => rows.fold(0, (sum, row) => sum + row.openNc);
  int get totalHighCritical =>
      rows.fold(0, (sum, row) => sum + row.highCritical);
  int get totalOverdue =>
      rows.fold(0, (sum, row) => sum + row.overdueActions);
  int get totalExpired =>
      rows.fold(0, (sum, row) => sum + row.expiredTraining);
  int get priorityCompanies =>
      rows.where((row) => row.status == 'Prioridade alta').length;
  int get attentionCompanies =>
      rows.where((row) => row.status == 'Atenção').length;
  int get controlledCompanies =>
      rows.where((row) => row.status == 'Controlada').length;

  Future<void> _openCompany(_CompanyPortfolioRow row) async {
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => FieldOperationalControlScreen(
          initialCompanyId: row.company.id,
        ),
      ),
    );
    await _load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AuditarBrand.background,
      appBar: AppBar(
        title: const Text('Gestão Multempresa'),
        actions: [
          IconButton(
            tooltip: 'Atualizar carteira',
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
                    child: Text(
                      'Não foi possível montar a gestão multempresa: $error',
                    ),
                  ),
                )
              : LayoutBuilder(
                  builder: (context, constraints) {
                    return RefreshIndicator(
                      onRefresh: _load,
                      child: ListView(
                        padding: const EdgeInsets.fromLTRB(24, 20, 24, 36),
                        children: [
                          _hero(),
                          const SizedBox(height: 14),
                          _summaryCards(),
                          const SizedBox(height: 18),
                          _filters(),
                          const SizedBox(height: 12),
                          constraints.maxWidth >= 1050
                              ? _desktopTable()
                              : _compactList(),
                          const SizedBox(height: 16),
                          const Text(
                            'Situação gerencial calculada somente para priorização interna da carteira. Não representa certificação, laudo ou conclusão legal.',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              color: AuditarBrand.neutral,
                              fontSize: 10.5,
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                ),
    );
  }

  Widget _hero() {
    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: AuditarBrand.navy,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        children: [
          Container(
            width: 54,
            height: 54,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: .09),
              borderRadius: BorderRadius.circular(16),
            ),
            child: const Icon(
              Icons.apartment_rounded,
              color: Colors.white,
              size: 30,
            ),
          ),
          const SizedBox(width: 16),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'CARTEIRA DE EMPRESAS • AUDITAR SST',
                  style: TextStyle(
                    color: Color(0xFFA0E9D0),
                    fontSize: 10.5,
                    fontWeight: FontWeight.w900,
                    letterSpacing: .7,
                  ),
                ),
                SizedBox(height: 5),
                Text(
                  'Visão gerencial de todas as empresas acompanhadas',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 23,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                SizedBox(height: 5),
                Text(
                  'Priorize onde agir primeiro e entre no acompanhamento detalhado de cada cliente.',
                  style: TextStyle(
                    color: Colors.white70,
                    height: 1.35,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 18),
          Container(
            padding: const EdgeInsets.symmetric(
              horizontal: 18,
              vertical: 13,
            ),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: .08),
              borderRadius: BorderRadius.circular(15),
              border: Border.all(
                color: Colors.white.withValues(alpha: .14),
              ),
            ),
            child: Column(
              children: [
                Text(
                  '${rows.length}',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 30,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const Text(
                  'empresas',
                  style: TextStyle(
                    color: Colors.white70,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _summaryCards() {
    return Wrap(
      spacing: 10,
      runSpacing: 10,
      children: [
        _metric(
          'Prioridade alta',
          priorityCompanies,
          Icons.priority_high_rounded,
          AuditarBrand.danger,
        ),
        _metric(
          'Em atenção',
          attentionCompanies,
          Icons.warning_amber_rounded,
          AuditarBrand.warning,
        ),
        _metric(
          'Controladas',
          controlledCompanies,
          Icons.verified_outlined,
          AuditarBrand.greenDark,
        ),
        _metric(
          'NCs abertas',
          totalOpenNc,
          Icons.report_problem_outlined,
          AuditarBrand.warning,
        ),
        _metric(
          'Alta/Crítica',
          totalHighCritical,
          Icons.gpp_maybe_outlined,
          AuditarBrand.danger,
        ),
        _metric(
          'Ações vencidas',
          totalOverdue,
          Icons.event_busy_outlined,
          AuditarBrand.danger,
        ),
        _metric(
          'Trein. vencidos',
          totalExpired,
          Icons.school_outlined,
          AuditarBrand.info,
        ),
      ],
    );
  }

  Widget _metric(
    String label,
    int value,
    IconData icon,
    Color color,
  ) {
    return SizedBox(
      width: 178,
      child: Card(
        margin: EdgeInsets.zero,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              Icon(icon, color: color),
              const SizedBox(width: 9),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '$value',
                      style: TextStyle(
                        color: color,
                        fontSize: 22,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    Text(
                      label,
                      style: const TextStyle(
                        fontSize: 10.5,
                        fontWeight: FontWeight.w700,
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

  Widget _filters() {
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(13),
        child: Row(
          children: [
            Expanded(
              child: TextField(
                onChanged: (value) => setState(() => search = value),
                decoration: const InputDecoration(
                  prefixIcon: Icon(Icons.search_rounded),
                  labelText: 'Pesquisar empresa ou CNPJ',
                  isDense: true,
                ),
              ),
            ),
            const SizedBox(width: 12),
            SizedBox(
              width: 190,
              child: DropdownButtonFormField<String>(
                value: statusFilter,
                isDense: true,
                decoration: const InputDecoration(
                  labelText: 'Situação',
                  isDense: true,
                ),
                items: const [
                  'Todas',
                  'Prioridade alta',
                  'Atenção',
                  'Controlada',
                  'Sem dados',
                ]
                    .map(
                      (value) => DropdownMenuItem(
                        value: value,
                        child: Text(value),
                      ),
                    )
                    .toList(),
                onChanged: (value) {
                  if (value != null) {
                    setState(() => statusFilter = value);
                  }
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _desktopTable() {
    final data = filteredRows;
    return Card(
      margin: EdgeInsets.zero,
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 15, 16, 4),
            child: Text(
              'Empresas por prioridade de acompanhamento',
              style: TextStyle(
                color: AuditarBrand.navy,
                fontSize: 17,
                fontWeight: FontWeight.w900,
              ),
            ),
          ),
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 0, 16, 10),
            child: Text(
              'Clique em uma empresa para abrir a Central de Gestão e o Painel Executivo.',
              style: TextStyle(
                color: AuditarBrand.neutral,
                fontSize: 11.5,
              ),
            ),
          ),
          const Divider(height: 1),
          if (data.isEmpty)
            const Padding(
              padding: EdgeInsets.all(24),
              child: Center(child: Text('Nenhuma empresa neste filtro.')),
            )
          else
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                columns: const [
                  DataColumn(label: Text('Empresa')),
                  DataColumn(label: Text('Situação')),
                  DataColumn(label: Text('NCs abertas'), numeric: true),
                  DataColumn(label: Text('Alta/Crítica'), numeric: true),
                  DataColumn(label: Text('Ações vencidas'), numeric: true),
                  DataColumn(label: Text('Trein. vencidos'), numeric: true),
                  DataColumn(label: Text('Última vistoria')),
                ],
                rows: [
                  for (final row in data)
                    DataRow(
                      onSelectChanged: (_) => _openCompany(row),
                      cells: [
                        DataCell(
                          SizedBox(
                            width: 230,
                            child: Text(
                              row.company.name,
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                          ),
                        ),
                        DataCell(_statusChip(row)),
                        DataCell(Text('${row.openNc}')),
                        DataCell(Text('${row.highCritical}')),
                        DataCell(Text('${row.overdueActions}')),
                        DataCell(Text('${row.expiredTraining}')),
                        DataCell(Text(row.lastInspectionLabel)),
                      ],
                    ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _compactList() {
    final data = filteredRows;
    if (data.isEmpty) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Center(child: Text('Nenhuma empresa neste filtro.')),
        ),
      );
    }
    return Column(
      children: [
        for (final row in data)
          Card(
            margin: const EdgeInsets.only(bottom: 9),
            child: ListTile(
              onTap: () => _openCompany(row),
              leading: CircleAvatar(
                backgroundColor: row.statusColor.withValues(alpha: .10),
                child: Icon(
                  Icons.business_outlined,
                  color: row.statusColor,
                ),
              ),
              title: Text(
                row.company.name,
                style: const TextStyle(fontWeight: FontWeight.w900),
              ),
              subtitle: Text(
                '${row.status} • NCs ${row.openNc} • Vencidas ${row.overdueActions} • Trein. ${row.expiredTraining}',
              ),
              trailing: const Icon(Icons.chevron_right_rounded),
            ),
          ),
      ],
    );
  }

  Widget _statusChip(_CompanyPortfolioRow row) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: row.statusColor.withValues(alpha: .10),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        row.status,
        style: TextStyle(
          color: row.statusColor,
          fontSize: 10.5,
          fontWeight: FontWeight.w900,
        ),
      ),
    );
  }
}

class _CompanyPortfolioRow {
  final Company company;
  final String status;
  final int statusRank;
  final int openNc;
  final int highCritical;
  final int overdueActions;
  final int expiredTraining;
  final int missingRequired;
  final DateTime? lastInspection;

  const _CompanyPortfolioRow({
    required this.company,
    required this.status,
    required this.statusRank,
    required this.openNc,
    required this.highCritical,
    required this.overdueActions,
    required this.expiredTraining,
    required this.missingRequired,
    required this.lastInspection,
  });

  Color get statusColor {
    switch (status) {
      case 'Prioridade alta':
        return AuditarBrand.danger;
      case 'Atenção':
        return AuditarBrand.warning;
      case 'Controlada':
        return AuditarBrand.greenDark;
      default:
        return AuditarBrand.neutral;
    }
  }

  String get lastInspectionLabel {
    final date = lastInspection;
    if (date == null) return 'Sem registro';
    final day = date.day.toString().padLeft(2, '0');
    final month = date.month.toString().padLeft(2, '0');
    return '$day/$month/${date.year}';
  }
}

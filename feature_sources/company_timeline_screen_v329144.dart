import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../brand.dart';
import '../database.dart';
import '../models.dart';
import 'action_plan_screen.dart';
import 'history_screen.dart';
import 'routine_hub_screen.dart';
import 'trainings_screen.dart';

class CompanyTimelineScreen extends StatefulWidget {
  final Company company;

  const CompanyTimelineScreen({super.key, required this.company});

  @override
  State<CompanyTimelineScreen> createState() => _CompanyTimelineScreenState();
}

class _CompanyTimelineScreenState extends State<CompanyTimelineScreen> {
  bool loading = true;
  String filter = 'Tudo';
  List<_TimelineEvent> events = const [];

  static const filters = <String>[
    'Tudo',
    'Vistorias',
    'DDS',
    'Treinamentos',
    'Segurança',
    'Correções',
  ];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    if (mounted) setState(() => loading = true);
    final db = AppDatabase.instance;
    final inspections = await db.getInspectionHistory(companyId: widget.company.id);
    final dds = await db.getSstRecords(type: 'DDS', companyId: widget.company.id);
    final trainings = await db.getSstRecords(
      type: 'TREINAMENTO_SESSAO',
      companyId: widget.company.id,
    );
    final safety = await db.getSstRecords(
      type: 'OBSERVACAO_SEGURANCA',
      companyId: widget.company.id,
    );
    final actions = await db.getPendingActions(
      companyId: widget.company.id,
      includeCompleted: true,
    );

    final result = <_TimelineEvent>[];
    for (final row in inspections) {
      final date = DateTime.tryParse('${row['date'] ?? ''}');
      if (date == null) continue;
      result.add(_TimelineEvent(
        date: date,
        category: 'Vistorias',
        icon: Icons.fact_check_outlined,
        title: '${row['report_number'] ?? ''}'.trim().isNotEmpty
            ? 'Vistoria • ${row['report_number']}'
            : 'Vistoria realizada',
        subtitle: [
          row['area'],
          row['sector_name'],
          row['status'],
        ].where((e) => '${e ?? ''}'.trim().isNotEmpty).join(' • '),
        page: () => HistoryScreen(companyId: widget.company.id),
      ));
    }

    void addRecords(
      List<SstRecord> rows,
      String category,
      IconData icon,
      Widget Function() page,
    ) {
      for (final record in rows) {
        result.add(_TimelineEvent(
          date: record.date,
          category: category,
          icon: icon,
          title: record.title.trim().isEmpty ? category : record.title,
          subtitle: [
            record.payload['sectorName'],
            record.payload['location'],
            record.status,
          ].where((e) => '${e ?? ''}'.trim().isNotEmpty).join(' • '),
          page: page,
        ));
      }
    }

    addRecords(
      dds,
      'DDS',
      Icons.record_voice_over_outlined,
      () => RoutineHubScreen(companyId: widget.company.id),
    );
    addRecords(
      trainings,
      'Treinamentos',
      Icons.school_outlined,
      () => TrainingsScreen(companyId: widget.company.id),
    );
    addRecords(
      safety,
      'Segurança',
      Icons.visibility_outlined,
      () => RoutineHubScreen(companyId: widget.company.id),
    );

    for (final row in actions) {
      final completed = DateTime.tryParse('${row['completion_date'] ?? ''}');
      if (completed == null) continue;
      result.add(_TimelineEvent(
        date: completed,
        category: 'Correções',
        icon: Icons.verified_outlined,
        title: '${row['corrective_action'] ?? 'Correção concluída'}',
        subtitle: [
          row['sector_name'],
          row['responsible'],
          row['completed_by'],
        ].where((e) => '${e ?? ''}'.trim().isNotEmpty).join(' • '),
        page: () => ActionPlanScreen(companyId: widget.company.id),
      ));
    }

    result.sort((a, b) => b.date.compareTo(a.date));
    if (!mounted) return;
    setState(() {
      events = result;
      loading = false;
    });
  }

  List<_TimelineEvent> get visible => filter == 'Tudo'
      ? events
      : events.where((e) => e.category == filter).toList(growable: false);

  Future<void> _open(Widget page) async {
    await Navigator.of(context).push(MaterialPageRoute(builder: (_) => page));
    if (mounted) _load();
  }

  @override
  Widget build(BuildContext context) {
    final rows = visible;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Linha do tempo'),
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
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.fromLTRB(14, 14, 14, 30),
                children: [
                  Container(
                    padding: const EdgeInsets.all(17),
                    decoration: BoxDecoration(
                      color: AuditarBrand.navy,
                      borderRadius: BorderRadius.circular(18),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(Icons.timeline_rounded,
                            color: Colors.white, size: 30),
                        const SizedBox(height: 9),
                        Text(
                          widget.company.name,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 19,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                        const SizedBox(height: 4),
                        const Text(
                          'Vistorias, DDS, treinamentos, observações de segurança e correções em ordem cronológica.',
                          style: TextStyle(color: Colors.white70, height: 1.35),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: filters.map((value) => Padding(
                        padding: const EdgeInsets.only(right: 7),
                        child: ChoiceChip(
                          label: Text(value),
                          selected: filter == value,
                          onSelected: (_) => setState(() => filter = value),
                        ),
                      )).toList(),
                    ),
                  ),
                  const SizedBox(height: 12),
                  if (rows.isEmpty)
                    const Card(
                      child: Padding(
                        padding: EdgeInsets.all(18),
                        child: Text('Nenhum registro encontrado neste filtro.'),
                      ),
                    )
                  else
                    ...rows.map((event) => _eventCard(event)),
                ],
              ),
            ),
    );
  }

  Widget _eventCard(_TimelineEvent event) {
    final date = DateFormat('dd/MM/yyyy • HH:mm').format(event.date.toLocal());
    return Container(
      margin: const EdgeInsets.only(bottom: 9),
      child: Card(
        child: ListTile(
          contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          leading: CircleAvatar(
            backgroundColor: AuditarBrand.greenSoft,
            foregroundColor: AuditarBrand.greenDark,
            child: Icon(event.icon),
          ),
          title: Text(
            event.title,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontWeight: FontWeight.w800),
          ),
          subtitle: Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(
              '${event.category} • $date'
              '${event.subtitle.trim().isEmpty ? '' : '\n${event.subtitle}'}',
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          trailing: const Icon(Icons.chevron_right_rounded),
          onTap: () => _open(event.page()),
        ),
      ),
    );
  }
}

class _TimelineEvent {
  final DateTime date;
  final String category;
  final IconData icon;
  final String title;
  final String subtitle;
  final Widget Function() page;

  const _TimelineEvent({
    required this.date,
    required this.category,
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.page,
  });
}

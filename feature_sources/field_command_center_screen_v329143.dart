import 'package:flutter/material.dart';

import '../brand.dart';
import '../database.dart';
import 'action_plan_screen.dart';
import 'companies_screen.dart';
import 'non_conformities_screen.dart';
import 'routine_hub_screen.dart';
import 'trainings_screen.dart';

class FieldCommandCenterScreen extends StatefulWidget {
  const FieldCommandCenterScreen({super.key});

  @override
  State<FieldCommandCenterScreen> createState() => _FieldCommandCenterScreenState();
}

class _FieldCommandCenterScreenState extends State<FieldCommandCenterScreen> {
  bool loading = true;
  String error = '';
  int companies = 0;
  int workers = 0;
  int openNcs = 0;
  int pendingActions = 0;
  int overdueActions = 0;
  Map<String, int> routine = const {};
  List<Map<String, Object?>> priorities = const [];
  DateTime? updatedAt;

  @override
  void initState() {
    super.initState();
    _load();
  }

  bool _overdue(Map<String, Object?> row) {
    if ('${row['status'] ?? ''}' == 'Concluído') return false;
    final due = DateTime.tryParse('${row['due_date'] ?? ''}');
    if (due == null) return false;
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    return DateTime(due.year, due.month, due.day).isBefore(today);
  }

  Future<void> _load() async {
    if (mounted) setState(() {
      loading = true;
      error = '';
    });
    try {
      final db = AppDatabase.instance;
      final c = await db.getCompanies();
      final w = await db.getWorkers();
      final n = await db.getNonConformityRows(includeClosed: false);
      final a = await db.getPendingActions(includeCompleted: false);
      final r = await db.getRoutineTodaySummary();
      final ordered = [...a]..sort((x, y) {
        final xo = _overdue(x) ? 0 : 1;
        final yo = _overdue(y) ? 0 : 1;
        if (xo != yo) return xo.compareTo(yo);
        final xd = DateTime.tryParse('${x['due_date'] ?? ''}');
        final yd = DateTime.tryParse('${y['due_date'] ?? ''}');
        if (xd == null && yd == null) return 0;
        if (xd == null) return 1;
        if (yd == null) return -1;
        return xd.compareTo(yd);
      });
      if (!mounted) return;
      setState(() {
        companies = c.length;
        workers = w.length;
        openNcs = n.length;
        pendingActions = a.length;
        overdueActions = a.where(_overdue).length;
        routine = r;
        priorities = ordered.take(8).toList(growable: false);
        updatedAt = DateTime.now();
        loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        error = 'Não foi possível montar o resumo agora. Os registros existentes foram preservados.';
        loading = false;
      });
    }
  }

  Widget _metric(String label, int value, IconData icon, {bool warning = false}) {
    final tone = warning ? AuditarBrand.danger : AuditarBrand.greenDark;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: tone.withValues(alpha: .07),
        borderRadius: BorderRadius.circular(15),
        border: Border.all(color: tone.withValues(alpha: .15)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: tone),
          const SizedBox(height: 9),
          Text('$value',
              style: TextStyle(
                color: tone,
                fontSize: 24,
                fontWeight: FontWeight.w900,
              )),
          const SizedBox(height: 2),
          Text(label, style: const TextStyle(fontSize: 11.5)),
        ],
      ),
    );
  }

  Future<void> _open(Widget page) async {
    await Navigator.of(context).push(MaterialPageRoute(builder: (_) => page));
    if (mounted) _load();
  }

  String _due(Map<String, Object?> row) {
    final parsed = DateTime.tryParse('${row['due_date'] ?? ''}');
    if (parsed == null) return 'Sem prazo';
    final text =
        '${parsed.day.toString().padLeft(2, '0')}/${parsed.month.toString().padLeft(2, '0')}/${parsed.year}';
    return _overdue(row) ? 'Vencida • $text' : 'Prazo • $text';
  }

  @override
  Widget build(BuildContext context) {
    final agendaToday = routine['agendaToday'] ?? routine['agenda_today'] ?? 0;
    final equipmentDue = routine['equipmentDue'] ?? routine['equipment_due'] ?? 0;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Central do Técnico'),
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
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      color: AuditarBrand.navy,
                      borderRadius: BorderRadius.circular(19),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(Icons.engineering_outlined,
                            color: Colors.white, size: 30),
                        const SizedBox(height: 10),
                        const Text('O que precisa da sua atenção',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 20,
                              fontWeight: FontWeight.w900,
                            )),
                        const SizedBox(height: 5),
                        Text(
                          updatedAt == null
                              ? 'Resumo operacional do aplicativo.'
                              : 'Atualizado às ${updatedAt!.hour.toString().padLeft(2, '0')}:${updatedAt!.minute.toString().padLeft(2, '0')}',
                          style: const TextStyle(color: Colors.white70),
                        ),
                      ],
                    ),
                  ),
                  if (error.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    Text(error, style: const TextStyle(color: Colors.deepOrange)),
                  ],
                  const SizedBox(height: 12),
                  GridView.count(
                    crossAxisCount: MediaQuery.sizeOf(context).width >= 700 ? 4 : 2,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    crossAxisSpacing: 9,
                    mainAxisSpacing: 9,
                    childAspectRatio: 1.45,
                    children: [
                      _metric('Empresas', companies, Icons.business_outlined),
                      _metric('Trabalhadores', workers, Icons.groups_outlined),
                      _metric('NCs abertas', openNcs, Icons.warning_amber_rounded,
                          warning: openNcs > 0),
                      _metric('Ações vencidas', overdueActions, Icons.event_busy_outlined,
                          warning: overdueActions > 0),
                    ],
                  ),
                  const SizedBox(height: 14),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      ActionChip(
                        avatar: const Icon(Icons.business_outlined, size: 18),
                        label: const Text('Empresas'),
                        onPressed: () => _open(const CompaniesScreen()),
                      ),
                      ActionChip(
                        avatar: const Icon(Icons.assignment_turned_in_outlined, size: 18),
                        label: Text('Planos de ação ($pendingActions)'),
                        onPressed: () => _open(const ActionPlanScreen()),
                      ),
                      ActionChip(
                        avatar: const Icon(Icons.warning_amber_rounded, size: 18),
                        label: Text('NCs ($openNcs)'),
                        onPressed: () => _open(const NonConformitiesScreen()),
                      ),
                      ActionChip(
                        avatar: const Icon(Icons.calendar_month_outlined, size: 18),
                        label: Text('Agenda de hoje ($agendaToday)'),
                        onPressed: () => _open(const RoutineHubScreen()),
                      ),
                      ActionChip(
                        avatar: const Icon(Icons.handyman_outlined, size: 18),
                        label: Text('Equipamentos próximos ($equipmentDue)'),
                        onPressed: () => _open(const RoutineHubScreen()),
                      ),
                      ActionChip(
                        avatar: const Icon(Icons.school_outlined, size: 18),
                        label: const Text('Treinamentos'),
                        onPressed: () => _open(const TrainingsScreen()),
                      ),
                    ],
                  ),
                  const SizedBox(height: 18),
                  Text('Prioridades',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w900,
                      )),
                  const SizedBox(height: 7),
                  if (priorities.isEmpty)
                    const Card(
                      child: Padding(
                        padding: EdgeInsets.all(16),
                        child: Text('Nenhuma ação pendente encontrada.'),
                      ),
                    )
                  else
                    ...priorities.map((row) => Card(
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: (_overdue(row)
                                  ? AuditarBrand.danger
                                  : AuditarBrand.warning)
                              .withValues(alpha: .10),
                          foregroundColor: _overdue(row)
                              ? AuditarBrand.danger
                              : AuditarBrand.warning,
                          child: Icon(_overdue(row)
                              ? Icons.priority_high_rounded
                              : Icons.pending_actions_outlined),
                        ),
                        title: Text(
                          '${row['corrective_action'] ?? row['non_conformity'] ?? 'Ação pendente'}',
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontWeight: FontWeight.w700),
                        ),
                        subtitle: Text(
                          '${row['company_name'] ?? ''} • ${_due(row)}',
                          maxLines: 2,
                        ),
                        trailing: const Icon(Icons.chevron_right_rounded),
                        onTap: () => _open(const ActionPlanScreen()),
                      ),
                    )),
                ],
              ),
            ),
    );
  }
}

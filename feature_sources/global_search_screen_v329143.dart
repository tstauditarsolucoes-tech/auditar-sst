import 'package:flutter/material.dart';

import '../brand.dart';
import '../database.dart';
import '../models.dart';
import 'action_plan_screen.dart';
import 'company_detail_screen.dart';
import 'history_screen.dart';
import 'non_conformities_screen.dart';
import 'routine_hub_screen.dart';
import 'trainings_screen.dart';
import 'workers_screen.dart';

class GlobalSearchScreen extends StatefulWidget {
  final Company? company;

  const GlobalSearchScreen({super.key, this.company});

  @override
  State<GlobalSearchScreen> createState() => _GlobalSearchScreenState();
}

class _GlobalSearchScreenState extends State<GlobalSearchScreen> {
  final controller = TextEditingController();
  bool loading = false;
  int generation = 0;
  List<_SearchHit> hits = [];

  @override
  void initState() {
    super.initState();
    controller.addListener(_search);
  }

  @override
  void dispose() {
    controller.removeListener(_search);
    controller.dispose();
    super.dispose();
  }

  bool _match(String query, Iterable<Object?> values) {
    final text = values.map((e) => '${e ?? ''}'.toLowerCase()).join(' ');
    return text.contains(query);
  }

  Future<void> _search() async {
    final query = controller.text.trim().toLowerCase();
    final current = ++generation;
    if (query.length < 2) {
      if (mounted) setState(() {
        hits = [];
        loading = false;
      });
      return;
    }
    if (mounted) setState(() => loading = true);
    try {
      final db = AppDatabase.instance;
      final companyId = widget.company?.id;
      final companies = companyId == null
          ? await db.getCompanies(onlyActive: false)
          : <Company>[widget.company!];
      final workers = await db.getWorkers(companyId: companyId, onlyActive: false);
      final inspections = await db.getInspectionHistory(companyId: companyId);
      final ncs = await db.getNonConformityRows(
        companyId: companyId,
        includeClosed: true,
      );
      final actions = await db.getPendingActions(
        companyId: companyId,
        includeCompleted: true,
      );
      final dds = await db.getSstRecords(type: 'DDS', companyId: companyId);
      final trainings = await db.getSstRecords(
        type: 'TREINAMENTO_SESSAO',
        companyId: companyId,
      );
      final safety = await db.getSstRecords(
        type: 'OBSERVACAO_SEGURANCA',
        companyId: companyId,
      );
      if (!mounted || current != generation) return;

      final companyById = {for (final c in companies) c.id: c};
      final result = <_SearchHit>[];

      for (final c in companies) {
        if (_match(query, [c.name, c.cnpj, c.city, c.uf, c.contact])) {
          result.add(_SearchHit(
            icon: Icons.business_outlined,
            type: 'Empresa',
            title: c.name,
            subtitle: [c.cnpj, c.city, c.uf]
                .where((v) => v != null && v!.trim().isNotEmpty)
                .join(' • '),
            companyId: c.id,
            open: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => CompanyDetailScreen(company: c)),
            ),
          ));
        }
      }

      for (final w in workers) {
        if (_match(query, [w.name, w.role, w.cpf])) {
          final c = companyById[w.companyId];
          result.add(_SearchHit(
            icon: Icons.person_search_outlined,
            type: 'Trabalhador',
            title: w.name,
            subtitle: [w.role, c?.name].where((e) => '${e ?? ''}'.isNotEmpty).join(' • '),
            companyId: w.companyId,
            open: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => WorkersScreen(companyId: w.companyId)),
            ),
          ));
        }
      }

      for (final row in inspections) {
        if (_match(query, [
          row['company_name'], row['area'], row['sector_name'],
          row['worksite_name'], row['report_number'], row['status'],
          row['checklist_type'],
        ])) {
          result.add(_SearchHit(
            icon: Icons.fact_check_outlined,
            type: 'Vistoria',
            title: '${row['area'] ?? row['checklist_type'] ?? 'Vistoria'}',
            subtitle: '${row['company_name'] ?? ''} • ${row['sector_name'] ?? ''}',
            open: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => HistoryScreen(companyId: companyId)),
            ),
          ));
        }
      }

      for (final row in ncs) {
        if (_match(query, [
          row['code'], row['description'], row['company_name'],
          row['sector_name'], row['area'], row['status'],
          row['question_text'], row['question_reference'],
        ])) {
          result.add(_SearchHit(
            icon: Icons.warning_amber_rounded,
            type: 'Não conformidade',
            title: '${row['code'] ?? 'NC'} • ${row['description'] ?? ''}',
            subtitle: '${row['company_name'] ?? ''} • ${row['status'] ?? ''}',
            open: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => NonConformitiesScreen(companyId: companyId)),
            ),
          ));
        }
      }

      for (final row in actions) {
        if (_match(query, [
          row['company_name'], row['nc_code'], row['sector_name'],
          row['area'], row['location_detail'], row['non_conformity'],
          row['corrective_action'], row['responsible'], row['status'],
        ])) {
          result.add(_SearchHit(
            icon: Icons.assignment_turned_in_outlined,
            type: 'Plano de ação',
            title: '${row['corrective_action'] ?? row['non_conformity'] ?? 'Ação'}',
            subtitle: '${row['company_name'] ?? ''} • ${row['status'] ?? ''}',
            open: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => ActionPlanScreen(companyId: companyId)),
            ),
          ));
        }
      }

      void addRecords(List<SstRecord> records, String type, IconData icon, Widget Function() page) {
        for (final record in records) {
          if (_match(query, [
            record.title, record.status, record.priority,
            record.payload['description'], record.payload['sectorName'],
            record.payload['location'], record.payload['theme'],
          ])) {
            result.add(_SearchHit(
              icon: icon,
              type: type,
              title: record.title,
              subtitle: '${record.status} • ${record.date.day.toString().padLeft(2, '0')}/${record.date.month.toString().padLeft(2, '0')}/${record.date.year}',
              open: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => page()),
              ),
            ));
          }
        }
      }

      addRecords(
        dds,
        'DDS',
        Icons.record_voice_over_outlined,
        () => RoutineHubScreen(companyId: companyId),
      );
      addRecords(
        trainings,
        'Treinamento',
        Icons.school_outlined,
        () => TrainingsScreen(companyId: companyId),
      );
      addRecords(
        safety,
        'Segurança observada',
        Icons.visibility_outlined,
        () => RoutineHubScreen(companyId: companyId),
      );

      result.sort((a, b) {
        final aStarts = a.title.toLowerCase().startsWith(query) ? 0 : 1;
        final bStarts = b.title.toLowerCase().startsWith(query) ? 0 : 1;
        final byStart = aStarts.compareTo(bStarts);
        return byStart != 0 ? byStart : a.type.compareTo(b.type);
      });
      if (!mounted || current != generation) return;
      setState(() {
        hits = result.take(80).toList(growable: false);
        loading = false;
      });
    } catch (_) {
      if (!mounted || current != generation) return;
      setState(() {
        hits = [];
        loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final scope = widget.company == null ? 'todo o app' : widget.company!.name;
    return Scaffold(
      appBar: AppBar(title: const Text('Busca global')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 14, 14, 8),
            child: TextField(
              controller: controller,
              autofocus: true,
              decoration: InputDecoration(
                labelText: 'Pesquisar em $scope',
                hintText: 'Nome, NR, setor, relatório, DDS, treinamento...',
                prefixIcon: const Icon(Icons.search_rounded),
                suffixIcon: controller.text.isEmpty
                    ? null
                    : IconButton(
                        tooltip: 'Limpar',
                        onPressed: controller.clear,
                        icon: const Icon(Icons.close_rounded),
                      ),
              ),
            ),
          ),
          if (loading) const LinearProgressIndicator(minHeight: 2),
          Expanded(
            child: controller.text.trim().length < 2
                ? const _SearchEmpty(
                    icon: Icons.manage_search_rounded,
                    title: 'Pesquise tudo em um só lugar',
                    text: 'Digite pelo menos 2 caracteres para localizar empresas, trabalhadores, vistorias, NCs, ações, DDS e treinamentos.',
                  )
                : hits.isEmpty && !loading
                ? const _SearchEmpty(
                    icon: Icons.search_off_rounded,
                    title: 'Nenhum resultado encontrado',
                    text: 'Tente outro nome, setor, NR, palavra do relatório ou atividade.',
                  )
                : ListView.separated(
                    padding: const EdgeInsets.fromLTRB(12, 6, 12, 24),
                    itemCount: hits.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 5),
                    itemBuilder: (_, index) {
                      final hit = hits[index];
                      return Card(
                        child: ListTile(
                          leading: CircleAvatar(
                            backgroundColor: AuditarBrand.greenSoft,
                            foregroundColor: AuditarBrand.greenDark,
                            child: Icon(hit.icon),
                          ),
                          title: Text(
                            hit.title,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontWeight: FontWeight.w700),
                          ),
                          subtitle: Text(
                            '${hit.type}${hit.subtitle.trim().isEmpty ? '' : ' • ${hit.subtitle}'}',
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                          trailing: const Icon(Icons.chevron_right_rounded),
                          onTap: hit.open,
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

class _SearchHit {
  final IconData icon;
  final String type;
  final String title;
  final String subtitle;
  final String? companyId;
  final VoidCallback open;

  const _SearchHit({
    required this.icon,
    required this.type,
    required this.title,
    required this.subtitle,
    required this.open,
    this.companyId,
  });
}

class _SearchEmpty extends StatelessWidget {
  final IconData icon;
  final String title;
  final String text;

  const _SearchEmpty({
    required this.icon,
    required this.title,
    required this.text,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 440),
        child: Padding(
          padding: const EdgeInsets.all(26),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 52, color: AuditarBrand.greenDark),
              const SizedBox(height: 12),
              Text(title,
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
              const SizedBox(height: 7),
              Text(text,
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.black54, height: 1.4)),
            ],
          ),
        ),
      ),
    );
  }
}

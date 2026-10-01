import 'package:flutter/material.dart';

import '../brand.dart';
import '../database.dart';
import '../models.dart';
import 'company_detail_screen.dart';
import 'history_screen.dart';
import 'trainings_screen.dart';
import 'workers_screen.dart';

class GlobalSearchScreen extends StatefulWidget {
  const GlobalSearchScreen({super.key});

  @override
  State<GlobalSearchScreen> createState() => _GlobalSearchScreenState();
}

class _SearchHit {
  final String kind;
  final String title;
  final String subtitle;
  final IconData icon;
  final String? companyId;
  final Company? company;

  const _SearchHit({
    required this.kind,
    required this.title,
    required this.subtitle,
    required this.icon,
    this.companyId,
    this.company,
  });
}

class _GlobalSearchScreenState extends State<GlobalSearchScreen> {
  final queryController = TextEditingController();
  bool loading = true;
  String error = '';
  String query = '';

  List<Company> companies = const [];
  List<Worker> workers = const [];
  List<TrainingControl> trainings = const [];
  List<Map<String, Object?>> inspections = const [];
  List<SstRecord> safety = const [];
  List<SstRecord> dds = const [];
  List<SstRecord> trainingSessions = const [];
  List<SstRecord> improvements = const [];

  Map<String, Company> get companyById => {
    for (final company in companies) company.id: company,
  };

  Map<String, Worker> get workerById => {
    for (final worker in workers) worker.id: worker,
  };

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    queryController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    if (mounted) setState(() {
      loading = true;
      error = '';
    });
    try {
      final db = AppDatabase.instance;
      final values = await Future.wait<Object>([
        db.getCompanies(),
        db.getWorkers(),
        db.getTrainingControls(),
        db.getInspectionHistory(),
        db.getSstRecords(type: 'OBSERVACAO_SEGURANCA'),
        db.getSstRecords(type: 'DDS'),
        db.getSstRecords(type: 'TREINAMENTO_SESSAO'),
        db.getSstRecords(type: 'MELHORIA'),
      ]);
      if (!mounted) return;
      setState(() {
        companies = values[0] as List<Company>;
        workers = values[1] as List<Worker>;
        trainings = values[2] as List<TrainingControl>;
        inspections = values[3] as List<Map<String, Object?>>;
        safety = values[4] as List<SstRecord>;
        dds = values[5] as List<SstRecord>;
        trainingSessions = values[6] as List<SstRecord>;
        improvements = values[7] as List<SstRecord>;
        loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        error = 'Não foi possível preparar a pesquisa: $e';
        loading = false;
      });
    }
  }

  String _norm(Object? value) => '$value'.trim().toLowerCase();

  bool _matches(String value, List<String> terms) {
    final text = value.toLowerCase();
    return terms.every(text.contains);
  }

  List<_SearchHit> _hits() {
    final raw = query.trim();
    if (raw.length < 2) return const [];
    final terms = raw.toLowerCase().split(RegExp(r'\s+')).where((e) => e.isNotEmpty).toList();
    final hits = <_SearchHit>[];
    final companiesMap = companyById;
    final workersMap = workerById;

    for (final company in companies) {
      final text = [company.name, company.cnpj ?? '', company.city ?? '', company.uf ?? ''].join(' ');
      if (_matches(text, terms)) {
        hits.add(_SearchHit(
          kind: 'Empresa',
          title: company.name,
          subtitle: [company.cnpj ?? '', company.city ?? '', company.uf ?? ''].where((e) => e.trim().isNotEmpty).join(' • '),
          icon: Icons.business_outlined,
          companyId: company.id,
          company: company,
        ));
      }
    }

    for (final worker in workers) {
      final company = companiesMap[worker.companyId];
      final text = [worker.name, worker.role, company?.name ?? ''].join(' ');
      if (_matches(text, terms)) {
        hits.add(_SearchHit(
          kind: 'Trabalhador',
          title: worker.name,
          subtitle: [worker.role, company?.name ?? ''].where((e) => e.trim().isNotEmpty).join(' • '),
          icon: Icons.person_search_outlined,
          companyId: worker.companyId,
          company: company,
        ));
      }
    }

    for (final training in trainings) {
      final worker = workersMap[training.workerId];
      final company = worker == null ? null : companiesMap[worker.companyId];
      final text = [training.code, training.title, worker?.name ?? '', company?.name ?? ''].join(' ');
      if (_matches(text, terms)) {
        hits.add(_SearchHit(
          kind: 'Treinamento',
          title: [training.code, training.title].where((e) => e.trim().isNotEmpty).join(' • '),
          subtitle: [worker?.name ?? '', company?.name ?? '', training.statusAt(DateTime.now())]
              .where((e) => e.trim().isNotEmpty).join(' • '),
          icon: Icons.school_outlined,
          companyId: worker?.companyId,
          company: company,
        ));
      }
    }

    for (final row in inspections) {
      final text = [
        _norm(row['company_name']),
        _norm(row['area']),
        _norm(row['checklist_type']),
        _norm(row['report_number']),
        _norm(row['sector_name']),
      ].join(' ');
      if (_matches(text, terms)) {
        hits.add(_SearchHit(
          kind: 'Vistoria',
          title: '${row['area'] ?? row['checklist_type'] ?? 'Vistoria'}',
          subtitle: [
            '${row['company_name'] ?? ''}',
            '${row['sector_name'] ?? ''}',
            '${row['status'] ?? ''}',
          ].where((e) => e.trim().isNotEmpty).join(' • '),
          icon: Icons.fact_check_outlined,
        ));
      }
    }

    void addRecords(List<SstRecord> records, String kind, IconData icon) {
      for (final record in records) {
        final company = record.companyId == null ? null : companiesMap[record.companyId];
        final payloadText = record.payload.values
            .where((v) => v is String || v is num || v is bool)
            .take(12)
            .join(' ');
        final text = [record.title, record.status, record.priority, company?.name ?? '', payloadText].join(' ');
        if (_matches(text, terms)) {
          hits.add(_SearchHit(
            kind: kind,
            title: record.title.trim().isEmpty ? kind : record.title,
            subtitle: [company?.name ?? '', record.status, record.priority]
                .where((e) => e.trim().isNotEmpty).join(' • '),
            icon: icon,
            companyId: record.companyId,
            company: company,
          ));
        }
      }
    }

    addRecords(safety, 'Segurança observada', Icons.health_and_safety_outlined);
    addRecords(dds, 'DDS', Icons.groups_outlined);
    addRecords(trainingSessions, 'Treinamento realizado', Icons.workspace_premium_outlined);
    addRecords(improvements, 'Melhoria', Icons.auto_awesome_outlined);

    return hits.take(80).toList(growable: false);
  }

  Future<void> _open(_SearchHit hit) async {
    Widget destination;
    switch (hit.kind) {
      case 'Empresa':
        destination = CompanyDetailScreen(company: hit.company!);
        break;
      case 'Trabalhador':
        destination = WorkersScreen(companyId: hit.companyId);
        break;
      case 'Treinamento':
        destination = TrainingsScreen(companyId: hit.companyId);
        break;
      case 'Vistoria':
        destination = const HistoryScreen();
        break;
      default:
        if (hit.company != null) {
          destination = CompanyDetailScreen(company: hit.company!);
        } else {
          destination = const HistoryScreen();
        }
    }
    await Navigator.of(context).push(MaterialPageRoute(builder: (_) => destination));
  }

  @override
  Widget build(BuildContext context) {
    final hits = _hits();
    return Scaffold(
      appBar: AppBar(title: const Text('Pesquisa global')),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            TextField(
              controller: queryController,
              autofocus: true,
              onChanged: (value) => setState(() => query = value),
              decoration: InputDecoration(
                labelText: 'Pesquisar no Auditar SST',
                hintText: 'Empresa, trabalhador, NR, treinamento, DDS, vistoria...',
                prefixIcon: const Icon(Icons.search_rounded),
                suffixIcon: query.isEmpty
                    ? null
                    : IconButton(
                        tooltip: 'Limpar',
                        onPressed: () {
                          queryController.clear();
                          setState(() => query = '');
                        },
                        icon: const Icon(Icons.close_rounded),
                      ),
                border: const OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 10),
            const Text(
              'A pesquisa é feita somente nos dados disponíveis neste aparelho.',
              style: TextStyle(fontSize: 11.5, color: Colors.black54),
            ),
            const SizedBox(height: 14),
            if (loading)
              const Center(child: Padding(
                padding: EdgeInsets.all(24),
                child: CircularProgressIndicator(),
              ))
            else if (error.isNotEmpty)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      Text(error, textAlign: TextAlign.center),
                      const SizedBox(height: 10),
                      FilledButton.icon(
                        onPressed: _load,
                        icon: const Icon(Icons.refresh_rounded),
                        label: const Text('Tentar novamente'),
                      ),
                    ],
                  ),
                ),
              )
            else if (query.trim().length < 2)
              const Card(
                child: Padding(
                  padding: EdgeInsets.all(18),
                  child: Text(
                    'Digite pelo menos 2 caracteres. Você pode procurar por empresa, trabalhador, função, NR, treinamento, DDS, vistoria, situação de segurança ou melhoria.',
                  ),
                ),
              )
            else if (hits.isEmpty)
              const Card(
                child: Padding(
                  padding: EdgeInsets.all(18),
                  child: Text('Nenhum registro encontrado para esta pesquisa.'),
                ),
              )
            else ...[
              Text(
                '${hits.length} resultado(s)',
                style: const TextStyle(
                  color: AuditarBrand.navy,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 8),
              for (final hit in hits)
                Card(
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: AuditarBrand.greenSoft,
                      foregroundColor: AuditarBrand.greenDark,
                      child: Icon(hit.icon),
                    ),
                    title: Text(hit.title, maxLines: 2, overflow: TextOverflow.ellipsis),
                    subtitle: Text(
                      [hit.kind, hit.subtitle].where((e) => e.trim().isNotEmpty).join('\n'),
                    ),
                    trailing: const Icon(Icons.chevron_right_rounded),
                    onTap: () => _open(hit),
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }
}

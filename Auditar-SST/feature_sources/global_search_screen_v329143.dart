import 'package:flutter/material.dart';

import '../brand.dart';
import '../database.dart';
import '../models.dart';
import '../services/auth_service.dart';
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

  /// A vistoria sem ID só pode ser ligada a uma empresa autorizada com nome único.
  static Company? _inspectionCompany(
      Map<String,Object?> row,List<Company> authorized){
    final raw=(row['company_id']??row['companyId']??'').toString().trim();
    if(raw.isNotEmpty){
      for(final c in authorized){if(c.id==raw)return c;}
      return null;
    }
    final name=(row['company_name']??'').toString().trim().toLowerCase();
    if(name.isEmpty)return null;
    final matches=authorized.where((c)=>c.name.trim().toLowerCase()==name)
      .take(2).toList();
    return matches.length==1?matches.single:null;
  }

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
      final userId=AuthService.currentUser?.id;
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
      if(!mounted||userId!=AuthService.currentUser?.id)return;
      final accessibleCompanies=(values[0] as List<Company>)
        .where((c)=>c.active&&AuthService.canAccessCompany(c.id)).toList();
      final allowedIds=accessibleCompanies.map((c)=>c.id).toSet();
      final accessibleWorkers=(values[1] as List<Worker>)
        .where((w)=>allowedIds.contains(w.companyId)).toList();
      final allowedWorkers=accessibleWorkers.map((w)=>w.id).toSet();
      List<SstRecord> accessibleRecords(Object rows)=>
        (rows as List<SstRecord>).where((r)=>r.companyId==null?
          AuthService.isAdmin:allowedIds.contains(r.companyId)).toList();
      setState(() {
        companies=accessibleCompanies;
        workers=accessibleWorkers;
        trainings=(values[2] as List<TrainingControl>)
          .where((t)=>allowedWorkers.contains(t.workerId)).toList();
        inspections=(values[3] as List<Map<String,Object?>>)
          .where((row)=>_inspectionCompany(row,accessibleCompanies)!=null)
          .toList();
        safety=accessibleRecords(values[4]);
        dds=accessibleRecords(values[5]);
        trainingSessions=accessibleRecords(values[6]);
        improvements=accessibleRecords(values[7]);
        loading=false;
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
      final company=_inspectionCompany(row,companies);
      if(company==null||!AuthService.canAccessCompany(company.id))continue;
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
          companyId:company.id,
          company:company,
        ));
      }
    }

    void addRecords(List<SstRecord> records, String kind, IconData icon) {
      for (final record in records) {
        if(record.companyId==null?!AuthService.isAdmin:
            !AuthService.canAccessCompany(record.companyId!))continue;
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
    if(hit.companyId==null?!AuthService.isAdmin:
        !AuthService.canAccessCompany(hit.companyId!)){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content:Text('Acesso à empresa não autorizado.')));
      return;
    }
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
        destination = HistoryScreen(companyId:hit.companyId);
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

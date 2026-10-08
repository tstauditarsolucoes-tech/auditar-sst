import 'package:flutter/material.dart';

import '../database.dart';
import '../models.dart';
import '../services/auth_service.dart';
import '../widgets/company_organization.dart';
import 'companies_screen.dart';
import 'company_detail_screen.dart';
import 'express_round_screen.dart';
import 'new_inspection_screen.dart';
import 'history_screen.dart';
import 'field_operational_control_screen.dart';
import 'manager_reports_screen.dart';
import 'safety_observations_screen.dart';

enum VisitIntent { visit, drafts, pending, reports }

List<Company> quickVisitCompanies(
  List<Company> companies,
  CompanyOrganization organization, {
  String query = '',
  String? group,
  bool favorites = false,
  bool recent = false,
  required bool Function(String) canAccess,
}) {
  final q = CompanyOrganization.normalized(query);
  final result = companies
      .where(
        (c) =>
            c.active &&
            canAccess(c.id) &&
            (group == null || organization.group(c.id) == group) &&
            (!favorites || organization.favorite(c.id)) &&
            (!recent || organization.lastVisit(c.id).isNotEmpty) &&
            (q.isEmpty ||
                [
                  c.name,
                  c.cnpj ?? '',
                  c.city ?? '',
                  organization.alias(c.id),
                  organization.group(c.id),
                ].any((s) => CompanyOrganization.normalized(s).contains(q))),
      )
      .toList();
  result.sort((a, b) {
    final favorite =
        (organization.favorite(b.id) ? 1 : 0) -
        (organization.favorite(a.id) ? 1 : 0);
    if (favorite != 0) return favorite;
    final visited = organization
        .lastVisit(b.id)
        .compareTo(organization.lastVisit(a.id));
    return visited != 0
        ? visited
        : a.name.toLowerCase().compareTo(b.name.toLowerCase());
  });
  return result;
}

class VisitStartPanel extends StatelessWidget {
  const VisitStartPanel({
    super.key,
    required this.onOpen,
    required this.onMore,
    this.companyName,
    this.onChange,
  });
  final ValueChanged<VisitIntent> onOpen;
  final VoidCallback onMore;
  final String? companyName;
  final VoidCallback? onChange;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.all(16),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'Seu trabalho de hoje',
          style: Theme.of(context).textTheme.headlineSmall
              ?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        if (companyName != null)
          Card(
            child: ListTile(
              leading: const Icon(Icons.business_outlined),
              title: Text(
                companyName!,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              subtitle: const Text('Empresa / obra selecionada'),
              trailing: TextButton(
                onPressed: onChange,
                child: const Text('Trocar'),
              ),
            ),
          )
        else
          const Text('Escolha uma tarefa e a empresa ou obra que vai atender.'),
        const SizedBox(height: 16),
        FilledButton.icon(
          key: const Key('start-visit'),
          onPressed: () => onOpen(VisitIntent.visit),
          style: FilledButton.styleFrom(padding: const EdgeInsets.all(20)),
          icon: const Icon(Icons.add_location_alt_outlined),
          label: const Text('Iniciar visita'),
        ),
        const SizedBox(height: 10),
        OutlinedButton.icon(
          onPressed: () => onOpen(VisitIntent.drafts),
          style: OutlinedButton.styleFrom(padding: const EdgeInsets.all(18)),
          icon: const Icon(Icons.edit_note),
          label: const Text('Continuar rascunho'),
        ),
        const SizedBox(height: 10),
        OutlinedButton.icon(
          onPressed: () => onOpen(VisitIntent.pending),
          style: OutlinedButton.styleFrom(padding: const EdgeInsets.all(18)),
          icon: const Icon(Icons.task_alt),
          label: const Text('Pendências'),
        ),
        const SizedBox(height: 10),
        OutlinedButton.icon(
          onPressed: () => onOpen(VisitIntent.reports),
          style: OutlinedButton.styleFrom(padding: const EdgeInsets.all(18)),
          icon: const Icon(Icons.description_outlined),
          label: const Text('Relatórios'),
        ),
        const SizedBox(height: 16),
        TextButton.icon(
          onPressed: onMore,
          icon: const Icon(Icons.apps),
          label: const Text('Mais opções'),
        ),
      ],
    ),
  );
}

class QuickVisitScreen extends StatefulWidget {
  const QuickVisitScreen({
    super.key,
    this.initialCompany,
    this.intent = VisitIntent.visit,
    this.onSelected,
  });
  final Company? initialCompany;
  final VisitIntent intent;
  final ValueChanged<Company>? onSelected;
  @override
  State<QuickVisitScreen> createState() => _QuickVisitScreenState();
}

class _QuickVisitScreenState extends State<QuickVisitScreen> {
  final _search = TextEditingController();
  List<Company> _companies = [];
  CompanyOrganization _organization = CompanyOrganization();
  Company? _selected;
  bool _loading = true;
  bool _favorites = false;
  bool _recent = false;
  bool _opening = false;
  String? _group;
  String? _error;
  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final companies = await AppDatabase.instance.getCompanies();
      CompanyOrganization organization;
      try {
        organization = await CompanyOrganization.load();
      } catch (_) {
        organization = CompanyOrganization();
      }
      if (!mounted) return;
      final initialId = (_selected ?? widget.initialCompany)?.id;
      setState(() {
        _companies = companies
            .where((c) => c.active && AuthService.canAccessCompany(c.id))
            .toList();
        _organization = organization;
        _selected = _companies.where((c) => c.id == initialId).firstOrNull;
        _loading = false;
        _error = null;
      });
    } catch (_) {
      if (mounted)
        setState(() {
          _loading = false;
          _error = 'Não foi possível carregar as empresas. Tente novamente.';
        });
    }
  }

  void _select(Company company) {
    if (!AuthService.canAccessCompany(company.id)) return;
    setState(() => _selected = company);
    widget.onSelected?.call(company);
  }

  Future<void> _open(Widget page) async {
    final company = _selected;
    if (_opening ||
        company == null ||
        !AuthService.canAccessCompany(company.id))
      return;
    setState(() => _opening = true);
    // Marcar recentes não pode atrasar a abertura nem impedir a visita.
    _organization.markVisited(company.id).catchError((Object _) {});
    try {
      await Navigator.of(context).push(MaterialPageRoute(builder: (_) => page));
    } finally {
      if (mounted) setState(() => _opening = false);
    }
  }

  Widget _action(
    String title,
    String detail,
    IconData icon,
    Widget page,
  ) => Card(
    child: ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      leading: Icon(icon),
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
      subtitle: Text(detail),
      trailing: const Icon(Icons.chevron_right),
      onTap: _opening ? null : () => _open(page),
    ),
  );
  Future<void> _recordObservation() async {
    final c = _selected;
    if (c == null || _opening || !AuthService.canAccessCompany(c.id)) return;
    try {
      final sectors = await AppDatabase.instance.getSectors(c.id);
      if (!mounted || _selected?.id != c.id) return;
      await _open(SafetyObservationFormScreen(company: c, sectors: sectors));
    } catch (_) {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'Não foi possível abrir o registro. Tente novamente.',
            ),
          ),
        );
    }
  }

  Widget _tasks() {
    final c = _selected!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          child: ListTile(
            leading: const Icon(Icons.business_outlined),
            title: Text(
              c.name,
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            subtitle: Text(
              [
                _organization.alias(c.id),
                _organization.group(c.id),
                c.city ?? '',
              ].where((s) => s.isNotEmpty).join(' • '),
            ),
            trailing: TextButton(
              onPressed: _opening
                  ? null
                  : () => setState(() => _selected = null),
              child: const Text('Trocar'),
            ),
          ),
        ),
        const SizedBox(height: 12),
        if (widget.intent == VisitIntent.visit) ...[
          _action(
            'Nova ronda',
            'Fotos e descrição das situações encontradas',
            Icons.add_a_photo_outlined,
            ExpressRoundScreen(company: c),
          ),
          _action(
            'Nova vistoria',
            'Inspeção com checklist da empresa selecionada',
            Icons.fact_check_outlined,
            NewInspectionScreen(initialCompany: c, fieldMode: true),
          ),
          Card(
            child: ListTile(
              leading: const Icon(Icons.warning_amber_outlined),
              title: const Text('Registrar não conformidade'),
              subtitle: const Text('Abrir o formulário de registro'),
              trailing: const Icon(Icons.chevron_right),
              onTap: _opening ? null : _recordObservation,
            ),
          ),
          _action(
            'Pendências da empresa',
            'Ações, não conformidades e vencimentos',
            Icons.task_alt,
            FieldOperationalControlScreen(initialCompanyId: c.id),
          ),
        ],
        if (widget.intent == VisitIntent.drafts) ...[
          const Text(
            'Escolha o tipo de trabalho que deseja retomar. A Ronda usa a recuperação de rascunhos já existente.',
          ),
          _action(
            'Continuar ronda',
            'Abrir a ronda e recuperar o rascunho disponível',
            Icons.edit_note,
            ExpressRoundScreen(company: c),
          ),
          _action(
            'Vistorias em andamento',
            'Consultar o histórico e abrir a vistoria',
            Icons.fact_check_outlined,
            HistoryScreen(companyId: c.id),
          ),
        ],
        if (widget.intent == VisitIntent.pending)
          _action(
            'Ver pendências',
            'Ações, não conformidades e treinamentos',
            Icons.task_alt,
            FieldOperationalControlScreen(initialCompanyId: c.id),
          ),
        if (widget.intent == VisitIntent.reports) ...[
          _action(
            'Relatórios de vistoria',
            'Abrir uma vistoria para revisar e gerar o PDF',
            Icons.description_outlined,
            HistoryScreen(companyId: c.id),
          ),
          _action(
            'Relatórios gerenciais',
            'Pendências e acompanhamento da empresa',
            Icons.analytics_outlined,
            ManagerReportsScreen(company: c),
          ),
          _action(
            'Relatório da ronda',
            'Abrir os registros da ronda e emitir o relatório',
            Icons.photo_library_outlined,
            ExpressRoundScreen(company: c),
          ),
        ],
        const SizedBox(height: 12),
        _action(
          'Mais opções da empresa',
          'Trabalhadores, DDS, treinamentos, CIPA e documentos',
          Icons.apps,
          CompanyDetailScreen(company: c),
        ),
      ],
    );
  }

  Widget _picker() {
    final visible = quickVisitCompanies(
      _companies,
      _organization,
      query: _search.text,
      group: _group,
      favorites: _favorites,
      recent: _recent,
      canAccess: AuthService.canAccessCompany,
    );
    final groups =
        _companies.map((c) => _organization.group(c.id)).toSet().toList()
          ..sort();
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextField(
                controller: _search,
                onChanged: (_) => setState(() {}),
                decoration: InputDecoration(
                  labelText: 'Buscar empresa, obra ou grupo',
                  prefixIcon: const Icon(Icons.search),
                  suffixIcon: _search.text.isEmpty
                      ? null
                      : IconButton(
                          tooltip: 'Limpar busca',
                          onPressed: () {
                            _search.clear();
                            setState(() {});
                          },
                          icon: const Icon(Icons.close),
                        ),
                  border: const OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 8),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    FilterChip(
                      label: const Text('Favoritas'),
                      selected: _favorites,
                      onSelected: (v) => setState(() => _favorites = v),
                    ),
                    const SizedBox(width: 8),
                    FilterChip(
                      label: const Text('Recentes'),
                      selected: _recent,
                      onSelected: (v) => setState(() => _recent = v),
                    ),
                    const SizedBox(width: 8),
                    PopupMenuButton<String>(
                      tooltip: 'Filtrar por grupo',
                      onSelected: (value) =>
                          setState(() => _group = value == '*' ? null : value),
                      itemBuilder: (_) => [
                        const PopupMenuItem(
                          value: '*',
                          child: Text('Todos os grupos'),
                        ),
                        ...groups.map(
                          (g) => PopupMenuItem(
                            value: g,
                            child: Text(g.isEmpty ? 'Sem grupo' : g),
                          ),
                        ),
                      ],
                      child: Chip(
                        avatar: const Icon(Icons.folder_outlined),
                        label: Text(
                          _group == null
                              ? 'Todos os grupos'
                              : _group!.isEmpty
                              ? 'Sem grupo'
                              : _group!,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        Expanded(
          child: visible.isEmpty
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text('Nenhuma empresa encontrada.'),
                      TextButton(
                        onPressed: () {
                          _search.clear();
                          setState(() {
                            _favorites = false;
                            _recent = false;
                            _group = null;
                          });
                        },
                        child: const Text('Limpar filtros'),
                      ),
                    ],
                  ),
                )
              : ListView.builder(
                  itemCount: visible.length,
                  itemBuilder: (_, i) {
                    final c = visible[i];
                    return ListTile(
                      key: ValueKey('visit-company-${c.id}'),
                      leading: Icon(
                        _organization.favorite(c.id)
                            ? Icons.star
                            : Icons.business_outlined,
                      ),
                      title: Text(
                        _organization.alias(c.id).isEmpty
                            ? c.name
                            : _organization.alias(c.id),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      subtitle: Text(
                        [
                          if (_organization.alias(c.id).isNotEmpty) c.name,
                          _organization.group(c.id).isEmpty
                              ? 'Sem grupo'
                              : _organization.group(c.id),
                          c.city ?? '',
                        ].where((s) => s.isNotEmpty).join(' • '),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => _select(c),
                    );
                  },
                ),
        ),
        SafeArea(
          top: false,
          child: TextButton.icon(
            onPressed: () async {
              await Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const CompaniesScreen()),
              );
              if (mounted) await _load();
            },
            icon: const Icon(Icons.business_outlined),
            label: const Text('Cadastrar ou organizar empresas'),
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(
      title: Text(
        _selected == null
            ? 'Escolher empresa / obra'
            : switch (widget.intent) {
                VisitIntent.visit => 'Visita',
                VisitIntent.drafts => 'Continuar rascunho',
                VisitIntent.pending => 'Pendências',
                VisitIntent.reports => 'Relatórios',
              },
      ),
    ),
    body: _loading
        ? const Center(child: CircularProgressIndicator())
        : _error != null
        ? Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(_error!),
                TextButton(
                  onPressed: _load,
                  child: const Text('Tentar novamente'),
                ),
              ],
            ),
          )
        : Align(
            alignment: Alignment.topCenter,
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 1000),
              child: _selected == null ? _picker() : _tasks(),
            ),
          ),
  );
}

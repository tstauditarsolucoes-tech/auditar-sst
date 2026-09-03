import 'package:flutter/material.dart';

import '../brand.dart';
import '../database.dart';
import '../widgets/auditar_brand_logo.dart';
import '../widgets/responsive_wrap.dart';
import 'action_plan_screen.dart';
import 'checklist_templates_screen.dart';
import 'cipa_screen.dart';
import 'companies_screen.dart';
import 'compliance_alerts_screen.dart';
import 'dashboard_screen.dart';
import 'history_screen.dart';
import 'improvements_screen.dart';
import 'new_inspection_screen.dart';
import 'non_conformities_screen.dart';
import 'routine_hub_screen.dart';
import 'settings_screen.dart';
import 'trainings_screen.dart';
import 'workers_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ScrollController _mobileScrollController = ScrollController();
  final GlobalKey _modulesKey = GlobalKey();

  Map<String, int> summary = {};
  Map<String, int> routineSummary = {};
  int openNcs = 0;
  bool loading = true;

  List<_ModuleData> get _modules => [
        _ModuleData(
          title: 'Empresas',
          subtitle: 'Cadastros, obras, setores e controles por empresa',
          icon: Icons.business_outlined,
          color: AuditarBrand.navy,
          page: () => const CompaniesScreen(),
        ),
        _ModuleData(
          title: 'Vistorias',
          subtitle: 'Histórico, relatórios e vistorias em andamento',
          icon: Icons.fact_check_outlined,
          color: AuditarBrand.info,
          page: () => const HistoryScreen(),
        ),
        _ModuleData(
          title: 'Não conformidades',
          subtitle: 'Pendências identificadas durante as inspeções',
          icon: Icons.warning_amber_rounded,
          color: AuditarBrand.danger,
          page: () => const NonConformitiesScreen(),
        ),
        _ModuleData(
          title: 'Planos de ação',
          subtitle: 'Responsáveis, prazos, correções e acompanhamento',
          icon: Icons.assignment_turned_in_outlined,
          color: AuditarBrand.warning,
          page: () => const ActionPlanScreen(),
        ),
        _ModuleData(
          title: 'Trabalhadores',
          subtitle: 'Cadastro, função, setor e importação de listas',
          icon: Icons.groups_rounded,
          color: const Color(0xFF3766A6),
          page: () => const WorkersScreen(),
        ),
        _ModuleData(
          title: 'Treinamentos',
          subtitle: 'NRs em dia, pendentes, vencidas e obrigatórias',
          icon: Icons.school_outlined,
          color: const Color(0xFF8356B8),
          page: () => const TrainingsScreen(),
        ),
        _ModuleData(
          title: 'Alertas e obrigações',
          subtitle: 'Registros obrigatórios, exames e vencimentos',
          icon: Icons.notification_important_outlined,
          color: AuditarBrand.danger,
          page: () => const ComplianceAlertsScreen(),
        ),
        _ModuleData(
          title: 'CIPA',
          subtitle: 'Eleições, candidatos, QR Code e votação',
          icon: Icons.how_to_vote_outlined,
          color: const Color(0xFF7252A5),
          page: () => const CipaScreen(),
        ),
        _ModuleData(
          title: 'Biblioteca de checklists',
          subtitle: 'Modelos prontos e perguntas organizadas por NR',
          icon: Icons.library_add_check_outlined,
          color: AuditarBrand.greenDark,
          page: () => const ChecklistTemplatesScreen(),
        ),
        _ModuleData(
          title: 'Rotina SST',
          subtitle: 'Agenda, DDS, APR/PT, incidentes e equipamentos',
          icon: Icons.dashboard_customize_outlined,
          color: const Color(0xFF2B7A78),
          page: () => const RoutineHubScreen(),
        ),
        _ModuleData(
          title: 'Melhorias',
          subtitle: 'Sugestões e melhorias realizadas por empresa e setor',
          icon: Icons.auto_awesome_outlined,
          color: const Color(0xFF16836B),
          page: () => const ImprovementsScreen(),
        ),
        _ModuleData(
          title: 'Indicadores',
          subtitle: 'Desempenho, evolução, filtros e prioridades',
          icon: Icons.bar_chart_rounded,
          color: AuditarBrand.info,
          page: () => const DashboardScreen(),
        ),
      ];

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  @override
  void dispose() {
    _mobileScrollController.dispose();
    super.dispose();
  }

  Future<void> _refresh() async {
    final result = await AppDatabase.instance.getDashboardSummary();
    final ncRows = await AppDatabase.instance.getNonConformityRows(
      includeClosed: false,
    );
    final routine = await AppDatabase.instance.getRoutineTodaySummary();

    if (!mounted) return;
    setState(() {
      summary = result;
      routineSummary = routine;
      openNcs = ncRows.length;
      loading = false;
    });
  }

  Future<void> _open(Widget page) async {
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => page),
    );
    await _refresh();
  }

  Future<void> _showModules() async {
    final sectionContext = _modulesKey.currentContext;
    if (sectionContext != null) {
      await Scrollable.ensureVisible(
        sectionContext,
        duration: const Duration(milliseconds: 350),
        curve: Curves.easeOut,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 16,
        title: const AuditarBrandLogo(
          compact: true,
          onDark: true,
          iconSize: 34,
        ),
        actions: [
          IconButton(
            tooltip: 'Atualizar dados',
            onPressed: _refresh,
            icon: const Icon(Icons.refresh_rounded),
          ),
          IconButton(
            tooltip: 'Configurações',
            onPressed: () => _open(const SettingsScreen()),
            icon: const Icon(Icons.settings_outlined),
          ),
        ],
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : LayoutBuilder(
              builder: (context, constraints) {
                if (constraints.maxWidth >= 900) {
                  return _desktopBody();
                }
                return _mobileBody();
              },
            ),
      bottomNavigationBar: MediaQuery.sizeOf(context).width < 900
          ? NavigationBar(
              selectedIndex: 0,
              onDestinationSelected: (index) {
                if (index == 1) {
                  _open(const CompaniesScreen());
                } else if (index == 2) {
                  _open(const HistoryScreen());
                } else if (index == 3) {
                  _showModules();
                }
              },
              destinations: const [
                NavigationDestination(
                  icon: Icon(Icons.home_outlined),
                  selectedIcon: Icon(Icons.home_rounded),
                  label: 'Início',
                ),
                NavigationDestination(
                  icon: Icon(Icons.business_outlined),
                  selectedIcon: Icon(Icons.business),
                  label: 'Empresas',
                ),
                NavigationDestination(
                  icon: Icon(Icons.fact_check_outlined),
                  selectedIcon: Icon(Icons.fact_check),
                  label: 'Vistorias',
                ),
                NavigationDestination(
                  icon: Icon(Icons.apps_rounded),
                  label: 'Módulos',
                ),
              ],
            )
          : null,
    );
  }

  Widget _mobileBody() {
    return RefreshIndicator(
      onRefresh: _refresh,
      child: ListView(
        controller: _mobileScrollController,
        padding: const EdgeInsets.fromLTRB(14, 14, 14, 28),
        children: [
          _overviewPanel(desktop: false),
          const SizedBox(height: 12),
          _newInspectionButton(),
          const SizedBox(height: 18),
          _sectionHeader(
            'Coleta em campo',
            'Acessos principais para usar durante a visita',
          ),
          const SizedBox(height: 10),
          _moduleWrap(_modules.take(4).toList(), minWidth: 145, maxColumns: 2),
          const SizedBox(height: 20),
          _routinePanel(),
          const SizedBox(height: 22),
          Container(
            key: _modulesKey,
            child: _sectionHeader(
              'Todos os módulos',
              'As funções voltaram a ficar visíveis, sem menus escondidos',
            ),
          ),
          const SizedBox(height: 10),
          _moduleWrap(_modules.skip(4).toList(), minWidth: 145, maxColumns: 2),
          const SizedBox(height: 12),
          _companyResourcesCard(),
          const SizedBox(height: 18),
          const Center(
            child: Text(
              'Auditar SST • versão 3.21.1',
              style: TextStyle(fontSize: 10.5, color: Colors.black45),
            ),
          ),
        ],
      ),
    );
  }

  Widget _desktopBody() {
    return Row(
      children: [
        Container(
          width: 292,
          decoration: const BoxDecoration(
            color: Colors.white,
            border: Border(right: BorderSide(color: AuditarBrand.line)),
          ),
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(14, 16, 14, 10),
                child: SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: () => _open(const NewInspectionScreen()),
                    icon: const Icon(Icons.add_a_photo_outlined),
                    label: const Text('Nova vistoria'),
                  ),
                ),
              ),
              const Padding(
                padding: EdgeInsets.fromLTRB(18, 8, 18, 8),
                child: Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    'NAVEGAÇÃO COMPLETA',
                    style: TextStyle(
                      color: AuditarBrand.neutral,
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      letterSpacing: .5,
                    ),
                  ),
                ),
              ),
              Expanded(
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(8, 0, 8, 12),
                  children: [
                    for (final module in _modules)
                      ListTile(
                        dense: true,
                        leading: Icon(module.icon, color: module.color),
                        title: Text(
                          module.title,
                          style: const TextStyle(fontWeight: FontWeight.w700),
                        ),
                        onTap: () => _open(module.page()),
                      ),
                    const Divider(),
                    ListTile(
                      dense: true,
                      leading: const Icon(Icons.settings_outlined),
                      title: const Text(
                        'Configurações e sincronização',
                        style: TextStyle(fontWeight: FontWeight.w700),
                      ),
                      onTap: () => _open(const SettingsScreen()),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        Expanded(
          child: RefreshIndicator(
            onRefresh: _refresh,
            child: ListView(
              padding: const EdgeInsets.fromLTRB(24, 22, 24, 32),
              children: [
                Row(
                  children: [
                    const Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Central de gestão SST',
                            style: TextStyle(
                              color: AuditarBrand.navy,
                              fontSize: 26,
                              fontWeight: FontWeight.w900,
                            ),
                          ),
                          SizedBox(height: 4),
                          Text(
                            'Visão completa para organizar empresas, registros e resultados.',
                            style: TextStyle(color: AuditarBrand.neutral),
                          ),
                        ],
                      ),
                    ),
                    OutlinedButton.icon(
                      onPressed: () => _open(const SettingsScreen()),
                      icon: const Icon(Icons.sync_rounded),
                      label: const Text('Sincronização'),
                    ),
                  ],
                ),
                const SizedBox(height: 18),
                _overviewPanel(desktop: true),
                const SizedBox(height: 22),
                _sectionHeader(
                  'Ações principais',
                  'Acesse diretamente o que precisa acompanhar ou editar',
                ),
                const SizedBox(height: 10),
                _moduleWrap(_modules.take(4).toList(), minWidth: 210, maxColumns: 4),
                const SizedBox(height: 22),
                _routinePanel(),
                const SizedBox(height: 22),
                _sectionHeader(
                  'Gestão completa',
                  'Cadastros, controles, CIPA, checklists e indicadores',
                ),
                const SizedBox(height: 10),
                _moduleWrap(_modules.skip(4).toList(), minWidth: 230, maxColumns: 3),
                const SizedBox(height: 12),
                _companyResourcesCard(),
                const SizedBox(height: 20),
                const Center(
                  child: Text(
                    'Auditar SST para Windows • versão 3.21.1',
                    style: TextStyle(fontSize: 11, color: Colors.black45),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _overviewPanel({required bool desktop}) {
    final inspections = summary['inspections'] ?? 0;
    final conformity = summary['conformity'] ?? 0;
    final pending = summary['pending'] ?? 0;
    final overdue = summary['ncOverdue'] ?? 0;

    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: EdgeInsets.all(desktop ? 20 : 15),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Expanded(
                  child: Text(
                    'Visão geral',
                    style: TextStyle(
                      color: AuditarBrand.navy,
                      fontSize: 18,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ),
                Text(
                  '$conformity% conforme',
                  style: TextStyle(
                    color: conformity >= 80
                        ? AuditarBrand.greenDark
                        : AuditarBrand.warning,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ResponsiveWrap(
              minItemWidth: desktop ? 150 : 125,
              maxColumns: desktop ? 5 : 2,
              children: [
                _metric('Vistorias', inspections, Icons.fact_check_outlined, AuditarBrand.info),
                _metric('NCs abertas', openNcs, Icons.warning_amber_rounded, AuditarBrand.danger),
                _metric('Ações pendentes', pending, Icons.assignment_outlined, AuditarBrand.warning),
                _metric('Ações vencidas', overdue, Icons.event_busy_outlined, AuditarBrand.danger),
                _metric('Conformidade', conformity, Icons.verified_outlined, AuditarBrand.greenDark, suffix: '%'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _metric(
    String label,
    int value,
    IconData icon,
    Color color, {
    String suffix = '',
  }) {
    return Container(
      constraints: const BoxConstraints(minHeight: 76),
      padding: const EdgeInsets.all(11),
      decoration: BoxDecoration(
        color: color.withValues(alpha: .07),
        borderRadius: BorderRadius.circular(13),
        border: Border.all(color: color.withValues(alpha: .16)),
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 24),
          const SizedBox(width: 9),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  '$value$suffix',
                  style: TextStyle(
                    color: color,
                    fontSize: 21,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                Text(
                  label,
                  style: const TextStyle(
                    fontSize: 11,
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

  Widget _newInspectionButton() {
    return SizedBox(
      width: double.infinity,
      child: FilledButton.icon(
        onPressed: () => _open(const NewInspectionScreen()),
        icon: const Icon(Icons.add_a_photo_outlined),
        label: const Text('Iniciar nova vistoria'),
      ),
    );
  }

  Widget _routinePanel() {
    final agenda = routineSummary['agendaToday'] ?? 0;
    final training = routineSummary['trainingsDue'] ?? 0;
    final missing = routineSummary['missingRequiredTrainings'] ?? 0;
    final equipment = routineSummary['equipmentDue'] ?? 0;

    return Card(
      margin: EdgeInsets.zero,
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => _open(const RoutineHubScreen()),
        child: Padding(
          padding: const EdgeInsets.all(15),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Row(
                children: [
                  Icon(Icons.today_outlined, color: AuditarBrand.navy),
                  SizedBox(width: 9),
                  Expanded(
                    child: Text(
                      'Resumo da rotina SST',
                      style: TextStyle(
                        color: AuditarBrand.navy,
                        fontSize: 17,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ),
                  Icon(Icons.chevron_right_rounded),
                ],
              ),
              const SizedBox(height: 11),
              Wrap(
                spacing: 7,
                runSpacing: 7,
                children: [
                  _statusChip('Agenda hoje', agenda),
                  _statusChip('Treinamentos', training),
                  _statusChip('Sem registro', missing),
                  _statusChip('Equipamentos', equipment),
                ],
              ),
              const SizedBox(height: 9),
              const Text(
                'Inclui Agenda, DDS, APR/PT, acidentes, incidentes e máquinas.',
                style: TextStyle(fontSize: 12, color: AuditarBrand.neutral),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _statusChip(String label, int value) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(
        color: value > 0 ? const Color(0xFFFFF4E1) : AuditarBrand.greenSoft,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        '$label: $value',
        style: TextStyle(
          color: value > 0 ? const Color(0xFF9A5A00) : AuditarBrand.greenDark,
          fontSize: 11,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }

  Widget _moduleWrap(
    List<_ModuleData> modules, {
    required double minWidth,
    required int maxColumns,
  }) {
    return ResponsiveWrap(
      minItemWidth: minWidth,
      maxColumns: maxColumns,
      spacing: 9,
      runSpacing: 9,
      children: modules.map(_moduleCard).toList(growable: false),
    );
  }

  Widget _moduleCard(_ModuleData module) {
    return Card(
      margin: EdgeInsets.zero,
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () => _open(module.page()),
        child: ConstrainedBox(
          constraints: const BoxConstraints(minHeight: 112),
          child: Padding(
            padding: const EdgeInsets.all(13),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 39,
                  height: 39,
                  decoration: BoxDecoration(
                    color: module.color.withValues(alpha: .10),
                    borderRadius: BorderRadius.circular(11),
                  ),
                  child: Icon(module.icon, color: module.color, size: 22),
                ),
                const SizedBox(height: 9),
                Text(
                  module.title,
                  style: const TextStyle(
                    color: AuditarBrand.navy,
                    fontSize: 14,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  module.subtitle,
                  style: const TextStyle(
                    color: AuditarBrand.neutral,
                    fontSize: 11,
                    height: 1.25,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _companyResourcesCard() {
    return Card(
      margin: EdgeInsets.zero,
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
        leading: Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            color: AuditarBrand.navySoft,
            borderRadius: BorderRadius.circular(12),
          ),
          child: const Icon(Icons.domain_outlined, color: AuditarBrand.navy),
        ),
        title: const Text(
          'Recursos dentro de cada empresa',
          style: TextStyle(fontWeight: FontWeight.w900),
        ),
        subtitle: const Text(
          'Obras, setores, extintores, atos e condições, documentos e painel gerencial.',
          style: TextStyle(fontSize: 11.5),
        ),
        trailing: const Icon(Icons.chevron_right_rounded),
        onTap: () => _open(const CompaniesScreen()),
      ),
    );
  }

  Widget _sectionHeader(String title, String subtitle) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            color: AuditarBrand.navy,
            fontSize: 18,
            fontWeight: FontWeight.w900,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          subtitle,
          style: const TextStyle(color: AuditarBrand.neutral, fontSize: 12),
        ),
      ],
    );
  }
}

class _ModuleData {
  final String title;
  final String subtitle;
  final IconData icon;
  final Color color;
  final Widget Function() page;

  const _ModuleData({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.color,
    required this.page,
  });
}

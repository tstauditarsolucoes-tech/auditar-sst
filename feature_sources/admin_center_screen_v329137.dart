import 'package:flutter/material.dart';

import '../brand.dart';
import '../database.dart';
import '../services/auth_service.dart';
import '../services/admin_access_policy.dart';
import 'users_screen.dart';
import 'companies_screen.dart';
import 'checklist_templates_screen.dart';
import 'dashboard_screen.dart';
import 'history_screen.dart';

/// A single administrative entry point for Android and Windows.
/// Server-side auth_user_save and auth_users_list still validate the token.
class AuditarAdminCenterScreen extends StatefulWidget {
  const AuditarAdminCenterScreen({super.key});

  @override
  State<AuditarAdminCenterScreen> createState() =>
      _AuditarAdminCenterScreenState();
}

class _AuditarAdminCenterScreenState extends State<AuditarAdminCenterScreen> {
  bool _loading = true;
  String _status = '';
  int? _companyCount;
  int? _userCount;
  int? _clientCount;
  int? _technicianCount;

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  Future<void> _refresh() async {
    if (!AuditarAdminAccess.isAdmin(AuthService.currentUser)) {
      if (mounted) setState(() {
        _loading = false;
        _status = 'Acesso reservado ao administrador Auditar.';
      });
      return;
    }
    setState(() {
      _loading = true;
      _status = '';
    });
    try {
      final accounts = await AuthService.listUsers();
      final companies = await AppDatabase.instance.getCompanies(onlyActive: false);
      if (!mounted) return;
      setState(() {
        _userCount = accounts.where((u) => u.active).length;
        _clientCount =
            accounts.where((u) => u.active && u.role == 'cliente').length;
        _technicianCount =
            accounts.where((u) => u.active && u.role == 'tecnico').length;
        _companyCount = companies.length;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _status = 'Indicadores indisponíveis. Confira a conexão com a Central Online. '
            'Os atalhos administrativos continuam disponíveis.';
      });
    }
  }

  Future<void> _open(Widget screen) async {
    if (!AuditarAdminAccess.isAdmin(AuthService.currentUser)) return;
    await Navigator.of(context).push(MaterialPageRoute(builder: (_) => screen));
    if (mounted) _refresh();
  }

  Widget _metric(String title, int? value, IconData icon) => Expanded(
    child: Container(
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        border: Border.all(color: AuditarBrand.line),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Icon(icon, color: AuditarBrand.greenDark),
        const SizedBox(height: 9),
        Text(_loading ? '—' : value?.toString() ?? '—',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w800, color: AuditarBrand.navy)),
        Text(title, style: const TextStyle(fontSize: 12)),
      ]),
    ),
  );

  Widget _action(
    String title,
    String description,
    IconData icon,
    VoidCallback action,
  ) => Card(
    child: ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 7),
      leading: CircleAvatar(
        backgroundColor: AuditarBrand.greenSoft,
        foregroundColor: AuditarBrand.greenDark,
        child: Icon(icon),
      ),
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
      subtitle: Text(description),
      trailing: const Icon(Icons.chevron_right_rounded),
      onTap: action,
    ),
  );

  @override
  Widget build(BuildContext context) {
    if (!AuditarAdminAccess.isAdmin(AuthService.currentUser)) {
      return Scaffold(
        appBar: AppBar(title: const Text('Administração Auditar')),
        body: const Center(child: Padding(
          padding: EdgeInsets.all(24),
          child: Text('Acesso exclusivo à conta administradora Auditar.'),
        )),
      );
    }
    return Scaffold(
      appBar: AppBar(
        title: const Text('Administração Auditar'),
        actions: [
          IconButton(
            tooltip: 'Atualizar indicadores',
            onPressed: _loading ? null : _refresh,
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Container(
            padding: const EdgeInsets.all(22),
            decoration: BoxDecoration(
              color: AuditarBrand.navy,
              borderRadius: BorderRadius.circular(20),
            ),
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.admin_panel_settings_rounded,
                    color: Colors.white, size: 34),
                SizedBox(height: 12),
                Text('Central Administrativa',
                    style: TextStyle(color: Colors.white, fontSize: 24,
                        fontWeight: FontWeight.w800)),
                SizedBox(height: 6),
                Text('Controle os acessos, empresas e ferramentas da Auditar '
                    'em um único ambiente. Os clientes acessam somente o '
                    'Portal Gerencial autorizado.',
                    style: TextStyle(color: Colors.white, height: 1.4)),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Row(children: [
            _metric('Empresas', _companyCount, Icons.business_outlined),
            const SizedBox(width: 9),
            _metric('Contas ativas', _userCount, Icons.people_outline_rounded),
          ]),
          const SizedBox(height: 9),
          Row(children: [
            _metric('Clientes', _clientCount, Icons.badge_outlined),
            const SizedBox(width: 9),
            _metric('Técnicos', _technicianCount, Icons.engineering_outlined),
          ]),
          if (_loading) const LinearProgressIndicator(),
          if (_status.isNotEmpty) Padding(
            padding: const EdgeInsets.only(top: 10, bottom: 4),
            child: Text(_status, style: TextStyle(
              color: Theme.of(context).colorScheme.error)),
          ),
          const SizedBox(height: 20),
          Text('Contas e permissões',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w800)),
          const SizedBox(height: 8),
          _action('Usuários e acessos',
              'Criar, editar ou desativar contas da Auditar e dos clientes.',
              Icons.manage_accounts_outlined,
              () => _open(const UsersScreen())),
          _action('Acessos ao painel dos clientes',
              'Gerente, diretoria e RH: e-mail, senha, empresa e permissões individuais.',
              Icons.shield_outlined,
              () => _open(const UsersScreen(initialRoleFilter: 'cliente'))),
          _action('Empresas e ambientes',
              'Abrir o cadastro e administrar os acessos individuais de cada empresa.',
              Icons.business_outlined,
              () => _open(const CompaniesScreen())),
          const SizedBox(height: 14),
          Text('Supervisão e ferramentas',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w800)),
          const SizedBox(height: 8),
          _action('Biblioteca de checklists',
              'Acessar os modelos e a organização dos checklists.',
              Icons.library_add_check_outlined,
              () => _open(const ChecklistTemplatesScreen())),
          _action('Indicadores gerenciais',
              'Consultar os indicadores disponíveis no aplicativo.',
              Icons.bar_chart_rounded,
              () => _open(const DashboardScreen())),
          _action('Histórico e relatórios',
              'Consultar as vistorias e relatórios existentes.',
              Icons.description_outlined,
              () => _open(const HistoryScreen())),
          const SizedBox(height: 16),
          const Text('As operações administrativas exigem sessão de '
              'administrador válida na Central Online. Esta área não altera '
              'sincronização, registros técnicos nem o histórico de auditoria.',
              style: TextStyle(fontSize: 12)),
        ],
      ),
    );
  }
}

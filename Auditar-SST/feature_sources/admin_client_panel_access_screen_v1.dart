import 'package:flutter/material.dart';

import '../brand.dart';
import '../database.dart';
import '../models.dart';
import '../services/auth_service.dart';
import '../services/admin_access_policy.dart';
import '../widgets/company_client_access_section.dart';

/// Acesso exclusivo do ADM ao gerenciamento individual dos usuários do
/// Painel do Cliente. Reusa o editor existente por empresa, sem mudar API,
/// autenticação, banco, sincronização ou destinatários de relatórios.
class AuditarClientPanelAccessScreen extends StatefulWidget {
  const AuditarClientPanelAccessScreen({super.key});

  @override
  State<AuditarClientPanelAccessScreen> createState() =>
      _AuditarClientPanelAccessScreenState();
}

class _AuditarClientPanelAccessScreenState
    extends State<AuditarClientPanelAccessScreen> {
  bool _loading = true;
  String _error = '';
  String _search = '';
  List<Company> _companies = const [];

  @override
  void initState() {
    super.initState();
    _loadCompanies();
  }

  Future<void> _loadCompanies() async {
    if (!AuditarAdminAccess.isAdmin(AuthService.currentUser)) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = 'Acesso exclusivo à conta administradora Auditar.';
        });
      }
      return;
    }
    setState(() {
      _loading = true;
      _error = '';
    });
    try {
      final companies =
          await AppDatabase.instance.getCompanies(onlyActive: false);
      companies.sort((a, b) =>
          a.name.toLowerCase().compareTo(b.name.toLowerCase()));
      if (!mounted) return;
      setState(() {
        _companies = companies;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _error = 'Não foi possível carregar as empresas. '
            'Confira os dados locais e tente novamente.';
        _loading = false;
      });
    }
  }

  void _openCompany(Company company) {
    if (!AuditarAdminAccess.isAdmin(AuthService.currentUser)) return;
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => _ClientAccessForCompanyScreen(company: company),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (!AuditarAdminAccess.isAdmin(AuthService.currentUser)) {
      return Scaffold(
        appBar: AppBar(title: const Text('Acessos ao painel dos clientes')),
        body: const Center(
          child: Text('Acesso exclusivo à conta administradora Auditar.'),
        ),
      );
    }

    final term = _search.trim().toLowerCase();
    final filtered = _companies
        .where((company) => company.name.toLowerCase().contains(term))
        .toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Acessos ao painel dos clientes'),
        actions: [
          IconButton(
            tooltip: 'Atualizar empresas',
            onPressed: _loading ? null : _loadCompanies,
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 920),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Selecione a empresa para gerenciar os acessos ao '
                  'Painel do Cliente.',
                  style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Gerente, diretoria e RH podem ter e-mails, senhas e '
                  'permissões individuais para o mesmo painel. '
                  'As contas internas da Auditar permanecem separadas.',
                  style: TextStyle(fontSize: 13, height: 1.4),
                ),
                const SizedBox(height: 16),
                TextField(
                  onChanged: (value) => setState(() => _search = value),
                  decoration: const InputDecoration(
                    prefixIcon: Icon(Icons.search_rounded),
                    hintText: 'Pesquisar empresa',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                ),
                if (_loading) const LinearProgressIndicator(),
                if (_error.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    child: Text(
                      _error,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                      ),
                    ),
                  ),
                const SizedBox(height: 8),
                Expanded(
                  child: _loading
                      ? const Center(child: CircularProgressIndicator())
                      : filtered.isEmpty
                          ? const Center(
                              child: Text('Nenhuma empresa encontrada.'),
                            )
                          : ListView.separated(
                              itemCount: filtered.length,
                              separatorBuilder: (_, __) =>
                                  const SizedBox(height: 5),
                              itemBuilder: (context, index) {
                                final company = filtered[index];
                                return Card(
                                  child: ListTile(
                                    leading: CircleAvatar(
                                      backgroundColor: AuditarBrand.greenSoft,
                                      foregroundColor: AuditarBrand.greenDark,
                                      child:
                                          const Icon(Icons.business_outlined),
                                    ),
                                    title: Text(
                                      company.name,
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w700,
                                      ),
                                    ),
                                    subtitle: const Text(
                                      'Ver e gerenciar acessos individuais',
                                    ),
                                    trailing: const Icon(
                                      Icons.chevron_right_rounded,
                                    ),
                                    onTap: () => _openCompany(company),
                                  ),
                                );
                              },
                            ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// Somente apresenta o editor existente da empresa: não grava alterações
/// em e-mails de relatórios, pois esses controladores não são utilizados
/// pelo editor de acessos e são descartados ao sair da tela.
class _ClientAccessForCompanyScreen extends StatefulWidget {
  const _ClientAccessForCompanyScreen({required this.company});

  final Company company;

  @override
  State<_ClientAccessForCompanyScreen> createState() =>
      _ClientAccessForCompanyScreenState();
}

class _ClientAccessForCompanyScreenState
    extends State<_ClientAccessForCompanyScreen> {
  final _reportEmail = TextEditingController();
  final _reportRecipient = TextEditingController();

  @override
  void dispose() {
    _reportEmail.dispose();
    _reportRecipient.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!AuditarAdminAccess.isAdmin(AuthService.currentUser)) {
      return Scaffold(
        appBar: AppBar(title: const Text('Painel do Cliente')),
        body: const Center(
          child: Text('Acesso exclusivo à conta administradora Auditar.'),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text('Acessos • ${widget.company.name}'),
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 880),
          child: ListView(
            padding: const EdgeInsets.all(18),
            children: [
              Text(
                'Empresa: ${widget.company.name}',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
              ),
              const SizedBox(height: 6),
              const Text(
                'Cadastre ou edite os responsáveis autorizados. '
                'Cada pessoa tem sua própria conta e permissões.',
              ),
              CompanyClientAccessSection(
                key: ValueKey('client_panel_accounts_${widget.company.id}'),
                company: widget.company,
                reportEmail: _reportEmail,
                reportRecipient: _reportRecipient,
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}

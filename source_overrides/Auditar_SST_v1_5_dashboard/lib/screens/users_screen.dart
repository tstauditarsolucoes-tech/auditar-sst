import 'package:flutter/material.dart';

import '../brand.dart';
import '../database.dart';
import '../models.dart';
import '../services/auth_service.dart';

class UsersScreen extends StatefulWidget {
  const UsersScreen({super.key});

  @override
  State<UsersScreen> createState() => _UsersScreenState();
}

class _UsersScreenState extends State<UsersScreen> {
  bool loading = true;
  String error = '';
  List<AuditarUser> users = const [];
  List<Company> companies = const [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      loading = true;
      error = '';
    });
    try {
      final values = await Future.wait([
        AuthService.listUsers(),
        AppDatabase.instance.getCompanies(onlyActive: false),
      ]);
      if (!mounted) return;
      setState(() {
        users = values[0] as List<AuditarUser>;
        companies = values[1] as List<Company>;
        loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        error = '$e'.replaceFirst('Bad state: ', '');
        loading = false;
      });
    }
  }

  Future<void> _edit([AuditarUser? existing]) async {
    final saved = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (_) => _UserEditorDialog(
        user: existing,
        companies: companies,
      ),
    );
    if (saved == true) await _load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Usuários e acessos'),
        actions: [
          IconButton(
            tooltip: 'Atualizar',
            onPressed: loading ? null : _load,
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: loading ? null : () => _edit(),
        icon: const Icon(Icons.person_add_alt_1_rounded),
        label: const Text('Novo usuário'),
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : error.isNotEmpty
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.error_outline_rounded, size: 44, color: AuditarBrand.danger),
                        const SizedBox(height: 12),
                        Text(error, textAlign: TextAlign.center),
                        const SizedBox(height: 14),
                        FilledButton.icon(
                          onPressed: _load,
                          icon: const Icon(Icons.refresh_rounded),
                          label: const Text('Tentar novamente'),
                        ),
                      ],
                    ),
                  ),
                )
              : ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
                  itemCount: users.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 10),
                  itemBuilder: (context, index) {
                    final user = users[index];
                    final accessLabel = user.isAdmin || user.allCompanies
                        ? 'Todas as empresas'
                        : user.companyIds.isEmpty
                            ? 'Sem empresas liberadas'
                            : '${user.companyIds.length} empresa(s) liberada(s)';
                    return Card(
                      child: ListTile(
                        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
                        leading: CircleAvatar(
                          backgroundColor: user.active ? AuditarBrand.greenSoft : const Color(0xFFF1F3F5),
                          foregroundColor: user.active ? AuditarBrand.greenDark : Colors.black45,
                          child: Icon(user.isAdmin ? Icons.admin_panel_settings_rounded : Icons.engineering_rounded),
                        ),
                        title: Text(user.name, style: const TextStyle(fontWeight: FontWeight.w800)),
                        subtitle: Text('${user.email}\n${user.isAdmin ? 'Administrador' : 'Técnico'} • $accessLabel'),
                        isThreeLine: true,
                        trailing: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(user.active ? Icons.check_circle_rounded : Icons.block_rounded,
                                color: user.active ? AuditarBrand.greenDark : Colors.black38),
                            const SizedBox(height: 2),
                            Text(user.active ? 'Ativo' : 'Inativo', style: const TextStyle(fontSize: 10)),
                          ],
                        ),
                        onTap: () => _edit(user),
                      ),
                    );
                  },
                ),
    );
  }
}

class _UserEditorDialog extends StatefulWidget {
  final AuditarUser? user;
  final List<Company> companies;

  const _UserEditorDialog({required this.user, required this.companies});

  @override
  State<_UserEditorDialog> createState() => _UserEditorDialogState();
}

class _UserEditorDialogState extends State<_UserEditorDialog> {
  late final TextEditingController name;
  late final TextEditingController email;
  late final TextEditingController password;
  late String role;
  late bool active;
  late bool allCompanies;
  late Set<String> selectedCompanies;
  bool saving = false;
  bool obscure = true;
  String error = '';

  @override
  void initState() {
    super.initState();
    final user = widget.user;
    name = TextEditingController(text: user?.name ?? '');
    email = TextEditingController(text: user?.email ?? '');
    password = TextEditingController();
    role = user?.isAdmin == true ? 'admin' : 'tecnico';
    active = user?.active ?? true;
    allCompanies = user?.allCompanies ?? false;
    selectedCompanies = {...?user?.companyIds};
  }

  @override
  void dispose() {
    name.dispose();
    email.dispose();
    password.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (name.text.trim().length < 3) {
      setState(() => error = 'Informe o nome do usuário.');
      return;
    }
    if (!email.text.trim().contains('@')) {
      setState(() => error = 'Informe um e-mail válido.');
      return;
    }
    if (widget.user == null && password.text.length < 8) {
      setState(() => error = 'Defina uma senha inicial com pelo menos 8 caracteres.');
      return;
    }
    if (password.text.isNotEmpty && password.text.length < 8) {
      setState(() => error = 'A nova senha deve ter pelo menos 8 caracteres.');
      return;
    }

    setState(() {
      saving = true;
      error = '';
    });
    try {
      await AuthService.saveUser(
        userId: widget.user?.id,
        name: name.text,
        email: email.text,
        role: role,
        active: active,
        allCompanies: role == 'admin' ? true : allCompanies,
        companyIds: role == 'admin' || allCompanies ? const [] : selectedCompanies.toList(),
        password: password.text,
      );
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) setState(() => error = '$e'.replaceFirst('Bad state: ', ''));
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final editing = widget.user != null;
    return AlertDialog(
      title: Text(editing ? 'Editar usuário' : 'Novo usuário'),
      content: SizedBox(
        width: 520,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextField(
                controller: name,
                textCapitalization: TextCapitalization.words,
                decoration: const InputDecoration(labelText: 'Nome'),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: email,
                keyboardType: TextInputType.emailAddress,
                autocorrect: false,
                decoration: const InputDecoration(labelText: 'E-mail de acesso'),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: password,
                obscureText: obscure,
                autocorrect: false,
                enableSuggestions: false,
                decoration: InputDecoration(
                  labelText: editing ? 'Nova senha (opcional)' : 'Senha inicial',
                  helperText: editing ? 'Preencha apenas se quiser trocar a senha.' : 'Mínimo de 8 caracteres.',
                  suffixIcon: IconButton(
                    onPressed: () => setState(() => obscure = !obscure),
                    icon: Icon(obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined),
                  ),
                ),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: role,
                decoration: const InputDecoration(labelText: 'Perfil'),
                items: const [
                  DropdownMenuItem(value: 'tecnico', child: Text('Técnico SST')),
                  DropdownMenuItem(value: 'admin', child: Text('Administrador')),
                ],
                onChanged: (value) => setState(() {
                  role = value ?? 'tecnico';
                  if (role == 'admin') allCompanies = true;
                }),
              ),
              const SizedBox(height: 6),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Usuário ativo'),
                value: active,
                onChanged: (value) => setState(() => active = value),
              ),
              if (role != 'admin') ...[
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Acesso a todas as empresas'),
                  subtitle: const Text('Desative para escolher empresas específicas.'),
                  value: allCompanies,
                  onChanged: (value) => setState(() => allCompanies = value),
                ),
                if (!allCompanies) ...[
                  const SizedBox(height: 4),
                  const Text('Empresas liberadas', style: TextStyle(fontWeight: FontWeight.w800)),
                  const SizedBox(height: 6),
                  Container(
                    constraints: const BoxConstraints(maxHeight: 230),
                    decoration: BoxDecoration(
                      border: Border.all(color: AuditarBrand.line),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: widget.companies.isEmpty
                        ? const Padding(
                            padding: EdgeInsets.all(14),
                            child: Text('Nenhuma empresa cadastrada.'),
                          )
                        : ListView.builder(
                            shrinkWrap: true,
                            itemCount: widget.companies.length,
                            itemBuilder: (context, index) {
                              final company = widget.companies[index];
                              return CheckboxListTile(
                                dense: true,
                                value: selectedCompanies.contains(company.id),
                                title: Text(company.name),
                                onChanged: (checked) => setState(() {
                                  if (checked == true) {
                                    selectedCompanies.add(company.id);
                                  } else {
                                    selectedCompanies.remove(company.id);
                                  }
                                }),
                              );
                            },
                          ),
                  ),
                ],
              ],
              if (error.isNotEmpty) ...[
                const SizedBox(height: 10),
                Text(error, style: const TextStyle(color: AuditarBrand.danger, fontWeight: FontWeight.w700)),
              ],
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: saving ? null : () => Navigator.pop(context, false),
          child: const Text('Cancelar'),
        ),
        FilledButton.icon(
          onPressed: saving ? null : _save,
          icon: const Icon(Icons.save_rounded),
          label: Text(saving ? 'Salvando...' : 'Salvar'),
        ),
      ],
    );
  }
}

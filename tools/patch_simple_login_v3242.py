#!/usr/bin/env python3
"""Auditar SST v3.24.2: login simples tipo Gestão EPI + fim do loading infinito."""
from pathlib import Path
import re, sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')

def read(rel): return (root / rel).read_text(encoding='utf-8')
def write(rel, text):
    p=root/rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text, encoding='utf-8')
def replace_once(text, old, new, label):
    if new in text: return text
    if old not in text: raise RuntimeError(f'Marcador não encontrado: {label}')
    return text.replace(old,new,1)

# Versão
pub = read('pubspec.yaml')
pub = re.sub(r'^version:\s*\d+\.\d+\.\d+\+\d+\s*$', 'version: 3.24.2+102', pub, flags=re.M)
write('pubspec.yaml', pub)

# Login: abre imediatamente, sem consulta de status bloqueando a tela.
login = r'''import 'dart:io';

import 'package:flutter/material.dart';

import '../brand.dart';
import '../services/auth_service.dart';
import '../widgets/auditar_brand_logo.dart';
import 'home_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final user = TextEditingController();
  final password = TextEditingController();
  final adminName = TextEditingController();
  final adminEmail = TextEditingController();
  final adminPassword = TextEditingController();

  bool busy = false;
  bool obscure = true;
  bool checkingFirstAccess = false;
  String error = '';

  @override
  void dispose() {
    user.dispose();
    password.dispose();
    adminName.dispose();
    adminEmail.dispose();
    adminPassword.dispose();
    super.dispose();
  }

  String _friendly(Object value) {
    final text = '$value'.replaceFirst('Bad state: ', '').trim();
    if (text.contains('TimeoutException')) {
      return 'A Central Online demorou para responder. Verifique a internet e tente novamente.';
    }
    return text;
  }

  Future<void> _enter() async {
    if (busy) return;
    final username = user.text.trim();
    final pass = password.text;
    if (username.isEmpty || pass.isEmpty) {
      setState(() => error = 'Informe usuário e senha.');
      return;
    }
    if (pass.length < 8) {
      setState(() => error = 'A senha deve ter pelo menos 8 caracteres.');
      return;
    }
    setState(() { busy = true; error = ''; });
    try {
      await AuthService.login(username: username, password: pass)
          .timeout(const Duration(seconds: 25));
      if (!mounted) return;
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (_) => const HomeScreen()),
        (_) => false,
      );
    } catch (e) {
      if (mounted) setState(() => error = _friendly(e));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> _firstAccess() async {
    if (checkingFirstAccess) return;
    setState(() { checkingFirstAccess = true; error = ''; });
    try {
      final status = await AuthService.status().timeout(const Duration(seconds: 20));
      if (!mounted) return;
      if (status.hasUsers) {
        setState(() => error = 'Já existe um administrador. Entre com seu usuário e senha.');
        return;
      }
      await _showCreateAdmin();
    } catch (e) {
      if (mounted) setState(() => error = _friendly(e));
    } finally {
      if (mounted) setState(() => checkingFirstAccess = false);
    }
  }

  Future<void> _showCreateAdmin() async {
    adminName.clear(); adminEmail.clear(); adminPassword.clear();
    final created = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Criar administrador'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: adminName, decoration: const InputDecoration(labelText: 'Nome')),
              const SizedBox(height: 10),
              TextField(controller: adminEmail, decoration: const InputDecoration(labelText: 'E-mail')),
              const SizedBox(height: 10),
              TextField(controller: adminPassword, obscureText: true, decoration: const InputDecoration(labelText: 'Senha')),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(dialogContext, true), child: const Text('Criar')),
        ],
      ),
    );
    if (created != true || !mounted) return;
    final name = adminName.text.trim();
    final email = adminEmail.text.trim();
    final pass = adminPassword.text;
    if (name.length < 3 || !email.contains('@') || pass.length < 8) {
      setState(() => error = 'Preencha nome, e-mail válido e senha com pelo menos 8 caracteres.');
      return;
    }
    setState(() { busy = true; error = ''; });
    try {
      await AuthService.bootstrapAdmin(name: name, email: email, password: pass)
          .timeout(const Duration(seconds: 25));
      if (!mounted) return;
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (_) => const HomeScreen()),
        (_) => false,
      );
    } catch (e) {
      if (mounted) setState(() => error = _friendly(e));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final desktop = MediaQuery.sizeOf(context).width >= 760;
    return Scaffold(
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [AuditarBrand.navyDark, AuditarBrand.navy],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(22),
              child: ConstrainedBox(
                constraints: BoxConstraints(maxWidth: desktop ? 460 : 430),
                child: Card(
                  elevation: 12,
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(22, 24, 22, 22),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        const Center(child: AuditarBrandLogo(iconSize: 54)),
                        const SizedBox(height: 18),
                        Text('Entrar no Auditar SST', textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900, color: AuditarBrand.navy)),
                        const SizedBox(height: 6),
                        Text('Acesso individual com usuário e senha. Use a mesma conta no celular e no computador.',
                          textAlign: TextAlign.center, style: const TextStyle(color: Colors.black54, height: 1.35)),
                        const SizedBox(height: 20),
                        TextField(
                          controller: user,
                          autocorrect: false,
                          enableSuggestions: false,
                          textInputAction: TextInputAction.next,
                          decoration: const InputDecoration(labelText: 'Usuário', prefixIcon: Icon(Icons.person_outline_rounded)),
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: password,
                          obscureText: obscure,
                          autocorrect: false,
                          enableSuggestions: false,
                          onSubmitted: (_) => _enter(),
                          decoration: InputDecoration(
                            labelText: 'Senha',
                            prefixIcon: const Icon(Icons.lock_outline_rounded),
                            suffixIcon: IconButton(
                              onPressed: () => setState(() => obscure = !obscure),
                              icon: Icon(obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined),
                            ),
                          ),
                        ),
                        if (error.isNotEmpty) ...[
                          const SizedBox(height: 12),
                          Container(
                            padding: const EdgeInsets.all(11),
                            decoration: BoxDecoration(color: const Color(0xFFFFF0F0), borderRadius: BorderRadius.circular(12)),
                            child: Text(error, style: const TextStyle(color: AuditarBrand.danger, fontWeight: FontWeight.w700)),
                          ),
                        ],
                        const SizedBox(height: 18),
                        FilledButton.icon(
                          onPressed: busy ? null : _enter,
                          icon: busy
                              ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                              : const Icon(Icons.login_rounded),
                          label: Text(busy ? 'Entrando…' : 'Entrar'),
                        ),
                        const SizedBox(height: 6),
                        TextButton(
                          onPressed: busy || checkingFirstAccess ? null : _firstAccess,
                          child: Text(checkingFirstAccess ? 'Verificando…' : 'Primeiro acesso'),
                        ),
                        const SizedBox(height: 10),
                        Text('${Platform.isWindows ? 'Computador' : 'Celular'} • acesso individual',
                          textAlign: TextAlign.center, style: const TextStyle(fontSize: 11.5, color: Colors.black45)),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
'''
write('lib/screens/login_screen.dart', login)

# AuthService: login por usuário OU e-mail; envia os dois campos para compatibilidade.
auth = read('lib/services/auth_service.dart')
old = r'''  static Future<AuditarUser> login({
    required String email,
    required String password,
  }) async {
    final result = await _post({
      'action': 'auth_login',
      'email': email.trim(),
      'password': password,
      'deviceId': await deviceId(),
      'platform': Platform.isWindows ? 'windows' : 'android',
    });
'''
new = r'''  static Future<AuditarUser> login({
    required String username,
    required String password,
  }) async {
    final identifier = username.trim();
    final result = await _post({
      'action': 'auth_login',
      'username': identifier,
      'email': identifier,
      'password': password,
      'deviceId': await deviceId(),
      'platform': Platform.isWindows ? 'windows' : 'android',
    });
'''
auth = replace_once(auth, old, new, 'login por usuário')
write('lib/services/auth_service.dart', auth)

# Home: qualquer erro deixa de prender o usuário num spinner infinito.
home = read('lib/screens/home_screen.dart')
home = replace_once(home, '  bool loading = true;\n', "  bool loading = true;\n  String loadError = '';\n", 'estado de erro home')
pattern = re.compile(r"  Future<void> _refresh\(\) async \{.*?\n  \}\n\n  Future<void> _open", re.S)
new_refresh_block = r'''  Future<void> _refresh() async {
    if (mounted) setState(() { loading = true; loadError = ''; });
    try {
      final result = await AppDatabase.instance.getDashboardSummary()
          .timeout(const Duration(seconds: 15));
      final ncRows = await AppDatabase.instance.getNonConformityRows(
        includeClosed: false,
      ).timeout(const Duration(seconds: 15));
      final routine = await AppDatabase.instance.getRoutineTodaySummary()
          .timeout(const Duration(seconds: 15));
      final history = await AppDatabase.instance.getInspectionHistory()
          .timeout(const Duration(seconds: 15));
      Map<String, Object?>? inProgress;
      for (final row in history) {
        if ('${row['status'] ?? ''}' != 'Finalizada') {
          inProgress = row;
          break;
        }
      }

      if (!mounted) return;
      setState(() {
        summary = result;
        routineSummary = routine;
        openNcs = ncRows.length;
        activeInspection = inProgress;
        loading = false;
        loadError = '';
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        loading = false;
        loadError = '$e'.replaceFirst('Bad state: ', '').trim();
      });
    }
  }

  Future<void> _open'''
if "getInspectionHistory()\n          .timeout" not in home:
    home, count = pattern.subn(new_refresh_block, home, count=1)
    if count != 1:
        raise RuntimeError('Marcador não encontrado: refresh home com timeout')
old_body = r'''      body: loading
          ? const Center(child: CircularProgressIndicator())
          : LayoutBuilder(
'''
new_body = r'''      body: loading
          ? const Center(child: CircularProgressIndicator())
          : loadError.isNotEmpty
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(maxWidth: 520),
                      child: Card(
                        child: Padding(
                          padding: const EdgeInsets.all(20),
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(Icons.sync_problem_rounded, size: 42, color: AuditarBrand.warning),
                              const SizedBox(height: 12),
                              const Text('Não foi possível carregar os dados', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 17)),
                              const SizedBox(height: 8),
                              Text(loadError, textAlign: TextAlign.center, style: const TextStyle(color: Colors.black54)),
                              const SizedBox(height: 16),
                              FilledButton.icon(onPressed: _refresh, icon: const Icon(Icons.refresh_rounded), label: const Text('Tentar novamente')),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                )
              : LayoutBuilder(
'''
home = replace_once(home, old_body, new_body, 'home sem spinner infinito')
write('lib/screens/home_screen.dart', home)

# Backend: login aceita email completo ou usuário = parte antes do @.
mu = read('painel_web_google_apps_script/MultiUser.gs')
if 'request.username || request.email' not in mu:
    pattern_login = re.compile(
        r"function authLogin_\(request\) \{\n  const email = normalizeAuthEmail_\(request.email\);\n  const password = String\(request.password \|\| ''\);\n(?:  const ss = ensureAuthStorage_\(\);\n)?  const users = readAuthUsers_\((?:ss)?\);\n  const user = users.find\(item => item.email === email\);"
    )
    replacement_login = """function authLogin_(request) {\n  const identifier = normalizeAuthEmail_(request.username || request.email);\n  const password = String(request.password || '');\n  const ss = ensureAuthStorage_();\n  const users = readAuthUsers_(ss);\n  const user = users.find(item => {\n    const email = normalizeAuthEmail_(item.email);\n    const username = email.indexOf('@') > 0 ? email.split('@')[0] : email;\n    return email === identifier || username === identifier;\n  });"""
    mu, count = pattern_login.subn(replacement_login, mu, count=1)
    if count != 1:
        raise RuntimeError('Marcador não encontrado: authLogin backend')
mu = mu.replace("message: 'E-mail ou senha inválidos.'", "message: 'Usuário ou senha inválidos.'")
write('painel_web_google_apps_script/MultiUser.gs', mu)

print('Auditar SST v3.24.2: login simples e proteção contra loading infinito aplicados.')

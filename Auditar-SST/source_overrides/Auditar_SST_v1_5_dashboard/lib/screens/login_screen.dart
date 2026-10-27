import 'dart:io';

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
  final name = TextEditingController();
  final email = TextEditingController();
  final password = TextEditingController();
  final confirmPassword = TextEditingController();

  bool loading = true;
  bool busy = false;
  bool firstAdmin = false;
  bool obscure = true;
  String error = '';

  @override
  void initState() {
    super.initState();
    _loadStatus();
  }

  @override
  void dispose() {
    name.dispose();
    email.dispose();
    password.dispose();
    confirmPassword.dispose();
    super.dispose();
  }

  Future<void> _loadStatus() async {
    try {
      final status = await AuthService.status();
      if (!mounted) return;
      setState(() {
        firstAdmin = !status.hasUsers;
        loading = false;
        error = '';
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        loading = false;
        error = _friendly(e);
      });
    }
  }

  String _friendly(Object error) {
    final text = '$error'.replaceFirst('Bad state: ', '').trim();
    if (text.contains('Requisição inválida')) {
      return 'A Central Online ainda precisa ser atualizada para a versão multiusuário.';
    }
    return text;
  }

  Future<void> _submit() async {
    if (busy) return;
    final mail = email.text.trim();
    final pass = password.text;
    if (!mail.contains('@') || mail.length < 5) {
      setState(() => error = 'Informe um e-mail válido.');
      return;
    }
    if (pass.length < 8) {
      setState(() => error = 'A senha deve ter pelo menos 8 caracteres.');
      return;
    }
    if (firstAdmin) {
      if (name.text.trim().length < 3) {
        setState(() => error = 'Informe o nome do administrador.');
        return;
      }
      if (pass != confirmPassword.text) {
        setState(() => error = 'As senhas não são iguais.');
        return;
      }
    }

    setState(() {
      busy = true;
      error = '';
    });
    try {
      if (firstAdmin) {
        await AuthService.bootstrapAdmin(
          name: name.text.trim(),
          email: mail,
          password: pass,
        );
      } else {
        await AuthService.login(email: mail, password: pass);
      }
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
                constraints: BoxConstraints(maxWidth: desktop ? 470 : 430),
                child: Card(
                  elevation: 12,
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(22, 24, 22, 22),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        const Center(
                          child: AuditarBrandLogo(iconSize: 54),
                        ),
                        const SizedBox(height: 18),
                        Text(
                          firstAdmin ? 'Primeiro acesso' : 'Entrar no Auditar SST',
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                fontWeight: FontWeight.w900,
                                color: AuditarBrand.navy,
                              ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          firstAdmin
                              ? 'Crie a conta administradora. Os dados atuais serão preservados nesta conta.'
                              : 'Use a mesma conta no celular e no computador.',
                          textAlign: TextAlign.center,
                          style: const TextStyle(color: Colors.black54, height: 1.35),
                        ),
                        const SizedBox(height: 20),
                        if (loading)
                          const Padding(
                            padding: EdgeInsets.all(20),
                            child: Center(child: CircularProgressIndicator()),
                          )
                        else ...[
                          if (firstAdmin) ...[
                            TextField(
                              controller: name,
                              textCapitalization: TextCapitalization.words,
                              decoration: const InputDecoration(
                                labelText: 'Nome',
                                prefixIcon: Icon(Icons.person_outline_rounded),
                              ),
                            ),
                            const SizedBox(height: 12),
                          ],
                          TextField(
                            controller: email,
                            keyboardType: TextInputType.emailAddress,
                            autocorrect: false,
                            decoration: const InputDecoration(
                              labelText: 'E-mail',
                              prefixIcon: Icon(Icons.alternate_email_rounded),
                            ),
                          ),
                          const SizedBox(height: 12),
                          TextField(
                            controller: password,
                            obscureText: obscure,
                            autocorrect: false,
                            enableSuggestions: false,
                            onSubmitted: (_) {
                              if (!firstAdmin) _submit();
                            },
                            decoration: InputDecoration(
                              labelText: 'Senha',
                              prefixIcon: const Icon(Icons.lock_outline_rounded),
                              suffixIcon: IconButton(
                                onPressed: () => setState(() => obscure = !obscure),
                                icon: Icon(obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined),
                              ),
                            ),
                          ),
                          if (firstAdmin) ...[
                            const SizedBox(height: 12),
                            TextField(
                              controller: confirmPassword,
                              obscureText: obscure,
                              autocorrect: false,
                              enableSuggestions: false,
                              onSubmitted: (_) => _submit(),
                              decoration: const InputDecoration(
                                labelText: 'Confirmar senha',
                                prefixIcon: Icon(Icons.verified_user_outlined),
                              ),
                            ),
                          ],
                          if (error.isNotEmpty) ...[
                            const SizedBox(height: 12),
                            Container(
                              padding: const EdgeInsets.all(11),
                              decoration: BoxDecoration(
                                color: const Color(0xFFFFF0F0),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                error,
                                style: const TextStyle(
                                  color: AuditarBrand.danger,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                          ],
                          const SizedBox(height: 18),
                          FilledButton.icon(
                            onPressed: busy ? null : _submit,
                            icon: Icon(firstAdmin ? Icons.admin_panel_settings_outlined : Icons.login_rounded),
                            label: Text(firstAdmin ? 'Criar administrador' : 'Entrar'),
                          ),
                          if (error.isNotEmpty) ...[
                            const SizedBox(height: 8),
                            TextButton.icon(
                              onPressed: busy ? null : _loadStatus,
                              icon: const Icon(Icons.refresh_rounded),
                              label: const Text('Tentar novamente'),
                            ),
                          ],
                          const SizedBox(height: 12),
                          Text(
                            '${Platform.isWindows ? 'Computador' : 'Celular'} • acesso individual',
                            textAlign: TextAlign.center,
                            style: const TextStyle(fontSize: 11.5, color: Colors.black45),
                          ),
                        ],
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

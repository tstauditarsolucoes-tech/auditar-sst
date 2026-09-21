#!/usr/bin/env python3
from pathlib import Path
import sys

root=Path(sys.argv[1])
pub=root/'pubspec.yaml'
auth=root/'lib/services/auth_service.dart'
login=root/'lib/screens/login_screen.dart'

p=pub.read_text(encoding='utf-8')
if 'version: 3.29.72+214' not in p:
    if 'version: 3.29.71+213' not in p:
        raise RuntimeError('Base esperada v3.29.71+213 não encontrada')
    p=p.replace('version: 3.29.71+213','version: 3.29.72+214',1)
pub.write_text(p,encoding='utf-8')

a=auth.read_text(encoding='utf-8')
old="""  static Future<Map<String, dynamic>> _post(Map<String, Object?> payload) async {
    final response = await AppsScriptHttp.postJson(await _endpoint(), payload);
"""
new="""  static Future<Map<String, dynamic>> _post(
    Map<String, Object?> payload, {
    Duration timeout = const Duration(seconds: 30),
    bool allowLongAndroidRequest = false,
  }) async {
    final response = await AppsScriptHttp.postJson(
      await _endpoint(),
      payload,
      timeout: timeout,
      allowLongAndroidRequest: allowLongAndroidRequest,
    );
"""
if new not in a:
    if old not in a: raise RuntimeError('_post do AuthService não encontrado')
    a=a.replace(old,new,1)

# Login é não-idempotente: uma tentativa lenta não deve ser reenviada
# automaticamente por outra rota, pois isso pode criar sessões duplicadas.
old_login="""      final result = await _post({
        'action': 'auth_login',
        'username': identifier,
        'email': identifier,
        'password': password,
        'deviceId': await deviceId(),
        'platform': Platform.isWindows ? 'windows' : 'android',
      });
"""
new_login="""      final result = await _post(
        {
          'action': 'auth_login',
          'username': identifier,
          'email': identifier,
          'password': password,
          'deviceId': await deviceId(),
          'platform': Platform.isWindows ? 'windows' : 'android',
        },
        timeout: const Duration(seconds: 30),
        allowLongAndroidRequest: true,
      );
"""
if new_login not in a:
    if old_login not in a: raise RuntimeError('AuthService.login não encontrado')
    a=a.replace(old_login,new_login,1)

# Primeiro acesso também cria dados e deve seguir a mesma proteção.
old_boot="""    final result = await _post({
      'action': 'auth_bootstrap_admin',
      'syncKey': syncKey,
      'name': name.trim(),
      'email': email.trim(),
      'password': password,
      'deviceId': await deviceId(),
      'platform': Platform.isWindows ? 'windows' : 'android',
    });
"""
new_boot="""    final result = await _post(
      {
        'action': 'auth_bootstrap_admin',
        'syncKey': syncKey,
        'name': name.trim(),
        'email': email.trim(),
        'password': password,
        'deviceId': await deviceId(),
        'platform': Platform.isWindows ? 'windows' : 'android',
      },
      timeout: const Duration(seconds: 30),
      allowLongAndroidRequest: true,
    );
"""
if new_boot not in a:
    if old_boot not in a: raise RuntimeError('bootstrapAdmin não encontrado')
    a=a.replace(old_boot,new_boot,1)

auth.write_text(a,encoding='utf-8')

l=login.read_text(encoding='utf-8')
old_enter="""      await AuthService.login(username: username, password: pass)
          .timeout(const Duration(seconds: 25));
"""
new_enter="""      await AuthService.login(username: username, password: pass);
"""
if new_enter not in l:
    if old_enter not in l: raise RuntimeError('timeout externo de login não encontrado')
    l=l.replace(old_enter,new_enter,1)

old_admin="""      await AuthService.bootstrapAdmin(name: name, email: email, password: pass)
          .timeout(const Duration(seconds: 25));
"""
new_admin="""      await AuthService.bootstrapAdmin(
        name: name,
        email: email,
        password: pass,
      );
"""
if new_admin not in l:
    if old_admin not in l: raise RuntimeError('timeout externo do primeiro acesso não encontrado')
    l=l.replace(old_admin,new_admin,1)

# Mensagem específica para os novos erros de transporte sem esconder a causa.
old_friendly="""    if (text.contains('TimeoutException')) {
      return 'A Central Online demorou para responder. Verifique a internet e tente novamente.';
    }
"""
new_friendly="""    if (text.contains('TimeoutException')) {
      return 'A Central Online demorou para responder. Tente novamente em alguns instantes.';
    }
    if (text.contains('não respondeu a tempo')) {
      return 'A Central Online está oscilando e não respondeu a tempo. Tente novamente.';
    }
"""
if new_friendly not in l:
    if old_friendly not in l: raise RuntimeError('_friendly timeout não encontrado')
    l=l.replace(old_friendly,new_friendly,1)

login.write_text(l,encoding='utf-8')

assert 'version: 3.29.72+214' in p
assert 'allowLongAndroidRequest: true' in a
assert "AuthService.login(username: username, password: pass);" in l
assert "AuthService.login(username: username, password: pass)\n          .timeout" not in l
print('v3.29.72: autenticação Android resiliente aplicada; sync compartilhado preservado.')

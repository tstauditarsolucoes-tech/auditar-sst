#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/Auditar_SST_v1_5_dashboard')

auth = root / 'lib/services/auth_service.dart'
login = root / 'lib/screens/login_screen.dart'

if not auth.exists() or not login.exists():
    raise SystemExit('Arquivos de autenticação não encontrados.')

text = auth.read_text(encoding='utf-8')

marker = """  static bool canAccessCompany(String companyId) {
    final user = _currentUser;
    if (user == null || !user.active) return false;
    if (user.isAdmin || user.allCompanies) return true;
    return user.companyIds.contains(companyId);
  }
"""
insert = marker + """
  static String _loginEmail(String value) {
    final raw = value.trim().toLowerCase();
    if (raw.contains('@')) return raw;
    final clean = raw.replaceAll(RegExp(r'[^a-z0-9._-]'), '');
    if (clean.length < 3) {
      throw StateError('Informe um usuário válido.');
    }
    return '$clean@sstgestao.local';
  }
"""
if '_loginEmail(String value)' not in text:
    if marker not in text:
        raise SystemExit('Ponto de inserção _loginEmail não encontrado.')
    text = text.replace(marker, insert, 1)

old_boot = """      'name': name.trim(),
      'email': email.trim(),
      'password': password,
"""
new_boot = """      'name': name.trim(),
      'username': email.trim(),
      'email': _loginEmail(email),
      'loginEmail': _loginEmail(email),
      'contactEmail': '',
      'password': password,
"""
if old_boot in text:
    text = text.replace(old_boot, new_boot, 1)

text = text.replace("'action': 'auth_bootstrap_admin'", "'action': 'sst_auth_bootstrap_admin'")

old_login = """      'action': 'sst_auth_login',
      'email': email.trim(),
      'password': password,
"""
new_login = """      'action': 'auth_login',
      'username': email.trim(),
      'email': _loginEmail(email),
      'password': password,
"""
if old_login in text:
    text = text.replace(old_login, new_login, 1)

text = text.replace("'action': 'auth_session'", "'action': 'sst_auth_session'")
text = text.replace("'action': 'auth_users_list'", "'action': 'sst_auth_users_list'")
text = text.replace("'action': 'auth_user_save'", "'action': 'sst_auth_user_save'")
auth.write_text(text, encoding='utf-8', newline='\n')

ui = login.read_text(encoding='utf-8')
ui = ui.replace(
"""    final mail = email.text.trim();
    final pass = password.text;
    if (!mail.contains('@') || mail.length < 5) {
      setState(() => error = 'Informe um e-mail válido.');
      return;
    }
""",
"""    final mail = email.text.trim();
    final pass = password.text;
    if (mail.length < 3) {
      setState(() => error = 'Informe seu usuário.');
      return;
    }
""",
1,
)
ui = ui.replace('keyboardType: TextInputType.emailAddress,\n', '', 1)
ui = ui.replace("labelText: 'E-mail',", "labelText: 'Usuário',", 1)
ui = ui.replace('prefixIcon: Icon(Icons.alternate_email_rounded),', 'prefixIcon: Icon(Icons.person_outline_rounded),', 1)
login.write_text(ui, encoding='utf-8', newline='\n')

print('NEUTRAL_USERNAME_LOGIN_OK: login por usuário habilitado; e-mail não é obrigatório para autenticação.')

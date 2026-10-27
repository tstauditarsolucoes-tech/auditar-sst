#!/usr/bin/env python3
"""Static guardrails for the Auditar administrator hub on both platforms."""
from pathlib import Path
import sys
import re


def normalized(text):
    return re.sub(r'\s+', '', text)

root = Path(sys.argv[1])
service = (root / 'lib/services/admin_access_policy.dart').read_text(encoding='utf-8')
center = (root / 'lib/screens/admin_center_screen.dart').read_text(encoding='utf-8')
client_access = (root / 'lib/screens/admin_client_panel_access_screen.dart').read_text(encoding='utf-8')
home = (root / 'lib/screens/home_screen.dart').read_text(encoding='utf-8')
settings = (root / 'lib/screens/settings_screen.dart').read_text(encoding='utf-8')
users = (root / 'lib/screens/users_screen.dart').read_text(encoding='utf-8')
test = (root / 'test/admin_access_policy_test.dart').read_text(encoding='utf-8')

for value in (
    "user.active && user.role.toLowerCase() == 'admin'",
    "user.role.toLowerCase() == 'tecnico'",
    "static bool canAccessCompany",
    "if (isAdmin(user)) return true;",
):
    if normalized(value) not in normalized(service):
        raise SystemExit('Admin policy missing: ' + value)
for value in (
    "AuditarAdminAccess.isAdmin(AuthService.currentUser)",
    'AuthService.listUsers()',
    'AppDatabase.instance.getCompanies(',
    'const UsersScreen()',
    'const AuditarClientPanelAccessScreen()',
    'const CompaniesScreen()',
):
    if normalized(value) not in normalized(center):
        raise SystemExit('Admin center missing: ' + value)
# The two visually different administrative shortcuts must never point
# to the same UsersScreen route again.
assert center.count('const UsersScreen()') == 1
assert center.count('const AuditarClientPanelAccessScreen()') == 1
for marker in (
    'class AuditarClientPanelAccessScreen',
    'AppDatabase.instance.getCompanies(onlyActive: false)',
    'CompanyClientAccessSection(',
    'AuditarAdminAccess.isAdmin(AuthService.currentUser)',
    "'Acessos ao painel dos clientes'",
):
    if normalized(marker) not in normalized(client_access):
        raise SystemExit('Dedicated client-panel access page missing: ' + marker)
for forbidden in ('AuthService.saveUser(', 'DeviceSyncService.', 'MediaSyncService.',
                  'SharedPreferences', 'AppDatabase.instance.save'):
    if forbidden in client_access:
        raise SystemExit('Dedicated client-panel page must reuse safe existing editor: ' + forbidden)

if normalized('if (AuthService.isAdmin)') not in normalized(home) or \
        normalized('page: () => const AuditarAdminCenterScreen()') not in normalized(home):
    raise SystemExit('Home admin entry not properly gated')
# Existing account screen stays unchanged. The admin hub is gated in Home
# and backend remains the authority for auth_users_list/auth_user_save.
for forbidden in (
    'DeviceSyncService.', 'MediaSyncService.', 'syncKey',
    'passwordHash', 'passwordSalt', 'authBootstrapAdmin_',
    'AUDITAR_SYNC_KEY',
):
    if forbidden in center + service:
        raise SystemExit('Admin feature contains protected operation: ' + forbidden)
print('ADMIN_AUTHORITY_UI_REGRESSION_OK')
print('ADMIN_ONLY_CLIENT_ACCOUNT_AND_MULTI_COMPANY_GUARDS_OK')

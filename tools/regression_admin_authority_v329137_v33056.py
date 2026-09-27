#!/usr/bin/env python3
"""Static guardrails for the Auditar administrator hub on both platforms."""
from pathlib import Path
import sys

root = Path(sys.argv[1])
service = (root / 'lib/services/admin_access_policy.dart').read_text(encoding='utf-8')
center = (root / 'lib/screens/admin_center_screen.dart').read_text(encoding='utf-8')
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
    if value not in service:
        raise SystemExit('Admin policy missing: ' + value)
for value in (
    "AuditarAdminAccess.isAdmin(AuthService.currentUser)",
    'AuthService.listUsers()',
    'AppDatabase.instance.getCompanies(onlyActive: false)',
    "const UsersScreen(initialRoleFilter: 'cliente')",
    'const UsersScreen()',
    'const CompaniesScreen()',
):
    if value not in center:
        raise SystemExit('Admin center missing: ' + value)
if 'if (AuthService.isAdmin)' not in home or \
        'page: () => const AuditarAdminCenterScreen()' not in home:
    raise SystemExit('Home admin entry not properly gated')
if 'Central Administrativa Auditar' not in settings or \
        'if (AuthService.isAdmin)' not in settings:
    raise SystemExit('Settings admin entry not properly gated')
for value in (
    'if (!AuthService.isAdmin) return;',
    'if (!AuthService.isAdmin) {',
    'initialRoleFilter',
    'initialRole: widget.initialRoleFilter',
    'final visibleUsers = widget.initialRoleFilter == null',
):
    if value not in users:
        raise SystemExit('Users screen missing guard: ' + value)
for value in (
    'all administrative capabilities belong only to active admin',
    'admin can see all companies; technician remains scoped',
    'client and inactive accounts cannot operate the app',
):
    if value not in test:
        raise SystemExit('Admin policy test missing: ' + value)
for forbidden in (
    'DeviceSyncService.', 'MediaSyncService.', 'syncKey',
    'passwordHash', 'passwordSalt', 'authBootstrapAdmin_',
    'AUDITAR_SYNC_KEY',
):
    if forbidden in center + service:
        raise SystemExit('Admin feature contains protected operation: ' + forbidden)
print('ADMIN_AUTHORITY_UI_REGRESSION_OK')
print('ADMIN_ONLY_CLIENT_ACCOUNT_AND_MULTI_COMPANY_GUARDS_OK')

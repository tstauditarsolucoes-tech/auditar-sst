#!/usr/bin/env python3
"""Company account regression: many people, one company, separate e-mail recipients."""
from pathlib import Path
import re
import sys
root = Path(sys.argv[1])
source = (root / 'lib/widgets/company_client_access_section.dart').read_text(encoding='utf-8')
test = (root / 'test/company_multi_client_access_test.dart').read_text(encoding='utf-8')
screen = (root / 'lib/screens/companies_screen.dart').read_text(encoding='utf-8')
flat = re.sub(r'\s+', '', source)
for marker in (
    'class ClientCompanyAccessRules',
    "user.role.toLowerCase() == 'cliente'",
    '!user.allCompanies',
    'user.companyIds.length == 1',
    'user.companyIds.single == companyId',
    'user.email.trim().toLowerCase() == normalized',
    'user.id != editingId',
    'ClientCompanyAccessRules.belongsTo(',
    'ClientCompanyAccessRules.duplicates(',
    "name.text=user?.name??'';",
    "email.text=user?.email??'';",
    'Acessos individuais • Painel do Cliente',
    'Adicionar outro e-mail de acesso',
    'Cada novo cadastro cria um login separado no mesmo painel.',
    "AuthService.listUsers()",
    "AuthService.saveUser(",
    "role:'cliente'",
    'allCompanies:false',
    'companyIds:[widget.company.id]',
    'clientPermissions:permissions',
    "password:secret",
    'O e-mail de login é independente dos destinatários de relatórios.',
):
    if re.sub(r'\s+', '', marker) not in flat:
        raise SystemExit('MULTI_CLIENT missing ' + marker)
for marker in ('manager and director belong to one shared company panel',
               'duplicate e-mail is case-insensitive',
               'one person may be deactivated',
               'rejects zero, multiple, and unrestricted companies'):
    if marker not in test:
        raise SystemExit('MULTI_CLIENT missing test: ' + marker)
assert 'CompanyClientAccessSection(' in screen
assert 'AuthService.isAdmin && company != null' in screen
for forbidden in ('AppDatabase.', 'DeviceSyncService.', 'MediaSyncService.',
                  'upsertCompany(', 'passwordHash', 'passwordSalt'):
    if forbidden in source:
        raise SystemExit('MULTI_CLIENT UI contains forbidden core operation ' + forbidden)
print('MULTI_CLIENT_SAME_COMPANY_REGRESSION_OK')

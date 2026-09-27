#!/usr/bin/env python3
"""Company editor client accounts regression with existing authenticated admin routes."""
from pathlib import Path
import sys
import re
root=Path(sys.argv[1])
screen=(root/'lib/screens/companies_screen.dart').read_text(encoding='utf-8')
section=(root/'lib/widgets/company_client_access_section.dart').read_text(encoding='utf-8')
assert "import '../widgets/company_client_access_section.dart';" in screen
assert "if (AuthService.isAdmin && company != null)" in screen
assert "CompanyClientAccessSection(" in screen
assert screen.index("CompanyClientAccessSection(") < screen.index("title: const Text('Enviar relatório mensal')")
assert "reportEmail: reportEmail" in screen and "reportRecipient: reportRecipient" in screen
assert "if (AuthService.isAdmin && company == null)" in screen
flat=re.sub(r'\\s+','',section)
for token in (
 "AuthService.isAdmin","AuthService.isOfflineMode",
 "AuthService.listUsers()","AuthService.saveUser(",
 "role:'cliente'","allCompanies:false","companyIds:[widget.company.id]",
 "u.companyIds.length==1","u.companyIds.single==widget.company.id",
 "editing!.companyIds.single!=widget.company.id",
 "clientPermissions:permissions","password:secret",
 "Cadastrar acesso do cliente",
 "E-mail de acesso *","Senha inicial (mín. 8 caracteres)",
 "O e-mail de login é independente dos destinatários de relatórios.",
 "Publique o painel da empresa antes de liberar acesso.",
):
 assert re.sub(r'\\s+','',token) in flat,'COMPANY CLIENT ACCESS missing '+token
assert "AppDatabase" not in section
assert "DeviceSyncService" not in section
assert "MediaSyncService" not in section
assert "upsertCompany" not in section
print('COMPANY_CLIENT_ACCESS_REGRESSION_OK')

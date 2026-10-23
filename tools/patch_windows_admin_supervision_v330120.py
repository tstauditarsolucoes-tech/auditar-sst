#!/usr/bin/env python3
"""Windows-only ADM supervision UI, no auth, DB, sync, GS or Android mutation."""
from pathlib import Path
import sys,shutil,hashlib
root=Path(sys.argv[1]);repo=Path(__file__).resolve().parents[1]
admin=root/'lib/screens/admin_center_screen.dart'
target=root/'lib/screens/admin_technician_supervision_screen.dart'
pub=root/'pubspec.yaml'
protected=['lib/database.dart','lib/models.dart','lib/services/auth_service.dart',
 'lib/services/device_sync_service.dart','lib/services/sync_coordinator.dart',
 'lib/services/media_sync_service.dart','lib/services/apps_script_http.dart',
 'lib/screens/users_screen.dart',
 'painel_web_google_apps_script/Code.gs','painel_web_google_apps_script/MultiUser.gs']
before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in protected if (root/p).is_file()}
s=admin.read_text(encoding='utf8')
assert s.count("import 'history_screen.dart';")==1
assert s.count("'Indicadores gerenciais'")==1

assert not target.exists()
s=s.replace("import 'history_screen.dart';","import 'history_screen.dart';\nimport 'admin_technician_supervision_screen.dart';\nimport 'client_treatment_inbox_screen.dart';",1)
# dart format may wrap _action() before title; anchor on unique label.
marker="'Indicadores gerenciais'"
position=s.index(marker)
anchor=s.rfind("_action(",0,position)
assert anchor>=0 and position-anchor<250, 'Admin action structure changed'
line_start=s.rfind("\n",0,anchor)+1
indent=s[line_start:anchor]
assert not indent.strip(), 'Unexpected indentation'
addition="""_action(
  'Atividade dos técnicos',
  'Acompanhe último acesso, atividade recente e produtividade.',
  Icons.manage_history_rounded,
  () => _open(const AdminTechnicianSupervisionScreen()),
),
_action(
  'Comunicação e correções dos clientes',
  'Abra a caixa de entrada de tratativas da equipe.',
  Icons.mark_chat_unread_outlined,
  () => _open(const ClientTreatmentInboxScreen()),
),
"""
s=s[:line_start]+indent+addition.replace("\n","\n"+indent)+s[line_start:]
# Add operational command center and direct ADM account management.
s=s.replace("import 'client_treatment_inbox_screen.dart';",
"""import 'client_treatment_inbox_screen.dart';
import 'admin_operational_hub_screen.dart';""",1)
if s.count("'Atividade dos técnicos'") != 1:
    raise AssertionError('Admin layout changed; refusing duplicate')
pos=s.index("'Atividade dos técnicos'")
a=s.rfind("_action(",0,pos)
line=s.rfind("\n",0,a)+1
indent=s[line:a]
assert a>=0 and not indent.strip()
addition="""_action(
  'Central Operacional ADM',
  'Pendências, prazos, visitas, fotos, histórico e empresas em destaque.',
  Icons.dashboard_customize_outlined,
  () => _open(const AdminOperationalHubScreen()),
),
_action(
  'Criar e gerenciar contas',
  'Criar técnico, cliente ou ADM, definir senha e empresas autorizadas.',
  Icons.person_add_alt_1_rounded,
  () => _open(const UsersScreen()),
),
"""
s=s[:line]+indent+addition.replace("\n","\n"+indent)+s[line:]
admin.write_text(s,encoding='utf8')
shutil.copyfile(repo/'feature_sources/admin_operational_hub_screen_v330122.dart',
                root/'lib/screens/admin_operational_hub_screen.dart')
# Preserve the established client-aware UsersScreen assembled by
# patch_client_accounts_ui_v329106.py and tested by its own regressions.
# User account creation is already server-authenticated via auth_user_save.
# This Windows-only ADM feature must NEVER rewrite existing account roles.
users=root/'lib/screens/users_screen.dart'
assert users.is_file(), 'UsersScreen not assembled'
u=users.read_text(encoding='utf8')
assert 'class UsersScreen extends StatefulWidget' in u
assert 'AuthService.saveUser(' in u
assert 'Novo usuário' in u
assert 'cliente' in u.lower(), 'Client account editor unexpectedly absent'
# users_screen.dart is included in the protected hash list above.

shutil.copyfile(repo/'feature_sources/admin_technician_supervision_screen_v330120.dart',target)
s=pub.read_text(encoding='utf8')
assert s.count('version: 3.30.119+306')==1
pub.write_text(s.replace('version: 3.30.119+306','version: 3.30.122+309',1),encoding='utf8')
for p,h in before.items():assert hashlib.sha256((root/p).read_bytes()).hexdigest()==h,p
print('WINDOWS_ADM_SUPERVISION_V330120_READY')
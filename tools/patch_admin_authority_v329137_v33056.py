#!/usr/bin/env python3
"""Add an Auditar-only administration hub without changing sync/auth/GS/database.

Runs after the existing multiple-client account UI patch for Android and Windows.
"""
from pathlib import Path
import hashlib
import shutil
import sys

root = Path(sys.argv[1])
repo = Path(__file__).resolve().parents[1]
protected = [
    'lib/database.dart',
    'lib/services/auth_service.dart',
    'lib/services/device_sync_service.dart',
    'lib/services/sync_coordinator.dart',
    'lib/services/media_sync_service.dart',
    'lib/services/drive_service.dart',
    'lib/services/apps_script_http.dart',
    'lib/services/ai_assistant_service.dart',
    'painel_web_google_apps_script/Code.gs',
    'painel_web_google_apps_script/MultiUser.gs',
    'painel_web_google_apps_script/ClientPortal.gs',
    'painel_web_google_apps_script/ClientPortal.html',
    'painel_web_google_apps_script/ReportEmail.gs',
]
before = {p: hashlib.sha256((root / p).read_bytes()).hexdigest()
          for p in protected}

def replace(s, old, new, label):
    if new in s:
        return s
    if s.count(old) != 1:
        raise SystemExit('ADMIN_CENTER patch mismatch: ' + label +
                         ' count=' + str(s.count(old)))
    return s.replace(old, new, 1)

target = root / 'lib/services/admin_access_policy.dart'
if target.exists():
    raise SystemExit('Admin policy already installed; refusing duplicate patch.')
shutil.copyfile(repo / 'feature_sources/admin_access_policy_v329137.dart', target)
shutil.copyfile(repo / 'feature_sources/admin_center_screen_v329137.dart',
                root / 'lib/screens/admin_center_screen.dart')
shutil.copyfile(repo / 'feature_sources/admin_access_policy_test_v329137.dart',
                root / 'test/admin_access_policy_test.dart')

home = root / 'lib/screens/home_screen.dart'
s = home.read_text(encoding='utf-8')
s = replace(s, "import '../database.dart';\n",
            "import '../database.dart';\n"
            "import '../services/auth_service.dart';\n", 'home auth import')
s = replace(s, "import 'settings_screen.dart';\n",
            "import 'settings_screen.dart';\n"
            "import 'admin_center_screen.dart';\n", 'home admin import')
s = replace(s, "  List<_ModuleData> get _modules => [\n",
            """  List<_ModuleData> get _modules => [
        if (AuthService.isAdmin)
          _ModuleData(
            title: 'Administração Auditar',
            tutorialId: 'admin',
            subtitle: 'Contas, clientes e gestão administrativa',
            icon: Icons.admin_panel_settings_rounded,
            color: AuditarBrand.greenDark,
            page: () => const AuditarAdminCenterScreen(),
          ),
""", 'home admin module')
home.write_text(s, encoding='utf-8', newline='\n')

# The existing Account & Access menu already opens UsersScreen. The new
# administration hub is reachable through the admin-only Home module.
# Do not rewrite Settings/Users screens assembled from platform-specific bases:
# their widgets and formatting differ between Android and Windows.
changed = [p for p, digest in before.items()
           if hashlib.sha256((root / p).read_bytes()).hexdigest() != digest]
if changed:
    raise SystemExit('PROTECTED FILE MODIFIED: ' + repr(changed))
print('AUDITAR_ADMIN_CENTER_PATCH_OK')
print('AUTH_SYNC_DATABASE_GS_MEDIA_IDENTICAL_OK')

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
            subtitle: 'Contas, clientes e gestão administrativa',
            icon: Icons.admin_panel_settings_rounded,
            color: AuditarBrand.greenDark,
            page: () => const AuditarAdminCenterScreen(),
          ),
""", 'home admin module')
home.write_text(s, encoding='utf-8', newline='\n')

settings = root / 'lib/screens/settings_screen.dart'
s = settings.read_text(encoding='utf-8')
s = replace(s, "import 'users_screen.dart';\n",
            "import 'users_screen.dart';\n"
            "import 'admin_center_screen.dart';\n", 'settings import')
s = replace(s,
    """                      label: const Text('Usuários e acessos'),
                    ),
                  ],""",
    """                      label: const Text('Usuários e acessos'),
                    ),
                    const SizedBox(height: 10),
                    OutlinedButton.icon(
                      onPressed: () => Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => const AuditarAdminCenterScreen(),
                        ),
                      ),
                      icon: const Icon(Icons.admin_panel_settings_rounded),
                      label: const Text('Central Administrativa Auditar'),
                    ),
                  ],""",
    'settings admin button')
settings.write_text(s, encoding='utf-8', newline='\n')

users = root / 'lib/screens/users_screen.dart'
s = users.read_text(encoding='utf-8')
s = replace(s,
    """class UsersScreen extends StatefulWidget {
  const UsersScreen({super.key});""",
    """class UsersScreen extends StatefulWidget {
  final String? initialRoleFilter;
  const UsersScreen({super.key, this.initialRoleFilter});""",
    'users optional client filter')
s = replace(s,
    """  Future<void> _load() async {
    setState(() {""",
    """  Future<void> _load() async {
    if (!AuthService.isAdmin) return;
    setState(() {""",
    'users load guard')
s = replace(s,
    """  Future<void> _edit([AuditarUser? existing]) async {
    final saved = await showDialog<bool>(""",
    """  Future<void> _edit([AuditarUser? existing]) async {
    if (!AuthService.isAdmin) return;
    final saved = await showDialog<bool>(""",
    'users edit guard')
s = replace(s,
    """        user: existing,
        companies: companies,""",
    """        user: existing,
        initialRole: widget.initialRoleFilter,
        companies: companies,""",
    'editor initial role')
s = replace(s,
    """  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Usuários e acessos'),""",
    """  Widget build(BuildContext context) {
    if (!AuthService.isAdmin) {
      return Scaffold(
        appBar: AppBar(title: const Text('Usuários e acessos')),
        body: const Center(child: Text(
          'Somente o administrador Auditar pode gerenciar usuários.')),
      );
    }
    final visibleUsers = widget.initialRoleFilter == null
        ? users
        : users.where((u) => u.role == widget.initialRoleFilter).toList();
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.initialRoleFilter == 'cliente'
            ? 'Acessos dos clientes'
            : 'Usuários e acessos'),""",
    'users role gated build')
s = replace(s,
    """              : ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
                  itemCount: users.length,""",
    """              : visibleUsers.isEmpty
                  ? Center(child: Text(widget.initialRoleFilter == 'cliente'
                      ? 'Nenhum acesso de cliente cadastrado.'
                      : 'Nenhum usuário cadastrado.'))
                  : ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
                  itemCount: visibleUsers.length,""",
    'users list filtering')
s = replace(s, "                    final user = users[index];\n",
            "                    final user = visibleUsers[index];\n",
            'users visible list')
s = replace(s,
    """  final List<Company> companies;

  const _UserEditorDialog({required this.user, required this.companies});""",
    """  final List<Company> companies;
  final String? initialRole;

  const _UserEditorDialog({
    required this.user,
    required this.companies,
    this.initialRole,
  });""",
    'editor optional initial role')
s = replace(s, "    role = user?.role ?? 'tecnico';\n",
            "    role = user?.role ?? widget.initialRole ?? 'tecnico';\n",
            'editor role default')
s = replace(s,
    """  Future<void> _save() async {
    if (name.text.trim().length < 3) {""",
    """  Future<void> _save() async {
    if (!AuthService.isAdmin) {
      setState(() => error = 'Apenas administradores podem salvar acessos.');
      return;
    }
    if (name.text.trim().length < 3) {""",
    'user save guard')
users.write_text(s, encoding='utf-8', newline='\n')

changed = [p for p, digest in before.items()
           if hashlib.sha256((root / p).read_bytes()).hexdigest() != digest]
if changed:
    raise SystemExit('PROTECTED FILE MODIFIED: ' + repr(changed))
print('AUDITAR_ADMIN_CENTER_PATCH_OK')
print('AUTH_SYNC_DATABASE_GS_MEDIA_IDENTICAL_OK')

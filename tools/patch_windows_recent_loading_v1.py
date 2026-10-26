#!/usr/bin/env python3
"""Windows-only progressive loading for recent Auditar SST screens.

Changes assembled presentation screens only, after historical source patches.
Do not alter auth, central routing, sync, DB, GS, photos or Android.
"""
from pathlib import Path
import hashlib
import sys

assert len(sys.argv) == 2, "Use: patch_windows_recent_loading_v1.py APP_DIR"
root = Path(sys.argv[1])
screens = root / "lib/screens"
center = screens / "admin_center_screen.dart"
hub = screens / "admin_operational_hub_screen.dart"
agenda = screens / "technician_agenda_screen.dart"
for path in (center, hub, agenda):
    assert path.is_file(), f"Tela nao localizada: {path}"
protected = [
    "lib/database.dart", "lib/models.dart", "lib/services/auth_service.dart",
    "lib/services/device_sync_service.dart", "lib/services/sync_coordinator.dart",
    "lib/services/media_sync_service.dart", "lib/services/apps_script_http.dart",
    "lib/services/drive_service.dart", "lib/services/web_service_config.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
]
before = {path: hashlib.sha256((root / path).read_bytes()).hexdigest()
          for path in protected if (root / path).is_file()}

def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise AssertionError(f"{label}: esperado um ponto, encontrado {count}")
    return source.replace(old, new, 1)

updated = {}

s = center.read_text(encoding="utf-8")
start = s.index("  Future<void> _refresh() async {")
end = s.index("  Future<void> _open(Widget screen) async {", start)
old = s[start:end]
new = """  Future<void> _refresh() async {
    if (!AuditarAdminAccess.isAdmin(AuthService.currentUser)) {
      if (mounted) setState(() {
        _loading = false;
        _status = 'Acesso reservado ao administrador Auditar.';
      });
      return;
    }
    final actor = AuthService.currentUser?.id;
    setState(() {
      _loading = true;
      _status = '';
    });
    bool failedAccounts = false;
    bool failedCompanies = false;
    // Local data and remote users are independent; don't make the PC wait
    // for a remote round trip before showing the number of companies.
    await Future.wait<void>([
      () async {
        try {
          final companies = await AppDatabase.instance.getCompanies(
            onlyActive: false,
          );
          if (!mounted || !AuditarAdminAccess.isAdmin(AuthService.currentUser) ||
              AuthService.currentUser?.id != actor) return;
          setState(() => _companyCount = companies.length);
        } catch (_) {
          failedCompanies = true;
        }
      }(),
      () async {
        try {
          final accounts = await AuthService.listUsers();
          if (!mounted || !AuditarAdminAccess.isAdmin(AuthService.currentUser) ||
              AuthService.currentUser?.id != actor) return;
          setState(() {
            _userCount = accounts.where((u) => u.active).length;
            _clientCount =
                accounts.where((u) => u.active && u.role == 'cliente').length;
            _technicianCount =
                accounts.where((u) => u.active && u.role == 'tecnico').length;
          });
        } catch (_) {
          failedAccounts = true;
        }
      }(),
    ]);
    if (!mounted || !AuditarAdminAccess.isAdmin(AuthService.currentUser) ||
        AuthService.currentUser?.id != actor) return;
    setState(() {
      _loading = false;
      _status = failedCompanies
          ? 'Não foi possível consultar as empresas neste dispositivo.'
          : failedAccounts
              ? 'Contas indisponíveis na Central Online. '
                  'Os atalhos administrativos continuam disponíveis.'
              : '';
    });
  }

"""
assert "final accounts = await AuthService.listUsers();" in old
assert "getCompanies(" in old
s = s[:start] + new + s[end:]
updated[center] = s

s = hub.read_text(encoding="utf-8")
class_pos = s.index("class _AdminOperationalHubScreenState")
class_brace = s.index("{", class_pos)
s = s[:class_brace + 1] + """
  int _loadedCompanies = 0;
  int _totalCompanies = 0;
""" + s[class_brace + 1:]
start = s.index("  Future<void> _load() async {")
end = s.index("  List<_CompanyPulse> get shown", start)
existing = s[start:end]
assert "getCompanies()" in existing and "Future.wait(" in existing
new = """  Future<void> _load() async {
    if (!adm) {
      if (mounted) setState(() => busy = false);
      return;
    }
    final actor = AuthService.currentUser?.id;
    setState(() {
      busy = true;
      error = '';
      _loadedCompanies = 0;
      _totalCompanies = 0;
    });
    try {
      final companies = (await AppDatabase.instance.getCompanies())
          .where((c) => c.active && AuthService.canAccessCompany(c.id))
          .toList();
      if (!mounted || !adm || actor != AuthService.currentUser?.id) return;
      setState(() => _totalCompanies = companies.length);
      final values = <_CompanyPulse>[];
      for (var i = 0; i < companies.length; i += 4) {
        values.addAll(await Future.wait(companies.skip(i).take(4).map(_read)));
        if (!mounted || !adm || actor != AuthService.currentUser?.id) return;
        // On Windows, render each completed batch while the rest loads.
        // Values represent real data and are never guessed or cached.
        final partial = List<_CompanyPulse>.of(values)
          ..sort((a, b) {
            if (a.error != null && b.error == null) return 1;
            if (b.error != null && a.error == null) return -1;
            final n = b.score.compareTo(a.score);
            return n != 0 ? n : a.company.name.compareTo(b.company.name);
          });
        setState(() {
          data = partial;
          _loadedCompanies = values.length;
        });
      }
      values.sort((a, b) {
        if (a.error != null && b.error == null) return 1;
        if (b.error != null && a.error == null) return -1;
        final n = b.score.compareTo(a.score);
        return n != 0 ? n : a.company.name.compareTo(b.company.name);
      });
      if (mounted && adm && actor == AuthService.currentUser?.id) {
        setState(() {
          data = values;
          busy = false;
          if (!data.any((e) => e.company.id == selected)) selected = '';
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          busy = false;
          error = 'Não foi possível carregar os registros locais.';
        });
      }
    }
  }
"""
s = s[:start] + new + s[end:]
import re
progress_pat = r"(?m)^(?P<indent>[ \t]*)if\s*\(\s*busy\s*\)\s*const\s+LinearProgressIndicator\(\)\s*,\s*$"
match = re.search(progress_pat, s)
assert match, "Progresso atual da Central ADM não encontrado"
indent = match.group("indent")
progress = """if (busy) ...[
  const LinearProgressIndicator(),
  if (_totalCompanies > 0)
    Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
      child: Text('Carregando empresas: ' +
          _loadedCompanies.toString() + ' de ' + _totalCompanies.toString()),
    ),
],"""
s = s[:match.start()] + indent + progress.replace("\n", "\n" + indent) + "\n" + s[match.end():]
updated[hub] = s

s = agenda.read_text(encoding="utf-8")
start = s.index("  Future<void> _load() async {")
end = s.index("  String label(", start)
existing = s[start:end]
assert "getCompanies()" in existing and "operation" in existing
new = """  Future<void> _load() async {
    if (!allowed) return;
    setState(() {
      busy = true;
      error = '';
    });
    try {
      // Three independent reads begin together. The existing API,
      // authorized companies and visible task data remain identical.
      final parts = await Future.wait<dynamic>([
        AppDatabase.instance.getCompanies(),
        AuthService.isAdmin
            ? AuthService.listUsers()
            : Future<List<AuditarUser>>.value(<AuditarUser>[]),
        _post({'operation': 'list'}),
      ]);
      final cs = (parts[0] as List<Company>)
          .where((c) => c.active && AuthService.canAccessCompany(c.id))
          .toList();
      final us = (parts[1] as List<AuditarUser>)
          .where((u) => u.active && u.role == 'tecnico')
          .toList();
      final resp = parts[2] as Map<String, dynamic>;
      final raw = resp['tasks'];
      if (mounted) {
        setState(() {
          companies = cs;
          technicians = us;
          tasks = raw is List
              ? raw.whereType<Map>()
                  .map((e) => Map<String, dynamic>.from(e)).toList()
              : [];
          busy = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          busy = false;
          error = e.toString().replaceFirst('Bad state: ', '');
        });
      }
    }
  }
"""
s = s[:start] + new + s[end:]
updated[agenda] = s

# No intermediate partial writes if any anchor fails.
for path, content in updated.items():
    path.write_text(content, encoding="utf-8", newline="\n")

for path, digest in before.items():
    if hashlib.sha256((root / path).read_bytes()).hexdigest() != digest:
        raise AssertionError(f"Arquivo protegido modificado: {path}")

assert "Future.wait<void>" in updated[center]
assert "_loadedCompanies = values.length" in updated[hub]
assert "Future.wait<dynamic>" in updated[agenda]
assert "agenda_tecnicos_v1" in updated[agenda]
print("WINDOWS_RECENT_LOADING_OPTIMIZED_OK: independent requests, partial data and unchanged core.")

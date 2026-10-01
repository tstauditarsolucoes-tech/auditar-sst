#!/usr/bin/env python3
"""Auditar SST v3.29.143 / v3.30.62

Additive field-productivity package:
- global search across existing records;
- technician command center;
- admin shortcut to existing data-safety diagnostics;
- optional reuse of last sector/location in Express Round.

No schema, sync protocol, auth, AI route, media transport, Drive, or Apps Script changes.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv) < 3:
    raise SystemExit("uso: patch_field_productivity_v329143_v33062.py <APP_DIR> <android|windows>")

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
repo = Path(__file__).resolve().parents[1]
if platform not in ("android", "windows"):
    raise SystemExit("plataforma invalida")

def read(rel):
    return (root / rel).read_text(encoding="utf-8")

def write(rel, value):
    (root / rel).write_text(value, encoding="utf-8", newline="\n")

def once(text, old, new, label):
    if new in text:
        return text
    if text.count(old) != 1:
        raise RuntimeError(f"{label}: esperado 1, encontrado {text.count(old)}")
    return text.replace(old, new, 1)

protected = [
    "lib/database.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/auth_service.dart",
    "lib/services/drive_service.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/ai_assistant_service.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
    "painel_web_google_apps_script/ClientPortal.html",
    "painel_web_google_apps_script/ReportEmail.gs",
]
before = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected
}

# New read-only/additive screens.
for src_name, dst_name in [
    ("global_search_screen_v329143.dart", "global_search_screen.dart"),
    ("field_command_center_screen_v329143.dart", "field_command_center_screen.dart"),
]:
    src = repo / "feature_sources" / src_name
    dst = root / "lib" / "screens" / dst_name
    if not src.exists():
        raise RuntimeError("fonte ausente: " + src_name)
    shutil.copyfile(src, dst)

# Home: one operational module + global search in the top bar.
rel = "lib/screens/home_screen.dart"
s = read(rel)
s = once(
    s,
    "import 'field_quick_screen.dart';\n",
    "import 'field_quick_screen.dart';\n"
    "import 'field_command_center_screen.dart';\n"
    "import 'global_search_screen.dart';\n",
    "imports Home",
)
module_anchor = "  List<_ModuleData> get _modules => [\n"
if module_anchor not in s:
    raise RuntimeError("lista de modulos Home ausente")
module = """        _ModuleData(
          title: 'Central do Técnico',
          tutorialId: 'field_center',
          subtitle: 'Prioridades, ações vencidas e rotina do dia',
          icon: Icons.engineering_outlined,
          color: AuditarBrand.greenDark,
          page: () => const FieldCommandCenterScreen(),
        ),
"""
if "tutorialId: 'field_center'" not in s:
    s = s.replace(module_anchor, module_anchor + module, 1)

# Desktop must also expose the new module.
s = once(
    s,
    "      'companies',\n      'non_conformities',",
    "      'field_center',\n      'companies',\n      'non_conformities',",
    "desktop main",
)
# There can be a second set used by navigation. Add only if still absent there.
nav_anchor = "  List<_ModuleData> get _desktopNavigationModules"
nav_pos = s.find(nav_anchor)
if nav_pos >= 0:
    tail = s[nav_pos:]
    target = "      'companies',\n      'history',"
    if target in tail and "'field_center'," not in tail.split("};", 1)[0]:
        tail = tail.replace(
            target,
            "      'field_center',\n      'companies',\n      'history',",
            1,
        )
        s = s[:nav_pos] + tail

appbar_anchor = """        actions: [
          IconButton(
            tooltip: 'Atualizar dados',"""
appbar_new = """        actions: [
          IconButton(
            tooltip: 'Busca global',
            onPressed: () => _open(const GlobalSearchScreen()),
            icon: const Icon(Icons.search_rounded),
          ),
          IconButton(
            tooltip: 'Atualizar dados',"""
s = once(s, appbar_anchor, appbar_new, "busca global Home")
write(rel, s)

# Company detail: company-scoped search shortcut.
rel = "lib/screens/company_detail_screen.dart"
s = read(rel)
s = once(
    s,
    "import 'history_screen.dart';\n",
    "import 'history_screen.dart';\nimport 'global_search_screen.dart';\n",
    "company search import",
)
appbar = """        appBar: AppBar(
          title: Text(
            widget.company.name,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          bottom:"""
appbar2 = """        appBar: AppBar(
          title: Text(
            widget.company.name,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          actions: [
            IconButton(
              tooltip: 'Pesquisar nesta empresa',
              onPressed: () => _open(GlobalSearchScreen(company: widget.company)),
              icon: const Icon(Icons.search_rounded),
            ),
          ],
          bottom:"""
s = once(s, appbar, appbar2, "company search action")
write(rel, s)

# Admin center: reuse the existing DataSafetyScreen instead of duplicating diagnostics.
rel = "lib/screens/admin_center_screen.dart"
s = read(rel)
s = once(
    s,
    "import 'dashboard_screen.dart';\n",
    "import 'dashboard_screen.dart';\nimport 'data_safety_screen.dart';\n",
    "admin diagnostics import",
)
diag_anchor = """          _action('Indicadores gerenciais',
              'Consultar os indicadores disponíveis no aplicativo.',
              Icons.bar_chart_rounded,
              () => _open(const DashboardScreen())),"""
diag_new = diag_anchor + """
          _action('Diagnóstico técnico',
              'Fila de dados, fotos, relatórios, último envio e backup local.',
              Icons.health_and_safety_outlined,
              () => _open(const DataSafetyScreen())),"""
s = once(s, diag_anchor, diag_new, "admin diagnostics action")
write(rel, s)

# Express Round: save the last context locally and offer an explicit reuse button.
# No record/schema/sync change.
rel = "lib/screens/express_round_screen.dart"
s = read(rel)
s = once(
    s,
    "  String? sectorId;\n",
    "  String? sectorId;\n  String lastSectorId = '';\n  String lastLocation = '';\n",
    "Ronda context fields",
)
load_anchor = """    final storedConclusion =
        (await db.getSetting('express_round_conclusion_$activeRound')).trim();"""
load_new = load_anchor + """
    final storedLastSector =
        (await db.getSetting('express_round_last_sector_${widget.company.id}')).trim();
    final storedLastLocation =
        (await db.getSetting('express_round_last_location_${widget.company.id}')).trim();"""
s = once(s, load_anchor, load_new, "Ronda load last context")

state_anchor = """      sectors = loaded;
      sectorId = loaded.isEmpty ? null : loaded.first.id;
      roundRecords = current;"""
state_new = """      sectors = loaded;
      lastSectorId = storedLastSector;
      lastLocation = storedLastLocation;
      sectorId = loaded.isEmpty ? null : loaded.first.id;
      roundRecords = current;"""
s = once(s, state_anchor, state_new, "Ronda state last context")

method_anchor = "  Future<void> _pickPhoto(ImageSource source) async {\n"
method = """  void _reuseLastContext() {
    if (lastSectorId.isEmpty && lastLocation.isEmpty) return;
    setState(() {
      if (lastSectorId.isNotEmpty &&
          sectors.any((sector) => sector.id == lastSectorId)) {
        sectorId = lastSectorId;
      }
      if (lastLocation.isNotEmpty) location.text = lastLocation;
    });
    _message('Último setor/local reaplicado. Confira antes de salvar.');
  }

"""
if "_reuseLastContext()" not in s:
    if method_anchor not in s:
        raise RuntimeError("Ronda pick photo anchor ausente")
    s = s.replace(method_anchor, method + method_anchor, 1)

save_anchor = """      await AppDatabase.instance.upsertSstRecord(record);
      if (photoPath.trim().isNotEmpty) {"""
save_new = """      await AppDatabase.instance.upsertSstRecord(record);
      final savedLocation = location.text.trim();
      await AppDatabase.instance.setSetting(
        'express_round_last_sector_${widget.company.id}',
        sectorId ?? '',
      );
      if (savedLocation.isNotEmpty) {
        await AppDatabase.instance.setSetting(
          'express_round_last_location_${widget.company.id}',
          savedLocation,
        );
      }
      lastSectorId = sectorId ?? '';
      if (savedLocation.isNotEmpty) lastLocation = savedLocation;
      if (photoPath.trim().isNotEmpty) {"""
s = once(s, save_anchor, save_new, "Ronda persist context")

ui_anchor = """                      TextField(
                        controller: location,
                        decoration: const InputDecoration(
                          labelText: 'Local exato (opcional)',
                          hintText: 'Ex.: ao lado da betoneira / 2º pavimento',
                        ),
                      ),
                      if (!_isConformity) ...["""
ui_new = """                      TextField(
                        controller: location,
                        decoration: const InputDecoration(
                          labelText: 'Local exato (opcional)',
                          hintText: 'Ex.: ao lado da betoneira / 2º pavimento',
                        ),
                      ),
                      if (lastSectorId.isNotEmpty || lastLocation.isNotEmpty)
                        Align(
                          alignment: Alignment.centerLeft,
                          child: TextButton.icon(
                            onPressed: _reuseLastContext,
                            icon: const Icon(Icons.repeat_rounded, size: 18),
                            label: const Text('Usar último setor/local'),
                          ),
                        ),
                      if (!_isConformity) ...["""
s = once(s, ui_anchor, ui_new, "Ronda reuse button")
write(rel, s)

# Release version only.
rel = "pubspec.yaml"
pub = read(rel)
old_version, new_version = (
    ("3.29.142+284", "3.29.143+285")
    if platform == "android"
    else ("3.30.61+248", "3.30.62+249")
)
marker = "version: " + old_version
if pub.count(marker) != 1:
    raise RuntimeError("versao esperada ausente: " + old_version)
pub = pub.replace(marker, "version: " + new_version, 1)
write(rel, pub)

changed = [
    name for name, digest in before.items()
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

assert (root / "lib/screens/global_search_screen.dart").exists()
assert (root / "lib/screens/field_command_center_screen.dart").exists()
assert "GlobalSearchScreen()" in read("lib/screens/home_screen.dart")
assert "FieldCommandCenterScreen()" in read("lib/screens/home_screen.dart")
assert "GlobalSearchScreen(company: widget.company)" in read("lib/screens/company_detail_screen.dart")
assert "DataSafetyScreen()" in read("lib/screens/admin_center_screen.dart")
assert "Usar último setor/local" in read("lib/screens/express_round_screen.dart")
assert "express_round_last_location_" in read("lib/screens/express_round_screen.dart")
assert "version: " + new_version in read("pubspec.yaml")

print("FIELD_PRODUCTIVITY_PACKAGE_OK", platform, new_version)
print("SYNC_DB_AUTH_MEDIA_AI_GS_BYTE_IDENTICAL_OK")

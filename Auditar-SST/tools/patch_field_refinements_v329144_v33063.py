#!/usr/bin/env python3
"""Auditar SST v3.29.144 / v3.30.63

Second additive field-productivity pack:
- quick search from Home and company screen using the existing Central Inteligente;
- company activity timeline;
- explicit reuse of last sector/location in Express Round.

No schema, sync protocol, auth, AI, media transport, Drive or Apps Script changes.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv) < 3:
    raise SystemExit("uso: patch_field_refinements_v329144_v33063.py <APP_DIR> <android|windows>")

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

# ---------------------------------------------------------------------------
# 1) Company timeline (read-only over existing data)
# ---------------------------------------------------------------------------
src = repo / "feature_sources/company_timeline_screen_v329144.dart"
dst = root / "lib/screens/company_timeline_screen.dart"
if not src.exists():
    raise RuntimeError("fonte da linha do tempo ausente")
shutil.copyfile(src, dst)

# ---------------------------------------------------------------------------
# 2) Central Inteligente can open directly on Search and preselect company.
# ---------------------------------------------------------------------------
rel = "lib/screens/field_intelligence_center_screen.dart"
s = read(rel)
old_widget = """class FieldIntelligenceCenterScreen extends StatefulWidget {
  const FieldIntelligenceCenterScreen({super.key});

  @override"""
new_widget = """class FieldIntelligenceCenterScreen extends StatefulWidget {
  final int initialTab;
  final String initialCompanyId;

  const FieldIntelligenceCenterScreen({
    super.key,
    this.initialTab = 0,
    this.initialCompanyId = '',
  });

  @override"""
s = once(s, old_widget, new_widget, "Central constructor")

old_init = """  @override
  void initState() {
    super.initState();
    tabs = TabController(length: AuthService.isAdmin ? 4 : 3, vsync: this);
    search.addListener(() {"""
new_init = """  @override
  void initState() {
    super.initState();
    companyId = widget.initialCompanyId;
    final tabCount = AuthService.isAdmin ? 4 : 3;
    final initial =
        widget.initialTab < 0
            ? 0
            : (widget.initialTab >= tabCount ? tabCount - 1 : widget.initialTab);
    tabs = TabController(length: tabCount, initialIndex: initial, vsync: this);
    search.addListener(() {"""
s = once(s, old_init, new_init, "Central initial context")
write(rel, s)

# ---------------------------------------------------------------------------
# 3) Home quick search: one tap goes straight to the Central search tab.
# ---------------------------------------------------------------------------
rel = "lib/screens/home_screen.dart"
s = read(rel)
appbar = """        actions: [
          IconButton(
            tooltip: 'Atualizar dados',"""
appbar_new = """        actions: [
          IconButton(
            tooltip: 'Busca global',
            onPressed: () => _open(
              const FieldIntelligenceCenterScreen(initialTab: 1),
            ),
            icon: const Icon(Icons.search_rounded),
          ),
          IconButton(
            tooltip: 'Atualizar dados',"""
s = once(s, appbar, appbar_new, "Home quick search")
write(rel, s)

# ---------------------------------------------------------------------------
# 4) Company screen: scoped search + timeline shortcut.
# ---------------------------------------------------------------------------
rel = "lib/screens/company_detail_screen.dart"
s = read(rel)
s = once(
    s,
    "import 'history_screen.dart';\n",
    "import 'history_screen.dart';\n"
    "import 'field_intelligence_center_screen.dart';\n"
    "import 'company_timeline_screen.dart';\n",
    "Company imports",
)

appbar = """        appBar: AppBar(
          title: Text(
            widget.company.name,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          bottom:"""
appbar_new = """        appBar: AppBar(
          title: Text(
            widget.company.name,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          actions: [
            IconButton(
              tooltip: 'Pesquisar nesta empresa',
              onPressed: () => _open(
                FieldIntelligenceCenterScreen(
                  initialTab: 1,
                  initialCompanyId: widget.company.id,
                ),
              ),
              icon: const Icon(Icons.search_rounded),
            ),
          ],
          bottom:"""
s = once(s, appbar, appbar_new, "Company scoped search")

trace_anchor = """          _shortcut(
            icon: Icons.verified_user_outlined,
            title: 'Rastreabilidade',
            subtitle: 'Veja quem alterou, quando e em qual dispositivo',
            onTap: () => _open(AuditTrailScreen(company: widget.company)),
          ),
          const SizedBox(height: 14),"""
trace_new = """          _shortcut(
            icon: Icons.verified_user_outlined,
            title: 'Rastreabilidade',
            subtitle: 'Veja quem alterou, quando e em qual dispositivo',
            onTap: () => _open(AuditTrailScreen(company: widget.company)),
          ),
          const SizedBox(height: 10),
          _shortcut(
            icon: Icons.timeline_rounded,
            title: 'Linha do tempo da empresa',
            subtitle: 'Vistorias, DDS, treinamentos, segurança e correções em ordem cronológica',
            onTap: () => _open(CompanyTimelineScreen(company: widget.company)),
          ),
          const SizedBox(height: 14),"""
s = once(s, trace_anchor, trace_new, "Company timeline shortcut")
write(rel, s)

# ---------------------------------------------------------------------------
# 5) Express Round: reuse last context only when the technician asks for it.
#    Settings table already exists; no DB migration and no sync payload change.
# ---------------------------------------------------------------------------
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
s = once(s, state_anchor, state_new, "Ronda state context")

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
s = once(s, ui_anchor, ui_new, "Ronda reuse UI")
write(rel, s)

# ---------------------------------------------------------------------------
# 6) Release version
# ---------------------------------------------------------------------------
rel = "pubspec.yaml"
pub = read(rel)
old_version, new_version = (
    ("3.29.143+285", "3.29.144+286")
    if platform == "android"
    else ("3.30.62+249", "3.30.63+250")
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

assert "initialCompanyId" in read("lib/screens/field_intelligence_center_screen.dart")
assert "FieldIntelligenceCenterScreen(initialTab: 1)" in read("lib/screens/home_screen.dart")
assert "CompanyTimelineScreen(company: widget.company)" in read("lib/screens/company_detail_screen.dart")
assert "Usar último setor/local" in read("lib/screens/express_round_screen.dart")
assert "version: " + new_version in read("pubspec.yaml")

print("FIELD_REFINEMENTS_OK", platform, new_version)
print("SYNC_DB_AUTH_MEDIA_AI_GS_BYTE_IDENTICAL_OK")

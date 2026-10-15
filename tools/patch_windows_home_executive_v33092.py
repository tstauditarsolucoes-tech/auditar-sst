#!/usr/bin/env python3
"""Auditar SST Windows v3.30.92 — Home executiva visivelmente desktop.

Mudança exclusivamente de apresentação/navegação no Windows:
- redesenha somente _desktopBody da Home;
- destaca Central Executiva/Painel;
- preserva mobile, banco, sync, auth, HTTP, mídia, IA e Apps Script.
"""
from pathlib import Path
import hashlib
import sys

if len(sys.argv) < 2:
    raise SystemExit("uso: patch_windows_home_executive_v33092.py <APP_DIR>")

root = Path(sys.argv[1])

def read(rel):
    return (root / rel).read_text(encoding="utf-8")

def write(rel, value):
    (root / rel).write_text(value, encoding="utf-8", newline="\n")

protected = [
    "lib/database.dart",
    "lib/models.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/auth_service.dart",
    "lib/services/drive_service.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/ai_assistant_service.dart",
    "lib/services/offline_report_knowledge_service.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
    "painel_web_google_apps_script/ClientPortal.html",
    "painel_web_google_apps_script/ReportEmail.gs",
]
before = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected if (root / name).exists()
}

rel = "lib/screens/home_screen.dart"
s = read(rel)

# Import apenas da tela já existente, sem criar novo fluxo.
imp = "import 'field_operational_control_screen.dart';\n"
if imp not in s:
    anchor = "import 'field_intelligence_center_screen.dart';\n"
    if anchor not in s:
        # fallback após um import de tela estável
        anchor = "import 'history_screen.dart';\n"
    if anchor not in s:
        raise RuntimeError("anchor de import da Home não encontrado")
    s = s.replace(anchor, anchor + imp, 1)

start = s.find("  Widget _desktopBody() {")
if start < 0:
    raise RuntimeError("_desktopBody não encontrado")

# Localiza o fechamento do método por balanceamento de chaves.
brace = s.find("{", start)
depth = 0
end = None
for i in range(brace, len(s)):
    ch = s[i]
    if ch == "{":
        depth += 1
    elif ch == "}":
        depth -= 1
        if depth == 0:
            end = i + 1
            break
if end is None:
    raise RuntimeError("fim de _desktopBody não encontrado")

new_method = r'''  Widget _desktopBody() {
    return Row(
      children: [
        Container(
          width: 276,
          decoration: const BoxDecoration(
            color: Colors.white,
            border: Border(right: BorderSide(color: AuditarBrand.line)),
          ),
          child: Column(
            children: [
              Container(
                width: double.infinity,
                padding: const EdgeInsets.fromLTRB(18, 20, 18, 16),
                decoration: const BoxDecoration(
                  color: AuditarBrand.navy,
                ),
                child: const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'AUDITAR SST',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.w900,
                        letterSpacing: .8,
                      ),
                    ),
                    SizedBox(height: 3),
                    Text(
                      'Central Executiva',
                      style: TextStyle(
                        color: Color(0xFFA0E9D0),
                        fontSize: 12,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ],
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(12, 14, 12, 8),
                child: SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: () => _open(
                      const FieldOperationalControlScreen(),
                    ),
                    icon: const Icon(Icons.query_stats_rounded),
                    label: const Text('Central de Gestão'),
                  ),
                ),
              ),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: () => _open(const NewInspectionScreen()),
                    icon: const Icon(Icons.add_a_photo_outlined),
                    label: const Text('Nova vistoria'),
                  ),
                ),
              ),
              const Padding(
                padding: EdgeInsets.fromLTRB(18, 18, 18, 7),
                child: Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    'NAVEGAÇÃO',
                    style: TextStyle(
                      color: AuditarBrand.neutral,
                      fontSize: 10.5,
                      fontWeight: FontWeight.w900,
                      letterSpacing: .7,
                    ),
                  ),
                ),
              ),
              Expanded(
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(8, 0, 8, 12),
                  children: [
                    ListTile(
                      dense: true,
                      leading: const Icon(
                        Icons.space_dashboard_outlined,
                        color: AuditarBrand.greenDark,
                      ),
                      title: const Text(
                        'Painel executivo',
                        style: TextStyle(fontWeight: FontWeight.w900),
                      ),
                      subtitle: const Text(
                        'Indicadores e prioridades',
                        style: TextStyle(fontSize: 10),
                      ),
                      onTap: () => _open(
                        const FieldOperationalControlScreen(),
                      ),
                    ),
                    const Divider(),
                    for (final module in _modules)
                      ListTile(
                        dense: true,
                        leading: Icon(module.icon, color: module.color),
                        title: Text(
                          module.title,
                          style: const TextStyle(fontWeight: FontWeight.w700),
                        ),
                        onTap: () => _open(module.page()),
                      ),
                    const Divider(),
                    ListTile(
                      dense: true,
                      leading: const Icon(Icons.settings_outlined),
                      title: const Text(
                        'Configurações e sincronização',
                        style: TextStyle(fontWeight: FontWeight.w700),
                      ),
                      onTap: () => _open(const SettingsScreen()),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        Expanded(
          child: RefreshIndicator(
            onRefresh: _refresh,
            child: ListView(
              padding: const EdgeInsets.fromLTRB(26, 24, 26, 36),
              children: [
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [
                        AuditarBrand.navy,
                        Color(0xFF173F4B),
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(22),
                  ),
                  child: Row(
                    children: [
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'CENTRAL EXECUTIVA AUDITAR SST',
                              style: TextStyle(
                                color: Color(0xFFA0E9D0),
                                fontSize: 11,
                                fontWeight: FontWeight.w900,
                                letterSpacing: .8,
                              ),
                            ),
                            SizedBox(height: 8),
                            Text(
                              'Gestão SST em uma visão única',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 28,
                                fontWeight: FontWeight.w900,
                              ),
                            ),
                            SizedBox(height: 7),
                            Text(
                              'Indicadores, pendências, evolução, evidências e prioridades para decisão.',
                              style: TextStyle(
                                color: Colors.white70,
                                fontSize: 13,
                                height: 1.35,
                              ),
                            ),
                            SizedBox(height: 16),
                            Wrap(
                              spacing: 7,
                              runSpacing: 7,
                              children: [
                                _ExecutiveTag('Painel Executivo'),
                                _ExecutiveTag('Evolução mensal'),
                                _ExecutiveTag('Antes × Depois'),
                                _ExecutiveTag('Prioridades'),
                              ],
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 24),
                      Column(
                        children: [
                          FilledButton.icon(
                            style: FilledButton.styleFrom(
                              backgroundColor: Colors.white,
                              foregroundColor: AuditarBrand.navy,
                              padding: const EdgeInsets.symmetric(
                                horizontal: 18,
                                vertical: 15,
                              ),
                            ),
                            onPressed: () => _open(
                              const FieldOperationalControlScreen(),
                            ),
                            icon: const Icon(Icons.present_to_all_rounded),
                            label: const Text(
                              'Abrir Central de Gestão',
                              style: TextStyle(fontWeight: FontWeight.w900),
                            ),
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            'Selecione a empresa para abrir o Painel Executivo',
                            style: TextStyle(
                              color: Colors.white60,
                              fontSize: 10,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                _overviewPanel(desktop: true),
                const SizedBox(height: 22),
                Row(
                  children: [
                    Expanded(
                      child: _sectionHeader(
                        'Acompanhar agora',
                        'Atalhos para o que exige decisão e acompanhamento',
                      ),
                    ),
                    OutlinedButton.icon(
                      onPressed: () => _open(const SettingsScreen()),
                      icon: const Icon(Icons.sync_rounded),
                      label: const Text('Sincronização'),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                _moduleWrap(
                  _modules.take(4).toList(),
                  minWidth: 210,
                  maxColumns: 4,
                ),
                const SizedBox(height: 22),
                _routinePanel(),
                const SizedBox(height: 22),
                _sectionHeader(
                  'Gestão completa',
                  'Cadastros, pessoas, capacitações, CIPA, checklists e indicadores',
                ),
                const SizedBox(height: 10),
                _moduleWrap(
                  _modules.skip(4).toList(),
                  minWidth: 230,
                  maxColumns: 3,
                ),
                const SizedBox(height: 12),
                _companyResourcesCard(),
                const SizedBox(height: 20),
                const Center(
                  child: Text(
                    'Auditar SST para Windows • versão 3.30.92',
                    style: TextStyle(
                      fontSize: 11,
                      color: Colors.black45,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }'''

s = s[:start] + new_method + s[end:]

# Widget mínimo de apoio, inserido antes de _ModuleData (ou no fim).
helper = r'''
class _ExecutiveTag extends StatelessWidget {
  final String label;

  const _ExecutiveTag(this.label);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: .08),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(
          color: Colors.white.withValues(alpha: .14),
        ),
      ),
      child: Text(
        label,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 10.5,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}

'''
if "class _ExecutiveTag" not in s:
    anchor = "class _ModuleData"
    pos = s.find(anchor)
    if pos < 0:
        raise RuntimeError("_ModuleData não encontrado para inserir helper")
    s = s[:pos] + helper + s[pos:]

write(rel, s)

# Versiona apenas o Windows montado.
pub_rel = "pubspec.yaml"
pub = read(pub_rel)
old = "version: 3.30.91+278"
new = "version: 3.30.92+279"
if pub.count(old) != 1:
    raise RuntimeError("versão base v3.30.91 não encontrada")
write(pub_rel, pub.replace(old, new, 1))

after = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected if (root / name).exists()
}
changed = [name for name in before if before[name] != after[name]]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

final_home = read(rel)
assert "CENTRAL EXECUTIVA AUDITAR SST" in final_home
assert "Gestão SST em uma visão única" in final_home
assert "Abrir Central de Gestão" in final_home
assert "versão 3.30.92" in final_home
assert "Widget _mobileBody()" in final_home
assert "version: 3.30.92+279" in read(pub_rel)

print("WINDOWS_HOME_EXECUTIVE_LAYOUT_OK")
print("WINDOWS_VERSION_3_30_92_OK")
print("MOBILE_HOME_PRESERVED_OK")
print("PROTECTED_CORE_BYTE_IDENTICAL_OK")

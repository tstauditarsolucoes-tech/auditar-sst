#!/usr/bin/env python3
"""Windows-only desktop presentation pass for Auditar SST v3.30.118.

Targets assembled Flutter screens AFTER all existing field/NR18/navigation
patches. Mobile Android sources, database, auth, sync, photos, media, GS and
report renderers must remain untouched. Fails closed on unexpected anchors.
"""
from pathlib import Path
import hashlib
import re
import sys

assert len(sys.argv) == 2, "uso: patch_windows_desktop_ux_v330118.py APP_DIR"
root = Path(sys.argv[1])
screens = root / "lib" / "screens"
paths = {
    "visit": screens / "quick_visit_screen.dart",
    "cipa": screens / "cipa_management_screen.dart",
    "timeline": screens / "company_timeline_screen.dart",
    "photos": screens / "evidence_backup_screen.dart",
    "login": screens / "login_screen.dart",
}
for path in paths.values():
    assert path.is_file(), f"Tela Windows nao localizada: {path}"

protected_names = [
    "lib/database.dart",
    "lib/models.dart",
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
protected = {
    str(p): hashlib.sha256(p.read_bytes()).hexdigest()
    for name in protected_names
    for p in [root / name] if p.exists()
}
pre = {k: v.read_text(encoding="utf-8") for k, v in paths.items()}

def one(value, marker, replacement, name):
    count = value.count(marker)
    if count != 1:
        raise RuntimeError(f"{name}: marcador encontrado {count} vez(es)")
    return value.replace(marker, replacement, 1)

# 1. Left-side company selector and independent right-side task workspace.
s = pre["visit"]
s = one(s, "constraints: const BoxConstraints(maxWidth: 1000),",
        "constraints: const BoxConstraints(maxWidth: 1560),",
        "visita largura util PC")
s = one(
    s, "child: _selected == null ? _picker() : _tasks(),",
    """child: LayoutBuilder(
                  builder: (context, size) {
                    if (size.maxWidth < 920) {
                      return _selected == null ? _picker() : _tasks();
                    }
                    return Row(
                      children: [
                        SizedBox(
                          width: 356,
                          child: DecoratedBox(
                            decoration: const BoxDecoration(
                              border: Border(
                                right: BorderSide(color: Color(0xFFDAE1E8)),
                              ),
                            ),
                            child: _picker(),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _selected == null
                              ? Center(
                                  child: Padding(
                                    padding: const EdgeInsets.all(32),
                                    child: Column(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Icon(
                                          Icons.business_center_outlined,
                                          size: 52,
                                          color: Colors.blueGrey,
                                        ),
                                        SizedBox(height: 14),
                                        Text(
                                          'Selecione uma empresa ou obra à esquerda',
                                          textAlign: TextAlign.center,
                                          style: TextStyle(
                                            fontSize: 19,
                                            fontWeight: FontWeight.w800,
                                          ),
                                        ),
                                        SizedBox(height: 7),
                                        Text(
                                          'As atividades aparecerão aqui sem trocar de tela.',
                                          textAlign: TextAlign.center,
                                        ),
                                      ],
                                    ),
                                  ),
                                )
                              : _tasks(),
                        ),
                      ],
                    );
                  },
                ),""",
    "visita seletor e tarefas simultaneos")
paths["visit"].write_text(s, encoding="utf-8", newline="\n")

# 2. CIPA: keep the 10 tab pages, add desktop navigation at left. No
# business-method changes and no new database access.
s = pre["cipa"]
s = one(
    s, "bottom: const TabBar(",
    "bottom: MediaQuery.sizeOf(context).width >= 960 ? null : const TabBar(",
    "CIPA tabbar apenas compacta")
cipa_tab = re.compile(
    r"TabBarView\(\s*children:\s*\[\s*"
    r"_panelTab\(\),\s*_mandateTab\(\),\s*_membersTab\(\),\s*"
    r"_meetingsTab\(\),\s*_minutesTab\(\),\s*_actionsTab\(\),\s*"
    r"_electionTab\(\),\s*_trainingTab\(\),\s*_documentsTab\(\),\s*"
    r"_historyTab\(\),\s*\],\s*\),"
)
matches = list(cipa_tab.finditer(s))
assert len(matches) == 1, f"CIPA TabBarView encontrada {len(matches)} vez(es)"
tabs = """Builder(
              builder: (tabsContext) {
                final controller = DefaultTabController.of(tabsContext);
                final pages = TabBarView(
                  children: [
                    _panelTab(),
                    _mandateTab(),
                    _membersTab(),
                    _meetingsTab(),
                    _minutesTab(),
                    _actionsTab(),
                    _electionTab(),
                    _trainingTab(),
                    _documentsTab(),
                    _historyTab(),
                  ],
                );
                if (MediaQuery.sizeOf(tabsContext).width < 960) {
                  return pages;
                }
                const names = <String>[
                  'Painel', 'Mandato', 'Membros', 'Reuniões', 'Atas',
                  'Ações', 'Eleição', 'Treinamentos', 'Documentos', 'Histórico',
                ];
                const icons = <IconData>[
                  Icons.dashboard_outlined,
                  Icons.calendar_month_outlined,
                  Icons.groups_outlined,
                  Icons.event_note_outlined,
                  Icons.article_outlined,
                  Icons.task_alt_outlined,
                  Icons.how_to_vote_outlined,
                  Icons.school_outlined,
                  Icons.folder_outlined,
                  Icons.history_outlined,
                ];
                return Row(
                  children: [
                    SizedBox(
                      width: 230,
                      child: ColoredBox(
                        color: const Color(0xFFF4F7FA),
                        child: AnimatedBuilder(
                          animation: controller,
                          builder: (context, _) => ListView.builder(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 9, vertical: 12),
                            itemCount: names.length,
                            itemBuilder: (context, index) => Padding(
                              padding: const EdgeInsets.only(bottom: 3),
                              child: ListTile(
                                dense: true,
                                selected: controller.index == index,
                                selectedTileColor: const Color(0xFFDCEEE9),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(10)),
                                leading: Icon(icons[index], size: 20),
                                title: Text(names[index],
                                  style: const TextStyle(fontSize: 13.5)),
                                onTap: () => controller.animateTo(index),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                    const VerticalDivider(width: 1),
                    Expanded(child: pages),
                  ],
                );
              },
            ),"""
s = s[:matches[0].start()] + tabs + s[matches[0].end():]
paths["cipa"].write_text(s, encoding="utf-8", newline="\n")

# 3. Timeline: persistent left filters + a readable right activity stream.
# Every event still opens its original destination via _eventCard.
s = pre["timeline"]
s = one(
    s, "    final rows = visible;\n    return Scaffold(",
    """    final rows = visible;
    if (!loading && MediaQuery.sizeOf(context).width >= 960) {
      return _windowsTimelineDesktop(rows);
    }
    return Scaffold(""",
    "linha do tempo layout desktop")
anchor = "  Widget _eventCard(_TimelineEvent event) {"
method = """  Widget _windowsTimelineDesktop(List<_TimelineEvent> rows) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Linha do tempo • Área de trabalho'),
        actions: [
          IconButton(
            tooltip: 'Atualizar',
            onPressed: _load,
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: Row(
        children: [
          SizedBox(
            width: 268,
            child: ColoredBox(
              color: const Color(0xFFF4F7FA),
              child: ListView(
                padding: const EdgeInsets.fromLTRB(14, 18, 14, 24),
                children: [
                  Text(
                    widget.company.name,
                    style: const TextStyle(
                      fontSize: 17, fontWeight: FontWeight.w900),
                  ),
                  const SizedBox(height: 7),
                  const Text(
                    'Filtre as atividades para encontrar rapidamente um registro.',
                    style: TextStyle(fontSize: 12),
                  ),
                  const Divider(height: 30),
                  for (final value in filters)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: ListTile(
                        dense: true,
                        selected: filter == value,
                        selectedTileColor: const Color(0xFFDCEEE9),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10)),
                        leading: Icon(
                          value == 'Tudo'
                              ? Icons.view_list_outlined
                              : Icons.filter_list_outlined,
                          size: 20,
                        ),
                        title: Text(value),
                        onTap: () => setState(() => filter = value),
                      ),
                    ),
                  const Divider(height: 26),
                  Text(
                    rows.length.toString() + ' registro(s) neste filtro',
                    style: const TextStyle(fontWeight: FontWeight.w800),
                  ),
                ],
              ),
            ),
          ),
          const VerticalDivider(width: 1),
          Expanded(
            child: RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.fromLTRB(25, 20, 25, 34),
                children: [
                  const Text(
                    'Histórico de atividades e correções',
                    style: TextStyle(
                      fontSize: 23, fontWeight: FontWeight.w900),
                  ),
                  const SizedBox(height: 5),
                  Text(
                    'Registros de ' + widget.company.name +
                      ' em ordem cronológica.',
                    style: const TextStyle(color: Colors.black54),
                  ),
                  const SizedBox(height: 17),
                  if (rows.isEmpty)
                    const Card(
                      child: Padding(
                        padding: EdgeInsets.all(24),
                        child: Text('Nenhum registro encontrado neste filtro.'),
                      ),
                    )
                  else
                    for (final entry in rows) _eventCard(entry),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

"""
s = one(s, anchor, method+anchor, "linha do tempo detalhe clicavel")
paths["timeline"].write_text(s, encoding="utf-8", newline="\n")

# 4. Photo protection: tabular, readable, read-only verification on desktop.
# Do NOT treat "sync success" as proof that missing photos are backed up.
s = pre["photos"]
anchor = "  @override Widget build(BuildContext context) {"
method = """  Widget _windowsRecordRow(BackupRecordItem item) {
    return Card(
      margin: const EdgeInsets.fromLTRB(18, 4, 18, 4),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              flex: 5,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(item.title,
                    style: const TextStyle(
                      fontWeight: FontWeight.w800, fontSize: 14)),
                  const SizedBox(height: 5),
                  Text(item.category + ' • ' +
                    DateFormat('dd/MM/yyyy HH:mm').format(item.date),
                    style: const TextStyle(
                      color: Colors.black54, fontSize: 12)),
                ],
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              flex: 4,
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    item.state == BackupRecordState.confirmed
                      ? Icons.cloud_done_outlined : Icons.save_outlined,
                    size: 18, color: _recordColor(item.state)),
                  const SizedBox(width: 7),
                  Expanded(
                    child: Text(item.recordLabel,
                      style: TextStyle(
                        color: _recordColor(item.state), fontSize: 12.5))),
                ],
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              flex: 5,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (item.photos.isEmpty)
                    const Text('Nenhuma foto anexada',
                      style: TextStyle(
                        fontSize: 12.5, color: Colors.black54)),
                  for (final photo in item.photos)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 7),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(
                            photo.state == BackupPhotoState.confirmed
                              ? Icons.cloud_done_outlined
                              : photo.state == BackupPhotoState.missing
                                ? Icons.error_outline
                                : Icons.cloud_upload_outlined,
                            size: 18,
                            color: _photoColor(photo.state),
                          ),
                          const SizedBox(width: 7),
                          Expanded(child: Text(photo.label,
                            style: TextStyle(
                              color: _photoColor(photo.state),
                              fontSize: 12.5))),
                        ],
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

"""
matches = list(re.finditer(r"@override\s+Widget build\(BuildContext context\) \{", s))
assert len(matches) == 1, "Montagem da tela de fotos alterada"
s = s[:matches[0].start()] + method + s[matches[0].start():]
row_pattern = re.compile(
    r"(final\s+item\s*=\s*s\.records\[index\];\s*)(return\s+Card\()")
assert len(list(row_pattern.finditer(s))) == 1, "Linha de fotografia não encontrada"
s = row_pattern.sub(
    lambda m: m.group(1) +
      """if (MediaQuery.sizeOf(context).width >= 1000) {
                  return _windowsRecordRow(item);
                }
                """ + m.group(2), s, count=1)
paths["photos"].write_text(s, encoding="utf-8", newline="\n")

# 5. Separate desktop sign-in illustration, preserving the exact login form,
# validation, authentication and state that were already in the Card.
s = pre["login"]
s = one(
    s, "final desktop = MediaQuery.sizeOf(context).width >= 760;",
    """final desktop = MediaQuery.sizeOf(context).width >= 760;
    final wideDesktop = MediaQuery.sizeOf(context).width >= 1100;""",
    "login desktop breakpoint")
s = one(
    s, "constraints: BoxConstraints(maxWidth: desktop ? 470 : 430),",
    """constraints: BoxConstraints(
                  maxWidth: wideDesktop ? 1120 : (desktop ? 470 : 430)),""",
    "login usable width")
s = one(
    s, "child: Card(",
    """child: Row(
                  children: [
                    if (wideDesktop)
                      const Expanded(
                        flex: 6,
                        child: Padding(
                          padding: EdgeInsets.symmetric(horizontal: 35),
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Icon(Icons.space_dashboard_rounded,
                                size: 52, color: Colors.white),
                              SizedBox(height: 21),
                              Text('AUDITAR SST',
                                style: TextStyle(color: Colors.white,
                                  fontWeight: FontWeight.w900,
                                  letterSpacing: 1, fontSize: 29)),
                              SizedBox(height: 12),
                              Text(
                                'Sua central de Segurança do Trabalho no computador',
                                style: TextStyle(color: Colors.white,
                                  fontWeight: FontWeight.w800,
                                  fontSize: 22, height: 1.25)),
                              SizedBox(height: 13),
                              Text(
                                'Empresas, vistorias, ações, treinamentos e '
                                'indicadores disponíveis na mesma área de trabalho.',
                                style: TextStyle(color: Colors.white70,
                                  fontSize: 14, height: 1.5)),
                            ],
                          ),
                        ),
                      ),
                    Flexible(
                      flex: 5,
                      child: ConstrainedBox(
                        constraints: const BoxConstraints(maxWidth: 470),
                        child: Card(""",
    "login desktop visual left panel")
# Add closures for login Card -> inner ConstrainedBox -> Flexible -> Row,
# then preserve the original outer ConstrainedBox/ScrollView/Center/SafeArea.
tail = """                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}"""
replacement = """                ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}"""
s = one(s, tail, replacement, "login preserved form closure")
paths["login"].write_text(s, encoding="utf-8", newline="\n")

# Current Windows release completed all preceding steps at 3.30.117+304.
pub = root / "pubspec.yaml"
version = pub.read_text(encoding="utf-8")
assert version.count("version: 3.30.117+304") == 1, "Windows base inesperada"
pub.write_text(
    version.replace("version: 3.30.117+304", "version: 3.30.118+305", 1),
    encoding="utf-8", newline="\n")

for name, digest in protected.items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, (
        "Protected core modified: " + name)

for k, target in paths.items():
    assert target.read_text(encoding="utf-8") != pre[k], "No improvement: " + k

print("WINDOWS_DESKTOP_UX_V330118_OK")
print("VISIT_SPLIT_CIPA_SIDEBAR_TIMELINE_SIDEBAR_PHOTO_DESKTOP_ROWS_OK")
print("MOBILE_ANDROID_SOURCES_AND_PROTECTED_CORE_UNMODIFIED")

#!/usr/bin/env python3
"""Late, fail-closed CIPA-only patch. Run AFTER all existing platform patches."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import sys

REPO = Path(__file__).resolve().parents[1]
MARKER = "// CIPA_PARTICIPATION_V1"


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError(f"Unexpected CIPA anchor ({text.count(old)}): {old[:90]}")
    return text.replace(old, new, 1)


def regex_once(text, pattern, replacement):
    result, count = re.subn(pattern, lambda m: replacement(m), text)
    if count != 1:
        raise RuntimeError(f"Unexpected CIPA regex ({count}): {pattern[:90]}")
    return result


def transform(source, platform):
    if MARKER in source:
        raise RuntimeError("CIPA patch already applied; no overwrite permitted")
    s = replace_once(source, "import '../services/cipa_management_service.dart';",
        "import '../services/cipa_management_service.dart';\n"
        "import '../services/cipa_participation_rules.dart';\n"
        "import 'package:uuid/uuid.dart';")
    s = replace_once(s, "class CipaManagementScreen extends StatefulWidget {",
        MARKER + "\npart 'cipa_participation_screen.dart';\n\n"
        "class CipaManagementScreen extends StatefulWidget {")
    s = replace_once(s, "bool busy = false;", """bool busy = false;
  bool _cipaSimpleMode = false;
  String _cipaResponsibleFilter = '';
  DateTime _cipaReportMonth = DateTime(DateTime.now().year, DateTime.now().month);
""")
    # Hide archived records at the presentation boundary, never delete them.
    for name, collection in [('activeMembers', 'members'), ('mandateMeetings', 'meetings'),
                             ('mandateMinutes', 'minutes'), ('mandateDocuments', 'documents')]:
        pattern = rf'(List<SstRecord> get {name}\s*\{{.*?return {collection})(\s*\.where\()'
        s = regex_once(s, pattern.replace('.*?', '[\\s\\S]*?'),
            lambda m: m[1] + '.where(_cipaVisible)' + m[2])
    a = s.index('  List<SstRecord> get mandateActions {')
    b = s.index('  List<SstRecord> get mandateMinutes {', a)
    s = s[:a] + """  List<SstRecord> get mandateActions {
    final mandateId = activeMandate?.id ?? '';
    final rules = _cipaRules;
    return actions.where((a) => _cipaVisible(a) && (mandateId.isEmpty ||
      '${a.payload['mandateId'] ?? ''}' == mandateId || rules.carriedTo(a.id, mandateId))).toList();
  }

""" + s[b:]
    s = replace_once(s, "m.status != 'Realizada'", "m.status == 'Agendada'")
    s = replace_once(s, 'final pending = mandateMeetings.length - realized;',
        "final pending = mandateMeetings.where((m) => m.status == 'Agendada').length;")
    a = s.index('  Widget _annualCipaCalendarCard() {')
    b = s.index('  Widget _panelTab() {', a)
    s = s[:a] + '  Widget _annualCipaCalendarCard() => _cipaCalendar();\n\n' + s[b:]

    # Add agenda suggestions without silently replacing user-entered text.
    # Full platform builds reformat nested fields differently from the base
    # fixture. Match whitespace/trailing commas, never a different label.
    pattern = r"(TextField\(\s*controller: agenda,[\s\S]*?labelText:\s*'Pauta'\s*,?\s*\),\s*\),)"
    s = regex_once(s, pattern, lambda m: m[1] + """
                  TextButton.icon(onPressed: () => _cipaSuggestAgenda(agenda),
                    icon: const Icon(Icons.playlist_add), label: const Text('Sugerir pendências para a pauta')),
""")
    # Monotonic revision numbers include archived versions, independent of sorting.
    s = regex_once(s, r'final existing\s*=\s*mandateMinutes', lambda m: 'final existing = minutes')
    s = regex_once(s, r"version:\s*existing\.isEmpty\s*\?\s*1\s*:[\s\S]*?\+\s*1,",
        lambda m: "version: CipaParticipationRules.nextVersion(existing.map((a) => a.payload['version'])),")
    # Preserve original mandate when a carried action is updated.
    a = s.index('  Future<void> _editAction(')
    b = s.index('  Future<void> _createNc(', a)
    action = s[a:b]
    action = replace_once(action, '    await CipaManagementService.saveAction(',
        """    final actionId = current?.id ?? const Uuid().v4();
    await _cipaRun(() async {
    await CipaManagementService.saveAction(""")
    action = replace_once(action, 'id: current?.id,', 'id: actionId,')
    action = replace_once(action, 'mandateId: mandate.id,',
        "mandateId: current == null ? mandate.id : '${current.payload['mandateId'] ?? mandate.id}',")
    action = replace_once(action, '    await _load(showLoading: false);', """    if (current == null || current.status != status) {
      await _cipaEvent('action_status', actionId, {'status': status, 'title': title.text.trim()});
    }
    });""")
    s = s[:a] + action + s[b:]
    # Keep a visible support shortcut in the original action tab as well.
    s = replace_once(s, "label: Text(ncId.isEmpty ? 'Criar NC' : 'Abrir NC'),",
        "label: Text(ncId.isEmpty ? 'Criar NC' : 'Abrir NC'),")
    pattern = r"(label: Text\(ncId\.isEmpty \? 'Criar NC' : 'Abrir NC'\),\s*\),)"
    s = regex_once(s, pattern, lambda m: m[1] + """
                    if (item.status != 'Resolvida') TextButton(
                      onPressed: busy ? null : () => _cipaSupport(item), child: const Text('Preciso de apoio')),
""")
    # Add revision controls to minutes only, no mutation of signed attachments.
    a = s.index('  Widget _minutesTab()')
    b = s.index('  Widget _actionsTab()', a)
    block = s[a:b]
    block = regex_once(block, r'(child: Column\(\s*children: \[)',
        lambda m: m[1] + '\n              _cipaMinutesTools(item),')
    s = s[:a] + block + s[b:]
    s = replace_once(s, "pw.Text('Data: ${_date.format(ata.date)}'),", """pw.Text('Data: ${_date.format(ata.date)}'),
          pw.Text('Versão: ${ata.payload['version'] ?? 1} • ${ata.status}'),
          if ('${ata.payload['revisionReason'] ?? ''}'.isNotEmpty)
            pw.Text('Motivo da revisão: ${ata.payload['revisionReason']}'),
          pw.Text('Este PDF não inclui automaticamente as assinaturas dos anexos.'),""")
    s = replace_once(s, "'Ata_CIPA_${_date.format(ata.date).replaceAll('/', '-')}.pdf'",
        "'Ata_CIPA_${_date.format(ata.date).replaceAll('/', '-')}_v${ata.payload['version'] ?? 1}.pdf'")
    # Filter/archive wrapper for all existing standard list tabs.
    a = s.index('  Widget _standardList({')
    b = s.index('  @override', a)
    block = s[a:b]
    block = replace_once(block, '    return ListView(',
        '    final visibleItems = items.where(_cipaVisible).toList();\n    return ListView(')
    block = replace_once(block, 'if (items.isEmpty)', 'if (visibleItems.isEmpty)')
    block = replace_once(block, '...items.map(itemBuilder)',
        '...visibleItems.map((item) => _cipaRecordCard(item, itemBuilder(item)))')
    s = s[:a] + block + s[b:]
    # New workspace tab, maintaining desktop navigation instead of replacing it.
    s = replace_once(s, 'length: 10,', 'length: 11,')
    s = replace_once(s, "Tab(text: 'Histórico'),", "Tab(text: 'Histórico'),\n              Tab(text: 'Participação'),")
    s = replace_once(s, '_historyTab(),', '_historyTab(),\n                    _cipaWorkspaceTab(),')
    if platform == 'windows':
        s = regex_once(s, r"('Documentos',\s*'Histórico',)", lambda m: m[1] + " 'Participação',")
        # This icon appears exactly once in the desktop sidebar list.
        s = regex_once(s, r'(const icons = <IconData>\[[\s\S]*?Icons.history_outlined,)',
            lambda m: m[1] + '\n                  Icons.volunteer_activism_outlined,')
    s = replace_once(s, "title: const Text('CIPA'),", """title: const Text('CIPA'),""")
    # Separate simplified view, not a different security context.
    build = '  Widget build(BuildContext context) {'
    s = replace_once(s, build, build + """
    if (_cipaSimpleMode && !loading) {
      return Scaffold(appBar: AppBar(title: const Text('CIPA • visão simplificada'),
        actions: [IconButton(tooltip: 'Voltar à gestão completa', icon: const Icon(Icons.dashboard_outlined),
          onPressed: () => setState(() => _cipaSimpleMode = false))]),
        body: SafeArea(child: Stack(children: [_cipaWorkspaceTab(),
          if (busy) const Positioned.fill(child: ColoredBox(color: Color(0x55000000),
            child: Center(child: CircularProgressIndicator())))])));
    }
""")
    s = replace_once(s, "tooltip: 'Atualizar',", "tooltip: 'Atualizar',")
    pattern = r"(title: const Text\('CIPA'\),\s*actions: \[)"
    s = regex_once(s, pattern, lambda m: m[1] + """
            IconButton(tooltip: 'Visão simplificada (mesmas permissões)', icon: const Icon(Icons.view_agenda_outlined),
              onPressed: () => setState(() => _cipaSimpleMode = true)),
""")
    return s


def snapshot(root):
    # Hash EVERYTHING except the CIPA screen and new feature files, not only a
    # hand-picked protected list. Catch accidental changes to app infrastructure.
    allowed = {'lib/screens/cipa_management_screen.dart', 'lib/screens/cipa_participation_screen.dart',
        'lib/services/cipa_participation_rules.dart', 'test/cipa_participation_rules_test.dart'}
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for base in ('lib', 'painel_web_google_apps_script')
        for p in (root / base).rglob('*') if p.is_file() and p.relative_to(root).as_posix() not in allowed}


def main(root, platform):
    if platform not in ('android', 'windows'): raise RuntimeError('Invalid platform')
    path = root / 'lib/screens/cipa_management_screen.dart'
    before = snapshot(root)
    text = transform(path.read_text(encoding='utf-8'), platform)
    copies = {
        'feature_sources/cipa_participation_screen_v1.dart': 'lib/screens/cipa_participation_screen.dart',
        'feature_sources/cipa_participation_rules_v1.dart': 'lib/services/cipa_participation_rules.dart',
        'feature_sources/cipa_participation_rules_test_v1.dart': 'test/cipa_participation_rules_test.dart',
    }
    for name in copies:
        if not (REPO / name).is_file(): raise RuntimeError('Missing source: ' + name)
    path.write_text(text, encoding='utf-8')
    for source, target in copies.items():
        destination = root / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / source, destination)
        if target.startswith('test/'):
            destination.write_text(destination.read_text(encoding='utf-8').replace(
                "import 'cipa_participation_rules_v1.dart';",
                "import '../lib/services/cipa_participation_rules.dart';"), encoding='utf-8')
    after = snapshot(root)
    if before != after: raise RuntimeError('Protected/non-CIPA application files changed')
    (root / '.cipa_participation_protected.json').write_text(json.dumps(after, indent=2), encoding='utf-8')
    print('CIPA_PARTICIPATION_V1_OK', platform, 'ALL_NON_CIPA_FILES_UNCHANGED', len(after))


if __name__ == '__main__':
    if len(sys.argv) != 3: raise SystemExit('usage: patch_cipa_participation_v1.py APP_DIR android|windows')
    main(Path(sys.argv[1]), sys.argv[2])

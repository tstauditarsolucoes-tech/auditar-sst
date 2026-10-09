#!/usr/bin/env python3
"""Isolated cloud knowledge & rapid field navigation (no core sync/schema changes)."""
from pathlib import Path
import hashlib, shutil, sys
root=Path(sys.argv[1]); platform=sys.argv[2]
assert platform in ('android','windows')
repo=Path(__file__).resolve().parents[1]
widget=root/'lib/widgets/offline_report_inline_suggestions.dart'
quick=root/'lib/screens/quick_visit_screen.dart'
code=root/'painel_web_google_apps_script/Code.gs'
assert all(p.exists() for p in (widget,quick,code))
service=root/'lib/services/offline_knowledge_cloud_service.dart'
assert not service.exists(), 'Cloud service already exists; inspect baseline'
allowed={widget,quick,code}
protected=[p for folder in ('lib','painel_web_google_apps_script')
           for p in (root/folder).rglob('*') if p.is_file() and p not in allowed]
before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}

shutil.copyfile(repo/'feature_sources/offline_knowledge_cloud_service_v329177.dart',service)
# A session-protected, additive Apps Script handler; does not modify old routes.
route="    if (request.action === 'device_sync_push') {"
s=code.read_text(encoding='utf-8')
assert s.count(route)==1 and "'offline_knowledge_sync_v1'" not in s
s=s.replace(route,"    if (request.action === 'offline_knowledge_sync_v1') {\n      return jsonResponse_(offlineKnowledgeSyncV1_(request));\n    }\n\n"+route,1)
code.write_text(s,encoding='utf-8',newline='\n')
shutil.copyfile(repo/'feature_sources/OfflineKnowledgeCloud_v1.gs',
                code.parent/'OfflineKnowledgeCloud.gs')

# Cloud reads cache with no wait for network. Local learning is saved first.
s=widget.read_text(encoding='utf-8')
marker="import '../services/offline_reasoning.dart';"
assert s.count(marker)==1
s=s.replace(marker,marker+"\nimport '../services/offline_knowledge_cloud_service.dart';",1)
anchor="    _learnedCache = List.unmodifiable(learned);"
assert s.count(anchor)==1
s=s.replace(anchor, """    try {
      for (final data in await OfflineKnowledgeCloudService.cachedModels()) {
        final item = _fromMap(data);
        if (item != null) learned.add(item);
      }
    } catch (_) {} // Cloud cache may be unavailable; never block field records.
"""+anchor,1)
anchor="      invalidateLearnedCache();"
assert s.count(anchor)==1
s=s.replace(anchor, """      invalidateLearnedCache();
      try {
        await OfflineKnowledgeCloudService.queueApplied(map);
      } catch (_) { /* Saved locally; cloud queue can be retried later. */ }
""",1)
anchor="    final normalized = _normalize(OfflineReasoning.normalize(query));"
assert s.count(anchor)==1
s=s.replace(anchor,"    OfflineKnowledgeCloudService.schedule();\n"+anchor,1)
widget.write_text(s,encoding='utf-8',newline='\n')

# Three large repeated navigation cards become compact touch-friendly actions.
s=quick.read_text(encoding='utf-8')
start=s.index("        if (widget.intent == VisitIntent.visit) ...[")
end=s.index("          _action(\n            'Pendências da empresa',",start)
original=s[start:end]
for token in ("'Nova ronda'","'Nova vistoria'","'Registrar não conformidade'"):
    assert token in original
replacement="""        if (widget.intent == VisitIntent.visit) ...[
          Wrap(spacing: 8, runSpacing: 8, children: [
            FilledButton.icon(
              onPressed: _opening ? null : () => _open(ExpressRoundScreen(company: c)),
              icon: const Icon(Icons.add_a_photo_outlined),
              label: const Text('Nova ronda')),
            OutlinedButton.icon(
              onPressed: _opening ? null : () => _open(NewInspectionScreen(
                initialCompany: c, fieldMode: true)),
              icon: const Icon(Icons.fact_check_outlined),
              label: const Text('Nova vistoria')),
            OutlinedButton.icon(
              onPressed: _opening ? null : _recordObservation,
              icon: const Icon(Icons.warning_amber_outlined),
              label: const Text('Registrar não conformidade')),
          ]),
          const SizedBox(height: 8),
"""
s=s[:start]+replacement+s[end:]
# Explicit reuse of latest *authorized* visit. Never auto-switch company.
marker="  Widget _picker() {\n"
assert s.count(marker)==1
s=s.replace(marker,marker+"""    final previous = _companies.where((c) =>
      c.active && AuthService.canAccessCompany(c.id) &&
      _organization.lastVisit(c.id).isNotEmpty).toList()
        ..sort((a,b) => _organization.lastVisit(b.id)
          .compareTo(_organization.lastVisit(a.id)));
""",1)
marker="              TextField(\n                controller: _search,"
assert s.count(marker)==1
s=s.replace(marker,"""              if (previous.isNotEmpty && _search.text.trim().isEmpty &&
                  _group == null && !_favorites && !_recent) ...[
                OutlinedButton.icon(
                  onPressed: () => _select(previous.first),
                  icon: const Icon(Icons.history_rounded),
                  label: Text(
                    'Continuar na última empresa: ' +
                      (_organization.alias(previous.first.id).isEmpty
                       ? previous.first.name
                       : _organization.alias(previous.first.id)),
                    maxLines: 2, overflow: TextOverflow.ellipsis),
                ),
                const SizedBox(height: 8),
              ],
"""+marker,1)
quick.write_text(s,encoding='utf-8',newline='\n')

version=root/'pubspec.yaml'; s=version.read_text(encoding='utf-8')
old,new=('3.29.176+318','3.29.177+319') if platform=='android' else ('3.30.99+286','3.30.100+287')
assert s.count('version: '+old)==1
version.write_text(s.replace('version: '+old,'version: '+new),encoding='utf-8',newline='\n')

for path,digest in before.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,str(path)
print('CLOUD_KNOWLEDGE_FIELD_READY: core database/sync/auth/photos/IA preserved',platform)

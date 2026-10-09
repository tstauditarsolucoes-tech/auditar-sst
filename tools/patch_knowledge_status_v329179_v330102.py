#!/usr/bin/env python3
"""Knowledge cloud status UX; supplemental to core synchronization."""
from pathlib import Path
import hashlib,shutil,sys
root=Path(sys.argv[1]);platform=sys.argv[2]
assert platform in ('android','windows')
repo=Path(__file__).resolve().parents[1]
quick=root/'lib/screens/quick_visit_screen.dart'
dest=root/'lib/screens/offline_knowledge_status_screen.dart'
service=root/'lib/services/offline_knowledge_cloud_service.dart'
assert quick.exists() and service.exists() and not dest.exists()
assert 'Future<OfflineKnowledgeStatus> status()' in service.read_text(encoding='utf-8')
protected=[p for folder in ('lib','painel_web_google_apps_script')
    for p in (root/folder).rglob('*') if p.is_file() and p!=quick]
before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
shutil.copyfile(repo/'feature_sources/offline_knowledge_status_screen_v329179.dart',dest)
s=quick.read_text(encoding='utf-8')
anchor="import 'worksite_followup_screen.dart';"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\nimport 'offline_knowledge_status_screen.dart';",1)
anchor="        const SizedBox(height: 12),\n        _action(\n          'Mais opções da empresa',"
assert s.count(anchor)==1
addition="""        Card(
          child: ListTile(
            leading: const Icon(Icons.cloud_sync_outlined),
            title: const Text('Biblioteca técnica online'),
            subtitle: const Text('Modelos pendentes e atualização entre aparelhos'),
            trailing: const Icon(Icons.chevron_right),
            onTap: _opening ? null : () => _open(const OfflineKnowledgeStatusScreen()),
          ),
        ),
"""
s=s.replace(anchor,addition+anchor,1)
quick.write_text(s,encoding='utf-8',newline='\n')
p=root/'pubspec.yaml';v=p.read_text(encoding='utf-8')
old,new=('3.29.178+320','3.29.179+321') if platform=='android' else ('3.30.101+288','3.30.102+289')
assert v.count('version: '+old)==1
p.write_text(v.replace('version: '+old,'version: '+new),encoding='utf-8',newline='\n')
for path,hashvalue in before.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest()==hashvalue,str(path)
print('KNOWLEDGE_STATUS_READY: database auth sync transport photos unchanged',platform)

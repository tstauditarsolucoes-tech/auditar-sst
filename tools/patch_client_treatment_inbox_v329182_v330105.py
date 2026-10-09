#!/usr/bin/env python3
"""Tratativas in app + Central route: additive, protecting sync, media, DB, auth and IA."""
from pathlib import Path
import hashlib,shutil,sys,re
root=Path(sys.argv[1]); platform=sys.argv[2]
assert platform in ('android','windows')
repo=Path(__file__).resolve().parents[1]
code=root/'painel_web_google_apps_script/Code.gs'
portal=root/'painel_web_google_apps_script/ClientPortal.html'
home=root/'lib/screens/home_screen.dart'
quick=root/'lib/screens/quick_visit_screen.dart'
target=root/'lib/screens/client_treatment_inbox_screen.dart'
assert all(p.exists() for p in (code,portal,home,quick)) and not target.exists()
allowed={code,portal,home,quick}
protected=[
  p for folder in ('lib','painel_web_google_apps_script')
  for p in (root/folder).rglob('*')
  if p.is_file() and p not in allowed
]
before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
shutil.copyfile(repo/'feature_sources/client_treatment_inbox_screen_v329181.dart',target)
s=code.read_text(encoding='utf-8')
anchor="    if (request.action === 'worksite_followup_sync_v1') {"
assert s.count(anchor)==1 and "'client_treatment_v2'" not in s
s=s.replace(anchor,
  "    if (request.action === 'client_treatment_v2') {\n"
  "      return jsonResponse_(clientTreatmentAppV2_(request));\n"
  "    }\n\n"+anchor,1)
code.write_text(s,encoding='utf-8',newline='\n')
s=home.read_text(encoding='utf-8')
imp="import 'client_treatment_inbox_screen.dart';\n"
assert imp not in s
s=imp+s
# Quick Visit replaces the Home layout; insert after its VisitStartPanel
# callback without depending on Dart formatter indentation for the full list.
matches=list(re.finditer(r'(?m)^[ \t]*onMore:[ \t]*_showModules,[ \t]*\n([ \t]*)\),[ \t]*$',s))
assert len(matches)==1 and s.count('onMore: _showModules,')==1, (
  'Home: expected one VisitStartPanel for the Auditar inbox'
)
insert="""\n      Card(
        child: ListTile(
          leading: const Icon(Icons.forum_outlined),
          title: const Text('Caixa de entrada Auditar'),
          subtitle: const Text('Respostas de clientes, prazos e reuniões'),
          trailing: const Icon(Icons.chevron_right),
          onTap: () => _open(const ClientTreatmentInboxScreen()),
        ),
      ),"""
s=s[:matches[0].end()]+insert+s[matches[0].end():]
home.write_text(s,encoding='utf-8',newline='\n')
s=quick.read_text(encoding='utf-8')
s="import 'client_treatment_inbox_screen.dart';\n"+s
anchor="        _action(\n          'Mais opções da empresa',"
assert s.count(anchor)==1
s=s.replace(anchor,"""        _action(
          'Comunicação e tratativas',
          'Mensagens da empresa, resposta técnica e acompanhamento',
          Icons.forum_outlined,
          ClientTreatmentInboxScreen(companyId:c.id,companyName:c.name),
        ),
"""+anchor,1)
quick.write_text(s,encoding='utf-8',newline='\n')
s=portal.read_text(encoding='utf-8')
anchor="  res.companies.forEach(renderCompany);"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\n  renderTreatmentInboxV2();",1)
portal.write_text(s,encoding='utf-8',newline='\n')
pub=root/'pubspec.yaml'
s=pub.read_text(encoding='utf-8')
old,new=('3.29.181+323','3.29.182+324') if platform=='android' else ('3.30.104+291','3.30.105+292')
assert s.count('version: '+old)==1,('Unexpected version',old)
pub.write_text(s.replace('version: '+old,'version: '+new),encoding='utf-8',newline='\n')
for p,digest in before.items():
 assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,str(p)
print('CLIENT_TREATMENT_INBOX_APP_READY: auth/sync/data/photos unaffected',platform)

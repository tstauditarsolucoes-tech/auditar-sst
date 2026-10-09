#!/usr/bin/env python3
"""Install isolated cloud worksite metadata channel; leave core services byte-for-byte unchanged."""
from pathlib import Path
import hashlib,shutil,sys
root=Path(sys.argv[1]);platform=sys.argv[2]
assert platform in ('android','windows')
repo=Path(__file__).resolve().parents[1]
screen=root/'lib/screens/worksite_followup_screen.dart'
service=root/'lib/services/worksite_followup_cloud_service.dart'
code=root/'painel_web_google_apps_script/Code.gs'
assert screen.exists() and code.exists() and not service.exists()
allowed={screen,code}
protected=[p for base in ('lib','painel_web_google_apps_script')
  for p in (root/base).rglob('*') if p.is_file() and p not in allowed]
before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
shutil.copyfile(repo/'feature_sources/worksite_followup_cloud_service_v329180.dart',service)
shutil.copyfile(repo/'feature_sources/worksite_followup_screen_v329180.dart',screen)
shutil.copyfile(repo/'feature_sources/worksite_followup_cloud_test_v329180.dart',
  root/'test/worksite_followup_cloud_test.dart')
s=code.read_text(encoding='utf-8')
anchor="    if (request.action === 'offline_knowledge_sync_v1') {"
assert s.count(anchor)==1 and "'worksite_followup_sync_v1'" not in s
s=s.replace(anchor,
  "    if (request.action === 'worksite_followup_sync_v1') {\n"
  "      return jsonResponse_(worksiteFollowupCloudV1_(request));\n"
  "    }\n\n"+anchor,1)
code.write_text(s,encoding='utf-8',newline='\n')
shutil.copyfile(repo/'feature_sources/WorksiteFollowupCloud_v1.gs',
  code.parent/'WorksiteFollowupCloud.gs')
pub=root/'pubspec.yaml'
content=pub.read_text(encoding='utf-8')
old,new=('3.29.179+321','3.29.180+322') if platform=='android' else ('3.30.102+289','3.30.103+290')
assert content.count('version: '+old)==1,(platform,old)
pub.write_text(content.replace('version: '+old,'version: '+new),
  encoding='utf-8',newline='\n')
for path,digest in before.items():
  assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,str(path)
print('WORKSITE_CLOUD_READY; SYNC_DATABASE_AUTH_MEDIA_IA_OTHER_SCREENS_UNCHANGED',platform)

#!/usr/bin/env python3
"""Add isolated treatment outbox; preserve all preexisting services and GS bytes."""
from pathlib import Path
import hashlib,shutil,sys
root=Path(sys.argv[1]);platform=sys.argv[2]
assert platform in ('android','windows')
repo=Path(__file__).resolve().parents[1]
target=root/'lib/screens/client_treatment_inbox_screen.dart'
assert target.exists()
protected=[p for folder in ('lib','painel_web_google_apps_script') for p in (root/folder).rglob('*') if p.is_file() and p!=target]
before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
for source,dest in [
 ('client_treatment_inbox_screen_v329185.dart','lib/screens/client_treatment_inbox_screen.dart'),
 ('treatment_outbox_v1.dart','lib/services/treatment_outbox.dart'),
 ('treatment_outbox_store_v1.dart','lib/services/treatment_outbox_store.dart'),
 ('treatment_outbox_test_v1.dart','test/treatment_outbox_test.dart')]:
 out=root/dest
 if out!=target:assert not out.exists(),str(out)
 out.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(repo/'feature_sources'/source,out)
pub=root/'pubspec.yaml';s=pub.read_text(encoding='utf-8')
old,new=('3.29.184+326','3.29.185+327') if platform=='android' else ('3.30.107+294','3.30.108+295')
assert s.count('version: '+old)==1
pub.write_text(s.replace('version: '+old,'version: '+new),encoding='utf-8')
for p,digest in before.items():assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,str(p)
print('OUTBOX_READY: old services, database, auth, media and GS preserved; '+new)

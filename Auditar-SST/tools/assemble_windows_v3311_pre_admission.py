#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

repo=Path(__file__).resolve().parents[1]
root=Path(sys.argv[1]) if len(sys.argv)>1 else repo/'app/Auditar_SST_v1_5_dashboard'
if not root.is_absolute():
    root=(repo/root).resolve()
py=sys.executable

def run(path,*args):
    result=subprocess.run(
        [py,str(repo/path),*map(str,args)],
        cwd=repo,
    )
    if result.returncode!=0:
        raise RuntimeError(f'Falhou: {path}')

run('tools/assemble_windows_v3309_mobile_parity.py',root)
run('tools/patch_signature_handoff_v32982.py',root,'windows')
run('tools/patch_pre_admission_search_v32983.py',root,'windows')

pub=(root/'pubspec.yaml').read_text(encoding='utf-8')
assert 'version: 3.30.11+198' in pub
assert 'ASSINANDO AGORA' in (root/'lib/screens/training_records_screen.dart').read_text(encoding='utf-8')
assert 'PRE_ADMISSION_PARTICIPANT' in (root/'lib/services/pre_admission_participant_service.dart').read_text(encoding='utf-8')
assert 'Pesquisar por nome' in (root/'lib/screens/sst_record_form_screen.dart').read_text(encoding='utf-8')
assert 'SearchableWorkerField' in (root/'lib/screens/cipa_management_screen.dart').read_text(encoding='utf-8')
print('WINDOWS_V3311_PRE_ADMISSION_OK')

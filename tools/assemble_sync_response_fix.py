#!/usr/bin/env python3
from pathlib import Path
import base64, hashlib, lzma, re, subprocess, sys

root=Path('.').resolve()
platform=(sys.argv[1] if len(sys.argv)>1 else '').strip().lower()
if platform not in {'android','windows'}:
    raise SystemExit('Uso: assemble_sync_response_fix.py <android|windows>')
app=root/'app/Auditar_SST_v1_5_dashboard'

def run(*args):
    subprocess.run([str(x) for x in args], check=True)

def unpack_b64(src, out):
    packed=base64.b64decode(re.sub(r'[^A-Za-z0-9+/=]','',Path(src).read_text(encoding='utf-8')))
    Path(out).write_bytes(lzma.decompress(packed))

def screen_hashes():
    result=[]
    for p in sorted((app/'lib/screens').glob('**/*')):
        if p.is_file():
            result.append((str(p.relative_to(app)), hashlib.sha256(p.read_bytes()).hexdigest()))
    return result

run(sys.executable, 'tools/assemble_v32920.py')
parts=['part00.b64','part01.b64','part02.b64','part03.b64','part04.b64','part05.b64','part06.b64','part07a.b64','part07b.b64','part08.b64']
packed=base64.b64decode(re.sub(r'[^A-Za-z0-9+/=]','', ''.join((root/'build_sources/v3.29.27-patch'/p).read_text(encoding='utf-8') for p in parts)))
assert hashlib.sha256(packed).hexdigest()=='0b238c75455f7cb942acaa5a28e6f8c3eeb18be0fb52cdaac06b2f5ba8dc2c7c'
Path('v32927.patch').write_bytes(lzma.decompress(packed))
for src,out in [
    ('build_sources/v3.29.28-panel/v32927_to_v32928.patch.xz.b64','v32928.patch'),
    ('build_sources/v3.29.31-pc-layout/v32930_to_v32931.patch.xz.b64','v32931.patch'),
    ('build_sources/v3.29.32-pc-premium/v32931_to_v32932.patch.xz.b64','v32932.patch'),
    ('build_sources/v3.29.34-drive-evidence/v32933_to_v32934.patch.xz.b64','v32934.patch'),
]: unpack_b64(src,out)
run('git','apply',f'--directory={app.relative_to(root)}','v32927.patch')
run('git','apply',f'--directory={app.relative_to(root)}','build_sources/v3.29.27-patch/hotfix-sync-biblioteca.patch')
run('git','apply',f'--directory={app.relative_to(root)}','v32928.patch')
run(sys.executable,'tools/patch_tutorial_v32930.py',str(app),str(root))
run('git','apply','-p2',f'--directory={app.relative_to(root)}','v32931.patch')
run('git','apply','-p2',f'--directory={app.relative_to(root)}','v32932.patch')
run(sys.executable,'tools/patch_photo_recovery_v32933.py',str(app))
run('git','apply',f'--directory={app.relative_to(root)}','v32934.patch')

if platform=='windows':
    for src,out in [
        ('build_sources/v3.29.35-pc-deep/v32934_to_v32935.patch.xz.b64','v32935.patch'),
        ('build_sources/v3.29.36-pc-syncfix/v32935_to_v32936_v2.patch.xz.b64','v32936.patch'),
        ('build_sources/v3.29.37-data-safety/v32936_to_v32937.patch.xz.b64','v32937.patch'),
    ]: unpack_b64(src,out)
    run('git','apply',f'--directory={app.relative_to(root)}','v32935.patch')
    run('git','apply','-p1',f'--directory={app.relative_to(root)}','v32936.patch')
    run('git','apply','-p2',f'--directory={app.relative_to(root)}','v32937.patch')

before=screen_hashes()
run(sys.executable,'tools/patch_v32938_central_recovery.py',str(app),platform)
run(sys.executable,'tools/patch_apps_script_transport_recovery.py',str(app))
run(sys.executable,'tools/patch_fresh_login_v32936_32939.py',str(app),platform)
run(sys.executable,'tools/patch_sync_response_recovery_v32938_32941.py',str(app),platform)
after=screen_hashes()
if before != after:
    raise RuntimeError('A interface/layout foi alterada pela correcao interna.')

pub=(app/'pubspec.yaml').read_text(encoding='utf-8')
target='version: 3.29.38+180' if platform=='android' else 'version: 3.29.41+183'
assert target in pub
assert '_pushChangesSafely' in (app/'lib/services/device_sync_service.dart').read_text(encoding='utf-8')
assert 'persistentConnection = false' in (app/'lib/services/apps_script_http.dart').read_text(encoding='utf-8')
assert 'restoreSavedSessionForTesting = false' in (app/'lib/services/auth_service.dart').read_text(encoding='utf-8')
print(f'Fonte final montada e UI preservada: {target}')

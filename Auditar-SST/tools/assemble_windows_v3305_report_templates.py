#!/usr/bin/env python3
from pathlib import Path
import hashlib
import subprocess
import sys

repo = Path(__file__).resolve().parents[1]
root = Path(sys.argv[1]) if len(sys.argv) > 1 else repo / 'app/Auditar_SST_v1_5_dashboard'
if not root.is_absolute():
    root = (repo / root).resolve()
py = sys.executable


def run(script, *args):
    subprocess.check_call([py, str(repo / script), *map(str, args)], cwd=repo)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_files():
    fixed = [
        root / 'lib/services/device_sync_service.dart',
        root / 'lib/services/media_sync_service.dart',
        root / 'lib/services/auth_service.dart',
        root / 'lib/services/drive_service.dart',
        root / 'lib/database.dart',
        root / 'lib/services/web_service_config.dart',
    ]
    extra = sorted((root / 'lib/services').glob('*transport*.dart'))
    extra += sorted((root / 'lib/services').glob('*apps_script*.dart'))
    seen = []
    for path in fixed + extra:
        if path.exists() and path not in seen:
            seen.append(path)
    return seen


# Base Windows atual, sem qualquer alteração da sincronização.
run('tools/assemble_windows_v3304_ronda_latest.py', root)
protected = protected_files()
before = {path: digest(path) for path in protected}

# Recurso novo: somente relatórios/modelos. A base Windows tem pequena diferença
# de layout no Settings; o patch compartilhado chega até esse ponto e o
# complemento Windows termina somente Settings/PDF/versionamento.
shared = subprocess.run(
    [py, str(repo / 'tools/patch_report_templates_v32962.py'), str(root)],
    cwd=repo,
)
if shared.returncode != 0:
    run('tools/patch_report_templates_windows_compat_v3305.py', root)
run('tools/patch_report_templates_user_default_v32962.py', root)
run('tools/patch_report_templates_compile_fix_v32962.py', root)

# A patch compartilhada usa numeração Android; restaura a linha Windows monotônica.
pub = root / 'pubspec.yaml'
text = pub.read_text(encoding='utf-8')
if 'version: 3.29.62+204' not in text:
    raise RuntimeError('Versão intermediária dos modelos não encontrada no Windows')
pub.write_text(text.replace('version: 3.29.62+204', 'version: 3.30.5+192', 1), encoding='utf-8', newline='\n')

after = {path: digest(path) for path in protected}
changed = [str(path.relative_to(root)) for path in protected if before[path] != after[path]]
if changed:
    raise RuntimeError('PROTEÇÃO DE SYNC: a atualização de relatórios alterou arquivos protegidos: ' + ', '.join(changed))

# Marcadores funcionais da sincronização Windows existente continuam presentes.
coord = (root / 'lib/services/sync_coordinator.dart').read_text(encoding='utf-8')
dev = (root / 'lib/services/device_sync_service.dart').read_text(encoding='utf-8')
assert 'Duration(seconds: 10)' in coord, 'timeout de sync Windows foi alterado'
assert 'final pullLimit = isWindows ? 500 : 100;' in dev, 'pull limit Windows foi alterado'

# Modelo atual continua sendo o fallback/renderer legado.
templates = (root / 'lib/services/report_template_service.dart').read_text(encoding='utf-8')
pdf = (root / 'lib/services/pdf_service.dart').read_text(encoding='utf-8')
assert "name: 'Padrão Auditar atual'" in templates
assert 'useLegacyRenderer: true' in templates
assert 'selectDefaultForCurrentUser' in templates
assert 'AuthService.currentUser?.id' in templates
assert 'if (!reportTemplate.useLegacyRenderer)' in pdf
assert 'version: 3.30.5+192' in pub.read_text(encoding='utf-8')

print('WINDOWS_V3305_OK: modelos + padrão individual por usuário adicionados; arquivos de sincronização/login/mídia/Drive/banco permanecem byte por byte idênticos à base v3.30.4.')
for path in protected:
    print('SYNC_PROTEGIDO_OK', path.relative_to(root), after[path])

#!/usr/bin/env python3
from pathlib import Path
import base64, lzma, os, re, subprocess, sys, tempfile

repo=Path(__file__).resolve().parents[1]
root=Path(sys.argv[1]) if len(sys.argv)>1 else repo/'app/Auditar_SST_v1_5_dashboard'
if not root.is_absolute():
    root=(repo/root).resolve()
py=sys.executable

def _utf8_env():
    env=os.environ.copy()
    env['PYTHONUTF8']='1'
    env['PYTHONIOENCODING']='utf-8'
    return env

def run(path,*args,allow_fail=False):
    cmd=[py,str(repo/path),*map(str,args)]
    result=subprocess.run(cmd,cwd=repo,env=_utf8_env())
    if result.returncode!=0 and not allow_fail:
        raise RuntimeError(f'Falhou: {path}')
    return result.returncode

def set_version(value):
    pub=root/'pubspec.yaml'
    text=pub.read_text(encoding='utf-8')
    text,n=re.subn(r'^version:\s*[^\n]+',f'version: {value}',text,count=1,flags=re.M)
    if n!=1: raise RuntimeError('Versão não localizada')
    pub.write_text(text,encoding='utf-8',newline='\n')

def run_b64(path,*args):
    raw=lzma.decompress(base64.b64decode((repo/path).read_text(encoding='utf-8').strip()))
    with tempfile.NamedTemporaryFile('wb',suffix='.py',delete=False) as tmp:
        tmp.write(raw)
        temp=Path(tmp.name)
    try:
        result=subprocess.run(
            [py,str(temp),str(root),*map(str,args)],
            cwd=repo,
            env=_utf8_env(),
        )
        if result.returncode!=0:
            raise RuntimeError(f'Falhou patch compactado: {path}')
    finally:
        temp.unlink(missing_ok=True)

# Base Windows estável mais recente
run('tools/assemble_windows_v3305_report_templates.py',root)
run('tools/patch_training_records_media_v32968_v3306.py',root,'windows')
run('tools/patch_internal_management_training_v32969_v3307.py',root,'windows')
run('tools/patch_management_panel_logo_theme_v32970_v3308.py',root,'windows')

# Port das melhorias Android pós-v3.29.70 sem tocar no motor de sync Windows.
set_version('3.29.70+212')
run_b64('build_sources/v3.29.71-nc-quick-resolve/patch_nc_quick_resolve_v32971.py.xz.b64')

# O AuthService Windows já usa a Central embutida e possui fluxo próprio.
# Portamos apenas o refinamento visual/comportamental do Login Android,
# sem alterar transporte, sync ou AuthService do PC.
loginp=root/'lib/screens/login_screen.dart'
login=loginp.read_text(encoding='utf-8')
login=login.replace(
    "      await AuthService.login(username: username, password: pass)\n          .timeout(const Duration(seconds: 25));",
    "      await AuthService.login(username: username, password: pass);",
    1,
)
login=login.replace(
    "      await AuthService.bootstrapAdmin(name: name, email: email, password: pass)\n          .timeout(const Duration(seconds: 25));",
    "      await AuthService.bootstrapAdmin(\n        name: name,\n        email: email,\n        password: pass,\n      );",
    1,
)
login=login.replace(
    "      return 'A Central Online demorou para responder. Verifique a internet e tente novamente.';",
    "      return 'A Central Online demorou para responder. Tente novamente em alguns instantes.';",
    1,
)
if "text.contains('não respondeu a tempo')" not in login:
    marker="""    if (text.contains('TimeoutException')) {
      return 'A Central Online demorou para responder. Tente novamente em alguns instantes.';
    }
"""
    if marker in login:
        login=login.replace(
            marker,
            marker+"    if (text.contains('não respondeu a tempo')) {\n      return 'A Central Online está oscilando e não respondeu a tempo. Tente novamente.';\n    }\n",
            1,
        )
loginp.write_text(login,encoding='utf-8',newline='\n')
set_version('3.29.72+214')

# Importação inteligente de treinamentos
run('tools/patch_training_bulk_import_v32973.py',root)
run_b64('build_sources/v3.29.74-training-photo/patch_training_import_photo_v32974.py.xz.b64')
run('tools/patch_training_import_robust_v32975.py',root)

# Gestão CIPA completa
run('tools/patch_cipa_management_v32976.py',root)

# Multa opcional + confirmação por foto DDS/treinamentos
run_b64('build_sources/v3.29.77-checklist-fine-face/patch_checklist_fine_face_v32977.py.xz.b64')
run('tools/patch_refine_new_features_v32978.py',root)
run('tools/patch_refine_new_features_v32979.py',root)

# Novo modelo de relatório Performance
run('tools/patch_performance_report_v32980.py',root)

# Refinamento compartilhado de IA/fotos + adaptações desktop
run('tools/patch_cross_platform_refinement_v32981.py',root,'windows')

# Validações estruturais de paridade
pub=(root/'pubspec.yaml').read_text(encoding='utf-8')
assert 'version: 3.30.9+196' in pub
assert (root/'lib/screens/training_import_screen.dart').exists()
assert (root/'lib/services/training_import_service.dart').exists()
assert (root/'lib/screens/cipa_management_screen.dart').exists()
assert (root/'lib/services/cipa_management_service.dart').exists()
assert (root/'lib/services/performance_report_pdf_service.dart').exists()

training=(root/'lib/services/training_import_service.dart').read_text(encoding='utf-8')
assert 'Fotos • IA da Central' in training
assert '_buildPhotoPdf' in training
assert "mode':'training_record_import'" in training or "'mode': 'training_record_import'" in training
assert "mode':'employee_pdf_import'" in training or "'mode': 'employee_pdf_import'" in training

ai=(root/'lib/services/ai_assistant_service.dart').read_text(encoding='utf-8')
assert 'WebServiceConfig.endpoint' in ai
assert "'mode': 'checklist_photo'" in ai
assert "'rondaDeferred': true" in ai

cipa=(root/'lib/screens/cipa_management_screen.dart').read_text(encoding='utf-8')
assert 'Painel' in cipa and 'Mandato' in cipa and 'Eleição' in cipa
check=(root/'lib/screens/checklist_screen.dart').read_text(encoding='utf-8')
assert 'Valor de referência' in check and 'Mostrar no relatório' in check
training_records=(root/'lib/screens/training_records_screen.dart').read_text(encoding='utf-8')
assert 'Assinatura facial' in training_records
sst=(root/'lib/screens/sst_record_form_screen.dart').read_text(encoding='utf-8')
assert 'Assinatura facial' in sst
report=(root/'lib/services/report_template_service.dart').read_text(encoding='utf-8')
assert 'Performance - Foto + Descrição' in report
nc=(root/'lib/screens/non_conformity_detail_screen.dart').read_text(encoding='utf-8')
assert 'Resolver agora' in nc
print('WINDOWS_V3309_PARITY_OK')

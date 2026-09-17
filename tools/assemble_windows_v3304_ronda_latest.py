#!/usr/bin/env python3
from pathlib import Path
import base64
import lzma
import re
import subprocess
import sys
import tempfile

repo = Path(__file__).resolve().parents[1]
root = Path(sys.argv[1]) if len(sys.argv) > 1 else repo / 'app/Auditar_SST_v1_5_dashboard'
if not root.is_absolute():
    root = (repo / root).resolve()
py = sys.executable


def run(script, *args):
    path = repo / script
    print(f'>> {path.name} {" ".join(map(str, args))}')
    subprocess.check_call([py, str(path), *map(str, args)], cwd=repo)


def set_version(expected, new):
    pubp = root / 'pubspec.yaml'
    text = pubp.read_text(encoding='utf-8')
    if expected not in text:
        current = next((x.strip() for x in text.splitlines() if x.startswith('version:')), 'version:?')
        raise RuntimeError(f'Versao esperada {expected!r} ausente; atual={current}')
    pubp.write_text(text.replace(expected, new, 1), encoding='utf-8', newline='\n')


# Base Windows exatamente equivalente a v3.30.3+190.
run('tools/assemble_sync_response_fix.py', 'windows')
run('tools/patch_sync_progress_v32939_32942.py', root, 'windows')
run('tools/patch_sync_progress_compile_safety.py', root)
run('tools/patch_windows_sync_logo_stability_v32943.py', root)
run('tools/patch_sync_queue_media_separation_v32940_32944.py', root, 'windows')

training_b64 = repo / 'build_sources/v3.30.0-training-attendance/patch_training_attendance_v3300.py.xz.b64'
with tempfile.NamedTemporaryFile('wb', suffix='.py', delete=False) as tmp:
    tmp.write(lzma.decompress(base64.b64decode(training_b64.read_text(encoding='utf-8').strip())))
    training_patch = Path(tmp.name)
subprocess.check_call([py, str(training_patch), str(root), 'windows'], cwd=repo)
training_patch.unlink(missing_ok=True)

run('tools/patch_windows_dds_mobile_module_v3301.py', root)
run('tools/patch_windows_mobile_improvements_v3301_compat.py', root)
set_version('version: 3.30.1+188', 'version: 3.30.2+189')
run('tools/patch_company_logo_persistence_v32954_v3303.py', root, 'windows')

# Primeiro port oficial da Ronda IA/conformidade para a base Windows v3.30.3.
ronda_b64 = repo / 'build_sources/v3.29.55-ronda-ia-conformidade/patch_express_round_ai_conformity_v32955_v3304.py.xz.b64'
with tempfile.NamedTemporaryFile('wb', suffix='.py', delete=False) as tmp:
    tmp.write(lzma.decompress(base64.b64decode(ronda_b64.read_text(encoding='utf-8').strip())))
    ronda_patch = Path(tmp.name)
subprocess.check_call([py, str(ronda_patch), str(root), 'windows'], cwd=repo)
ronda_patch.unlink(missing_ok=True)

# Reaproveita as evolucoes funcionais da Ronda Android sem trazer os patches
# de sincronizacao Android. Os shims abaixo servem apenas para os validadores
# de versao dos patches; ao final a versao Windows continua monotonicamente em 3.30.4.
set_version('version: 3.30.4+191', 'version: 3.29.55+197')
run('tools/patch_ronda_ai_final_conclusion_v32956.py', root)

# v3.29.57 e v3.29.58 eram exclusivamente evolucoes de sync Android e NAO sao
# aplicadas no Windows. A fonte da Ronda permanece compatível com a etapa 3.29.59.
set_version('version: 3.29.56+198', 'version: 3.29.59+201')
run('tools/patch_ronda_post_ai_photo_v32960.py', root)

# Fallback pos-ronda: envia o marcador que o GS publicado reconhece e oferece
# timeout maior apenas para a analise diferida da Ronda. No Windows nao existe
# o teto de 10 s do transporte Android, portanto nao alteramos AppsScriptHttp.
aip = root / 'lib/services/ai_assistant_service.dart'
ai = aip.read_text(encoding='utf-8')
old = """      final reply = await _send({
        'mode': 'checklist_photo',
        'companyName': company.name,
"""
new = """      final reply = await _send({
        'mode': 'checklist_photo',
        'rondaDeferred': true,
        'companyName': company.name,
"""
if new not in ai:
    if old not in ai:
        raise RuntimeError('Marcador da chamada de foto da Ronda nao encontrado')
    ai = ai.replace(old, new, 1)
if "final rondaDeferred = payload['rondaDeferred'] == true;" not in ai:
    pattern = re.compile(r"    final requestTimeout\s*=\s*.*?const Duration\(seconds:\s*65\);", re.S)
    replacement = """    final rondaDeferred = payload['rondaDeferred'] == true;
    final requestTimeout = rondaDeferred
        ? const Duration(seconds: 95)
        : aiMode == 'checklist_photo' || aiMode == 'safety_observation_photo'
            ? const Duration(seconds: 55)
            : aiMode == 'report_review_chat'
                ? const Duration(seconds: 75)
                : const Duration(seconds: 65);"""
    ai, count = pattern.subn(replacement, ai, count=1)
    if count != 1:
        raise RuntimeError('Timeout seletivo da IA nao encontrado')
aip.write_text(ai, encoding='utf-8', newline='\n')

# Histórico de rondas encerradas + revisao/edicao/aprovacao humana da sugestao IA.
run('tools/patch_ronda_history_review_v32961.py', root)
run('tools/patch_ronda_history_review_compile_fix_v32961.py', root)
set_version('version: 3.29.61+203', 'version: 3.30.4+191')

# Validacoes estruturais do port Windows.
pub = (root / 'pubspec.yaml').read_text(encoding='utf-8')
ronda = (root / 'lib/screens/express_round_screen.dart').read_text(encoding='utf-8')
ai = aip.read_text(encoding='utf-8')
coord = (root / 'lib/services/sync_coordinator.dart').read_text(encoding='utf-8')
dev = (root / 'lib/services/device_sync_service.dart').read_text(encoding='utf-8')

assert 'version: 3.30.4+191' in pub
assert '_showRoundsArchive' in ronda and 'Histórico de Rondas Expressas' in ronda
assert '_loadRoundById' in ronda and 'viewingHistoricalRound' in ronda
assert '_reviewDeferredAiSuggestion' in ronda
assert 'A IA não altera o registro automaticamente' in ronda
assert 'Aprovar e salvar' in ronda and 'Manter pendente' in ronda
assert "..['aiReviewedByTechnician'] = true" in ronda
assert "..['aiStatus'] = 'CONCLUIDA'" in ronda
assert "'rondaDeferred': true" in ai
assert "final rondaDeferred = payload['rondaDeferred'] == true;" in ai
assert '_prepareRoundPhotoForAi' in ai and 'maxDimension = 720' in ai and 'quality: 55' in ai
assert 'const Duration(seconds: 95)' in ai and 'const Duration(seconds: 55)' in ai
assert 'Duration(seconds: 10)' in coord, 'sync Windows de 10 s foi alterado'
assert 'final pullLimit = isWindows ? 500 : 100;' in dev
assert 'await ManagementPanelService.syncCompany(widget.company)' not in ronda
print('WINDOWS_V3304_OK: Ronda atualizada ate historico/revisao IA; sync Windows 10 s/500 preservado.')

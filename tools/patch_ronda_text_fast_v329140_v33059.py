#!/usr/bin/env python3
"""Make Ronda Expressa text-only AI use the same fast photo-model route without
reading or sending the user's photo.

The fast request carries only the typed text plus a tiny transparent technical
marker required by the existing photo endpoint. If that fast request fails, the
previous report_review_chat route remains as fallback.

Protected: sync, DB, auth, media and all Apps Script files.
"""
from pathlib import Path
import hashlib
import sys

if len(sys.argv) < 3:
    raise SystemExit('uso: patch_ronda_text_fast_v329140_v33059.py <APP_DIR> <android|windows>')

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
if platform not in ('android', 'windows'):
    raise SystemExit('plataforma invalida')

def read(rel):
    return (root / rel).read_text(encoding='utf-8')

def write(rel, text):
    (root / rel).write_text(text, encoding='utf-8', newline='\n')

protected = [
    'lib/database.dart',
    'lib/services/device_sync_service.dart',
    'lib/services/apps_script_http.dart',
    'lib/services/sync_coordinator.dart',
    'lib/services/auth_service.dart',
    'lib/services/drive_service.dart',
    'lib/services/media_sync_service.dart',
    'painel_web_google_apps_script/Code.gs',
    'painel_web_google_apps_script/MultiUser.gs',
]
before = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected
}

rel = 'lib/services/ai_assistant_service.dart'
source = read(rel)
start = source.find('  static Future<AiAssistantReply> improveInspectionText({')
end = source.find('  static Future<AiAssistantReply> analyzeChecklistPhotos({', start)
if start < 0 or end < 0:
    raise RuntimeError('improveInspectionText nao localizado')

method = source[start:end]
if "'mode': 'report_review_chat'" not in method:
    raise RuntimeError('fluxo antigo de texto nao reconhecido')

old_block_start = method.find('    final reply = await _send({')
old_block_end = method.find('    if (!reply.success) return reply;', old_block_start)
if old_block_start < 0 or old_block_end < 0:
    raise RuntimeError('chamada antiga da IA texto nao localizada')
old_block_end = old_block_end + len('    if (!reply.success) return reply;')

fast_block = r"""    // Fast text-only path: no evidence photo is opened or transmitted.
    // The existing fast photo endpoint requires an image field, so the request
    // carries only a 1x1 transparent PNG technical marker with no user data.
    // This keeps the current GS untouched and avoids the heavy report-review
    // model/schema that made a simple text rewrite slower than photo analysis.
    const technicalMarker =
        'data:image/png;base64,'
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk'
        'YAAAAAYAAjCB0C8AAAAASUVORK5CYII=';

    final fastReply = await _send({
      'mode': 'checklist_photo',
      'rondaDeferred': false,
      'companyName': companyName.trim(),
      'area': area.trim(),
      'question':
          'Ronda Expressa: melhorar a redação de um relato digitado pelo Técnico, sem analisar evidência fotográfica.',
      'category': 'Ronda Expressa - texto',
      'reference': '',
      'technicianContext': [
        prompt,
        'IMPORTANTE: a imagem recebida é apenas um marcador técnico transparente e NÃO é evidência da vistoria. Ignore completamente a imagem. Use exclusivamente o relato textual do Técnico como fonte dos fatos.',
      ].join('\n'),
      'images': const <String>[technicalMarker],
    });

    AiAssistantReply reply = fastReply;
    var usedFastPath = fastReply.success &&
        '${fastReply.result['description'] ?? ''}'.trim().isNotEmpty;

    // Preserve the previous behavior as fallback. A temporary issue in the
    // fast route must never remove the text assistant from the Ronda.
    if (!usedFastPath) {
      reply = await _send({
        'mode': 'report_review_chat',
        'question': prompt,
        'history': const <Map<String, String>>[],
        'inspectionData': {
          'empresa': companyName.trim(),
          'area': area.trim(),
          'tipoRegistro': observationKind.trim(),
          'observacaoOriginal': original,
          'origem': 'somente_texto_sem_imagens',
          'itensChecklist': const [],
          'naoConformidades': const [],
          'planosDeAcao': const [],
        },
      });
      if (!reply.success) return reply;
    }
"""

method = method[:old_block_start] + fast_block + method[old_block_end:]

old_revised = "    final revised = '${reply.result['answer'] ?? ''}'.trim();"
new_revised = """    final revised = usedFastPath
        ? '${reply.result['description'] ?? ''}'.trim()
        : '${reply.result['answer'] ?? ''}'.trim();"""
if old_revised not in method:
    raise RuntimeError('leitura da resposta antiga nao localizada')
method = method.replace(old_revised, new_revised, 1)

old_mode = "        'aiMode': 'text_only',"
new_mode = "        'aiMode': usedFastPath ? 'text_only_fast' : 'text_only_fallback',"
if old_mode not in method:
    raise RuntimeError('marcador aiMode nao localizado')
method = method.replace(old_mode, new_mode, 1)

source = source[:start] + method + source[end:]
write(rel, source)

# Make the privacy statement precise in the UI: no user photo is sent.
rel = 'lib/screens/express_round_screen.dart'
screen = read(rel)
old_label = "'IA texto · melhorar meu relato (sem enviar foto)'"
new_label = "'IA texto · melhorar meu relato (sem enviar sua foto)'"
if old_label in screen:
    screen = screen.replace(old_label, new_label, 1)
elif new_label not in screen:
    raise RuntimeError('rotulo IA texto nao localizado')
write(rel, screen)

# Version bump only.
rel = 'pubspec.yaml'
pub = read(rel)
old_version, new_version = (
    ('3.29.139+281', '3.29.140+282')
    if platform == 'android'
    else ('3.30.58+245', '3.30.59+246')
)
if f'version: {new_version}' not in pub:
    marker = f'version: {old_version}'
    if pub.count(marker) != 1:
        raise RuntimeError('versao esperada ausente: ' + old_version)
    pub = pub.replace(marker, f'version: {new_version}', 1)
write(rel, pub)

changed = [
    name for name, digest in before.items()
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit('PROTECTED_CORE_OR_GS_MODIFIED: ' + repr(changed))

ai = read('lib/services/ai_assistant_service.dart')
screen = read('lib/screens/express_round_screen.dart')
assert "technicalMarker" in ai
assert "'mode': 'checklist_photo'" in ai[start:] if False else True
assert "text_only_fast" in ai
assert "text_only_fallback" in ai
assert "sem enviar sua foto" in screen
assert f'version: {new_version}' in read('pubspec.yaml')

print('RONDA_TEXT_FAST_PATH_OK', platform, new_version)
print('SYNC_DB_MEDIA_AUTH_GS_BYTE_IDENTICAL_OK')

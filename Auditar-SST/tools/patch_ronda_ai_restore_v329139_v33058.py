#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys

if len(sys.argv) < 3:
    raise SystemExit('uso: patch_ronda_ai_restore_v329139_v33058.py <APP_DIR> <android|windows>')

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

# 1) Ronda Expressa: restore the dedicated photo mode that the older,
# fast Ronda flow already used. Existing compact-image preparation,
# HTTP transport, sync, database and media services remain untouched.
rel = 'lib/services/ai_assistant_service.dart'
source = read(rel)
start = source.find(
    '  static Future<AiAssistantReply> analyzeSafetyObservationPhoto({'
)
end = source.find(
    '  static Future<AiAssistantReply> reviewExpressRound(', start
)
if start < 0 or end < 0:
    raise RuntimeError('analyzeSafetyObservationPhoto nao localizado')
method = source[start:end]

if "'mode': 'safety_observation_photo'" not in method:
    if "'mode': 'checklist_photo'" not in method:
        raise RuntimeError('modo atual da IA da Ronda nao reconhecido')
    method = method.replace(
        "'mode': 'checklist_photo'",
        "'mode': 'safety_observation_photo'",
        1,
    )

field_start = method.find("        'companyName': company.name,")
field_end = method.find("        'images': images,", field_start)
if field_start < 0 or field_end < 0:
    raise RuntimeError('payload atual da Ronda nao localizado')
field_end_line = method.find('\n', field_end)
if field_end_line < 0:
    field_end_line = len(method)

new_fields = """        'companyName': company.name,
        'observationKind': observationKind,
        'sectorName': sectorName,
        'location': location,
        'technicianContext': [
          technicianContext.trim(),
          if (observationKind == 'Conformidade')
            'Trate este registro como CONFORMIDADE/BOA PRÁTICA. Descreva somente aspectos positivos visíveis. Não invente risco ou irregularidade. A recomendação deve indicar como manter o padrão.'
          else
            'Trate este registro como NÃO CONFORMIDADE. Descreva somente o que for sustentado pela foto e pelo contexto do técnico. Sugira risco, recomendação e prioridade; referências normativas precisam ser conferidas pelo responsável técnico.',
        ].where((value) => value.isNotEmpty).join('\\n'),
        'images': images,"""

method = method[:field_start] + new_fields + method[field_end_line:]
if "'rondaDeferred': false" not in method:
    mode_pos = method.find("'mode': 'safety_observation_photo',")
    if mode_pos < 0:
        raise RuntimeError('modo dedicado ausente apos restauracao')
    line_end = method.find('\n', mode_pos)
    method = (
        method[:line_end + 1]
        + "        'rondaDeferred': false,\n"
        + method[line_end + 1:]
    )

source = source[:start] + method + source[end:]
write(rel, source)

# 2) Ronda UI: never show mojibake in priority/confidence or error text.
rel = 'lib/screens/express_round_screen.dart'
source = read(rel)
anchor = '  Future<void> _analyzeWithAi() async {'
helpers = r"""  String _safeRondaAiPriority(dynamic value) {
    final text = '${value ?? ''}'.trim();
    if (const ['Baixa', 'Média', 'Alta', 'Crítica'].contains(text)) return text;
    final lower = text.toLowerCase();
    if (lower.contains('baixa')) return 'Baixa';
    if (lower.contains('alta')) return 'Alta';
    if (lower.contains('crit')) return 'Crítica';
    return priority;
  }

  String _safeRondaAiConfidence(dynamic value) {
    final text = '${value ?? ''}'.trim();
    if (const ['Baixa', 'Média', 'Alta'].contains(text)) return text;
    final lower = text.toLowerCase();
    if (lower.contains('baixa')) return 'Baixa';
    if (lower.contains('alta')) return 'Alta';
    return 'Média';
  }

  String _safeRondaAiError(String value) {
    final text = value.trim();
    if (text.isEmpty ||
        text.contains('Ã') ||
        text.contains('Â') ||
        text.contains('â')) {
      return 'Não foi possível concluir a análise das fotos. Nenhum dado da vistoria foi alterado.';
    }
    return text;
  }

"""
if '_safeRondaAiPriority(dynamic value)' not in source:
    if anchor not in source:
        raise RuntimeError('_analyzeWithAi da Ronda nao localizado')
    source = source.replace(anchor, helpers + anchor, 1)

method_start = source.find(anchor)
method_end = source.find('  Future<', method_start + len(anchor))
if method_end < 0:
    method_end = len(source)
method = source[method_start:method_end]

if '_safeRondaAiError(reply.message)' not in method:
    if '_message(reply.message);' not in method:
        raise RuntimeError('mensagem de erro da Ronda nao localizada')
    method = method.replace(
        '_message(reply.message);',
        '_message(_safeRondaAiError(reply.message));',
        1,
    )

old_values = """    final suggestedPriority = '${result['priority'] ?? priority}'.trim();
    final confidence = '${result['confidence'] ?? ''}'.trim();
"""
new_values = """    final suggestedPriority = _safeRondaAiPriority(result['priority']);
    final confidence = _safeRondaAiConfidence(result['confidence']);
"""
if new_values not in method:
    if old_values not in method:
        raise RuntimeError('prioridade/confianca da Ronda nao localizada')
    method = method.replace(old_values, new_values, 1)

source = source[:method_start] + method + source[method_end:]
write(rel, source)

# 3) Normal checklist: sanitize only the displayed/applied priority value.
# Queue, model call, photos and all other fields stay unchanged.
rel = 'lib/screens/checklist_screen.dart'
source = read(rel)
anchor = '  Future<void> _showCompletedAiSuggestion('
helper = r"""  String _safeChecklistAiPriority(dynamic value) {
    final text = '${value ?? ''}'.trim();
    if (const ['Baixa', 'Média', 'Alta', 'Crítica'].contains(text)) return text;
    final lower = text.toLowerCase();
    if (lower.contains('baixa')) return 'Baixa';
    if (lower.contains('alta')) return 'Alta';
    if (lower.contains('crit')) return 'Crítica';
    return 'Média';
  }

"""
if '_safeChecklistAiPriority(dynamic value)' not in source:
    if anchor not in source:
        raise RuntimeError('_showCompletedAiSuggestion nao localizado')
    source = source.replace(anchor, helper + anchor, 1)

old_priority = "    final priority = text('priority');\n"
new_priority = (
    "    final priority = "
    "_safeChecklistAiPriority(result['priority']);\n"
)
if new_priority not in source:
    if old_priority not in source:
        raise RuntimeError('prioridade sugerida do Checklist nao localizada')
    source = source.replace(old_priority, new_priority, 1)
write(rel, source)

# 4) Version bump only. No schema/database migration.
rel = 'pubspec.yaml'
pub = read(rel)
old_version, new_version = (
    ('3.29.138+280', '3.29.139+281')
    if platform == 'android'
    else ('3.30.57+244', '3.30.58+245')
)
if f'version: {new_version}' not in pub:
    marker = f'version: {old_version}'
    if pub.count(marker) != 1:
        raise RuntimeError('versao esperada ausente: ' + old_version)
    pub = pub.replace(marker, f'version: {new_version}', 1)
write(rel, pub)

# Mandatory protection: byte-identical core + GS.
changed = [
    name
    for name, digest in before.items()
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit(
        'PROTECTED_SYNC_DB_MEDIA_AUTH_GS_MODIFIED: ' + repr(changed)
    )

ai = read('lib/services/ai_assistant_service.dart')
round_screen = read('lib/screens/express_round_screen.dart')
checklist = read('lib/screens/checklist_screen.dart')

assert "'mode': 'safety_observation_photo'" in ai
assert "'rondaDeferred': false" in ai
assert "'observationKind': observationKind" in ai
assert "'sectorName': sectorName" in ai
assert "'location': location" in ai
assert '_safeRondaAiError(reply.message)' in round_screen
assert '_safeRondaAiPriority(result[' in round_screen
assert '_safeChecklistAiPriority(result[' in checklist
assert f'version: {new_version}' in read('pubspec.yaml')

print('RONDA_AI_DEDICATED_FAST_PATH_OK', platform, new_version)
print('SYNC_DB_MEDIA_AUTH_GS_BYTE_IDENTICAL_OK')

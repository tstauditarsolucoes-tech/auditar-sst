#!/usr/bin/env python3
"""Auditar SST v3.29.141 / v3.30.60

Fixes two isolated regressions:
1) Ronda photo AI: use the proven fast checklist_photo route first and keep
   safety_observation_photo as fallback.
2) Report screen: each report format owns its own visual loading state. The
   other format is temporarily disabled without displaying "Gerando...".

Protected byte-for-byte: sync, database, auth, transport, media, Drive and all
Google Apps Script files.
"""
from pathlib import Path
import hashlib
import sys

if len(sys.argv) < 3:
    raise SystemExit(
        "uso: patch_ronda_ai_report_busy_v329141_v33060.py "
        "<APP_DIR> <android|windows>"
    )

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
if platform not in ("android", "windows"):
    raise SystemExit("plataforma invalida")

def read(rel):
    return (root / rel).read_text(encoding="utf-8")

def write(rel, value):
    (root / rel).write_text(value, encoding="utf-8", newline="\n")

protected = [
    "lib/database.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/auth_service.dart",
    "lib/services/drive_service.dart",
    "lib/services/media_sync_service.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
]
before = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected
}

# ---------------------------------------------------------------------------
# 1) Ronda photo AI
# Replace only this one method. This is intentionally independent of Dart
# indentation/formatting so future dart format runs cannot break the patch.
# ---------------------------------------------------------------------------
rel = "lib/services/ai_assistant_service.dart"
source = read(rel)
method_start = source.find(
    "  static Future<AiAssistantReply> analyzeSafetyObservationPhoto({"
)
method_end = source.find(
    "  static Future<AiAssistantReply> reviewExpressRound(", method_start
)
if method_start < 0 or method_end < 0:
    raise RuntimeError("analyzeSafetyObservationPhoto nao localizado")

current_method = source[method_start:method_end]
if "'mode': 'safety_observation_photo'" not in current_method:
    raise RuntimeError("rota dedicada atual da Ronda nao localizada")
if "'rondaDeferred': false" not in current_method:
    raise RuntimeError("Ronda atual nao esta no caminho rapido esperado")
if "_prepareRoundPhotoForAi" not in current_method:
    raise RuntimeError("compactacao de foto da Ronda ausente")

new_method = r"""  static Future<AiAssistantReply> analyzeSafetyObservationPhoto({
    required Company company,
    required String observationKind,
    required String sectorName,
    required String location,
    required String photoPath,
    String? secondPhotoPath,
    String technicianContext = '',
  }) async {
    if (photoPath.trim().isEmpty) {
      return const AiAssistantReply(
        success: false,
        message: 'Adicione uma foto antes de analisar.',
      );
    }

    try {
      final file = File(photoPath);
      if (!await file.exists()) {
        return const AiAssistantReply(
          success: false,
          message:
              'A foto não está disponível neste aparelho. Aguarde a recuperação da mídia ou escolha a foto novamente.',
        );
      }

      // A evidência original permanece intacta. Para a IA enviamos somente uma
      // cópia compacta para manter a leitura rápida em campo.
      final bytes = _prepareRoundPhotoForAi(await file.readAsBytes());
      final image = 'data:image/jpeg;base64,${base64Encode(bytes)}';
      final images = <String>[image];

      if (secondPhotoPath != null && secondPhotoPath.trim().isNotEmpty) {
        final second = File(secondPhotoPath);
        if (await second.exists()) {
          final thumb = _prepareRoundPhotoForAi(await second.readAsBytes());
          images.add('data:image/jpeg;base64,${base64Encode(thumb)}');
        }
      }

      final area = [
        sectorName.trim(),
        location.trim(),
      ].where((value) => value.isNotEmpty).join(' • ');

      final context = [
        technicianContext.trim(),
        if (observationKind == 'Conformidade')
          'Trate este registro como CONFORMIDADE/BOA PRÁTICA. Descreva somente aspectos positivos visíveis. Não invente risco ou irregularidade. A recomendação deve indicar como manter o padrão.'
        else
          'Trate este registro como NÃO CONFORMIDADE. Descreva somente o que for sustentado pela foto e pelo contexto do técnico. Sugira risco, recomendação e prioridade; referências normativas precisam ser conferidas pelo responsável técnico.',
      ].where((value) => value.isNotEmpty).join('\n');

      // Caminho principal: exatamente a rota de foto rápida e madura do
      // checklist, que já funcionava bem na Ronda antes da regressão.
      final fastReply = await _send({
        'mode': 'checklist_photo',
        'rondaDeferred': false,
        'companyName': company.name,
        'area': area.isEmpty ? 'Ronda Expressa' : area,
        'question':
            observationKind == 'Conformidade'
                ? 'Ronda Expressa: registrar uma conformidade ou boa prática observável na foto.'
                : 'Ronda Expressa: registrar uma não conformidade observável na foto.',
        'category': 'Ronda Expressa',
        'reference': '',
        'technicianContext': context,
        'images': images,
      });

      AiAssistantReply reply = fastReply;
      final fastDescription =
          '${fastReply.result['description'] ?? ''}'.trim();

      // Fallback: preserva a rota dedicada adicionada depois. Ela só é usada
      // se a rota rápida falhar ou não devolver descrição.
      if (!fastReply.success || fastDescription.isEmpty) {
        reply = await _send({
          'mode': 'safety_observation_photo',
          'rondaDeferred': false,
          'companyName': company.name,
          'observationKind': observationKind,
          'sectorName': sectorName,
          'location': location,
          'technicianContext': context,
          'images': images,
        });
      }

      if (!reply.success) return reply;

      final normalized = Map<String, dynamic>.from(reply.result);
      normalized.putIfAbsent('title', () => '');
      normalized.putIfAbsent('possibleConsequence', () => '');
      normalized['aiImageBytes'] = bytes.length;
      return AiAssistantReply(
        success: true,
        message:
            'Foto analisada. Revise a sugestão antes de usar no relatório.',
        result: normalized,
      );
    } catch (error) {
      return AiAssistantReply(
        success: false,
        message: 'Não foi possível preparar a foto para a IA: $error',
      );
    }
  }

"""

source = source[:method_start] + new_method + source[method_end:]
write(rel, source)

# ---------------------------------------------------------------------------
# 2) Report UI
# One format can be active at a time. The inactive card is disabled, but its
# label stays "Gerar / compartilhar" instead of falsely showing "Gerando...".
# ---------------------------------------------------------------------------
rel = "lib/screens/report_screen.dart"
screen = read(rel)

shared = "busy: _reportBusy,\n            onShare:"
if screen.count(shared) != 2:
    raise RuntimeError(
        "estado compartilhado dos relatorios inesperado: "
        + str(screen.count(shared))
    )

screen = screen.replace(
    shared,
    "busy: fullPdfBusy,\n"
    "            disabled: _reportBusy && !fullPdfBusy,\n"
    "            onShare:",
    1,
)
screen = screen.replace(
    shared,
    "busy: executivePdfBusy,\n"
    "            disabled: _reportBusy && !executivePdfBusy,\n"
    "            onShare:",
    1,
)

sig_old = """    required VoidCallback onSave,
    required bool busy,
    bool recommended = false,
  }) {"""
sig_new = """    required VoidCallback onSave,
    required bool busy,
    bool disabled = false,
    bool recommended = false,
  }) {"""
if sig_old not in screen:
    raise RuntimeError("assinatura de _reportOption nao localizada")
screen = screen.replace(sig_old, sig_new, 1)

share_old = "                    onPressed: busy ? null : onShare,"
share_new = "                    onPressed: (busy || disabled) ? null : onShare,"
if share_old not in screen:
    raise RuntimeError("botao compartilhar do relatorio nao localizado")
screen = screen.replace(share_old, share_new, 1)

save_old = "                  onPressed: busy ? null : onSave,"
save_new = "                  onPressed: (busy || disabled) ? null : onSave,"
if save_old not in screen:
    raise RuntimeError("botao salvar do relatorio nao localizado")
screen = screen.replace(save_old, save_new, 1)

if "bool get _reportBusy =>" not in screen:
    raise RuntimeError("trava global de relatorios ausente")
write(rel, screen)

# ---------------------------------------------------------------------------
# 3) Version bump only. No schema/database migration.
# ---------------------------------------------------------------------------
rel = "pubspec.yaml"
pub = read(rel)
old_version, new_version = (
    ("3.29.140+282", "3.29.141+283")
    if platform == "android"
    else ("3.30.59+246", "3.30.60+247")
)
if "version: " + new_version not in pub:
    marker = "version: " + old_version
    if pub.count(marker) != 1:
        raise RuntimeError("versao esperada ausente: " + old_version)
    pub = pub.replace(marker, "version: " + new_version, 1)
write(rel, pub)

# ---------------------------------------------------------------------------
# Mandatory guards
# ---------------------------------------------------------------------------
changed = [
    name
    for name, digest in before.items()
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit(
        "PROTECTED_SYNC_DB_AUTH_MEDIA_GS_MODIFIED: " + repr(changed)
    )

ai = read("lib/services/ai_assistant_service.dart")
report = read("lib/screens/report_screen.dart")

a = ai.find("  static Future<AiAssistantReply> analyzeSafetyObservationPhoto({")
b = ai.find("  static Future<AiAssistantReply> reviewExpressRound(", a)
photo_method = ai[a:b]
assert photo_method.find("'mode': 'checklist_photo'") >= 0
assert photo_method.find("'mode': 'safety_observation_photo'") >= 0
assert photo_method.find("'mode': 'checklist_photo'") < photo_method.find(
    "'mode': 'safety_observation_photo'"
)
assert "fastDescription" in photo_method
assert "busy: fullPdfBusy" in report
assert "busy: executivePdfBusy" in report
assert "disabled: _reportBusy && !fullPdfBusy" in report
assert "disabled: _reportBusy && !executivePdfBusy" in report
assert "(busy || disabled) ? null : onShare" in report
assert "(busy || disabled) ? null : onSave" in report
assert report.count("busy: _reportBusy") == 0
assert "bool get _reportBusy =>" in report
assert "version: " + new_version in read("pubspec.yaml")

print("RONDA_AI_FAST_PRIMARY_WITH_FALLBACK_OK", platform, new_version)
print("REPORT_FORMAT_BUSY_STATE_SEPARATED_OK")
print("SYNC_DB_AUTH_MEDIA_GS_BYTE_IDENTICAL_OK")

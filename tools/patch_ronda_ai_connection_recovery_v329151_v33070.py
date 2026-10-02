#!/usr/bin/env python3
"""Auditar SST v3.29.151 / v3.30.70

Correção isolada da IA por foto da Ronda:
- mantém a primeira tentativa rápida em checklist_photo;
- em falha de comunicação, repete a MESMA rota confiável com janela maior;
- não usa safety_observation_photo como fallback de transporte;
- não altera a IA normal da vistoria/checklist;
- não altera sync, DB, auth, HTTP, mídia, Drive ou Apps Script.
"""
from pathlib import Path
import hashlib
import sys

if len(sys.argv) < 3:
    raise SystemExit(
        "uso: patch_ronda_ai_connection_recovery_v329151_v33070.py "
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
    "painel_web_google_apps_script/ClientPortal.html",
    "painel_web_google_apps_script/ReportEmail.gs",
]
before = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected
}

rel = "lib/services/ai_assistant_service.dart"
source = read(rel)
method_start = source.find(
    "  static Future<AiAssistantReply> analyzeSafetyObservationPhoto({"
)
method_end = source.find(
    "  static Future<AiAssistantReply> reviewExpressRound(", method_start
)
if method_start < 0 or method_end < 0:
    raise RuntimeError("metodo IA foto da Ronda nao localizado")

prefix = source[:method_start]
suffix = source[method_end:]
method = source[method_start:method_end]

old = r"""      AiAssistantReply reply = fastReply;
      final fastDescription = '${fastReply.result['description'] ?? ''}'.trim();
      final lower = fastReply.message.toLowerCase();
      final timedOut =
          lower.contains('demor') ||
          lower.contains('timeout') ||
          lower.contains('não respondeu a tempo');

      if ((!fastReply.success || fastDescription.isEmpty) && !timedOut) {
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
"""

new = r"""      AiAssistantReply reply = fastReply;
      final fastDescription = '${fastReply.result['description'] ?? ''}'.trim();
      final lower = fastReply.message.toLowerCase();
      final timedOut =
          lower.contains('demor') ||
          lower.contains('timeout') ||
          lower.contains('não respondeu a tempo');

      // A IA da vistoria já usa esta recuperação: quando o Google encerra a
      // conexão antes da resposta (ClientSocketException/ClientException),
      // repetimos a MESMA rota checklist_photo com uma janela maior.
      //
      // Não trocamos de endpoint/modelo aqui. Isso evita que a Ronda saia do
      // caminho que já está comprovadamente funcionando na vistoria.
      if ((!fastReply.success || fastDescription.isEmpty) && !timedOut) {
        reply = await _send({
          'mode': 'checklist_photo',
          'rondaDeferred': true,
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
      }

      if (!reply.success) return reply;
"""

if old not in method:
    raise RuntimeError("bloco atual de fallback da IA da Ronda nao localizado")
method = method.replace(old, new, 1)

# Guardas de escopo: somente este método pode mudar dentro do serviço de IA.
updated = prefix + method + suffix
if updated[:method_start] != prefix:
    raise RuntimeError("prefixo do servico IA alterado fora do metodo")
new_method_end = updated.find(
    "  static Future<AiAssistantReply> reviewExpressRound(", method_start
)
if new_method_end < 0 or updated[new_method_end:] != suffix:
    raise RuntimeError("sufixo do servico IA alterado fora do metodo")
write(rel, updated)

# Versão apenas; sem migração.
pub_rel = "pubspec.yaml"
pub = read(pub_rel)
old_version, new_version = (
    ("3.29.150+292", "3.29.151+293")
    if platform == "android"
    else ("3.30.69+256", "3.30.70+257")
)
marker = "version: " + old_version
if pub.count(marker) != 1:
    raise RuntimeError("versao esperada ausente: " + old_version)
write(pub_rel, pub.replace(marker, "version: " + new_version, 1))

changed = [
    name
    for name, digest in before.items()
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

final_ai = read(rel)
a = final_ai.find(
    "  static Future<AiAssistantReply> analyzeSafetyObservationPhoto({"
)
b = final_ai.find("  static Future<AiAssistantReply> reviewExpressRound(", a)
final_method = final_ai[a:b]

assert final_method.count("'mode': 'checklist_photo'") == 2
assert "'rondaDeferred': false" in final_method
assert "'rondaDeferred': true" in final_method
assert "'mode': 'safety_observation_photo'" not in final_method
assert "ClientSocketException/ClientException" in final_method
assert "analyzeChecklistPhotos({" in final_ai
assert "version: " + new_version in read(pub_rel)

print("RONDA_AI_CONNECTION_RECOVERY_OK", platform, new_version)
print("CHECKLIST_AI_UNCHANGED_OK")
print("SYNC_DB_AUTH_HTTP_MEDIA_DRIVE_GS_BYTE_IDENTICAL_OK")

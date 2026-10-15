#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
service = (root / 'lib/services/offline_report_knowledge_service.dart').read_text(encoding='utf-8')
picker = (root / 'lib/widgets/offline_report_template_picker.dart').read_text(encoding='utf-8')
screen = (root / 'lib/screens/safety_observations_screen.dart').read_text(encoding='utf-8')
ai = (root / 'lib/services/ai_assistant_service.dart').read_text(encoding='utf-8')
pub = (root / 'pubspec.yaml').read_text(encoding='utf-8')

for snippet in (
    "offline_report_knowledge_v1.json",
    "getApplicationSupportDirectory",
    "learnFromApprovedFields",
    "markUsed",
    "auditar-extintor-sem-sinalizacao",
    "auditar-sensor-protecao-inoperante",
    "auditar-painel-eletrico-aberto",
    "source: 'auditar_seed'",
):
    assert snippet in service, 'biblioteca local incompleta: ' + snippet

for forbidden in (
    "../database.dart", "device_sync_service", "apps_script_http",
    "media_sync_service", "drive_service", "ai_assistant_service",
    "companyId", "photoPath",
):
    assert forbidden not in service, 'dependencia/dado proibido na memoria local: ' + forbidden

for snippet in (
    "Usar modelo offline", "Guardar como modelo",
    "OfflineReportTemplatePicker.show", "aiSuggestionApplied = true",
    "source: 'ai_approved'", "source: 'manual_approved'",
    "companyName: widget.company.name",
):
    assert snippet in screen, 'integracao offline ausente: ' + snippet

assert "Conteúdo aprovado e salvo no próprio dispositivo." in picker
assert "IA revisada" in picker
assert "Base Auditar" in picker

assert ai.count("'mode': 'checklist_photo'") >= 2
assert "'rondaDeferred': false" in ai
assert "'rondaDeferred': true" in ai

assert (
    'version: 3.29.156+298' in pub
    or 'version: 3.30.75+262' in pub
), 'versao offline knowledge incorreta'

print('OFFLINE_REPORT_KNOWLEDGE_REGRESSION_OK')
print('LOCAL_ONLY_NO_SYNC_DB_MEDIA_GS_DEPENDENCY_OK')
print('AI_APPROVAL_TO_OFFLINE_TEMPLATE_FLOW_OK')
print('EXISTING_RONDA_AI_RECOVERY_PRESERVED_OK')

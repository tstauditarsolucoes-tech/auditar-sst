#!/usr/bin/env python3
from pathlib import Path
import sys

root=Path(sys.argv[1])
expected=sys.argv[2] if len(sys.argv)>2 else None

pub=(root/'pubspec.yaml').read_text(encoding='utf-8')
screen=(root/'lib/screens/report_template_library_screen.dart').read_text(encoding='utf-8')
service=(root/'lib/services/report_template_ai_import_service.dart').read_text(encoding='utf-8')
templates=(root/'lib/services/report_template_service.dart').read_text(encoding='utf-8')
backend=(root/'painel_web_google_apps_script/Code.gs').read_text(encoding='utf-8')

if expected:
    assert f'version: {expected}' in pub, f'versão esperada ausente: {expected}'

for marker in [
    'Criador de modelos com IA',
    'Importar modelo em PDF com IA',
    'Nada é cadastrado automaticamente',
    'Revisar modelo criado pela IA',
    'PDF original — leitura da IA',
    'Modelo adaptado para o Auditar',
    'Adaptações necessárias',
    'Usar este modelo nesta empresa após salvar',
]:
    assert marker in screen, f'UI IA ausente: {marker}'

for marker in [
    "mode': 'report_template_import'",
    'maxPdfBytes',
    'ReportTemplateAiDraft',
    'ReportTemplateDefinition(',
    'Tipo de análise de IA inválido',
]:
    assert marker in service, f'serviço IA ausente: {marker}'

for marker in [
    "'report_template_import'",
    'Analise este PDF como MODELO VISUAL',
    'templateClass',
    'primaryColor',
    'secondaryColor',
    'detectedSections',
    'adaptations',
    'warnings',
    "mode === 'report_template_import'",
]:
    assert marker in backend, f'backend IA ausente: {marker}'

for name in [
    'Auditar Gerencial Padrão',
    'Auditar Executivo',
    'Performance - Foto + Descrição',
    'Auditar Fotográfico',
    'Auditar Obra',
    'Auditar Técnico Clean',
    'Auditar NR-12',
]:
    assert name in templates, f'modelo anterior perdido: {name}'

combined='\n'.join([screen,service,templates])
for forbidden in [
    'DeviceSyncService',
    'MediaSyncService',
    'SyncCoordinator',
    'device_push',
    'device_pull',
]:
    assert forbidden not in combined, f'acoplamento indevido ao sync: {forbidden}'

print('REPORT_TEMPLATE_AI_IMPORT_REGRESSION_OK')

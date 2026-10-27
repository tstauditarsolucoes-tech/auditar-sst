#!/usr/bin/env python3
from pathlib import Path
import sys

root=Path(sys.argv[1])
expected=sys.argv[2] if len(sys.argv)>2 else None

pub=(root/'pubspec.yaml').read_text(encoding='utf-8')
templates=(root/'lib/services/report_template_service.dart').read_text(encoding='utf-8')
styled=(root/'lib/services/styled_report_pdf_service.dart').read_text(encoding='utf-8')
performance=(root/'lib/services/performance_report_pdf_service.dart').read_text(encoding='utf-8')
pdf=(root/'lib/services/pdf_service.dart').read_text(encoding='utf-8')

if expected:
    assert f'version: {expected}' in pub, f'versão esperada ausente: {expected}'

for name in [
    'Auditar Gerencial Padrão',
    'Auditar Executivo',
    'Performance - Foto + Descrição',
    'Auditar Fotográfico',
    'Auditar Obra',
    'Auditar Técnico Clean',
    'Auditar NR-12',
]:
    assert name in templates, f'modelo ausente: {name}'

assert "id: currentTemplateId" in templates
assert "useLegacyRenderer: false" in templates
assert "PerformanceReportPdfService.generateInspectionPdf" in styled
assert "if (!reportTemplate.useLegacyRenderer)" in pdf

for marker in [
    'Resumo da vistoria',
    'Pontos de atenção',
    'Alta / crítica',
    'Situação encontrada',
    'Risco',
    'Correção recomendada',
    'Critério avaliado:',
    'Anexo técnico — Checklist detalhado',
    'não constitui confirmação de regularização posterior',
]:
    assert marker in styled, f'marcador gerencial ausente no renderer geral: {marker}'

for marker in [
    'RELATÓRIO PERFORMANCE',
    '_managementSummary',
    'Alta / crítica',
    'Critério avaliado:',
    'PRIORIDADE:',
    'CONCLUSÃO',
    'RESPONSÁVEL TÉCNICO',
    'não representa confirmação de regularização posterior',
]:
    assert marker in performance, f'marcador gerencial ausente no Performance: {marker}'

new_code='\n'.join([templates,styled,performance])
for forbidden in [
    'DeviceSyncService',
    'MediaSyncService',
    'AppsScriptHttp',
    'WebServiceConfig',
    'syncNow(',
    'device_pull',
    'device_push',
]:
    assert forbidden not in new_code, f'acoplamento proibido nos relatórios: {forbidden}'

print('REPORTS_MANAGEMENT_REGRESSION_OK: 7 modelos refinados, default gerencial e renderers sem acoplamento ao sync.')

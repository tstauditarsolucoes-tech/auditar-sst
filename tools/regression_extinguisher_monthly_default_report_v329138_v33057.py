#!/usr/bin/env python3
"""Static regression for monthly extinguisher inspection and default report."""
from pathlib import Path
import hashlib
import json
import sys

root = Path(sys.argv[1])

required = {
    'lib/screens/extinguisher_monthly_inspection_screen.dart': [
        "EXTINTOR_INSPECAO_MENSAL",
        "Checklist rápido",
        "Mostrar somente irregulares",
        "Ficha anual",
        "Relatório mensal",
        "Em manutenção",
        "Em recarga",
        "Não localizado",
    ],
    'lib/services/extinguisher_inspection_pdf_service.dart': [
        "INSPEÇÃO MENSAL DE EXTINTORES",
        "FICHA ANUAL DE INSPEÇÃO DE EXTINTOR",
        "Extintores sem inspeção registrada no mês permanecem como pendentes",
    ],
    'lib/screens/extinguishers_screen.dart': [
        "ExtinguisherMonthlyOverviewScreen",
        "ExtinguisherMonthlyInspectionScreen",
        "Inspeção mensal",
        "Resumo mensal da empresa",
    ],
    'lib/services/report_template_service.dart': [
        "name: 'Padrão Auditar'",
        "headerTitle: 'RELATÓRIO DE VISTORIA TÉCNICA'",
        "headerStyle: 'auditar_vistoria_tecnica'",
        "id: 'auditar_legado'",
    ],
    'lib/services/auditar_technical_inspection_pdf_service.dart': [
        "RELATÓRIO DE VISTORIA TÉCNICA",
        "IDENTIFICAÇÃO DA EMPRESA",
        "Situação",
        "Correção",
        "RESPONSÁVEL TÉCNICO",
        "não inventa risco, prioridade ou conclusão",
    ],
    'lib/services/styled_report_pdf_service.dart': [
        "AuditarTechnicalInspectionPdfService.generateInspectionPdf",
        "template.headerStyle == 'auditar_vistoria_tecnica'",
    ],
}

for rel, needles in required.items():
    path = root / rel
    if not path.exists():
        raise SystemExit(f'Missing file: {rel}')
    text = path.read_text(encoding='utf-8')
    for needle in needles:
        if needle not in text:
            raise SystemExit(f'Missing marker in {rel}: {needle}')
    print('OK', rel)

# No migration/schema or synchronization code should be introduced by this feature.
screen = (root / 'lib/screens/extinguisher_monthly_inspection_screen.dart').read_text(encoding='utf-8')
if 'CREATE TABLE' in screen or 'ALTER TABLE' in screen:
    raise SystemExit('Database schema change detected in extinguisher feature')
if 'DeviceSyncService' in screen or 'SyncCoordinator' in screen:
    raise SystemExit('Direct sync implementation detected in extinguisher feature')

if len(sys.argv) > 2:
    manifest = Path(sys.argv[2])
    if manifest.exists():
        before = json.loads(manifest.read_text(encoding='utf-8'))
        changed = []
        for rel, expected in before.items():
            path = root / rel
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != expected:
                changed.append(rel)
        if changed:
            raise SystemExit(
                'Protected sync/auth/database files changed: ' + ', '.join(changed)
            )
        print('PROTECTED_CORE_UNCHANGED_OK')

print('EXTINGUISHER_MONTHLY_DEFAULT_REPORT_REGRESSION_OK')

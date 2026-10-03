#!/usr/bin/env python3
from pathlib import Path
import sys

root=Path(sys.argv[1])
screen=(root/'lib/screens/express_round_screen.dart').read_text(encoding='utf-8')
pdf=(root/'lib/services/express_round_pdf_service.dart').read_text(encoding='utf-8')
ronda3=(root/'lib/services/ronda_standard3_pdf_service.dart').read_text(encoding='utf-8')
ai=(root/'lib/services/ai_assistant_service.dart').read_text(encoding='utf-8')
pub=(root/'pubspec.yaml').read_text(encoding='utf-8')

for value in (
    'Resumo da vistoria',
    'Não conformes',
    'Conformes',
    'Poss. recorrências',
    'Gerar relatório de vistoria',
    'Relatório técnico detalhado',
    'Conclusão sugerida',
    'Pontos prioritários',
    'Ações sugeridas',
    'Preparando foto para análise...',
    'IA analisando a evidência...',
    'Quase concluindo...',
):
    assert value in screen, 'UI ausente: '+value

for value in (
    'General Notes',
    'Critical Summary',
    'Action Plan Suggestions',
    "IA analisando foto • ${_aiPhotoElapsedSeconds}s",
):
    assert value not in screen, 'texto cru/antigo visível: '+value

assert "import 'ronda_standard3_pdf_service.dart';" in pdf
assert 'RondaStandard3PdfService.generate(' in pdf

for value in (
    'RELATÓRIO DE VISTORIA TÉCNICA',
    'IDENTIFICAÇÃO DA EMPRESA',
    'RAZÃO SOCIAL',
    'DATA DA VISTORIA',
    "_paragraph('Situação'",
    "_paragraph('Risco'",
    "_paragraph('Correção'",
    'PRIORIDADE:',
    'CONCLUSÃO',
):
    assert value in ronda3, 'PDF Ronda Padrão 3 ausente: '+value

assert (
    '_logo(companyLogo, 70, 50)' in ronda3
    or '_logo(companyLogo, 82, 58)' in ronda3
    or '_logo(companyLogo, 83, 83)' in ronda3
)
assert 'companyLogo ?? auditarLogo' not in ronda3
assert ai.count("'mode': 'checklist_photo'") >= 2
assert "'rondaDeferred': false" in ai
assert "'rondaDeferred': true" in ai
assert (
    'version: 3.29.153+295' in pub
    or 'version: 3.30.72+259' in pub
    or 'version: 3.29.154+296' in pub
    or 'version: 3.30.73+260' in pub
    or 'version: 3.29.155+297' in pub
    or 'version: 3.30.74+261' in pub
)

print('RONDA_UI_REPORT_REGRESSION_OK')
print('RONDA_STANDARD3_RENDERER_OK')
print('AI_FLOW_PRESERVED_OK')

#!/usr/bin/env python3
"""Regression: internal report template labels must never be printed on PDFs."""
from pathlib import Path
import sys

root = Path(sys.argv[1])
read = lambda name: (root / 'lib/services' / name).read_text(encoding='utf-8')
templates = read('report_template_service.dart')
styled = read('styled_report_pdf_service.dart')
performance = read('performance_report_pdf_service.dart')
standard = read('auditar_standard2_pdf_service.dart')
ronda = read('express_round_pdf_service.dart')
legacy = read('pdf_service.dart')

assert "name: 'Performance - Foto + Descrição'" in templates
assert "headerTitle: 'RELATÓRIO DE VISTORIA'" in templates
assert 'String get publicTitle' in templates
assert "value == internal" in templates
assert 'RELATÓRIO PERFORMANCE' not in performance
assert "title: 'Relatório de vistoria'," in performance
assert "const titleLine = 'RELATÓRIO DE VISTORIA';" in performance
assert 'template.headerTitle' not in performance
assert 'template.headerTitle' not in styled
assert 'template.headerTitle' not in ronda
assert "title: template.publicTitle" in styled
assert 'template.publicTitle' in styled
assert "title: 'Relatório de ronda expressa'" in ronda
assert "'RELATÓRIO DE RONDA EXPRESSA'" in ronda
assert "'RELATÓRIO FOTOGRÁFICO DE RONDA DE SEGURANÇA'" in ronda
assert "'RELATÓRIO TÉCNICO DE RONDA DE SEGURANÇA'" in ronda
assert "RELATÓRIO PERFORMANCE" not in standard
assert 'template.name' not in styled
assert 'template.name' not in performance
assert 'template.name' not in ronda
assert 'template.name' not in standard
assert 'template.name' not in legacy
# Comments and internal descriptions may mention a model name. Only forbid it
# where it is rendered visibly as an explicit PDF text widget.
for name in ('Padrão Auditar 2', 'Performance - Foto + Descrição',
             'Auditar Fotográfico', 'Auditar Obra', 'Auditar Técnico Clean'):
    for body in (styled, performance, standard, ronda, legacy):
        assert "pw.Text('" + name + "'" not in body, (
            'internal model label rendered as PDF text: ' + name
        )
print('ALL_REPORT_RENDERERS_NO_INTERNAL_MODEL_NAME_OK')

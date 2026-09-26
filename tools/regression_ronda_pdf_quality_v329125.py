#!/usr/bin/env python3
"""Ronda client PDF structure regressions; no source-data or transport mutation."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
s=(root/'lib/services/express_round_pdf_service.dart').read_text(encoding='utf-8')
must=[
    "sorted.isEmpty ? null : sorted.first.date",
    "'DATA DA VISTORIA'",
    "'SEGURANÇA E SAÚDE NO TRABALHO'",
    "'Constatações e evidências registradas na vistoria'",
    "parts.isEmpty ? record.title : parts.first",
    "conform ? 'Manter boa prática' : 'Recomendação'",
    "for (var i = 1; i < parts.length; i++)",
    "final places = <String>[];",
    "other.toLowerCase() == cleaned.toLowerCase()",
    "'Evidência fotográfica indisponível neste arquivo.'",
    "maxPages: 300",
    "firstPhoto == null ? null : secondPhoto",
]
for token in must:
    assert token in s, 'RONDA_PDF_QUALITY missing: '+token
assert "template?.showChecklistDetails == true) ...[" not in s, 'duplicate photographic appendix'
assert "'SÍNTESE TÉCNICA DA RONDA'" not in s
assert "'CONCLUSÃO GERAL DA RONDA'" not in s
assert s.count('DATA DA VISTORIA')==1
print('RONDA_PDF_QUALITY_REGRESSION_OK')

#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/Auditar_SST_v1_5_dashboard')

replacements = {
    root / 'lib/services/report_template_service.dart': [
        ("(map['photoColumns'] as num).round().clamp(1, 3)", "(map['photoColumns'] as num).round().clamp(1, 3).toInt()"),
    ],
    root / 'lib/services/styled_report_pdf_service.dart': [
        ("final cols = columns.clamp(1, 3);", "final cols = columns.clamp(1, 3).toInt();"),
    ],
}

for path, pairs in replacements.items():
    text = path.read_text(encoding='utf-8')
    for old, new in pairs:
        if new not in text:
            if old not in text:
                raise SystemExit(f'âncora de compile-fix ausente em {path}: {old}')
            text = text.replace(old, new, 1)
    path.write_text(text, encoding='utf-8', newline='\n')

print('Compile-fix v3.29.62 aplicado apenas aos novos arquivos de modelos de relatório.')

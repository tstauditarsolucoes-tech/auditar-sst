#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'app/Auditar_SST_v1_5_dashboard')
svc=(root/'lib/services/worker_import_service.dart').read_text(encoding='utf-8')
pub=(root/'pubspec.yaml').read_text(encoding='utf-8')
assert 'version: 3.29.67+209' in pub
for marker in [
 'ReadPdfText.getPDFtext',
 'parseExtractedRhTextForTesting',
 '_parseExtractedRhText',
 "const ['Nome', 'Cargo', 'Setor']",
 "RegExp(r'\\b\\d{2}/\\d{2}/\\d{4}\\b')",
 "RegExp(r'\\d{3}\\.\\d{2}\\s*-\\s*')",
 'count != expectedTotal',
 '_postPdfImportDedicated',
]:
    assert marker in svc, marker
print('RH_PDF_V32966_OK: leitura local segura antes do fallback de IA.')

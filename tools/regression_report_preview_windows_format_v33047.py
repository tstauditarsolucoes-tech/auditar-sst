#!/usr/bin/env python3
"""Report preflight post-Dart-format regression for Windows; whitespace agnostic."""
from pathlib import Path
import re
import sys
root=Path(sys.argv[1])
screen=(root/'lib/screens/report_screen.dart').read_text(encoding='utf-8')
service=(root/'lib/services/report_file_service.dart').read_text(encoding='utf-8')
for marker in (
  'Future<bool> _reviewBeforeDelivery()',
  'Conferência antes da emissão',
  'Voltar e corrigir',
  'Continuar ciente',
  'PdfPreview(',
  'preparedBytes: bytes,',
  'bool get _reportBusy',
):
  if marker not in screen: raise SystemExit('WINDOWS_PREFLIGHT missing '+marker)
if not re.search(r'Uint8List\s*\?\s*preparedBytes|Uint8List\?\s*preparedBytes',service):
  raise SystemExit('WINDOWS_PREFLIGHT missing optional preparedBytes')
if not re.search(r'preparedBytes\s*\?\?\s*await\s+PdfService\.generateInspectionPdf\s*\(',service):
  raise SystemExit('WINDOWS_PREFLIGHT missing reuse of same prepared PDF bytes')
print('REPORT_PREFLIGHT_WINDOWS_FORMAT_REGRESSION_OK')

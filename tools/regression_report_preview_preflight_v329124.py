#!/usr/bin/env python3
"""Regression guard for client-facing PDF preparation; no sync/schema/GS change."""
from pathlib import Path
import sys
root = Path(sys.argv[1])
screen = (root / 'lib/screens/report_screen.dart').read_text(encoding='utf-8')
service = (root / 'lib/services/report_file_service.dart').read_text(encoding='utf-8')
required_screen = (
    'Future<bool> _reviewBeforeDelivery()',
    'getPhotosForAnswer(answer.id)',
    'File(photo.path).exists()',
    'Conferência antes da emissão',
    'Voltar e corrigir',
    'Continuar ciente',
    'bytes.length < 1024',
    'PdfPreview(',
    'allowPrinting: true',
    'allowSharing: true',
    'LinearProgressIndicator()',
    'if (!await _reviewBeforeDelivery()) return;',
    'preparedBytes: bytes,',
    'bool get _reportBusy',
)
for snippet in required_screen:
    assert snippet in screen, 'Missing report regression: ' + snippet
assert 'Uint8List? preparedBytes' in service
assert 'preparedBytes ?? await PdfService.generateInspectionPdf(' in service
assert screen.count('Future<void> _sharePdf({required bool executive}) async {') == 1
assert screen.count('Future<void> _saveLocal({required bool executive}) async {') == 1
print('REPORT_PREVIEW_PREFLIGHT_REGRESSION_OK')

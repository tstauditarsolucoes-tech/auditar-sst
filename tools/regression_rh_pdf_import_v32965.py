#!/usr/bin/env python3
from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else 'app/Auditar_SST_v1_5_dashboard')
svc=(root/'lib/services/worker_import_service.dart').read_text(encoding='utf-8')
pub=(root/'pubspec.yaml').read_text(encoding='utf-8')

assert 'version: 3.29.65+207' in pub
assert 'read_pdf_text: ^0.3.1' in pub
assert "package:read_pdf_text/read_pdf_text.dart" in svc
assert 'ReadPdfText.getPDFtext(localPath)' in svc
assert 'const Duration(seconds: 20)' in svc
assert '_normalizeExtractedRhText' in svc
assert '_buildLightweightRhPdf' in svc
assert 'compress: true' in svc
assert 'base64Encode(uploadBytes)' in svc
assert '_postPdfImportDedicated' in svc
assert 'const Duration(seconds: 90)' in svc
assert 'AppsScriptHttp.postJson' not in svc
assert 'allowLongAndroidRequest: true' not in svc

print('RH_PDF_V32965_OK: extracao local + PDF leve + chamada isolada, sem transporte de sync.')

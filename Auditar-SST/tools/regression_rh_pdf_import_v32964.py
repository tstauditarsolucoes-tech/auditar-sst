#!/usr/bin/env python3
from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else 'app/Auditar_SST_v1_5_dashboard')
svc=(root/'lib/services/worker_import_service.dart').read_text(encoding='utf-8')
pub=(root/'pubspec.yaml').read_text(encoding='utf-8')

assert "'mode': 'employee_pdf_import'" in svc
assert '_postPdfImportDedicated' in svc
assert "import 'package:http/http.dart' as http;" in svc
assert "'Content-Type': 'application/json; charset=utf-8'" in svc
assert 'const Duration(seconds: 90)' in svc
assert 'foi cancelada' in svc
assert 'Nenhum trabalhador existente foi alterado' in svc
assert 'AppsScriptHttp.postJson' not in svc
assert 'allowLongAndroidRequest: true' not in svc
assert 'version: 3.29.64+206' in pub

print('RH_PDF_V32964_OK: cliente proprio + cancelamento 90 s; transporte de sync nao utilizado.')

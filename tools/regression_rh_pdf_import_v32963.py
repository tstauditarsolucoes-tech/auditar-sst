#!/usr/bin/env python3
from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else 'app/Auditar_SST_v1_5_dashboard')
svc=(root/'lib/services/worker_import_service.dart').read_text(encoding='utf-8')
pub=(root/'pubspec.yaml').read_text(encoding='utf-8')

assert "'mode': 'employee_pdf_import'" in svc
assert "timeout: const Duration(seconds: 180)" in svc
assert "allowLongAndroidRequest: true" in svc
assert "CentralTransportException" in svc
assert "Nenhum trabalhador existente foi alterado" in svc
assert "version: 3.29.63+205" in pub

# A correção precisa estar dentro da chamada do importador RH, não no transporte global.
mode_pos=svc.index("'mode': 'employee_pdf_import'")
long_pos=svc.index('allowLongAndroidRequest: true')
assert mode_pos < long_pos < mode_pos + 1800

print('RH_PDF_IMPORT_REGRESSION_OK: chamada longa somente no importador RH; timeout 180 s preservado.')

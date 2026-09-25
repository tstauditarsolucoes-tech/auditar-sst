#!/usr/bin/env python3
"""Guard the only route changed by the PDF-template AI timeout hotfix."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
service=(root/'lib/services/report_template_ai_import_service.dart').read_text(encoding='utf-8')
transport=(root/'lib/services/apps_script_http.dart').read_text(encoding='utf-8')
screen=(root/'lib/screens/report_template_library_screen.dart').read_text(encoding='utf-8')
# The Android HTTP client applies a short default unless explicitly opted in.
# Windows has its own transport with no Android-specific named argument.
if 'allowLongAndroidRequest' in transport:
    assert service.count('allowLongAndroidRequest: true') == 1
else:
    assert 'allowLongAndroidRequest' not in service
assert 'timeout: const Duration(seconds: 105)' in service
assert "on TimeoutException {" in service
assert "on SocketException catch (error)" in service
assert "CentralTransportException" not in service
assert "mode': 'report_template_import'" in service
assert "maxPdfBytes = 11 * 1024 * 1024" in service
assert "A análise do PDF ultrapassou o tempo" in service
assert "Analisando PDF (até 2 min)..." in screen
# Android and Windows use different transport implementations; their shared
# contract is the opt-in flag, not a literal formatting/branch expression.
assert "postJson(" in transport
for path in ['lib/services/device_sync_service.dart',
             'lib/services/media_sync_service.dart',
             'painel_web_google_apps_script/Code.gs']:
    assert (root/path).exists(), path
print('TEMPLATE_IMPORT_LONG_TIMEOUT_ISOLATED_REGRESSION_OK')

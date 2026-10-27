#!/usr/bin/env python3
"""Windows-only API compatibility: existing AppsScriptHttp.postJson has no Android-only flag."""
from pathlib import Path
import hashlib
import sys
root=Path(sys.argv[1])
target=root/'lib/screens/paper_attendance_screen.dart'
protected=[
'lib/database.dart','lib/services/device_sync_service.dart',
'lib/services/sync_coordinator.dart','lib/services/media_sync_service.dart',
'lib/services/drive_service.dart','lib/services/apps_script_http.dart',
'lib/services/ai_assistant_service.dart',
'painel_web_google_apps_script/Code.gs',
'painel_web_google_apps_script/MultiUser.gs',
'painel_web_google_apps_script/ClientPortal.gs',
]
before={x:hashlib.sha256((root/x).read_bytes()).hexdigest() for x in protected}
source=target.read_text(encoding='utf-8')
old='        allowLongAndroidRequest: true,\n'
if source.count(old)!=1: raise SystemExit('PAPER_AI_WINDOWS_HTTP_COMPAT expected exactly one Android-only flag')
target.write_text(source.replace(old,'',1),encoding='utf-8',newline='\n')
changed=[x for x,h in before.items() if hashlib.sha256((root/x).read_bytes()).hexdigest()!=h]
if changed: raise SystemExit('PROTECTED SYNC MEDIA DB GS AI CHANGED: '+repr(changed))
print('PAPER_AI_WINDOWS_HTTP_COMPAT_OK')

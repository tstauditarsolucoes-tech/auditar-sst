#!/usr/bin/env python3
"""UI-only upgrade of paper attendance reader. Never edit sync, GS, DB or AI service."""
from pathlib import Path
import hashlib
import shutil
import sys

root = Path(sys.argv[1])
source = Path(__file__).resolve().parents[1] / 'feature_sources/paper_attendance_screen_v329127.dart'
target = root / 'lib/screens/paper_attendance_screen.dart'
protected = [
    'lib/database.dart',
    'lib/services/device_sync_service.dart',
    'lib/services/sync_coordinator.dart',
    'lib/services/media_sync_service.dart',
    'lib/services/drive_service.dart',
    'lib/services/apps_script_http.dart',
    'lib/services/ai_assistant_service.dart',
    'painel_web_google_apps_script/Code.gs',
    'painel_web_google_apps_script/MultiUser.gs',
    'painel_web_google_apps_script/ClientPortal.gs',
]
before = {name: hashlib.sha256((root/name).read_bytes()).hexdigest()
          for name in protected}
current = target.read_text(encoding='utf-8')
if 'class PaperAttendanceScreen' not in current or '_readNamesWithAi' in current:
    raise SystemExit('Unexpected paper attendance screen version; no files changed')
shutil.copyfile(source, target)
changed = [name for name, digest in before.items()
           if hashlib.sha256((root/name).read_bytes()).hexdigest() != digest]
if changed:
    raise SystemExit('SYNC/MEDIA/DB/GS/AI MODIFIED: ' + repr(changed))
print('PAPER_AI_ISOLATED_OK')
print('SYNC_MEDIA_GS_DB_AI_BYTE_IDENTICAL_OK')

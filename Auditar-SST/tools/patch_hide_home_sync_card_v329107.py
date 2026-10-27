#!/usr/bin/env python3
"""Remove the diagnostic sync/evidence card from Home without changing sync."""
from pathlib import Path
import re
import sys

if len(sys.argv) != 3 or sys.argv[2] not in ('android', 'windows'):
    raise SystemExit('Usage: patch_hide_home_sync_card_v329107.py APP_DIR android|windows')

root = Path(sys.argv[1])
platform = sys.argv[2]
home = root / 'lib/screens/home_screen.dart'
pubspec = root / 'pubspec.yaml'
original = home.read_text(encoding='utf-8')

anchors = (
    ('android Home', '          _syncQueueCard(),\n          const SizedBox(height: 12),\n'),
    ('Windows Home', '                  _syncQueueCard(),\n                  const SizedBox(height: 14),\n'),
)
updated = original
for label, marker in anchors:
    count = updated.count(marker)
    if count != 1:
        raise RuntimeError(f'{label}: expected exactly one visible card, found {count}')
    updated = updated.replace(marker, '', 1)

# Preserve the existing sync and evidence machinery: this patch only removes
# the two render call-sites. No transport, database, storage or media changes.
assert updated.count('_syncQueueCard()') == 1, 'The card must no longer be rendered'
assert '_refreshSyncStatus()' in updated and '_retryEvidenceUpload()' in updated
assert 'DeviceSyncService.events.listen' in updated
home.write_text(updated, encoding='utf-8', newline='\n')

old, new = {
    'android': ('3.29.106+248', '3.29.107+249'),
    'windows': ('3.30.30+217', '3.30.31+218'),
}[platform]
version = pubspec.read_text(encoding='utf-8')
match = re.findall(r'(?m)^version:\s*([^\r\n]+)', version)
if len(match) != 1 or match[0].strip() != old:
    raise RuntimeError(f'Unexpected app version: {match}')
pubspec.write_text(version.replace('version: ' + old, 'version: ' + new, 1),
                   encoding='utf-8', newline='\n')
print('HOME_SYNC_CARD_HIDDEN_OK', platform, new)
print('SYNC_MEDIA_TRANSPORT_UNTOUCHED_OK')

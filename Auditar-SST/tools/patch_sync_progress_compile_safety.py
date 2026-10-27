#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
screen = root / 'lib/screens/data_safety_screen.dart'
text = screen.read_text(encoding='utf-8')

text = text.replace(
    'syncPercent = shownPercent.clamp(0, 100);',
    'syncPercent = shownPercent.clamp(0, 100).toInt();',
)
text = text.replace(
    'final value = syncPercent.clamp(0, 100) / 100.0;',
    'final value = syncPercent.clamp(0, 100).toDouble() / 100.0;',
)

# Use media APIs shared by Android and Windows so the unified screen compiles
# on both platforms and no platform-specific helper can block the build.
old = '''        try {
          await MediaSyncService.syncBackgroundBatch(
            uploadLimit: 5,
            downloadLimit: 8,
          ).timeout(const Duration(seconds: 50));
        } catch (_) {}
'''
new = '''        try {
          await MediaSyncService.uploadPending()
              .timeout(const Duration(seconds: 30));
          await MediaSyncService.downloadMissing()
              .timeout(const Duration(seconds: 30));
        } catch (_) {}
'''
text = text.replace(old, new)

screen.write_text(text, encoding='utf-8', newline='\n')
assert 'shownPercent.clamp(0, 100).toInt()' in text
assert 'CircularProgressIndicator' not in text
assert 'Progresso da sincronização' in text
print('Compile-safety do progresso aplicada.')

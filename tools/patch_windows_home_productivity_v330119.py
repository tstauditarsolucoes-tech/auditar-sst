#!/usr/bin/env python3
"""Windows-only v3.30.119: show existing full executive Home on wide windows.

Runs AFTER v3.30.118 Windows desktop UX patch. No changes to Flutter
database, auth, sync, media, Android or production Apps Script sources.
"""
from pathlib import Path
import hashlib
import re
import sys

assert len(sys.argv) == 2, 'uso: patch_windows_home_productivity_v330119.py APP_DIR'
root = Path(sys.argv[1])
home_path = root / 'lib/screens/home_screen.dart'
pub_path = root / 'pubspec.yaml'
home = home_path.read_text(encoding='utf-8')
pub = pub_path.read_text(encoding='utf-8')

protected_names = [
    'lib/database.dart', 'lib/models.dart',
    'lib/services/device_sync_service.dart',
    'lib/services/apps_script_http.dart',
    'lib/services/sync_coordinator.dart',
    'lib/services/auth_service.dart',
    'lib/services/drive_service.dart',
    'lib/services/media_sync_service.dart',
    'lib/services/ai_assistant_service.dart',
    'painel_web_google_apps_script/Code.gs',
    'painel_web_google_apps_script/MultiUser.gs',
    'painel_web_google_apps_script/ClientPortal.gs',
    'painel_web_google_apps_script/ClientPortal.html',
    'painel_web_google_apps_script/ReportEmail.gs',
]
protected = {name: hashlib.sha256((root / name).read_bytes()).digest()
             for name in protected_names if (root / name).exists()}

# Full executive layout was only available under "Mais opções".
# Under 1000 logical pixels, preserve the existing two-column quick desktop.
old = 'Widget _desktopBody() => _quickBody(desktop: true);'
assert home.count(old) == 1, 'Unexpected main Home body'
assert home.count('Widget _completeDesktopBody() {') == 1, 'Executive Home absent'
replacement = """Widget _desktopBody() {
    final width = MediaQuery.sizeOf(context).width;
    if (width >= 1000) {
      return _completeDesktopBody();
    }
    return _quickBody(desktop: true);
  }"""
home = home.replace(old, replacement, 1)

def method_range(source, signature):
    start = source.find(signature)
    assert start >= 0, 'Missing method: ' + signature
    opening = source.find('{', start + len(signature) - 1)
    assert opening >= 0, 'Missing body: ' + signature
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == '{':
            depth += 1
        elif source[index] == '}':
            depth -= 1
            if depth == 0:
                return start, index + 1
    raise AssertionError('Unbalanced method: ' + signature)

# Previously skipped typography change now targets the REAL executive body.
start, end = method_range(home, 'Widget _completeDesktopBody() {')
body = home[start:end]
body, updated = re.subn(r'fontSize:\s*(?:10(?:\.5)?|11(?:\.5)?)(?![\d.])',
                        'fontSize: 12.5', body)
assert updated >= 4, 'Executive fonts were not upgraded'
home = home[:start] + body + home[end:]

# The sidebar section-title helper is outside the executive method.
start, end = method_range(home, 'Widget _desktopNavSectionTitle(String title) {')
section = home[start:end]
section, headings = re.subn(r'fontSize:\s*10\.5(?![\d.])',
                            'fontSize: 12.5', section)
assert headings == 1, 'Sidebar typography upgrade skipped'
home = home[:start] + section + home[end:]

assert pub.count('version: 3.30.118+305') == 1, 'Wrong Windows base version'
pub = pub.replace('version: 3.30.118+305', 'version: 3.30.119+306', 1)
assert home.count('Auditar SST para Windows • versão 3.30.118') == 1
home = home.replace('Auditar SST para Windows • versão 3.30.118',
                    'Auditar SST para Windows • versão 3.30.119', 1)
for name, digest in protected.items():
    assert hashlib.sha256((root / name).read_bytes()).digest() == digest, name
home_path.write_text(home, encoding='utf-8', newline='\n')
pub_path.write_text(pub, encoding='utf-8', newline='\n')
print(f'WINDOWS_HOME_330119_OK FONTS={updated} NAV_HEADINGS={headings}')
print('EXECUTIVE_1000_PLUS_COMPACT_760_TO_999_NO_PROTECTED_FILES_CHANGED')

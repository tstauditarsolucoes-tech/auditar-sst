#!/usr/bin/env python3
"""Accept the actual assembled Windows v3.30.119 Home, not source placeholders."""
from pathlib import Path
import re
import sys

assert len(sys.argv) == 2, 'uso: test_windows_home_productivity_v330119.py APP_DIR'
root = Path(sys.argv[1])
home = (root / 'lib/screens/home_screen.dart').read_text(encoding='utf-8')
pub = (root / 'pubspec.yaml').read_text(encoding='utf-8')
assert 'version: 3.30.119+306' in pub
assert 'Auditar SST para Windows • versão 3.30.119' in home
assert 'Widget _completeDesktopBody() {' in home
assert 'Widget _desktopBody() {' in home
main = home[home.index('Widget _desktopBody() {'):]
main = main[:main.index('\n  @override')]
assert 'width >= 1000' in main
assert 'return _completeDesktopBody();' in main
assert 'return _quickBody(desktop: true);' in main
assert 'Widget _mobileBody() => _quickBody(desktop: false);' in home
assert re.search(r'Platform\.isWindows\s*\?\s*width\s*>=\s*760', home)
assert 'Central Executiva' in home and 'Gestão Multempresa' in home
assert 'ClientTreatmentInboxScreen()' in home
assert 'VisitStartPanel(' in home and '_startVisit(' in home
assert 'Widget _desktopNavSectionTitle(String title) {' in home
nav = home[home.index('Widget _desktopNavSectionTitle(String title) {'):]
assert 'fontSize: 12.5' in nav[:500], 'Sidebar font upgrade was skipped'
exec_body = home[home.index('Widget _completeDesktopBody() {'):]
exec_body = exec_body[:exec_body.index('Widget _desktopNavSectionTitle(String title)')]
assert 'fontSize: 12.5' in exec_body
assert not re.search(r'fontSize:\s*(?:10(?:\.5)?|11(?:\.5)?)(?![\d.])',
                     exec_body), 'Small executive fonts survived'
print('WINDOWS_HOME_330119_REAL_DESKTOP_COMPACT_AND_FONTS_PASS')

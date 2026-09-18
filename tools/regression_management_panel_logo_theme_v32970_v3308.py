#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(sys.argv[1])
version=sys.argv[2]
pub=(root/'pubspec.yaml').read_text(encoding='utf-8')
screen=(root/'lib/screens/management_panel_screen.dart').read_text(encoding='utf-8')
assert f'version: {version}' in pub
for marker in [
    "import 'dart:ui' as ui;",
    "Future<void> _loadCompanyIdentity() async",
    "ui.instantiateImageCodec",
    "_companyLogoWidget()",
    "colors: [_companyHeaderColor, _companyHeaderDark]",
    "data: _companyPanelTheme(context)",
    "'identidade da empresa'",
    "companyAccent",
    "companyAccentDark",
]:
    assert marker in screen, marker
print('MANAGEMENT_PANEL_LOGO_THEME_REGRESSION_OK', version)

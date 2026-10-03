#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(sys.argv[1]);version=sys.argv[2]
read=lambda p:(root/p).read_text(encoding='utf-8')
assert 'version: '+version in read('pubspec.yaml')
media=read('lib/services/media_sync_service.dart')
companies=read('lib/screens/companies_screen.dart')
assert 'final cachedPath' in media
assert 'await _applyEntityPath(db, asset, cachedPath);' in media
assert 'if (downloaded)' in media
assert '_restoringMissingLogos' in companies
assert 'recuperada(s) do aparelho ou do backup' in companies
# Android and Windows use different upload-success flags. Both must preserve
# the previous cached logo when upload or sync fails.
if version.startswith('3.30.'):
    assert 'if (onlineReady && old != null' in companies
else:
    assert 'if (synced && old != null' in companies or 'if(synced && old!=null' in companies
assert 'errorBuilder:' in companies
assert 'ExpandTextButton' in read('lib/widgets/expand_text_button.dart')
assert 'initialText: original.text' in read('lib/widgets/expand_text_button.dart')
assert 'if (edited == null) return;' in read('lib/widgets/expand_text_button.dart')
assert 'draft.dispose();' in read('lib/widgets/expand_text_button.dart')
required = {
 'checklist_screen.dart': 12,
 'express_round_screen.dart': 8,
 'sst_record_form_screen.dart': 9,
 'safety_observations_screen.dart': 6,
 'improvements_screen.dart': 6,
}
for file,minimum in required.items():
 body=read('lib/screens/'+file)
 assert body.count('ExpandTextButton(controller:')>=minimum,(file,body.count('ExpandTextButton(controller:'))
 assert "import '../widgets/expand_text_button.dart';" in body
 print('TEXT_EXPAND_COVERAGE',file,body.count('ExpandTextButton(controller:'))
assert "static const standard2TemplateId = 'auditar_padrao_2';" in read('lib/services/report_template_service.dart')
print('LOGO_LOCAL_CACHE_RECOVERY_AND_ALL_INSPECTION_EDITORS_OK',version)

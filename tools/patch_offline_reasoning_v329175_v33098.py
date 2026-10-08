#!/usr/bin/env python3
"""Add deterministic suggestion review without changing existing services/storage."""
from pathlib import Path
import hashlib
import re
import shutil
import sys
root = Path(sys.argv[1])
platform = sys.argv[2]
assert platform in ('android', 'windows')
repo = Path(__file__).resolve().parents[1]
widget = root / 'lib/widgets/offline_report_inline_suggestions.dart'
service = root / 'lib/services/offline_reasoning.dart'
assert widget.exists() and not service.exists(), 'Unexpected offline baseline'
screens = [root / 'lib/screens/safety_observations_screen.dart', root / 'lib/screens/express_round_screen.dart']
protected = [p for folder in ('lib', 'painel_web_google_apps_script')
             for p in (root / folder).rglob('*') if p.is_file() and p != widget and p not in screens]
before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
for source, target in [
    ('offline_reasoning_v329175.dart', service),
    ('offline_report_inline_suggestions_v329175.dart', widget),
    ('offline_reasoning_test_v329175.dart', root / 'test/offline_reasoning_test.dart'),
]:
    shutil.copyfile(repo / 'feature_sources' / source, target)
# Explicit review must override previous field values in both integrations.
p = screens[0]
s = p.read_text(encoding='utf-8')
start = s.index('return OfflineReportInlineSuggestions(')
end = re.search(r'unawaited\(\s*OfflineReportKnowledgeService\.markUsed\(selected\.id\)', s[start:]).start() + start
block = s[start:end]
block, count = re.subn(r'controller\.text\.trim\(\)\.isEmpty\s*&&\s*text\.trim\(\)\.isNotEmpty',
                      '(selected.reviewed || (controller.text.trim().isEmpty && text.trim().isNotEmpty))', block)
assert count == 1, 'Vistoria field integration changed'
assert block.count("priority == 'Média'") == 1
block = block.replace("priority == 'Média'", "selected.reviewed || priority == 'Média'")
s = s[:start] + block + s[end:]
p.write_text(s, encoding='utf-8', newline='\n')
p = screens[1]
s = p.read_text(encoding='utf-8')
start = s.index('void _applyOfflineRoundSuggestion(')
end = s.index('void _clearOfflineRoundModel()', start)
block = s[start:end]
assert block.count('setState(() {') == 1
block = block.replace('setState(() {', 'setState(() {\n      if (selected.reviewed) { aiTitle = ""; aiRisk = ""; aiConsequence = ""; aiRecommendation = ""; }', 1)
assert block.count("priority == 'Média'") == 1
block = block.replace("priority == 'Média'", "(selected.reviewed || priority == 'Média')")
s = s[:start] + block + s[end:]
p.write_text(s, encoding='utf-8', newline='\n')
p = root / 'pubspec.yaml'
s = p.read_text(encoding='utf-8')
old, new = ('3.29.174+316', '3.29.175+317') if platform == 'android' else ('3.30.97+284', '3.30.98+285')
assert s.count('version: ' + old) == 1
p.write_text(s.replace('version: ' + old, 'version: ' + new), encoding='utf-8', newline='\n')
for path, digest in before.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, str(path)
print('OFFLINE_REASONING_READY; ALL_EXISTING_SERVICES_DATABASE_MODELS_OTHER_SCREENS_CENTRAL_BYTE_IDENTICAL', platform)

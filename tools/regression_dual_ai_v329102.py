#!/usr/bin/env python3
"""Strict checks: text AI never uploads photos; both routes remain available."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
version=sys.argv[2]
ai=(root/'lib/services/ai_assistant_service.dart').read_text(encoding='utf-8')
start=ai.index('  static Future<AiAssistantReply> improveInspectionText({')
end=ai.index('  static Future<AiAssistantReply> analyzeChecklistPhotos({',start)
text_method=ai[start:end]
assert "'mode': 'report_review_chat'" in text_method
assert "'images':" not in text_method
assert 'base64Encode(' not in text_method
assert 'File(' not in text_method
assert 'originalText' in text_method
assert 'result' in text_method
for rel in ['checklist_screen.dart','express_round_screen.dart','safety_observations_screen.dart']:
    s=(root/'lib/screens'/rel).read_text(encoding='utf-8')
    assert '_improveTextWithAi' in s, rel
    assert '_analyzeWithAi' in s, rel
    assert 'IA texto' in s and 'IA foto' in s, rel
    assert 'InspectionTextAiReview.show' in s, rel
assert "'aiText':" in (root/'lib/screens/checklist_screen.dart').read_text(encoding='utf-8')
assert "'aiTextOriginal':" in (root/'lib/screens/express_round_screen.dart').read_text(encoding='utf-8')
assert "'aiTextOriginal':" in (root/'lib/screens/safety_observations_screen.dart').read_text(encoding='utf-8')
assert (root/'lib/widgets/inspection_text_ai_review.dart').is_file()
assert f'version: {version}' in (root/'pubspec.yaml').read_text(encoding='utf-8')
print('DUAL_AI_ALL_INSPECTIONS_REGRESSION_OK',version)

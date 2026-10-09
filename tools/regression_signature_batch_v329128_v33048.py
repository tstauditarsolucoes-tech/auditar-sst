#!/usr/bin/env python3
"""Sequence uses existing signature evidence; verifies no auto-confirmation."""
from pathlib import Path
import re,sys
root=Path(sys.argv[1])
dds=(root/'lib/screens/sst_record_form_screen.dart').read_text(encoding='utf-8')
train=(root/'lib/screens/training_records_screen.dart').read_text(encoding='utf-8')
canvas=(root/'lib/widgets/large_signature_capture.dart').read_text(encoding='utf-8')
def has(body,pattern):return re.search(pattern,body,re.S) is not None
assert has(dds,r'Future<void>\s+_signDdsPendingInSequence\(\)')
assert has(dds,r'await\s+_collectDdsSignature\(\)')
assert has(dds,r'if\s*\(!after\.contains\(expected\)\)\s*break')
assert 'Assinar pendentes em sequência' in dds
assert 'Voltar ou cancelar interrompe a sequência.' in dds
assert 'participantIndex: position' in dds
assert has(train,r'Future<void>\s+_signPendingTrainingInSequence\(\)')
assert has(train,r'await\s+_sign\(current\)')
assert has(train,r"after\['status'\].*?ASSINADO|after\['status'\].*?\s*ASSINADO")
assert 'Assinar pendentes em sequência' in train
assert '_confirmReplaceTrainingConfirmation(' in train
assert 'registerDdsSignature(' in dds
assert 'registerTrainingRecordSignature(' in train
assert 'await _savePayload(payload: payload);' in train
assert 'auditar_large_signature_canvas' in canvas
assert 'ASSINANDO AGORA' in canvas
assert 'landscapeLeft' in canvas
assert dds.count('Future<void> _signDdsPendingInSequence()') == 1
assert train.count('Future<void> _signPendingTrainingInSequence()') == 1
print('SIGNATURE_BATCH_HUMAN_CONFIRMATION_REGRESSION_OK')

#!/usr/bin/env python3
"""Sequential signature guard: no false presence, no automatic overwrite."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
dds=(root/'lib/screens/sst_record_form_screen.dart').read_text(encoding='utf-8')
train=(root/'lib/screens/training_records_screen.dart').read_text(encoding='utf-8')
shared=(root/'lib/widgets/large_signature_capture.dart').read_text(encoding='utf-8')
checks={
 'dds':(dds,['Future<void> _signDdsPendingInSequence()','if (_ddsSignatureQueueRunning) return;',
   'await _collectDdsSignature();','if (!after.contains(expected)) break;',
   'Assinar pendentes em sequência','Voltar ou cancelar interrompe a sequência.',
   'participantIndex: position>=0 ? position+1 : null,']),
 'training':(train,['Future<void> _signPendingTrainingInSequence()',
   "'PENDENTE') continue;",'await _sign(current);',
   "!= 'ASSINADO') break;","_trainingSignatureQueueRunning ? null : _sign(participant)",
   'Assinar pendentes em sequência','_confirmReplaceTrainingConfirmation(']),
 'canvas':(shared,['auditar_large_signature_canvas','ASSINANDO AGORA',
    "DeviceOrientation.landscapeLeft","minHeight:54","widget.controller.isEmpty"]),
}
for area,(body,tokens) in checks.items():
 for token in tokens:
  assert token in body, 'BATCH_SIGN missing '+area+': '+token
assert dds.count('Future<void> _signDdsPendingInSequence()')==1
assert train.count('Future<void> _signPendingTrainingInSequence()')==1
assert "'status': 'ASSINADO'" in train and 'await _savePayload(payload: payload);' in train
assert 'registerDdsSignature(' in dds and 'registerTrainingRecordSignature(' in train
print('SIGNATURE_BATCH_HUMAN_CONFIRMATION_REGRESSION_OK')

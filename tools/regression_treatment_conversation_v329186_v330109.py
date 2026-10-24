#!/usr/bin/env python3
"""Guard message-local confirmation and on-screen queue regressions."""
from pathlib import Path
import sys

root = Path(sys.argv[1])
screen = (root / 'lib/screens/client_treatment_inbox_screen.dart').read_text(encoding='utf-8')
tests = (root / 'test/treatment_outbox_test.dart').read_text(encoding='utf-8')
assert "final queuedId=await treatmentOutbox.enqueue" in screen
assert "remaining.any((row)=>row['id']==queuedId)" in screen
assert 'await refreshLocalPending(); // Local messages remain visible' in screen
assert 'Guardadas neste aparelho' in screen
assert 'Revisão necessária na Caixa de entrada.' in screen
assert "confirmed message is identified by its ID" in tests
assert "client_treatment_v2" in screen
print('TRATATIVAS_CONVERSA_LOCAL_REGRESSION_OK')

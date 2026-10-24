#!/usr/bin/env python3
"""Human review and compatibility checks for paper attendance AI UI."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
screen=(root/'lib/screens/paper_attendance_screen.dart').read_text(encoding='utf-8')
required=[
    "'mode': 'training_record_import'",
    "'action': 'ai_assistant'",
    'AppsScriptHttp.postJson(',
    'AuthService.sessionToken',
    'Future<Uint8List> _pdfForAi(',
    'pw.MemoryImage(bytes)',
    'Future<void> _readNamesWithAi(',
    'Future<void> _reviewAiNames(',
    'Future<void> _confirmAiReview(',
    "'aiRecognizedNames': suggestedNames",
    "'reviewMethod': 'ai_with_human_confirmation'",
    "'participantIds': participantIds",
    'Confirmar participantes',
    'Nomes sem correspondência não serão lançados automaticamente.',
    "if (counts[name] == 1) selected.add(key);",
    "if (current == null || current.companyId != widget.companyId)",
    "current!.status.toUpperCase() == 'FINALIZADO'",
    "(person['status'] ?? '').toString() == 'ASSINADO'",
    "_readNamesWithAi(item)",
]
for token in required:
    assert token in screen, 'PAPER_AI missing: '+token
assert 'Future<void> _save(Uint8List bytes, String name)' in screen
assert 'Future<void> _open(Map<String, dynamic> item)' in screen
assert 'MediaSyncService.uploadPending' in screen, 'existing media upload call missing'
assert screen.count('Future<void> _readNamesWithAi(')==1
print('PAPER_AI_HUMAN_REVIEW_REGRESSION_OK')

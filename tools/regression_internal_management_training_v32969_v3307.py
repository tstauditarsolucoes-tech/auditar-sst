#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(sys.argv[1])
version=sys.argv[2]
pub=(root/'pubspec.yaml').read_text(encoding='utf-8')
screen=(root/'lib/screens/management_panel_screen.dart').read_text(encoding='utf-8')
assert f'version: {version}' in pub
for marker in [
    "type: 'TREINAMENTO_SESSAO'",
    'Treinamentos realizados',
    'Fotos, participantes, assinaturas e ficha do treinamento.',
    'TrainingRecordDetailScreen(',
    'TrainingRecordsScreen(',
    "'Realizados'",
    "'Finalizados'",
    "'Fotos'",
    "'Assinaturas'",
    "'Ver todos'",
]:
    assert marker in screen, marker
print('INTERNAL_MANAGEMENT_TRAINING_REGRESSION_OK', version)

#!/usr/bin/env python3
from pathlib import Path
import sys

root=Path(sys.argv[1])
version=sys.argv[2]
pub=(root/'pubspec.yaml').read_text(encoding='utf-8')
train=(root/'lib/screens/trainings_screen.dart').read_text(encoding='utf-8')
records=(root/'lib/screens/training_records_screen.dart').read_text(encoding='utf-8')
pdf=(root/'lib/services/training_record_pdf_service.dart').read_text(encoding='utf-8')
media=(root/'lib/services/media_sync_service.dart').read_text(encoding='utf-8')

assert f'version: {version}' in pub
for marker in [
    "title: 'Fotos e fichas'",
    'TrainingRecordsScreen(',
]:
    assert marker in train, marker
for marker in [
    "const _trainingRecordType = 'TREINAMENTO_SESSAO';",
    'Fotos do treinamento',
    'Participantes e assinaturas',
    'Visualizar / imprimir ficha de assinaturas',
    'TrainingRecordSignatureScreen',
    'registerTrainingRecordPhoto',
    'registerTrainingRecordSignature',
    'upsertTrainingControlsBatch',
    "status: 'FINALIZADO'",
]:
    assert marker in records, marker
for marker in [
    'FICHA DE REGISTRO DE TREINAMENTO',
    'LISTA DE PRESENÇA E ASSINATURAS',
    'REGISTRO FOTOGRÁFICO',
]:
    assert marker in pdf, marker
for marker in [
    'registerTrainingRecordPhoto({',
    'registerTrainingRecordSignature({',
    'trainingRecordMediaLocalPath({',
    'restoreTrainingRecordMedia({',
    "entityType: 'training_record_photo'",
    "entityType: 'training_record_signature'",
]:
    assert marker in media, marker
print('TRAINING_RECORDS_REGRESSION_OK', version)

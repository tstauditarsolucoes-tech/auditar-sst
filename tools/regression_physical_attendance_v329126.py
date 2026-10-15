#!/usr/bin/env python3
from pathlib import Path
import hashlib
import sys

root=Path(sys.argv[1])
dds=(root/'lib/screens/sst_records_screen.dart').read_text(encoding='utf-8')
train=(root/'lib/screens/training_records_screen.dart').read_text(encoding='utf-8')
pdf=(root/'lib/services/training_record_pdf_service.dart').read_text(encoding='utf-8')
widget=(root/'lib/widgets/physical_attendance_sheet.dart').read_text(encoding='utf-8')

for token in [
    'PhysicalAttendanceSheetScreen',
    "entityType: 'dds_attendance_sheet'",
    'dds_physical_attendance_ids',
    'Anexar ficha assinada em papel',
]:
    assert token in dds, token

for token in [
    "entityType: 'training_attendance_sheet'",
    'physicalAttendanceSheetIds',
    'Confirmar pela ficha física',
    "participantStatus != 'FICHA_FISICA'",
    "_count('ASSINADO') + _count('FICHA_FISICA')",
]:
    assert token in train, token

for token in [
    'physicalSheetCount',
    "status == 'FICHA_FISICA'",
    'FICHA FÍSICA',
]:
    assert token in pdf, token

for token in [
    'Importar PDF',
    'Tirar foto',
    'Galeria',
    'Backup confirmado',
    'MediaSyncService.uploadPending',
    'trainingRecordMediaLocalPath',
    "'media_assets'",
]:
    assert token in widget, token

for forbidden in [
    'class MediaSyncService',
    'class DeviceSyncService',
    'CREATE TABLE',
    'ALTER TABLE',
]:
    assert forbidden not in widget, forbidden

print('PHYSICAL_ATTENDANCE_REGRESSION_OK')

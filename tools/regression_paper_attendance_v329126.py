#!/usr/bin/env python3
"""Isolated paper proof regression. No synchronization/schema/GS code modifications."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
evidence=(root/'lib/screens/paper_attendance_screen.dart').read_text(encoding='utf-8')
dds=(root/'lib/screens/sst_records_screen.dart').read_text(encoding='utf-8')
form=(root/'lib/screens/sst_record_form_screen.dart').read_text(encoding='utf-8')
train=(root/'lib/screens/training_records_screen.dart').read_text(encoding='utf-8')
pdf=(root/'lib/services/training_record_pdf_service.dart').read_text(encoding='utf-8')
checks={
'evidence':(evidence,[
 'paper_dds_attendance','paper_training_attendance','media_assets',
 "'mime_type': mime", "'drive_file_id': ''",
 'ConflictAlgorithm.abort','getApplicationDocumentsDirectory()',
 "['pdf', 'jpg', 'jpeg', 'png']",'source: ImageSource.camera',
 'paper_attendance','FICHA_FISICA','trainingRecordMediaLocalPath',
 'Backup pendente de confirmação','Backup confirmado',
]),
'dds':(dds,["PaperAttendanceScreen(","recordType: 'DDS'","Ficha assinada em papel"]),
'dds edit':(form,["'paper_attendance': widget.record?.payload['paper_attendance']"]),
'training':(train,["PaperAttendanceScreen(","recordType: 'TREINAMENTO_SESSAO'",
 "'FICHA_FISICA'","Ficha de presença assinada em papel"]),
'pdf':(pdf,["'FICHA_FISICA'","VER FICHA ANEXADA","presença(s) em ficha física"]),
}
for context,(source,tokens) in checks.items():
 for token in tokens:
  assert token in source, 'PAPER_ATTENDANCE missing '+context+': '+token
assert "'status': 'ASSINADO'" not in evidence, 'Never forge a digital signature.'
print('PAPER_ATTENDANCE_REGRESSION_OK')

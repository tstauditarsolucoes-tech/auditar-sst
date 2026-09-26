#!/usr/bin/env python3
"""Original paper attendance workflow. Never patch synchronization, media, DB, GS or AI."""
from pathlib import Path
import hashlib, shutil, sys

root=Path(sys.argv[1])
src=Path(__file__).resolve().parents[1]/'feature_sources/paper_attendance_screen_v329126.dart'
out=root/'lib/screens/paper_attendance_screen.dart'
dds=root/'lib/screens/sst_records_screen.dart'
form=root/'lib/screens/sst_record_form_screen.dart'
train=root/'lib/screens/training_records_screen.dart'
pdf=root/'lib/services/training_record_pdf_service.dart'
protected=[
 'lib/database.dart','lib/services/device_sync_service.dart',
 'lib/services/sync_coordinator.dart','lib/services/media_sync_service.dart',
 'lib/services/drive_service.dart','lib/services/apps_script_http.dart',
 'lib/services/ai_assistant_service.dart',
 'painel_web_google_apps_script/Code.gs',
 'painel_web_google_apps_script/MultiUser.gs',
 'painel_web_google_apps_script/ClientPortal.gs',
]
baseline={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in protected}
def edit(path,old,new,label):
    s=path.read_text(encoding='utf-8')
    if s.count(old)!=1:
        raise RuntimeError(label+' expected once: '+str(s.count(old)))
    path.write_text(s.replace(old,new,1),encoding='utf-8',newline='\n')

shutil.copyfile(src,out)
edit(dds,"import 'sst_record_form_screen.dart';",
 "import 'sst_record_form_screen.dart';\nimport 'paper_attendance_screen.dart';",'dds import')
edit(dds,'  Future<void> _generateDdsPdf(SstRecord record) async {',
 """  Future<void> _paperSheet(SstRecord record) async {
    await Navigator.of(context).push(MaterialPageRoute<void>(
      builder: (_) => PaperAttendanceScreen(
        companyId: record.companyId,
        recordId: record.id,
        recordType: 'DDS',
      ),
    ));
    await _load();
  }

  Future<void> _generateDdsPdf(SstRecord record) async {""",'dds navigation')
edit(dds,"                  if (value == 'pdf') _generateDdsPdf(record);",
 "                  if (value == 'pdf') _generateDdsPdf(record);\n"
 "                  if (value == 'paper') _paperSheet(record);",'dds menu callback')
edit(dds,
 "                      if (record.type == 'DDS')\n"
 "                        const PopupMenuItem(\n"
 "                          value: 'pdf',",
 "                      if (record.type == 'DDS')\n"
 "                        const PopupMenuItem(\n"
 "                          value: 'paper',\n"
 "                          child: Text('Ficha assinada em papel'),\n"
 "                        ),\n"
 "                      if (record.type == 'DDS')\n"
 "                        const PopupMenuItem(\n"
 "                          value: 'pdf',",'dds menu item')
edit(dds,
 "                      const SizedBox(height: 10),\n"
 "                      SizedBox(\n"
 "                        width: double.infinity,\n"
 "                        child: OutlinedButton.icon(\n"
 "                          onPressed: () => _generateDdsPdf(record),",
 "                      const SizedBox(height: 10),\n"
 "                      SizedBox(\n"
 "                        width: double.infinity,\n"
 "                        child: FilledButton.tonalIcon(\n"
 "                          onPressed: () => _paperSheet(record),\n"
 "                          icon: const Icon(Icons.upload_file_outlined),\n"
 "                          label: const Text('Ficha assinada em papel'),\n"
 "                        ),\n"
 "                      ),\n"
 "                      const SizedBox(height: 10),\n"
 "                      SizedBox(\n"
 "                        width: double.infinity,\n"
 "                        child: OutlinedButton.icon(\n"
 "                          onPressed: () => _generateDdsPdf(record),",
 'dds prominent entry')
edit(form,
 "      if (widget.type == 'DDS') 'dds_signatures': ddsSignatures,",
 "      if (widget.type == 'DDS') 'dds_signatures': ddsSignatures,\n"
 "      if (widget.type == 'DDS')\n"
 "        'paper_attendance': widget.record?.payload['paper_attendance'] ?? const [],",
 'preserve evidence after DDS edit')
edit(train,"import 'pre_admission_dialogs.dart';",
 "import 'pre_admission_dialogs.dart';\nimport 'paper_attendance_screen.dart';",
 'training import')
edit(train,'  Future<void> _choosePhotoSource() async {',
 """  Future<void> _paperSheet() async {
    final current = record;
    if (current == null || busy) return;
    await Navigator.of(context).push(MaterialPageRoute<void>(
      builder: (_) => PaperAttendanceScreen(
        companyId: widget.company.id,
        recordId: current.id,
        recordType: 'TREINAMENTO_SESSAO',
      ),
    ));
    await _load();
  }

  Future<void> _choosePhotoSource() async {""",'training navigation')
edit(train,
 "    final signed = _count('ASSINADO');\n    final pending = _count('PENDENTE');",
 "    final signed = _count('ASSINADO');\n"
 "    final paper = _count('FICHA_FISICA');\n"
 "    final pending = _count('PENDENTE');",'training count')
edit(train,
 "            const SizedBox(height: 16),\n"
 "            Row(\n"
 "              children: [\n"
 "                const Expanded(\n"
 "                  child: Text(\n"
 "                    'Fotos do treinamento',",
 "            const SizedBox(height: 16),\n"
 "            SizedBox(width: double.infinity, child: FilledButton.tonalIcon(\n"
 "              onPressed: busy ? null : _paperSheet,\n"
 "              icon: const Icon(Icons.upload_file_outlined),\n"
 "              label: const Text('Ficha de presença assinada em papel'),\n"
 "            )),\n"
 "            const SizedBox(height: 6),\n"
 "            Text('Presenças por ficha física: ' + paper.toString()),\n"
 "            const SizedBox(height: 16),\n"
 "            Row(\n"
 "              children: [\n"
 "                const Expanded(\n"
 "                  child: Text(\n"
 "                    'Fotos do treinamento',",'training prominent entry')
edit(train,
 "status == 'ASSINADO'\n                      ? AuditarBrand.greenDark",
 "status == 'ASSINADO' || status == 'FICHA_FISICA'\n"
 "                      ? AuditarBrand.greenDark",'paper color')
edit(train,
 "                          status == 'ASSINADO'\n                              ? (confirmationMethod == 'face'",
 "                          status == 'FICHA_FISICA'\n"
 "                              ? Icons.description_outlined\n"
 "                              : status == 'ASSINADO'\n"
 "                              ? (confirmationMethod == 'face'",'paper icon')
edit(train,
 "                          if (status == 'ASSINADO')\n                            confirmationMethod == 'face'",
 "                          if (status == 'FICHA_FISICA') 'FICHA EM PAPEL',\n"
 "                          if (status == 'ASSINADO')\n                            confirmationMethod == 'face'",'paper label')
edit(train,
 "                                status == 'ASSINADO'\n                                    ? Icons.verified_outlined",
 "                                status == 'ASSINADO' || status == 'FICHA_FISICA'\n"
 "                                    ? Icons.verified_outlined",'paper badge')
D=chr(36)
expr="'"+D+"{participant['status'] ?? ''}'"
edit(train,
 "        if ("+expr+" != 'ASSINADO') continue;",
 "        if ("+expr+" != 'ASSINADO' &&\n"
 "            "+expr+" != 'FICHA_FISICA') continue;",'register training control')
edit(train,
 "            notes: 'Ficha assinada no Auditar SST • sessão "+D+"{current.id}',",
 "            notes: "+expr+" == 'FICHA_FISICA'\n"
 "                ? 'Presença comprovada por ficha física • sessão "+D+"{current.id}'\n"
 "                : 'Ficha assinada no Auditar SST • sessão "+D+"{current.id}',",
 'training notes')
edit(pdf,"    final participantRows = <pw.TableRow>[",
 "    final paper = participants.where((item) =>\n"
 "        (item['status'] ?? '').toString() == 'FICHA_FISICA').length;\n"
 "    final participantRows = <pw.TableRow>[",'pdf counts')
edit(pdf,"                        status == 'AUSENTE' ? 'AUSENTE' : '',",
 "                        status == 'AUSENTE' ? 'AUSENTE' :\n"
 "                            status == 'FICHA_FISICA' ? 'VER FICHA ANEXADA' : '',",
 'pdf reference to original')
edit(pdf,"                  'Auditar SST • $signed confirmação(ões) eletrônica(s)',",
 "                  'Auditar SST • $signed confirmação(ões) eletrônica(s) • $paper presença(s) em ficha física',",
 'pdf counts separated')
changed=[p for p,h in baseline.items()
         if hashlib.sha256((root/p).read_bytes()).hexdigest()!=h]
if changed: raise SystemExit('PROTECTED SYNC MEDIA DB GS AI CHANGED: '+repr(changed))
print('PAPER_ATTENDANCE_ISOLATED_OK')

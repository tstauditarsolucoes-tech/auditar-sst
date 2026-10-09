#!/usr/bin/env python3
"""Adds paper attendance sheets to existing DDS/training records.
This patch may use the existing media queue, but it MUST NOT modify sync/media
implementation, database schema, GS transport, auth, Drive or AI.
"""
from pathlib import Path
import hashlib
import shutil
import sys

root=Path(sys.argv[1])
repo_root=Path(__file__).resolve().parents[1]

protected_paths=[
    'lib/database.dart',
    'lib/services/device_sync_service.dart',
    'lib/services/sync_coordinator.dart',
    'lib/services/media_sync_service.dart',
    'lib/services/drive_service.dart',
    'lib/services/apps_script_http.dart',
    'lib/services/ai_assistant_service.dart',
    'painel_web_google_apps_script/Code.gs',
    'painel_web_google_apps_script/MultiUser.gs',
    'painel_web_google_apps_script/ClientPortal.gs',
]
baseline={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in protected_paths}

src=repo_root/'feature_sources/physical_attendance_sheet_v329126.dart'
dst=root/'lib/widgets/physical_attendance_sheet.dart'
dst.parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(src,dst)

def read(rel):
    return (root/rel).read_text(encoding='utf-8')

def write(rel,s):
    (root/rel).write_text(s,encoding='utf-8',newline='\n')

def once(s,old,new,label):
    if new in s:
        return s
    count=s.count(old)
    if count!=1:
        raise RuntimeError(f'PHYSICAL_ATTENDANCE {label}: expected once, got {count}')
    return s.replace(old,new,1)

# DDS: manage paper sheets from the permanent DDS history.
dds_path='lib/screens/sst_records_screen.dart'
dds=read(dds_path)
dds=once(
    dds,
    "import '../services/dds_pdf_service.dart';\n",
    "import '../services/dds_pdf_service.dart';\nimport '../widgets/physical_attendance_sheet.dart';\n",
    'DDS import',
)

dds_methods=r'''  List<String> _ddsPhysicalSheetIds(SstRecord record) {
    final raw = record.payload['dds_physical_attendance_ids'];
    if (raw is! List) return <String>[];
    return raw.map((value) => '$value'.trim()).where((value) => value.isNotEmpty).toList();
  }

  Future<void> _openDdsPhysicalSheet(SstRecord record) async {
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => PhysicalAttendanceSheetScreen(
          companyId: record.companyId,
          entityType: 'dds_attendance_sheet',
          title: 'Ficha assinada • DDS',
          initialIds: _ddsPhysicalSheetIds(record),
          onChanged: (ids) async {
            final payload = Map<String, dynamic>.from(record.payload)
              ..['dds_physical_attendance_ids'] = ids
              ..['dds_attendance_method'] = ids.isEmpty ? '' : 'FICHA_FISICA';
            await AppDatabase.instance.upsertSstRecord(
              SstRecord(
                id: record.id,
                companyId: record.companyId,
                sectorId: record.sectorId,
                type: record.type,
                title: record.title,
                date: record.date,
                dueDate: record.dueDate,
                status: record.status,
                priority: record.priority,
                payload: payload,
              ),
            );
          },
        ),
      ),
    );
    await _load();
  }

'''
if '_openDdsPhysicalSheet(SstRecord record)' not in dds:
    marker='  Widget _card(SstRecord record) {\n'
    if dds.count(marker)!=1:
        raise RuntimeError('PHYSICAL_ATTENDANCE DDS method marker')
    dds=dds.replace(marker,dds_methods+marker,1)

dds=once(
    dds,
r'''                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon(
                          onPressed: () => _generateDdsPdf(record),
                          icon: const Icon(Icons.picture_as_pdf_outlined, size: 18),
                          label: const Text('Retirar ficha do DDS'),
                        ),
                      ),
''',
r'''                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon(
                          onPressed: () => _generateDdsPdf(record),
                          icon: const Icon(Icons.picture_as_pdf_outlined, size: 18),
                          label: const Text('Retirar ficha do DDS'),
                        ),
                      ),
                      const SizedBox(height: 7),
                      SizedBox(
                        width: double.infinity,
                        child: FilledButton.tonalIcon(
                          onPressed: () => _openDdsPhysicalSheet(record),
                          icon: const Icon(Icons.fact_check_outlined, size: 18),
                          label: Text(
                            _ddsPhysicalSheetIds(record).isEmpty
                                ? 'Anexar ficha assinada em papel'
                                : 'Ficha física anexada (${_ddsPhysicalSheetIds(record).length})',
                          ),
                        ),
                      ),
''',
    'DDS paper button',
)
dds=once(
    dds,
r'''                  if (value == 'edit') _edit(record);
                  if (value == 'pdf') _generateDdsPdf(record);
                  if (value == 'delete') _delete(record);
''',
r'''                  if (value == 'edit') _edit(record);
                  if (value == 'pdf') _generateDdsPdf(record);
                  if (value == 'paper') _openDdsPhysicalSheet(record);
                  if (value == 'delete') _delete(record);
''',
    'DDS menu action',
)
dds=once(
    dds,
r'''                  if (record.type == 'DDS')
                    const PopupMenuItem(
                      value: 'pdf',
                      child: ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: Icon(Icons.picture_as_pdf_outlined),
                        title: Text('Retirar ficha do DDS'),
                      ),
                    ),
''',
r'''                  if (record.type == 'DDS')
                    const PopupMenuItem(
                      value: 'pdf',
                      child: ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: Icon(Icons.picture_as_pdf_outlined),
                        title: Text('Retirar ficha do DDS'),
                      ),
                    ),
                  if (record.type == 'DDS')
                    const PopupMenuItem(
                      value: 'paper',
                      child: ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: Icon(Icons.fact_check_outlined),
                        title: Text('Ficha assinada em papel'),
                      ),
                    ),
''',
    'DDS menu item',
)
write(dds_path,dds)

# Training record: attach PDF/photo and optionally use the paper sheet as proof.
train_path='lib/screens/training_records_screen.dart'
train=read(train_path)
train=once(
    train,
    "import '../services/training_record_pdf_service.dart';\n",
    "import '../services/training_record_pdf_service.dart';\nimport '../widgets/physical_attendance_sheet.dart';\n",
    'training import',
)

training_methods=r'''  List<String> get _physicalAttendanceIds {
    final raw = record?.payload['physicalAttendanceSheetIds'];
    if (raw is! List) return <String>[];
    return raw.map((value) => '$value'.trim()).where((value) => value.isNotEmpty).toList();
  }

  Future<void> _openPhysicalAttendance() async {
    final current = record;
    if (current == null) return;
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => PhysicalAttendanceSheetScreen(
          companyId: widget.company.id,
          entityType: 'training_attendance_sheet',
          title: 'Ficha assinada • treinamento',
          initialIds: _physicalAttendanceIds,
          onChanged: (ids) async {
            final payload = Map<String, dynamic>.from(record!.payload)
              ..['physicalAttendanceSheetIds'] = ids
              ..['attendanceMethod'] = ids.isEmpty ? '' : 'FICHA_FISICA';
            await _savePayload(payload: payload);
            if (mounted) setState(() {});
          },
        ),
      ),
    );
    await _load();
  }

'''
if 'Future<void> _openPhysicalAttendance() async' not in train:
    marker='  Future<void> _finalize() async {\n'
    if train.count(marker)!=1:
        raise RuntimeError('PHYSICAL_ATTENDANCE training method marker')
    train=train.replace(marker,training_methods+marker,1)

old_pending=r'''    final pending = _count('PENDENTE');
    if (pending > 0) {
      final markAbsent = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Participantes pendentes'),
          content: Text(
            'Existem $pending participante(s) sem assinatura. Deseja marcá-los como ausentes antes de finalizar?',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Voltar'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Marcar ausentes'),
            ),
          ],
        ),
      );
      if (markAbsent != true) return;
      participants = participants.map((item) {
        if ('${item['status']}' != 'PENDENTE') return item;
        return <String, dynamic>{...item, 'status': 'AUSENTE'};
      }).toList();
    }
'''
new_pending=r'''    final pending = _count('PENDENTE');
    if (pending > 0) {
      if (_physicalAttendanceIds.isNotEmpty) {
        final choice = await showDialog<String>(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('Participantes pendentes'),
            content: Text(
              'Existem $pending participante(s) sem assinatura digital e há ficha física anexada. '
              'Escolha como registrar esses participantes antes de finalizar.',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context, 'back'),
                child: const Text('Voltar'),
              ),
              TextButton(
                onPressed: () => Navigator.pop(context, 'absent'),
                child: const Text('Marcar ausentes'),
              ),
              FilledButton(
                onPressed: () => Navigator.pop(context, 'paper'),
                child: const Text('Confirmar pela ficha física'),
              ),
            ],
          ),
        );
        if (choice == null || choice == 'back') return;
        participants = participants.map((item) {
          if ('${item['status']}' != 'PENDENTE') return item;
          return <String, dynamic>{
            ...item,
            'status': choice == 'paper' ? 'FICHA_FISICA' : 'AUSENTE',
            if (choice == 'paper') 'confirmationMethod': 'paper',
          };
        }).toList();
      } else {
        final markAbsent = await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('Participantes pendentes'),
            content: Text(
              'Existem $pending participante(s) sem assinatura. Deseja marcá-los como ausentes antes de finalizar?',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: const Text('Voltar'),
              ),
              FilledButton(
                onPressed: () => Navigator.pop(context, true),
                child: const Text('Marcar ausentes'),
              ),
            ],
          ),
        );
        if (markAbsent != true) return;
        participants = participants.map((item) {
          if ('${item['status']}' != 'PENDENTE') return item;
          return <String, dynamic>{...item, 'status': 'AUSENTE'};
        }).toList();
      }
    }
'''
train=once(train,old_pending,new_pending,'training pending decision')
train=once(
    train,
    "        content: const Text(\n          'As assinaturas ficarão bloqueadas. Os participantes assinados serão lançados automaticamente no controle de treinamentos.',\n        ),",
    "        content: const Text(\n          'Após finalizar, as confirmações ficam bloqueadas. Participantes com assinatura digital ou presença confirmada pela ficha física serão lançados no controle de treinamentos.',\n        ),",
    'training finalize text',
)
train=once(
    train,
r'''      for (final participant in participants) {
        if ('${participant['status'] ?? ''}' != 'ASSINADO') continue;
        final workerId = '${participant['workerId'] ?? ''}'.trim();
''',
r'''      for (final participant in participants) {
        final participantStatus = '${participant['status'] ?? ''}';
        if (participantStatus != 'ASSINADO' &&
            participantStatus != 'FICHA_FISICA') {
          continue;
        }
        final workerId = '${participant['workerId'] ?? ''}'.trim();
''',
    'training accepted presence',
)
train=once(
    train,
    "            notes: 'Ficha assinada no Auditar SST • sessão ${current.id}',",
    "            notes: participantStatus == 'FICHA_FISICA'\n                ? 'Presença comprovada por ficha física anexada • sessão ${current.id}'\n                : 'Ficha assinada no Auditar SST • sessão ${current.id}',",
    'training control note',
)
train=once(
    train,
    "    final signed = _count('ASSINADO');\n",
    "    final signed = _count('ASSINADO') + _count('FICHA_FISICA');\n",
    'training presence metric',
)
train=once(
    train,
    "Expanded(child: _metric('Assinados', signed, AuditarBrand.greenDark)),",
    "Expanded(child: _metric('Presentes', signed, AuditarBrand.greenDark)),",
    'training metric label',
)

paper_card=r'''            const SizedBox(height: 18),
            Card(
              child: ListTile(
                leading: const Icon(Icons.fact_check_outlined),
                title: const Text(
                  'Ficha assinada em papel',
                  style: TextStyle(fontWeight: FontWeight.w800),
                ),
                subtitle: Text(
                  _physicalAttendanceIds.isEmpty
                      ? 'Importe PDF, tire foto ou selecione imagens da ficha de presença.'
                      : '${_physicalAttendanceIds.length} arquivo(s) vinculado(s) • toque para visualizar',
                ),
                trailing: FilledButton.tonal(
                  onPressed: busy ? null : _openPhysicalAttendance,
                  child: Text(_physicalAttendanceIds.isEmpty ? 'Anexar' : 'Abrir'),
                ),
                onTap: busy ? null : _openPhysicalAttendance,
              ),
            ),
'''
participant_marker=r'''            const SizedBox(height: 18),
            Row(
              children: [
                const Expanded(
                  child: Text(
                    'Participantes e assinaturas',
'''
if paper_card not in train:
    if train.count(participant_marker)!=1:
        raise RuntimeError('PHYSICAL_ATTENDANCE training paper card marker')
    train=train.replace(participant_marker,paper_card+participant_marker,1)

train=once(
    train,
r'''              final color = status == 'ASSINADO'
                  ? AuditarBrand.greenDark
                  : status == 'AUSENTE'
                      ? const Color(0xFF7B8495)
                      : const Color(0xFFF29D18);
''',
r'''              final color = status == 'ASSINADO' || status == 'FICHA_FISICA'
                  ? AuditarBrand.greenDark
                  : status == 'AUSENTE'
                      ? const Color(0xFF7B8495)
                      : const Color(0xFFF29D18);
''',
    'training paper color',
)
train=once(
    train,
r'''                          status == 'ASSINADO'
                              ? (confirmationMethod == 'face' ? Icons.face_outlined : Icons.draw_outlined)
                              : status == 'AUSENTE'
                                  ? Icons.person_off_outlined
                                  : Icons.pending_actions_outlined,
''',
r'''                          status == 'ASSINADO'
                              ? (confirmationMethod == 'face' ? Icons.face_outlined : Icons.draw_outlined)
                              : status == 'FICHA_FISICA'
                                  ? Icons.fact_check_outlined
                                  : status == 'AUSENTE'
                                      ? Icons.person_off_outlined
                                      : Icons.pending_actions_outlined,
''',
    'training paper icon',
)
train=once(
    train,
r'''                          status,
                          if (status == 'ASSINADO') confirmationMethod == 'face' ? 'FACIAL' : 'ASSINATURA',
''',
r'''                          status == 'FICHA_FISICA' ? 'PRESENÇA CONFIRMADA' : status,
                          if (status == 'FICHA_FISICA') 'FICHA FÍSICA',
                          if (status == 'ASSINADO') confirmationMethod == 'face' ? 'FACIAL' : 'ASSINATURA',
''',
    'training paper label',
)
train=once(
    train,
r'''                              status == 'ASSINADO'
                                  ? Icons.verified_outlined
                                  : Icons.remove_circle_outline,
''',
r'''                              status == 'ASSINADO' || status == 'FICHA_FISICA'
                                  ? Icons.verified_outlined
                                  : Icons.remove_circle_outline,
''',
    'training paper finalized icon',
)
train=once(
    train,
r'''                                if (value == 'absent') {
                                  _setParticipantStatus(participant, 'AUSENTE');
                                }
''',
r'''                                if (value == 'paper') {
                                  _setParticipantStatus(participant, 'FICHA_FISICA');
                                }
                                if (value == 'absent') {
                                  _setParticipantStatus(participant, 'AUSENTE');
                                }
''',
    'training paper action',
)
train=once(
    train,
r'''                                const PopupMenuItem(
                                  value: 'absent',
                                  child: Text('Marcar ausente'),
                                ),
''',
r'''                                if (_physicalAttendanceIds.isNotEmpty)
                                  const PopupMenuItem(
                                    value: 'paper',
                                    child: Text('Confirmar pela ficha física'),
                                  ),
                                const PopupMenuItem(
                                  value: 'absent',
                                  child: Text('Marcar ausente'),
                                ),
''',
    'training paper menu item',
)
write(train_path,train)

# Training-generated PDF: paper proof is not presented as a digital signature.
pdf_path='lib/services/training_record_pdf_service.dart'
pdf=read(pdf_path)
pdf=once(
    pdf,
r'''    final signed = participants
        .where((item) => '${item['status'] ?? ''}' == 'ASSINADO')
        .length;
''',
r'''    final signed = participants
        .where((item) {
          final status = '${item['status'] ?? ''}';
          return status == 'ASSINADO' || status == 'FICHA_FISICA';
        })
        .length;
    final rawPhysicalSheets = payload['physicalAttendanceSheetIds'];
    final physicalSheetCount =
        rawPhysicalSheets is List ? rawPhysicalSheets.length : 0;
''',
    'training PDF present count',
)
pdf=once(
    pdf,
    "                      status == 'AUSENTE' ? 'AUSENTE' : '',",
    "                      status == 'AUSENTE'\n                          ? 'AUSENTE'\n                          : status == 'FICHA_FISICA'\n                              ? 'FICHA FÍSICA'\n                              : '',",
    'training PDF signature cell',
)
pdf=once(
    pdf,
r'''              [
                status,
                if (signedAt != null)
''',
r'''              [
                status == 'FICHA_FISICA' ? 'PRESENTE' : status,
                if (status == 'FICHA_FISICA') 'FICHA FÍSICA',
                if (signedAt != null)
''',
    'training PDF status',
)
pdf=once(
    pdf,
r'''          pw.Text(
            'As assinaturas e confirmações faciais acima foram registradas eletronicamente no aplicativo Auditar SST e vinculadas a este registro. Quando houver código FAC-, ele identifica a fotografia específica por sua impressão digital criptográfica.',
            style: const pw.TextStyle(fontSize: 7.2, color: PdfColors.grey700),
          ),
''',
r'''          pw.Text(
            physicalSheetCount > 0
                ? 'As assinaturas digitais e confirmações faciais foram registradas no Auditar SST. '
                    'Também há $physicalSheetCount arquivo(s) de ficha física assinada vinculado(s) a este treinamento; '
                    'participantes identificados como FICHA FÍSICA têm sua presença comprovada por essa evidência.'
                : 'As assinaturas e confirmações faciais acima foram registradas eletronicamente no aplicativo Auditar SST e vinculadas a este registro. Quando houver código FAC-, ele identifica a fotografia específica por sua impressão digital criptográfica.',
            style: const pw.TextStyle(fontSize: 7.2, color: PdfColors.grey700),
          ),
''',
    'training PDF evidence note',
)
write(pdf_path,pdf)

changed=[p for p,h in baseline.items()
         if hashlib.sha256((root/p).read_bytes()).hexdigest()!=h]
if changed:
    raise SystemExit('SYNC/MEDIA/DB/GS/AI MODIFIED WITHOUT AUTHORIZATION: '+repr(changed))

assert (root/'lib/widgets/physical_attendance_sheet.dart').exists()
assert '_openDdsPhysicalSheet' in read(dds_path)
assert '_openPhysicalAttendance' in read(train_path)
assert 'FICHA_FISICA' in read(pdf_path)
print('PHYSICAL_ATTENDANCE_V329126_OK')
print('SYNC_CORE_AND_MEDIA_IMPLEMENTATION_BYTE_IDENTICAL_OK')

#!/usr/bin/env python3
"""Ronda media durability + cleaner Ronda PDF. Leaves structured sync untouched."""
from pathlib import Path
import re, sys

if len(sys.argv) != 3 or sys.argv[2] not in ('android','windows'):
    raise SystemExit('usage: patch_ronda_media_backup_report_v329108.py APP_DIR android|windows')
root=Path(sys.argv[1]); platform=sys.argv[2]

def read(rel): return (root/rel).read_text(encoding='utf-8')
def write(rel,s): (root/rel).write_text(s,encoding='utf-8',newline='\n')
def one(s,old,new,label):
    if s.count(old)!=1: raise RuntimeError(f'{label}: {s.count(old)}')
    return s.replace(old,new,1)

# 1) Media catalog: Ronda photos become first-class cloud-backed assets.
rel='lib/services/media_sync_service.dart'; s=read(rel)
anchor="""    final signatures = await db.query(
      'inspections',
"""
insert="""    // Ronda Expressa stores its photo path inside sst_records.payload.
    // Register every local Ronda image in media_assets so uninstall/reinstall
    // recovery uses the same Drive-backed evidence pipeline as checklists.
    final roundRows = await db.query(
      'sst_records',
      columns: ['id', 'company_id', 'payload'],
      where: "type = 'OBSERVACAO_SEGURANCA'",
    );
    for (final row in roundRows) {
      final recordId = '${row['id'] ?? ''}'.trim();
      final companyId = '${row['company_id'] ?? ''}'.trim();
      final rawPayload = '${row['payload'] ?? ''}'.trim();
      if (recordId.isEmpty || companyId.isEmpty || rawPayload.isEmpty) continue;
      try {
        final decoded = jsonDecode(rawPayload);
        if (decoded is! Map) continue;
        final payload = Map<String, dynamic>.from(decoded);
        final roundType = '${payload['roundType'] ?? ''}'.trim();
        final photoPath = '${payload['photoPath'] ?? ''}'.trim();
        if (roundType != 'RONDA_EXPRESSA' || photoPath.isEmpty) continue;
        await _ensureAsset(
          db,
          companyId: companyId,
          entityType: 'round_photo',
          entityId: recordId,
          localPath: photoPath,
        );
      } catch (_) {}
    }

"""
s=one(s,anchor,insert+anchor,'discover Ronda media')

anchor="""  static Future<void> registerDdsSignature({
"""
insert="""  static Future<void> registerRoundPhoto({
    required String companyId,
    required String recordId,
    required String localPath,
  }) async {
    final company = companyId.trim();
    final record = recordId.trim();
    final path = localPath.trim();
    if (company.isEmpty || record.isEmpty || path.isEmpty) return;
    final db = await AppDatabase.instance.database;
    await _ensureAsset(
      db,
      companyId: company,
      entityType: 'round_photo',
      entityId: record,
      localPath: path,
    );
  }

  static Future<int> restoreRoundMedia({
    required String companyId,
    required String roundId,
  }) async {
    if (!AuthService.isSignedIn) return 0;
    final company = companyId.trim();
    final round = roundId.trim();
    if (company.isEmpty || round.isEmpty) return 0;
    final db = await AppDatabase.instance.database;
    await _discoverLocalMedia(db);
    final rows = await db.query(
      'sst_records',
      columns: ['id', 'payload'],
      where: "company_id = ? AND type = 'OBSERVACAO_SEGURANCA'",
      whereArgs: [company],
    );
    final refs = <Map<String,String>>[];
    for (final row in rows) {
      try {
        final decoded = jsonDecode('${row['payload'] ?? ''}');
        if (decoded is! Map) continue;
        final payload = Map<String,dynamic>.from(decoded);
        if ('${payload['roundId'] ?? ''}'.trim() != round) continue;
        final id = '${row['id'] ?? ''}'.trim();
        if (id.isNotEmpty) refs.add({'type':'round_photo','id':id});
      } catch (_) {}
    }
    return _restoreEntities(db, company, refs);
  }

"""
s=one(s,anchor,insert+anchor,'Ronda media APIs')

old="""    } else if (entityType == 'extinguisher_photo') {
      final rows = await db.query(
        'sst_records',
"""
new="""    } else if (entityType == 'extinguisher_photo' ||
        entityType == 'round_photo') {
      final rows = await db.query(
        'sst_records',
"""
s=one(s,old,new,'apply Ronda path')
write(rel,s)

# 2) Ronda screen: catalog immediately, kick independent media queue, restore
# from Drive when opening history and before producing a PDF.
rel='lib/screens/express_round_screen.dart'; s=read(rel)
s=one(s,"import 'dart:io';","import 'dart:async';\nimport 'dart:io';",'async import')
s=one(s,"import '../services/express_round_pdf_service.dart';",
      "import '../services/express_round_pdf_service.dart';\nimport '../services/device_sync_service.dart';\nimport '../services/media_sync_service.dart';",
      'media imports')
s=one(s,"""      final record = SstRecord(
        id: uuid.v4(),
""","""      final recordId = uuid.v4();
      final record = SstRecord(
        id: recordId,
""",'stable Ronda id')
s=one(s,"""      await AppDatabase.instance.upsertSstRecord(record);
      if (!mounted) return;
""","""      await AppDatabase.instance.upsertSstRecord(record);
      if (photoPath.trim().isNotEmpty) {
        await MediaSyncService.registerRoundPhoto(
          companyId: widget.company.id,
          recordId: recordId,
          localPath: photoPath,
        );
        // Media uses its own non-blocking queue; structured sync is untouched.
        unawaited(DeviceSyncService.sendPendingMediaNow());
      }
      if (!mounted) return;
""",'catalog/upload Ronda photo')
s=one(s,"""    final db = AppDatabase.instance;
    final all = await db.getSstRecords(
      type: 'OBSERVACAO_SEGURANCA',
      companyId: widget.company.id,
    );
""","""    final db = AppDatabase.instance;
    try {
      await MediaSyncService.restoreRoundMedia(
        companyId: widget.company.id,
        roundId: id,
      ).timeout(const Duration(seconds: 18));
    } catch (_) {
      // Offline history remains available; recovery retries on the next open.
    }
    final all = await db.getSstRecords(
      type: 'OBSERVACAO_SEGURANCA',
      companyId: widget.company.id,
    );
""",'history restore')
s=one(s,"""    setState(() => generatingReport = true);
    try {
      final bytes = await ExpressRoundPdfService.generate(
""","""    setState(() => generatingReport = true);
    try {
      try {
        await MediaSyncService.restoreRoundMedia(
          companyId: widget.company.id,
          roundId: roundId,
        ).timeout(const Duration(seconds: 18));
        await _reloadRoundRecords();
      } catch (_) {}
      final bytes = await ExpressRoundPdfService.generate(
""",'PDF media restore')
write(rel,s)

# 3) PDF: never print raw AI object/maps and use professional Portuguese labels.
rel='lib/services/express_round_pdf_service.dart'; s=read(rel)
start=s.index('  static List<pw.Widget> _aiReviewBlocks(')
end=s.index('  static List<pw.Widget> _conclusionBlocks(',start)
new_block=r'''  static List<pw.Widget> _aiReviewBlocks(
    Map<String, dynamic> review,
    PdfColor primary,
  ) {
    final sections = <pw.Widget>[];
    final preferred = <String, String>{
      'generalNotes': 'Síntese técnica da ronda',
      'criticalSummary': 'Pontos prioritários',
      'limitations': 'Limitações da avaliação',
    };
    var added = 0;
    for (final entry in preferred.entries) {
      final value = review[entry.key];
      String text = '';
      if (value is String) text = value.trim();
      if (value is List) {
        text = value
            .map((item) => '$item'.trim())
            .where((item) => item.isNotEmpty)
            .join('; ');
      }
      if (text.isEmpty) continue;
      if (added == 0) {
        sections.add(
          pw.Text(
            'SÍNTESE TÉCNICA DA RONDA',
            style: pw.TextStyle(
              fontSize: 11,
              fontWeight: pw.FontWeight.bold,
              color: primary,
            ),
          ),
        );
        sections.add(pw.SizedBox(height: 6));
      }
      sections.addAll(_pagedLabel(entry.value, text, primary));
      added++;
    }
    // actionPlanSuggestions intentionally stays out of the final PDF because
    // its raw map/ids are application data, not presentation content.
    return sections;
  }

'''
s=s[:start]+new_block+s[end:]
write(rel,s)

# Version bump only after all guarded edits succeeded.
rel='pubspec.yaml'; s=read(rel)
old,new={'android':('3.29.107+249','3.29.108+250'),
         'windows':('3.30.31+218','3.30.32+219')}[platform]
if s.count('version: '+old)!=1: raise RuntimeError('unexpected version '+old)
write(rel,s.replace('version: '+old,'version: '+new,1))

# Guardrails: no structured sync/database implementation was patched here.
media=read('lib/services/media_sync_service.dart')
screen=read('lib/screens/express_round_screen.dart')
pdf=read('lib/services/express_round_pdf_service.dart')
assert "entityType: 'round_photo'" in media
assert 'registerRoundPhoto' in screen and 'sendPendingMediaNow' in screen
assert 'restoreRoundMedia' in screen
assert "'actionPlanSuggestions'" not in pdf[pdf.index('static List<pw.Widget> _aiReviewBlocks'):pdf.index('static List<pw.Widget> _conclusionBlocks')]
print('RONDA_MEDIA_BACKUP_REPORT_OK',platform,new)

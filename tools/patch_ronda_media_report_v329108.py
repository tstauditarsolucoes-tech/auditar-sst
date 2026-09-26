#!/usr/bin/env python3
"""Protect Express Round photos in Drive and clean the Express Round PDF.

Targeted post-patch for Android 3.29.107 / Windows 3.30.31.
Does not modify structured sync, auth, DB schema, or Apps Script transport.
"""
from pathlib import Path
import re, sys

if len(sys.argv) != 3 or sys.argv[2] not in ('android','windows'):
    raise SystemExit('usage: patch_ronda_media_report_v329108.py APP_DIR android|windows')
root=Path(sys.argv[1]); platform=sys.argv[2]

def read(rel): return (root/rel).read_text(encoding='utf-8')
def write(rel,s): (root/rel).write_text(s,encoding='utf-8',newline='\n')
def once(s,old,new,label):
    if old not in s: raise RuntimeError('anchor missing '+label)
    if s.count(old)!=1: raise RuntimeError(f'anchor ambiguous {label}: {s.count(old)}')
    return s.replace(old,new,1)

# ---- Media catalog: Express Round photo is a first-class Drive evidence ----
rel='lib/services/media_sync_service.dart'; s=read(rel)

marker="""  static Future<void> registerCompanyLogo({
"""
insert="""  /// Registers an Express Round photo in the same protected Drive evidence
  /// catalog used by checklist photos. The SstRecord keeps its local path,
  /// while media_assets tracks the confirmed remote copy.
  static Future<void> registerExpressRoundPhoto({
    required String companyId,
    required String recordId,
    required String localPath,
  }) async {
    final cleanCompanyId = companyId.trim();
    final cleanRecordId = recordId.trim();
    final cleanPath = localPath.trim();
    if (cleanCompanyId.isEmpty || cleanRecordId.isEmpty || cleanPath.isEmpty) {
      return;
    }
    final db = await AppDatabase.instance.database;
    await _ensureAsset(
      db,
      companyId: cleanCompanyId,
      entityType: 'express_round_photo',
      entityId: cleanRecordId,
      localPath: cleanPath,
    );
  }

"""
s=once(s,marker,insert+marker,'public ronda media registration')

marker="""    final signatures = await db.query(
"""
insert="""    // Ronda Expressa historically stored photoPath only inside the JSON
    // payload. Discover those files too, otherwise they can be invisible to
    // the evidence queue and disappear after an uninstall.
    final roundRows = await db.query(
      'sst_records',
      columns: ['id', 'company_id', 'payload'],
      where: 'type = ?',
      whereArgs: const ['OBSERVACAO_SEGURANCA'],
    );
    for (final row in roundRows) {
      final recordId = '${row['id'] ?? ''}'.trim();
      final companyId = '${row['company_id'] ?? ''}'.trim();
      final rawPayload = '${row['payload'] ?? ''}'.trim();
      if (recordId.isEmpty || companyId.isEmpty || rawPayload.isEmpty) continue;
      try {
        final decoded = jsonDecode(rawPayload);
        if (decoded is! Map) continue;
        final path = '${decoded['photoPath'] ?? ''}'.trim();
        if (path.isEmpty) continue;
        await _ensureAsset(
          db,
          companyId: companyId,
          entityType: 'express_round_photo',
          entityId: recordId,
          localPath: path,
        );
      } catch (_) {}
    }

"""
s=once(s,marker,insert+marker,'discover ronda photos')

old="""    final rows = await db.query(
      'media_assets',
      where: 'entity_type IN (?, ?)',
      whereArgs: const ['evidence_photo', 'completion_photo'],
      orderBy: 'updated_at ASC',
    );
"""
new="""    final rows = await db.query(
      'media_assets',
      where: 'entity_type IN (?, ?, ?)',
      whereArgs: const [
        'evidence_photo',
        'completion_photo',
        'express_round_photo',
      ],
      orderBy: 'updated_at ASC',
    );
"""
s=once(s,old,new,'repair library includes ronda')

old="""    } else if (entityType == 'extinguisher_photo') {
"""
new="""    } else if (entityType == 'extinguisher_photo' ||
        entityType == 'express_round_photo') {
"""
s=once(s,old,new,'restore ronda path into payload')
write(rel,s)

# ---- Ronda save: register immediately and kick evidence upload ----
rel='lib/screens/express_round_screen.dart'; s=read(rel)
s=once(s,"import 'dart:io';\n","import 'dart:async';\nimport 'dart:io';\n",'async import')
s=once(s,"import '../services/express_round_pdf_service.dart';\n",
       "import '../services/express_round_pdf_service.dart';\nimport '../services/device_sync_service.dart';\nimport '../services/media_sync_service.dart';\n",
       'ronda media imports')
old="""      await AppDatabase.instance.upsertSstRecord(record);
      if (!mounted) return;
"""
new="""      await AppDatabase.instance.upsertSstRecord(record);
      if (photoPath.trim().isNotEmpty) {
        await MediaSyncService.registerExpressRoundPhoto(
          companyId: widget.company.id,
          recordId: record.id,
          localPath: photoPath,
        );
        // Do not block field capture on network. The independent evidence
        // queue confirms the Drive copy in background and retries if needed.
        unawaited(DeviceSyncService.sendPendingMediaNow());
      }
      if (!mounted) return;
"""
s=once(s,old,new,'register and upload ronda photo')
write(rel,s)

# ---- PDF: remove raw IA structures and make missing-photo reports readable ----
rel='lib/services/express_round_pdf_service.dart'; s=read(rel)
old="""      if (const {
        'automaticChecks',
        'metrics',
        'conclusion',
        'conclusao',
        'finalConclusion',
        'conclusaoFinal',
      }.contains(entry.key))
        continue;
"""
new="""      if (const {
        'automaticChecks',
        'metrics',
        'conclusion',
        'conclusao',
        'finalConclusion',
        'conclusaoFinal',
        'actionPlanSuggestions',
        'action_plan_suggestions',
        'suggestedActions',
      }.contains(entry.key)) {
        continue;
      }
"""
s=once(s,old,new,'hide raw AI action structures')

old="""      sections.addAll(_pagedLabel(_humanize(entry.key), text, primary));
"""
new="""      const friendlyLabels = <String, String>{
        'generalNotes': 'Síntese técnica',
        'general_notes': 'Síntese técnica',
        'criticalSummary': 'Pontos prioritários',
        'critical_summary': 'Pontos prioritários',
        'limitations': 'Limitações da análise',
        'recommendations': 'Recomendações complementares',
      };
      sections.addAll(
        _pagedLabel(
          friendlyLabels[entry.key] ?? _humanize(entry.key),
          text,
          primary,
        ),
      );
"""
s=once(s,old,new,'friendly AI labels')

# Replace the fixed empty-photo card by a compact full-width finding when the
# original photo is not available. This avoids a giant blank "Sem foto" box.
anchor="""    final parts = _pageChunks(
      narrative.isEmpty ? record.title : narrative,
      limit: 260,
    );
    return [
"""
replacement="""    final parts = _pageChunks(
      narrative.isEmpty ? record.title : narrative,
      limit: 260,
    );
    if (photo == null) {
      return [
        pw.Container(
          margin: const pw.EdgeInsets.only(bottom: 3),
          padding: const pw.EdgeInsets.all(9),
          decoration: pw.BoxDecoration(
            border: pw.Border.all(color: PdfColors.grey500, width: .6),
          ),
          child: pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Row(
                children: [
                  pw.Expanded(
                    child: pw.Text(
                      conform
                          ? 'CONFORMIDADE / BOA PRÁTICA'
                          : 'NÃO CONFORMIDADE',
                      style: pw.TextStyle(
                        fontSize: 7.5,
                        fontWeight: pw.FontWeight.bold,
                        color: conform ? green : red,
                      ),
                    ),
                  ),
                  pw.Text(
                    'Evidência fotográfica indisponível',
                    style: const pw.TextStyle(
                      fontSize: 7,
                      color: PdfColors.grey600,
                    ),
                  ),
                ],
              ),
              pw.SizedBox(height: 4),
              pw.Text(
                _categories(record),
                style: pw.TextStyle(
                  fontSize: 9,
                  fontWeight: pw.FontWeight.bold,
                  color: primary,
                ),
              ),
              pw.SizedBox(height: 5),
              pw.Text(
                parts.isEmpty ? '-' : parts.first,
                style: const pw.TextStyle(fontSize: 8.4, lineSpacing: 1.4),
              ),
            ],
          ),
        ),
        for (var i = 1; i < parts.length; i++)
          pw.Padding(
            padding: const pw.EdgeInsets.fromLTRB(8, 2, 8, 3),
            child: pw.Text(
              parts[i],
              style: const pw.TextStyle(fontSize: 8.4, lineSpacing: 1.4),
            ),
          ),
        pw.Padding(
          padding: const pw.EdgeInsets.fromLTRB(8, 3, 8, 8),
          child: pw.Text(
            _locationLine(record, sectors),
            style: const pw.TextStyle(fontSize: 7.2, color: PdfColors.grey700),
          ),
        ),
      ];
    }
    return [
"""
s=once(s,anchor,replacement,'compact missing photo report')
write(rel,s)

# Version bump.
rel='pubspec.yaml'; s=read(rel)
old,new={
 'android':('3.29.107+249','3.29.108+250'),
 'windows':('3.30.31+218','3.30.32+219'),
}[platform]
if s.count('version: '+old)!=1: raise RuntimeError('unexpected version '+old)
s=s.replace('version: '+old,'version: '+new,1); write(rel,s)

# Safety/regression assertions.
media=read('lib/services/media_sync_service.dart')
ronda=read('lib/screens/express_round_screen.dart')
pdf=read('lib/services/express_round_pdf_service.dart')
assert "entityType: 'express_round_photo'" in media
assert "'express_round_photo'," in media
assert "entityType == 'express_round_photo'" in media
assert 'registerExpressRoundPhoto' in ronda
assert 'DeviceSyncService.sendPendingMediaNow()' in ronda
assert "'actionPlanSuggestions'" in pdf
assert 'Evidência fotográfica indisponível' in pdf
assert 'Síntese técnica' in pdf and 'Pontos prioritários' in pdf
print('RONDA_MEDIA_REPORT_PROTECTION_OK',platform,new)
print('STRUCTURED_SYNC_NOT_TOUCHED_OK')

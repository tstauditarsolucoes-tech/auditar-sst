#!/usr/bin/env python3
"""Protect Express Round photos in the media library and polish Ronda PDF output."""
from pathlib import Path
import re, sys

root=Path(sys.argv[1]); platform=sys.argv[2]
if platform not in ('android','windows'): raise SystemExit('platform')

def read(rel): return (root/rel).read_text(encoding='utf-8')
def write(rel,s): (root/rel).write_text(s,encoding='utf-8',newline='\n')
def once(s,old,new,label):
    n=s.count(old)
    if n!=1: raise RuntimeError(f'{label}: expected 1, got {n}')
    return s.replace(old,new,1)

# --- Media library: discover, upload and restore Express Round photos.
rel='lib/services/media_sync_service.dart'; s=read(rel)
anchor="""    final signatures = await db.query(
      'inspections',
"""
insert="""    // Ronda Expressa stores the photo path inside sst_records.payload.
    // Register every local photo in the durable media catalog so reinstalling
    // the app does not make the evidence disappear when it was already sent.
    final roundRows = await db.query(
      'sst_records',
      columns: ['id', 'company_id', 'type', 'payload'],
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
        if ('${payload['roundType'] ?? ''}' != 'RONDA_EXPRESSA') continue;
        final localPath = '${payload['photoPath'] ?? ''}'.trim();
        if (localPath.isEmpty) continue;
        await _ensureAsset(
          db,
          companyId: companyId,
          entityType: 'express_round_photo',
          entityId: recordId,
          localPath: localPath,
        );
      } catch (_) {}
    }

"""
s=once(s,anchor,insert+anchor,'discover Ronda media')
anchor2="""  static Future<void> registerDdsSignature({
"""
method="""  static Future<void> registerExpressRoundPhoto({
    required String companyId,
    required String recordId,
    required String localPath,
  }) async {
    if (companyId.trim().isEmpty ||
        recordId.trim().isEmpty ||
        localPath.trim().isEmpty) return;
    final db = await AppDatabase.instance.database;
    await _ensureAsset(
      db,
      companyId: companyId,
      entityType: 'express_round_photo',
      entityId: recordId,
      localPath: localPath,
    );
  }

  static Future<int> restoreExpressRoundPhotos({
    required String companyId,
    required Iterable<String> recordIds,
  }) async {
    if (!AuthService.isSignedIn) return 0;
    final ids = recordIds.map((e) => e.trim()).where((e) => e.isNotEmpty).toSet();
    if (ids.isEmpty || companyId.trim().isEmpty) return 0;
    final db = await AppDatabase.instance.database;
    return _restoreEntities(
      db,
      companyId,
      ids.map((id) => {'type':'express_round_photo','id':id}).toList(),
    );
  }

"""
s=once(s,anchor2,method+anchor2,'Ronda media public API')
old="""    } else if (entityType == 'extinguisher_photo') {
      final rows = await db.query(
        'sst_records',
"""
new="""    } else if (entityType == 'extinguisher_photo' ||
        entityType == 'express_round_photo') {
      final rows = await db.query(
        'sst_records',
"""
s=once(s,old,new,'apply Ronda restored path')
# Repair library must also include Ronda assets.
old="""      where: 'entity_type IN (?, ?)',
      whereArgs: const ['evidence_photo', 'completion_photo'],
"""
new="""      where: 'entity_type IN (?, ?, ?)',
      whereArgs: const [
        'evidence_photo',
        'completion_photo',
        'express_round_photo',
      ],
"""
s=once(s,old,new,'repair Ronda media')
write(rel,s)

# --- Ronda screen: register photo immediately and recover when historical round opens.
rel='lib/screens/express_round_screen.dart'; s=read(rel)
s=once(s,"import 'dart:io';","import 'dart:async';\nimport 'dart:io';",'async import')
s=once(s,"import '../services/express_round_pdf_service.dart';",
       "import '../services/express_round_pdf_service.dart';\nimport '../services/media_sync_service.dart';",'media import')
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
        // Upload is independent from the structured sync and never blocks
        // navigation through the Ronda.
        unawaited(MediaSyncService.uploadPending(limit: 4));
      }
      if (!mounted) return;
"""
s=once(s,old,new,'register Ronda photo after save')

# Recover any protected Ronda photo when a historical round is loaded.
needle="""  Future<void> _loadRoundById(
"""
idx=s.find(needle)
if idx<0: raise RuntimeError('load round method absent')
# locate body marker in this method: after set of selected records is assigned. Use known all query section.
old="""    if (!mounted) return;
    setState(() {
      roundId = id;
      roundRecords = selected;
"""
new="""    if (historical && selected.isNotEmpty) {
      try {
        await MediaSyncService.restoreExpressRoundPhotos(
          companyId: widget.company.id,
          recordIds: selected.map((record) => record.id),
        );
        final refreshed = await AppDatabase.instance.getSstRecords(
          companyId: widget.company.id,
          type: 'OBSERVACAO_SEGURANCA',
        );
        selected = refreshed
            .where((record) => '${record.payload['roundId'] ?? ''}' == id)
            .toList();
      } catch (_) {
        // Historical structured data remains available even if offline.
      }
    }
    if (!mounted) return;
    setState(() {
      roundId = id;
      roundRecords = selected;
"""
# there can be exact occurrence one inside load method
s=once(s,old,new,'restore historical Ronda photos')
write(rel,s)

# --- PDF: do not print raw JSON-like IA structures; use professional labels.
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
      final value = entry.value;
      String text = '';
      if (value is String) text = value.trim();
      if (value is List)
        text = value
            .map((item) => '$item')
            .where((item) => item.trim().isNotEmpty)
            .join('; ');
      if (text.isEmpty) continue;
      sections.addAll(_pagedLabel(_humanize(entry.key), text, primary));
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
      }.contains(entry.key)) continue;
      final value = entry.value;
      String text = '';
      if (value is String) text = value.trim();
      if (value is List && value.every((item) => item is String)) {
        text = value
            .cast<String>()
            .map((item) => item.trim())
            .where((item) => item.isNotEmpty)
            .join('; ');
      }
      // Maps/lists of maps are internal structured data and must never be
      // printed as Dart/JSON text in a customer report.
      if (text.isEmpty) continue;
      const labels = <String, String>{
        'generalNotes': 'Síntese técnica',
        'general_notes': 'Síntese técnica',
        'criticalSummary': 'Pontos prioritários',
        'critical_summary': 'Pontos prioritários',
        'limitations': 'Limitações da análise',
        'recommendations': 'Recomendações gerais',
      };
      sections.addAll(
        _pagedLabel(labels[entry.key] ?? _humanize(entry.key), text, primary),
      );
"""
s=once(s,old,new,'clean IA review PDF')

# In photographic template, when there is no image, use the full width for text
# instead of a large empty "Sem foto" panel.
old="""    return [
      pw.Container(
        margin: const pw.EdgeInsets.only(bottom: 3),
        decoration: pw.BoxDecoration(
          border: pw.Border.all(color: PdfColors.grey500, width: .6),
        ),
        child: pw.Row(
"""
new="""    if (photo == null) {
      return [
        pw.Container(
          width: double.infinity,
          margin: const pw.EdgeInsets.only(bottom: 6),
          padding: const pw.EdgeInsets.all(8),
          decoration: pw.BoxDecoration(
            border: pw.Border.all(color: PdfColors.grey500, width: .6),
          ),
          child: pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Text(
                conform ? 'CONFORMIDADE' : 'NÃO CONFORMIDADE',
                style: pw.TextStyle(
                  fontSize: 8.5,
                  fontWeight: pw.FontWeight.bold,
                  color: conform ? green : red,
                ),
              ),
              pw.SizedBox(height: 4),
              pw.Text(
                narrative.isEmpty ? record.title : narrative,
                style: const pw.TextStyle(fontSize: 8, lineSpacing: 1.6),
                textAlign: pw.TextAlign.justify,
              ),
              pw.SizedBox(height: 4),
              pw.Text(
                _locationLine(record, sectors),
                style: const pw.TextStyle(fontSize: 6.8, color: PdfColors.grey700),
              ),
            ],
          ),
        ),
      ];
    }
    return [
      pw.Container(
        margin: const pw.EdgeInsets.only(bottom: 3),
        decoration: pw.BoxDecoration(
          border: pw.Border.all(color: PdfColors.grey500, width: .6),
        ),
        child: pw.Row(
"""
s=once(s,old,new,'no blank photo panel')
write(rel,s)

# Version.
rel='pubspec.yaml'; s=read(rel)
oldv,newv=(('3.29.107+249','3.29.108+250') if platform=='android'
           else ('3.30.31+218','3.30.32+219'))
if f'version: {oldv}' not in s: raise RuntimeError('version '+oldv+' absent')
write(rel,s.replace(f'version: {oldv}',f'version: {newv}',1))

# Source assertions.
media=read('lib/services/media_sync_service.dart')
screen=read('lib/screens/express_round_screen.dart')
pdf=read('lib/services/express_round_pdf_service.dart')
assert "entityType: 'express_round_photo'" in media
assert 'registerExpressRoundPhoto' in screen and 'restoreExpressRoundPhotos' in screen
assert "'actionPlanSuggestions'" in pdf and 'Maps/lists of maps' in pdf
assert 'if (photo == null)' in pdf
print('RONDA_EVIDENCE_PROTECTION_AND_PDF_OK',platform,newv)

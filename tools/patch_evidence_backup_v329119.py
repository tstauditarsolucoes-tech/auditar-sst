#!/usr/bin/env python3
"""Factual record/evidence protection UX without changing the existing sync protocol or GS."""
from pathlib import Path
import sys

root=Path(sys.argv[1]); platform=sys.argv[2]
assert platform in ('android','windows')
feature=Path(__file__).resolve().parents[1]/'feature_sources/evidence_backup_screen.dart'
assert feature.exists(),'Protection screen source missing'
dst=root/'lib/screens/evidence_backup_screen.dart'
dst.write_bytes(feature.read_bytes())

def patch(rel,old,new,label):
 p=root/rel
 s=p.read_text(encoding='utf-8')
 count=s.count(old)
 if count!=1:raise RuntimeError(f'{label}: expected one occurrence, got {count}')
 p.write_text(s.replace(old,new,1),encoding='utf-8',newline='\n')

# Company: a real, per-company protective status viewer rather than a fake green
# success badge on the Home screen.
patch('lib/screens/company_detail_screen.dart',
      "import 'action_plan_screen.dart';",
      "import 'evidence_backup_screen.dart';\nimport 'action_plan_screen.dart';",
      'company backup import')
patch('lib/screens/company_detail_screen.dart',
"""          _shortcut(
            icon: Icons.monitor_heart_outlined,
            title: 'Painel Gerencial',""",
"""          _shortcut(
            icon: Icons.cloud_done_outlined,
            title: 'Proteção de vistorias e fotos',
            subtitle: 'Confira o salvamento local, pendências e backup por empresa',
            onTap: () => _open(EvidenceBackupScreen(company: widget.company)),
          ),
          const SizedBox(height: 10),
          _shortcut(
            icon: Icons.monitor_heart_outlined,
            title: 'Painel Gerencial',""",'company backup shortcut')

# Ronda: direct access from current/archived history without cluttering Home.
patch('lib/screens/express_round_screen.dart',
      "import 'safety_observations_screen.dart';",
      "import 'safety_observations_screen.dart';\nimport 'evidence_backup_screen.dart';",
      'Ronda backup import')
patch('lib/screens/express_round_screen.dart',
"""  Future<void> _showRoundsArchive() async {""",
"""  Future<void> _openBackupStatus() async {
    await Navigator.of(context).push<void>(MaterialPageRoute(
      builder: (_) => EvidenceBackupScreen(company: widget.company),
    ));
  }

  Future<void> _showRoundsArchive() async {""",
      'Ronda backup action')
patch('lib/screens/express_round_screen.dart',
"""        actions: [
          IconButton(
            tooltip: 'Histórico de rondas',""",
"""        actions: [
          IconButton(
            tooltip: 'Proteção de vistorias e fotos',
            onPressed: _openBackupStatus,
            icon: const Icon(Icons.cloud_done_outlined),
          ),
          IconButton(
            tooltip: 'Histórico de rondas',""",
      'Ronda backup app bar')
patch('lib/screens/express_round_screen.dart',
"""                        IconButton(
                          onPressed: () => Navigator.pop(sheetContext),
                          icon: const Icon(Icons.close_rounded),
                        ),""",
"""                        IconButton(
                          tooltip: 'Conferir proteção dos registros e fotos',
                          onPressed: () {
                            Navigator.pop(sheetContext);
                            _openBackupStatus();
                          },
                          icon: const Icon(Icons.cloud_done_outlined),
                        ),
                        IconButton(
                          onPressed: () => Navigator.pop(sheetContext),
                          icon: const Icon(Icons.close_rounded),
                        ),""",
       'Ronda history protection shortcut')
patch('lib/screens/express_round_screen.dart',
"""            subtitle: Text(
                              '$kind • ${record.priority}'""",
"""            subtitle: Text(
                              '$kind • ${record.priority} • salvo neste aparelho'""",
       'Ronda honest saved label')
patch('lib/screens/express_round_screen.dart',
      "'Registro salvo. Continue a ronda.',",
      "'Registro salvo neste aparelho. Backup em segundo plano; confira no ícone da nuvem.',",
      'Ronda success explanation')
patch('lib/screens/express_round_screen.dart',
      "'Conformidade salva. Continue a ronda.'",
      "'Conformidade salva neste aparelho. Confira o backup no ícone da nuvem.'",
      'Ronda conform explanation')

# Avoid claiming a replaced photo is backed up with the old file's Drive ID.
# This only reconciles an explicit existing Ronda asset when the current local
# file path changes. Never delete the older local file; no schema/protocol edit.
patch('lib/services/media_sync_service.dart',
"""      entityId: record,
      localPath: path,
    );
  }

  static Future<int> restoreRoundMedia({""",
"""      entityId: record,
      localPath: path,
    );
    // Replacing a picture must invalidate the PREVIOUS picture's cloud ID.
    // Only do this for an actual local file, never a path from another device.
    if (!await File(path).exists()) return;
    final mediaId = _assetId('round_photo', record);
    final existing = await db.query('media_assets',
      columns: ['local_path','drive_file_id'],
      where: 'id = ?', whereArgs: [mediaId], limit: 1);
    if (existing.isNotEmpty) {
      final previous = '${existing.first['local_path'] ?? ''}'.trim();
      if (previous.isNotEmpty && previous != path) {
        await db.update('media_assets', {
          'local_path': path,
          'drive_file_id': '',
          'file_name': p.basename(path),
          'mime_type': _mimeTypeFor(path),
          'updated_at': DateTime.now().toUtc().toIso8601String(),
        }, where: 'id = ?', whereArgs: [mediaId]);
      }
    }
  }

  static Future<int> restoreRoundMedia({""",
      'reset stale Ronda media confirmation only for real replacement')

# Editing a Ronda record does not wait for media uploads; registration happens
# after the local save. The established queue uploads separately.
patch('lib/screens/safety_observations_screen.dart',
      "import 'dart:io';",
      "import 'dart:async';\nimport 'dart:io';",
      'edit async import')
patch('lib/screens/safety_observations_screen.dart',
      "import '../services/management_panel_service.dart';",
      "import '../services/management_panel_service.dart';\nimport '../services/media_sync_service.dart';\nimport '../services/device_sync_service.dart';",
      'edit media imports')
patch('lib/screens/safety_observations_screen.dart',
"""    Navigator.pop(context, true);
    // Keep the existing management-panel refresh, but do not block the save.""",
"""    Navigator.pop(context, true);
    // Only local evidence files are registered; remote cache-only paths are
    // recovered using the existing media library, not overwritten here.
    unawaited(() async {
      try {
        if (payload['roundType'] == 'RONDA_EXPRESSA') {
          for (final slot in <(String, String)>[
            (record.id, photoPath),
            (record.id + '_2', secondPhotoPath),
          ]) {
            if (slot.$2.isEmpty || !await File(slot.$2).exists()) continue;
            await MediaSyncService.registerRoundPhoto(
              companyId: widget.company.id,
              recordId: slot.$1,
              localPath: slot.$2,
            );
          }
          await DeviceSyncService.sendPendingMediaNow();
        }
      } catch (_) {
        // The saved record stays available offline even when the upload fails.
      }
    }());
    // Keep the existing management-panel refresh, but do not block the save.""",
      'queue edited evidence without blocking save')

p=root/'pubspec.yaml'
s=p.read_text(encoding='utf-8')
old='version: 3.29.118+260' if platform=='android' else 'version: 3.30.42+229'
new='version: 3.29.119+261' if platform=='android' else 'version: 3.30.43+230'
if old not in s:
 oldLine=next((v for v in s.splitlines() if v.startswith('version: ')),'')
 raise RuntimeError('Expected release baseline '+old+' but found '+oldLine)
p.write_text(s.replace(old,new,1),encoding='utf-8',newline='\n')
assert 'class EvidenceBackupScreen' in dst.read_text(encoding='utf-8')
assert "title: 'Proteção de vistorias e fotos'" in (root/'lib/screens/company_detail_screen.dart').read_text(encoding='utf-8')
assert 'await DeviceSyncService.sendPendingMediaNow()' in (root/'lib/screens/safety_observations_screen.dart').read_text(encoding='utf-8')
print('PER_COMPANY_EVIDENCE_STATUS_AND_EDITED_MEDIA_OK',platform,new)

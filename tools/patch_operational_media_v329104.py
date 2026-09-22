#!/usr/bin/env python3
"""Targeted operational improvements on the already released Auditar SST base."""
from pathlib import Path
import sys

root = Path(sys.argv[1])
platform = sys.argv[2] if len(sys.argv)>2 else 'android'
if platform not in ('android','windows'): raise ValueError(platform)

def replace_once(path, old, new, label):
    s=path.read_text(encoding='utf-8')
    if old not in s: raise RuntimeError(f'{label} marker absent: {path}')
    if s.count(old)!=1: raise RuntimeError(f'{label} marker ambiguous {s.count(old)}: {path}')
    path.write_text(s.replace(old,new,1),encoding='utf-8',newline='\n')

sync = root/'lib/services/device_sync_service.dart'
media = root/'lib/services/media_sync_service.dart'
pub = root/'pubspec.yaml'
policy = root/'lib/services/media_sync_policy.dart'
policy.write_text(Path('build_sources/v3.29.104-field-speed/media_sync_policy.dart').read_text(encoding='utf-8'),encoding='utf-8',newline='\n')

replace_once(sync, "import 'media_sync_service.dart';",
             "import 'media_sync_service.dart';\nimport 'media_sync_policy.dart';",
             'media policy import')
replace_once(sync, "  final bool skipped;\n", "  final bool skipped;\n  final bool mediaChanged;\n", 'event property')
replace_once(sync, "    this.skipped = false,\n", "    this.skipped = false,\n    this.mediaChanged = false,\n", 'event ctor')
replace_once(sync, "  static DateTime? _lastAutoMediaKick;\n",
             "  static DateTime? _lastAutoMediaKick;\n  static int? _lastMediaPending;\n  static bool _lastMediaFailed = false;\n",
             'media state')

start=sync.read_text(encoding='utf-8')
begin=start.index('      // Mídia é baixa prioridade. Só inicia quando este ciclo não teve dados')
end=start.index('      return result;',begin)
new=r'''      // Fotos e assinaturas são enviadas numa fila independente. Mesmo que
      // cheguem cadastros continuamente, as evidências não ficam bloqueadas.
      // Nunca aguardamos a fila de mídia para liberar o pull/push principal.
      final mediaNow = DateTime.now().toUtc();
      if (MediaSyncPolicy.shouldKick(
        now: mediaNow,
        lastKick: _lastAutoMediaKick,
        active: _activeMediaSync != null,
        lastFailed: _lastMediaFailed,
        pendingAfterLastAttempt: _lastMediaPending,
      )) {
        _lastAutoMediaKick = mediaNow;
        unawaited(_syncMediaBestEffort());
      }
'''
sync.write_text(start[:begin]+new+start[end:],encoding='utf-8',newline='\n')

start=sync.read_text(encoding='utf-8')
begin=start.index('  static Future<void> _syncMediaBestEffort() {')
end=start.index('  static Future<bool> _attemptIsDue(',begin)
new=r'''  /// Retries the evidence queue without running a second structured sync.
  static Future<void> sendPendingMediaNow() =>
      _syncMediaBestEffort(limit: MediaSyncPolicy.manualBatchLimit);

  static Future<void> _syncMediaBestEffort({
    int limit = MediaSyncPolicy.automaticBatchLimit,
  }) {
    final active = _activeMediaSync;
    if (active != null) return active;

    late final Future<void> operation;
    operation = (() async {
      try {
        final summary = await MediaSyncService.uploadPending(limit: limit);
        _lastMediaPending = summary.pending;
        _lastMediaFailed = (await AppDatabase.instance.getSetting(
          'media_sync_last_error',
        )).trim().isNotEmpty;
      } catch (_) {
        _lastMediaFailed = true;
        try {
          await AppDatabase.instance.setSetting(
            'media_sync_last_error',
            'Envio temporariamente indisponível; as evidências permanecem no aparelho.',
          );
        } catch (_) {}
      } finally {
        _events.add(const DeviceSyncResult(mediaChanged: true));
      }
    })().whenComplete(() {
      if (identical(_activeMediaSync, operation)) _activeMediaSync = null;
    });
    _activeMediaSync = operation;
    return operation;
  }

'''
sync.write_text(start[:begin]+new+start[end:],encoding='utf-8',newline='\n')

replace_once(media,
  "  static const int _maxMediaBytes = 12 * 1024 * 1024;\n\n  static Future<MediaSyncSummary> uploadPending({int limit = 40}) async {",
  """  static const int _maxMediaBytes = 12 * 1024 * 1024;
  static Future<MediaSyncSummary>? _activeUpload;

  static Future<MediaSyncSummary> uploadPending({int limit = 40}) {
    final active = _activeUpload;
    if (active != null) return active;
    late final Future<MediaSyncSummary> operation;
    operation = _uploadPendingImpl(limit: limit).whenComplete(() {
      if (identical(_activeUpload, operation)) _activeUpload = null;
    });
    _activeUpload = operation;
    return operation;
  }

  static Future<MediaSyncSummary> _uploadPendingImpl({int limit = 40}) async {""",
  'single-flight media upload')
replace_once(media,
  "      if (!await file.exists()) continue;",
  """      if (!await file.exists()) {
        lastError = 'Uma evidência está sem arquivo neste aparelho. '
            'O registro foi preservado; confira a biblioteca de evidências.';
        continue;
      }""",
  'missing file visible')

old_version='3.29.103+245' if platform=='android' else '3.30.27+214'
new_version='3.29.104+246' if platform=='android' else '3.30.28+215'
replace_once(pub, 'version: '+old_version, 'version: '+new_version, 'version bump')
print('MEDIA_QUEUE_STATUS_PATCH_OK',platform,new_version)

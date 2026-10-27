#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
path = root / 'lib/services/device_sync_service.dart'
text = path.read_text(encoding='utf-8')

old_result = '''class DeviceSyncResult {
  final int sent;
  final int received;
  final bool skipped;

  const DeviceSyncResult({
    this.sent = 0,
    this.received = 0,
    this.skipped = false,
  });
}
'''
new_result = '''class DeviceSyncResult {
  final int sent;
  final int received;
  final bool skipped;
  final bool partial;
  final int pending;

  const DeviceSyncResult({
    this.sent = 0,
    this.received = 0,
    this.skipped = false,
    this.partial = false,
    this.pending = 0,
  });
}
'''
if 'final bool partial;' not in text:
    if old_result not in text:
        raise RuntimeError('DeviceSyncResult Android não encontrado')
    text = text.replace(old_result, new_result, 1)

old_entry = '''  static Future<DeviceSyncResult> synchronize({bool force = false}) {
    final active = _activeSync;
    if (active != null) return active;

    late final Future<DeviceSyncResult> operation;
    operation = _synchronizeOnce(force: force).whenComplete(() {
'''
new_entry = '''  static Future<DeviceSyncResult> synchronize({
    bool force = false,
    bool? syncMedia,
  }) {
    final active = _activeSync;
    if (active != null) return active;

    late final Future<DeviceSyncResult> operation;
    operation = _synchronizeOnce(
      force: force,
      syncMedia: syncMedia ?? true,
    ).whenComplete(() {
'''
if 'bool? syncMedia' not in text:
    if old_entry not in text:
        raise RuntimeError('Entrada synchronize Android não encontrada')
    text = text.replace(old_entry, new_entry, 1)

old_once = '''  static Future<DeviceSyncResult> _synchronizeOnce({
    required bool force,
  }) async {
'''
new_once = '''  static Future<DeviceSyncResult> _synchronizeOnce({
    required bool force,
    required bool syncMedia,
  }) async {
'''
if 'required bool syncMedia' not in text:
    if old_once not in text:
        raise RuntimeError('_synchronizeOnce Android não encontrado')
    text = text.replace(old_once, new_once, 1)

old_upload = '''      try {
        await MediaSyncService.uploadPending();
      } catch (_) {
        // A falha de uma foto não bloqueia a sincronização dos demais dados.
      }
'''
new_upload = '''      if (syncMedia) {
        try {
          await MediaSyncService.uploadPending();
        } catch (_) {
          // A falha de uma foto não bloqueia a sincronização dos demais dados.
        }
      }
'''
if old_upload in text:
    text = text.replace(old_upload, new_upload, 1)

old_pull_start = '''      var received = 0;
      for (var page = 0; page < 12; page++) {
'''
new_pull_start = '''      var received = 0;
      var remoteHasMore = false;
      const pullPages = 12;
      for (var page = 0; page < pullPages; page++) {
'''
if 'var remoteHasMore = false;' not in text:
    if old_pull_start not in text:
        raise RuntimeError('Loop de pull Android não encontrado')
    text = text.replace(old_pull_start, new_pull_start, 1)

old_has_more = '''        if (response['hasMore'] == true && savedVersion <= since) {
          throw StateError(
            'A Central Online informou mais dados, mas não avançou a versão. '
            'A sincronização foi interrompida para evitar repetição infinita.',
          );
        }
        if (response['hasMore'] != true) break;
'''
new_has_more = '''        if (response['hasMore'] == true && savedVersion <= since) {
          throw StateError(
            'A Central Online informou mais dados, mas não avançou a versão. '
            'A sincronização foi interrompida para evitar repetição infinita.',
          );
        }
        remoteHasMore = response['hasMore'] == true;
        if (!remoteHasMore) break;
'''
if "remoteHasMore = response['hasMore'] == true;" not in text:
    if old_has_more not in text:
        raise RuntimeError('Controle hasMore Android não encontrado')
    text = text.replace(old_has_more, new_has_more, 1)

old_download = '''      try {
        await MediaSyncService.downloadMissing();
      } catch (_) {
        // O download de evidências será tentado novamente no próximo ciclo.
      }

      final now = DateTime.now().toUtc().toIso8601String();
'''
new_download = '''      if (syncMedia) {
        try {
          await MediaSyncService.downloadMissing();
        } catch (_) {
          // O download de evidências será tentado novamente no próximo ciclo.
        }
      }

      final pending = await pendingChangesCount();
      final partial = pending > 0 || remoteHasMore;
      final now = DateTime.now().toUtc().toIso8601String();
'''
if 'final partial = pending > 0 || remoteHasMore;' not in text:
    if old_download not in text:
        raise RuntimeError('Download/final Android não encontrado')
    text = text.replace(old_download, new_download, 1)

old_result_line = '      final result = DeviceSyncResult(sent: sent, received: received);\n'
new_result_line = '''      final result = DeviceSyncResult(
        sent: sent,
        received: received,
        partial: partial,
        pending: pending,
      );
'''
if 'partial: partial' not in text:
    if old_result_line not in text:
        raise RuntimeError('Resultado final Android não encontrado')
    text = text.replace(old_result_line, new_result_line, 1)

path.write_text(text, encoding='utf-8', newline='\n')
assert 'bool? syncMedia' in text
assert 'required bool syncMedia' in text
assert 'var remoteHasMore = false;' in text
assert "remoteHasMore = response['hasMore'] == true;" in text
assert 'final partial = pending > 0 || remoteHasMore;' in text
assert 'partial: partial' in text
print('Compatibilidade Android para progresso real aplicada.')

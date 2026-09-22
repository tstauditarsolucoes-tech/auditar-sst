#!/usr/bin/env python3
"""A truthful non-blocking sync/evidence status card on both Home layouts."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
path=root/'lib/screens/home_screen.dart'
s=path.read_text(encoding='utf-8')

def once(old,new,label):
    global s
    if s.count(old)!=1: raise RuntimeError(f'{label}: {s.count(old)} matches')
    s=s.replace(old,new,1)

once("import '../services/device_sync_service.dart';",
     "import '../services/device_sync_service.dart';\nimport '../services/media_sync_service.dart';\nimport '../services/auth_service.dart';",
     'status imports')
once('  String loadError = \'\';',
     """  String loadError = '';
  int _pendingStructured = 0;
  int _pendingEvidence = 0;
  String _structuredSyncError = '';
  String _evidenceSyncError = '';
  bool _syncStatusRefreshing = false;
  bool _sendingEvidence = false;""",
     'status fields')

once("""    _deviceSyncSubscription = DeviceSyncService.events.listen((result) {
      if (!mounted || result.received <= 0) return;""",
     """    _deviceSyncSubscription = DeviceSyncService.events.listen((result) {
      if (!mounted) return;
      if (result.mediaChanged) unawaited(_refreshSyncStatus());
      if (result.received <= 0) return;""",
     'media event UI')

once("""        loadError = '';
      });
    } catch (e) {""",
     """        loadError = '';
      });
      unawaited(_refreshSyncStatus());
    } catch (e) {""",
     'refresh status without blocking Home')

anchor='  Future<void> _open(Widget page, {String? tutorialId}) async {'
if s.count(anchor)!=1: raise RuntimeError('home open anchor')
insert=r'''  Future<void> _refreshSyncStatus() async {
    if (!mounted || !AuthService.isSignedIn || _syncStatusRefreshing) return;
    _syncStatusRefreshing = true;
    try {
      final db = AppDatabase.instance;
      final structured = await DeviceSyncService.pendingChangesCount()
          .timeout(const Duration(seconds: 8));
      final evidence = await MediaSyncService.pendingCount()
          .timeout(const Duration(seconds: 8));
      final structuredError = await db.getSetting('last_device_sync_error');
      final evidenceError = await db.getSetting('media_sync_last_error');
      if (!mounted) return;
      setState(() {
        _pendingStructured = structured;
        _pendingEvidence = evidence;
        _structuredSyncError = structuredError.trim();
        _evidenceSyncError = evidenceError.trim();
      });
    } catch (_) {
      // Keep previously displayed counters rather than showing a false zero.
    } finally {
      _syncStatusRefreshing = false;
    }
  }

  Future<void> _retryEvidenceUpload() async {
    if (_sendingEvidence || !AuthService.isSignedIn) return;
    setState(() => _sendingEvidence = true);
    try {
      await DeviceSyncService.sendPendingMediaNow();
      await _refreshSyncStatus();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(_pendingEvidence == 0
            ? 'Envio local de fotos e assinaturas concluído.'
            : 'Ainda há $_pendingEvidence evidência(s) na fila. '
              'O app continuará tentando em segundo plano.'),
      ));
    } finally {
      if (mounted) setState(() => _sendingEvidence = false);
    }
  }

  Widget _syncQueueCard() {
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(children: [
              Icon(Icons.cloud_sync_outlined, size: 20),
              SizedBox(width: 8),
              Expanded(child: Text(
                'Sincronização e evidências',
                style: TextStyle(fontWeight: FontWeight.w800),
              )),
            ]),
            const SizedBox(height: 7),
            Text('Dados locais aguardando envio: $_pendingStructured'),
            Text('Fotos e assinaturas aguardando envio: $_pendingEvidence'),
            if (_structuredSyncError.isNotEmpty)
              Text('Dados: $_structuredSyncError',
                  style: const TextStyle(color: Colors.deepOrange)),
            if (_evidenceSyncError.isNotEmpty)
              Text('Evidências: $_evidenceSyncError',
                  style: const TextStyle(color: Colors.deepOrange)),
            if (_pendingEvidence > 0) ...[
              const SizedBox(height: 6),
              OutlinedButton.icon(
                onPressed: _sendingEvidence ? null : _retryEvidenceUpload,
                icon: _sendingEvidence
                    ? const SizedBox(
                        width: 16, height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.cloud_upload_outlined),
                label: Text(_sendingEvidence
                    ? 'Enviando evidências...'
                    : 'Tentar enviar evidências agora'),
              ),
            ],
            const SizedBox(height: 3),
            const Text(
              'Os indicadores mostram somente a fila deste aparelho. '
              'Fotos não enviadas continuam armazenadas localmente.',
              style: TextStyle(fontSize: 11, color: Colors.black54),
            ),
          ],
        ),
      ),
    );
  }

'''
s=s.replace(anchor,insert+anchor,1)
once("""          _overviewPanel(desktop: false),
          const SizedBox(height: 12),
          _continueInspectionCard(),""",
     """          _overviewPanel(desktop: false),
          const SizedBox(height: 12),
          _syncQueueCard(),
          const SizedBox(height: 12),
          _continueInspectionCard(),""", 'mobile card')
once("""                  _overviewPanel(desktop: true),
                  const SizedBox(height: 14),
                  _continueInspectionCard(),""",
     """                  _overviewPanel(desktop: true),
                  const SizedBox(height: 14),
                  _syncQueueCard(),
                  const SizedBox(height: 14),
                  _continueInspectionCard(),""",'desktop card')

path.write_text(s,encoding='utf-8',newline='\n')
print('HOME_SYNC_QUEUE_UI_OK')

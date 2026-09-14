#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
if platform not in {'android', 'windows'}:
    raise SystemExit('Uso: patch_sync_queue_media_separation_v32940_32944.py <app_dir> <android|windows>')

pubp = root / 'pubspec.yaml'
syncp = root / 'lib/services/device_sync_service.dart'
mediap = root / 'lib/services/media_sync_service.dart'
coordp = root / 'lib/services/sync_coordinator.dart'
screenp = root / 'lib/screens/data_safety_screen.dart'

pub = pubp.read_text(encoding='utf-8')
sync = syncp.read_text(encoding='utf-8')
media = mediap.read_text(encoding='utf-8')
coord = coordp.read_text(encoding='utf-8')
screen = screenp.read_text(encoding='utf-8')

expected = 'version: 3.29.39+181' if platform == 'android' else 'version: 3.29.43+185'
target = 'version: 3.29.40+182' if platform == 'android' else 'version: 3.29.44+186'
if target not in pub:
    if expected not in pub:
        raise RuntimeError(f'Versão base ausente: {expected}')
    pub = pub.replace(expected, target, 1)

# 1) media_assets continua aceito no PULL por compatibilidade, mas sai da fila
# outbound. Fotos, assinaturas e logos usam MediaSyncService/Google Drive.
old_outbound = '  static Set<String> get _outboundTables => _allTables;'
new_outbound = "  static Set<String> get _outboundTables => {..._allTables}..remove('media_assets');"
if old_outbound in sync:
    sync = sync.replace(old_outbound, new_outbound, 1)
elif new_outbound not in sync:
    raise RuntimeError('Getter _outboundTables não localizado')

old_pending = """    final result = await db.rawQuery(
      'SELECT COUNT(*) FROM $_changesTable WHERE dirty = 1',
    );
"""
new_pending = """    final tables = _outboundTables.toList()..sort();
    if (tables.isEmpty) return 0;
    final placeholders = List.filled(tables.length, '?').join(',');
    final result = await db.rawQuery(
      'SELECT COUNT(*) FROM $_changesTable '
      'WHERE dirty = 1 AND table_name IN ($placeholders)',
      tables,
    );
"""
if old_pending in sync:
    sync = sync.replace(old_pending, new_pending, 1)
elif "WHERE dirty = 1 AND table_name IN ($placeholders)" not in sync:
    raise RuntimeError('pendingChangesCount não localizado')

helper = r'''  static Future<void> _discardMediaAssetChanges(Database db) async {
    for (final suffix in const ['insert', 'update', 'delete']) {
      await db.execute('DROP TRIGGER IF EXISTS device_sync_media_assets_$suffix');
    }
    await db.delete(
      _changesTable,
      where: "table_name = 'media_assets'",
    );
    try {
      await db.delete(
        'device_sync_scopes',
        where: "table_name = 'media_assets'",
      );
    } catch (_) {}
  }

'''
marker = '  static Future<void> _discardBuiltInChecklistChanges(Database db) async {'
if '_discardMediaAssetChanges(Database db)' not in sync:
    if marker not in sync:
        raise RuntimeError('Marcador de descarte não localizado')
    sync = sync.replace(marker, helper + marker, 1)

sync = sync.replace(
    "        await _discardBuiltInChecklistChanges(db);\n        return;",
    "        await _discardMediaAssetChanges(db);\n        await _discardBuiltInChecklistChanges(db);\n        return;",
    1,
)
sync = sync.replace(
    "    await _discardBuiltInChecklistChanges(db);\n    _changeTrackingReady = true;",
    "    await _discardMediaAssetChanges(db);\n    await _discardBuiltInChecklistChanges(db);\n    _changeTrackingReady = true;",
    1,
)

# Evita repetição agressiva de tentativas automáticas. Manual force:true segue imediato.
sync = sync.replace(
    '        const Duration(seconds: 15);',
    '        const Duration(seconds: 60);',
    1,
)

# 2) Timer rápido só usa rede quando realmente existe alteração local.
early_marker = '''  Future<void> _trySync({bool deviceOnly = false}) async {
    if (_syncing || _maintenanceBusy || !AuthService.isSignedIn) return;
    final nextAttempt = _nextSyncAttempt;
'''
early_replacement = '''  Future<void> _trySync({bool deviceOnly = false}) async {
    if (_syncing || _maintenanceBusy || !AuthService.isSignedIn) return;

    if (deviceOnly) {
      try {
        final localPending = await DeviceSyncService.pendingChangesCount();
        if (localPending == 0) return;
      } catch (_) {
        return;
      }
    }

    final nextAttempt = _nextSyncAttempt;
'''
if 'final localPending = await DeviceSyncService.pendingChangesCount();' not in coord:
    if early_marker not in coord:
        raise RuntimeError('Início de _trySync não localizado')
    coord = coord.replace(early_marker, early_replacement, 1)

# 3) Indicador geral do Windows: porcentagem pequena no lugar do spinner.
if 'StreamSubscription<DeviceSyncProgress>? _progressSubscription;' not in coord:
    coord = coord.replace(
        '  StreamSubscription<List<ConnectivityResult>>? _subscription;\n',
        '  StreamSubscription<List<ConnectivityResult>>? _subscription;\n'
        '  StreamSubscription<DeviceSyncProgress>? _progressSubscription;\n',
        1,
    )
if '  int _syncPercent = 0;' not in coord:
    coord = coord.replace(
        '  bool _showIndicator = false;\n',
        '  bool _showIndicator = false;\n  int _syncPercent = 0;\n',
        1,
    )

listen_marker = '''    _subscription = Connectivity()
        .onConnectivityChanged
        .listen(_handleConnectivity);
'''
listen_replacement = '''    _subscription = Connectivity()
        .onConnectivityChanged
        .listen(_handleConnectivity);

    final initialProgress = DeviceSyncService.lastProgress;
    _syncPercent = initialProgress.percent.clamp(0, 100).toInt();
    _progressSubscription = DeviceSyncService.progressEvents.listen((progress) {
      if (!mounted) return;
      setState(() {
        _syncPercent = progress.percent.clamp(0, 100).toInt();
      });
    });
'''
if 'final initialProgress = DeviceSyncService.lastProgress;' not in coord:
    if listen_marker not in coord:
        raise RuntimeError('Listener de conectividade não localizado')
    coord = coord.replace(listen_marker, listen_replacement, 1)

if '_progressSubscription?.cancel();' not in coord:
    coord = coord.replace(
        '    _subscription?.cancel();\n',
        '    _subscription?.cancel();\n    _progressSubscription?.cancel();\n',
        1,
    )

if 'percent: _syncPercent,' not in coord:
    coord = coord.replace(
        '''            child: _SyncIndicator(
              label: _statusLabel,
              tone: _statusTone,
            ),''',
        '''            child: _SyncIndicator(
              label: _statusLabel,
              tone: _statusTone,
              percent: _syncPercent,
            ),''',
        1,
    )

if 'final int percent;' not in coord:
    coord = coord.replace(
        '''class _SyncIndicator extends StatelessWidget {
  final String label;
  final _SyncTone tone;
''',
        '''class _SyncIndicator extends StatelessWidget {
  final String label;
  final _SyncTone tone;
  final int percent;
''',
        1,
    )
    coord = coord.replace(
        '''  const _SyncIndicator({
    required this.label,
    required this.tone,
  });''',
        '''  const _SyncIndicator({
    required this.label,
    required this.tone,
    required this.percent,
  });''',
        1,
    )

spinner = '''            if (tone == _SyncTone.syncing)
              SizedBox(
                width: 15,
                height: 15,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: foreground,
                ),
              )
            else
              Icon(icon, size: 17, color: foreground),'''
percentage = '''            if (tone == _SyncTone.syncing)
              Text(
                '${percent.clamp(0, 100)}%',
                style: TextStyle(
                  color: foreground,
                  fontSize: percent >= 100 ? 8.0 : 9.5,
                  fontWeight: FontWeight.w900,
                ),
              )
            else
              Icon(icon, size: 17, color: foreground),'''
if 'CircularProgressIndicator(' in coord and "'${percent.clamp(0, 100)}%'" not in coord:
    if spinner not in coord:
        raise RuntimeError('Spinner do indicador global não localizado')
    coord = coord.replace(spinner, percentage, 1)

# A barra grande criada na tela Segurança dos dados é removida. O percentual
# permanece no botão de sincronização e, no PC, no indicador global compacto.
screen = screen.replace(
    '''            _syncProgressCard(),
            if (syncRunning || syncPercent > 0) const SizedBox(height: 2),
''',
    '',
    1,
)

# 4) Caminhos locais são cache e não devem recriar dirty nas tabelas principais.
if '_localOnlyPathUpdate(' not in media:
    helper_marker = '  static Future<void> _applyEntityPath('
    local_helper = r'''  static Future<void> _localOnlyPathUpdate(
    Database db, {
    required String table,
    required String recordId,
    required Map<String, Object?> values,
  }) async {
    if (recordId.trim().isEmpty) return;
    Map<String, Object?>? previous;
    var trackingAvailable = false;
    try {
      final rows = await db.query(
        'device_sync_changes',
        where: 'table_name = ? AND record_id = ?',
        whereArgs: [table, recordId],
        limit: 1,
      );
      trackingAvailable = true;
      if (rows.isNotEmpty) previous = Map<String, Object?>.from(rows.first);
    } catch (_) {}

    await db.update(table, values, where: 'id = ?', whereArgs: [recordId]);

    if (!trackingAvailable) return;
    try {
      if (previous == null) {
        await db.delete(
          'device_sync_changes',
          where: 'table_name = ? AND record_id = ?',
          whereArgs: [table, recordId],
        );
      } else {
        await db.update(
          'device_sync_changes',
          {
            'local_version': previous['local_version'],
            'dirty': previous['dirty'],
            'deleted': previous['deleted'],
          },
          where: 'table_name = ? AND record_id = ?',
          whereArgs: [table, recordId],
        );
      }
    } catch (_) {}
  }

'''
    if helper_marker not in media:
        raise RuntimeError('Marcador _applyEntityPath não localizado')
    media = media.replace(helper_marker, local_helper + helper_marker, 1)

pattern = re.compile(
    r"  static Future<void> _applyEntityPath\([\s\S]*?\n  static Future<Map<String, dynamic>> _post\(",
    re.MULTILINE,
)
match = pattern.search(media)
if not match:
    raise RuntimeError('Função _applyEntityPath não localizada')
block = match.group(0)
if 'await _localOnlyPathUpdate(' not in block:
    new_apply = r'''  static Future<void> _applyEntityPath(
    Database db,
    Map<String, Object?> row,
    String path,
  ) async {
    final entityType = '${row['entity_type'] ?? ''}'.trim();
    final entityId = '${row['entity_id'] ?? ''}'.trim();
    if (entityId.isEmpty) return;

    if (entityType == 'evidence_photo') {
      await _localOnlyPathUpdate(
        db,
        table: 'evidence_photos',
        recordId: entityId,
        values: {'path': path},
      );
    } else if (entityType == 'completion_photo') {
      await _localOnlyPathUpdate(
        db,
        table: 'completion_photos',
        recordId: entityId,
        values: {'path': path},
      );
    } else if (entityType == 'technician_signature') {
      await _localOnlyPathUpdate(
        db,
        table: 'inspections',
        recordId: entityId,
        values: {'technician_signature_path': path},
      );
    } else if (entityType == 'responsible_signature') {
      await _localOnlyPathUpdate(
        db,
        table: 'inspections',
        recordId: entityId,
        values: {'responsible_signature_path': path},
      );
    } else if (entityType == 'company_logo') {
      await _localOnlyPathUpdate(
        db,
        table: 'companies',
        recordId: entityId,
        values: {'logo_path': path},
      );
    }
  }

  static Future<Map<String, dynamic>> _post('''
    media = media[:match.start()] + new_apply + media[match.end():]

pubp.write_text(pub, encoding='utf-8', newline='\n')
syncp.write_text(sync, encoding='utf-8', newline='\n')
mediap.write_text(media, encoding='utf-8', newline='\n')
coordp.write_text(coord, encoding='utf-8', newline='\n')
screenp.write_text(screen, encoding='utf-8', newline='\n')

final_sync = syncp.read_text(encoding='utf-8')
final_media = mediap.read_text(encoding='utf-8')
final_coord = coordp.read_text(encoding='utf-8')
final_screen = screenp.read_text(encoding='utf-8')
assert target in pubp.read_text(encoding='utf-8')
assert "remove('media_assets')" in final_sync
assert '_discardMediaAssetChanges' in final_sync
assert "table_name = 'media_assets'" in final_sync
assert 'WHERE dirty = 1 AND table_name IN ($placeholders)' in final_sync
assert 'const Duration(seconds: 60)' in final_sync
assert '_localOnlyPathUpdate' in final_media
assert 'final localPending = await DeviceSyncService.pendingChangesCount();' in final_coord
assert 'if (localPending == 0) return;' in final_coord
if platform == 'windows':
    assert 'percent: _syncPercent' in final_coord
    assert "'${percent.clamp(0, 100)}%'" in final_coord
assert '            _syncProgressCard(),' not in final_screen
print(f'{target}: fila 9 corrigida, auto-sync ocioso desativado e progresso compacto aplicado.')

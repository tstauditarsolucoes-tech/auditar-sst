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

pub = pubp.read_text(encoding='utf-8')
sync = syncp.read_text(encoding='utf-8')
media = mediap.read_text(encoding='utf-8')

expected = 'version: 3.29.39+181' if platform == 'android' else 'version: 3.29.43+185'
target = 'version: 3.29.40+182' if platform == 'android' else 'version: 3.29.44+186'
if target not in pub:
    if expected not in pub:
        raise RuntimeError(f'Versão base ausente: {expected}')
    pub = pub.replace(expected, target, 1)

# ---------------------------------------------------------------------------
# 1) O catálogo de mídia NÃO pertence à fila de dados estruturados.
# Fotos, assinaturas e logos já têm MediaSyncService + Drive próprios.
# Manter media_assets no device_sync gerava o ciclo 9 -> 0 -> 9 porque o
# próprio upload/download atualiza drive_file_id/updated_at/local_path.
# ---------------------------------------------------------------------------
old_all = "  static Set<String> get _allTables => {..._masterTables, ..._fieldTables};"
new_all = "  static Set<String> get _allTables => {..._masterTables, ..._fieldTables}..remove('media_assets');"
if old_all in sync:
    sync = sync.replace(old_all, new_all, 1)
elif new_all not in sync:
    raise RuntimeError('Getter _allTables não localizado')

# pendingChangesCount deve contar somente tabelas realmente publicáveis.
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

# Limpa a fila antiga e remove triggers persistentes já existentes no banco.
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

# Em qualquer caminho de _ensureChangeTracking, limpar mídia antiga antes de
# calcular a fila. Isso resolve instalações que já possuem os 9 dirty antigos.
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

# ---------------------------------------------------------------------------
# 2) Caminhos locais são cache do dispositivo. No Android antigo ainda havia
# updates normais em path/logo_path que podiam gerar dirty. Reaproveitamos a
# proteção já usada no Windows v3.29.43 também no Android.
# ---------------------------------------------------------------------------
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

# Troca a função _applyEntityPath inteira somente se ainda usar db.update direto.
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

final_sync = syncp.read_text(encoding='utf-8')
final_media = mediap.read_text(encoding='utf-8')
assert target in pubp.read_text(encoding='utf-8')
assert "..remove('media_assets')" in final_sync
assert '_discardMediaAssetChanges' in final_sync
assert "table_name = 'media_assets'" in final_sync
assert 'WHERE dirty = 1 AND table_name IN ($placeholders)' in final_sync
assert '_localOnlyPathUpdate' in final_media
print(f'{target}: mídia separada da fila estruturada; pendências antigas de media_assets serão limpas.')

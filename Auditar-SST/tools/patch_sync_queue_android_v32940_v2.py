#!/usr/bin/env python3
from pathlib import Path
import re, sys

root=Path(sys.argv[1])
pubp=root/'pubspec.yaml'; syncp=root/'lib/services/device_sync_service.dart'; mediap=root/'lib/services/media_sync_service.dart'; coordp=root/'lib/services/sync_coordinator.dart'
pub=pubp.read_text(encoding='utf-8'); sync=syncp.read_text(encoding='utf-8'); media=mediap.read_text(encoding='utf-8'); coord=coordp.read_text(encoding='utf-8')

def once(text, old, new, label):
    if old not in text: raise RuntimeError(f'Marcador ausente: {label}')
    return text.replace(old,new,1)

if 'version: 3.29.40+182' not in pub:
    pub=once(pub,'version: 3.29.38+180','version: 3.29.40+182','versão')

# Catálogo de mídia fica fora da fila estruturada. Ele já é sincronizado pelo Drive.
sync=once(sync,
    '  static Set<String> get _outboundTables => _allTables;',
    "  static Set<String> get _outboundTables => {..._allTables}..remove('media_assets');",
    'outbound tables')

sync=once(sync,
"""    final result = await db.rawQuery(
      'SELECT COUNT(*) FROM $_changesTable WHERE dirty = 1',
    );
""",
"""    final tables = _outboundTables.toList()..sort();
    if (tables.isEmpty) return 0;
    final placeholders = List.filled(tables.length, '?').join(',');
    final result = await db.rawQuery(
      'SELECT COUNT(*) FROM $_changesTable '
      'WHERE dirty = 1 AND table_name IN ($placeholders)',
      tables,
    );
""",'contador de pendências')

cleanup=r'''  static Future<void> _discardMediaAssetChanges(Database db) async {
    for (final suffix in const ['insert', 'update', 'delete']) {
      await db.execute('DROP TRIGGER IF EXISTS device_sync_media_assets_$suffix');
    }
    await db.delete(_changesTable, where: "table_name = 'media_assets'");
    try {
      await db.delete('device_sync_scopes', where: "table_name = 'media_assets'");
    } catch (_) {}
  }

'''
marker='  static Future<void> _discardBuiltInChecklistChanges(Database db) async {'
if '_discardMediaAssetChanges(Database db)' not in sync:
    if marker not in sync: raise RuntimeError('Marcador discardBuiltIn não encontrado')
    sync=sync.replace(marker,cleanup+marker,1)

# Limpa instalações existentes e elimina os triggers antigos de media_assets.
old="        await _discardBuiltInChecklistChanges(db);\n        return;"
if old in sync:
    sync=sync.replace(old,"        await _discardMediaAssetChanges(db);\n        await _discardBuiltInChecklistChanges(db);\n        return;",1)
old="    await _discardBuiltInChecklistChanges(db);\n    _changeTrackingReady = true;"
if old in sync:
    sync=sync.replace(old,"    await _discardMediaAssetChanges(db);\n    await _discardBuiltInChecklistChanges(db);\n    _changeTrackingReady = true;",1)
if sync.count('_discardMediaAssetChanges(db);') < 2:
    raise RuntimeError('Limpeza de media_assets não foi ligada aos dois caminhos')

sync=once(sync,'        const Duration(seconds: 15);','        const Duration(seconds: 60);','janela de tentativa')

# O timer de 45s só abre rede quando existe alteração local real.
coord=once(coord,
"""  Future<void> _trySync({bool deviceOnly = false}) async {
    if (_syncing || !AuthService.isSignedIn) return;

    final connectivity = await Connectivity().checkConnectivity();
""",
"""  Future<void> _trySync({bool deviceOnly = false}) async {
    if (_syncing || !AuthService.isSignedIn) return;

    if (deviceOnly) {
      try {
        final localPending = await DeviceSyncService.pendingChangesCount();
        if (localPending == 0) return;
      } catch (_) {
        return;
      }
    }

    final connectivity = await Connectivity().checkConnectivity();
""",'gate do auto-sync Android')

# Atualizar caminhos locais não é uma alteração de negócio. Preserve o dirty anterior.
if '_localOnlyPathUpdate(' not in media:
    helper=r'''  static Future<void> _localOnlyPathUpdate(
    Database db, {
    required String table,
    required String recordId,
    required Map<String, Object?> values,
  }) async {
    if (recordId.trim().isEmpty) return;
    Map<String, Object?>? previous;
    var trackingAvailable=false;
    try {
      final rows=await db.query('device_sync_changes',where:'table_name = ? AND record_id = ?',whereArgs:[table,recordId],limit:1);
      trackingAvailable=true;
      if(rows.isNotEmpty) previous=Map<String,Object?>.from(rows.first);
    } catch (_) {}
    await db.update(table,values,where:'id = ?',whereArgs:[recordId]);
    if(!trackingAvailable) return;
    try {
      if(previous==null){
        await db.delete('device_sync_changes',where:'table_name = ? AND record_id = ?',whereArgs:[table,recordId]);
      } else {
        await db.update('device_sync_changes',{
          'local_version':previous['local_version'],'dirty':previous['dirty'],'deleted':previous['deleted'],
        },where:'table_name = ? AND record_id = ?',whereArgs:[table,recordId]);
      }
    } catch (_) {}
  }

'''
    pos=media.find('  static Future<void> _applyEntityPath(')
    if pos<0: raise RuntimeError('_applyEntityPath ausente')
    media=media[:pos]+helper+media[pos:]

pat=re.compile(r"  static Future<void> _applyEntityPath\([\s\S]*?\n  static Future<Map<String, dynamic>> _post\(",re.M)
m=pat.search(media)
if not m: raise RuntimeError('Bloco _applyEntityPath ausente')
new_apply=r'''  static Future<void> _applyEntityPath(
    Database db,
    Map<String, Object?> row,
    String path,
  ) async {
    final entityType='${row['entity_type'] ?? ''}'.trim();
    final entityId='${row['entity_id'] ?? ''}'.trim();
    if(entityId.isEmpty)return;
    if(entityType=='evidence_photo'){
      await _localOnlyPathUpdate(db,table:'evidence_photos',recordId:entityId,values:{'path':path});
    }else if(entityType=='completion_photo'){
      await _localOnlyPathUpdate(db,table:'completion_photos',recordId:entityId,values:{'path':path});
    }else if(entityType=='technician_signature'){
      await _localOnlyPathUpdate(db,table:'inspections',recordId:entityId,values:{'technician_signature_path':path});
    }else if(entityType=='responsible_signature'){
      await _localOnlyPathUpdate(db,table:'inspections',recordId:entityId,values:{'responsible_signature_path':path});
    }else if(entityType=='company_logo'){
      await _localOnlyPathUpdate(db,table:'companies',recordId:entityId,values:{'logo_path':path});
    }
  }

  static Future<Map<String, dynamic>> _post('''
media=media[:m.start()]+new_apply+media[m.end():]

pubp.write_text(pub,encoding='utf-8',newline='\n'); syncp.write_text(sync,encoding='utf-8',newline='\n'); mediap.write_text(media,encoding='utf-8',newline='\n'); coordp.write_text(coord,encoding='utf-8',newline='\n')

assert 'version: 3.29.40+182' in pub
assert "_outboundTables => {..._allTables}..remove('media_assets')" in sync
assert "WHERE dirty = 1 AND table_name IN ($placeholders)" in sync
assert sync.count('_discardMediaAssetChanges(db);') >= 2
assert 'if (localPending == 0) return;' in coord
assert '_localOnlyPathUpdate' in media
print('Android v3.29.40+182: fila 9 removida e sincronização rápida ociosa desativada; telas não alteradas.')

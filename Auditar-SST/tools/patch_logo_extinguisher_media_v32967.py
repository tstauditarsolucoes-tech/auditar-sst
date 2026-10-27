#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/Auditar_SST_v1_5_dashboard')
pubp = root / 'pubspec.yaml'
companiesp = root / 'lib/screens/companies_screen.dart'
extp = root / 'lib/screens/extinguishers_screen.dart'
mediap = root / 'lib/services/media_sync_service.dart'

pub = pubp.read_text(encoding='utf-8')
companies = companiesp.read_text(encoding='utf-8')
ext = extp.read_text(encoding='utf-8')
media = mediap.read_text(encoding='utf-8')

def once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Marcador ausente: {label}')
    return text.replace(old, new, 1)

pub, n = re.subn(r'^version:\s*[^\n]+', 'version: 3.29.67+209', pub, count=1, flags=re.M)
if n != 1:
    raise RuntimeError('Versão não localizada')

old_load = """    Future.delayed(const Duration(seconds: 15), () {
      if (!mounted) return;
      _restoreMissingCompanyLogos(result);
    });
"""
new_load = """    // Renderiza a lista primeiro; restaura as logos em segundo plano.
    unawaited(_restoreMissingCompanyLogos(result));
"""
companies = once(companies, old_load, new_load, 'disparo tardio das logos')

old_restore = """      final restored = await MediaSyncService.restoreCompanyLogos(
        companyIds: missing.take(1),
      ).timeout(const Duration(seconds: 12));
"""
new_restore = """      final restored = await MediaSyncService.restoreCompanyLogos(
        companyIds: missing,
      ).timeout(const Duration(seconds: 45));
"""
companies = once(companies, old_restore, new_restore, 'restauração de uma única logo')

media_marker = """  static Future<void> registerCompanyLogo({required String companyId, required String localPath}) async {
"""
media_helpers = """  static Future<void> registerExtinguisherPhoto({
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
    final mediaId = _assetId('extinguisher_photo', cleanRecordId);
    final existing = await db.query(
      'media_assets',
      where: 'id = ?',
      whereArgs: [mediaId],
      limit: 1,
    );
    final now = DateTime.now().toUtc().toIso8601String();

    if (existing.isEmpty) {
      await db.insert(
        'media_assets',
        {
          'id': mediaId,
          'company_id': cleanCompanyId,
          'entity_type': 'extinguisher_photo',
          'entity_id': cleanRecordId,
          'local_path': cleanPath,
          'drive_file_id': '',
          'file_name': p.basename(cleanPath),
          'mime_type': _mimeTypeFor(cleanPath),
          'updated_at': now,
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
      return;
    }

    final current = existing.first;
    final previousPath = '${current['local_path'] ?? ''}'.trim();
    final changed = previousPath != cleanPath;
    await db.update(
      'media_assets',
      {
        'company_id': cleanCompanyId,
        'entity_type': 'extinguisher_photo',
        'entity_id': cleanRecordId,
        'local_path': cleanPath,
        'file_name': p.basename(cleanPath),
        'mime_type': _mimeTypeFor(cleanPath),
        'updated_at': now,
        if (changed) 'drive_file_id': '',
      },
      where: 'id = ?',
      whereArgs: [mediaId],
    );
  }

  static Future<int> restoreExtinguisherPhotos({
    required String companyId,
    required Iterable<String> recordIds,
  }) async {
    if (!AuthService.isSignedIn) return 0;
    final ids = recordIds
        .map((id) => id.trim())
        .where((id) => id.isNotEmpty)
        .toSet()
        .toList();
    if (ids.isEmpty) return 0;
    final db = await AppDatabase.instance.database;
    return _restoreEntities(
      db,
      companyId,
      ids
          .map((id) => <String, String>{
                'type': 'extinguisher_photo',
                'id': id,
              })
          .toList(),
    );
  }

"""
if 'registerExtinguisherPhoto({' not in media:
    media = once(media, media_marker, media_helpers + media_marker, 'helpers de mídia do extintor')

old_apply = """    }else if(entityType=='company_logo'){
      await _localOnlyPathUpdate(db,table:'companies',recordId:entityId,values:{'logo_path':path});
    }
"""
new_apply = """    }else if(entityType=='company_logo'){
      await _localOnlyPathUpdate(db,table:'companies',recordId:entityId,values:{'logo_path':path});
    }else if(entityType=='extinguisher_photo'){
      final rows = await db.query(
        'sst_records',
        columns: ['payload'],
        where: 'id = ?',
        whereArgs: [entityId],
        limit: 1,
      );
      if (rows.isNotEmpty) {
        Map<String, dynamic> payload = <String, dynamic>{};
        final rawPayload = '${rows.first['payload'] ?? ''}'.trim();
        if (rawPayload.isNotEmpty) {
          try {
            final decoded = jsonDecode(rawPayload);
            if (decoded is Map) {
              payload = Map<String, dynamic>.from(decoded);
            }
          } catch (_) {}
        }
        payload['photoPath'] = path;
        await _localOnlyPathUpdate(
          db,
          table: 'sst_records',
          recordId: entityId,
          values: {'payload': jsonEncode(payload)},
        );
      }
    }
"""
media = once(media, old_apply, new_apply, 'aplicação local da foto de extintor')

if "import 'dart:async';" not in ext:
    ext = once(ext, "import 'dart:io';\n", "import 'dart:async';\nimport 'dart:io';\n", 'dart async')
if "import '../services/media_sync_service.dart';" not in ext:
    ext = once(
        ext,
        "import '../services/management_panel_service.dart';\n",
        "import '../services/management_panel_service.dart';\nimport '../services/media_sync_service.dart';\n",
        'import MediaSyncService',
    )

old_load_ext = """    setState(() {
      records = results[0] as List<SstRecord>;
      sectors = results[1] as List<Sector>;
      loading = false;
    });
  }
"""
new_load_ext = """    final loadedRecords = results[0] as List<SstRecord>;
    setState(() {
      records = loadedRecords;
      sectors = results[1] as List<Sector>;
      loading = false;
    });
    unawaited(_protectAndRestoreExtinguisherPhotos(loadedRecords));
  }

  Future<void> _protectAndRestoreExtinguisherPhotos(
    List<SstRecord> snapshot,
  ) async {
    final missing = <String>[];
    var hasLocalPhotos = false;

    for (final record in snapshot) {
      final path = '${record.payload['photoPath'] ?? ''}'.trim();
      if (path.isNotEmpty && File(path).existsSync()) {
        hasLocalPhotos = true;
        try {
          await MediaSyncService.registerExtinguisherPhoto(
            companyId: widget.company.id,
            recordId: record.id,
            localPath: path,
          );
        } catch (_) {}
      } else {
        missing.add(record.id);
      }
    }

    if (hasLocalPhotos) {
      unawaited(MediaSyncService.uploadPending());
    }

    if (missing.isEmpty) return;
    try {
      final restored = await MediaSyncService.restoreExtinguisherPhotos(
        companyId: widget.company.id,
        recordIds: missing,
      ).timeout(const Duration(seconds: 45));
      if (restored <= 0 || !mounted) return;

      final refreshed = await AppDatabase.instance.getSstRecords(
        type: 'EXTINTOR',
        companyId: widget.company.id,
      );
      if (!mounted) return;
      setState(() => records = refreshed);
    } catch (_) {
      // Foto ausente não bloqueia cadastro/lista.
    }
  }

  void _showExtinguisherPhoto(String path) {
    final clean = path.trim();
    if (clean.isEmpty || !File(clean).existsSync()) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('A foto deste extintor ainda não está disponível neste aparelho.'),
        ),
      );
      return;
    }
    showDialog<void>(
      context: context,
      builder: (context) => Dialog(
        insetPadding: const EdgeInsets.all(16),
        child: Stack(
          children: [
            Padding(
              padding: const EdgeInsets.all(12),
              child: InteractiveViewer(
                minScale: 0.8,
                maxScale: 5,
                child: Image.file(
                  File(clean),
                  fit: BoxFit.contain,
                  width: double.infinity,
                ),
              ),
            ),
            Positioned(
              right: 4,
              top: 4,
              child: IconButton(
                tooltip: 'Fechar',
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.close_rounded),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _extinguisherPhotoOrIcon(SstRecord record, Color color) {
    final path = '${record.payload['photoPath'] ?? ''}'.trim();
    final available = path.isNotEmpty && File(path).existsSync();
    if (!available) {
      return Container(
        width: 52,
        height: 52,
        decoration: BoxDecoration(
          color: color.withValues(alpha: .10),
          borderRadius: BorderRadius.circular(13),
        ),
        child: Icon(Icons.fire_extinguisher_rounded, color: color),
      );
    }

    return Tooltip(
      message: 'Ver foto do local',
      child: InkWell(
        borderRadius: BorderRadius.circular(13),
        onTap: () => _showExtinguisherPhoto(path),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(13),
          child: SizedBox(
            width: 52,
            height: 52,
            child: Image.file(
              File(path),
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => Container(
                color: color.withValues(alpha: .10),
                alignment: Alignment.center,
                child: Icon(Icons.fire_extinguisher_rounded, color: color),
              ),
            ),
          ),
        ),
      ),
    );
  }
"""
ext = once(ext, old_load_ext, new_load_ext, 'load dos extintores')

old_icon = """                                Container(
                                  width: 48,
                                  height: 48,
                                  decoration: BoxDecoration(
                                    color: color.withValues(alpha: .10),
                                    borderRadius: BorderRadius.circular(13),
                                  ),
                                  child: Icon(
                                    Icons.fire_extinguisher_rounded,
                                    color: color,
                                  ),
                                ),
"""
ext = once(ext, old_icon, "                                _extinguisherPhotoOrIcon(record, color),\n", 'ícone do card')

old_select = """                                  onSelected: (value) {
                                    if (value == 'edit') _edit(record);
                                    if (value == 'toggle_empty') {
                                      _toggleLocationEmpty(record);
                                    }
                                    if (value == 'delete') _delete(record);
                                  },
"""
new_select = """                                  onSelected: (value) {
                                    if (value == 'edit') _edit(record);
                                    if (value == 'photo') {
                                      _showExtinguisherPhoto(
                                        '${p['photoPath'] ?? ''}',
                                      );
                                    }
                                    if (value == 'toggle_empty') {
                                      _toggleLocationEmpty(record);
                                    }
                                    if (value == 'delete') _delete(record);
                                  },
"""
ext = once(ext, old_select, new_select, 'menu do card')

old_items = """                                  itemBuilder: (_) => [
                                    const PopupMenuItem(
                                      value: 'edit',
                                      child: Text('Editar'),
                                    ),
"""
new_items = """                                  itemBuilder: (_) => [
                                    const PopupMenuItem(
                                      value: 'edit',
                                      child: Text('Editar'),
                                    ),
                                    if ('${p['photoPath'] ?? ''}'.trim().isNotEmpty)
                                      const PopupMenuItem(
                                        value: 'photo',
                                        child: ListTile(
                                          contentPadding: EdgeInsets.zero,
                                          leading: Icon(Icons.photo_outlined),
                                          title: Text('Ver foto do local'),
                                        ),
                                      ),
"""
ext = once(ext, old_items, new_items, 'opção ver foto')

old_save = """    await AppDatabase.instance.upsertSstRecord(record);
    await ManagementPanelService.syncCompany(widget.company);
"""
new_save = """    await AppDatabase.instance.upsertSstRecord(record);
    if (photoPath.isNotEmpty && File(photoPath).existsSync()) {
      await MediaSyncService.registerExtinguisherPhoto(
        companyId: widget.company.id,
        recordId: record.id,
        localPath: photoPath,
      );
      unawaited(MediaSyncService.uploadPending());
    }
    await ManagementPanelService.syncCompany(widget.company);
"""
ext = once(ext, old_save, new_save, 'proteção da foto ao salvar')

pubp.write_text(pub, encoding='utf-8', newline='\n')
companiesp.write_text(companies, encoding='utf-8', newline='\n')
extp.write_text(ext, encoding='utf-8', newline='\n')
mediap.write_text(media, encoding='utf-8', newline='\n')

assert 'version: 3.29.67+209' in pub
assert 'unawaited(_restoreMissingCompanyLogos(result));' in companies
assert 'companyIds: missing,' in companies
assert 'registerExtinguisherPhoto({' in media
assert 'restoreExtinguisherPhotos({' in media
assert "entityType=='extinguisher_photo'" in media
assert '_extinguisherPhotoOrIcon(record, color)' in ext
assert "title: Text('Ver foto do local')" in ext
assert 'MediaSyncService.registerExtinguisherPhoto(' in ext
print('v3.29.67+209: logos e fotos de extintor corrigidas.')

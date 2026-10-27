#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) < 3:
    raise SystemExit('Uso: patch_company_logo_persistence_v32954_v3303.py <app_dir> <android|windows>')

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
if platform not in {'android', 'windows'}:
    raise SystemExit('Plataforma deve ser android ou windows')

pub_path = root / 'pubspec.yaml'
media_path = root / 'lib/services/media_sync_service.dart'
companies_path = root / 'lib/screens/companies_screen.dart'

pub = pub_path.read_text(encoding='utf-8')
media = media_path.read_text(encoding='utf-8')
companies = companies_path.read_text(encoding='utf-8')

if platform == 'android':
    old_version = 'version: 3.29.53+195'
    new_version = 'version: 3.29.54+196'
else:
    old_version = 'version: 3.30.2+189'
    new_version = 'version: 3.30.3+190'

if new_version not in pub:
    if old_version not in pub:
        raise AssertionError(f'Versão base não encontrada: {old_version}')
    pub = pub.replace(old_version, new_version, 1)

if 'static Future<String> uploadCompanyLogoNow(String companyId)' not in media:
    marker = '  static Future<MediaSyncSummary> downloadMissing() async {'
    if marker not in media:
        raise AssertionError('Marcador downloadMissing Android não encontrado')
    upload_method = r'''  static Future<String> uploadCompanyLogoNow(String companyId) async {
    if (!AuthService.isSignedIn) {
      throw StateError('Faça login para salvar a logo online.');
    }
    final cleanCompanyId = companyId.trim();
    if (cleanCompanyId.isEmpty) throw StateError('Empresa não identificada.');

    final appDb = AppDatabase.instance;
    final db = await appDb.database;
    await _discoverLocalMedia(db);
    final rows = await db.query(
      'media_assets',
      where: "entity_type = 'company_logo' AND entity_id = ?",
      whereArgs: [cleanCompanyId],
      orderBy: 'updated_at DESC',
      limit: 1,
    );
    if (rows.isEmpty) throw StateError('Logo local não encontrada para envio.');
    final row = Map<String, Object?>.from(rows.first);
    final currentFileId = '${row['drive_file_id'] ?? ''}'.trim();
    if (currentFileId.isNotEmpty) return currentFileId;

    final localPath = '${row['local_path'] ?? ''}'.trim();
    if (localPath.isEmpty) throw StateError('Arquivo local da logo não encontrado.');
    final file = File(localPath);
    if (!await file.exists()) throw StateError('Arquivo local da logo não encontrado.');
    final length = await file.length();
    if (length <= 0 || length > _maxMediaBytes) {
      throw StateError('A logo deve ter no máximo 12 MB.');
    }

    final companyRows = await db.query(
      'companies',
      columns: ['name', 'cnpj'],
      where: 'id = ?',
      whereArgs: [cleanCompanyId],
      limit: 1,
    );
    final company = companyRows.isEmpty
        ? const <String, Object?>{}
        : companyRows.first;
    final response = await _postReliable(<String, Object?>{
      'action': 'media_upload',
      'syncKey': await appDb.getSetting('management_panel_sync_key'),
      'authToken': AuthService.sessionToken,
      'companyId': cleanCompanyId,
      'companyName': '${company['name'] ?? 'Empresa'}',
      'companyCnpj': '${company['cnpj'] ?? ''}',
      'deviceId': await AuthService.deviceId(),
      'platform': Platform.isWindows ? 'windows' : 'android',
      'mediaId': '${row['id'] ?? ''}',
      'entityType': 'company_logo',
      'entityId': cleanCompanyId,
      'fileName': '${row['file_name'] ?? p.basename(localPath)}',
      'mimeType': '${row['mime_type'] ?? _mimeTypeFor(localPath)}',
      'contentBase64': base64Encode(await file.readAsBytes()),
    });
    final fileId = '${response['fileId'] ?? ''}'.trim();
    if (fileId.isEmpty) {
      throw StateError('A Central não confirmou o armazenamento da logo.');
    }
    await db.update(
      'media_assets',
      {
        'drive_file_id': fileId,
        'updated_at': DateTime.now().toUtc().toIso8601String(),
      },
      where: 'id = ?',
      whereArgs: [row['id']],
    );
    await appDb.setSetting('media_sync_last_error', '');
    await appDb.setSetting(
      'media_sync_last_success',
      DateTime.now().toUtc().toIso8601String(),
    );
    return fileId;
  }

'''
    media = media.replace(marker, upload_method + marker, 1)

if 'static Future<int> restoreCompanyLogos({' not in media:
    marker = '  static Future<int> restoreInspectionMedia(String inspectionId) async {'
    if marker not in media:
        raise AssertionError('Marcador restoreInspectionMedia não encontrado')
    restore_method = r'''  static Future<int> restoreCompanyLogos({
    Iterable<String>? companyIds,
  }) async {
    if (!AuthService.isSignedIn) return 0;

    final db = await AppDatabase.instance.database;
    final wanted = companyIds == null
        ? null
        : companyIds.map((id) => id.trim()).where((id) => id.isNotEmpty).toSet();
    final companies = await db.query(
      'companies',
      columns: ['id', 'logo_path'],
      where: 'active = 1',
    );

    var recovered = 0;
    for (final company in companies) {
      final companyId = '${company['id'] ?? ''}'.trim();
      if (companyId.isEmpty || (wanted != null && !wanted.contains(companyId))) {
        continue;
      }

      final currentPath = '${company['logo_path'] ?? ''}'.trim();
      if (currentPath.isNotEmpty && await File(currentPath).exists()) {
        await _ensureAsset(
          db,
          companyId: companyId,
          entityType: 'company_logo',
          entityId: companyId,
          localPath: currentPath,
        );
        continue;
      }

      final mediaId = _assetId('company_logo', companyId);
      var assetRows = await db.query(
        'media_assets',
        where: 'id = ?',
        whereArgs: [mediaId],
        limit: 1,
      );
      Map<String, Object?> asset;
      if (assetRows.isEmpty) {
        asset = <String, Object?>{
          'id': mediaId,
          'company_id': companyId,
          'entity_type': 'company_logo',
          'entity_id': companyId,
          'local_path': '',
          'drive_file_id': '',
          'file_name': '',
          'mime_type': '',
          'updated_at': DateTime.now().toUtc().toIso8601String(),
        };
        await db.insert(
          'media_assets',
          asset,
          conflictAlgorithm: ConflictAlgorithm.ignore,
        );
      } else {
        asset = Map<String, Object?>.from(assetRows.first);
      }

      final lookedUp = await _lookupAssetOnDrive(db, asset);
      if (lookedUp != null) asset = lookedUp;
      if ('${asset['drive_file_id'] ?? ''}'.trim().isEmpty) continue;

      try {
        if (await _downloadAsset(db, asset)) recovered++;
      } catch (_) {
        // Falha de rede não apaga a logo nem bloqueia os dados estruturados.
      }
    }
    return recovered;
  }

'''
    media = media.replace(marker, restore_method + marker, 1)

if 'Future<void> _restoreMissingCompanyLogos(' not in companies:
    marker = '  Future<void> _editCompany([Company? company]) async {'
    if marker not in companies:
        raise AssertionError('Marcador _editCompany não encontrado')
    helper = r'''  Future<void> _restoreMissingCompanyLogos(List<Company> snapshot) async {
    final missing = <String>[];
    for (final company in snapshot) {
      final path = company.logoPath?.trim() ?? '';
      if (path.isEmpty || !File(path).existsSync()) {
        missing.add(company.id);
      }
    }
    if (missing.isEmpty) return;

    try {
      final restored = await MediaSyncService.restoreCompanyLogos(
        companyIds: missing,
      );
      if (restored <= 0 || !mounted) return;
      final refreshed = await AppDatabase.instance.getCompanies(
        onlyActive: false,
      );
      if (!mounted) return;
      setState(() => companies = refreshed);
    } catch (_) {
      // A ausência de internet não interfere na lista de empresas.
    }
  }

'''
    companies = companies.replace(marker, helper + marker, 1)

load_tail = r'''    setState(() {
      companies = result;
      stats = loadedStats;
      loading = false;
    });
  }
'''
load_new = r'''    setState(() {
      companies = result;
      stats = loadedStats;
      loading = false;
    });
    _restoreMissingCompanyLogos(result);
  }
'''
if '_restoreMissingCompanyLogos(result);' not in companies:
    if load_tail not in companies:
        raise AssertionError('Final de _load não encontrado')
    companies = companies.replace(load_tail, load_new, 1)

if platform == 'android' and 'await MediaSyncService.uploadCompanyLogoNow(company.id).timeout(' not in companies:
    compact = "    var synced=false; try { await DeviceSyncService.synchronize(force:true); synced=true; } catch(_) {}"
    expanded = r'''    var synced = false;
    String onlineError = '';
    try {
      await MediaSyncService.uploadCompanyLogoNow(company.id).timeout(
        const Duration(seconds: 45),
      );
      await DeviceSyncService.synchronize(
        force: true,
        syncMedia: false,
      ).timeout(const Duration(seconds: 45));
      synced = true;
    } catch (e) {
      onlineError = e.toString().replaceFirst('Bad state: ', '');
    }'''
    if compact not in companies:
        raise AssertionError('Bloco Android de sincronização da logo não encontrado')
    companies = companies.replace(compact, expanded, 1)

    old_msg = "ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(synced?'Logo salva e sincronizada. Ela será recuperada após reinstalar o app.':'Logo salva. A sincronização com a Central ficou pendente.')));"
    new_msg = "ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(synced ? 'Logo salva e protegida no Drive. Ela será restaurada automaticamente nos outros dispositivos.' : 'Logo salva neste aparelho. O envio online ficou pendente${onlineError.isEmpty ? '.' : ': $onlineError'}')));"
    if old_msg in companies:
        companies = companies.replace(old_msg, new_msg, 1)

pub_path.write_text(pub, encoding='utf-8', newline='\n')
media_path.write_text(media, encoding='utf-8', newline='\n')
companies_path.write_text(companies, encoding='utf-8', newline='\n')

assert new_version in pub
assert 'static Future<int> restoreCompanyLogos({' in media
assert "'action': 'media_lookup'" in media
assert "entityType: 'company_logo'" in media
assert "entityType=='company_logo'" in media or "entityType == 'company_logo'" in media
assert "'logo_path'" in media
assert 'Future<void> _restoreMissingCompanyLogos(' in companies
assert '_restoreMissingCompanyLogos(result);' in companies
assert 'MediaSyncService.restoreCompanyLogos(' in companies
assert "'companies': {'logo_path'}" in (root / 'lib/services/device_sync_service.dart').read_text(encoding='utf-8')
if platform == 'android':
    assert 'static Future<String> uploadCompanyLogoNow(String companyId)' in media
    assert 'MediaSyncService.uploadCompanyLogoNow(company.id)' in companies
else:
    assert 'MediaSyncService.uploadCompanyLogoNow(company.id)' in companies

print(f'Persistência de logos aplicada em {platform}: {new_version}')

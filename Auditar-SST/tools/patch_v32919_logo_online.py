#!/usr/bin/env python3
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
APP = REPO / 'app' / 'Auditar_SST_v1_5_dashboard'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Trecho esperado não encontrado: {label}')
    return text.replace(old, new, 1)


def patch_media() -> None:
    path = APP / 'lib/services/media_sync_service.dart'
    text = path.read_text(encoding='utf-8')
    marker = '  static Future<int> pendingCount() async {\n'
    insert = r'''  /// Envia imediatamente a logo da empresa para o armazenamento online.
  /// Retorna o ID confirmado pelo Google Drive somente após o upload concluir.
  static Future<String> uploadCompanyLogoNow(String companyId) async {
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
      where: "entity_type = 'company_logo' AND entity_id = ? "
          'AND local_path IS NOT NULL AND local_path <> ""',
      whereArgs: [cleanCompanyId],
      orderBy: 'updated_at DESC',
      limit: 1,
    );
    if (rows.isEmpty) throw StateError('Logo local não encontrada para envio.');
    return _uploadSingleAsset(
      appDb,
      db,
      Map<String, Object?>.from(rows.first),
    );
  }

  /// Migra logos de versões anteriores que ainda estejam somente no aparelho.
  /// É restrito às logos para não atrasar o login com outras evidências.
  static Future<MediaSyncSummary> uploadPendingCompanyLogos() async {
    if (!AuthService.isSignedIn) return const MediaSyncSummary();
    final appDb = AppDatabase.instance;
    final db = await appDb.database;
    await _discoverLocalMedia(db);
    final rows = await db.query(
      'media_assets',
      where: "entity_type = 'company_logo' "
          'AND (drive_file_id IS NULL OR drive_file_id = "") '
          'AND local_path IS NOT NULL AND local_path <> ""',
      orderBy: 'updated_at ASC',
    );

    var uploaded = 0;
    String lastError = '';
    for (final raw in rows) {
      try {
        await _uploadSingleAsset(
          appDb,
          db,
          Map<String, Object?>.from(raw),
        );
        uploaded++;
      } catch (e) {
        lastError = _friendlyError(e);
      }
    }
    if (lastError.isNotEmpty) {
      await appDb.setSetting('media_sync_last_error', lastError);
    }
    return MediaSyncSummary(uploaded: uploaded, pending: await pendingCount());
  }

  static Future<String> _uploadSingleAsset(
    AppDatabase appDb,
    Database db,
    Map<String, Object?> row,
  ) async {
    final localPath = '${row['local_path'] ?? ''}'.trim();
    final companyId = '${row['company_id'] ?? ''}'.trim();
    if (localPath.isEmpty || companyId.isEmpty) {
      throw StateError('Mídia sem arquivo local ou empresa.');
    }
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
      whereArgs: [companyId],
      limit: 1,
    );
    final company = companyRows.isEmpty
        ? const <String, Object?>{}
        : companyRows.first;
    final response = await _post(<String, Object?>{
      'action': 'media_upload',
      'syncKey': await appDb.getSetting('management_panel_sync_key'),
      'authToken': AuthService.sessionToken,
      'companyId': companyId,
      'companyName': '${company['name'] ?? 'Empresa'}',
      'companyCnpj': '${company['cnpj'] ?? ''}',
      'deviceId': await AuthService.deviceId(),
      'platform': Platform.isWindows ? 'windows' : 'android',
      'entityType': '${row['entity_type'] ?? ''}',
      'entityId': '${row['entity_id'] ?? ''}',
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
    await appDb.setSetting(
      'media_sync_last_success',
      DateTime.now().toUtc().toIso8601String(),
    );
    return fileId;
  }

'''
    text = replace_once(text, marker, insert + marker, 'métodos de logo online')
    path.write_text(text, encoding='utf-8')


def patch_companies() -> None:
    path = APP / 'lib/screens/companies_screen.dart'
    text = path.read_text(encoding='utf-8')
    start = text.index('  Future<void> _chooseLogo(Company company) async {')
    end = text.index('\n\n  Future<void> _removeLogo', start)
    new = '''  Future<void> _chooseLogo(Company company) async {
    final image = await picker.pickImage(
      source: ImageSource.gallery,
      imageQuality: 90,
      maxWidth: 1600,
    );
    if (image == null) return;

    final old = company.logoPath;
    final stored = await StorageService.persistImage(
      image.path,
      folder: 'logos_empresas',
    );
    await AppDatabase.instance.updateCompanyLogo(company.id, stored);
    await MediaSyncService.registerCompanyLogo(
      companyId: company.id,
      localPath: stored,
    );

    var onlineReady = false;
    String? onlineError;
    try {
      await MediaSyncService.uploadCompanyLogoNow(company.id).timeout(
        const Duration(seconds: 35),
      );
      await DeviceSyncService.synchronize(force: true).timeout(
        const Duration(seconds: 20),
      );
      onlineReady = true;
    } catch (e) {
      onlineError = e.toString().replaceFirst('Bad state: ', '');
    }

    if (old != null && old.isNotEmpty && old != stored) {
      try {
        final file = File(old);
        if (await file.exists()) await file.delete();
      } catch (_) {}
    }
    await _load();
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          onlineReady
              ? 'Logo salva online e vinculada à empresa. Ela será recuperada automaticamente em outros dispositivos e após reinstalação.'
              : 'Logo salva neste aparelho. O envio online ficou pendente${onlineError == null ? '.' : ': $onlineError'}',
        ),
      ),
    );
  }'''
    text = text[:start] + new + text[end:]
    path.write_text(text, encoding='utf-8')


def patch_sync_coordinator() -> None:
    path = APP / 'lib/services/sync_coordinator.dart'
    text = path.read_text(encoding='utf-8')
    text = replace_once(
      text,
      "import 'management_panel_service.dart';\n",
      "import 'management_panel_service.dart';\nimport 'media_sync_service.dart';\n",
      'import MediaSyncService',
    )
    text = replace_once(
      text,
      '''      DeviceSyncResult? result;
      try {
        result = await DeviceSyncService.synchronize();
      } catch (_) {
''',
      '''      // Protege online logos antigas antes de enviar os metadados.
      try {
        await MediaSyncService.uploadPendingCompanyLogos().timeout(
          const Duration(seconds: 25),
        );
      } catch (_) {}

      DeviceSyncResult? result;
      try {
        result = await DeviceSyncService.synchronize();
      } catch (_) {
''',
      'migração automática de logos locais',
    )
    text = replace_once(
      text,
      '''      if (result != null) {
        _setDesktopStatus(
          label: '',
          tone: _SyncTone.ok,
        );
      }
''',
      '''      if (result != null) {
        // Após receber os metadados, restaura do Drive as logos ausentes.
        try {
          await MediaSyncService.downloadCompanyLogos().timeout(
            const Duration(seconds: 25),
          );
        } catch (_) {}
        _setDesktopStatus(
          label: '',
          tone: _SyncTone.ok,
        );
      }
''',
      'restauração automática de logos online',
    )
    path.write_text(text, encoding='utf-8')


def patch_version() -> None:
    pub = APP / 'pubspec.yaml'
    text = pub.read_text(encoding='utf-8')
    text = replace_once(text, 'version: 3.29.18+161', 'version: 3.29.19+162', 'versão')
    pub.write_text(text, encoding='utf-8')

    home = APP / 'lib/screens/home_screen.dart'
    text = home.read_text(encoding='utf-8')
    text = text.replace('Auditar SST • versão 3.29.18', 'Auditar SST • versão 3.29.19')
    text = text.replace('Auditar SST para Windows • versão 3.29.18', 'Auditar SST para Windows • versão 3.29.19')
    home.write_text(text, encoding='utf-8')


def validate() -> None:
    media = (APP / 'lib/services/media_sync_service.dart').read_text(encoding='utf-8')
    companies = (APP / 'lib/screens/companies_screen.dart').read_text(encoding='utf-8')
    coordinator = (APP / 'lib/services/sync_coordinator.dart').read_text(encoding='utf-8')
    checks = {
      'versão': 'version: 3.29.19+162' in (APP / 'pubspec.yaml').read_text(encoding='utf-8'),
      'upload imediato': 'uploadCompanyLogoNow' in media,
      'migração de logos antigas': 'uploadPendingCompanyLogos' in media,
      'confirmação fileId': "response['fileId']" in media,
      'salvamento chama upload': 'MediaSyncService.uploadCompanyLogoNow(company.id)' in companies,
      'upload automático no sync': 'MediaSyncService.uploadPendingCompanyLogos()' in coordinator,
      'restauração automática': 'MediaSyncService.downloadCompanyLogos()' in coordinator,
      'IA Executivo preservada': 'Conversar com a IA sobre o Executivo' in (APP / 'lib/screens/report_screen.dart').read_text(encoding='utf-8'),
    }
    missing = [name for name, ok in checks.items() if not ok]
    if missing:
      raise RuntimeError('Validações v3.29.19 falharam: ' + ', '.join(missing))


def main() -> int:
    patch_media()
    patch_companies()
    patch_sync_coordinator()
    patch_version()
    validate()
    print('v3.29.19+162: logo online com upload imediato e restauração automática aplicada.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
pubp = root / 'pubspec.yaml'
mediap = root / 'lib/services/media_sync_service.dart'
companiesp = root / 'lib/screens/companies_screen.dart'
coordp = root / 'lib/services/sync_coordinator.dart'
screenp = root / 'lib/screens/data_safety_screen.dart'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Trecho esperado não encontrado: {label}')
    return text.replace(old, new, 1)

# Versão nova para distinguir da build que ficava em ciclo 0 -> 9.
pub = pubp.read_text(encoding='utf-8')
pub = replace_once(pub, 'version: 3.29.42+184', 'version: 3.29.43+185', 'versão Windows')
pubp.write_text(pub, encoding='utf-8', newline='\n')

# ---------------------------------------------------------------------------
# MÍDIA / LOGOS
# ---------------------------------------------------------------------------
media = mediap.read_text(encoding='utf-8')

# Logos sempre têm prioridade de upload e download no PC.
media = replace_once(
    media,
    "      orderBy: 'updated_at ASC',\n      limit: limit.clamp(1, 40),",
    "      orderBy: \"CASE WHEN entity_type = 'company_logo' THEN 0 ELSE 1 END, updated_at ASC\",\n      limit: limit.clamp(1, 40),",
    'prioridade de upload das logos',
)
media = replace_once(
    media,
    "      orderBy: 'updated_at DESC',\n      limit: limit.clamp(1, 120),",
    "      orderBy: \"CASE WHEN entity_type = 'company_logo' THEN 0 ELSE 1 END, updated_at DESC\",\n      limit: limit.clamp(1, 120),",
    'prioridade de download das logos',
)

# Upload imediato da logo: no Windows o sync estruturado não envia mídia por
# padrão, portanto salvar a logo precisa proteger o arquivo no Drive antes.
if 'static Future<String> uploadCompanyLogoNow' not in media:
    marker = '  static Future<MediaSyncSummary> downloadMissing({int limit = 120}) async {'
    method = r'''  static Future<String> uploadCompanyLogoNow(String companyId) async {
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
    final response = await _post(<String, Object?>{
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
    if marker not in media:
        raise RuntimeError('Marcador de downloadMissing não encontrado')
    media = media.replace(marker, method + marker, 1)

# Alterar somente caminhos locais NÃO pode criar uma nova alteração estruturada.
# Antes da atualização local salvamos o marcador de sync e depois o restauramos.
helper_marker = '  static Future<void> _applyEntityPath('
helper = r'''  static Future<void> _localOnlyPathUpdate(
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
if '_localOnlyPathUpdate(' not in media:
    if helper_marker not in media:
        raise RuntimeError('Marcador _applyEntityPath não encontrado')
    media = media.replace(helper_marker, helper + helper_marker, 1)

# downloadMissing: local_path é cache local; preserve o estado de dirty anterior.
old_download_update = '''        await db.update(
          'media_assets',
          {'local_path': destination},
          where: 'id = ?',
          whereArgs: [row['id']],
        );
'''
new_download_update = '''        await _localOnlyPathUpdate(
          db,
          table: 'media_assets',
          recordId: '${row['id'] ?? ''}',
          values: {'local_path': destination},
        );
'''
media = replace_once(media, old_download_update, new_download_update, 'cache local da mídia')

# _ensureAsset também pode apenas reconstruir local_path de uma mídia remota.
old_ensure_update = '''      await db.update(
        'media_assets',
        {
          'local_path': localPath,
          'file_name': p.basename(localPath),
          'mime_type': _mimeTypeFor(localPath),
        },
        where: 'id = ?',
        whereArgs: [id],
      );
'''
new_ensure_update = '''      await _localOnlyPathUpdate(
        db,
        table: 'media_assets',
        recordId: id,
        values: {'local_path': localPath},
      );
'''
media = replace_once(media, old_ensure_update, new_ensure_update, 'reconstrução do local_path')

# Substitui somente o aplicador de caminhos locais. Os dados estruturados do
# registro permanecem intactos e o contador de pendências não volta a subir.
pattern = re.compile(
    r"  static Future<void> _applyEntityPath\([\s\S]*?\n  static Future<Map<String, dynamic>> _post\(",
    re.MULTILINE,
)
match = pattern.search(media)
if not match:
    raise RuntimeError('Função _applyEntityPath não localizada')
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

mediap.write_text(media, encoding='utf-8', newline='\n')

# ---------------------------------------------------------------------------
# TELA DE EMPRESAS: salvar logo no Windows deve fazer upload imediatamente.
# ---------------------------------------------------------------------------
companies = companiesp.read_text(encoding='utf-8')
start = companies.index('  Future<void> _chooseLogo(Company company) async {')
end = companies.index('\n\n  Future<void> _removeLogo', start)
new_choose = r'''  Future<void> _chooseLogo(Company company) async {
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
    String onlineError = '';
    try {
      await MediaSyncService.uploadCompanyLogoNow(company.id).timeout(
        const Duration(seconds: 45),
      );
      await DeviceSyncService.synchronize(
        force: true,
        syncMedia: false,
      ).timeout(const Duration(seconds: 45));
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
              ? 'Logo salva e protegida no Drive. Ela aparecerá nos outros dispositivos após a sincronização.'
              : 'Logo salva neste computador. O envio online ficou pendente${onlineError.isEmpty ? '.' : ': $onlineError'}',
        ),
      ),
    );
  }'''
companies = companies[:start] + new_choose + companies[end:]
companiesp.write_text(companies, encoding='utf-8', newline='\n')

# ---------------------------------------------------------------------------
# INDICADOR GLOBAL: durante sync mostra só o símbolo, sem faixa com nome.
# ---------------------------------------------------------------------------
coord = coordp.read_text(encoding='utf-8')
coord = replace_once(
    coord,
    '    final showText = tone == _SyncTone.warning || tone == _SyncTone.offline;',
    '    const showText = false;',
    'indicador global compacto',
)
coordp.write_text(coord, encoding='utf-8', newline='\n')

# ---------------------------------------------------------------------------
# SEGURANÇA DOS DADOS: nunca iniciar em 0% se já existe sync ativo e, se a UI
# ultrapassar o limite, retirar o estado de carregamento infinito.
# ---------------------------------------------------------------------------
screen = screenp.read_text(encoding='utf-8')
screen = screen.replace(
    'syncPercent = Platform.isWindows ? ((last.percent * 90) ~/ 100) : last.percent;',
    "syncPercent = last.running && last.percent <= 0\n        ? 1\n        : (Platform.isWindows ? ((last.percent * 90) ~/ 100) : last.percent);",
    1,
)
old_timeout = '''    } on TimeoutException {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'A sincronização continua em segundo plano. O progresso permanecerá visível nesta tela.',
            ),
          ),
        );
      }
'''
new_timeout = '''    } on TimeoutException {
      if (mounted) {
        setState(() {
          syncRunning = false;
          syncPhase = 'A Central demorou a responder • nova tentativa será automática';
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'A Central demorou a responder. O app saiu do carregamento e tentará novamente automaticamente.',
            ),
          ),
        );
      }
'''
screen = replace_once(screen, old_timeout, new_timeout, 'timeout visual da sincronização')
screenp.write_text(screen, encoding='utf-8', newline='\n')

# Validações finais.
final_media = mediap.read_text(encoding='utf-8')
final_companies = companiesp.read_text(encoding='utf-8')
final_coord = coordp.read_text(encoding='utf-8')
final_screen = screenp.read_text(encoding='utf-8')
assert 'version: 3.29.43+185' in pubp.read_text(encoding='utf-8')
assert 'static Future<String> uploadCompanyLogoNow' in final_media
assert "CASE WHEN entity_type = 'company_logo' THEN 0 ELSE 1 END" in final_media
assert '_localOnlyPathUpdate' in final_media
assert 'uploadCompanyLogoNow(company.id)' in final_companies
assert 'const showText = false;' in final_coord
assert 'A Central demorou a responder • nova tentativa será automática' in final_screen
print('v3.29.43+185: ciclo 0→9 corrigido, logos Windows priorizadas e indicador global compacto.')

#!/usr/bin/env python3
"""Cloud draft UX on top of v329129 local safety copy. Existing sync/GS/DB are byte-identical."""
from pathlib import Path
import hashlib,shutil,sys
root=Path(sys.argv[1])
screen=root/'lib/screens/express_round_screen.dart'
target=root/'lib/services/express_round_cloud_draft_service.dart'
source=Path(__file__).resolve().parents[1]/'feature_sources/express_round_cloud_draft_v329130.dart'
protected=[
'lib/database.dart','lib/services/device_sync_service.dart',
'lib/services/sync_coordinator.dart','lib/services/media_sync_service.dart',
'lib/services/storage_service.dart','lib/services/drive_service.dart',
'lib/services/apps_script_http.dart','lib/services/ai_assistant_service.dart',
'painel_web_google_apps_script/Code.gs',
'painel_web_google_apps_script/MultiUser.gs',
'painel_web_google_apps_script/ClientPortal.gs']
before={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in protected}
s=screen.read_text(encoding='utf-8')
def edit(old,new,label):
 global s
 count=s.count(old)
 if count!=1:raise RuntimeError('CLOUD_DRAFT '+label+' expected once '+str(count))
 s=s.replace(old,new,1)

edit("import '../services/express_round_draft_storage.dart';",
 "import '../services/express_round_draft_storage.dart';\nimport '../services/express_round_cloud_draft_service.dart';",
 'cloud import')
edit("  bool _restoringSavedPhotos = false;",
 """  bool _restoringSavedPhotos = false;
  Timer? _cloudDraftTimer;
  bool _cloudDraftBusy = false;
  bool _cloudDraftFetching = false;
  Future<void> _cloudDraftIdle = Future<void>.value();
  int _cloudDraftRevision = 0;
  final Map<String, dynamic> _cloudPhotoRefs = <String, dynamic>{};""",
 'cloud state')
edit("""      unawaited(_flushRoundDraft());
    }
  }

  @override
  void dispose() {""","""      unawaited(_flushRoundDraft().then((_) => _publishCloudRoundDraft()));
    }
  }

  @override
  void dispose() {""",'background best effort')
edit("    _roundDraftTimer?.cancel();\n    if (_roundDraftDirty", 
     "    _roundDraftTimer?.cancel();\n    _cloudDraftTimer?.cancel();\n    if (_roundDraftDirty",
     'cancel timers')
edit("      photoPath.isNotEmpty ||\n      secondPhotoPath.isNotEmpty ||",
     "      photoPath.isNotEmpty ||\n      secondPhotoPath.isNotEmpty ||\n      _cloudPhotoRefs.isNotEmpty ||",
     'cloud refs count as pending content')
edit("""    _roundDraftDirty = true;
    _roundDraftTimer?.cancel();""",
     """    _roundDraftDirty = true;
    _cloudDraftRevision++;
    _roundDraftTimer?.cancel();""",
     'revision of draft changes')
edit("    'photoPath2': secondPhotoPath,\n    'categories':",
     "    'photoPath2': secondPhotoPath,\n    'cloudPhotoRefs': Map<String, dynamic>.from(_cloudPhotoRefs),\n    'categories':",
     'carry cloud refs')
edit("""        setState(() => _roundDraftStatus = 'Rascunho salvo neste aparelho');
      }
      if (showMessage) _message('Rascunho salvo neste aparelho. Continue ao reabrir a ronda.');""",
     """        setState(() => _roundDraftStatus =
            'Salvo no aparelho • aguardando confirmação na nuvem');
        _cloudDraftTimer?.cancel();
        _cloudDraftTimer = Timer(const Duration(seconds: 12), () {
          unawaited(_publishCloudRoundDraft());
        });
      }
      if (showMessage) _message('Rascunho salvo localmente. Enviando para a nuvem...');""",
     'cloud status after local save')
methods=r'''  Future<void> _publishCloudRoundDraft({bool showMessage = false}) async {
    _cloudDraftTimer?.cancel();
    if (_cloudDraftBusy || _roundDraftRestoring || viewingHistoricalRound ||
        roundId.isEmpty || saving || !_roundDraftHasContent) return;
    final company = widget.company.id;
    final targetRound = roundId;
    final targetEntry = _roundDraftEntryId;
    final revision = _cloudDraftRevision;
    final completed = Completer<void>();
    _cloudDraftIdle = completed.future;
    if (mounted) setState(() {
      _cloudDraftBusy = true;
      _roundDraftStatus = 'Enviando rascunho e fotos à nuvem...';
    });
    try {
      await _roundDraftTail;
      final confirmed = await ExpressRoundCloudDraftService.publish(
        companyId: company, roundId: targetRound,
        snapshot: _roundDraftPayload(),
      );
      if (!mounted || roundId != targetRound ||
          _roundDraftEntryId != targetEntry ||
          _cloudDraftRevision != revision) return;
      setState(() => _roundDraftStatus = confirmed
          ? 'Na nuvem • texto e fotos com backup confirmado'
          : 'Backup pendente • cópia preservada neste aparelho');
      if (showMessage) _message(confirmed
          ? 'Rascunho e fotos confirmados na nuvem.'
          : 'Backup ainda pendente. Não desinstale o aplicativo.');
    } catch (error) {
      if (mounted && roundId == targetRound) {
        setState(() => _roundDraftStatus =
            'Backup pendente • cópia preservada neste aparelho');
        if (showMessage) _message(
            'Nuvem indisponível no momento. Seu rascunho local está salvo.');
      }
    } finally {
      completed.complete();
      if (mounted) {
        setState(() => _cloudDraftBusy = false);
        if (_cloudDraftRevision != revision && _roundDraftHasContent) {
          _cloudDraftTimer?.cancel();
          _cloudDraftTimer = Timer(const Duration(seconds: 2), () {
            unawaited(_publishCloudRoundDraft());
          });
        }
      }
    }
  }

  Future<void> _openCloudRoundDrafts() async {
    if (_cloudDraftFetching || _cloudDraftBusy || saving) return;
    if (_roundDraftHasContent) {
      await _flushRoundDraft();
      _message('Existe um rascunho nesta tela. Salve a ocorrência antes '
          'de abrir outra na nuvem.');
      return;
    }
    setState(() => _cloudDraftFetching = true);
    try {
      await DeviceSyncService.synchronize(force: true)
          .timeout(const Duration(seconds: 40));
      final available = await ExpressRoundCloudDraftService.list(
          widget.company.id);
      if (!mounted) return;
      final actual = roundRecords.map((record) => record.id).toSet();
      final items = available.where((record) =>
          !actual.contains((record.payload['entryId'] ?? '').toString()))
          .toList();
      if (items.isEmpty) {
        _message('Nenhum rascunho pendente da nuvem para esta empresa.');
        return;
      }
      final chosen = await showDialog<SstRecord>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          title: const Text('Continuar rascunho da nuvem'),
          content: SizedBox(
            width: 500,
            height: 350,
            child: ListView.builder(
              itemCount: items.length,
              itemBuilder: (context, index) {
                final item = items[index];
                final info = item.payload;
                final text = (info['description'] ?? '').toString().trim();
                return ListTile(
                  leading: const Icon(Icons.cloud_done_outlined),
                  title: Text(text.isEmpty ? 'Rascunho de vistoria' : text,
                      maxLines: 2, overflow: TextOverflow.ellipsis),
                  subtitle: Text((info['updatedAt'] ?? '').toString()),
                  onTap: () => Navigator.pop(dialogContext, item),
                );
              },
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(dialogContext),
                child: const Text('Cancelar')),
          ],
        ),
      );
      if (chosen == null || !mounted) return;
      final cloud = await ExpressRoundCloudDraftService.restore(
          companyId: widget.company.id, record: chosen);
      final newRound = (cloud['roundId'] ?? '').toString().trim();
      if (newRound.isEmpty) throw StateError('Rascunho sem identificador.');
      await ExpressRoundDraftStorage.save(
          widget.company.id, newRound, cloud);
      await AppDatabase.instance.setSetting(_openRoundSetting, newRound);
      if (!mounted) return;
      await _load();
      _message(cloud['cloudPhotoMissing'] == true
          ? 'Texto restaurado da nuvem. Algumas fotos aguardam recuperação.'
          : 'Rascunho recuperado da nuvem. Confira antes de continuar.');
    } catch (_) {
      if (mounted) _message(
        'Não foi possível consultar os rascunhos agora. '
        'Confira a conexão e o acesso à Central Online.');
    } finally {
      if (mounted) setState(() => _cloudDraftFetching = false);
    }
  }

'''
edit("  Future<void> _restoreSavedRoundPhotos() async {",
 methods+"  Future<void> _restoreSavedRoundPhotos() async {",
 'cloud methods')
edit("""      _roundDraftDirty = false;
      _draftPhotoMissing = (path.isNotEmpty && !photoAvailable) ||""",
     """      _roundDraftDirty = false;
      _cloudPhotoRefs
        ..clear()
        ..addAll(draft?['cloudPhotoRefs'] is Map
            ? Map<String, dynamic>.from(draft!['cloudPhotoRefs'] as Map)
            : <String, dynamic>{});
      _draftPhotoMissing = draft?['cloudPhotoMissing'] == true ||
          (path.isNotEmpty && !photoAvailable) ||""",
     'cloud restore state')
edit("""      _roundDraftEntryId = (draft?['entryId'] ?? '').toString().trim();""",
     """      _roundDraftEntryId = (draft?['entryId'] ?? '').toString().trim();""",
     'verify restore entry') if False else None
edit("""      await _roundDraftTail;
      try {
        await ExpressRoundDraftStorage.clear(widget.company.id, roundId);""",
     """      await _roundDraftTail;
      _cloudDraftTimer?.cancel();
      await _cloudDraftIdle;
      try {
        await ExpressRoundCloudDraftService.complete(
            companyId: widget.company.id, roundId: roundId);
      } catch (_) {
        // A locally completed observation is never undone by cloud downtime.
      }
      try {
        await ExpressRoundDraftStorage.clear(widget.company.id, roundId);""",
     'cloud completed tombstone')
edit("""        _draftPhotoMissing = false;
        _roundDraftStatus = 'Nenhum registro pendente no rascunho';""",
     """        _draftPhotoMissing = false;
        _cloudPhotoRefs.clear();
        _roundDraftStatus = 'Nenhum registro pendente no rascunho';""",
     'reset refs')
edit("""      _message('Há uma ocorrência no rascunho. Salve-a antes de finalizar.');""",
     """      _message('Há uma ocorrência no rascunho. Salve-a antes de finalizar.');""",
     'verify completion blocker') if False else None
edit("""          'Rascunhos ficam neste aparelho. Salve o registro '
                          'e confirme o backup das fotos antes de desinstalar '
                          'ou limpar os dados do aplicativo.',""",
     """          'O rascunho é enviado à nuvem. A cópia local permanece até '
                          'a confirmação dos dados e fotos. Não desinstale '
                          'enquanto o backup estiver pendente.',""",
     'accurate cloud help')
edit("""                                  await _flushRoundDraft(showMessage: true);
                                },""",
     """                                  await _flushRoundDraft();
                                  await _publishCloudRoundDraft(
                                      showMessage: true);
                                },""",
     'manual save immediate cloud')
edit("""                    ),
                    const SizedBox(height: 7),""",
     """                    ),
                    const SizedBox(height: 7),""",
     'noop') if False else None
# Insert an explicit open-from-cloud button after the draft status card,
# using the unique anchor for the subsequent original widget.
marker="""                          icon: const Icon(Icons.save_as_outlined),
                        ),
                      ),
                    ),"""
edit(marker,marker+"""
                    const SizedBox(height: 6),
                    OutlinedButton.icon(
                      onPressed: _cloudDraftFetching || _cloudDraftBusy
                          ? null : _openCloudRoundDrafts,
                      icon: _cloudDraftFetching
                          ? const SizedBox(width: 16, height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2))
                          : const Icon(Icons.cloud_download_outlined),
                      label: const Text('Continuar rascunho da nuvem'),
                    ),""",
 'cloud button')
edit("""                    _draftPhotoMissing = false;
                    _clearAiState();""",
     """                    _draftPhotoMissing = false;
                    _cloudPhotoRefs.clear();
                    _clearAiState();""",
     'remove stale cloud photo refs')
shutil.copyfile(source,target)
screen.write_text(s,encoding='utf-8',newline='\n')
changed=[name for name,h in before.items()
         if hashlib.sha256((root/name).read_bytes()).hexdigest()!=h]
if changed:raise SystemExit('CORE_SYNC_DB_MEDIA_GS_AI_MODIFIED '+repr(changed))
print('CLOUD_DRAFT_UI_ISOLATED_OK')
print('EXISTING_SYNC_MEDIA_DB_GS_BYTE_IDENTICAL_OK')

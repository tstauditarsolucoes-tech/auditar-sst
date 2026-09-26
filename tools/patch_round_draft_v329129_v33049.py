#!/usr/bin/env python3
"""Local Ronda autosave and explicit saved-photo recovery. Sync/GS/DB untouched."""
from pathlib import Path
import hashlib, shutil, sys
root=Path(sys.argv[1])
path=root/'lib/screens/express_round_screen.dart'
helper=root/'lib/services/express_round_draft_storage.dart'
src=Path(__file__).resolve().parents[1]/'feature_sources/express_round_draft_storage_v329129.dart'
test_src=Path(__file__).resolve().parents[1]/'feature_sources/express_round_draft_storage_test_v329129.dart'
protected=[
 'lib/database.dart','lib/services/device_sync_service.dart',
 'lib/services/sync_coordinator.dart','lib/services/media_sync_service.dart',
 'lib/services/storage_service.dart','lib/services/drive_service.dart',
 'lib/services/apps_script_http.dart','lib/services/ai_assistant_service.dart',
 'painel_web_google_apps_script/Code.gs',
 'painel_web_google_apps_script/MultiUser.gs',
 'painel_web_google_apps_script/ClientPortal.gs',
]
before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in protected}
s=path.read_text(encoding='utf-8')
def edit(old,new,label):
 global s
 n=s.count(old)
 if n!=1: raise RuntimeError('DRAFT '+label+' expected once: '+str(n))
 s=s.replace(old,new,1)
edit("import '../services/express_round_pdf_service.dart';",
     "import '../services/express_round_pdf_service.dart';\nimport '../services/express_round_draft_storage.dart';",'import')
edit('class _ExpressRoundScreenState extends State<ExpressRoundScreen> {',
     'class _ExpressRoundScreenState extends State<ExpressRoundScreen> with WidgetsBindingObserver {','lifecycle')
edit('  bool generatingReport = false;',"""  bool generatingReport = false;
  Timer? _roundDraftTimer;
  Future<void> _roundDraftTail = Future<void>.value();
  String _roundDraftEntryId = '';
  String _roundDraftStatus = 'Rascunho automático neste aparelho';
  bool _roundDraftDirty = false;
  bool _roundDraftRestoring = true;
  bool _draftPhotoMissing = false;
  bool _restoringSavedPhotos = false;""",'state')
edit('    super.initState();\n    _load();',"""    super.initState();
    WidgetsBinding.instance.addObserver(this);
    description.addListener(_scheduleRoundDraft);
    location.addListener(_scheduleRoundDraft);
    _load();""",'init')
edit("""  @override
  void dispose() {
    description.dispose();
    location.dispose();
    super.dispose();
  }""","""  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.inactive ||
        state == AppLifecycleState.paused ||
        state == AppLifecycleState.detached) {
      unawaited(_flushRoundDraft());
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _roundDraftTimer?.cancel();
    if (_roundDraftDirty && !_roundDraftRestoring &&
        !viewingHistoricalRound && roundId.isNotEmpty) {
      // Capture before disposing controllers; the background task uses values,
      // not the disposed widget. The last snapshot is queued after older ones.
      unawaited(_enqueueRoundDraft(_roundDraftPayload()));
    }
    description.dispose();
    location.dispose();
    super.dispose();
  }""",'dispose')
methods=r'''  bool get _roundDraftHasContent =>
      description.text.trim().isNotEmpty ||
      location.text.trim().isNotEmpty ||
      photoPath.isNotEmpty ||
      selectedCategories.isNotEmpty ||
      findingType != 'Não conformidade' ||
      priority != 'Média' || recurring;

  Map<String, dynamic> _roundDraftPayload() => <String, dynamic>{
    'entryId': _roundDraftEntryId,
    'sectorId': sectorId ?? '',
    'findingType': findingType,
    'priority': priority,
    'recurring': recurring,
    'description': description.text,
    'location': location.text,
    'photoPath': photoPath,
    'categories': selectedCategories.toList(),
    'aiTextOriginal': aiTextOriginal,
    'aiTitle': aiTitle,
    'aiRisk': aiRisk,
    'aiConsequence': aiConsequence,
    'aiRecommendation': aiRecommendation,
    'aiImmediateAction': aiImmediateAction,
    'aiResponsible': aiResponsible,
    'aiConfidence': aiConfidence,
    'aiReferences': aiReferences,
    'aiChecks': aiChecks,
  };

  Future<void> _enqueueRoundDraft(Map<String, dynamic> snapshot) {
    final company = widget.company.id;
    final targetRound = roundId;
    final write = _roundDraftTail.then((_) =>
        ExpressRoundDraftStorage.save(company, targetRound, snapshot));
    _roundDraftTail = write.catchError((Object _) {});
    return write;
  }

  void _scheduleRoundDraft() {
    if (_roundDraftRestoring || viewingHistoricalRound ||
        roundId.isEmpty || saving) return;
    _roundDraftDirty = true;
    _roundDraftTimer?.cancel();
    _roundDraftTimer = Timer(const Duration(milliseconds: 700), () {
      unawaited(_flushRoundDraft());
    });
  }

  Future<void> _flushRoundDraft({bool showMessage = false}) async {
    _roundDraftTimer?.cancel();
    if (_roundDraftRestoring || viewingHistoricalRound ||
        roundId.isEmpty || !_roundDraftDirty) return;
    final snapshot = _roundDraftPayload();
    _roundDraftDirty = false;
    try {
      await _enqueueRoundDraft(snapshot);
      if (mounted && !_roundDraftDirty) {
        setState(() => _roundDraftStatus = 'Rascunho salvo neste aparelho');
      }
      if (showMessage) _message('Rascunho salvo neste aparelho. Continue ao reabrir a ronda.');
    } catch (_) {
      _roundDraftDirty = true;
      if (mounted) {
        setState(() => _roundDraftStatus = 'Falha ao salvar rascunho. Tente novamente.');
        _message('Não foi possível salvar o rascunho. Tente novamente antes de sair.');
      }
    }
  }

  Future<void> _restoreSavedRoundPhotos() async {
    if (_restoringSavedPhotos || roundRecords.isEmpty || roundId.isEmpty) return;
    final targetRound = roundId;
    final before = roundRecords.where((record) {
      final path = (record.payload['photoPath'] ?? '').toString().trim();
      return path.isNotEmpty && !File(path).existsSync();
    }).length;
    if (before == 0) {
      _message('As fotos desta ronda estão disponíveis neste aparelho.');
      return;
    }
    setState(() => _restoringSavedPhotos = true);
    try {
      final count = await MediaSyncService.restoreRoundMedia(
        companyId: widget.company.id,
        roundId: targetRound,
      ).timeout(const Duration(seconds: 25));
      if (!mounted || roundId != targetRound) return;
      await _reloadRoundRecords();
      final remaining = roundRecords.where((record) {
        final path = (record.payload['photoPath'] ?? '').toString().trim();
        return path.isNotEmpty && !File(path).existsSync();
      }).length;
      _message(remaining == 0
          ? 'Fotos recuperadas do backup existente (' + count.toString() + ').'
          : 'Ainda há ' + remaining.toString() +
              ' foto(s) indisponível(is). Confira se o backup foi concluído.');
    } catch (_) {
      _message('Não foi possível recuperar agora. Confira a conexão e o backup.');
    } finally {
      if (mounted) setState(() => _restoringSavedPhotos = false);
    }
  }

'''
edit('  Future<void> _load() async {',methods+'  Future<void> _load() async {','draft methods')
edit("""    if (!mounted) return;
    setState(() {
      roundId = activeRound;""","""    final storedDraft = await ExpressRoundDraftStorage.load(
      widget.company.id, activeRound,
    );
    final alreadySaved = storedDraft != null && current.any(
      (record) => record.id == (storedDraft['entryId'] ?? '').toString(),
    );
    if (alreadySaved) {
      // Avoid duplicating a record committed just before the process stopped.
      await ExpressRoundDraftStorage.clear(widget.company.id, activeRound);
    }
    final draft = alreadySaved ? null : storedDraft;
    final path = (draft?['photoPath'] ?? '').toString().trim();
    final photoAvailable = path.isNotEmpty &&
        File(path).existsSync() && File(path).lengthSync() > 0;
    if (!mounted) return;
    setState(() {
      roundId = activeRound;""",'restore entry')
edit("""      roundAiConclusion = storedConclusion;
      loading = false;""","""      roundAiConclusion = storedConclusion;
      _roundDraftEntryId = (draft?['entryId'] ?? '').toString().trim();
      if (_roundDraftEntryId.isEmpty) _roundDraftEntryId = uuid.v4();
      _roundDraftRestoring = true;
      _roundDraftDirty = false;
      _draftPhotoMissing = path.isNotEmpty && !photoAvailable;
      if (draft != null) {
        final restoredSector = (draft['sectorId'] ?? '').toString();
        if (restoredSector.isEmpty ||
            loaded.any((value) => value.id == restoredSector)) {
          sectorId = restoredSector.isEmpty ? null : restoredSector;
        }
        final kind = (draft['findingType'] ?? '').toString();
        if (kind == 'Conformidade' || kind == 'Não conformidade') findingType = kind;
        final restoredPriority = (draft['priority'] ?? '').toString();
        if (const ['Baixa', 'Média', 'Alta', 'Crítica']
            .contains(restoredPriority)) priority = restoredPriority;
        recurring = draft['recurring'] == true;
        selectedCategories
          ..clear()
          ..addAll((draft['categories'] is List
              ? draft['categories'] as List : const [])
              .map((value) => value.toString())
              .where((value) => categories.contains(value)));
        description.text = (draft['description'] ?? '').toString();
        location.text = (draft['location'] ?? '').toString();
        photoPath = photoAvailable ? path : '';
        aiTextOriginal = (draft['aiTextOriginal'] ?? '').toString();
        aiTitle = photoAvailable ? (draft['aiTitle'] ?? '').toString() : '';
        aiRisk = (draft['aiRisk'] ?? '').toString();
        aiConsequence = (draft['aiConsequence'] ?? '').toString();
        aiRecommendation = (draft['aiRecommendation'] ?? '').toString();
        aiImmediateAction = (draft['aiImmediateAction'] ?? '').toString();
        aiResponsible = (draft['aiResponsible'] ?? '').toString();
        aiConfidence = (draft['aiConfidence'] ?? '').toString();
        aiReferences = (draft['aiReferences'] is List
            ? draft['aiReferences'] as List : const [])
            .map((value) => value.toString()).toList();
        aiChecks = (draft['aiChecks'] is List
            ? draft['aiChecks'] as List : const [])
            .map((value) => value.toString()).toList();
        _roundDraftStatus = _draftPhotoMissing
            ? 'Rascunho restaurado; foto indisponível. Reanexe a imagem.'
            : 'Rascunho restaurado neste aparelho';
      }
      _roundDraftRestoring = false;
      loading = false;""",'restore fields')
# Preserve the current, already-tested camera/gallery flow; append only the
# post-persistence draft safeguard, independent of layout changes upstream.
photo_start=s.index('  Future<void> _pickPhoto(')
photo_end=s.index('  Future<void> _improveTextWithAi()',photo_start)
if photo_start<0 or photo_end<0:raise RuntimeError('DRAFT photo boundaries missing')
photo=s[photo_start:photo_end]
if 'persisted' not in photo:raise RuntimeError('DRAFT persisted image reference missing')
photo_close=photo.rfind('\n  }')
if photo_close<0:raise RuntimeError('DRAFT photo closing brace missing')
photo=photo[:photo_close]+"""
    if (persisted.isNotEmpty) {
      if (!File(persisted).existsSync() || File(persisted).lengthSync() == 0) {
        _message('A foto não foi copiada para o armazenamento do aplicativo.');
        return;
      }
      _draftPhotoMissing = false;
      _scheduleRoundDraft();
      await _flushRoundDraft();
    }
"""+photo[photo_close:]
s=s[:photo_start]+photo+s[photo_end:]
edit("""        if (_isConformity) priority = 'Baixa';
      });
    }

    titleCtl.dispose();""","""        if (_isConformity) priority = 'Baixa';
      });
      _scheduleRoundDraft();
    }
    titleCtl.dispose();""",'AI results')
edit("""    setState(() => saving = true);
    final now = DateTime.now();""","""    await _flushRoundDraft();
    if (!mounted) return;
    setState(() => saving = true);
    final now = DateTime.now();""",'flush before save')
edit("      final recordId = uuid.v4();\n      final record = SstRecord(",
     "      final recordId = _roundDraftEntryId;\n      final record = SstRecord(",'stable id')
edit("""          'roundType': 'RONDA_EXPRESSA',
          'updatedAt': now.toIso8601String(),""","""          'roundType': 'RONDA_EXPRESSA',
          'localDraftEntryId': recordId,
          'updatedAt': now.toIso8601String(),""",'commit marker')
edit("""      if (!mounted) return;
      setState(() {
        roundRecords.add(record);""","""      await _roundDraftTail;
      try {
        await ExpressRoundDraftStorage.clear(widget.company.id, roundId);
      } catch (_) {
        // On the next open the matching saved record suppresses stale draft.
      }
      if (!mounted) return;
      setState(() {
        _roundDraftEntryId = uuid.v4();
        _roundDraftDirty = false;
        _draftPhotoMissing = false;
        _roundDraftStatus = 'Nenhum registro pendente no rascunho';
        roundRecords.add(record);""",'clear only after commit')
edit("""    final id = targetRoundId.trim();
    if (id.isEmpty) return;
    final db = AppDatabase.instance;""","""    final id = targetRoundId.trim();
    if (id.isEmpty) return;
    if (!viewingHistoricalRound && roundId == activeRoundId) {
      await _flushRoundDraft();
    }
    final db = AppDatabase.instance;""",'keep draft on history switch')
edit("""  Future<void> _finish() async {
    if (roundRecords.isEmpty) {""","""  Future<void> _finish() async {
    if (_roundDraftHasContent && !viewingHistoricalRound) {
      await _flushRoundDraft();
      _message('Há uma ocorrência no rascunho. Salve-a antes de finalizar.');
      return;
    }
    if (roundRecords.isEmpty) {""",'prevent dropped entry')
edit("""          IconButton(
            tooltip: 'Histórico de rondas',""","""          IconButton(
            tooltip: _restoringSavedPhotos
                ? 'Recuperando fotos...' : 'Verificar e recuperar fotos salvas',
            onPressed: roundRecords.isEmpty || _restoringSavedPhotos
                ? null : _restoreSavedRoundPhotos,
            icon: _restoringSavedPhotos
                ? const SizedBox(width: 18, height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.cloud_download_outlined),
          ),
          IconButton(
            tooltip: 'Histórico de rondas',""",'recovery button')
edit("""                    _header(),
                    const SizedBox(height: 12),""","""                    _header(),
                    const SizedBox(height: 7),
                    Card(
                      color: _draftPhotoMissing
                          ? const Color(0xFFFFF2DC) : AuditarBrand.greenSoft,
                      child: ListTile(
                        dense: true,
                        leading: Icon(_draftPhotoMissing
                            ? Icons.warning_amber_rounded : Icons.save_outlined),
                        title: Text(_roundDraftStatus),
                        subtitle: const Text(
                          'Rascunhos ficam neste aparelho. Salve o registro '
                          'e confirme o backup das fotos antes de desinstalar '
                          'ou limpar os dados do aplicativo.',
                          style: TextStyle(fontSize: 11.5)),
                        trailing: IconButton(
                          tooltip: 'Salvar rascunho agora',
                          onPressed: saving || _roundDraftRestoring
                              ? null : () async {
                                  _roundDraftDirty = true;
                                  await _flushRoundDraft(showMessage: true);
                                },
                          icon: const Icon(Icons.save_as_outlined),
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),""",'visible status')
edit("""                      onChanged: (value) => setState(
                        () => sectorId = value == null || value.isEmpty ? null : value,
                      ),""","""                      onChanged: (value) {
                        setState(() =>
                            sectorId = value == null || value.isEmpty ? null : value);
                        _scheduleRoundDraft();
                      },""",'sector')
edit("""                      }),
                    ),
                    const SizedBox(height: 16),
                    _label('2. Fotografe a situação'),""","""                      }),
                    ),
                    const SizedBox(height: 16),
                    _label('2. Fotografe a situação'),""",'placeholder')
# Wrap other selection callbacks with listeners without altering other fields.
edit("""                        }
                      }),
                    ),
                    const SizedBox(height: 16),
                    _label('2. Fotografe a situação'),""","""                        }
                        _scheduleRoundDraft();
                      }),
                    ),
                    const SizedBox(height: 16),
                    _label('2. Fotografe a situação'),""",'finding kind')
edit("""                            } else {
                              selectedCategories.remove(category);
                            }
                          }),""","""                            } else {
                              selectedCategories.remove(category);
                            }
                            _scheduleRoundDraft();
                          }),""",'categories')
edit("""                        onChanged: (value) =>
                            setState(() => priority = value ?? priority),""","""                        onChanged: (value) {
                          setState(() => priority = value ?? priority);
                          _scheduleRoundDraft();
                        },""",'priority')
edit("""                        onChanged: (value) => setState(() => recurring = value),""","""                        onChanged: (value) {
                          setState(() => recurring = value);
                          _scheduleRoundDraft();
                        },""",'recurrence')
edit("""                    photoPath = '';
                    _clearAiState();""","""                    photoPath = '';
                    _draftPhotoMissing = false;
                    _clearAiState();
                    _scheduleRoundDraft();""",'photo removal')
shutil.copyfile(src,helper)
shutil.copyfile(test_src,root/'test/express_round_draft_storage_test.dart')
path.write_text(s,encoding='utf-8',newline='\n')
changed=[p for p,h in before.items() if hashlib.sha256((root/p).read_bytes()).hexdigest()!=h]
if changed:raise SystemExit('PROTECTED SYNC MEDIA DB GS AI MODIFIED: '+repr(changed))
print('ROUND_LOCAL_DRAFT_AND_EXISTING_PHOTO_RECOVERY_OK')
print('SYNC_MEDIA_DATABASE_GS_BYTE_IDENTICAL_OK')

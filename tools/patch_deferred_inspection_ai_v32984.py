#!/usr/bin/env python3
from pathlib import Path
import re, shutil, sys

root=Path(sys.argv[1])
platform=(sys.argv[2] if len(sys.argv)>2 else 'android').lower()
repo=Path.cwd()

def read(rel): return (root/rel).read_text(encoding='utf-8')
def write(rel,text): (root/rel).write_text(text,encoding='utf-8',newline='\n')
def once(text,old,new,label):
    if new in text: return text
    if old not in text: raise RuntimeError('Marcador ausente: '+label)
    return text.replace(old,new,1)

version='3.30.12+199' if platform=='windows' else '3.29.84+226'
pub=read('pubspec.yaml')
pub,n=re.subn(r'^version:\s*[^\n]+',f'version: {version}',pub,count=1,flags=re.M)
if n!=1: raise RuntimeError('Versao nao localizada')
write('pubspec.yaml',pub)

src=repo/'build_sources/v3.29.84-deferred-inspection-ai/inspection_photo_ai_queue_service.dart'
dst=root/'lib/services/inspection_photo_ai_queue_service.dart'
dst.parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(src,dst)

# ------------------------------------------------------------
# CHECKLIST: marcar foto de NC/Parcial para IA posterior.
# ------------------------------------------------------------
rel='lib/screens/checklist_screen.dart'
c=read(rel)

c=once(
    c,
    "  final Map<String, bool> fineShowInReport = {};\n  final Map<String, List<String>> photos = {};\n",
    "  final Map<String, bool> fineShowInReport = {};\n"
    "  final Map<String, Map<String, dynamic>> aiPhotoMeta = {};\n"
    "  final Map<String, List<String>> photos = {};\n",
    'state aiPhotoMeta',
)

c=once(
    c,
    "      fineShowInReport[item.id] = false;\n      priorities[item.id] = item.priority;\n",
    "      fineShowInReport[item.id] = false;\n"
    "      aiPhotoMeta[item.id] = <String, dynamic>{};\n"
    "      priorities[item.id] = item.priority;\n",
    'init aiPhotoMeta',
)

# Load meta from occurrences JSON.
load_anchor="""            final fine = decoded['fine'];
            if (fine is Map) {
"""
load_insert="""            final aiPhoto = decoded['aiPhoto'];
            if (aiPhoto is Map) {
              aiPhotoMeta[answer.questionId] =
                  Map<String, dynamic>.from(aiPhoto);
            }
            final fine = decoded['fine'];
            if (fine is Map) {
"""
c=once(c,load_anchor,load_insert,'load ai photo meta')

# Helper to invalidate/requeue when photo/status changes.
helper_anchor="""  String _occurrencesPayload(String itemId) {
"""
helper=r'''  void _markAiPhotoPending(String itemId) {
    final status = statuses[itemId] ?? '';
    final hasPhotos = (photos[itemId] ?? const <String>[]).isNotEmpty;
    if ((status == 'Não Conforme' || status == 'Parcial') && hasPhotos) {
      aiPhotoMeta[itemId] = <String, dynamic>{
        'status': 'PENDENTE',
        'queuedAt': DateTime.now().toUtc().toIso8601String(),
        'lastError': '',
      };
    } else {
      aiPhotoMeta[itemId] = <String, dynamic>{};
    }
  }

'''
if '_markAiPhotoPending(String itemId)' not in c:
    c=once(c,helper_anchor,helper+helper_anchor,'helper ai pending')

# Add aiPhoto to occurrences JSON and auto queue issue photos.
old_occ="""  String _occurrencesPayload(String itemId) {
    final fineCents = _fineAmountCents(itemId);
    return jsonEncode({
      'version': 3,
      'fine': {
"""
new_occ="""  String _occurrencesPayload(String itemId) {
    final fineCents = _fineAmountCents(itemId);
    final currentAi = Map<String, dynamic>.from(
      aiPhotoMeta[itemId] ?? const <String, dynamic>{},
    );
    final aiStatus = '\${currentAi['status'] ?? ''}'.toUpperCase();
    final eligibleForLaterAi =
        (statuses[itemId] == 'Não Conforme' || statuses[itemId] == 'Parcial') &&
        (photos[itemId] ?? const <String>[]).isNotEmpty;
    if (eligibleForLaterAi &&
        !const ['PRONTA_REVISAO', 'APLICADA', 'DESCARTADA']
            .contains(aiStatus)) {
      currentAi['status'] = 'PENDENTE';
      currentAi.putIfAbsent(
        'queuedAt',
        () => DateTime.now().toUtc().toIso8601String(),
      );
    }
    return jsonEncode({
      'version': 4,
      'aiPhoto': currentAi,
      'fine': {
"""
c=once(c,old_occ,new_occ,'occurrences ai photo')

# Photo add/removal makes prior AI stale.
c=once(
    c,
    """    if (mounted) {
      setState(() => photos[itemId]!.add(storedPath));
      _scheduleDraftSave();
    }
""",
    """    if (mounted) {
      setState(() {
        photos[itemId]!.add(storedPath);
        _markAiPhotoPending(itemId);
      });
      _scheduleDraftSave();
    }
""",
    'camera marks ai pending',
)
c=once(
    c,
    """    if (mounted) {
      setState(() => photos[itemId]!.addAll(added));
      _scheduleDraftSave();
    }
""",
    """    if (mounted) {
      setState(() {
        photos[itemId]!.addAll(added);
        _markAiPhotoPending(itemId);
      });
      _scheduleDraftSave();
    }
""",
    'gallery marks ai pending',
)
c=once(
    c,
    """  void _removePhoto(String itemId, int index) {
    setState(() {
      photos[itemId]!.removeAt(index);
    });
    _scheduleDraftSave();
  }
""",
    """  void _removePhoto(String itemId, int index) {
    setState(() {
      photos[itemId]!.removeAt(index);
      _markAiPhotoPending(itemId);
    });
    _scheduleDraftSave();
  }
""",
    'remove photo marks ai pending',
)

# Immediate AI status lifecycle.
c=once(
    c,
    """    setState(() => analyzingItems.add(item.id));
    final reply = await AiAssistantService.analyzeChecklistPhotos(
""",
    """    setState(() {
      analyzingItems.add(item.id);
      aiPhotoMeta[item.id] = <String, dynamic>{
        'status': 'ANALISANDO',
        'startedAt': DateTime.now().toUtc().toIso8601String(),
        'lastError': '',
      };
    });
    _scheduleDraftSave();
    final reply = await AiAssistantService.analyzeChecklistPhotos(
""",
    'immediate ai analyzing status',
)

c=once(
    c,
    """    if (!reply.success) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(reply.message)),
      );
      return;
    }

    final result = reply.result;
""",
    """    if (!reply.success) {
      setState(() {
        aiPhotoMeta[item.id] = <String, dynamic>{
          'status': 'ERRO',
          'lastError': reply.message,
          'failedAt': DateTime.now().toUtc().toIso8601String(),
        };
      });
      _scheduleDraftSave();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(reply.message)),
      );
      return;
    }

    final result = reply.result;
    setState(() {
      aiPhotoMeta[item.id] = <String, dynamic>{
        'status': 'PRONTA_REVISAO',
        'result': result,
        'analyzedAt': DateTime.now().toUtc().toIso8601String(),
        'lastError': '',
      };
    });
    _scheduleDraftSave();
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text(
          'IA concluiu a análise. A sugestão ficou salva para revisão; continue a vistoria normalmente.',
        ),
      ),
    );
    return;
""",
    'immediate ai ready status',
)

c=once(
    c,
    """    if (useSuggestion != true || !mounted) return;
    setState(() {
      if (description.isNotEmpty) observations[item.id]!.text = description;
""",
    """    if (useSuggestion != true || !mounted) return;
    setState(() {
      aiPhotoMeta[item.id] = <String, dynamic>{
        ...aiPhotoMeta[item.id] ?? const <String, dynamic>{},
        'status': 'APLICADA',
        'appliedAt': DateTime.now().toUtc().toIso8601String(),
      };
      if (description.isNotEmpty) observations[item.id]!.text = description;
""",
    'immediate ai applied status',
)

# Status changes should queue/clear.
c=once(
    c,
    """    setState(() {
      statuses[itemId] = value;
      if (value != 'Não Conforme') {
        _expandedAnswered.remove(itemId);
      }
    });
    _scheduleDraftSave();
""",
    """    setState(() {
      statuses[itemId] = value;
      if (value != 'Não Conforme') {
        _expandedAnswered.remove(itemId);
      }
      _markAiPhotoPending(itemId);
    });
    _scheduleDraftSave();
""",
    'status change ai pending',
)

# UI wording: optional now, clear later path.
c=c.replace(
    "'Analisar fotos com IA'",
    "'Analisar em segundo plano com IA (opcional)'",
    1,
)
old_note="""                            const Text(
                              'Antes da análise você poderá informar, opcionalmente, o que observou no local. A IA combinará essa informação com até 4 fotos. Evite rostos, crachás, documentos e outros dados pessoais.',
                              style: TextStyle(
                                fontSize: 11.5,
                                color: Colors.black54,
                              ),
                            ),
"""
new_note="""                            const Text(
                              'Você pode continuar respondendo o checklist enquanto a IA analisa. Quando terminar, a sugestão ficará salva para revisão e não abrirá nenhuma janela automaticamente. Se preferir, também pode analisar depois pela tela Relatórios. Evite rostos, crachás, documentos e outros dados pessoais.',
                              style: TextStyle(
                                fontSize: 11.5,
                                color: Colors.black54,
                              ),
                            ),
"""
c=once(c,old_note,new_note,'later ai checklist note')
write(rel,c)

# ------------------------------------------------------------
# REPORT SCREEN: background queue + review ready suggestions.
# ------------------------------------------------------------
rel='lib/screens/report_screen.dart'
r=read(rel)
if "import 'dart:async';" not in r:
    r="import 'dart:async';\n\n"+r
if "import '../services/inspection_photo_ai_queue_service.dart';" not in r:
    r=once(
        r,
        "import '../services/drive_service.dart';\n",
        "import '../services/drive_service.dart';\n"
        "import '../services/inspection_photo_ai_queue_service.dart';\n",
        'import photo ai queue',
    )

r=once(
    r,
    """  bool aiReviewBusy = false;
  bool aiActionPlanBusy = false;
""",
    """  bool aiReviewBusy = false;
  bool aiActionPlanBusy = false;
  bool photoAiStarting = false;
  int photoAiPending = 0;
  int photoAiReady = 0;
  int photoAiErrors = 0;
  int photoAiApplied = 0;
  Timer? photoAiPollTimer;
""",
    'report ai photo state',
)

# dispose
init_anchor="""  @override
  void initState() {
    super.initState();
    _load();
  }

"""
dispose_block="""  @override
  void dispose() {
    photoAiPollTimer?.cancel();
    super.dispose();
  }

"""
if "photoAiPollTimer?.cancel();" not in r:
    r=once(r,init_anchor,init_anchor+dispose_block,'report dispose')

# Load queue state.
r=once(
    r,
    """    final template = await ReportTemplateService.resolveForHeader(header);

    if (!mounted) return;
""",
    """    final template = await ReportTemplateService.resolveForHeader(header);
    final photoAiState =
        await InspectionPhotoAiQueueService.state(widget.inspectionId);

    if (!mounted) return;
""",
    'load photo ai state',
)
r=once(
    r,
    """      selectedReportTemplate = template;

      if (existing != null) {
""",
    """      selectedReportTemplate = template;
      photoAiPending = photoAiState.pending + photoAiState.analyzing;
      photoAiReady = photoAiState.ready;
      photoAiErrors = photoAiState.errors;
      photoAiApplied = photoAiState.applied;

      if (existing != null) {
""",
    'assign photo ai state',
)

# Methods before critical reviewer.
method_anchor="""  Future<void> _openCriticalAiReviewer() async {
"""
methods=r'''  Future<void> _refreshPhotoAiState() async {
    final state =
        await InspectionPhotoAiQueueService.state(widget.inspectionId);
    if (!mounted) return;
    setState(() {
      photoAiPending = state.pending + state.analyzing;
      photoAiReady = state.ready;
      photoAiErrors = state.errors;
      photoAiApplied = state.applied;
      photoAiStarting = state.running;
    });
  }

  void _startPhotoAiPoll() {
    photoAiPollTimer?.cancel();
    photoAiPollTimer = Timer.periodic(
      const Duration(seconds: 3),
      (_) async {
        await _refreshPhotoAiState();
        if (!InspectionPhotoAiQueueService.isRunning(widget.inspectionId)) {
          photoAiPollTimer?.cancel();
        }
      },
    );
  }

  Future<void> _startPhotoAiBackground() async {
    if (photoAiStarting ||
        InspectionPhotoAiQueueService.isRunning(widget.inspectionId)) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('A IA já está analisando as fotos desta vistoria.'),
        ),
      );
      return;
    }

    setState(() => photoAiStarting = true);
    _startPhotoAiPoll();
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text(
          'Análise iniciada em segundo plano. Você pode continuar usando o app e gerar o relatório normalmente.',
        ),
        duration: Duration(seconds: 5),
      ),
    );

    unawaited(
      InspectionPhotoAiQueueService.processPending(widget.inspectionId)
          .then((summary) async {
        if (!mounted) return;
        await _refreshPhotoAiState();
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'IA das fotos: \${summary.completed} concluída(s), '
              '\${summary.failed} com erro. Revise as sugestões antes de aplicar.',
            ),
          ),
        );
      }).whenComplete(() {
        if (mounted) {
          setState(() => photoAiStarting = false);
        }
      }),
    );
  }

  Widget _photoAiTextBlock(String label, String value) {
    if (value.trim().isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 9),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w800,
              color: AuditarBrand.navyDark,
            ),
          ),
          const SizedBox(height: 3),
          SelectableText(value),
        ],
      ),
    );
  }

  Future<String?> _reviewPhotoAiSuggestion(
    InspectionPhotoAiSuggestion suggestion,
  ) async {
    final answer = suggestion.answer;
    final result = suggestion.result;
    String text(String key) => '\${result[key] ?? ''}'.trim();
    final recommendation = <String>[
      text('recommendation'),
      text('correctiveAction'),
    ].where((value) => value.isNotEmpty).join('\\n');

    return showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(
          answer.questionText.trim().isEmpty
              ? 'Sugestão da IA'
              : answer.questionText,
        ),
        content: SizedBox(
          width: 700,
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.amber.withValues(alpha: .12),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Text(
                    'A IA analisou a foto depois da vistoria. Compare a sugestão com o que você observou antes de aplicar.',
                    style: TextStyle(fontSize: 12.5),
                  ),
                ),
                const SizedBox(height: 12),
                _photoAiTextBlock(
                  'Descrição atual',
                  answer.observation,
                ),
                _photoAiTextBlock(
                  'Descrição sugerida',
                  text('description'),
                ),
                _photoAiTextBlock(
                  'Risco atual',
                  answer.riskIdentified,
                ),
                _photoAiTextBlock(
                  'Risco sugerido',
                  text('risk'),
                ),
                _photoAiTextBlock(
                  'Recomendação atual',
                  answer.recommendation,
                ),
                _photoAiTextBlock(
                  'Recomendação sugerida',
                  recommendation,
                ),
                if (text('priority').isNotEmpty)
                  _photoAiTextBlock(
                    'Prioridade sugerida',
                    text('priority'),
                  ),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, 'later'),
            child: const Text('Revisar depois'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, 'dismiss'),
            child: const Text('Descartar sugestão'),
          ),
          FilledButton.icon(
            onPressed: () => Navigator.pop(dialogContext, 'apply'),
            icon: const Icon(Icons.check),
            label: const Text('Aplicar ao relatório'),
          ),
        ],
      ),
    );
  }

  Future<void> _reviewReadyPhotoAi() async {
    final suggestions =
        await InspectionPhotoAiQueueService.readySuggestions(
      widget.inspectionId,
    );
    if (!mounted) return;
    if (suggestions.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Não há sugestões de fotos aguardando revisão.'),
        ),
      );
      return;
    }

    var applied = 0;
    var dismissed = 0;
    for (final suggestion in suggestions) {
      if (!mounted) break;
      final action = await _reviewPhotoAiSuggestion(suggestion);
      if (!mounted || action == null || action == 'later') break;
      if (action == 'apply') {
        await InspectionPhotoAiQueueService.applySuggestion(suggestion);
        applied++;
      } else if (action == 'dismiss') {
        await InspectionPhotoAiQueueService.dismissSuggestion(suggestion);
        dismissed++;
      }
    }

    await _load();
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          '\$applied sugestão(ões) aplicada(s) e '
          '\$dismissed descartada(s). Gere o PDF novamente para refletir alterações.',
        ),
      ),
    );
  }

'''
if '_startPhotoAiBackground()' not in r:
    r=once(r,method_anchor,methods+method_anchor,'report photo ai methods')

# Insert card before existing Revisao final com IA card.
card_anchor="""          Card(
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
              side: BorderSide(color: AuditarBrand.green.withOpacity(.35)),
            ),
            child: Padding(
              padding: const EdgeInsets.all(15),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
"""
photo_card=r'''          Card(
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
              side: BorderSide(color: Colors.deepPurple.shade200),
            ),
            child: Padding(
              padding: const EdgeInsets.all(15),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        Icons.photo_library_outlined,
                        color: Colors.deepPurple.shade700,
                      ),
                      const SizedBox(width: 9),
                      const Expanded(
                        child: Text(
                          'IA das fotos sem atrasar a vistoria',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w800,
                            color: AuditarBrand.navyDark,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 7),
                  const Text(
                    'Você pode gerar e compartilhar o relatório agora. As fotos de itens Não Conforme/Parcial podem ser analisadas depois; a IA prepara sugestões e só altera o registro após sua aprovação.',
                    style: TextStyle(height: 1.35),
                  ),
                  const SizedBox(height: 10),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      Chip(
                        label: Text('Pendentes: \$photoAiPending'),
                      ),
                      Chip(
                        label: Text('Prontas para revisão: \$photoAiReady'),
                      ),
                      if (photoAiErrors > 0)
                        Chip(
                          label: Text('Erros/tentar novamente: \$photoAiErrors'),
                        ),
                      if (photoAiApplied > 0)
                        Chip(
                          label: Text('Aplicadas: \$photoAiApplied'),
                        ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  if (photoAiPending > 0 || photoAiErrors > 0)
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton.tonalIcon(
                        onPressed: photoAiStarting
                            ? null
                            : _startPhotoAiBackground,
                        icon: photoAiStarting
                            ? const SizedBox(
                                width: 18,
                                height: 18,
                                child:
                                    CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Icon(Icons.auto_awesome_outlined),
                        label: Text(
                          photoAiStarting
                              ? 'IA analisando em segundo plano...'
                              : 'Analisar fotos em segundo plano',
                        ),
                      ),
                    ),
                  if (photoAiReady > 0) ...[
                    const SizedBox(height: 8),
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton.icon(
                        onPressed: _reviewReadyPhotoAi,
                        icon: const Icon(Icons.fact_check_outlined),
                        label: Text(
                          'Revisar \$photoAiReady sugestão(ões) pronta(s)',
                        ),
                      ),
                    ),
                  ],
                  const SizedBox(height: 7),
                  Text(
                    'Enquanto o app permanecer aberto, a fila continua mesmo se você sair desta tela. Se o app for fechado, o que faltar permanece pendente para retomar depois.',
                    style: TextStyle(
                      color: Colors.grey.shade700,
                      fontSize: 11.5,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 14),
'''
if "IA das fotos sem atrasar a vistoria" not in r:
    r=once(r,card_anchor,photo_card+card_anchor,'report photo ai card')

write(rel,r)

# Assertions
checks={
 'lib/screens/checklist_screen.dart':[
   "'aiPhoto': currentAi",
   "Analisar em segundo plano com IA (opcional)",
   "não abrirá nenhuma janela automaticamente",
   "'status': 'PRONTA_REVISAO'",
 ],
 'lib/screens/report_screen.dart':[
   "IA das fotos sem atrasar a vistoria",
   "_startPhotoAiBackground",
   "_reviewReadyPhotoAi",
   "Analisar fotos em segundo plano",
 ],
 'lib/services/inspection_photo_ai_queue_service.dart':[
   "class InspectionPhotoAiQueueService",
   "'PRONTA_REVISAO'",
   "processPending",
 ],
}
for rel,markers in checks.items():
    text=read(rel)
    for marker in markers:
        assert marker in text, f'{rel}: ausente {marker}'
assert f'version: {version}' in read('pubspec.yaml')
print('DEFERRED_INSPECTION_AI_OK',platform,version)

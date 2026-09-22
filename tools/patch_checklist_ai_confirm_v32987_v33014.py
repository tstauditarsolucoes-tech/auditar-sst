#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) < 2:
    raise SystemExit("uso: patch_checklist_ai_confirm_v32987_v33014.py <APP_DIR> [android|windows]")

root = Path(sys.argv[1])
platform = (sys.argv[2] if len(sys.argv) > 2 else "android").lower()

def read(rel):
    return (root / rel).read_text(encoding="utf-8")

def write(rel, text):
    (root / rel).write_text(text, encoding="utf-8", newline="\n")

def replace_dart_method(text, signature, replacement):
    start = text.find(signature)
    if start < 0:
        raise RuntimeError("método não localizado: " + signature)
    brace = text.find("{", start)
    if brace < 0:
        raise RuntimeError("abertura não localizada: " + signature)
    depth = 0
    quote = None
    escape = False
    line_comment = False
    block_comment = False
    i = brace
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if line_comment:
            if ch == "\n":
                line_comment = False
            i += 1
            continue
        if block_comment:
            if ch == "*" and nxt == "/":
                block_comment = False
                i += 2
                continue
            i += 1
            continue
        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
            i += 1
            continue
        if ch == "/" and nxt == "/":
            line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            block_comment = True
            i += 2
            continue
        if ch in ("'", '"'):
            quote = ch
            i += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[:start] + replacement.rstrip() + text[i + 1:]
        i += 1
    raise RuntimeError("fim não localizado: " + signature)

rel = "lib/services/inspection_photo_ai_queue_service.dart"
q = read(rel)

if "_suggestionListeners" not in q:
    marker = """  static final Map<String, Map<String, dynamic>> _liveMeta =
      <String, Map<String, dynamic>>{};
"""
    replacement = marker + """
  static final Map<
      String,
      Future<void> Function(InspectionPhotoAiSuggestion suggestion)>
      _suggestionListeners =
      <String,
          Future<void> Function(InspectionPhotoAiSuggestion suggestion)>{};
"""
    if marker not in q:
        raise RuntimeError("mapa liveMeta não localizado")
    q = q.replace(marker, replacement, 1)

if "static void setSuggestionListener(" not in q:
    marker = """  static void rememberMeta(
    String inspectionId,
    String questionId,
    Map<String, dynamic> meta,
  ) {
    _liveMeta[_liveKey(inspectionId, questionId)] =
        Map<String, dynamic>.from(meta);
  }
"""
    addition = marker + """
  static void setSuggestionListener(
    String inspectionId,
    Future<void> Function(InspectionPhotoAiSuggestion suggestion) listener,
  ) {
    _suggestionListeners[inspectionId] = listener;
  }

  static void clearSuggestionListener(String inspectionId) {
    _suggestionListeners.remove(inspectionId);
  }
"""
    if marker not in q:
        raise RuntimeError("rememberMeta não localizado")
    q = q.replace(marker, addition, 1)

old_ready = """        completed++;
        await _saveMeta(
          latest,
          <String, dynamic>{
            ..._aiMeta(latest),
            'status': 'PRONTA_REVISAO',
            'result': reply.result,
            'analyzedAt': DateTime.now().toUtc().toIso8601String(),
            'lastError': '',
          },
        );
"""
new_ready = """        completed++;
        final readyMeta = <String, dynamic>{
          ..._aiMeta(latest),
          'status': 'PRONTA_REVISAO',
          'result': reply.result,
          'analyzedAt': DateTime.now().toUtc().toIso8601String(),
          'lastError': '',
        };
        await _saveMeta(latest, readyMeta);

        final listener = _suggestionListeners[inspectionId];
        if (listener != null) {
          await listener(
            InspectionPhotoAiSuggestion(
              answer: latest,
              result: Map<String, dynamic>.from(reply.result),
            ),
          );
        }
"""
if new_ready not in q:
    if old_ready not in q:
        raise RuntimeError("conclusão PRONTA_REVISAO não localizada")
    q = q.replace(old_ready, new_ready, 1)

old_finally = """    } finally {
      _running.remove(inspectionId);
    }
"""
new_finally = """    } finally {
      _running.remove(inspectionId);
      _suggestionListeners.remove(inspectionId);
    }
"""
if new_finally not in q:
    if old_finally not in q:
        raise RuntimeError("finally da fila não localizado")
    q = q.replace(old_finally, new_finally, 1)

write(rel, q)

rel = "lib/screens/checklist_screen.dart"
c = read(rel)

dialog_methods = r'''  Future<void> _showCompletedAiSuggestion(
    InspectionPhotoAiSuggestion suggestion,
  ) async {
    if (!mounted) return;

    final result = suggestion.result;
    final questionId = suggestion.answer.questionId;
    String text(String key) => '${result[key] ?? ''}'.trim();

    final description = text('description');
    final risk = text('risk');
    final immediateAction = text('immediateAction');
    final technicalRecommendation = text('recommendation');
    final correctiveAction = text('correctiveAction');
    final responsibleProfile = text('responsibleProfile');
    final priority = text('priority');
    final deadline = result['suggestedDeadlineDays'];

    final recommendation = <String>[
      if (immediateAction.isNotEmpty)
        'Ação imediata: $immediateAction',
      if (technicalRecommendation.isNotEmpty)
        technicalRecommendation,
      if (correctiveAction.isNotEmpty)
        'Ação corretiva sugerida: $correctiveAction',
      if (responsibleProfile.isNotEmpty)
        'Responsável sugerido: $responsibleProfile',
      if (deadline != null)
        'Prazo inicial sugerido: $deadline dia(s)',
    ].join('\n');

    final useSuggestion = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Sugestão da IA'),
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
                    'Rascunho de apoio. Confirme a situação no local e edite o texto antes de usar no relatório.',
                    style: TextStyle(fontSize: 12.5, height: 1.35),
                  ),
                ),
                const SizedBox(height: 12),
                _aiSuggestionField('Descrição sugerida', description),
                _aiSuggestionField('Risco identificado', risk),
                _aiSuggestionField('Ação imediata', immediateAction),
                _aiSuggestionField(
                  'Recomendação técnica',
                  technicalRecommendation,
                ),
                _aiSuggestionField(
                  'Ação corretiva sugerida',
                  correctiveAction,
                ),
                _aiSuggestionField(
                  'Responsável sugerido',
                  responsibleProfile,
                ),
                if (deadline != null)
                  _aiSuggestionField(
                    'Prazo sugerido',
                    '$deadline dia(s)',
                  ),
                _aiSuggestionField('Prioridade sugerida', priority),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('Não usar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('Usar e editar'),
          ),
        ],
      ),
    );

    if (!mounted) return;

    if (useSuggestion != true) {
      await InspectionPhotoAiQueueService.dismissSuggestion(suggestion);
      if (!mounted) return;
      setState(() {
        analyzingItems.remove(questionId);
        aiPhotoMeta[questionId] = <String, dynamic>{
          ...(aiPhotoMeta[questionId] ?? const <String, dynamic>{}),
          'status': 'DESCARTADA',
          'dismissedAt': DateTime.now().toUtc().toIso8601String(),
        };
      });
      _scheduleDraftSave();
      return;
    }

    await InspectionPhotoAiQueueService.applySuggestion(suggestion);
    if (!mounted) return;

    setState(() {
      if (description.isNotEmpty && observations[questionId] != null) {
        observations[questionId]!.text = description;
      }
      if (risk.isNotEmpty && risks[questionId] != null) {
        risks[questionId]!.text = risk;
      }
      if (recommendation.isNotEmpty && recommendations[questionId] != null) {
        recommendations[questionId]!.text = recommendation;
      }
      if (const ['Baixa', 'Média', 'Alta', 'Crítica'].contains(priority)) {
        priorities[questionId] = priority;
      }
      aiPhotoMeta[questionId] = <String, dynamic>{
        ...(aiPhotoMeta[questionId] ?? const <String, dynamic>{}),
        'status': 'APLICADA',
        'result': result,
        'appliedAt': DateTime.now().toUtc().toIso8601String(),
      };
      analyzingItems.remove(questionId);
    });

    await _saveDraft();
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text(
          'Sugestão aplicada. Descrição, risco e recomendação foram preenchidos e continuam editáveis.',
        ),
      ),
    );
  }

'''

if "_showCompletedAiSuggestion(" not in c:
    marker = "  Future<void> _analyzeWithAi(ChecklistItem item) async {"
    if marker not in c:
        raise RuntimeError("_analyzeWithAi não localizado para inserir diálogo")
    c = c.replace(marker, dialog_methods + marker, 1)

new_analyze = r'''  Future<void> _analyzeWithAi(ChecklistItem item) async {
    final evidence = photos[item.id] ?? const <String>[];
    if (evidence.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Tire ou escolha pelo menos uma foto antes de analisar.'),
        ),
      );
      return;
    }

    final currentStatus = statuses[item.id] ?? '';
    if (currentStatus != 'Não Conforme' && currentStatus != 'Parcial') {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Para análise de evidência, marque primeiro o item como Não Conforme ou Parcial.',
          ),
        ),
      );
      return;
    }

    final inspectionId = widget.inspection.id;
    final queueWasRunning =
        InspectionPhotoAiQueueService.isRunning(inspectionId);

    InspectionPhotoAiQueueService.setSuggestionListener(
      inspectionId,
      (suggestion) async {
        if (!mounted) return;
        await _showCompletedAiSuggestion(suggestion);
      },
    );

    setState(() {
      _markAiPhotoPending(item.id);
      analyzingItems.add(item.id);
    });

    await _saveDraft();
    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          queueWasRunning
              ? 'Foto adicionada à fila. Continue a vistoria; o resultado aparecerá quando ficar pronto.'
              : 'Análise iniciada. Continue a vistoria; o resultado aparecerá quando ficar pronto.',
        ),
        duration: const Duration(seconds: 4),
      ),
    );

    if (queueWasRunning) {
      return;
    }

    unawaited(
      InspectionPhotoAiQueueService.processPending(inspectionId)
          .then((summary) async {
        final answers = await AppDatabase.instance.getAnswers(inspectionId);
        final refreshed = <String, Map<String, dynamic>>{};
        for (final answer in answers) {
          final raw = answer.occurrencesJson.trim();
          if (raw.isEmpty) continue;
          try {
            final decoded = jsonDecode(raw);
            if (decoded is! Map) continue;
            final meta = decoded['aiPhoto'];
            if (meta is Map) {
              refreshed[answer.questionId] =
                  Map<String, dynamic>.from(meta);
            }
          } catch (_) {}
        }

        if (!mounted) return;
        setState(() {
          for (final entry in refreshed.entries) {
            aiPhotoMeta[entry.key] = entry.value;
          }
          analyzingItems.removeWhere((questionId) {
            final status =
                '${aiPhotoMeta[questionId]?['status'] ?? ''}'
                    .toUpperCase();
            return status != 'ANALISANDO' && status != 'PENDENTE';
          });
        });

        if (summary.failed > 0) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                '${summary.failed} foto(s) ficaram pendentes por instabilidade da Central. Você pode tentar novamente no final da vistoria.',
              ),
              duration: const Duration(seconds: 5),
            ),
          );
        }
      }).catchError((_) {
        if (!mounted) return;
        setState(() => analyzingItems.clear());
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'A análise ficou pendente. A foto continua salva e pode ser processada no final da vistoria.',
            ),
          ),
        );
      }),
    );
  }'''

c = replace_dart_method(
    c,
    "  Future<void> _analyzeWithAi(ChecklistItem item) async",
    new_analyze,
)

c = c.replace(
    "'IA trabalhando em segundo plano...'",
    "'IA analisando... continue a vistoria'",
)
c = c.replace(
    "'Enviar para fila da IA (opcional)'",
    "'Analisar foto com IA'",
)
c = c.replace(
    "Você pode continuar descendo e respondendo o checklist enquanto a IA trabalha. Nenhuma janela será aberta quando terminar. Se preferir, não analise agora: no final da vistoria use “Analisar todas as fotos pendentes”. Evite rostos, crachás, documentos e outros dados pessoais.",
    "Você pode continuar descendo e respondendo o checklist enquanto a IA analisa. Assim que terminar, a sugestão aparecerá para você confirmar. Se preferir, deixe as fotos para analisar no final da vistoria. Evite rostos, crachás, documentos e outros dados pessoais.",
)
write(rel, c)

rel = "lib/screens/report_screen.dart"
r = read(rel)

for token in [
    'photoAiPending',
    'photoAiReady',
    'photoAiErrors',
    'photoAiApplied',
    'applied',
    'dismissed',
]:
    r = r.replace('\\\\$' + token, '$' + token)
    r = r.replace('\\$' + token, '$' + token)

for token in ['summary.completed', 'summary.failed']:
    r = r.replace('\\\\${' + token + '}', '${' + token + '}')
    r = r.replace('\\${' + token + '}', '${' + token + '}')

r = r.replace(
    "'IA das fotos sem atrasar a vistoria'",
    "'Análise de fotos no final'",
)
r = r.replace(
    "As fotos de itens Não Conforme/Parcial podem ser analisadas aqui, depois que a coleta de campo terminar. A IA trabalha em fila, prepara sugestões e só altera o registro após sua aprovação.",
    "Se preferir não esperar durante a vistoria, analise aqui todas as fotos pendentes. A IA prepara as sugestões e você confirma antes de preencher os registros.",
)
r = r.replace(
    "'IA analisando em segundo plano...'",
    "'IA analisando as fotos...'",
)

old_summary = """        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'IA das fotos: ${summary.completed} concluída(s), '
              '${summary.failed} com erro. Revise as sugestões antes de aplicar.',
            ),
          ),
        );
"""
new_summary = """        if (summary.completed > 0 && photoAiReady > 0) {
          await _reviewReadyPhotoAi();
          return;
        }
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'IA das fotos: ${summary.completed} concluída(s), '
              '${summary.failed} com erro.',
            ),
          ),
        );
"""
if old_summary in r:
    r = r.replace(old_summary, new_summary, 1)

write(rel, r)

rel = "pubspec.yaml"
pub = read(rel)
version = "3.30.14+201" if platform == "windows" else "3.29.87+229"
pub, count = re.subn(
    r"(?m)^version:\s*[^\r\n]+",
    "version: " + version,
    pub,
    count=1,
)
if count != 1:
    raise RuntimeError("versão não localizada")
write(rel, pub)

queue = read("lib/services/inspection_photo_ai_queue_service.dart")
check = read("lib/screens/checklist_screen.dart")
report = read("lib/screens/report_screen.dart")

for marker in [
    "_suggestionListeners",
    "setSuggestionListener",
    "await listener(",
    "_analyzeWithRetry",
]:
    assert marker in queue, "fila sem " + marker

for marker in [
    "Sugestão da IA",
    "Usar e editar",
    "Não usar",
    "observations[questionId]!.text = description",
    "risks[questionId]!.text = risk",
    "recommendations[questionId]!.text = recommendation",
    "Analisar foto com IA",
    "o resultado aparecerá quando ficar pronto",
]:
    assert marker in check, "checklist sem " + marker

assert "Nenhuma janela será aberta quando terminar" not in check
assert r"\$photoAiPending" not in report
assert r"\${summary.completed}" not in report
assert "Análise de fotos no final" in report
assert f"version: {version}" in read("pubspec.yaml")
print("CHECKLIST_AI_CONFIRM_OK", platform, version)

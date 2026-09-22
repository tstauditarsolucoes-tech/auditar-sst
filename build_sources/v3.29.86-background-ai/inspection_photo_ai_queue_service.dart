import 'dart:convert';

import '../database.dart';
import '../models.dart';
import 'ai_assistant_service.dart';

class InspectionPhotoAiQueueState {
  final int pending;
  final int analyzing;
  final int ready;
  final int applied;
  final int errors;
  final int eligible;
  final bool running;

  const InspectionPhotoAiQueueState({
    required this.pending,
    required this.analyzing,
    required this.ready,
    required this.applied,
    required this.errors,
    required this.eligible,
    required this.running,
  });

  int get waiting => pending + analyzing + errors;
}

class InspectionPhotoAiSuggestion {
  final InspectionAnswer answer;
  final Map<String, dynamic> result;

  const InspectionPhotoAiSuggestion({
    required this.answer,
    required this.result,
  });
}

class InspectionPhotoAiQueueSummary {
  final int completed;
  final int failed;
  final int skipped;

  const InspectionPhotoAiQueueSummary({
    required this.completed,
    required this.failed,
    required this.skipped,
  });
}

class InspectionPhotoAiQueueService {
  static final Set<String> _running = <String>{};

  // Estado vivo compartilhado com a tela do checklist. Ele evita que um
  // auto-save feito enquanto a IA trabalha devolva PENDENTE sobre um resultado
  // que já ficou PRONTA_REVISAO no banco.
  static final Map<String, Map<String, dynamic>> _liveMeta =
      <String, Map<String, dynamic>>{};

  static String _liveKey(String inspectionId, String questionId) =>
      '$inspectionId::$questionId';

  static bool isRunning(String inspectionId) =>
      _running.contains(inspectionId);

  static Map<String, dynamic>? liveMeta(
    String inspectionId,
    String questionId,
  ) {
    final value = _liveMeta[_liveKey(inspectionId, questionId)];
    return value == null ? null : Map<String, dynamic>.from(value);
  }

  static void rememberMeta(
    String inspectionId,
    String questionId,
    Map<String, dynamic> meta,
  ) {
    _liveMeta[_liveKey(inspectionId, questionId)] =
        Map<String, dynamic>.from(meta);
  }

  static Future<InspectionPhotoAiQueueState> state(
    String inspectionId,
  ) async {
    final db = AppDatabase.instance;
    final answers = await db.getAnswers(inspectionId);
    var pending = 0;
    var analyzing = 0;
    var ready = 0;
    var applied = 0;
    var errors = 0;
    var eligible = 0;

    for (final answer in answers) {
      final photos = await db.getPhotosForAnswer(answer.id);
      if (!_eligible(answer, photos)) continue;
      eligible++;
      final meta = _aiMeta(answer);
      rememberMeta(answer.inspectionId, answer.questionId, meta);
      final status = '${meta['status'] ?? ''}'.trim().toUpperCase();
      switch (status) {
        case 'ANALISANDO':
          analyzing++;
          break;
        case 'PRONTA_REVISAO':
          ready++;
          break;
        case 'APLICADA':
          applied++;
          break;
        case 'ERRO':
          errors++;
          break;
        case 'DESCARTADA':
        case 'CANCELADA':
          break;
        default:
          pending++;
      }
    }

    return InspectionPhotoAiQueueState(
      pending: pending,
      analyzing: analyzing,
      ready: ready,
      applied: applied,
      errors: errors,
      eligible: eligible,
      running: isRunning(inspectionId),
    );
  }

  static Future<List<InspectionPhotoAiSuggestion>> readySuggestions(
    String inspectionId,
  ) async {
    final answers = await AppDatabase.instance.getAnswers(inspectionId);
    final rows = <InspectionPhotoAiSuggestion>[];
    for (final answer in answers) {
      final meta = _aiMeta(answer);
      rememberMeta(answer.inspectionId, answer.questionId, meta);
      if ('${meta['status'] ?? ''}'.toUpperCase() != 'PRONTA_REVISAO') {
        continue;
      }
      final result = meta['result'];
      if (result is! Map) continue;
      rows.add(
        InspectionPhotoAiSuggestion(
          answer: answer,
          result: Map<String, dynamic>.from(result),
        ),
      );
    }
    return rows;
  }

  static bool _isTransientFailure(String message) {
    final value = message.toLowerCase();
    return value.contains('google') ||
        value.contains('tempor') ||
        value.contains('página') ||
        value.contains('pagina') ||
        value.contains('html') ||
        value.contains('timeout') ||
        value.contains('demor') ||
        value.contains('oscil') ||
        value.contains('comunica') ||
        value.contains('conex') ||
        value.contains('internet') ||
        value.contains('429') ||
        value.contains('502') ||
        value.contains('503') ||
        value.contains('504');
  }

  static Future<AiAssistantReply> _analyzeWithRetry({
    required Inspection inspection,
    required String companyName,
    required ChecklistItem item,
    required List<String> photoPaths,
    required String technicianContext,
  }) async {
    AiAssistantReply? lastReply;
    for (var attempt = 1; attempt <= 3; attempt++) {
      final reply = await AiAssistantService.analyzeChecklistPhotos(
        inspection: inspection,
        companyName: companyName,
        item: item,
        photoPaths: photoPaths,
        technicianContext: technicianContext,
      );
      lastReply = reply;
      if (reply.success || !_isTransientFailure(reply.message)) {
        return reply;
      }
      if (attempt < 3) {
        await Future<void>.delayed(
          Duration(seconds: attempt == 1 ? 2 : 5),
        );
      }
    }
    return lastReply ??
        const AiAssistantReply(
          success: false,
          message: 'A IA não respondeu. A foto continua salva para tentar novamente.',
        );
  }

  static String _photoFingerprint(List<EvidencePhoto> photos) {
    final values = photos.map((photo) => photo.path.trim()).toList()..sort();
    return values.join('|');
  }

  static Future<InspectionAnswer?> _latestAnswer(
    InspectionAnswer fallback,
  ) async {
    final answers =
        await AppDatabase.instance.getAnswers(fallback.inspectionId);
    for (final answer in answers) {
      if (answer.id == fallback.id) return answer;
    }
    return null;
  }

  static Future<InspectionPhotoAiQueueSummary> processPending(
    String inspectionId,
  ) async {
    if (_running.contains(inspectionId)) {
      return const InspectionPhotoAiQueueSummary(
        completed: 0,
        failed: 0,
        skipped: 0,
      );
    }

    _running.add(inspectionId);
    var completed = 0;
    var failed = 0;
    var skipped = 0;
    final attempted = <String>{};

    try {
      final db = AppDatabase.instance;
      final header = await db.getInspectionHeader(inspectionId);
      if (header == null) {
        return const InspectionPhotoAiQueueSummary(
          completed: 0,
          failed: 1,
          skipped: 0,
        );
      }

      final inspection = _inspectionFromHeader(header);
      final companyName = '${header['company_name'] ?? ''}'.trim();

      // Recarrega a lista a cada ciclo. Assim, se o técnico tirar outra foto
      // enquanto a fila está trabalhando, o novo item entra no mesmo lote sem
      // abrir uma segunda requisição concorrente.
      while (true) {
        final answers = await db.getAnswers(inspectionId);
        InspectionAnswer? seed;
        for (final candidate in answers) {
          if (attempted.contains(candidate.id)) continue;
          final candidatePhotos =
              await db.getPhotosForAnswer(candidate.id);
          if (!_eligible(candidate, candidatePhotos)) continue;
          final status =
              '${_aiMeta(candidate)['status'] ?? ''}'.trim().toUpperCase();
          if (status == 'PRONTA_REVISAO' ||
              status == 'APLICADA' ||
              status == 'DESCARTADA' ||
              status == 'CANCELADA') {
            continue;
          }
          seed = candidate;
          break;
        }

        if (seed == null) break;
        attempted.add(seed.id);

        final answer = await _latestAnswer(seed) ?? seed;
        final photos = await db.getPhotosForAnswer(answer.id);
        if (!_eligible(answer, photos)) {
          skipped++;
          continue;
        }

        final currentMeta = _aiMeta(answer);
        final currentStatus =
            '${currentMeta['status'] ?? ''}'.trim().toUpperCase();
        if (currentStatus == 'PRONTA_REVISAO' ||
            currentStatus == 'APLICADA' ||
            currentStatus == 'DESCARTADA' ||
            currentStatus == 'CANCELADA') {
          skipped++;
          continue;
        }

        final photoFingerprint = _photoFingerprint(photos);
        final analyzingMeta = <String, dynamic>{
          ...currentMeta,
          'status': 'ANALISANDO',
          'startedAt': DateTime.now().toUtc().toIso8601String(),
          'lastError': '',
        };
        await _saveMeta(answer, analyzingMeta);

        final ncs = await db.getNonConformitiesForAnswer(answer.id);
        final priority =
            ncs.isNotEmpty ? ncs.first.classification : 'Média';
        final item = ChecklistItem(
          id: answer.questionId,
          templateId: inspection.checklistTemplateId,
          sortOrder: 0,
          category: answer.questionCategory,
          text: answer.questionText,
          reference: answer.questionReference,
          priority: priority,
        );

        final context = <String>[
          if (answer.observation.trim().isNotEmpty)
            'Observação do técnico: ${answer.observation.trim()}',
          if (answer.riskIdentified.trim().isNotEmpty)
            'Risco já registrado: ${answer.riskIdentified.trim()}',
          if (answer.recommendation.trim().isNotEmpty)
            'Recomendação já registrada: ${answer.recommendation.trim()}',
          'Esta análise está sendo feita em segundo plano. Não invente elementos que não estejam visíveis ou informados.',
        ].join('\n');

        final reply = await _analyzeWithRetry(
          inspection: inspection,
          companyName: companyName,
          item: item,
          photoPaths: photos.map((photo) => photo.path).toList(),
          technicianContext: context,
        );

        final latest = await _latestAnswer(answer) ?? answer;
        final latestPhotos = await db.getPhotosForAnswer(latest.id);

        // O técnico pode ter corrigido o item ou trocado a foto enquanto a IA
        // estava trabalhando. Nesse caso não aplicamos um resultado antigo.
        if (!_eligible(latest, latestPhotos)) {
          skipped++;
          await _saveMeta(
            latest,
            <String, dynamic>{
              ..._aiMeta(latest),
              'status': 'CANCELADA',
              'lastError': '',
              'cancelledAt': DateTime.now().toUtc().toIso8601String(),
            },
          );
          continue;
        }

        if (_photoFingerprint(latestPhotos) != photoFingerprint) {
          skipped++;
          await _saveMeta(
            latest,
            <String, dynamic>{
              ..._aiMeta(latest),
              'status': 'PENDENTE',
              'queuedAt': DateTime.now().toUtc().toIso8601String(),
              'lastError':
                  'A evidência mudou durante a análise. A nova foto ficará para o próximo processamento.',
            },
          );
          continue;
        }

        if (!reply.success) {
          failed++;
          await _saveMeta(
            latest,
            <String, dynamic>{
              ..._aiMeta(latest),
              'status': 'ERRO',
              'lastError': reply.message,
              'failedAt': DateTime.now().toUtc().toIso8601String(),
            },
          );
          continue;
        }

        completed++;
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
      }
    } finally {
      _running.remove(inspectionId);
    }

    return InspectionPhotoAiQueueSummary(
      completed: completed,
      failed: failed,
      skipped: skipped,
    );
  }

  static Future<void> applySuggestion(
    InspectionPhotoAiSuggestion suggestion,
  ) async {
    final db = AppDatabase.instance;
    final answer = await _latestAnswer(suggestion.answer) ??
        suggestion.answer;
    final result = suggestion.result;

    String text(String key) => '${result[key] ?? ''}'.trim();
    final description = text('description');
    final risk = text('risk');
    final recommendation = <String>[
      if (text('immediateAction').isNotEmpty)
        'Ação imediata: ${text('immediateAction')}',
      if (text('recommendation').isNotEmpty) text('recommendation'),
      if (text('correctiveAction').isNotEmpty)
        'Ação corretiva sugerida: ${text('correctiveAction')}',
      if (text('responsibleProfile').isNotEmpty)
        'Responsável sugerido: ${text('responsibleProfile')}',
      if (result['suggestedDeadlineDays'] != null)
        'Prazo inicial sugerido: ${result['suggestedDeadlineDays']} dia(s)',
    ].join('\n');
    final priority = text('priority');

    final meta = _aiMeta(answer);
    final nextMeta = <String, dynamic>{
      ...meta,
      'status': 'APLICADA',
      'appliedAt': DateTime.now().toUtc().toIso8601String(),
    };
    rememberMeta(answer.inspectionId, answer.questionId, nextMeta);

    final nextAnswer = InspectionAnswer(
      id: answer.id,
      inspectionId: answer.inspectionId,
      questionId: answer.questionId,
      questionText: answer.questionText,
      questionCategory: answer.questionCategory,
      questionReference: answer.questionReference,
      status: answer.status,
      observation:
          description.isNotEmpty ? description : answer.observation,
      riskIdentified: risk.isNotEmpty ? risk : answer.riskIdentified,
      recommendation:
          recommendation.isNotEmpty ? recommendation : answer.recommendation,
      occurrencesJson: _mergeMeta(answer.occurrencesJson, nextMeta),
    );
    await db.upsertAnswer(nextAnswer);

    final ncs = await db.getNonConformitiesForAnswer(answer.id);
    if (ncs.isNotEmpty) {
      final current = ncs.first;
      final acceptedPriority =
          const ['Baixa', 'Média', 'Alta', 'Crítica'].contains(priority)
              ? priority
              : current.classification;
      await db.upsertNonConformity(
        NonConformity(
          id: current.id,
          inspectionId: current.inspectionId,
          answerId: current.answerId,
          code: current.code,
          description:
              description.isNotEmpty ? description : current.description,
          riskIdentified:
              risk.isNotEmpty ? risk : current.riskIdentified,
          recommendation: recommendation.isNotEmpty
              ? recommendation
              : current.recommendation,
          classification: acceptedPriority,
          status: current.status,
          createdAt: current.createdAt,
          verifiedAt: current.verifiedAt,
          verifiedBy: current.verifiedBy,
        ),
      );
    }
  }

  static Future<void> dismissSuggestion(
    InspectionPhotoAiSuggestion suggestion,
  ) async {
    final answer =
        await _latestAnswer(suggestion.answer) ?? suggestion.answer;
    final meta = _aiMeta(answer);
    await _saveMeta(
      answer,
      <String, dynamic>{
        ...meta,
        'status': 'DESCARTADA',
        'dismissedAt': DateTime.now().toUtc().toIso8601String(),
      },
    );
  }

  static bool _eligible(
    InspectionAnswer answer,
    List<EvidencePhoto> photos,
  ) {
    if (photos.isEmpty) return false;
    return answer.status == 'Não Conforme' || answer.status == 'Parcial';
  }

  static Map<String, dynamic> _aiMeta(InspectionAnswer answer) {
    final raw = answer.occurrencesJson.trim();
    if (raw.isEmpty) return <String, dynamic>{};
    try {
      final decoded = jsonDecode(raw);
      if (decoded is! Map) return <String, dynamic>{};
      final meta = decoded['aiPhoto'];
      if (meta is! Map) return <String, dynamic>{};
      return Map<String, dynamic>.from(meta);
    } catch (_) {
      return <String, dynamic>{};
    }
  }

  static Future<void> _saveMeta(
    InspectionAnswer answer,
    Map<String, dynamic> meta,
  ) async {
    // Sempre parte da versão mais recente do registro. Assim a conclusão da IA
    // não sobrescreve observação, risco ou recomendação que o técnico tenha
    // editado enquanto continuava descendo o checklist.
    final latest = await _latestAnswer(answer) ?? answer;
    rememberMeta(latest.inspectionId, latest.questionId, meta);

    final updated = InspectionAnswer(
      id: latest.id,
      inspectionId: latest.inspectionId,
      questionId: latest.questionId,
      questionText: latest.questionText,
      questionCategory: latest.questionCategory,
      questionReference: latest.questionReference,
      status: latest.status,
      observation: latest.observation,
      riskIdentified: latest.riskIdentified,
      recommendation: latest.recommendation,
      occurrencesJson: _mergeMeta(latest.occurrencesJson, meta),
    );
    await AppDatabase.instance.upsertAnswer(updated);
  }

  static String _mergeMeta(
    String occurrencesJson,
    Map<String, dynamic> meta,
  ) {
    final root = <String, dynamic>{};
    if (occurrencesJson.trim().isNotEmpty) {
      try {
        final decoded = jsonDecode(occurrencesJson);
        if (decoded is Map) {
          root.addAll(Map<String, dynamic>.from(decoded));
        }
      } catch (_) {}
    }
    root['aiPhoto'] = meta;
    return jsonEncode(root);
  }

  static Inspection _inspectionFromHeader(Map<String, Object?> header) {
    DateTime date(String key) =>
        DateTime.tryParse('${header[key] ?? ''}') ?? DateTime.now();
    final includeActionPlanRaw = header['include_action_plan'];
    final includeActionPlan = includeActionPlanRaw is int
        ? includeActionPlanRaw == 1
        : '${includeActionPlanRaw ?? '1'}' != '0';

    return Inspection(
      id: '${header['id'] ?? ''}',
      companyId: '${header['company_id'] ?? ''}',
      workSiteId: _nullable('${header['worksite_id'] ?? ''}'),
      sectorId: _nullable('${header['sector_id'] ?? ''}'),
      area: '${header['area'] ?? ''}',
      checklistType: '${header['checklist_type'] ?? ''}',
      checklistTemplateId: '${header['checklist_template_id'] ?? ''}',
      date: date('date'),
      status: '${header['status'] ?? 'Em andamento'}',
      technicianName: '${header['technician_name'] ?? ''}',
      responsibleName: '${header['responsible_name'] ?? ''}',
      technicianSignaturePath:
          _nullable('${header['technician_signature_path'] ?? ''}'),
      responsibleSignaturePath:
          _nullable('${header['responsible_signature_path'] ?? ''}'),
      generalNotes: '${header['general_notes'] ?? ''}',
      conclusion: '${header['conclusion'] ?? ''}',
      reportNumber: '${header['report_number'] ?? ''}',
      reportSignatureMode:
          '${header['report_signature_mode'] ?? 'app'}',
      includeActionPlan: includeActionPlan,
    );
  }

  static String? _nullable(String value) {
    final clean = value.trim();
    return clean.isEmpty || clean == 'null' ? null : clean;
  }
}

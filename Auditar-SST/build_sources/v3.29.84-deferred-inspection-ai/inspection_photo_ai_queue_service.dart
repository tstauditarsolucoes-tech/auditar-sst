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

  static bool isRunning(String inspectionId) =>
      _running.contains(inspectionId);

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
      final answers = await db.getAnswers(inspectionId);

      for (final answer in answers) {
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
            currentStatus == 'DESCARTADA') {
          skipped++;
          continue;
        }

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
          'Esta análise está sendo feita após a coleta de campo. Não invente elementos que não estejam visíveis ou informados.',
        ].join('\n');

        final reply = await AiAssistantService.analyzeChecklistPhotos(
          inspection: inspection,
          companyName: companyName,
          item: item,
          photoPaths: photos.map((photo) => photo.path).toList(),
          technicianContext: context,
        );

        if (!reply.success) {
          failed++;
          await _saveMeta(
            answer,
            <String, dynamic>{
              ...currentMeta,
              'status': 'ERRO',
              'lastError': reply.message,
              'failedAt': DateTime.now().toUtc().toIso8601String(),
            },
          );
          continue;
        }

        completed++;
        await _saveMeta(
          answer,
          <String, dynamic>{
            ...currentMeta,
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
    final answer = suggestion.answer;
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
      occurrencesJson: _mergeMeta(
        answer.occurrencesJson,
        <String, dynamic>{
          ...meta,
          'status': 'APLICADA',
          'appliedAt': DateTime.now().toUtc().toIso8601String(),
        },
      ),
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
    final meta = _aiMeta(suggestion.answer);
    await _saveMeta(
      suggestion.answer,
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
    final updated = InspectionAnswer(
      id: answer.id,
      inspectionId: answer.inspectionId,
      questionId: answer.questionId,
      questionText: answer.questionText,
      questionCategory: answer.questionCategory,
      questionReference: answer.questionReference,
      status: answer.status,
      observation: answer.observation,
      riskIdentified: answer.riskIdentified,
      recommendation: answer.recommendation,
      occurrencesJson: _mergeMeta(answer.occurrencesJson, meta),
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

import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:uuid/uuid.dart';

import '../database.dart';
import '../models.dart';
import 'apps_script_http.dart';
import 'auth_service.dart';
import 'media_sync_service.dart';

class CipaManagementService {
  CipaManagementService._();

  static const mandateType = 'CIPA_MANDATO';
  static const memberType = 'CIPA_MEMBRO';
  static const meetingType = 'CIPA_REUNIAO';
  static const minutesType = 'CIPA_ATA';
  static const actionType = 'CIPA_ACAO';
  static const documentType = 'CIPA_DOCUMENTO';
  static const committeeType = 'CIPA_COMISSAO_ELEITORAL';

  static const _uuid = Uuid();

  static Future<List<SstRecord>> records(
    String type,
    String companyId,
  ) =>
      AppDatabase.instance.getSstRecords(
        type: type,
        companyId: companyId,
      );

  static Future<void> saveRecord({
    required String companyId,
    required String type,
    required String title,
    required DateTime date,
    String? id,
    DateTime? dueDate,
    String status = 'Pendente',
    String priority = 'Média',
    Map<String, dynamic> payload = const {},
  }) async {
    await AppDatabase.instance.upsertSstRecord(
      SstRecord(
        id: id ?? _uuid.v4(),
        companyId: companyId,
        type: type,
        title: title.trim(),
        date: date,
        dueDate: dueDate,
        status: status,
        priority: priority,
        payload: payload,
      ),
    );
  }

  static Future<void> deleteRecord(String id) =>
      AppDatabase.instance.deleteSstRecord(id);

  static Future<void> saveMandate({
    String? id,
    required String companyId,
    required String title,
    required DateTime start,
    required DateTime end,
    required String status,
    String notes = '',
    String electionId = '',
  }) =>
      saveRecord(
        id: id,
        companyId: companyId,
        type: mandateType,
        title: title,
        date: start,
        dueDate: end,
        status: status,
        priority: 'Média',
        payload: {
          'startDate': start.toIso8601String(),
          'endDate': end.toIso8601String(),
          'notes': notes.trim(),
          'electionId': electionId.trim(),
        },
      );

  static Future<void> saveMember({
    String? id,
    required String companyId,
    required String mandateId,
    required String workerId,
    required String name,
    required String cipaRole,
    required String representation,
    required DateTime entryDate,
    DateTime? exitDate,
    String status = 'Ativo',
    int absences = 0,
    String substituteMemberId = '',
    String notes = '',
  }) =>
      saveRecord(
        id: id,
        companyId: companyId,
        type: memberType,
        title: name,
        date: entryDate,
        dueDate: exitDate,
        status: status,
        priority: 'Média',
        payload: {
          'mandateId': mandateId,
          'workerId': workerId,
          'cipaRole': cipaRole,
          'representation': representation,
          'entryDate': entryDate.toIso8601String(),
          'exitDate': exitDate?.toIso8601String(),
          'absences': absences,
          'substituteMemberId': substituteMemberId,
          'notes': notes.trim(),
        },
      );

  static Future<void> saveMeeting({
    String? id,
    required String companyId,
    required String mandateId,
    required String title,
    required DateTime dateTime,
    required String meetingKind,
    required String place,
    required String agenda,
    required String subjects,
    required String decisions,
    required List<String> memberIds,
    required List<String> presentIds,
    String status = 'Agendada',
  }) async {
    final meetingId = id ?? _uuid.v4();
    await saveRecord(
      id: meetingId,
      companyId: companyId,
      type: meetingType,
      title: title,
      date: dateTime,
      dueDate: dateTime,
      status: status,
      priority: 'Média',
      payload: {
        'mandateId': mandateId,
        'meetingKind': meetingKind,
        'place': place.trim(),
        'agenda': agenda.trim(),
        'subjects': subjects.trim(),
        'decisions': decisions.trim(),
        'memberIds': memberIds,
        'presentIds': presentIds,
      },
    );
    await _rebuildMeetingReminders(
      companyId: companyId,
      meetingId: meetingId,
      title: title,
      dateTime: dateTime,
      completed: status == 'Realizada',
    );
  }

  static Future<void> _rebuildMeetingReminders({
    required String companyId,
    required String meetingId,
    required String title,
    required DateTime dateTime,
    required bool completed,
  }) async {
    final existing = await AppDatabase.instance.getSstRecords(
      type: 'AGENDA',
      companyId: companyId,
    );
    for (final row in existing) {
      if ('${row.payload['cipaMeetingId'] ?? ''}' == meetingId) {
        await AppDatabase.instance.deleteSstRecord(row.id);
      }
    }
    if (completed) return;

    final day = DateTime(dateTime.year, dateTime.month, dateTime.day);
    for (final daysBefore in const [7, 1, 0]) {
      final reminderDate = day.subtract(Duration(days: daysBefore));
      await saveRecord(
        id: 'cipa-reminder-$meetingId-$daysBefore',
        companyId: companyId,
        type: 'AGENDA',
        title: daysBefore == 0
            ? 'CIPA • reunião hoje • $title'
            : 'CIPA • reunião em $daysBefore dia(s) • $title',
        date: reminderDate,
        dueDate: dateTime,
        status: 'Pendente',
        priority: daysBefore <= 1 ? 'Alta' : 'Média',
        payload: {
          'cipaMeetingId': meetingId,
          'autoCipaReminder': true,
          'daysBefore': daysBefore,
        },
      );
    }
  }

  static Future<void> saveMinutes({
    String? id,
    required String companyId,
    required String mandateId,
    required String meetingId,
    required String title,
    required DateTime date,
    required String content,
    String status = 'Rascunho',
    int version = 1,
    bool signed = false,
    bool importedByAi = false,
  }) =>
      saveRecord(
        id: id,
        companyId: companyId,
        type: minutesType,
        title: title,
        date: date,
        status: signed ? 'Assinada' : status,
        priority: 'Média',
        payload: {
          'mandateId': mandateId,
          'meetingId': meetingId,
          'content': content.trim(),
          'version': version,
          'signed': signed,
          'importedByAi': importedByAi,
        },
      );

  static Future<void> saveAction({
    String? id,
    required String companyId,
    required String mandateId,
    required String meetingId,
    required String title,
    required String description,
    required String responsible,
    required DateTime createdAt,
    required DateTime? dueDate,
    required String priority,
    required String status,
    String ncId = '',
    String notes = '',
  }) =>
      saveRecord(
        id: id,
        companyId: companyId,
        type: actionType,
        title: title,
        date: createdAt,
        dueDate: dueDate,
        status: status,
        priority: priority,
        payload: {
          'mandateId': mandateId,
          'meetingId': meetingId,
          'description': description.trim(),
          'responsible': responsible.trim(),
          'ncId': ncId.trim(),
          'notes': notes.trim(),
        },
      );

  static Future<void> saveCommitteeMember({
    String? id,
    required String companyId,
    required String workerId,
    required String name,
    required String function,
    String electionId = '',
    String status = 'Ativo',
    String notes = '',
  }) =>
      saveRecord(
        id: id,
        companyId: companyId,
        type: committeeType,
        title: name,
        date: DateTime.now(),
        status: status,
        priority: 'Média',
        payload: {
          'workerId': workerId,
          'function': function,
          'electionId': electionId,
          'notes': notes.trim(),
        },
      );

  static Future<void> saveDocument({
    String? id,
    required String companyId,
    required String mandateId,
    required String title,
    required String category,
    required DateTime date,
    bool requiredDocument = false,
    String status = 'Arquivado',
    String notes = '',
  }) =>
      saveRecord(
        id: id,
        companyId: companyId,
        type: documentType,
        title: title,
        date: date,
        status: status,
        priority: requiredDocument ? 'Alta' : 'Média',
        payload: {
          'mandateId': mandateId,
          'category': category,
          'requiredDocument': requiredDocument,
          'notes': notes.trim(),
        },
      );

  static Future<void> refreshLinkedNcStatuses(String companyId) async {
    final actions = await records(actionType, companyId);
    for (final action in actions) {
      final ncId = '${action.payload['ncId'] ?? ''}'.trim();
      if (ncId.isEmpty) continue;
      final nc = await AppDatabase.instance.getNonConformity(ncId);
      if (nc == null) continue;
      String mapped;
      switch (nc.status) {
        case 'Concluída':
          mapped = 'Resolvida';
          break;
        case 'Vencida':
          mapped = 'Vencida';
          break;
        case 'Em andamento':
        case 'Aguardando verificação':
          mapped = 'Em andamento';
          break;
        default:
          mapped = 'Aberta';
      }
      if (mapped == action.status) continue;
      await saveAction(
        id: action.id,
        companyId: companyId,
        mandateId: '${action.payload['mandateId'] ?? ''}',
        meetingId: '${action.payload['meetingId'] ?? ''}',
        title: action.title,
        description: '${action.payload['description'] ?? ''}',
        responsible: '${action.payload['responsible'] ?? ''}',
        createdAt: action.date,
        dueDate: action.dueDate,
        priority: action.priority,
        status: mapped,
        ncId: ncId,
        notes: '${action.payload['notes'] ?? ''}',
      );
    }
  }

  static Future<String> createNcFromAction({
    required String companyId,
    required String companyName,
    required SstRecord action,
  }) async {
    final db = AppDatabase.instance;
    final inspectionId = 'cipa-inspection-${action.id}';
    final answerId = 'cipa-answer-${action.id}';
    final ncId = 'cipa-nc-${action.id}';
    final now = DateTime.now();

    await db.insertInspection(
      Inspection(
        id: inspectionId,
        companyId: companyId,
        area: 'CIPA',
        checklistType: 'CIPA',
        checklistTemplateId: '',
        date: now,
        status: 'Finalizada',
        technicianName: 'CIPA',
        responsibleName: '${action.payload['responsible'] ?? ''}',
        generalNotes:
            'Registro criado diretamente pelo módulo da CIPA de $companyName.',
        conclusion: 'Não conformidade vinculada ao plano de ação da CIPA.',
        reportNumber: 'CIPA-${action.id.substring(0, action.id.length < 8 ? action.id.length : 8).toUpperCase()}',
        includeActionPlan: false,
      ),
    );
    await db.insertAnswer(
      InspectionAnswer(
        id: answerId,
        inspectionId: inspectionId,
        questionId: 'cipa-action-${action.id}',
        questionText: action.title,
        questionCategory: 'CIPA',
        questionReference: 'NR-05',
        status: 'Não Conforme',
        observation: '${action.payload['description'] ?? ''}',
        riskIdentified: '${action.payload['description'] ?? ''}',
        recommendation: '${action.payload['notes'] ?? ''}',
      ),
    );
    await db.upsertNonConformity(
      NonConformity(
        id: ncId,
        inspectionId: inspectionId,
        answerId: answerId,
        code: 'CIPA',
        description: action.title,
        riskIdentified: '${action.payload['description'] ?? ''}',
        recommendation: '${action.payload['notes'] ?? ''}',
        classification: action.priority,
        status: 'Pendente',
        createdAt: now,
      ),
    );
    await saveAction(
      id: action.id,
      companyId: companyId,
      mandateId: '${action.payload['mandateId'] ?? ''}',
      meetingId: '${action.payload['meetingId'] ?? ''}',
      title: action.title,
      description: '${action.payload['description'] ?? ''}',
      responsible: '${action.payload['responsible'] ?? ''}',
      createdAt: action.date,
      dueDate: action.dueDate,
      priority: action.priority,
      status: 'Aberta',
      ncId: ncId,
      notes: '${action.payload['notes'] ?? ''}',
    );
    return ncId;
  }

  static Future<Map<String, Object?>> registerAttachment({
    required String companyId,
    required String entityType,
    required String entityId,
    required PlatformFile picked,
  }) async {
    final bytes = picked.bytes ??
        (picked.path == null ? null : await File(picked.path!).readAsBytes());
    if (bytes == null || bytes.isEmpty) {
      throw StateError('Não foi possível ler o arquivo selecionado.');
    }
    if (bytes.length > 12 * 1024 * 1024) {
      throw StateError('O arquivo deve ter no máximo 12 MB.');
    }

    final base = await getApplicationDocumentsDirectory();
    final dir = Directory(
      p.join(base.path, 'auditar_cipa', companyId, entityId),
    );
    await dir.create(recursive: true);
    final safeName = _safeFileName(
      picked.name.isEmpty ? 'arquivo_${DateTime.now().millisecondsSinceEpoch}' : picked.name,
    );
    final local = File(p.join(dir.path, safeName));
    await local.writeAsBytes(bytes, flush: true);

    final mediaId = 'cipa-media-${_uuid.v4()}';
    final db = await AppDatabase.instance.database;
    final row = <String, Object?>{
      'id': mediaId,
      'company_id': companyId,
      'entity_type': entityType,
      'entity_id': entityId,
      'local_path': local.path,
      'drive_file_id': '',
      'file_name': safeName,
      'mime_type': _mimeFor(safeName),
      'updated_at': DateTime.now().toUtc().toIso8601String(),
    };
    await db.insert('media_assets', row);
    unawaited(MediaSyncService.uploadPending(limit: 6));
    return row;
  }

  static Future<List<Map<String, Object?>>> attachments({
    required String entityType,
    required String entityId,
  }) async {
    final db = await AppDatabase.instance.database;
    return db.query(
      'media_assets',
      where: 'entity_type = ? AND entity_id = ?',
      whereArgs: [entityType, entityId],
      orderBy: 'updated_at DESC',
    );
  }

  static Future<void> removeAttachment(String mediaId) async {
    final db = await AppDatabase.instance.database;
    final rows = await db.query(
      'media_assets',
      where: 'id = ?',
      whereArgs: [mediaId],
      limit: 1,
    );
    if (rows.isNotEmpty) {
      final path = '${rows.first['local_path'] ?? ''}'.trim();
      if (path.isNotEmpty) {
        try {
          final file = File(path);
          if (await file.exists()) await file.delete();
        } catch (_) {}
      }
    }
    await db.delete('media_assets', where: 'id = ?', whereArgs: [mediaId]);
  }

  static Future<Map<String, dynamic>> readMinutesWithAi({
    required Uint8List bytes,
    required String fileName,
    required String companyName,
  }) async {
    final endpoint = (await AppDatabase.instance.getSetting(
      'management_panel_endpoint',
      fallback: '',
    ))
        .trim();
    final syncKey = (await AppDatabase.instance.getSetting(
      'management_panel_sync_key',
      fallback: '',
    ))
        .trim();
    if (endpoint.isEmpty || syncKey.isEmpty) {
      throw StateError('A Central Online precisa estar configurada para usar a IA.');
    }

    final mime = _mimeFor(fileName);
    final response = await AppsScriptHttp.postJson(
      Uri.parse(endpoint),
      {
        'action': 'ai_assistant',
        'syncKey': syncKey,
        'authToken': AuthService.sessionToken,
        'payload': {
          'mode': 'cipa_minutes_import',
          'companyName': companyName,
          'document': 'data:$mime;base64,${base64Encode(bytes)}',
        },
      },
      timeout: const Duration(seconds: 70),
      allowLongAndroidRequest: true,
    );

    final decoded = jsonDecode(
      utf8.decode(response.bodyBytes, allowMalformed: true),
    );
    if (decoded is! Map || decoded['ok'] != true) {
      final message = decoded is Map
          ? '${decoded['message'] ?? 'A IA não conseguiu ler a ata.'}'
          : 'A Central retornou uma resposta inválida.';
      throw StateError(message);
    }
    final result = decoded['result'];
    if (result is! Map) {
      throw StateError('A IA não retornou os dados estruturados da ata.');
    }
    return Map<String, dynamic>.from(result);
  }

  static bool isCipaTraining(TrainingControl training) {
    final value =
        '${training.code} ${training.title}'.toUpperCase().replaceAll('-', ' ');
    return value.contains('CIPA') ||
        value.contains('NR 5') ||
        value.contains('NR 05');
  }

  static bool isOverdue(SstRecord record, {DateTime? now}) {
    if (record.status == 'Resolvida' ||
        record.status == 'Concluída' ||
        record.status == 'Arquivado') {
      return false;
    }
    final due = record.dueDate;
    if (due == null) return false;
    final current = now ?? DateTime.now();
    final today = DateTime(current.year, current.month, current.day);
    return DateTime(due.year, due.month, due.day).isBefore(today);
  }

  static String _safeFileName(String value) {
    final cleaned = value.replaceAll(RegExp(r'[^A-Za-z0-9._ -]'), '_').trim();
    return cleaned.isEmpty ? 'arquivo' : cleaned;
  }

  static String _mimeFor(String path) {
    switch (p.extension(path).toLowerCase()) {
      case '.pdf':
        return 'application/pdf';
      case '.doc':
        return 'application/msword';
      case '.docx':
        return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
      case '.png':
        return 'image/png';
      case '.jpg':
      case '.jpeg':
        return 'image/jpeg';
      case '.xlsx':
        return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
      default:
        return 'application/octet-stream';
    }
  }
}

import 'package:uuid/uuid.dart';

import '../database.dart';
import '../models.dart';

class PreAdmissionParticipantService {
  static const recordType = 'PRE_ADMISSION_PARTICIPANT';

  static Future<List<SstRecord>> getAll(
    String companyId, {
    bool includeConverted = true,
  }) async {
    final rows = await AppDatabase.instance.getSstRecords(
      type: recordType,
      companyId: companyId,
    );
    if (includeConverted) return rows;
    return rows
        .where((row) => row.status.toUpperCase() == 'ATIVO')
        .toList();
  }

  static Future<SstRecord?> findById(
    String companyId,
    String id,
  ) async {
    if (id.trim().isEmpty) return null;
    final rows = await getAll(companyId);
    for (final row in rows) {
      if (row.id == id) return row;
    }
    return null;
  }

  static Future<SstRecord> create({
    required String companyId,
    required String name,
    String cpf = '',
    String role = '',
    String? sectorId,
    String sectorName = '',
    String category = 'PRE_ADMISSION',
  }) async {
    final cleanName = name.trim();
    if (cleanName.isEmpty) {
      throw ArgumentError('Informe o nome do participante.');
    }
    final now = DateTime.now();
    final record = SstRecord(
      id: const Uuid().v4(),
      companyId: companyId,
      sectorId: sectorId,
      type: recordType,
      title: cleanName,
      date: now,
      status: 'ATIVO',
      priority: 'Baixa',
      payload: <String, dynamic>{
        'name': cleanName,
        'cpf': cpf.trim(),
        'role': role.trim(),
        'sectorId': sectorId ?? '',
        'sector': sectorName.trim(),
        'category': category,
        'employmentStatus': 'VINCULO_NAO_FORMALIZADO',
        'createdAt': now.toUtc().toIso8601String(),
        'workerId': '',
        'convertedAt': '',
        'archivedAt': '',
      },
    );
    await AppDatabase.instance.upsertSstRecord(record);
    return record;
  }

  static Future<void> archive(SstRecord participant) async {
    final payload = Map<String, dynamic>.from(participant.payload)
      ..['archivedAt'] = DateTime.now().toUtc().toIso8601String();
    await AppDatabase.instance.upsertSstRecord(
      SstRecord(
        id: participant.id,
        companyId: participant.companyId,
        sectorId: participant.sectorId,
        type: participant.type,
        title: participant.title,
        date: participant.date,
        dueDate: participant.dueDate,
        status: 'ARQUIVADO',
        priority: participant.priority,
        payload: payload,
      ),
    );
  }

  static Future<Worker> convertToWorker({
    required SstRecord participant,
    required String name,
    String cpf = '',
    String role = '',
    String? sectorId,
    DateTime? admissionDate,
  }) async {
    final companyId = participant.companyId ?? '';
    if (companyId.isEmpty) {
      throw StateError('Empresa do participante não encontrada.');
    }
    final cleanName = name.trim();
    if (cleanName.isEmpty) {
      throw ArgumentError('Informe o nome do colaborador.');
    }

    final workers = await AppDatabase.instance.getWorkers(
      companyId: companyId,
      onlyActive: false,
    );
    final cleanCpf = _digits(cpf);
    Worker? existing;
    if (cleanCpf.isNotEmpty) {
      for (final worker in workers) {
        if (_digits(worker.cpf) == cleanCpf) {
          existing = worker;
          break;
        }
      }
    }
    existing ??= _matchByName(workers, cleanName, role);

    final converted = Worker(
      id: existing?.id ?? const Uuid().v4(),
      companyId: companyId,
      sectorId: sectorId ?? existing?.sectorId,
      name: cleanName,
      cpf: cpf.trim().isNotEmpty ? cpf.trim() : (existing?.cpf ?? ''),
      role: role.trim().isNotEmpty ? role.trim() : (existing?.role ?? ''),
      admissionDate:
          admissionDate ?? existing?.admissionDate ?? DateTime.now(),
      lastMedicalExamDate: existing?.lastMedicalExamDate,
      nextMedicalExamDate: existing?.nextMedicalExamDate,
      asoPath: existing?.asoPath ?? '',
      active: true,
    );

    if (existing == null) {
      await AppDatabase.instance.insertWorker(converted);
    } else {
      await AppDatabase.instance.updateWorker(converted);
    }

    final convertedAt = DateTime.now().toUtc().toIso8601String();
    await _linkHistoricalRecords(
      companyId: companyId,
      preAdmissionId: participant.id,
      worker: converted,
      convertedAt: convertedAt,
    );

    final payload = Map<String, dynamic>.from(participant.payload)
      ..['name'] = converted.name
      ..['cpf'] = converted.cpf
      ..['role'] = converted.role
      ..['sectorId'] = converted.sectorId ?? ''
      ..['workerId'] = converted.id
      ..['employmentStatus'] = 'CONVERTIDO_EM_COLABORADOR'
      ..['convertedAt'] = convertedAt;

    await AppDatabase.instance.upsertSstRecord(
      SstRecord(
        id: participant.id,
        companyId: participant.companyId,
        sectorId: converted.sectorId,
        type: participant.type,
        title: converted.name,
        date: participant.date,
        dueDate: participant.dueDate,
        status: 'CONVERTIDO',
        priority: participant.priority,
        payload: payload,
      ),
    );
    return converted;
  }

  static Worker? _matchByName(
    List<Worker> workers,
    String name,
    String role,
  ) {
    final targetName = _normalize(name);
    final targetRole = _normalize(role);
    final sameName = workers
        .where((worker) => _normalize(worker.name) == targetName)
        .toList();
    if (sameName.length == 1) return sameName.first;
    if (sameName.length > 1 && targetRole.isNotEmpty) {
      for (final worker in sameName) {
        if (_normalize(worker.role) == targetRole) return worker;
      }
    }
    return null;
  }

  static Future<void> _linkHistoricalRecords({
    required String companyId,
    required String preAdmissionId,
    required Worker worker,
    required String convertedAt,
  }) async {
    final trainingControls = <TrainingControl>[];

    final trainings = await AppDatabase.instance.getSstRecords(
      type: 'TREINAMENTO_SESSAO',
      companyId: companyId,
    );
    for (final record in trainings) {
      final rawParticipants = record.payload['participants'];
      if (rawParticipants is! List) continue;
      var changed = false;
      final participants = rawParticipants.map((raw) {
        if (raw is! Map) return raw;
        final item = Map<String, dynamic>.from(raw);
        if ('${item['preAdmissionId'] ?? ''}' != preAdmissionId) {
          return item;
        }
        changed = true;
        item['workerId'] = worker.id;
        item['convertedWorkerId'] = worker.id;
        item['convertedAt'] = convertedAt;
        item['originParticipantType'] = 'PRE_ADMISSION';
        item['participantType'] = 'WORKER';
        item['cpf'] = worker.cpf;
        item['role'] = worker.role;
        return item;
      }).toList();
      if (!changed) continue;

      final payload = Map<String, dynamic>.from(record.payload)
        ..['participants'] = participants;
      await AppDatabase.instance.upsertSstRecord(
        SstRecord(
          id: record.id,
          companyId: record.companyId,
          sectorId: record.sectorId,
          type: record.type,
          title: record.title,
          date: record.date,
          dueDate: record.dueDate,
          status: record.status,
          priority: record.priority,
          payload: payload,
        ),
      );

      if (record.status.toUpperCase() == 'FINALIZADO') {
        final participant = participants.whereType<Map>().cast<Map>().firstWhere(
              (item) =>
                  '${item['preAdmissionId'] ?? ''}' == preAdmissionId,
              orElse: () => const <String, dynamic>{},
            );
        if ('${participant['status'] ?? ''}' == 'ASSINADO') {
          final validity =
              int.tryParse('${record.payload['validityMonths'] ?? 0}') ?? 0;
          trainingControls.add(
            TrainingControl(
              id: '${record.id}_${worker.id}',
              workerId: worker.id,
              code: '${record.payload['code'] ?? ''}'.trim().toUpperCase(),
              title: record.title,
              trainingDate: record.date,
              expiryDate:
                  validity > 0 ? _addMonths(record.date, validity) : null,
              notes:
                  'Histórico transferido da pré-admissão • sessão ${record.id}',
            ),
          );
        }
      }
    }

    final ddsRows = await AppDatabase.instance.getSstRecords(
      type: 'DDS',
      companyId: companyId,
    );
    for (final record in ddsRows) {
      final payload = Map<String, dynamic>.from(record.payload);
      var changed = false;

      final rawParticipants = payload['dds_participants'];
      if (rawParticipants is List) {
        payload['dds_participants'] = rawParticipants.map((raw) {
          if (raw is! Map) return raw;
          final item = Map<String, dynamic>.from(raw);
          if ('${item['preAdmissionId'] ?? ''}' != preAdmissionId) {
            return item;
          }
          changed = true;
          return <String, dynamic>{
            ...item,
            'workerId': worker.id,
            'convertedWorkerId': worker.id,
            'convertedAt': convertedAt,
            'originParticipantType': 'PRE_ADMISSION',
            'participantType': 'WORKER',
            'cpf': worker.cpf,
            'role': worker.role,
          };
        }).toList();
      }

      final rawSignatures = payload['dds_signatures'];
      if (rawSignatures is List) {
        payload['dds_signatures'] = rawSignatures.map((raw) {
          if (raw is! Map) return raw;
          final item = Map<String, dynamic>.from(raw);
          if ('${item['preAdmissionId'] ?? ''}' != preAdmissionId) {
            return item;
          }
          changed = true;
          return <String, dynamic>{
            ...item,
            'workerId': worker.id,
            'convertedWorkerId': worker.id,
            'convertedAt': convertedAt,
            'originParticipantType': 'PRE_ADMISSION',
            'participantType': 'WORKER',
            'cpf': worker.cpf,
            'role': worker.role,
          };
        }).toList();
      }

      if (!changed) continue;
      await AppDatabase.instance.upsertSstRecord(
        SstRecord(
          id: record.id,
          companyId: record.companyId,
          sectorId: record.sectorId,
          type: record.type,
          title: record.title,
          date: record.date,
          dueDate: record.dueDate,
          status: record.status,
          priority: record.priority,
          payload: payload,
        ),
      );
    }

    if (trainingControls.isNotEmpty) {
      await AppDatabase.instance.upsertTrainingControlsBatch(trainingControls);
    }
  }

  static DateTime _addMonths(DateTime source, int months) {
    final targetMonth = source.month - 1 + months;
    final year = source.year + targetMonth ~/ 12;
    final month = targetMonth % 12 + 1;
    final firstNext =
        month == 12 ? DateTime(year + 1, 1, 1) : DateTime(year, month + 1, 1);
    final lastDay = firstNext.subtract(const Duration(days: 1)).day;
    final day = source.day > lastDay ? lastDay : source.day;
    return DateTime(year, month, day);
  }

  static String _digits(String value) =>
      value.replaceAll(RegExp(r'\D'), '');

  static String _normalize(String value) => value
      .trim()
      .toLowerCase()
      .replaceAll(RegExp(r'\s+'), ' ');
}

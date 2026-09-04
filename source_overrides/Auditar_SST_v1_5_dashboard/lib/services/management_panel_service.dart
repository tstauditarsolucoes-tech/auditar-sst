import 'dart:convert';

import '../database.dart';
import '../models.dart';
import 'apps_script_http.dart';

class ManagementPanelSyncResult {
  final bool success;
  final String message;

  const ManagementPanelSyncResult({
    required this.success,
    required this.message,
  });
}

class ManagementPanelService {
  static Future<String> panelUrlForCompany(String companyId) async {
    final db = AppDatabase.instance;
    final endpoint = (await db.getSetting(
      'management_panel_endpoint',
      fallback: '',
    ))
        .trim();
    if (endpoint.isEmpty) return '';

    final panel = await db.ensureManagementPanel(companyId);
    final token = '${panel['access_token'] ?? ''}'.trim();
    if (token.isEmpty) return '';

    final separator = endpoint.contains('?') ? '&' : '?';
    return '$endpoint${separator}empresa=${Uri.encodeQueryComponent(token)}';
  }

  static Future<Map<String, Object?>> buildSnapshot(
    Company company, {
    bool? enabledOverride,
  }) async {
    final db = AppDatabase.instance;
    final panel = await db.ensureManagementPanel(company.id);
    final summary = await db.getDashboardSummary(companyId: company.id);
    final sectorPerformance =
        await db.getCompanySectorPerformance(company.id);
    final trainingSummary =
        await db.getTrainingSummary(companyId: company.id);
    final workers = await db.getWorkers(companyId: company.id);
    final companySectors = await db.getSectors(company.id);
    final trainings = await db.getTrainingControls(companyId: company.id);
    final missingTrainings =
        await db.getMissingRequiredTrainings(companyId: company.id);
    final ncs = await db.getNonConformityRows(
      companyId: company.id,
      includeClosed: false,
    );
    final allNcs = await db.getNonConformityRows(
      companyId: company.id,
      includeClosed: true,
    );
    final actions = await db.getPendingActions(
      companyId: company.id,
      includeCompleted: false,
    );
    final allActions = await db.getPendingActions(
      companyId: company.id,
      includeCompleted: true,
    );
    final inspections =
        await db.getInspectionHistory(companyId: company.id);
    final extinguishers = await db.getSstRecords(
      type: 'EXTINTOR',
      companyId: company.id,
    );
    final safetyObservations = await db.getSstRecords(
      type: 'OBSERVACAO_SEGURANCA',
      companyId: company.id,
    );
    final improvements = await db.getSstRecords(
      type: 'MELHORIA',
      companyId: company.id,
    );
    final agendaRecords = await db.getSstRecords(
      type: 'AGENDA',
      companyId: company.id,
    );
    final snapshotNow = DateTime.now();
    final currentMonthStart =
        DateTime(snapshotNow.year, snapshotNow.month, 1);
    final previousMonthStart =
        DateTime(currentMonthStart.year, currentMonthStart.month - 1, 1);
    final previousMonthEnd =
        currentMonthStart.subtract(const Duration(days: 1));
    final currentMonthSummary = await db.getDashboardSummary(
      companyId: company.id,
      startDate: currentMonthStart,
      endDate: snapshotNow,
    );
    final monthlySummary = await db.getDashboardSummary(
      companyId: company.id,
      startDate: previousMonthStart,
      endDate: previousMonthEnd,
    );
    final monthlyInspections = inspections.where((row) {
      final date = DateTime.tryParse('${row['date'] ?? ''}');
      return date != null &&
          !date.isBefore(previousMonthStart) &&
          date.isBefore(currentMonthStart);
    }).toList();

    final enabled = enabledOverride ?? ((panel['enabled'] as int? ?? 1) == 1);
    final now = DateTime.now();

    Worker? workerFor(String id) {
      for (final worker in workers) {
        if (worker.id == id) return worker;
      }
      return null;
    }

    int daysUntil(DateTime date) {
      final today = DateTime(now.year, now.month, now.day);
      return DateTime(date.year, date.month, date.day).difference(today).inDays;
    }

    Map<String, Object?> cleanSector(Map<String, Object?> row) => {
          'name': '${row['name'] ?? ''}',
          'inspections': _asInt(row['inspections']),
          'conformes': _asInt(row['conformes']),
          'parciais': _asInt(row['parciais']),
          'naoConformes': _asInt(row['nao_conformes']),
          'naoAplicaveis': _asInt(row['nao_aplicaveis']),
          'openNcs': _asInt(row['open_ncs']),
          'overdueNcs': _asInt(row['overdue_ncs']),
          'latestInspection': '${row['latest_inspection'] ?? ''}',
        };

    Map<String, Object?> cleanNc(Map<String, Object?> row) => {
          'code': '${row['code'] ?? ''}',
          'status': '${row['status'] ?? ''}',
          'classification': '${row['classification'] ?? ''}',
          'description': '${row['description'] ?? ''}',
          'risk': '${row['risk_identified'] ?? ''}',
          'recommendation': '${row['recommendation'] ?? ''}',
          'sector': '${row['sector_name'] ?? ''}',
          'area': '${row['area'] ?? ''}',
          'createdAt': '${row['created_at'] ?? ''}',
          'verifiedAt': '${row['verified_at'] ?? ''}',
          'verifiedBy': '${row['verified_by'] ?? ''}',
          'nextDueDate': '${row['next_due_date'] ?? ''}',
          'openActionCount': _asInt(row['open_action_count']),
        };

    Map<String, Object?> cleanAction(Map<String, Object?> row) => {
          'ncCode': '${row['nc_code'] ?? ''}',
          'status': '${row['status'] ?? ''}',
          'priority': '${row['priority'] ?? ''}',
          'problem': '${row['non_conformity'] ?? ''}',
          'correctiveAction': '${row['corrective_action'] ?? ''}',
          'responsible': '${row['responsible'] ?? ''}',
          'sector': '${row['sector_name'] ?? ''}',
          'area': '${row['area'] ?? ''}',
          'dueDate': '${row['due_date'] ?? ''}',
          'completionDate': '${row['completion_date'] ?? ''}',
          'completedBy': '${row['completed_by'] ?? ''}',
        };

    Map<String, Object?> cleanInspection(Map<String, Object?> row) => {
          'reportNumber': '${row['report_number'] ?? ''}',
          'date': '${row['date'] ?? ''}',
          'status': '${row['status'] ?? ''}',
          'sector': '${row['sector_name'] ?? ''}',
          'area': '${row['area'] ?? ''}',
          'checklistType': '${row['checklist_type'] ?? ''}',
        };

    Map<String, Object?> cleanTraining(TrainingControl training) {
      final worker = workerFor(training.workerId);
      final expiry = training.expiryDate;
      return {
        'id': training.id,
        'worker': worker?.name ?? '',
        'role': worker?.role ?? '',
        'code': training.code,
        'title': training.title,
        'expiryDate': expiry?.toIso8601String() ?? '',
        'daysUntilExpiry': expiry == null ? null : daysUntil(expiry),
        'status': training.statusAt(now),
      };
    }

    Map<String, Object?> cleanMedical(Worker worker) {
      final nextExam = worker.nextMedicalExamDate;
      return {
        'workerId': worker.id,
        'worker': worker.name,
        'role': worker.role,
        'nextExamDate': nextExam?.toIso8601String() ?? '',
        'daysUntilExpiry': nextExam == null ? null : daysUntil(nextExam),
      };
    }

    String sectorNameFor(String? sectorId) {
      if (sectorId == null) return '';
      for (final sector in companySectors) {
        if (sector.id == sectorId) return sector.name;
      }
      return '';
    }

    DateTime? payloadDate(SstRecord record, String key) {
      final raw = '${record.payload[key] ?? ''}'.trim();
      return raw.isEmpty ? null : DateTime.tryParse(raw);
    }

    String extinguisherStatus(SstRecord record) {
      final payload = record.payload;
      if (payload['locationEmpty'] == true) return 'LOCAL SEM EXTINTOR';
      final operational = '${payload['operationalStatus'] ?? ''}'.toUpperCase();
      if (operational == 'INATIVO') return 'INATIVO';
      if (operational == 'EM MANUTENÇÃO' || operational == 'EM MANUTENCAO') {
        return 'EM MANUTENÇÃO';
      }
      final checks = [
        payload['sealOk'],
        payload['gaugeOk'],
        payload['signageOk'],
        payload['accessOk'],
        payload['hoseNozzleOk'],
      ];
      if (checks.any((value) => value == false)) return 'IRREGULAR';
      final expiry = payloadDate(record, 'expiryDate') ?? record.dueDate;
      final hydro = payloadDate(record, 'hydrostaticExpiryDate');
      final today = DateTime(now.year, now.month, now.day);
      DateTime day(DateTime date) => DateTime(date.year, date.month, date.day);
      if ((expiry != null && day(expiry).isBefore(today)) ||
          (hydro != null && day(hydro).isBefore(today))) {
        return 'VENCIDO';
      }
      final upcoming = [expiry, hydro]
          .whereType<DateTime>()
          .map(daysUntil)
          .where((days) => days >= 0 && days <= 30)
          .isNotEmpty;
      return upcoming ? 'VENCE EM 30 DIAS' : 'EM DIA';
    }

    Map<String, Object?> cleanExtinguisher(SstRecord record) {
      final payload = record.payload;
      final expiry = payloadDate(record, 'expiryDate') ?? record.dueDate;
      return {
        'id': record.id,
        'code': '${payload['code'] ?? record.title}',
        'type': '${payload['extinguisherType'] ?? payload['type'] ?? ''}',
        'capacity': '${payload['capacity'] ?? ''}',
        'sector': '${payload['sectorName'] ?? sectorNameFor(record.sectorId)}',
        'location': '${payload['location'] ?? ''}',
        'status': extinguisherStatus(record),
        'expiryDate': expiry?.toIso8601String() ?? '',
        'hydrostaticExpiryDate':
            payloadDate(record, 'hydrostaticExpiryDate')?.toIso8601String() ?? '',
        'responsibility': '${payload['responsibility'] ?? ''}',
        'responsibleName': '${payload['responsibleName'] ?? ''}',
        'locationEmpty': payload['locationEmpty'] == true,
      };
    }

    final extinguisherRows = extinguishers.map(cleanExtinguisher).toList();
    final extinguisherSummary = <String, Object?>{
      'total': extinguishers.length,
      'current': extinguishers
          .where((record) => extinguisherStatus(record) == 'EM DIA')
          .length,
      'dueSoon': extinguishers
          .where((record) => extinguisherStatus(record) == 'VENCE EM 30 DIAS')
          .length,
      'expired': extinguishers
          .where((record) => extinguisherStatus(record) == 'VENCIDO')
          .length,
      'irregular': extinguishers
          .where((record) => extinguisherStatus(record) == 'IRREGULAR')
          .length,
      'maintenance': extinguishers
          .where((record) => extinguisherStatus(record) == 'EM MANUTENÇÃO')
          .length,
      'missingLocations': extinguishers
          .where((record) => extinguisherStatus(record) == 'LOCAL SEM EXTINTOR')
          .length,
    };

    bool safetyClosed(SstRecord record) {
      final value = record.status.toLowerCase();
      return value.contains('resolvid') || value.contains('conclu');
    }

    String safetyKind(SstRecord record) {
      final value = '${record.payload['kind'] ?? record.payload['subtype'] ?? ''}'
          .trim();
      return value.isEmpty ? 'Condição insegura' : value;
    }

    bool safetyOverdue(SstRecord record) {
      final due = record.dueDate;
      if (due == null || safetyClosed(record)) return false;
      final today = DateTime(now.year, now.month, now.day);
      final day = DateTime(due.year, due.month, due.day);
      return day.isBefore(today);
    }

    Map<String, Object?> cleanSafetyObservation(SstRecord record) {
      final payload = record.payload;
      return {
        'id': record.id,
        'title': record.title,
        'kind': safetyKind(record),
        'date': record.date.toIso8601String(),
        'dueDate': record.dueDate?.toIso8601String() ?? '',
        'status': record.status,
        'priority': record.priority,
        'overdue': safetyOverdue(record),
        'sector': '${payload['sectorName'] ?? sectorNameFor(record.sectorId)}',
        'location': '${payload['location'] ?? ''}',
        'risk': '${payload['risk'] ?? payload['risks'] ?? ''}',
        'action': '${payload['action'] ?? payload['measures'] ?? ''}',
        'responsible': '${payload['responsible'] ?? ''}',
        'resolvedAt': '${payload['resolvedAt'] ?? ''}',
      };
    }

    final safetyRows = safetyObservations.map(cleanSafetyObservation).toList();
    final safetySummary = <String, Object?>{
      'total': safetyRows.length,
      'open': safetyObservations.where((record) => !safetyClosed(record)).length,
      'resolved': safetyObservations.where(safetyClosed).length,
      'conditions': safetyObservations
          .where((record) => safetyKind(record) == 'Condição insegura')
          .length,
      'acts': safetyObservations
          .where((record) => safetyKind(record) == 'Ato inseguro')
          .length,
      'criticalOpen': safetyObservations
          .where((record) => !safetyClosed(record) && record.priority == 'Crítica')
          .length,
      'overdue': safetyObservations.where(safetyOverdue).length,
      'criticalOrOverdue': safetyObservations
          .where((record) =>
              !safetyClosed(record) &&
              (record.priority == 'Crítica' || safetyOverdue(record)))
          .length,
    };

    bool improvementRealized(SstRecord record) =>
        record.status.toLowerCase().contains('realiz') ||
        record.status.toLowerCase().contains('conclu');

    bool improvementOverdue(SstRecord record) {
      final due = record.dueDate;
      if (due == null || improvementRealized(record)) return false;
      final today = DateTime(now.year, now.month, now.day);
      final day = DateTime(due.year, due.month, due.day);
      return day.isBefore(today);
    }

    DateTime? improvementCompletedDate(SstRecord record) {
      final raw = '${record.payload['completedDate'] ?? ''}'.trim();
      return raw.isEmpty ? null : DateTime.tryParse(raw);
    }

    Map<String, Object?> cleanImprovement(SstRecord record) {
      final payload = record.payload;
      final beforePath = '${payload['beforePhotoPath'] ?? ''}'.trim();
      final afterPath = '${payload['afterPhotoPath'] ?? ''}'.trim();
      return {
        'id': record.id,
        'title': record.title,
        'date': record.date.toIso8601String(),
        'dueDate': record.dueDate?.toIso8601String() ?? '',
        'completedDate': '${payload['completedDate'] ?? ''}',
        'status': record.status,
        'priority': record.priority,
        'overdue': improvementOverdue(record),
        'sector': '${payload['sectorName'] ?? sectorNameFor(record.sectorId)}',
        'location': '${payload['location'] ?? ''}',
        'beforeSituation': '${payload['beforeSituation'] ?? ''}',
        'suggestion': '${payload['suggestion'] ?? ''}',
        'expectedBenefit': '${payload['expectedBenefit'] ?? ''}',
        'workPerformed': '${payload['workPerformed'] ?? ''}',
        'result': '${payload['result'] ?? ''}',
        'responsible': '${payload['responsible'] ?? ''}',
        'hasBeforePhoto': beforePath.isNotEmpty,
        'hasAfterPhoto': afterPath.isNotEmpty,
        'hasBeforeAfter': beforePath.isNotEmpty && afterPath.isNotEmpty,
      };
    }

    final improvementRows = improvements.map(cleanImprovement).toList();

    Map<String, Object?> cleanAgenda(SstRecord record) {
      final payload = record.payload;
      return {
        'id': record.id,
        'title': record.title,
        'date': record.date.toIso8601String(),
        'dueDate': record.dueDate?.toIso8601String() ?? '',
        'status': record.status,
        'priority': record.priority,
        'sector': sectorNameFor(record.sectorId),
        'location': '${payload['location'] ?? ''}',
        'responsible': '${payload['responsible'] ?? ''}',
        'description': '${payload['description'] ?? ''}',
        'notes': '${payload['notes'] ?? ''}',
        'subtype': '${payload['subtype'] ?? ''}',
      };
    }

    final agendaRows = agendaRecords.map(cleanAgenda).toList()
      ..sort((a, b) {
        final aDate = DateTime.tryParse('${a['date'] ?? ''}');
        final bDate = DateTime.tryParse('${b['date'] ?? ''}');
        if (aDate == null && bDate == null) return 0;
        if (aDate == null) return 1;
        if (bDate == null) return -1;
        return aDate.compareTo(bDate);
      });

    final todayAgenda = DateTime(now.year, now.month, now.day);
    final weekAgendaEnd = todayAgenda.add(const Duration(days: 7));
    bool agendaCompleted(SstRecord record) {
      final value = record.status.toLowerCase();
      return value.contains('conclu') || value.contains('realiz');
    }
    bool agendaOverdue(SstRecord record) {
      if (agendaCompleted(record)) return false;
      final day = DateTime(record.date.year, record.date.month, record.date.day);
      return day.isBefore(todayAgenda);
    }
    bool agendaThisWeek(SstRecord record) {
      final day = DateTime(record.date.year, record.date.month, record.date.day);
      return !day.isBefore(todayAgenda) && day.isBefore(weekAgendaEnd);
    }
    final agendaSummary = <String, Object?>{
      'total': agendaRecords.length,
      'today': agendaRecords.where((record) {
        final day = DateTime(record.date.year, record.date.month, record.date.day);
        return day == todayAgenda && !agendaCompleted(record);
      }).length,
      'next7Days': agendaRecords.where(agendaThisWeek).length,
      'overdue': agendaRecords.where(agendaOverdue).length,
      'completed': agendaRecords.where(agendaCompleted).length,
    };

    final improvementSummary = <String, Object?>{
      'total': improvements.length,
      'suggested': improvements.where((record) => record.status == 'Sugerida').length,
      'planned': improvements.where((record) => record.status == 'Planejada').length,
      'inProgress': improvements.where((record) => record.status == 'Em execução').length,
      'realized': improvements.where(improvementRealized).length,
      'overdue': improvements.where(improvementOverdue).length,
      'withBeforeAfter': improvements.where((record) {
        final beforePath = '${record.payload['beforePhotoPath'] ?? ''}'.trim();
        final afterPath = '${record.payload['afterPhotoPath'] ?? ''}'.trim();
        return beforePath.isNotEmpty && afterPath.isNotEmpty;
      }).length,
    };

    DateTime? rowDate(Map<String, Object?> row, String key) {
      final raw = '${row[key] ?? ''}'.trim();
      return raw.isEmpty ? null : DateTime.tryParse(raw);
    }

    DateTime endOfDay(DateTime date) =>
        DateTime(date.year, date.month, date.day, 23, 59, 59, 999);

    int openNcsAt(DateTime asOf) {
      final limit = endOfDay(asOf);
      return allNcs.where((row) {
        final created = rowDate(row, 'created_at');
        if (created == null || created.isAfter(limit)) return false;
        final verified = rowDate(row, 'verified_at');
        final concluded = '${row['status'] ?? ''}'
            .toLowerCase()
            .contains('conclu');
        if (verified != null) return verified.isAfter(limit);
        if (concluded) return false;
        return true;
      }).length;
    }

    int overdueActionsAt(DateTime asOf) {
      final limit = endOfDay(asOf);
      return allActions.where((row) {
        final due = rowDate(row, 'due_date');
        if (due == null || !due.isBefore(limit)) return false;
        final completed = rowDate(row, 'completion_date');
        return completed == null || completed.isAfter(limit);
      }).length;
    }

    int expiredTrainingsAt(DateTime asOf) {
      final day = DateTime(asOf.year, asOf.month, asOf.day);
      return trainings.where((training) {
        final expiry = training.expiryDate;
        if (expiry == null) return false;
        return DateTime(expiry.year, expiry.month, expiry.day).isBefore(day);
      }).length;
    }

    int sstScoreFor({
      required int conformity,
      required int openNcs,
      required int overdueActions,
      required int expiredTrainings,
    }) {
      var score = conformity;
      score -= openNcs * 2;
      score -= overdueActions * 4;
      score -= expiredTrainings * 2;
      return score.clamp(0, 100);
    }

    final currentOpenNcs = openNcsAt(snapshotNow);
    final previousOpenNcs = openNcsAt(previousMonthEnd);
    final currentOverdueActions = overdueActionsAt(snapshotNow);
    final previousOverdueActions = overdueActionsAt(previousMonthEnd);
    final currentExpiredTrainings = expiredTrainingsAt(snapshotNow);
    final previousExpiredTrainings = expiredTrainingsAt(previousMonthEnd);
    final currentSstScore = sstScoreFor(
      conformity: _asInt(currentMonthSummary['conformity']),
      openNcs: currentOpenNcs,
      overdueActions: currentOverdueActions,
      expiredTrainings: currentExpiredTrainings,
    );
    final previousSstScore = sstScoreFor(
      conformity: _asInt(monthlySummary['conformity']),
      openNcs: previousOpenNcs,
      overdueActions: previousOverdueActions,
      expiredTrainings: previousExpiredTrainings,
    );

    final monthNames = <String>[
      'jan', 'fev', 'mar', 'abr', 'mai', 'jun',
      'jul', 'ago', 'set', 'out', 'nov', 'dez',
    ];
    final monthlyTrend = <Map<String, Object?>>[];
    for (var i = 5; i >= 0; i--) {
      final start = DateTime(snapshotNow.year, snapshotNow.month - i, 1);
      final end = DateTime(start.year, start.month + 1, 1)
          .subtract(const Duration(milliseconds: 1));
      final month = await db.getDashboardSummary(
        companyId: company.id,
        startDate: start,
        endDate: end,
      );
      monthlyTrend.add({
        'label': '${monthNames[start.month - 1]}/${start.year.toString().substring(2)}',
        'inspections': _asInt(month['inspections']),
        'conformity': _asInt(month['inspections']) > 0
            ? _asInt(month['conformity'])
            : null,
      });
    }

    final recentActivities = <Map<String, Object?>>[];
    for (final row in inspections.take(8)) {
      final date = DateTime.tryParse('${row['date'] ?? ''}');
      if (date == null) continue;
      recentActivities.add({
        'date': date.toIso8601String(),
        'type': 'Vistoria',
        'title': '${row['report_number'] ?? 'Vistoria'}',
        'detail': [
          '${row['sector_name'] ?? ''}',
          '${row['area'] ?? ''}',
        ].where((value) => value.trim().isNotEmpty).join(' • '),
      });
    }
    for (final record in improvements) {
      final realized = improvementRealized(record);
      recentActivities.add({
        'date': (realized ? (improvementCompletedDate(record) ?? record.date) : record.date)
            .toIso8601String(),
        'type': realized ? 'Melhoria realizada' : 'Melhoria',
        'title': record.title,
        'detail': [sectorNameFor(record.sectorId), '${record.payload['location'] ?? ''}']
            .where((value) => value.trim().isNotEmpty)
            .join(' • '),
      });
    }
    for (final record in safetyObservations) {
      recentActivities.add({
        'date': record.date.toIso8601String(),
        'type': safetyKind(record),
        'title': record.title,
        'detail': [sectorNameFor(record.sectorId), '${record.payload['location'] ?? ''}']
            .where((value) => value.trim().isNotEmpty)
            .join(' • '),
      });
    }
    recentActivities.sort((a, b) {
      final aDate = DateTime.tryParse('${a['date'] ?? ''}');
      final bDate = DateTime.tryParse('${b['date'] ?? ''}');
      if (aDate == null && bDate == null) return 0;
      if (aDate == null) return 1;
      if (bDate == null) return -1;
      return bDate.compareTo(aDate);
    });

    final trainingRecords = trainings.map(cleanTraining).toList();
    final medicalAlerts = workers.map(cleanMedical).toList();
    final workforceDetails = workers.map((worker) {
      final workerTrainings = trainings
          .where((training) => training.workerId == worker.id)
          .toList();
      final missingCount = missingTrainings
          .where((item) => '${item['workerId'] ?? ''}' == worker.id)
          .length;
      final currentCount = workerTrainings
          .where((training) => training.statusAt(now) == 'EM DIA')
          .length;
      final expiredCount = workerTrainings
          .where((training) => training.statusAt(now) == 'VENCIDO')
          .length;
      final pendingCount = workerTrainings
          .where((training) => training.statusAt(now) == 'PENDENTE')
          .length;
      final dueSoonCount = workerTrainings.where((training) {
        final expiry = training.expiryDate;
        if (expiry == null) return false;
        final days = daysUntil(expiry);
        return days >= 0 && days <= 30;
      }).length;
      final trainingStatus = expiredCount > 0
          ? 'VENCIDO'
          : (missingCount + pendingCount) > 0
              ? 'PENDENTE'
              : dueSoonCount > 0
                  ? 'PRÓXIMO'
                  : 'EM DIA';
      final nextExam = worker.nextMedicalExamDate;
      final medicalDays = nextExam == null ? null : daysUntil(nextExam);
      final medicalStatus = medicalDays == null
          ? 'SEM DATA'
          : medicalDays < 0
              ? 'VENCIDO'
              : medicalDays <= 30
                  ? 'PRÓXIMO'
                  : 'EM DIA';
      return {
        'worker': worker.name,
        'role': worker.role,
        'sector': sectorNameFor(worker.sectorId),
        'trainingStatus': trainingStatus,
        'trainingDetails': '$currentCount em dia • $expiredCount vencido(s) • '
            '${missingCount + pendingCount} pendente(s)',
        'currentTrainings': currentCount,
        'expiredTrainings': expiredCount,
        'pendingTrainings': missingCount + pendingCount,
        'dueSoonTrainings': dueSoonCount,
        'nextExamDate': nextExam?.toIso8601String() ?? '',
        'medicalStatus': medicalStatus,
      };
    }).toList();

    return {
      'schemaVersion': 10,
      'accessToken': '${panel['access_token'] ?? ''}',
      'enabled': enabled,
      'updatedAt': DateTime.now().toIso8601String(),
      'company': {
        'id': company.id,
        'name': company.name,
        'city': company.city ?? '',
        'uf': company.uf ?? '',
        'contact': company.reportRecipient.isNotEmpty
            ? company.reportRecipient
            : (company.contact ?? ''),
      },
      'notifications': {
        'primaryEmail': company.reportEmail,
        'secondaryEmail': company.secondaryReportEmail,
        'monthlyReportEnabled': company.monthlyReportEnabled,
        'monthlyReportDay': company.monthlyReportDay,
        'trainingAlertsEnabled': company.trainingAlertsEnabled,
        'medicalAlertsEnabled': company.medicalAlertsEnabled,
      },
      'summary': summary,
      'periodComparison': {
        'currentStart': currentMonthStart.toIso8601String(),
        'currentEnd': snapshotNow.toIso8601String(),
        'currentSummary': currentMonthSummary,
        'previousStart': previousMonthStart.toIso8601String(),
        'previousEnd': previousMonthEnd.toIso8601String(),
        'previousSummary': monthlySummary,
        'currentMetrics': {
          'openNc': currentOpenNcs,
          'overdueActions': currentOverdueActions,
          'expiredTrainings': currentExpiredTrainings,
          'sstScore': currentSstScore,
        },
        'previousMetrics': {
          'openNc': previousOpenNcs,
          'overdueActions': previousOverdueActions,
          'expiredTrainings': previousExpiredTrainings,
          'sstScore': previousSstScore,
        },
      },
      'sstScore': {
        'value': currentSstScore,
        'previousValue': previousSstScore,
        'isCurrentMonth': (currentMonthSummary['inspections'] ?? 0) > 0,
        'method': 'Indicador gerencial interno Auditar: conformidade, NCs abertas, ações vencidas e treinamentos vencidos.',
      },
      'monthlyTrend': monthlyTrend,
      'recentActivities': recentActivities.take(12).toList(),
      'monthlyReport': {
        'periodStart': previousMonthStart.toIso8601String(),
        'periodEnd': previousMonthEnd.toIso8601String(),
        'summary': monthlySummary,
        'inspections': monthlyInspections.map(cleanInspection).toList(),
      },
      'trainingSummary': trainingSummary,
      'extinguisherSummary': extinguisherSummary,
      'extinguishers': extinguisherRows,
      'companySectors': companySectors
          .map((sector) => {'id': sector.id, 'name': sector.name})
          .toList(),
      'safetyObservationSummary': safetySummary,
      'safetyObservations': safetyRows,
      'improvementSummary': improvementSummary,
      'improvements': improvementRows,
      'agendaSummary': agendaSummary,
      'agenda': agendaRows,
      'workforceSummary': {
        'activeWorkers': workers.length,
        'missingRequiredTrainings': missingTrainings.length,
        'medicalRegular': workers.where((worker) {
          final nextExam = worker.nextMedicalExamDate;
          return nextExam != null && daysUntil(nextExam) > 30;
        }).length,
        'medicalDueSoon': workers.where((worker) {
          final nextExam = worker.nextMedicalExamDate;
          if (nextExam == null) return false;
          final days = daysUntil(nextExam);
          return days >= 0 && days <= 30;
        }).length,
        'medicalExpired': workers.where((worker) {
          final nextExam = worker.nextMedicalExamDate;
          return nextExam != null && daysUntil(nextExam) < 0;
        }).length,
        'medicalWithoutDate': workers
            .where((worker) => worker.nextMedicalExamDate == null)
            .length,
      },
      'workforceDetails': workforceDetails,
      'trainingRecords': trainingRecords,
      'missingRequiredTrainings': missingTrainings,
      'medicalAlerts': medicalAlerts,
      'sectors': sectorPerformance.map(cleanSector).toList(),
      'openNonConformities': ncs.map(cleanNc).toList(),
      'pendingActions': actions.map(cleanAction).toList(),
      'recentInspections': inspections.take(20).map(cleanInspection).toList(),
    };
  }

  static Future<ManagementPanelSyncResult> syncCompany(
    Company company, {
    bool? enabledOverride,
  }) async {
    final db = AppDatabase.instance;
    final endpoint = (await db.getSetting(
      'management_panel_endpoint',
      fallback: '',
    ))
        .trim();
    final syncKey = (await db.getSetting(
      'management_panel_sync_key',
      fallback: '',
    ))
        .trim();
    if (endpoint.isEmpty || syncKey.isEmpty) {
      return const ManagementPanelSyncResult(
        success: false,
        message: 'Configure a Central Online nas configurações do aplicativo.',
      );
    }

    try {
      final response = await AppsScriptHttp.postJson(
        Uri.parse(endpoint),
        {
          'action': 'sync',
          'syncKey': syncKey,
          'payload': await buildSnapshot(
            company,
            enabledOverride: enabledOverride,
          ),
        },
      );
      if (response.statusCode < 200 || response.statusCode >= 300) {
        return ManagementPanelSyncResult(
          success: false,
          message: 'A Central Online respondeu com erro ${response.statusCode}.',
        );
      }
      final decoded = jsonDecode(response.body);
      if (decoded is! Map) {
        return const ManagementPanelSyncResult(
          success: false,
          message: 'A Central Online retornou uma resposta inválida.',
        );
      }
      final result = Map<String, dynamic>.from(decoded);
      return ManagementPanelSyncResult(
        success: result['ok'] == true,
        message: '${result['message'] ?? 'Painel atualizado.'}',
      );
    } catch (error) {
      return ManagementPanelSyncResult(
        success: false,
        message: 'Não foi possível atualizar o painel: $error',
      );
    }
  }

  static int _asInt(Object? value) {
    if (value is int) return value;
    if (value is num) return value.toInt();
    return int.tryParse('$value') ?? 0;
  }
}

/// CIPA presentation rules. No database, transport, authentication or UI imports.
class CipaParticipationEvent {
  final String id;
  final String companyId;
  final DateTime date;
  final Map<String, dynamic> data;
  const CipaParticipationEvent(this.id, this.companyId, this.date, this.data);
  String get kind => '${data['kind'] ?? ''}';
  String get targetId => '${data['targetId'] ?? ''}';
}

class CipaParticipationRules {
  static const marker = 'auditar.cipa.participation.v1';
  final String companyId;
  late final List<CipaParticipationEvent> events;

  CipaParticipationRules(this.companyId, Iterable<CipaParticipationEvent> source) {
    events = source.where((e) => e.companyId == companyId &&
        e.data['workspaceEvent'] == marker).toList()
      ..sort((a, b) {
        final byDate = a.date.compareTo(b.date);
        return byDate == 0 ? a.id.compareTo(b.id) : byDate;
      });
  }

  CipaParticipationEvent? latest(String targetId, Set<String> kinds) {
    for (final event in events.reversed) {
      if (event.targetId == targetId && kinds.contains(event.kind)) return event;
    }
    return null;
  }

  bool archived(String id) => latest(id, {'archive', 'restore'})?.kind == 'archive';

  bool hiddenByArchive(String id, String type, String status, bool signed) =>
      archived(id) && canArchive(type, status, signed);

  CipaParticipationEvent? support(String id) {
    final event = latest(id, {'support_requested', 'support_completed'});
    return event?.kind == 'support_requested' ? event : null;
  }

  bool carriedTo(String actionId, String mandateId) => events.any((e) =>
      e.kind == 'handover' && e.targetId == mandateId &&
      (e.data['actionIds'] is List) &&
      (e.data['actionIds'] as List).contains(actionId));

  DateTime? knownCompletion(String actionId, String currentStatus, {bool linkedNc = false}) {
    // Legacy NC refresh can close/reopen actions without a dated CIPA event.
    // Do not invent an historical completion date from an old local event.
    if (currentStatus != 'Resolvida' || linkedNc) return null;
    final event = latest(actionId, {'action_status'});
    return event?.data['status'] == 'Resolvida' ? event?.date : null;
  }

  static bool inMonth(DateTime date, DateTime month) =>
      date.year == month.year && date.month == month.month;

  static int nextVersion(Iterable<Object?> versions) {
    var highest = 0;
    for (final value in versions) {
      final parsed = int.tryParse('$value') ?? 0;
      if (parsed > highest) highest = parsed;
    }
    return highest + 1;
  }

  static String meetingMonthLabel(Iterable<String> statuses, bool past) {
    final values = statuses.toSet();
    if (values.contains('Realizada')) return 'realizada';
    if (values.contains('Agendada')) return past ? 'conferir realização' : 'agendada';
    return past ? 'conferir' : 'planejar';
  }

  static bool canArchive(String type, String status, bool signed) {
    switch (type) {
      case 'CIPA_MANDATO': return status == 'Encerrado';
      case 'CIPA_MEMBRO': return status != 'Ativo';
      case 'CIPA_REUNIAO': return status == 'Cancelada';
      case 'CIPA_ACAO': return status == 'Resolvida';
      case 'CIPA_ATA': return status == 'Rascunho' && !signed;
      case 'CIPA_DOCUMENTO': return status == 'Arquivado' || status == 'Concluído';
      default: return false;
    }
  }

  /// Never append a line twice or replace the user's agenda.
  static String appendAgenda(String original, Iterable<String> lines) {
    final known = original.split('\n').map((e) => e.trim()).toSet();
    final fresh = lines.where((e) => e.trim().isNotEmpty && known.add(e.trim()));
    return [if (original.trim().isNotEmpty) original.trimRight(), ...fresh].join('\n');
  }
}

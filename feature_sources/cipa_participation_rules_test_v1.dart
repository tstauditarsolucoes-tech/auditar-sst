import 'cipa_participation_rules_v1.dart';

void main() {
  var count = 0;
  void check(bool condition, String name) {
    if (!condition) throw StateError(name);
    count++;
  }
  CipaParticipationEvent event(String id, String company, String kind, String target,
      int day, [Map<String, dynamic> extra = const {}]) => CipaParticipationEvent(
    id, company, DateTime(2026, 10, day), {
      'workspaceEvent': CipaParticipationRules.marker, 'kind': kind, 'targetId': target, ...extra,
    });
  final rules = CipaParticipationRules('A', [
    event('restore', 'A', 'restore', 'action', 5),
    event('request', 'A', 'support_requested', 'action', 2, {'categoryName': 'Compra'}),
    event('other-company', 'B', 'archive', 'action', 20),
    event('archive', 'A', 'archive', 'action', 1),
    event('help-done', 'A', 'support_completed', 'action', 3),
    event('handover', 'A', 'handover', 'new-mandate', 8, {'actionIds': ['action']}),
    event('resolved', 'A', 'action_status', 'action', 10, {'status': 'Resolvida'}),
    CipaParticipationEvent('not-event', 'A', DateTime(2026, 10, 30), {'kind': 'archive', 'targetId': 'action'}),
  ]);
  check(!rules.archived('action'), 'restoration wins chronologically, not input ordering');
  check(!rules.archived('unknown'), 'unknown record remains visible');
  check(rules.events.length == 6, 'isolate company and namespace');
  check(rules.support('action') == null, 'support resolved independently');
  check(rules.carriedTo('action', 'new-mandate'), 'handover exposes existing action id');
  check(!rules.carriedTo('other-action', 'new-mandate'), 'handover does not include unselected action');
  check(!rules.carriedTo('action', 'other-mandate'), 'mandate isolation');
  check(rules.knownCompletion('action', 'Resolvida') == DateTime(2026, 10, 10), 'dated conclusion');
  check(rules.knownCompletion('action', 'Aberta') == null, 'reopened action not a result');
  check(rules.knownCompletion('old', 'Resolvida') == null, 'no invented legacy completion');
  check(rules.knownCompletion('action', 'Resolvida', linkedNc: true) == null, 'no stale NC completion date');
  final requestAgain = CipaParticipationRules('A', [...rules.events,
    event('request-2', 'A', 'support_requested', 'action', 12, {'categoryName': 'Orientação'})]);
  check(requestAgain.support('action')?.data['categoryName'] == 'Orientação', 'new support request');
  final progress = CipaParticipationRules('A', [
    event('older-note', 'A', 'progress_reported', 'action', 10,
      {'detail': 'Iniciado'}),
    event('other-company-note', 'B', 'progress_reported', 'action', 30,
      {'detail': 'Não deve aparecer'}),
    event('newer-note', 'A', 'progress_reported', 'action', 12,
      {'detail': 'Em avaliação técnica'}),
  ]);
  check(progress.progress('action')?.data['detail'] == 'Em avaliação técnica',
    'only latest scoped progress note is shown');
  check(progress.progress('unknown') == null,
    'no unverified progress for unrelated actions');
  check(CipaParticipationRules.nextVersion([2, 7, 1, '4', null]) == 8, 'maximum version, not first');
  check(CipaParticipationRules.nextVersion([]) == 1, 'first revision');
  check(CipaParticipationRules.nextVersion(['bad', -5]) == 1, 'invalid legacy revisions');
  check(CipaParticipationRules.meetingMonthLabel(['Agendada'], false) == 'agendada', 'scheduled not realized');
  check(CipaParticipationRules.meetingMonthLabel(['Cancelada'], true) == 'conferir', 'cancelled not realized');
  check(CipaParticipationRules.meetingMonthLabel(['Realizada', 'Agendada'], true) == 'realizada', 'actual meeting');
  check(CipaParticipationRules.meetingMonthLabel(['Agendada'], true) == 'conferir realização', 'overdue schedule');
  check(!CipaParticipationRules.canArchive('CIPA_ACAO', 'Aberta', false), 'cannot hide open action');
  check(CipaParticipationRules.canArchive('CIPA_ACAO', 'Resolvida', false), 'resolved archive');
  check(!CipaParticipationRules.canArchive('CIPA_MANDATO', 'Ativo', false), 'cannot hide active mandate');
  check(!CipaParticipationRules.canArchive('CIPA_ATA', 'Finalizada', false), 'final minutes retained');
  check(!CipaParticipationRules.canArchive('CIPA_ATA', 'Rascunho', true), 'signed minutes retained');
  check(CipaParticipationRules.canArchive('CIPA_ATA', 'Rascunho', false), 'draft may be archived');
  check(!CipaParticipationRules.canArchive('CIPA_REUNIAO', 'Realizada', false), 'performed meetings retained');
  check(!CipaParticipationRules.canArchive('UNKNOWN', '', false), 'unknown types fail closed');
  check(CipaParticipationRules.appendAgenda('Minha pauta\n• Ação A', ['• Ação A', '• Ação B', '• Ação B']) ==
    'Minha pauta\n• Ação A\n• Ação B', 'agenda preserves text and removes duplicate additions');
  check(CipaParticipationRules.inMonth(DateTime(2026, 10, 31, 23, 59), DateTime(2026, 10)), 'inclusive final day');
  check(!CipaParticipationRules.inMonth(DateTime(2026, 11), DateTime(2026, 10)), 'next month excluded');
  check(!CipaParticipationRules.inMonth(DateTime(2025, 10), DateTime(2026, 10)), 'year boundary');
  final malformed = CipaParticipationRules('A', [event('bad-list', 'A', 'handover', 'm', 1, {'actionIds': 'a'})]);
  check(!malformed.carriedTo('a', 'm'), 'malformed legacy list fails safely');
  final archived = CipaParticipationRules('A', [event('archive', 'A', 'archive', 'action', 1)]);
  check(archived.hiddenByArchive('action', 'CIPA_ACAO', 'Resolvida', false), 'resolved action can be hidden');
  check(!archived.hiddenByArchive('action', 'CIPA_ACAO', 'Aberta', false), 'reopened action reappears despite earlier archive');
  check(!CipaParticipationRules.canArchive('CIPA_DOCUMENTO', 'Pendente de anexo', false), 'pending document remains visible');
  final noCompany = CipaParticipationRules('A', [
    CipaParticipationEvent('unscoped', null, DateTime(2026, 10, 31), {
      'workspaceEvent': CipaParticipationRules.marker,
      'kind': 'archive', 'targetId': 'action',
    }),
  ]);
  check(noCompany.events.isEmpty, 'nullable legacy company must not be assumed');
  check(!noCompany.archived('action'), 'unscoped record cannot hide company action');
  final guide = CipaParticipationRules('A', [
    event('done', 'A', 'monthly_check', 'mandate|2026-10|verificar_ambiente', 2, {
      'done': true, 'monthKey': '2026-10',
      'taskKey': 'verificar_ambiente', 'mandateId': 'mandate',
    }),
    event('other-month', 'A', 'monthly_check', 'mandate|2026-09|verificar_ambiente', 3, {
      'done': false, 'monthKey': '2026-09',
      'taskKey': 'verificar_ambiente', 'mandateId': 'mandate',
    }),
    event('other-company-check', 'B', 'monthly_check', 'mandate|2026-10|verificar_ambiente', 30, {
      'done': false, 'monthKey': '2026-10',
      'taskKey': 'verificar_ambiente', 'mandateId': 'mandate',
    }),
    event('observation-1', 'A', 'observation', 'obs-1', 4, {
      'mandateId': 'mandate', 'location': 'Expedição', 'detail': 'Corredor obstruído',
    }),
    event('observation-2', 'B', 'observation', 'obs-2', 5, {
      'mandateId': 'mandate', 'location': 'Outra empresa',
    }),
    event('observation-3', 'A', 'observation', 'obs-3', 6, {
      'mandateId': 'other-mandate',
    }),
    event('not-a-guide', 'A', 'monthly_check', 'mandate|2026-10|invented', 7, {
      'done': true, 'monthKey': '2026-10', 'taskKey': 'invented', 'mandateId': 'mandate',
    }),
  ]);
  check(CipaParticipationRules.monthKey(DateTime(2026, 1, 31)) == '2026-01',
    'month key normalized');
  check(guide.monthlyDone('mandate', DateTime(2026, 10), 'verificar_ambiente'),
    'monthly check persists for mandate');
  check(!guide.monthlyDone('mandate', DateTime(2026, 9), 'verificar_ambiente'),
    'different month not marked');
  check(!guide.monthlyDone('other-mandate', DateTime(2026, 10), 'verificar_ambiente'),
    'other mandate not marked');
  check(!guide.monthlyDone('mandate', DateTime(2026, 10), 'invented'),
    'unknown checklist item refused');
  check(guide.observations('mandate').length == 1,
    'observations restricted to company and mandate');
  check(guide.observations('other-mandate').length == 1,
    'separate mandate has separate observation list');
  check(guide.observations('').isEmpty, 'no unscoped observations');
  final uncheck = CipaParticipationRules('A', [
    ...guide.events,
    event('uncheck', 'A', 'monthly_check', 'mandate|2026-10|verificar_ambiente', 10, {
      'done': false, 'monthKey': '2026-10',
      'taskKey': 'verificar_ambiente', 'mandateId': 'mandate',
    }),
  ]);
  check(!uncheck.monthlyDone('mandate', DateTime(2026, 10), 'verificar_ambiente'),
    'reversing check records the new state without deleting history');
  print('CIPA_PARTICIPATION_RULES_OK $count checks');
}

import 'cipa_participation_rules_v1.dart';
import 'cipa_followup_queue_v1.dart';

CipaParticipationEvent event(
  String id, String? company, String kind, String targetId,
  DateTime date, Map<String, dynamic> details,
) => CipaParticipationEvent(id, company, date, {
  'workspaceEvent': CipaParticipationRules.marker,
  'kind': kind,
  'targetId': targetId,
  ...details,
});

void check(bool test, String message) {
  if (!test) throw StateError(message);
}

void main() {
  final d = DateTime(2026, 11, 5, 8);
  final events = [
    event('obs-A', 'empresa-A', 'observation', 'obs-A', d,
        {'mandateId': 'mandato-A', 'detail': 'Corredor obstruído'}),
    event('obs-B', 'empresa-B', 'observation', 'obs-B', d,
        {'mandateId': 'mandato-B', 'detail': 'Outro local'}),
    event('obs-semempresa', null, 'observation', 'obs-semempresa', d,
        {'mandateId': 'mandato-A'}),
    event('obs-antigo', 'empresa-A', 'observation', 'obs-antigo', d,
        {'mandateId': 'mandato-anterior'}),
    event('report-1', 'empresa-A', 'progress_reported', 'action-A',
        d.add(const Duration(minutes: 10)),
        {'detail': 'Foi instalada a proteção'}),
  ];
  CipaFollowupQueue queue(Iterable<CipaParticipationEvent> records) =>
      CipaFollowupQueue(CipaParticipationRules('empresa-A', records));

  var q = queue(events);
  check(q.pendingObservations('mandato-A').length == 1,
      'Uma observação do mandato e da empresa.');
  check(q.pendingObservations('mandato-B').isEmpty,
      'Não exibir informação de outro mandato.');
  check(q.pendingObservations('').isEmpty,
      'Não inferir mandato ausente.');
  check(q.pendingProgressActionIds(['action-A']).contains('action-A'),
      'Informe de andamento aguarda conferência.');
  check(!q.pendingProgressActionIds(['action-outra']).contains('action-A'),
      'Não incluir ação que não pertence ao escopo visível.');

  // Mesmo companyId e target: a revisão com fonte correta retira da fila.
  final reviewed = [
    ...events,
    event('review-A', 'empresa-A', 'observation_review', 'obs-A',
      d.add(const Duration(minutes: 15)),
      {'observationId': 'obs-A', 'mandateId': 'mandato-A',
       'detail': 'Encaminhado para avaliação técnica'}),
    event('review-progress-1', 'empresa-A', 'progress_review', 'action-A',
      d.add(const Duration(minutes: 20)),
      {'reportEventId': 'report-1', 'detail': 'Relato conferido'}),
  ];
  q = queue(reviewed);
  check(q.pendingObservations('mandato-A').isEmpty,
      'Acompanhamento registrado apenas para a observação correta.');
  check(q.pendingProgressActionIds(['action-A']).isEmpty,
      'O relato analisado não permanece na fila.');

  // Uma informação mais recente precisa de nova análise: não usar
  // confirmação antiga para esconder a nova comunicação da CIPA.
  q = queue([
    ...reviewed,
    event('report-2', 'empresa-A', 'progress_reported', 'action-A',
      d.add(const Duration(minutes: 30)),
      {'detail': 'Surgiu um novo problema'}),
  ]);
  check(q.pendingProgressActionIds(['action-A']).contains('action-A'),
      'Novo informe volta a pedir conferência.');
  check(q.pendingProgressReport('action-A')?.id == 'report-2',
      'O relatório mais recente tem prioridade.');

  // Confirmação por outra empresa não deve quitar um caso da empresa A.
  q = queue([
    ...events,
    event('review-externa', 'empresa-B', 'observation_review', 'obs-A',
      d.add(const Duration(minutes: 30)),
      {'observationId': 'obs-A', 'mandateId': 'mandato-A'}),
  ]);
  check(q.pendingObservations('mandato-A').length == 1,
      'Nunca cruzar empresas.');

  // Qualquer registro inválido, sem id correto, deve permanecer pendente.
  q = queue([
    ...events,
    event('review-errada', 'empresa-A', 'observation_review', 'obs-A',
      d.add(const Duration(minutes: 30)),
      {'observationId': 'outro-registro', 'mandateId': 'mandato-A'}),
  ]);
  check(q.pendingObservations('mandato-A').length == 1,
      'Referência divergente não pode quitar a fila.');
  print('CIPA_FOLLOWUP_QUEUE_OK');
}

import 'cipa_participation_rules.dart';

/// Fila de conferência administrativa da CIPA, calculada apenas em memória.
/// Nunca altera uma NC, ação, ata, presença, eleição ou a situação do mandato.
class CipaFollowupQueue {
  const CipaFollowupQueue(this.rules);

  final CipaParticipationRules rules;

  /// Só considera registros da empresa e do mandato presentes nas regras.
  /// Um evento de revisão é apenas uma confirmação de leitura/análise; NÃO
  /// transforma a observação em NC nem informa que houve correção.
  List<CipaParticipationEvent> pendingObservations(String mandateId) {
    if (mandateId.trim().isEmpty) return const [];
    final observations = rules.observations(mandateId);
    final pending = observations.where((observation) {
      final review = rules.latest(
        observation.id,
        const {'observation_review'},
      );
      return review == null ||
          review.data['observationId'] != observation.id ||
          review.data['mandateId'] != mandateId ||
          review.date.isBefore(observation.date);
    }).toList(growable: false);
    return pending.reversed.toList(growable: false);
  }

  /// Uma informação de andamento requer nova conferência se for posterior
  /// à última avaliação. Isso não altera status técnico da ação.
  Set<String> pendingProgressActionIds(Iterable<String> openActionIds) {
    final pending = <String>{};
    for (final actionId in openActionIds.toSet()) {
      if (actionId.trim().isEmpty) continue;
      final report = rules.progress(actionId);
      if (report == null) continue;
      final review = rules.latest(actionId, const {'progress_review'});
      final accepted = review != null &&
          review.data['reportEventId'] == report.id &&
          !review.date.isBefore(report.date);
      if (!accepted) pending.add(actionId);
    }
    return pending;
  }

  /// Recência e escopo permanecem ligados ao mesmo registro original.
  /// Após nova mensagem, a confirmação anterior deixa de quitar a fila.
  CipaParticipationEvent? pendingProgressReport(String actionId) {
    return pendingProgressActionIds([actionId]).contains(actionId)
        ? rules.progress(actionId)
        : null;
  }
}

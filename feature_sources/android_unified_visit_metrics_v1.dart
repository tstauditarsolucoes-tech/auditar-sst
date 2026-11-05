/// Leitura agregada da Ronda Expressa para a tela inicial Android.
/// Não altera o armazenamento nem os serviços de sincronização.
class RoundVisitOverview {
  const RoundVisitOverview({required this.rounds, required this.openIssues});
  final int rounds;
  final int openIssues;
}

class UnifiedVisitMetrics {
  static String _normal(String value) {
    var result=value.toLowerCase().trim();
    for (final entry in const {
      'á':'a','à':'a','ã':'a','â':'a','é':'e','ê':'e',
      'í':'i','ó':'o','õ':'o','ô':'o','ú':'u','ç':'c'
    }.entries) {
      result=result.replaceAll(entry.key,entry.value);
    }
    return result;
  }

  static bool _isNonConformity(Map payload) {
    final kind=_normal((payload['observationKind'] ??
        payload['findingType'] ?? '').toString());
    if (kind.isEmpty || kind=='conformidade' || kind=='boa pratica' ||
        kind=='conforme') return false;
    return kind.contains('nao conform') || kind=='nc' ||
      kind.contains('condicao insegura') || kind.contains('ato inseguro') ||
      kind=='risco' || kind=='nao_conformidade';
  }

  static bool _isCorrected(Map<String,Object?> row, Map payload) {
    final status=_normal((payload['correctionStatus'] ??
      payload['treatmentStatus'] ?? row['status'] ?? '').toString());
    // "Ronda finalizada" não significa que uma NC foi corrigida.
    return status.contains('corrig') || status.contains('resolvid') ||
      status.contains('valid') || status.contains('fechad');
  }

  /// Um roundId representa uma ronda; os seus vários achados não são
  /// contados como vistorias adicionais. Só inclui rondas com registros salvos.
  /// Ocorrências avulsas sem roundId são excluídas para evitar falso aumento.
  static RoundVisitOverview calculate(
      Iterable<Map<String,Object?>> records,
      {Set<String> existingIssueRecordIds = const {}}) {
    final roundKeys=<String>{};
    final issueKeys=<String>{};
    for(final row in records) {
      final payload=row['payload'];
      if(payload is! Map) continue;
      final companyId=(row['companyId'] ?? '').toString().trim();
      final roundId=(payload['roundId'] ?? '').toString().trim();
      if(companyId.isEmpty || roundId.isEmpty) continue;
      roundKeys.add('$companyId|$roundId');
      final id=(row['id'] ?? '').toString().trim();
      if(id.isEmpty || existingIssueRecordIds.contains(id)) continue;
      if(_isNonConformity(payload) && !_isCorrected(row,payload)) {
        issueKeys.add('$companyId|$id');
      }
    }
    return RoundVisitOverview(rounds:roundKeys.length,
      openIssues:issueKeys.length);
  }
}

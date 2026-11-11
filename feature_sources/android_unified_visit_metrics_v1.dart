/// Indicadores de Ronda Expressa para a Home Android, calculados somente
/// sobre registros locais já salvos. Não altera banco, sincronização nem PDF.
class RoundVisitOverview {
  const RoundVisitOverview({required this.rounds,required this.openIssues});
  final int rounds;
  final int openIssues;
}

class UnifiedVisitMetrics {
  static String _normal(String value) {
    var result=value.toLowerCase().trim();
    for(final entry in const {
      'á':'a','à':'a','ã':'a','â':'a','é':'e','ê':'e',
      'í':'i','ó':'o','õ':'o','ô':'o','ú':'u','ç':'c'
    }.entries) {
      result=result.replaceAll(entry.key,entry.value);
    }
    return result.replaceAll('_',' ').replaceAll('-',' ');
  }

  static bool _isNonConformity(Map payload) {
    final kind=_normal((payload['observationKind'] ??
        payload['findingType'] ?? '').toString());
    if(kind.isEmpty||kind=='conformidade'||kind=='boa pratica'||
       kind=='conforme')return false;
    return kind.contains('nao conform')||kind=='nc'||
      kind.contains('condicao insegura')||
      kind.contains('ato inseguro')||kind=='risco';
  }

  static bool _isCorrected(Map<String,Object?> row, Map payload) {
    // Estados de execução de vistoria não são comprovantes de tratamento
    // da NC. "Concluída", "Validando" e "Validação pendente" NÃO corrigem.
    final status=_normal((payload['correctionStatus'] ??
      payload['treatmentStatus'] ?? row['status'] ?? '').toString());
    return const <String>{
      'corrigida','corrigido',
      'resolvida','resolvido',
      'validada','validado',
      'fechada','fechado',
      'encerrada','encerrado',
      'corrigida e validada','corrigido e validado'
    }.contains(status);
  }

  /// Cada ronda conta uma única vez por empresa/roundId, mesmo que haja
  /// vários achados ou sincronizações repetidas. Ocorrências sem roundId
  /// NÃO passam a ser contabilizadas como rondas.
  ///
  /// [companyIds] restringe o escopo exibido a empresas autorizadas.
  /// [alreadyCountedRoundKeys] recebe somente chaves no formato
  /// "companyId|roundId" já contadas por outro indicador, impedindo soma
  /// duplicada quando a Home também contabiliza a mesma ronda.
  /// [existingIssueRecordIds] aceita tanto IDs antigos quanto chaves
  /// "companyId|recordId" de NCs já apresentadas em outro painel.
  static RoundVisitOverview calculate(
    Iterable<Map<String,Object?>> records,{
    Set<String> existingIssueRecordIds=const {},
    Set<String>? companyIds,
    Set<String> alreadyCountedRoundKeys=const {},
  }) {
    final roundKeys=<String>{};
    final issueKeys=<String>{};
    for(final row in records) {
      final payload=row['payload'];
      if(payload is! Map)continue;
      final companyId=(row['companyId']??'').toString().trim();
      final roundId=(payload['roundId']??'').toString().trim();
      if(companyId.isEmpty||roundId.isEmpty||
          (companyIds!=null&&!companyIds.contains(companyId)))continue;
      final roundKey='$companyId|$roundId';
      if(!alreadyCountedRoundKeys.contains(roundKey)) {
        roundKeys.add(roundKey);
      }
      final id=(row['id']??'').toString().trim();
      if(id.isEmpty||existingIssueRecordIds.contains(id)||
         existingIssueRecordIds.contains('$companyId|$id'))continue;
      if(_isNonConformity(payload)&&!_isCorrected(row,payload)) {
        issueKeys.add('$companyId|$id');
      }
    }
    return RoundVisitOverview(
      rounds:roundKeys.length,openIssues:issueKeys.length);
  }
}

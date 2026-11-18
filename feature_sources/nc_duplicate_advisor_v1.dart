/// Sugestões de NC semelhante para conferência humana antes de nova Ronda.
/// Não cria/edita registros, não sugere encerrar NC e não sincroniza.
class NcSimilarityCandidate {
  const NcSimilarityCandidate({
    required this.id, required this.companyId, required this.sector,
    required this.description, required this.score,
    required this.row,
  });
  final String id, companyId, sector, description;
  final double score;
  final Map<String, dynamic> row;
}

class NcDuplicateAdvisor {
  const NcDuplicateAdvisor._();

  static String first(Map<String,dynamic> row, List<String> keys) {
    for(final key in keys) {
      final value=(row[key]??'').toString().trim();
      if(value.isNotEmpty)return value;
    }
    return '';
  }

  static String normalize(String value) {
    var result=value.toLowerCase().trim();
    const accents={
      'á':'a','à':'a','â':'a','ã':'a','ä':'a',
      'é':'e','ê':'e','è':'e','í':'i','ì':'i',
      'ó':'o','ô':'o','õ':'o','ú':'u','ù':'u',
      'ü':'u','ç':'c',
    };
    for(final entry in accents.entries) {
      result=result.replaceAll(entry.key,entry.value);
    }
    return result.replaceAll(RegExp(r'[^a-z0-9]+'),' ').trim();
  }

  static const _stop={
    'a','as','o','os','um','uma','de','da','das','do','dos',
    'na','nas','no','nos','em','por','para','e','ou','com',
    'sem','que','foi','esta','estao','estava','continua',
    'falta','ausencia','ausente','presenca','existente',
    'equipamento','equipamentos','area','local','setor',
    'risco','problema','situacao','registro','observada',
  };

  static Set<String> tokens(String value) => normalize(value)
      .split(' ')
      .where((w)=>w.length>=3&&!_stop.contains(w))
      .toSet();

  static bool closed(String rawStatus) {
    final status=normalize(rawStatus);
    return const {
      'corrigida','corrigido','resolvida','resolvido',
      'validada','validado','fechada','fechado',
      'encerrada','encerrado','corrigida e validada',
      'corrigido e validado'
    }.contains(status);
  }

  /// Requer descrição informativa com pelo menos dois termos em comum.
  /// Setores divergentes bloqueiam a recomendação. Se não houver setor,
  /// exibe somente como hipótese, ainda sujeita a conferência do técnico.
  static List<NcSimilarityCandidate> suggest({
    required String companyId,
    required String description,
    String sector='',
    required Iterable<Map<String,dynamic>> existingOpenNcs,
    int maxResults=5,
  }) {
    if(companyId.trim().isEmpty)throw ArgumentError('Empresa obrigatória');
    if(maxResults<1||maxResults>20)throw RangeError.range(maxResults,1,20);
    final words=tokens(description);
    if(words.length<2)return const [];
    final wantedSector=normalize(sector);
    final seen=<String>{};
    final matches=<NcSimilarityCandidate>[];
    for(final row in existingOpenNcs) {
      final cid=first(row,['company_id','companyId','empresa_id']);
      final id=first(row,['id','nc_id','ncId']);
      if(cid!=companyId.trim()||id.isEmpty||!seen.add(id))continue;
      final status=first(row,['correctionStatus','treatmentStatus',
          'correction_status','treatment_status','status']);
      if(closed(status))continue;
      final problem=first(row,['description','title','descricao']);
      final existingSector=first(row,['sector','sector_name','setor']);
      final normalizedSector=normalize(existingSector);
      if(wantedSector.isNotEmpty && normalizedSector.isNotEmpty &&
         wantedSector!=normalizedSector)continue;
      final other=tokens(problem);
      if(other.length<2)continue;
      final overlap=words.intersection(other).length;
      if(overlap<2)continue;
      final overlapRatio=overlap/(words.length+other.length-overlap);
      final containment=overlap/(words.length<other.length?
          words.length:other.length);
      // São sugestões para revisão, não fusão automática.
      final score=(overlapRatio+containment)/2;
      if(score<0.59)continue;
      matches.add(NcSimilarityCandidate(
        id:id,companyId:cid,sector:existingSector,
        description:problem,score:score,row:Map.unmodifiable(row),
      ));
    }
    matches.sort((a,b){
      final order=b.score.compareTo(a.score);
      return order!=0?order:a.id.compareTo(b.id);
    });
    return List.unmodifiable(matches.take(maxResults));
  }
}

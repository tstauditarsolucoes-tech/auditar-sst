/// Preparação local de visita para uma empresa já autorizada pelo aplicativo.
/// NÃO executa análise automática de risco, não encerra NC e não sincroniza.
/// Usa somente os registros OBSERVACAO_SEGURANCA (Ronda Expressa) existentes.
class VisitBriefingItem {
  const VisitBriefingItem({
    required this.id,
    required this.sector,
    required this.description,
    required this.roundId,
    this.recurrenceCandidate=false,
  });
  final String id,sector,description,roundId;
  final bool recurrenceCandidate;
}

class VisitBriefing {
  const VisitBriefing({
    required this.companyId,
    required this.savedRounds,
    required this.openObservations,
    required this.recurrenceCandidates,
    required this.items,
    required this.scannedRecords,
  });
  final String companyId;
  final int savedRounds,openObservations,recurrenceCandidates,scannedRecords;
  final List<VisitBriefingItem> items;
  bool get hasLocalData=>savedRounds>0||scannedRecords>0;
}

class VisitIntelligence {
  const VisitIntelligence._();

  static String _text(Object? value)=>value==null?'':value.toString().trim();

  static String _normalized(Object? value) {
    var s=_text(value).toLowerCase();
    const accents={
      'á':'a','à':'a','â':'a','ã':'a','ä':'a',
      'é':'e','ê':'e','í':'i',
      'ó':'o','ô':'o','õ':'o','ú':'u','ü':'u','ç':'c',
    };
    for(final entry in accents.entries) {
      s=s.replaceAll(entry.key,entry.value);
    }
    return s.replaceAll(RegExp(r'[\s\-_]+'),' ').trim();
  }

  static bool _isRisk(Map<Object?,Object?> payload) {
    final kind=_normalized(
      payload['observationKind']??payload['findingType']);
    return kind=='nc'||kind.contains('nao conform')||
      kind.contains('condicao insegura')||
      kind.contains('ato inseguro')||kind=='risco';
  }

  static bool _resolved(Map<String,Object?> row,
    Map<Object?,Object?> payload) {
    final status=_normalized(payload['correctionStatus']??
      payload['treatmentStatus']??row['status']);
    // Uma vistoria finalizada NÃO comprova correção do risco.
    return const {
      'resolvida','resolvido','corrigida','corrigido',
      'validada','validado','fechada','fechado',
      'corrigida e validada','corrigido e validado',
    }.contains(status);
  }

  /// Uma ocorrência por ID. Supostas recorrências precisam existir em duas
  /// rondas distintas da MESMA empresa/setor com descrição igual normalizada.
  /// Por segurança são somente candidatos para o TST revisar.
  static VisitBriefing fromLocalRondas({
    required String companyId,
    required Iterable<Map<String,Object?>> records,
    int maxVisible=5,
  }) {
    if(companyId.trim().isEmpty) {
      throw ArgumentError.value(companyId,'companyId','Empresa obrigatória');
    }
    if(maxVisible<1||maxVisible>30) {
      throw RangeError.range(maxVisible,1,30,'maxVisible');
    }

    final seenRecordIds=<String>{};
    final roundIds=<String>{};
    final open=<VisitBriefingItem>[];
    final roundsByKey=<String,Set<String>>{};
    var scanned=0;

    for(final record in records) {
      if(_text(record['companyId'])!=companyId.trim())continue;
      final id=_text(record['id']);
      final payload=record['payload'];
      if(id.isEmpty||payload is! Map)continue;
      if(!seenRecordIds.add(id))continue;
      scanned++;
      final values=Map<Object?,Object?>.from(payload);
      final roundId=_text(values['roundId']);
      // Rondas sem identidade não são contabilizadas como visitas.
      if(roundId.isEmpty)continue;
      roundIds.add(roundId);

      if(!_isRisk(values)||_resolved(record,values))continue;

      final sector=_text(values['sector']??values['location']??
        values['place']);
      final description=_text(values['description']??
        values['observation']??values['detail']);
      final safeDescription=description.isEmpty?
        'Situação registrada sem descrição disponível':
        description.length>180?description.substring(0,180):description;
      open.add(VisitBriefingItem(
        id:id,roundId:roundId,
        sector:sector.isEmpty?'Setor não informado':sector,
        description:safeDescription,
      ));

      final fingerprint=_normalized(sector)+'|'+_normalized(description);
      // Sem setor e descrição não há base suficiente para recorrência.
      if(sector.isNotEmpty&&description.length>=8){
        (roundsByKey[fingerprint]??=<String>{}).add(roundId);
      }
    }

    final candidates=<VisitBriefingItem>[];
    for(final item in open) {
      final sector=item.sector=='Setor não informado'?'':item.sector;
      final fingerprint=_normalized(sector)+'|'+_normalized(item.description);
      final repeated=sector.isNotEmpty&&
        item.description!='Situação registrada sem descrição disponível'&&
        (roundsByKey[fingerprint]?.length??0)>=2;
      candidates.add(VisitBriefingItem(
        id:item.id,sector:item.sector,description:item.description,
        roundId:item.roundId,recurrenceCandidate:repeated));
    }
    return VisitBriefing(
      companyId:companyId.trim(),
      scannedRecords:scanned,
      savedRounds:roundIds.length,
      openObservations:candidates.length,
      recurrenceCandidates:candidates
        .where((i)=>i.recurrenceCandidate).length,
      items:List.unmodifiable(candidates.reversed.take(maxVisible).toList()),
    );
  }
}

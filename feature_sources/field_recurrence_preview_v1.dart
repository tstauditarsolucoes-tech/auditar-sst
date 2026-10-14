/// Consulta conservadora de reincidencias. Nao altera banco, sync ou UI.
class FieldRecurrenceItem {
  const FieldRecurrenceItem(this.id,this.companyId,this.worksiteId,this.sector,this.text);
  final String id,companyId,worksiteId,sector,text;
}
class FieldRecurrenceMatch {
  const FieldRecurrenceMatch(this.item,this.score);
  final FieldRecurrenceItem item;
  final int score;
}
class FieldRecurrencePreview {
  const FieldRecurrencePreview._();
  static String normalize(String value) {
    const map={'á':'a','à':'a','â':'a','ã':'a','é':'e','ê':'e','í':'i','ó':'o','ô':'o','õ':'o','ú':'u','ç':'c'};
    final chars=StringBuffer();
    for(final code in value.toLowerCase().runes) {
      final c=String.fromCharCode(code);
      chars.write(map[c]??c);
    }
    return chars.toString().replaceAll(RegExp(r'[^a-z0-9]+'),' ').trim();
  }
  static const families=<String,List<String>>{
    'maquinas':['correia','polia','prensa','engrenagem','maromba'],
    'parada':['botoeira','botao emergencia','parada emergencia','intertravamento','sensor'],
    'incendio':['extintor','hidrante','incendio'],
    'altura':['andaime','guarda corpo','ancoragem','talabarte'],
    'eletrica':['eletrico','aterramento','fiacao'],
    'poeira':['poeira','respirador'],
    'ruido':['ruido','auricular']
  };
  static Set<String> groups(String value) {
    final text=' ${normalize(value)} ';
    return families.entries.where((e)=>e.value.any((v)=>text.contains(' $v '))).map((e)=>e.key).toSet();
  }
  static Set<String> words(String value) {
    const ignored={'para','com','sem','uma','esta','falta','risco','setor','local','de','do','da'};
    return normalize(value).split(' ').where((w)=>w.length>=4&&!ignored.contains(w)).toSet();
  }
  static List<FieldRecurrenceMatch> find({
    required String companyId,required String sector,required String description,
    required Iterable<FieldRecurrenceItem> history,String worksiteId='',int limit=3,
  }) {
    if(companyId.trim().isEmpty||sector.trim().isEmpty||description.trim().isEmpty||limit<=0)return const [];
    final kinds=groups(description),tokens=words(description);
    if(kinds.isEmpty||tokens.isEmpty)return const [];
    final results=<FieldRecurrenceMatch>[];
    for(final item in history) {
      if(item.id.isEmpty||item.companyId!=companyId||normalize(item.sector)!=normalize(sector))continue;
      if(worksiteId.isNotEmpty&&item.worksiteId!=worksiteId)continue;
      if(kinds.intersection(groups(item.text)).isEmpty)continue;
      final older=words(item.text),common=tokens.intersection(older).length;
      final total=tokens.union(older).length;
      if(total==0||common==0)continue;
      final score=(100*common/total).round();
      if(score<20)continue;
      results.add(FieldRecurrenceMatch(item,score));
    }
    results.sort((a,b) {final n=b.score.compareTo(a.score);return n!=0?n:a.item.id.compareTo(b.item.id);});
    return results.take(limit).toList(growable:false);
  }
}

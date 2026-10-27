import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/offline_sst_expanded_catalog_v1.dart';
import 'package:auditar_sst/widgets/offline_report_inline_suggestions.dart';
void main() {
 test('acervo expandido contém campos técnicos sem duplicar IDs', () {
   final entries=OfflineSstExpandedCatalog.entries;
   expect(entries.length, greaterThanOrEqualTo(35));
   expect(entries.map((x)=>x['id']).toSet().length, entries.length);
   for (final item in entries) {
     for (final key in ['id','title','description','risk','possibleConsequence','recommendation','priority']) {
       expect((item[key]??'').trim(),isNotEmpty);
     }
   }
 });
 test('biblioteca combina catálogo existente com novos temas', () {
   final all=OfflineReportInlineSuggestionService.fallbackForTesting;
   expect(all.any((x)=>x.title.contains('ASO')),isTrue);
   expect(all.any((x)=>x.title.contains('PCMSO')),isTrue);
   expect(all.any((x)=>x.title.contains('Prensa cerâmica')),isTrue);
 });
 test('busca local reconhece termos específicos', () {
   final ranked=OfflineReportInlineSuggestionService.rankForTesting('ASO vencido');
   expect(ranked.any((x)=>x.title.contains('ASO')),isTrue);
 });
}

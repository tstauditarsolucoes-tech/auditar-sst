import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/offline_sst_deep_catalog_v2.dart';
import 'package:auditar_sst/widgets/offline_report_inline_suggestions.dart';

void main() {
  test('acervo detalhado: 122 casos, sem duplicidade e cobertura de NRs', () {
    final all=OfflineSstDeepCatalog.entries;
    expect(all.length,122);
    expect(all.map((e)=>e['id']).toSet().length,122);
    for(final nr in ['NR-12','NR-06','NR-18','NR-23','NR-31','NR-35']) {
      expect(all.where((e)=>e['nr']==nr).length,greaterThanOrEqualTo(15));
    }
    for(final item in all) {
      for(final f in ['id','nr','title','description','risk','possibleConsequence',
         'recommendation','priority','entityRegex','faultRegex']) {
        expect((item[f]??'').trim(),isNotEmpty,reason:f);
      }
    }
  });
  test('vencimento de inspeção é distinto de ensaio', () {
    final list=OfflineSstDeepCatalog.matches('Extintor com inspeção vencida');
    expect(list.any((e)=>e['id']=='deep-nr23-inspecao-venc'),isTrue);
    expect(list.any((e)=>e['id']=='deep-nr23-ensaio-venc'),isFalse);
  });
  test('ensaio hidrostático é distinto da inspeção', () {
    final list=OfflineSstDeepCatalog.matches('Extintor com ensaio hidrostático vencido');
    expect(list.any((e)=>e['id']=='deep-nr23-ensaio-venc'),isTrue);
    expect(list.any((e)=>e['id']=='deep-nr23-inspecao-venc'),isFalse);
  });
  test('não sugere falha em texto de conformidade', () {
    expect(OfflineSstDeepCatalog.matches('Extintor não está vencido'),isEmpty);
    expect(OfflineSstDeepCatalog.matches('Extintor funcionando normalmente'),isEmpty);
    expect(OfflineSstDeepCatalog.matches('Máquina com proteção instalada'),isEmpty);
  });
  test('identifica máquinas e campo agrícola', () {
    expect(OfflineSstDeepCatalog.matches('Roçadeira sem proteção')
       .any((e)=>e['nr']=='NR-31'),isTrue);
    expect(OfflineSstDeepCatalog.matches('Esteira sem proteção')
       .any((e)=>e['nr']=='NR-12'),isTrue);
  });
  test('biblioteca de vistoria mantém os modelos detalhados', () {
    final all=OfflineReportInlineSuggestionService.fallbackForTesting;
    expect(all.any((x)=>x.id=='deep-nr23-inspecao-venc'),isTrue);
    expect(all.any((x)=>x.title=='Roçadeira sem proteção adequada'),isTrue);
  });
}

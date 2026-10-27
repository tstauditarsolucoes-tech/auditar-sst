import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/offline_sst_deep_catalog_v2.dart';
import 'package:auditar_sst/widgets/offline_report_inline_suggestions.dart';

void main() {
  test('acervo detalhado: 145 casos, sem duplicidade e cobertura de NRs', () {
    final all=OfflineSstDeepCatalog.entries;
    expect(all.length,145);
    expect(all.map((e)=>e['id']).toSet().length,145);
    for(final nr in ['NR-12','NR-06','NR-17','NR-18','NR-23','NR-31','NR-35']) {
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
    expect(OfflineSstDeepCatalog.matches('Cadeira sem encosto, já corrigida'),isEmpty);
    expect(OfflineSstDeepCatalog.matches('EPI danificado, já substituído'),isEmpty);
  });
  test('NR-17: reconhece ergonomia e evita NC sem falha descrita', () {
    expect(OfflineSstDeepCatalog.matches('Cadeira sem encosto').any((e)=>e['nr']=='NR-17'),isTrue);
    expect(OfflineSstDeepCatalog.matches('Cadeira com encosto adequado'),isEmpty);
    expect(OfflineSstDeepCatalog.matches('Trabalho em pé sem alternância').any((e)=>e['nr']=='NR-17'),isTrue);
  });
  test('busca de vistoria ignora a ordem das palavras', () {
    final items=OfflineSstDeepCatalog.browse(search:'vencida inspecao extintor');
    expect(items.any((e)=>e['id']=='deep-nr23-inspecao-venc'),isTrue);
    expect(OfflineSstDeepCatalog.browse(search:'extintor com inspeção vencida')
      .any((e)=>e['id']=='deep-nr23-inspecao-venc'),isTrue);
  });
  test('filtro por NR evita mistura de modelos', () {
    final nr17=OfflineSstDeepCatalog.browse(standard:'NR-17',search:'cadeira encosto');
    expect(nr17,isNotEmpty);
    expect(nr17.every((e)=>e['nr']=='NR-17'),isTrue);
    final others=OfflineSstDeepCatalog.browse(standard:'Outras');
    expect(others.any((e)=>e['nr']=='NR-12'),isFalse);
    expect(others.any((e)=>e['nr']=='NR-17'),isFalse);
  });
  test('busca vazia lista sugestões sem bloquear a vistoria', () {
    expect(OfflineSstDeepCatalog.browse(standard:'NR-17').length,greaterThan(20));
    expect(OfflineSstDeepCatalog.browse(limit:0),isEmpty);
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

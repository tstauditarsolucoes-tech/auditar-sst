import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/offline_sst_deep_catalog_v2.dart';
import 'package:auditar_sst/services/offline_sst_field_catalog_v3.dart';
import 'package:auditar_sst/widgets/offline_report_inline_suggestions.dart';

void main() {
  group('Biblioteca offline setorial v3, preservando a anterior', () {
    test('mantém 145 anteriores e adiciona 59 sem duplicar ID', () {
      expect(OfflineSstFieldCatalogV3.entries.length, 59);
      expect(OfflineSstDeepCatalog.entries.length, 204);
      final ids=OfflineSstDeepCatalog.entries
          .map((item)=>item['id']).toList();
      expect(ids.toSet().length, ids.length);
      expect(ids, contains('deep-nr12-corr-trans'));
      expect(ids, contains('deep-nr23-inspecao-venc'));
      expect(ids, contains('campo-v3-cer03'));
      expect(ids, contains('campo-v3-obr04'));
      expect(ids, contains('campo-v3-pad01'));
      expect(ids, contains('campo-v3-lat01'));
      expect(ids, contains('campo-v3-urb04'));
    });

    test('cada modelo contém NR temática, risco, consequência e recomendação', () {
      const required=[
        'id','segment','nr','title','description','risk',
        'possibleConsequence','recommendation','priority',
        'entityRegex','faultRegex','example'
      ];
      for (final item in OfflineSstFieldCatalogV3.entries) {
        for (final field in required) {
          expect(item[field]?.trim(),isNotEmpty,reason:item['id']);
        }
        expect(['Baixa','Média','Alta','Crítica'],
          contains(item['priority']),reason:item['id']);
        expect(item['description']!.toLowerCase(),
          contains('conferir no local'),reason:item['id']);
      }
    });

    test('cada exemplo específico reconhece seu próprio modelo', () {
      for(final entry in OfflineSstFieldCatalogV3.entries) {
        final found=OfflineSstDeepCatalog.matches(entry['example']!);
        expect(found.map((x)=>x['id']),contains(entry['id']),
          reason:entry['id']);
      }
    });

    test('não sugerir falha em situação corrigida ou incerta', () {
      for(final description in [
        'Masseira funcionando normalmente',
        'Betoneira sem aterramento, já regularizado',
        'Talvez o sensor da empacotadora esteja inoperante',
        'Poda de árvore sem isolamento, já corrigido',
        'Roçadeira sem protetor, situação não confirmada',
        'Extintor não está vencido',
      ]) {
        expect(OfflineSstDeepCatalog.matches(description),isEmpty,
          reason:description);
      }
    });

    test('busca por segmento e NR mantém os modelos antigos', () {
      final ceramic=OfflineSstDeepCatalog.browse(search:'Cerâmica');
      expect(ceramic.where((e)=>e['segment']=='Cerâmica').length,12);
      final building=OfflineSstDeepCatalog.browse(search:'Construção civil');
      expect(building.where((e)=>e['segment']=='Construção civil').length,15);
      final bakery=OfflineSstDeepCatalog.browse(search:'Panificação');
      expect(bakery.where((e)=>e['segment']=='Panificação').length,8);
      final urban=OfflineSstDeepCatalog.browse(search:'Limpeza urbana');
      expect(urban.where((e)=>e['segment']=='Limpeza urbana').length,7);
      final nr=OfflineSstDeepCatalog.browse(standard:'NR-12',search:'masseira');
      expect(nr.any((e)=>e['id']=='campo-v3-pad01'),isTrue);
      expect(nr.every((e)=>e['nr']=='NR-12'),isTrue);
      expect(OfflineSstDeepCatalog.browse().length,204);
    });

    test('novos modelos integrados ao serviço original de sugestões', () {
      final all=OfflineReportInlineSuggestionService.fallbackForTesting;
      expect(all.any((e)=>e.id=='campo-v3-lat01'),isTrue);
      expect(all.any((e)=>e.id=='campo-v3-cer03'),isTrue);
      expect(all.any((e)=>e.id=='deep-nr23-ensaio-venc'),isTrue);
    });

    test('não misturar falhas de equipamentos diferentes', () {
      final found=OfflineSstDeepCatalog.matches(
        'Empacotadora com sensor inoperante');
      expect(found.map((e)=>e['id']),contains('campo-v3-lat01'));
      expect(found.any((e)=>e['id']=='campo-v3-obr04'),isFalse);
      expect(found.any((e)=>e['id']=='campo-v3-pad05'),isFalse);
      final current=OfflineSstDeepCatalog.matches(
        'Extintor da oficina sem placa');
      expect(current.map((e)=>e['id']),contains('campo-v3-lat06'));
      expect(current.any((e)=>e['id']=='campo-v3-lat01'),isFalse);
    });
  });
}

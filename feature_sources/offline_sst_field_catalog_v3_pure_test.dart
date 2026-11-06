import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/offline_sst_deep_catalog_v2.dart';
import 'package:auditar_sst/services/offline_sst_field_catalog_v3.dart';

void main() {
  test('145 modelos anteriores mais 95 setoriais, sem duplicação', () {
    final all=OfflineSstDeepCatalog.entries;
    expect(OfflineSstFieldCatalogV3.entries.length, 95);
    expect(all.length, 240);
    expect(all.map((e)=>e['id']).toSet().length, 240);
    expect(all.any((e)=>e['id']=='deep-nr23-ensaio-venc'),isTrue);
    expect(all.any((e)=>e['id']=='campo-v3-cer03'),isTrue);
  });
  test('todos os exemplos específicos ativam somente critérios explícitos', () {
    for(final item in OfflineSstFieldCatalogV3.entries){
      final matches=OfflineSstDeepCatalog.matches(item['example']!);
      expect(matches.map((e)=>e['id']),contains(item['id']),
        reason:item['id']);
    }
  });
  test('busca por setor, por NR e catálogo inteiro offline', () {
    expect(OfflineSstDeepCatalog.browse().length, 240);
    expect(OfflineSstDeepCatalog.browse(search:'Cerâmica')
      .where((e)=>e['segment']=='Cerâmica').length,17);
    expect(OfflineSstDeepCatalog.browse(search:'Limpeza urbana')
      .where((e)=>e['segment']=='Limpeza urbana').length,11);
    expect(OfflineSstDeepCatalog.browse(standard:'NR-12',search:'masseira')
      .any((e)=>e['id']=='campo-v3-pad01'),isTrue);
    expect(OfflineSstDeepCatalog.browse(standard:'NR-10',search:'quadro')
      .every((e)=>e['nr']=='NR-10'),isTrue);
  });
  test('descrições corrigidas e incertas não geram sugestão de falha', () {
    for(final text in [
      'Masseira funcionando normalmente',
      'Betoneira sem aterramento, já regularizado',
      'Talvez o sensor da empacotadora esteja inoperante',
      'Poda de árvore sem isolamento, já corrigido',
      'Roçadeira sem protetor, situação não confirmada',
    ]){
      expect(OfflineSstDeepCatalog.matches(text),isEmpty,reason:text);
    }
  });
}

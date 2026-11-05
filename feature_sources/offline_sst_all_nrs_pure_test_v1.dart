import 'offline_sst_all_nrs_v1.dart';

void main() {
  final all = OfflineSstAllNrsCatalog.entries;
  final standards = OfflineSstAllNrsCatalog.activeStandards;
  if (all.length != 151 || standards.length != 36) {
    throw StateError('Totais de entradas ou NRs inesperados');
  }
  if (standards.toSet().length != 36 ||
      standards.contains('NR-02') || standards.contains('NR-27')) {
    throw StateError('A lista de NRs vigentes contém valores inválidos');
  }
  final ids = <String>{};
  for (final item in all) {
    if (!ids.add(item['id'] ?? '')) {
      throw StateError('ID duplicado: ${item['id']}');
    }
    for (final key in const [
      'id','nr','title','description','risk','possibleConsequence',
      'recommendation','priority','entityRegex','faultRegex',
      'scope','browseOnly',
    ]) {
      if ((item[key] ?? '').trim().isEmpty) {
        throw StateError('Campo vazio: $key');
      }
    }
    try {
      RegExp(item['entityRegex']!);
      RegExp(item['faultRegex']!);
    } catch (error) {
      throw StateError('Expressão inválida em ${item['id']}: $error');
    }
  }
  for (final nr in standards) {
    if (all.where((row) => row['nr'] == nr).length < 4) {
      throw StateError('Sem cobertura mínima da $nr');
    }
  }
  for (final item in all.where((e) =>
      const {'NR-03','NR-15','NR-16','NR-28'}.contains(e['nr']))) {
    if (item['browseOnly'] != 'true') {
      throw StateError('Enquadramento automático proibido: ${item['id']}');
    }
  }
  print('ALL_NRS_CATALOG_151_OK; 36_NRS_VIGENTES; SEM_ENQUADRAMENTO_AUTOMATICO');
}

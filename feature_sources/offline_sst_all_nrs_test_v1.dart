import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/offline_sst_all_nrs_v1.dart';
import 'package:auditar_sst/services/offline_sst_deep_catalog_v2.dart';
import 'package:auditar_sst/widgets/offline_report_inline_suggestions.dart';

void main() {
  test('todas as 36 NRs vigentes estão cobertas por modelos distintos', () {
    final standards = OfflineSstAllNrsCatalog.activeStandards;
    final entries = OfflineSstAllNrsCatalog.entries;
    expect(standards.length, 36);
    expect(standards.toSet().length, 36);
    expect(entries.length, 151);
    expect(OfflineSstAllNrsCatalog.revokedStandards,
      containsAll(['NR-02', 'NR-27']));
    expect(standards, isNot(contains('NR-02')));
    expect(standards, isNot(contains('NR-27')));
    expect(entries.map((e) => e['id']).toSet().length, 151);
    for (final nr in standards) {
      expect(entries.where((e) => e['nr'] == nr).length,
        greaterThanOrEqualTo(4), reason: nr);
    }
    for (final entry in entries) {
      for (final key in const [
        'id', 'nr', 'title', 'description', 'risk',
        'possibleConsequence', 'recommendation', 'priority',
        'entityRegex', 'faultRegex', 'scope', 'browseOnly',
      ]) {
        expect((entry[key] ?? '').trim(), isNotEmpty, reason: key);
      }
      expect(() => RegExp(entry['entityRegex']!), returnsNormally);
      expect(() => RegExp(entry['faultRegex']!), returnsNormally);
    }
  });

  test('não duplica os 145 antigos nem os 49 de panificação', () {
    final all = OfflineSstDeepCatalog.entries;
    expect(all.length, 345);
    expect(all.map((e) => e['id']).toSet().length, 345);
    expect(all.any((e) => e['id'] == 'deep-nr12-corr-trans'), isTrue);
    expect(all.any((e) => e['id'] == 'bakery-nr12-ama-grade-ausente'), isTrue);
    expect(all.any((e) => e['id'] == 'all-nrs-01-01'), isTrue);
    final fallback = OfflineReportInlineSuggestionService.fallbackForTesting;
    expect(fallback.any((x) => x.id == 'all-nrs-33-01'), isTrue);
  });

  test('busca por qualquer NR e exceções de normas revogadas', () {
    for (final nr in OfflineSstAllNrsCatalog.activeStandards) {
      final found = OfflineSstDeepCatalog.browse(standard: nr);
      expect(found, isNotEmpty, reason: nr);
      expect(found.every((e) => e['nr'] == nr), isTrue, reason: nr);
    }
    expect(OfflineSstDeepCatalog.browse(standard:'NR-02'), isEmpty);
    expect(OfflineSstDeepCatalog.browse(standard:'NR-27'), isEmpty);
    expect(OfflineSstDeepCatalog.browse(standard:'Panificação').length, 49);
    expect(OfflineSstDeepCatalog.browse().length, 345);
  });

  test('sugere somente com tema e falha explicitamente descritos', () {
    for (final pair in <(String,String)>[
      ('PGR risco ausente', 'all-nrs-01-01'),
      ('CIPA sem ata', 'all-nrs-05-01'),
      ('Quadro elétrico sem tampa', 'all-nrs-10-01'),
      ('Espaço confinado sem PET', 'all-nrs-33-01'),
      ('Trabalho em altura sem AR', 'all-nrs-35-01'),
      ('Coleta urbana sem sinalização', 'all-nrs-38-01'),
    ]) {
      expect(OfflineSstDeepCatalog.matches(pair.$1)
        .any((e) => e['id'] == pair.$2),
        isTrue, reason: pair.$1);
    }
    expect(OfflineSstDeepCatalog.matches(
      'Quadro elétrico funcionando normalmente'), isEmpty);
    expect(OfflineSstDeepCatalog.matches(
      'CIPA sem ata, já corrigido'), isEmpty);
    expect(OfflineSstDeepCatalog.matches(
      'Talvez exista problema no PGR'), isEmpty);
  });

  test('insalubridade, periculosidade, embargo e multa só em consulta', () {
    final consultation = <String>['NR-03', 'NR-15', 'NR-16', 'NR-28'];
    for (final nr in consultation) {
      final items = OfflineSstAllNrsCatalog.entries
        .where((e) => e['nr'] == nr);
      expect(items.length, greaterThanOrEqualTo(4));
      expect(items.every((e) => e['browseOnly'] == 'true'), isTrue);
      expect(OfflineSstDeepCatalog.browse(standard:nr), isNotEmpty);
    }
    final suggestions = OfflineSstDeepCatalog.matches(
      'NR-15 ruído acima do limite sem laudo');
    expect(suggestions.where((e) =>
      e['id']!.startsWith('all-nrs-15-')), isEmpty);
    expect(OfflineSstAllNrsCatalog.entries.where((e) =>
      ['NR-02','NR-27'].contains(e['nr'])), isEmpty);
  });
}

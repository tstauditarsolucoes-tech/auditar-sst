import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/offline_sst_bakery_nr12_v1.dart';
import 'package:auditar_sst/services/offline_sst_deep_catalog_v2.dart';
import 'package:auditar_sst/widgets/offline_report_inline_suggestions.dart';

void main() {
  test('49 modelos de NR-12 panificação com campos e IDs únicos', () {
    final entries = OfflineSstBakeryNr12Catalog.entries;
    expect(entries.length, 49);
    expect(entries.map((e) => e['id']).toSet().length, 49);
    expect(entries.every((e) => e['nr'] == 'NR-12'), isTrue);
    expect(entries.every((e) => e['segment'] == 'Panificação'), isTrue);
    for (final entry in entries) {
      for (final field in const [
        'id', 'nr', 'title', 'description', 'risk',
        'possibleConsequence', 'recommendation', 'priority',
        'entityRegex', 'faultRegex',
      ]) {
        expect((entry[field] ?? '').trim(), isNotEmpty, reason: field);
      }
    }
  });

  test('catálogo antigo preservado, sem ID duplicado', () {
    final entries = OfflineSstDeepCatalog.entries;
    expect(entries.length, 194);
    expect(entries.map((e) => e['id']).toSet().length, 194);
    expect(entries.any((e) => e['id'] == 'deep-nr12-corr-trans'), isTrue);
    expect(entries.any((e) => e['id'] == 'deep-nr17-teleatendimento'), isTrue);
    for (final model in OfflineSstBakeryNr12Catalog.entries) {
      expect(entries.any((e) => e['id'] == model['id']), isTrue);
    }
  });

  test('aba Panificação lista somente modelos específicos', () {
    final matches = OfflineSstDeepCatalog.browse(standard: 'Panificação');
    expect(matches.length, 49);
    expect(matches.every(
      (e) => (e['id'] ?? '').startsWith('bakery-nr12-')), isTrue);
    final amassadeira = OfflineSstDeepCatalog.browse(
      standard: 'Panificação', search: 'amassadeira');
    expect(amassadeira.length, greaterThanOrEqualTo(7));
    final nr12 = OfflineSstDeepCatalog.browse(standard: 'NR-12');
    expect(nr12.length, greaterThan(49));
    expect(nr12.every((e) => e['nr'] == 'NR-12'), isTrue);
    expect(OfflineSstDeepCatalog.browse(standard: 'NR-06')
      .every((e) => e['nr'] == 'NR-06'), isTrue);
  });

  test('sugestões locais com contexto e falha explícitos', () {
    for (final pair in <(String, String)>[
      ('amassadeira sem grade', 'bakery-nr12-ama-grade-ausente'),
      ('batedeira sensor burlado', 'bakery-nr12-bat-intertravamento'),
      ('cilindro sovador sem rolete obstrutivo',
        'bakery-nr12-cil-rolete-obstrutivo'),
      ('modeladora rolos expostos', 'bakery-nr12-mod-rolos'),
      ('laminadora rolos expostos', 'bakery-nr12-lam-rolos'),
      ('fatiadora de pães entrada sem proteção', 'bakery-nr12-fat-entrada'),
      ('moinho de farinha de rosca bocal móvel solto',
        'bakery-nr12-moi-bocal'),
    ]) {
      final found = OfflineSstDeepCatalog.matches(pair.$1);
      expect(found.any((e) => e['id'] == pair.$2), isTrue,
        reason: pair.$1);
    }
  });

  test('não gera NC de condição comprovadamente normal/corrigida', () {
    expect(OfflineSstDeepCatalog.matches(
      'Amassadeira funcionando normalmente'), isEmpty);
    expect(OfflineSstDeepCatalog.matches(
      'Batedeira sensor burlado, já corrigido'), isEmpty);
    expect(OfflineSstDeepCatalog.matches(
      'Laminadora com proteção instalada'), isEmpty);
    expect(OfflineSstDeepCatalog.matches(
      'Fatiadora de pão sem irregularidade'), isEmpty);
  });

  test('não impõe emergência indevida à fatiadora ou ao moinho', () {
    final exceptions = OfflineSstBakeryNr12Catalog.entries.where(
      (e) => (e['id'] ?? '').startsWith('bakery-nr12-fat-') ||
             (e['id'] ?? '').startsWith('bakery-nr12-moi-'));
    expect(exceptions.length, 9);
    expect(exceptions.any((e) =>
      (e['title'] ?? '').contains('emergência')), isFalse);
    final fallback = OfflineReportInlineSuggestionService.fallbackForTesting;
    expect(fallback.any((x) =>
      x.id == 'bakery-nr12-ama-grade-ausente'), isTrue);
  });
}

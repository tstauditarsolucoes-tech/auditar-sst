import 'package:flutter_test/flutter_test.dart';

import 'package:auditar_sst/services/offline_report_knowledge_service.dart';

void main() {
  group('OfflineReportKnowledgeService', () {
    test('biblioteca base cobre situações técnicas recorrentes', () {
      final seeds = OfflineReportKnowledgeService.seedTemplatesForTesting;
      expect(seeds.length, greaterThanOrEqualTo(10));
      expect(seeds.any((item) => item.id == 'auditar-extintor-sem-sinalizacao'), isTrue);
      expect(seeds.any((item) => item.id == 'auditar-sensor-protecao-inoperante'), isTrue);
      expect(seeds.any((item) => item.id == 'auditar-painel-eletrico-aberto'), isTrue);
    });

    test('sanitização remove empresa e CNPJ do conhecimento reaproveitável', () {
      final sanitized = OfflineReportKnowledgeService.sanitizeForTesting(
        'Na Empresa Exemplo 12.345.678/0001-90 foi encontrado painel aberto.',
        'Empresa Exemplo',
      );
      expect(sanitized.toLowerCase(), isNot(contains('empresa exemplo')));
      expect(sanitized, isNot(contains('12.345.678/0001-90')));
      expect(sanitized.toLowerCase(), contains('painel aberto'));
    });

    test('ranking prioriza o modelo coerente com a pesquisa', () {
      final seeds = OfflineReportKnowledgeService.seedTemplatesForTesting;
      final extintor = seeds.firstWhere((item) => item.id == 'auditar-extintor-sem-sinalizacao');
      final ergonomia = seeds.firstWhere((item) => item.id == 'auditar-ergonomia-inadequada');
      expect(
        OfflineReportKnowledgeService.scoreForTesting(extintor, 'extintor sem placa'),
        greaterThan(OfflineReportKnowledgeService.scoreForTesting(ergonomia, 'extintor sem placa')),
      );
    });
  });
}

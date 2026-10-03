import 'package:flutter_test/flutter_test.dart';

import 'package:auditar_sst/widgets/offline_report_inline_suggestions.dart';

void main() {
  group('OfflineReportInlineSuggestionService', () {
    test('sugere extintor a partir da primeira informacao digitada', () {
      final ranked =
          OfflineReportInlineSuggestionService.rankForTesting('extintor sem placa');
      expect(ranked, isNotEmpty);
      expect(ranked.first.id, 'auditar-extintor-sem-sinalizacao');
    });

    test('sugere sensor de protecao sem depender de internet', () {
      final ranked =
          OfflineReportInlineSuggestionService.rankForTesting('sensor porta protecao');
      expect(ranked, isNotEmpty);
      expect(ranked.first.id, 'auditar-sensor-protecao-inoperante');
    });

    test('le modelo aprendido salvo na memoria local', () {
      const raw = '''
      {
        "templates": [
          {
            "id": "aprendido-1",
            "title": "Correia transportadora sem proteção",
            "description": "Proteção lateral ausente na correia.",
            "risk": "Contato com partes móveis.",
            "recommendation": "Regularizar a proteção antes da liberação.",
            "priority": "Crítica",
            "source": "manual_approved",
            "useCount": 3
          }
        ]
      }
      ''';
      final ranked = OfflineReportInlineSuggestionService
          .decodeAndRankForTesting(raw, 'correia sem protecao');
      expect(ranked, isNotEmpty);
      expect(ranked.first.id, 'aprendido-1');
      expect(ranked.first.learned, isTrue);
    });
  });
}

import 'package:flutter_test/flutter_test.dart';

import 'package:auditar_sst/services/offline_field_rules_service.dart';

void main() {
  group('OfflineFieldRulesService', () {
    test('sugere NR-23 e NR-26 para extintor obstruido sem sinalizacao', () {
      final nrs = OfflineFieldRulesService.suggestNrs(
        'Extintor com acesso obstruído e sem sinalização',
      );
      expect(nrs, contains('NR-23'));
      expect(nrs, contains('NR-26'));
    });

    test('sugere NR-12 para protecao de maquina e sensor', () {
      final nrs = OfflineFieldRulesService.suggestNrs(
        'Máquina com proteção removida e sensor inoperante',
      );
      expect(nrs, contains('NR-12'));
    });

    test('matriz eleva recorrencia sem usar IA', () {
      expect(
        OfflineFieldRulesService.priorityFromMatrix(3, 3),
        'Média',
      );
      expect(
        OfflineFieldRulesService.priorityFromMatrix(
          3,
          3,
          recurring: true,
        ),
        'Alta',
      );
      expect(
        OfflineFieldRulesService.priorityFromMatrix(5, 5),
        'Crítica',
      );
    });

    test('gera acao e prazo local', () {
      final result = OfflineFieldRulesService.analyze(
        text: 'Painel elétrico aberto',
        probability: 4,
        severity: 5,
      );
      expect(result.nrs, contains('NR-10'));
      expect(result.priority, 'Crítica');
      expect(
        result.actionPlan.toLowerCase(),
        contains('profissional autorizado'),
      );
      expect(
        result.deadlineSuggestion.toLowerCase(),
        contains('imediato'),
      );
    });
  });
}

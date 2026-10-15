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

    test('botao de emergencia recebe perfil completo de maquina', () {
      final result = OfflineFieldRulesService.analyze(
        text: 'Botão de emergência não funcionou',
        probability: 3,
        severity: 5,
      );
      expect(result.nrs, contains('NR-12'));
      expect(result.category.toLowerCase(), contains('emergência'));
      expect(result.riskSummary.toLowerCase(), contains('parada'));
      expect(result.consequenceSummary.toLowerCase(), contains('acidente'));
      expect(result.evidenceSuggestion.toLowerCase(), contains('teste'));
      expect(result.nrDetails.join(' '), contains('NR-12'));
      expect(result.suggestedSeverity, 5);
    });

    test('sugere valores iniciais coerentes para temas criticos', () {
      expect(
        OfflineFieldRulesService.suggestedSeverityForText(
          'Painel elétrico aberto com partes acessíveis',
        ),
        5,
      );
      expect(
        OfflineFieldRulesService.suggestedSeverityForText(
          'Andaime sem guarda corpo',
        ),
        5,
      );
      expect(
        OfflineFieldRulesService.suggestedProbabilityForText(
          'Extintor obstruído',
        ),
        inInclusiveRange(1, 5),
      );
    });

    test('cobre NRs frequentes da consultoria sem IA', () {
      final nrs = OfflineFieldRulesService.suggestNrs(
        'Empilhamento manual com postura inadequada, poeira, ruído e sinalização ausente',
      );
      expect(nrs, containsAll(<String>[
        'NR-11',
        'NR-15',
        'NR-17',
        'NR-26',
      ]));
    });
  });
}

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

    test('botao de emergencia prioriza parada de emergencia e nao extintor', () {
      final ranked = OfflineReportInlineSuggestionService.rankForTesting(
        'Botão de emergência não funcionou',
      );
      expect(ranked, isNotEmpty);
      expect(ranked.first.id, 'auditar-botao-emergencia-inoperante');
      expect(
        ranked.take(3).any((item) => item.id.startsWith('auditar-extintor-')),
        isFalse,
      );
    });

    test('botoeira continua reconhecida por conceito de comando', () {
      final ranked = OfflineReportInlineSuggestionService.rankForTesting(
        'botoeira não respondeu ao acionamento',
      );
      expect(ranked, isNotEmpty);
      expect(
        ranked.first.id,
        anyOf('auditar-botoeira-inoperante', 'auditar-botao-emergencia-inoperante'),
      );
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

    test('biblioteca ampliada cobre riscos comuns sem misturar assuntos', () {
      expect(
        OfflineReportInlineSuggestionService.fallbackForTesting.length,
        greaterThanOrEqualTo(80),
      );

      final electric = OfflineReportInlineSuggestionService.rankForTesting(
        'cabo elétrico com emenda danificada',
      );
      expect(electric, isNotEmpty);
      expect(electric.first.id, 'auditar-cabo-eletrico-danificado');
      expect(
        electric.take(3).any((item) => item.id.startsWith('auditar-extintor-')),
        isFalse,
      );

      final scaffold = OfflineReportInlineSuggestionService.rankForTesting(
        'andaime sem ancoragem',
      );
      expect(scaffold, isNotEmpty);
      expect(scaffold.first.id, 'auditar-andaime-sem-ancoragem');

      final chemical = OfflineReportInlineSuggestionService.rankForTesting(
        'produto químico em recipiente sem identificação',
      );
      expect(chemical, isNotEmpty);
      expect(chemical.first.id, 'auditar-quimico-sem-identificacao');
    });

    test('reconhece ergonomia poeira e empilhamento na base offline', () {
      final ergo = OfflineReportInlineSuggestionService.rankForTesting(
        'levantamento manual com postura inadequada',
      );
      expect(ergo, isNotEmpty);
      expect(ergo.first.id, 'auditar-postura-inadequada');

      final dust = OfflineReportInlineSuggestionService.rankForTesting(
        'trabalhador exposto a poeira sem proteção',
      );
      expect(dust, isNotEmpty);
      expect(dust.first.id, 'auditar-poeira-sem-protecao');

      final stack = OfflineReportInlineSuggestionService.rankForTesting(
        'empilhamento de materiais instável',
      );
      expect(stack, isNotEmpty);
      expect(stack.first.id, 'auditar-empilhamento-instavel');
    });
    test('biblioteca premium cobre emergencias maquinas movimentacao e obra', () {
      final exit = OfflineReportInlineSuggestionService.rankForTesting(
        'saída de emergência obstruída',
      );
      expect(exit, isNotEmpty);
      expect(exit.first.id, 'auditar-saida-emergencia-obstruida');

      final grinder = OfflineReportInlineSuggestionService.rankForTesting(
        'esmerilhadeira sem proteção',
      );
      expect(grinder, isNotEmpty);
      expect(grinder.first.id, 'auditar-esmerilhadeira-sem-protecao');

      final forklift = OfflineReportInlineSuggestionService.rankForTesting(
        'empilhadeira operador sem cinto',
      );
      expect(forklift, isNotEmpty);
      expect(forklift.first.id, 'auditar-empilhadeira-sem-cinto');

      final excavation = OfflineReportInlineSuggestionService.rankForTesting(
        'vala sem escoramento',
      );
      expect(excavation, isNotEmpty);
      expect(excavation.first.id, 'auditar-escavacao-sem-escoramento');
    });

    test('biblioteca premium cobre ventilacao iluminacao epi e içamento', () {
      final ventilation = OfflineReportInlineSuggestionService.rankForTesting(
        'ventilação inadequada',
      );
      expect(ventilation, isNotEmpty);
      expect(ventilation.first.id, 'auditar-ventilacao-inadequada');

      final light = OfflineReportInlineSuggestionService.rankForTesting(
        'iluminação insuficiente',
      );
      expect(light, isNotEmpty);
      expect(light.first.id, 'auditar-iluminacao-insuficiente');

      final respirator = OfflineReportInlineSuggestionService.rankForTesting(
        'respirador não utilizado',
      );
      expect(respirator, isNotEmpty);
      expect(respirator.first.id, 'auditar-respirador-nao-utilizado');

      final hook = OfflineReportInlineSuggestionService.rankForTesting(
        'gancho de içamento sem trava',
      );
      expect(hook, isNotEmpty);
      expect(hook.first.id, 'auditar-gancho-sem-trava');
    });

  });
}

import 'package:flutter_test/flutter_test.dart';

import 'package:auditar_sst/widgets/offline_report_inline_suggestions.dart';

void main() {
  group('Triagem segura da biblioteca técnica após versão v329175', () {
    test('descrições claramente conformes não geram NCs por palavra coincidente', () {
      expect(
        OfflineReportInlineSuggestionService.rankForTesting(
          'Correia da prensa com proteção instalada',
        ),
        isEmpty,
      );
      expect(
        OfflineReportInlineSuggestionService.rankForTesting(
          'Botoeira de emergência funcionando normalmente',
        ),
        isEmpty,
      );
    });

    test('consulta offline real também ignora condições conformes', () async {
      final results = await OfflineReportInlineSuggestionService.search(
        query: 'Botoeira de emergência funcionando normalmente',
      );
      expect(results, isEmpty);
    });

    test('máquina com proteção danificada continua sendo um problema', () {
      final results = OfflineReportInlineSuggestionService.rankForTesting(
        'Correia da prensa com proteção danificada',
      );
      expect(results, isNotEmpty);
      expect(
        results.any((item) => item.id.startsWith('auditar-extintor-')),
        isFalse,
      );
    });

    test('proteção ausente continua a gerar sugestões de máquina', () {
      final results = OfflineReportInlineSuggestionService.rankForTesting(
        'Correia da prensa sem proteção',
      );
      expect(results, isNotEmpty);
      expect(
        results.first.id.startsWith('auditar-extintor-'),
        isFalse,
      );
    });
  });
}

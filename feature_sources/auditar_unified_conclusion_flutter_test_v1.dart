import 'package:flutter_test/flutter_test.dart';

import '../lib/services/auditar_unified_conclusion.dart';

void main() {
  test('Conclusão local padrão da Ronda não inventa fatos', () {
    final text = AuditarUnifiedConclusion.fromRound(
      companyName: 'Cerâmica Exemplo',
      findings: 3,
      conformities: 1,
      nonConformities: 2,
      highPriority: 1,
      possibleRecurrences: 1,
    );
    expect(text, contains('2 não conformidade(s)'));
    expect(text, contains('prioridade alta ou crítica'));
    expect(text, contains('revisada pelo técnico'));
    expect(text, isNot(contains('IA')));

    final clean = AuditarUnifiedConclusion.fromRound(
      companyName: 'Exemplo',
      findings: 1,
      conformities: 1,
      nonConformities: 0,
    );
    expect(clean, contains('Não foram registradas'));
    expect(clean, isNot(contains('exigem tratamento')));

    final empty = AuditarUnifiedConclusion.fromRound(
      companyName: 'Exemplo',
      findings: 0,
      conformities: 0,
      nonConformities: 0,
    );
    expect(empty, contains('Não há registros suficientes'));
  });
}

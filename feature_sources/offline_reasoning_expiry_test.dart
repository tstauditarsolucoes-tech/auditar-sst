import 'offline_reasoning_v329175.dart';

void main() {
  void check(bool condition, String message) {
    if (!condition) throw StateError(message);
  }
  for (final query in ['Extintor vencido', 'Extintor com manutenção vencida']) {
    final result = OfflineReasoning.analyze(query);
    check(result.length == 1, 'Expected one expiry assessment: $query');
    check(result.single.rule.id == 'extinguisher-expiry', 'Wrong subject: $query');
    check(result.single.description == query, 'Original facts must be preserved');
    check(result.single.rule.question.contains('Qual prazo'), 'Deadline must be clarified');
  }
  for (final query in [
    'Extintor não está vencido',
    'Extintor não se encontra vencido',
    'Verificar se extintor está vencido',
    'Extintor vencido, já regularizado',
    'Extintor instalado na parede',
    'Botão de colaborador está danificada',
  ]) {
    check(OfflineReasoning.analyze(query).isEmpty, 'Do not invent a fault: $query');
  }
  check(OfflineReasoning.analyze('Botão de emergência não funcionou')
      .any((a) => a.rule.id == 'stop'), 'Emergency stop regression');
  print('OFFLINE_EXPIRY_NEGATION_AND_AMBIGUITY_OK');
}

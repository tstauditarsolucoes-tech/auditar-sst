import 'auditar_unified_conclusion_v1.dart';

void main() {
  final text=AuditarUnifiedConclusion.fromRound(
    companyName:'Cerâmica Exemplo',findings:3,conformities:1,
    nonConformities:2,highPriority:1,possibleRecurrences:1);
  assert(text.contains('2 não conformidade(s)'));
  assert(text.contains('prioridade alta ou crítica'));
  assert(text.contains('revisada pelo técnico'));
  assert(!text.contains('IA'), 'Conclusão local não afirma uso de IA');
  final clean=AuditarUnifiedConclusion.fromRound(
    companyName:'Exemplo',findings:1,conformities:1,nonConformities:0);
  assert(clean.contains('Não foram registradas'));
  assert(!clean.contains('exigem tratamento'));
  final empty=AuditarUnifiedConclusion.fromRound(
    companyName:'Exemplo',findings:0,conformities:0,nonConformities:0);
  assert(empty.contains('Não há registros suficientes'));
  print('AUDITAR_UNIFIED_CONCLUSION_OK');
}

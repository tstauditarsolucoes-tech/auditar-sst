import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/widgets/offline_report_inline_suggestions.dart';

void main() {
  final models = jsonEncode({
    'templates':[
      {
        'id':'deep-nr06-respirador-ajuste',
        'title':'Respirador sem ajuste adequado',
        'description':'Vedação insuficiente na face',
        'risk':'Entrada de contaminantes pela face',
        'recommendation':'Avaliar ajuste e vedação',
        'source':'auditar_seed',
      },
      {
        'id':'auditar-respirador-nao-utilizado',
        'title':'Proteção respiratória não utilizada',
        'description':'Trabalhador sem proteção respiratória prevista',
        'risk':'Inalação de contaminantes',
        'recommendation':'Regularizar uso do respirador',
        'source':'auditar_seed',
      },
    ]
  });
  test('não confundir ausência de uso com ajuste de respirador',(){
    final ranked=OfflineReportInlineSuggestionService.decodeAndRankForTesting(
      models,'respirador não utilizado');
    expect(ranked,isNotEmpty);
    expect(ranked.first.id,'auditar-respirador-nao-utilizado');
    expect(ranked.map((r)=>r.id),isNot(contains('deep-nr06-respirador-ajuste')));
  });
  test('ajuste da máscara continua disponível se descrito',(){
    final ranked=OfflineReportInlineSuggestionService.decodeAndRankForTesting(
      models,'respirador mal ajustado');
    expect(ranked,isNotEmpty);
    expect(ranked.first.id,'deep-nr06-respirador-ajuste');
  });
  test('retorno não declara conformidade sem dados',(){
    final ranked=OfflineReportInlineSuggestionService.decodeAndRankForTesting(
      models,'respirador não utilizado');
    expect(ranked.every((x)=>x.recommendation.isNotEmpty),isTrue);
  });
}

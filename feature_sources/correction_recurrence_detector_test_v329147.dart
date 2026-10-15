import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/correction_recurrence_detector.dart';

void main() {
  Map<String, Object?> nc(String id, String sector, String description) => {
        'id': id,
        'sector_name': sector,
        'description': description,
      };

  test('detecta repetição semelhante no mesmo setor', () {
    final rows = [
      nc('1', 'Forno', 'Extintor encontra-se obstruído por materiais'),
      nc('2', 'Forno', 'Extintor obstruído por caixas e materiais'),
      nc('3', 'Produção', 'Extintor obstruído por materiais'),
    ];
    final groups = CorrectionRecurrenceDetector.detect(rows);
    expect(groups, hasLength(1));
    expect(groups.first.count, 2);
    expect(groups.first.sector, 'Forno');
  });

  test('não mistura problemas diferentes só porque estão no mesmo setor', () {
    final rows = [
      nc('1', 'Produção', 'Extintor obstruído'),
      nc('2', 'Produção', 'Extintor vencido'),
      nc('3', 'Produção', 'Máquina sem proteção fixa'),
    ];
    expect(CorrectionRecurrenceDetector.detect(rows), isEmpty);
  });

  test('similaridade ignora acentos e pequenas palavras de ligação', () {
    expect(
      CorrectionRecurrenceDetector.similarity(
        'Proteção da máquina danificada',
        'Protecao maquina danificada',
      ),
      greaterThanOrEqualTo(0.99),
    );
  });
}

import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/correction_recurrence_detector.dart';

void main() {
  Map<String, Object?> nc(
    String id, String companyId, String worksiteId,
    String sector, String description,
  ) => <String, Object?>{
    'id': id, 'company_id': companyId, 'worksite_id': worksiteId,
    'sector_name': sector, 'description': description,
  };

  test('detecta reincidência plausível sem vincular registros', () {
    final rows = [
      nc('1', 'quality', 'obra-35', 'Fabricação',
        'Correia da prensa sem proteção'),
      nc('2', 'quality', 'obra-35', 'Fabricação',
        'Prensa com correia sem proteção instalada'),
    ];
    final result = CorrectionRecurrenceDetector.detect(
      rows, companyId: 'quality',
    );
    expect(result, hasLength(1));
    expect(result.single.count, 2);
  });

  test('separa empresas, obras e setores', () {
    final rows = [
      nc('1', 'quality', 'obra-35', 'Fabricação', 'Extintor obstruído por caixas'),
      nc('2', 'quality', 'obra-36', 'Fabricação', 'Extintor obstruído por materiais'),
      nc('3', 'outra', 'obra-35', 'Fabricação', 'Extintor obstruído por materiais'),
      nc('4', 'quality', 'obra-35', 'Oficina', 'Extintor obstruído por materiais'),
    ];
    expect(CorrectionRecurrenceDetector.detect(rows, companyId: 'quality'),
      isEmpty);
  });

  test('não confunde irregularidade com condição regularizada', () {
    final rows = [
      nc('1','quality','obra-35','Máquinas','Correia da prensa sem proteção'),
      nc('2','quality','obra-35','Máquinas','Correia da prensa com proteção instalada'),
    ];
    expect(CorrectionRecurrenceDetector.detect(rows,companyId:'quality'),
      isEmpty);
  });

  test('não mistura botão de emergência e extintor', () {
    final rows = [
      nc('1','quality','obra-35','Máquinas','Botão de emergência não funcionou'),
      nc('2','quality','obra-35','Máquinas','Extintor não funcionou'),
    ];
    expect(CorrectionRecurrenceDetector.detect(rows,companyId:'quality'),
      isEmpty);
  });

  test('não cruza obra informada com obra sem vínculo', () {
    final rows = [
      nc('1','quality','','Produção','Extintor obstruído por caixas'),
      nc('2','quality','obra-35','Produção','Extintor obstruído por materiais'),
    ];
    expect(CorrectionRecurrenceDetector.detect(rows,companyId:'quality'),
      isEmpty);
  });

  test('conserva comparação para registros legados sem obra', () {
    final rows = [
      nc('1','quality','','Forno','Extintor obstruído por caixas'),
      nc('2','quality','','Forno','Extintor obstruído por materiais'),
    ];
    expect(CorrectionRecurrenceDetector.detect(rows, companyId: 'quality'),
      hasLength(1));
  });
}

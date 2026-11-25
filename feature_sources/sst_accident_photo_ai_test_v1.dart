import 'package:flutter_test/flutter_test.dart';
import '../lib/screens/sst_accident_photo_ai.dart';

void main() {
  test('sem leitura visual nao ha sugestao aplicavel', () {
    final s = SstAccidentPhotoAiSuggestion.fromResult({
      'description': '',
      'recommendation': 'Implantar guarda-corpo',
    });
    expect(s.hasVisual, isFalse);
  });

  test('evidencia visual e indico nao comprovam a causa do acidente', () {
    final s = SstAccidentPhotoAiSuggestion.fromResult({
      'description': 'Abertura aparente no piso',
      'possibleConsequence': 'Queda em nivel diferente',
      'recommendation': 'Isolar e adequar a abertura',
    });
    expect(s.hasVisual, isTrue);
    expect(s.forEvidence(2), contains('NAO CONFIRMADO'));
    expect(s.forEvidence(2), contains('2'));
    expect(s.forConditions(), contains('A fotografia nao comprova'));
    expect(s.forActions(), contains('NAO EXECUTADA'));
    expect(s.forActions(), contains('Definir responsavel'));
  });

  test('texto de resposta malformada e limitado, nunca vira fato', () {
    final s = SstAccidentPhotoAiSuggestion.fromResult({
      'description': List<String>.filled(3000, 'x').join(),
      'possibleConsequence': 123,
      'recommendation': null,
    });
    expect(s.visual.length, 550);
    expect(s.possibleRisk, isEmpty);
    expect(s.proposedAction, isEmpty);
  });

  test('na falta da descricao usa titulo apenas como observacao', () {
    final s = SstAccidentPhotoAiSuggestion.fromResult({
      'title': 'Visao parcial de uma escada',
      'description': null,
    });
    expect(s.visual, 'Visao parcial de uma escada');
    expect(s.hasVisual, isTrue);
  });
}

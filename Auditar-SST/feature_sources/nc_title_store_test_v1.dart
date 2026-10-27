import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/nc_title_store.dart';

void main() {
  test('Nome escolhido não altera código e descrição originais', () {
    final row = <String, Object?>{
      'id': 'id1', 'code': 'NC-FA32',
      'description': 'Proteção removida na transmissão.',
    };
    expect(NcTitleStore.displayTitle(row, {'id1': 'Proteção removida'}),
        'Proteção removida');
    expect(row['code'], 'NC-FA32');
    expect(row['description'], 'Proteção removida na transmissão.');
  });
  test('Sem nome manual usa primeira frase da descrição', () {
    final row = <String, Object?>{
      'id': 'id2', 'code': 'NC-A75',
      'description': 'Extintor vencido. Providenciar substituição.',
    };
    expect(NcTitleStore.displayTitle(row, {}), 'Extintor vencido');
  });
  test('Sem descrição usa item verificado em vez de código', () {
    final row = <String, Object?>{
      'id': 'id3', 'code': 'ABC', 'question_text': 'Proteção da máquina',
    };
    expect(NcTitleStore.displayTitle(row, {}), 'Proteção da máquina');
  });
}

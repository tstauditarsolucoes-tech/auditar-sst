import 'package:flutter_test/flutter_test.dart';
import '../lib/services/worker_import_service.dart';

void main() {
  test('PDF por colunas sem data ou setor tem importacao local revisavel', () {
    const extracted = '''
FUNÇÃO
PRODUÇÃO DE MUDAS
E SEMENTES
AJUDANTE DE
CARVOARIA
CARBONIZADOR
NOME
CARLOS DA SILVA
EMPRESA AGROFLORESTAL
ANA DE SOUZA
BRUNO DOS SANTOS
''';
    final rows =
        WorkerImportService.parseSimpleSeparatedRhColumnsForTesting(extracted);
    expect(rows, isNotNull);
    expect(rows!.length, 4);
    expect(rows[0], ['Nome', 'Cargo', 'Setor']);
    expect(rows[1], ['ANA DE SOUZA', 'PRODUÇÃO DE MUDAS E SEMENTES', '']);
    expect(rows[2], ['BRUNO DOS SANTOS', 'AJUDANTE DE CARVOARIA', '']);
    expect(rows[3], ['CARLOS DA SILVA', 'CARBONIZADOR', '']);
  });

  test('quantidades divergentes de nomes e funcoes nao sao importadas', () {
    const extracted = '''
FUNÇÃO
AJUDANTE DE
CARVOARIA
CARBONIZADOR
NOME
ANA DE SOUZA
''';
    expect(
      WorkerImportService.parseSimpleSeparatedRhColumnsForTesting(extracted),
      isNull,
    );
  });

  test('relatorio com admissao e lotacao mantem parser anterior', () {
    const extracted = '''
Nome Admissão Função Lotação
ANA DE SOUZA 01/02/2026 CARBONIZADOR 001.01 - CARVOARIA
BRUNO DOS SANTOS 02/02/2026 AUXILIAR 001.02 - PRODUÇÃO
''';
    final rows=WorkerImportService.parseExtractedRhTextForTesting(extracted);
    expect(rows, isNotNull);
    expect(rows!.length, 3);
  });
}

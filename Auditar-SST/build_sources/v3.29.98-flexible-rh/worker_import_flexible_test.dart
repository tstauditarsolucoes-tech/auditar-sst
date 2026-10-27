import 'package:flutter_test/flutter_test.dart';
import '../lib/services/worker_import_service.dart';

void main() {
  test('tabela com colunas fora de ordem e duas paginas', () {
    const text = '''
Departamento | Ocupação | Funcionário
Produção | Ceramista | Maria de Souza
Forno | Operador de Forno | João da Silva
Página 2
Departamento | Ocupação | Funcionário
Expedição | Auxiliar | Ana dos Santos
''';
    final rows = WorkerImportService.parseFlexibleEmployeeTextForTesting(text);
    expect(rows, isNotNull);
    expect(rows!.length, 4);
    expect(rows[0], ['Nome', 'Cargo', 'Setor', 'CPF']);
    expect(rows[1], ['Maria de Souza', 'Ceramista', 'Produção', '']);
    expect(rows[3], ['Ana dos Santos', 'Auxiliar', 'Expedição', '']);
  });

  test('lista com campos Nome Cargo Setor em linhas independentes', () {
    const text = '''
Colaborador: Ana de Souza
Função: Soldadora
Lotação: Manutenção
Nome: Pedro Alves | Cargo: Motorista | Setor: Logística
''';
    final rows = WorkerImportService.parseFlexibleEmployeeTextForTesting(text);
    expect(rows, isNotNull);
    expect(rows!.length, 3);
    expect(rows[1], ['Ana de Souza', 'Soldadora', 'Manutenção', '']);
    expect(rows[2], ['Pedro Alves', 'Motorista', 'Logística', '']);
  });

  test('lista de nomes sem cargo exige complemento na previa', () {
    const text = '''
NOME
Ana de Souza
Pedro Alves
''';
    final rows = WorkerImportService.parseFlexibleEmployeeTextForTesting(text);
    expect(rows, isNotNull);
    expect(rows![1], ['Ana de Souza', '', '', '']);
  });

  test('colunas separadas por ponto e virgula sem setor', () {
    const text = '''
FUNÇÃO;NOME
Auxiliar;Ana de Souza
Operador;Pedro Alves
''';
    final rows = WorkerImportService.parseFlexibleEmployeeTextForTesting(text);
    expect(rows, isNotNull);
    expect(rows![1], ['Ana de Souza', 'Auxiliar', '', '']);
  });

  test('nao aceita lista incompleta com total declarado diferente', () {
    const text = '''
Nome | Cargo
Ana de Souza | Auxiliar
Pedro Alves | Operador
Total: 3 trabalhadores
''';
    expect(WorkerImportService.parseFlexibleEmployeeTextForTesting(text), isNull);
  });

  test('nao interpreta cabecalho isolado como lista', () {
    expect(WorkerImportService.parseFlexibleEmployeeTextForTesting(
        'Nome: Empresa Auditar\\nResponsável técnico: Luan Sena'), isNull);
  });
}

#!/usr/bin/env python3
from pathlib import Path
import base64
import io
import re
import sys
import tarfile

root = Path(sys.argv[1])
pubp = root / 'pubspec.yaml'
trainp = root / 'lib/screens/trainings_screen.dart'
bundle = Path('build_sources/v3.29.73-training-import/training_import_sources.tar.xz.b64')

if not bundle.exists():
    raise RuntimeError('Pacote do importador de treinamentos não encontrado.')

pub = pubp.read_text(encoding='utf-8')
train = trainp.read_text(encoding='utf-8')

# ---------------------------------------------------------------------------
# Versão. XLSX usa o pacote archive já existente no app.
# ---------------------------------------------------------------------------
pub, n = re.subn(
    r'^version:\s*[^\n]+',
    'version: 3.29.73+215',
    pub,
    count=1,
    flags=re.M,
)
if n != 1:
    raise RuntimeError('Versão do app não localizada.')


# ---------------------------------------------------------------------------
# Extrai somente os 3 arquivos novos do recurso.
# ---------------------------------------------------------------------------
raw = base64.b64decode(bundle.read_text(encoding='utf-8').strip())
with tarfile.open(fileobj=io.BytesIO(raw), mode='r:xz') as archive:
    allowed = {
        'lib/services/training_import_service.dart',
        'lib/screens/training_import_screen.dart',
        'test/training_import_service_test.dart',
    }
    members = []
    for member in archive.getmembers():
        name = member.name.lstrip('./')
        if name in allowed:
            member.name = name
            members.append(member)
    found = {m.name for m in members}
    if found != allowed:
        raise RuntimeError('Pacote do importador incompleto: ' + repr(sorted(found)))
    archive.extractall(root, members=members)

# ---------------------------------------------------------------------------
# Leitor XLSX local sem dependência nova. Reaproveita package:archive já
# usado pelo app, evitando conflito de versões e mantendo o APK leve.
# ---------------------------------------------------------------------------
servicep = root / 'lib/services/training_import_service.dart'
service_text = servicep.read_text(encoding='utf-8')
service_text = service_text.replace(
    "import 'package:excel/excel.dart';\n",
    "import 'package:archive/archive.dart';\n",
    1,
)

xlsx_start = service_text.find('  static _ParsedDocument _parseXlsx(')
xlsx_end = service_text.find('  static _ParsedDocument _parseCsv(', xlsx_start)
if xlsx_start < 0 or xlsx_end < 0:
    raise RuntimeError('Bloco _parseXlsx não localizado.')

xlsx_impl = r'''  static _ParsedDocument _parseXlsx(Uint8List bytes, List<Worker> workers) {
    try {
      final archive = ZipDecoder().decodeBytes(bytes, verify: true);
      String? sharedXml;
      final sheets = <String>[];
      for (final file in archive.files) {
        final name = file.name.replaceAll('\\', '/');
        if (!file.isFile) continue;
        if (name == 'xl/sharedStrings.xml') {
          sharedXml = utf8.decode(file.content as List<int>, allowMalformed: true);
        } else if (RegExp(r'^xl/worksheets/sheet\\d+\\.xmlif "import 'training_import_screen.dart';" not in train:
    marker = "import 'training_records_screen.dart';\n"
    if marker not in train:
        raise RuntimeError('Import de training_records_screen não localizado.')
    train = train.replace(
        marker,
        marker + "import 'training_import_screen.dart';\n",
        1,
    )

if "title: 'Importar lista'" not in train:
    marker = """                _trainingActionCard(
                  icon: Icons.photo_library_outlined,
                  title: 'Fotos e fichas',
"""
    card = """                _trainingActionCard(
                  icon: Icons.upload_file_outlined,
                  title: 'Importar lista',
                  subtitle: 'PDF ou planilha com IA',
                  color: AuditarBrand.navy,
                  onTap: () async {
                    final currentCompany = _currentCompany;
                    final companyId = widget.companyId;
                    if (companyId == null || currentCompany == null) return;
                    final changed = await Navigator.of(context).push<bool>(
                      MaterialPageRoute(
                        builder: (_) => TrainingImportScreen(
                          companyId: companyId,
                          companyName: currentCompany.name,
                        ),
                      ),
                    );
                    if (changed == true) {
                      await _load();
                    }
                  },
                ),
"""
    if marker not in train:
        raise RuntimeError('Card Fotos e fichas não localizado.')
    train = train.replace(marker, card + marker, 1)

pubp.write_text(pub, encoding='utf-8', newline='\n')
trainp.write_text(train, encoding='utf-8', newline='\n')

# Garantias básicas
service = (root / 'lib/services/training_import_service.dart').read_text(encoding='utf-8')
screen = (root / 'lib/screens/training_import_screen.dart').read_text(encoding='utf-8')
test = (root / 'test/training_import_service_test.dart').read_text(encoding='utf-8')

assert 'version: 3.29.73+215' in pub
assert "title: 'Importar lista'" in train
assert 'TrainingImportScreen(' in train
assert "allowedExtensions: const ['pdf', 'xlsx', 'csv']" in service
assert "package:archive/archive.dart" in service
assert "'mode': 'employee_pdf_import'" in service
assert 'upsertTrainingControlsBatch' in service
assert 'Não localizado nesta empresa' in screen
assert 'parser local identifica treinamento' in test
print('TRAINING_BULK_IMPORT_OK v3.29.73+215')
).hasMatch(name)) {
          sheets.add(utf8.decode(file.content as List<int>, allowMalformed: true));
        }
      }
      if (sheets.isEmpty) {
        throw const TrainingImportException(
          'A planilha XLSX não possui uma aba legível.',
        );
      }
      final shared = _xlsxSharedStrings(sharedXml ?? '');
      final tables = sheets
          .map((xml) => _xlsxSheetRows(xml, shared))
          .where(
            (rows) => rows.any(
              (row) => row.any((cell) => cell.trim().isNotEmpty),
            ),
          )
          .toList();
      if (tables.isEmpty) {
        throw const TrainingImportException('A planilha está vazia.');
      }
      tables.sort((a, b) => b.length.compareTo(a.length));
      final table = tables.first;
      final fullText = table
          .map(
            (row) => row.where((cell) => cell.trim().isNotEmpty).join(' | '),
          )
          .join('\\n');
      return _parseTable(table, workers, fullText);
    } on TrainingImportException {
      rethrow;
    } catch (error) {
      throw TrainingImportException(
        'Não foi possível ler a planilha XLSX: $error',
      );
    }
  }

  static List<String> _xlsxSharedStrings(String xml) {
    if (xml.trim().isEmpty) return const [];
    final result = <String>[];
    final itemExpression = RegExp(r'<si(?:\\s[^>]*)?>([\\s\\S]*?)</si>');
    final textExpression = RegExp(r'<t(?:\\s[^>]*)?>([\\s\\S]*?)</t>');
    for (final item in itemExpression.allMatches(xml)) {
      final inner = item.group(1) ?? '';
      final pieces = textExpression
          .allMatches(inner)
          .map((match) => _xmlUnescape(match.group(1) ?? ''))
          .toList();
      result.add(pieces.join().trim());
    }
    return result;
  }

  static List<List<String>> _xlsxSheetRows(
    String xml,
    List<String> shared,
  ) {
    final rows = <List<String>>[];
    final rowExpression = RegExp(r'<row(?:\\s[^>]*)?>([\\s\\S]*?)</row>');
    final cellExpression = RegExp(r'<c\\s+([^>]*)>([\\s\\S]*?)</c>');
    for (final rowMatch in rowExpression.allMatches(xml)) {
      final inner = rowMatch.group(1) ?? '';
      final values = <int, String>{};
      var maxColumn = -1;
      for (final cellMatch in cellExpression.allMatches(inner)) {
        final attributes = cellMatch.group(1) ?? '';
        final body = cellMatch.group(2) ?? '';
        final reference = RegExp(
          r'\\br="([A-Z]+)\\d+"',
        ).firstMatch(attributes)?.group(1);
        final column =
            reference == null ? maxColumn + 1 : _xlsxColumnIndex(reference);
        if (column < 0) continue;
        maxColumn = column > maxColumn ? column : maxColumn;
        final type = RegExp(
              r'\\bt="([^"]+)"',
            ).firstMatch(attributes)?.group(1) ??
            '';
        String value = '';
        if (type == 'inlineStr') {
          final texts = RegExp(r'<t(?:\\s[^>]*)?>([\\s\\S]*?)</t>')
              .allMatches(body)
              .map((match) => _xmlUnescape(match.group(1) ?? ''))
              .toList();
          value = texts.join();
        } else {
          final raw = RegExp(
                    r'<v(?:\\s[^>]*)?>([\\s\\S]*?)</v>',
                  ).firstMatch(body)?.group(1) ??
              '';
          if (type == 's') {
            final index = int.tryParse(raw.trim());
            value = index != null && index >= 0 && index < shared.length
                ? shared[index]
                : '';
          } else if (type == 'str') {
            value = _xmlUnescape(raw);
          } else {
            value = raw.trim();
          }
        }
        values[column] = value.trim();
      }
      if (maxColumn < 0) continue;
      final row = List<String>.filled(maxColumn + 1, '');
      values.forEach((index, value) => row[index] = value);
      rows.add(row);
    }
    return rows;
  }

  static int _xlsxColumnIndex(String letters) {
    var value = 0;
    for (final unit in letters.codeUnits) {
      if (unit < 65 || unit > 90) return -1;
      value = value * 26 + (unit - 64);
    }
    return value - 1;
  }

  static String _xmlUnescape(String value) => value
      .replaceAll('&lt;', '<')
      .replaceAll('&gt;', '>')
      .replaceAll('&quot;', '"')
      .replaceAll('&apos;', "'")
      .replaceAll('&amp;', '&');

'''
service_text = service_text[:xlsx_start] + xlsx_impl + service_text[xlsx_end:]
servicep.write_text(service_text, encoding='utf-8', newline='\n')

# ---------------------------------------------------------------------------
# Entrada dentro de cada empresa em Treinamentos.
# ---------------------------------------------------------------------------
if "import 'training_import_screen.dart';" not in train:
    marker = "import 'training_records_screen.dart';\n"
    if marker not in train:
        raise RuntimeError('Import de training_records_screen não localizado.')
    train = train.replace(
        marker,
        marker + "import 'training_import_screen.dart';\n",
        1,
    )

if "title: 'Importar lista'" not in train:
    marker = """                _trainingActionCard(
                  icon: Icons.photo_library_outlined,
                  title: 'Fotos e fichas',
"""
    card = """                _trainingActionCard(
                  icon: Icons.upload_file_outlined,
                  title: 'Importar lista',
                  subtitle: 'PDF ou planilha com IA',
                  color: AuditarBrand.navy,
                  onTap: () async {
                    final currentCompany = _currentCompany;
                    final companyId = widget.companyId;
                    if (companyId == null || currentCompany == null) return;
                    final changed = await Navigator.of(context).push<bool>(
                      MaterialPageRoute(
                        builder: (_) => TrainingImportScreen(
                          companyId: companyId,
                          companyName: currentCompany.name,
                        ),
                      ),
                    );
                    if (changed == true) {
                      await _load();
                    }
                  },
                ),
"""
    if marker not in train:
        raise RuntimeError('Card Fotos e fichas não localizado.')
    train = train.replace(marker, card + marker, 1)

pubp.write_text(pub, encoding='utf-8', newline='\n')
trainp.write_text(train, encoding='utf-8', newline='\n')

# Garantias básicas
service = (root / 'lib/services/training_import_service.dart').read_text(encoding='utf-8')
screen = (root / 'lib/screens/training_import_screen.dart').read_text(encoding='utf-8')
test = (root / 'test/training_import_service_test.dart').read_text(encoding='utf-8')

assert 'version: 3.29.73+215' in pub
assert "title: 'Importar lista'" in train
assert 'TrainingImportScreen(' in train
assert "allowedExtensions: const ['pdf', 'xlsx', 'csv']" in service
assert "'mode': 'employee_pdf_import'" in service
assert 'upsertTrainingControlsBatch' in service
assert 'Não localizado nesta empresa' in screen
assert 'parser local identifica treinamento' in test
print('TRAINING_BULK_IMPORT_OK v3.29.73+215')

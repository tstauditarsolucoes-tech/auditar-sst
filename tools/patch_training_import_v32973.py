#!/usr/bin/env python3
from pathlib import Path
import base64
import lzma
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/Auditar_SST_v1_5_dashboard')
repo_root = Path(__file__).resolve().parents[1]

pubp = root / 'pubspec.yaml'
screenp = root / 'lib/screens/trainings_screen.dart'
servicep = root / 'lib/services/training_import_service.dart'
importscreenp = root / 'lib/screens/training_import_screen.dart'

pub = pubp.read_text(encoding='utf-8')
screen = screenp.read_text(encoding='utf-8')

def once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Marcador ausente: {label}')
    return text.replace(old, new, 1)

# Version
pub, count = re.subn(
    r'^version:\s*[^\n]+',
    'version: 3.29.73+215',
    pub,
    count=1,
    flags=re.M,
)
if count != 1:
    raise RuntimeError('Versão não localizada no pubspec.')

# Dependencies used only by the on-demand importer.
if '  excel: ^4.0.6\n' not in pub:
    pub = once(
        pub,
        '  read_pdf_text: ^0.3.1\n',
        '  read_pdf_text: ^0.3.1\n'
        '  excel: ^4.0.6\n'
        '  google_mlkit_text_recognition: ^0.15.0\n',
        'dependências do importador',
    )

# Decode source files.
sources = {
    servicep: repo_root / 'build_sources/v3.29.73-training-import/training_import_service.dart.xz.b64',
    importscreenp: repo_root / 'build_sources/v3.29.73-training-import/training_import_screen.dart.xz.b64',
}
for target, encoded in sources.items():
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = lzma.decompress(base64.b64decode(encoded.read_text(encoding='utf-8').strip()))
    target.write_bytes(raw)

# Integrate with company-specific Trainings screen.
if "import 'training_import_screen.dart';" not in screen:
    screen = once(
        screen,
        "import 'training_records_screen.dart';\n",
        "import 'training_records_screen.dart';\nimport 'training_import_screen.dart';\n",
        'import da tela de importação',
    )

method_marker = """  Future<void> _openRequirements() async {
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => TrainingRequirementsScreen(companyId: widget.companyId),
      ),
    );
    await _load();
  }

"""
method_new = method_marker + """  Future<void> _openTrainingImport() async {
    final companyId = widget.companyId;
    if (companyId == null || companyId.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Abra Treinamentos dentro de uma empresa para importar uma listagem.'),
        ),
      );
      return;
    }
    final changed = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (_) => TrainingImportScreen(companyId: companyId),
      ),
    );
    if (changed == true) {
      await _load();
    }
  }

"""
if 'Future<void> _openTrainingImport() async' not in screen:
    screen = once(screen, method_marker, method_new, 'método abrir importador')

card_marker = """                _trainingActionCard(
                  icon: Icons.photo_library_outlined,
                  title: 'Fotos e fichas',
"""
card_new = """                _trainingActionCard(
                  icon: Icons.document_scanner_outlined,
                  title: 'Importar lista',
                  subtitle: 'PDF, planilha ou foto',
                  color: const Color(0xFF2563EB),
                  onTap: _openTrainingImport,
                ),
                _trainingActionCard(
                  icon: Icons.photo_library_outlined,
                  title: 'Fotos e fichas',
"""
screen = once(screen, card_marker, card_new, 'card Importar lista')

pubp.write_text(pub, encoding='utf-8', newline='\n')
screenp.write_text(screen, encoding='utf-8', newline='\n')

assert 'version: 3.29.73+215' in pub
assert 'excel: ^4.0.6' in pub
assert 'google_mlkit_text_recognition: ^0.15.0' in pub
assert "import 'training_import_screen.dart';" in screen
assert "title: 'Importar lista'" in screen
assert "subtitle: 'PDF, planilha ou foto'" in screen
assert 'Future<void> _openTrainingImport() async' in screen
assert 'Tirar foto da lista' in importscreenp.read_text(encoding='utf-8')
assert 'Selecionar planilha' in importscreenp.read_text(encoding='utf-8')
assert 'pickMultiImage' in importscreenp.read_text(encoding='utf-8')
assert 'TextRecognizer' in servicep.read_text(encoding='utf-8')
assert 'getWorkers(' in servicep.read_text(encoding='utf-8')
assert 'companyId: companyId' in servicep.read_text(encoding='utf-8')
print('v3.29.73+215: importação em lote por empresa com PDF, XLSX/CSV e foto aplicada.')

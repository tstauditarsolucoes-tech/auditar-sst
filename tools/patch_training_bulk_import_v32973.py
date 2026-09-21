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
# Versão e dependência XLSX.
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

if '  excel: ^4.0.6\n' not in pub:
    marker = '  crypto: ^3.0.6\n'
    if marker not in pub:
        raise RuntimeError('Ponto para dependência excel não localizado.')
    pub = pub.replace(marker, marker + '  excel: ^4.0.6\n', 1)

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
assert 'excel: ^4.0.6' in pub
assert "title: 'Importar lista'" in train
assert 'TrainingImportScreen(' in train
assert "allowedExtensions: const ['pdf', 'xlsx', 'csv']" in service
assert "'mode': 'employee_pdf_import'" in service
assert 'upsertTrainingControlsBatch' in service
assert 'Não localizado nesta empresa' in screen
assert 'parser local identifica treinamento' in test
print('TRAINING_BULK_IMPORT_OK v3.29.73+215')

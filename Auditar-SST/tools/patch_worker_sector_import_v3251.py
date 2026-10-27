#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')


def read(rel):
    return (root / rel).read_text(encoding='utf-8')


def write(rel, text):
    (root / rel).write_text(text, encoding='utf-8')


def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Marcador não encontrado: {label}')
    return text.replace(old, new, 1)

pub = read('pubspec.yaml')
pub = re.sub(r'^version:\s*\d+\.\d+\.\d+\+\d+\s*$', 'version: 3.25.1+121', pub, flags=re.M)
write('pubspec.yaml', pub)

svc = read('lib/services/worker_import_service.dart')
svc = replace_once(
    svc,
    """class WorkerImportCandidate {\n  final Worker worker;\n  final bool isNew;\n  final int sourceLine;\n\n  const WorkerImportCandidate({\n    required this.worker,\n    required this.isNew,\n    required this.sourceLine,\n  });\n}\n""",
    """class WorkerImportCandidate {\n  final Worker worker;\n  final bool isNew;\n  final int sourceLine;\n  final String sourceSectorName;\n\n  const WorkerImportCandidate({\n    required this.worker,\n    required this.isNew,\n    required this.sourceLine,\n    required this.sourceSectorName,\n  });\n}\n""",
    'sector name on import candidate',
)
svc = replace_once(
    svc,
    """        WorkerImportCandidate(\n          worker: worker,\n          isNew: matched == null,\n          sourceLine: rowIndex + 1,\n        ),\n""",
    """        WorkerImportCandidate(\n          worker: worker,\n          isNew: matched == null,\n          sourceLine: rowIndex + 1,\n          sourceSectorName: sectorName,\n        ),\n""",
    'candidate source sector',
)
insert_before = """  static _HeaderMap? _findHeader(List<List<String>> table) {\n"""
helper = r'''  static Future<List<Worker>> workersForSave({
    required String companyId,
    required WorkerImportPreview preview,
  }) async {
    final db = AppDatabase.instance;
    final sectors = await db.getSectors(companyId, onlyActive: false);
    final sectorByName = <String, Sector>{
      for (final sector in sectors) _normalize(sector.name): sector,
    };

    for (final rawName in preview.unknownSectors) {
      final name = rawName.trim();
      if (name.isEmpty) continue;
      final key = _normalize(name);
      if (sectorByName.containsKey(key)) continue;
      final sector = Sector(
        id: const Uuid().v4(),
        companyId: companyId,
        name: name,
        description: 'Cadastrado automaticamente pela importação da lista do RH.',
      );
      await db.insertSector(sector);
      sectorByName[key] = sector;
    }

    return preview.candidates.map((candidate) {
      final original = candidate.worker;
      final sourceSector = candidate.sourceSectorName.trim();
      final importedSector = sourceSector.isEmpty
          ? null
          : sectorByName[_normalize(sourceSector)];
      return Worker(
        id: original.id,
        companyId: original.companyId,
        sectorId: importedSector?.id ?? original.sectorId,
        name: original.name,
        cpf: original.cpf,
        role: original.role,
        admissionDate: original.admissionDate,
        lastMedicalExamDate: original.lastMedicalExamDate,
        nextMedicalExamDate: original.nextMedicalExamDate,
        asoPath: original.asoPath,
        active: original.active,
      );
    }).toList();
  }

'''
if 'static Future<List<Worker>> workersForSave' not in svc:
    svc = replace_once(svc, insert_before, helper + insert_before, 'workersForSave helper')
write('lib/services/worker_import_service.dart', svc)

screen = read('lib/screens/workers_screen.dart')
screen = screen.replace(
    'Selecione o PDF atualizado com Nome e Cargo. O documento será lido pela IA gratuita do Gemini.',
    'Selecione o PDF atualizado com Nome, Cargo e, quando houver, Setor. O documento será lido pela IA gratuita do Gemini.',
)
screen = replace_once(
    screen,
    """      await AppDatabase.instance.upsertWorkersFromImport(\n        companyId: companyId,\n        workers: preview.candidates.map((row) => row.worker).toList(),\n        deactivateMissing: deactivateMissing,\n      );\n""",
    """      final workersToSave = await WorkerImportService.workersForSave(\n        companyId: companyId,\n        preview: preview,\n      );\n      await AppDatabase.instance.upsertWorkersFromImport(\n        companyId: companyId,\n        workers: workersToSave,\n        deactivateMissing: deactivateMissing,\n      );\n""",
    'save sectors from RH import',
)
screen = replace_once(
    screen,
    """                      'Setores não encontrados no app: ${preview.unknownSectors.join(', ')}. O trabalhador será mantido sem alterar o setor.',\n""",
    """                      'Setores novos identificados no PDF: ${preview.unknownSectors.join(', ')}. Eles serão cadastrados automaticamente ao confirmar a atualização.',\n""",
    'unknown sector message',
)
screen = replace_once(
    screen,
    """                        (row) => Text(\n                          '• ${row.worker.name} — ${row.worker.role} '\n                          '${row.isNew ? '(novo)' : '(atualizar)'}',\n                        ),\n""",
    """                        (row) {\n                          final sector = row.sourceSectorName.trim();\n                          return Text(\n                            '• ${row.worker.name} — ${row.worker.role}'\n                            '${sector.isEmpty ? '' : ' — $sector'} '\n                            '${row.isNew ? '(novo)' : '(atualizar)'}',\n                          );\n                        },\n""",
    'preview with sector',
)
screen = screen.replace(
    'Importe um PDF com Nome e Cargo para incluir, atualizar e retirar funcionários da lista ativa.',
    'Importe um PDF com Nome, Cargo e Setor (quando disponível) para incluir, atualizar e retirar funcionários da lista ativa.',
)
write('lib/screens/workers_screen.dart', screen)

code = read('painel_web_google_apps_script/Code.gs')
code = replace_once(
    code,
    """      'Para cada pessoa, informe nome completo, cargo ou função e setor quando estiver claramente indicado.',\n      'Transcreva o nome e o cargo exatamente como aparecem no documento, sem resumir, corrigir ou trocar a nomenclatura.',\n""",
    """      'Para cada pessoa, informe nome completo, cargo ou função e setor quando estiver claramente indicado.',\n      'Considere como setor também colunas ou campos equivalentes como Departamento, Área, Lotação, Unidade, Unidade/Setor e Centro de Trabalho.',\n      'Se o setor aparecer como título de um bloco, associe-o somente às pessoas daquele bloco. Não copie setor de outro grupo.',\n      'Quando o documento não informar o setor daquela pessoa, retorne sector como texto vazio.',\n      'Transcreva nome, cargo e setor exatamente como aparecem no documento, sem resumir, corrigir ou trocar a nomenclatura.',\n""",
    'employee import sector prompt',
)
write('painel_web_google_apps_script/Code.gs', code)

print('v3.25.1: importação do RH com Nome + Cargo + Setor aplicada.')

#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')

pub = root / 'pubspec.yaml'
text = pub.read_text(encoding='utf-8')
text = re.sub(r'^version:\s*\d+\.\d+\.\d+\+\d+\s*$', 'version: 3.24.4+104', text, flags=re.M)
pub.write_text(text, encoding='utf-8')

main_path = root / 'lib/main.dart'
main = main_path.read_text(encoding='utf-8')

if "package:path/path.dart" not in main:
    main = main.replace("import 'package:flutter/material.dart';\n", "import 'package:flutter/material.dart';\nimport 'package:path/path.dart' as p;\nimport 'package:path_provider/path_provider.dart';\n", 1)
elif "package:path_provider/path_provider.dart" not in main:
    main = main.replace("import 'package:path/path.dart' as p;\n", "import 'package:path/path.dart' as p;\nimport 'package:path_provider/path_provider.dart';\n", 1)

old_block = '''  if (Platform.isWindows) {\n    sqfliteFfiInit();\n    databaseFactory = databaseFactoryFfi;\n\n    // No primeiro acesso do Windows, a pasta padrão do SQLite pode ainda\n    // não existir. Criá-la antes de autenticar evita o erro SQLite 14\n    // (unable to open database file) ao abrir/migrar o banco do usuário.\n    final dbPath = await getDatabasesPath();\n    await Directory(dbPath).create(recursive: true);\n  }\n'''
new_block = '''  if (Platform.isWindows) {\n    sqfliteFfiInit();\n    databaseFactory = databaseFactoryFfi;\n    await _prepareWindowsDatabasePath();\n  }\n'''
if old_block not in main and new_block not in main:
    raise RuntimeError('Bloco de inicialização Windows não encontrado.')
main = main.replace(old_block, new_block, 1)

helper = r'''Future<void> _prepareWindowsDatabasePath() async {
  // O caminho padrão do sqflite_common_ffi pode apontar para a pasta do
  // executável. Quando o app está instalado em Arquivos de Programas essa
  // pasta não é gravável por um usuário comum e o SQLite retorna erro 14.
  final legacyPath = await getDatabasesPath();

  Directory support;
  try {
    support = await getApplicationSupportDirectory();
  } catch (_) {
    final localAppData = Platform.environment['LOCALAPPDATA'] ??
        Platform.environment['APPDATA'];
    if (localAppData == null || localAppData.trim().isEmpty) {
      rethrow;
    }
    support = Directory(p.join(localAppData, 'Auditar SST'));
  }

  final databaseDirectory = Directory(p.join(support.path, 'database'));
  await databaseDirectory.create(recursive: true);

  final targetPath = p.normalize(databaseDirectory.path);
  final oldPath = p.normalize(legacyPath);

  // Preserva bancos de versões anteriores/portáteis quando existirem.
  if (oldPath.toLowerCase() != targetPath.toLowerCase()) {
    try {
      final oldDirectory = Directory(oldPath);
      if (await oldDirectory.exists()) {
        await for (final entity in oldDirectory.list(followLinks: false)) {
          if (entity is! File) continue;
          final name = p.basename(entity.path);
          if (!name.toLowerCase().startsWith('auditar_sst')) continue;
          final destination = File(p.join(targetPath, name));
          if (!await destination.exists()) {
            try {
              await entity.copy(destination.path);
            } catch (_) {}
          }
        }
      }
    } catch (_) {}
  }

  await databaseFactory.setDatabasesPath(targetPath);
}

'''
if 'Future<void> _prepareWindowsDatabasePath() async' not in main:
    marker = 'Future<void> main() async {'
    if marker not in main:
        raise RuntimeError('Função main não encontrada.')
    main = main.replace(marker, helper + marker, 1)

main_path.write_text(main, encoding='utf-8')

home_path = root / 'lib/screens/home_screen.dart'
home = home_path.read_text(encoding='utf-8')
home = home.replace('Auditar SST • versão 3.21.3', 'Auditar SST • versão 3.24.4')
home = home.replace('Auditar SST para Windows • versão 3.21.3', 'Auditar SST para Windows • versão 3.24.4')
home = home.replace("'Todos os módulos'", "'Demais módulos'")
home = home.replace("'As funções voltaram a ficar visíveis, sem menus escondidos'", "'Acesse os demais recursos do sistema'")
home_path.write_text(home, encoding='utf-8')

note = root / 'MUDANCAS_V3_24_4_WINDOWS_SQLITE.txt'
note.write_text(
    'Auditar SST v3.24.4\n\n'
    '- Corrige SQLite error 14 no Windows instalado em Arquivos de Programas.\n'
    '- Banco passa a usar pasta gravável de suporte do usuário.\n'
    '- Tenta migrar bancos antigos/portáteis sem sobrescrever arquivos existentes.\n'
    '- Corrige textos e número da versão exibidos na tela inicial.\n',
    encoding='utf-8',
)

print('v3.24.4: caminho seguro do SQLite no Windows aplicado.')

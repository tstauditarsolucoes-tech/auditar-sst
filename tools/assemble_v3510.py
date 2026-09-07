#!/usr/bin/env python3
from __future__ import annotations
import re, subprocess, sys
from pathlib import Path


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f'Trecho esperado não encontrado: {label}')
    return text.replace(old, new, 1)


def main():
    repo = Path(__file__).resolve().parent.parent
    subprocess.run([sys.executable, str(repo/'tools'/'assemble_v3500.py')], cwd=repo, check=True)
    app = repo/'app'/'Auditar_SST_v1_5_dashboard'

    pub = app/'pubspec.yaml'
    t = pub.read_text(encoding='utf-8')
    t = replace_once(t, 'version: 3.35.0+153', 'version: 3.35.1+154', 'versão')
    pub.write_text(t, encoding='utf-8')

    startup = app/'lib'/'services'/'startup_service.dart'
    startup.write_text(r'''import 'dart:io';

import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

/// Inicialização segura da camada local no Windows.
///
/// É executada depois que a primeira janela do Flutter já foi criada. Assim,
/// qualquer problema de pasta, permissão ou banco não faz o processo morrer
/// silenciosamente antes de mostrar a interface.
class StartupService {
  StartupService._();

  static Future<void> preparePlatform() async {
    if (!Platform.isWindows) return;

    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;

    final legacyPath = await getDatabasesPath();
    final localAppData = (Platform.environment['LOCALAPPDATA'] ??
            Platform.environment['APPDATA'] ??
            '')
        .trim();

    if (localAppData.isEmpty) {
      await Directory(legacyPath).create(recursive: true);
      return;
    }

    final targetDirectory = Directory(
      p.join(localAppData, 'Auditar SST', 'database'),
    );
    await targetDirectory.create(recursive: true);

    final oldPath = p.normalize(legacyPath);
    final targetPath = p.normalize(targetDirectory.path);

    // Copia bancos legados apenas quando ainda não existe cópia no destino.
    // Nada é apagado nem movido.
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
}
''', encoding='utf-8')

    mainp = app/'lib'/'main.dart'
    main_text = mainp.read_text(encoding='utf-8')
    main_text = re.sub(
      r"import 'dart:io';\n\nimport 'package:flutter/material.dart';\nimport 'package:path/path.dart' as p;\nimport 'package:path_provider/path_provider.dart';\nimport 'package:sqflite/sqflite.dart';\nimport 'package:sqflite_common_ffi/sqflite_ffi.dart';\n\nimport 'brand.dart';\nimport 'screens/splash_screen.dart';\nimport 'services/auth_service.dart';\nimport 'services/sync_coordinator.dart';",
      "import 'package:flutter/material.dart';\n\nimport 'brand.dart';\nimport 'screens/splash_screen.dart';\nimport 'services/sync_coordinator.dart';",
      main_text,
      count=1,
    )
    start = main_text.find('Future<void> _prepareWindowsDatabasePath() async {')
    end = main_text.find('class AuditarSstApp', start)
    if start < 0 or end < 0:
        raise RuntimeError('Bloco de startup antigo não encontrado')
    safe_main = """void main() {\n  WidgetsFlutterBinding.ensureInitialized();\n  // A janela é criada imediatamente. Inicialização de banco e sessão ocorre\n  // na SplashScreen, já com interface visível e tratamento de erro.\n  runApp(const AuditarSstApp());\n}\n\n"""
    main_text = main_text[:start] + safe_main + main_text[end:]
    mainp.write_text(main_text, encoding='utf-8')

    authp = app/'lib'/'services'/'auth_service.dart'
    auth = authp.read_text(encoding='utf-8')
    old_auth_file = """  static Future<File> _authFile() async {\n    final root = await getApplicationSupportDirectory();\n    await root.create(recursive: true);\n    return File(p.join(root.path, _authFileName));\n  }\n\n  static Future<void> initialize() async {\n    final file = await _authFile();\n    if (!await file.exists()) return;\n    try {\n"""
    new_auth_file = """  static Future<File> _authFile() async {\n    Directory root;\n    if (Platform.isWindows) {\n      final localAppData = (Platform.environment['LOCALAPPDATA'] ??\n              Platform.environment['APPDATA'] ??\n              '')\n          .trim();\n      if (localAppData.isNotEmpty) {\n        root = Directory(p.join(localAppData, 'Auditar SST'));\n      } else {\n        root = await getApplicationSupportDirectory();\n      }\n    } else {\n      root = await getApplicationSupportDirectory();\n    }\n    await root.create(recursive: true);\n    return File(p.join(root.path, _authFileName));\n  }\n\n  static Future<void> initialize() async {\n    try {\n      final file = await _authFile();\n      if (!await file.exists()) return;\n"""
    auth = replace_once(auth, old_auth_file, new_auth_file, 'auth seguro')
    authp.write_text(auth, encoding='utf-8')

    splashp = app/'lib'/'screens'/'splash_screen.dart'
    splash = splashp.read_text(encoding='utf-8')
    splash = replace_once(
      splash,
      "import '../services/auth_service.dart';\n",
      "import '../services/auth_service.dart';\nimport '../services/startup_service.dart';\n",
      'import startup',
    )
    old_init = """  @override\n  void initState() {\n    super.initState();\n\n    Timer(const Duration(milliseconds: 1100), () {\n      if (!mounted) return;\n      Navigator.of(context).pushReplacement(\n        MaterialPageRoute(\n          builder: (_) => AuthService.isSignedIn\n              ? const HomeScreen()\n              : const LoginScreen(),\n        ),\n      );\n    });\n  }\n"""
    new_init = """  String startupMessage = '';\n\n  @override\n  void initState() {\n    super.initState();\n    WidgetsBinding.instance.addPostFrameCallback((_) => _initializeAndOpen());\n  }\n\n  Future<void> _initializeAndOpen() async {\n    final startedAt = DateTime.now();\n    var sessionReady = false;\n\n    try {\n      await StartupService.preparePlatform();\n      await AuthService.initialize();\n      if (AuthService.isSignedIn) {\n        try {\n          await AuthService.activateSavedSession();\n          sessionReady = true;\n        } catch (e) {\n          startupMessage =\n              'Não foi possível abrir a sessão salva. Entre novamente. Seus dados locais não foram apagados.';\n        }\n      }\n    } catch (e) {\n      startupMessage =\n          'O Windows bloqueou parte da inicialização. O aplicativo foi aberto em modo de recuperação.';\n    }\n\n    final elapsed = DateTime.now().difference(startedAt);\n    const minimumSplash = Duration(milliseconds: 900);\n    if (elapsed < minimumSplash) {\n      await Future.delayed(minimumSplash - elapsed);\n    }\n    if (!mounted) return;\n\n    Navigator.of(context).pushReplacement(\n      MaterialPageRoute(\n        builder: (_) => sessionReady\n            ? const HomeScreen()\n            : LoginScreen(initialMessage: startupMessage),\n      ),\n    );\n  }\n"""
    splash = replace_once(splash, old_init, new_init, 'bootstrap splash')
    splashp.write_text(splash, encoding='utf-8')

    loginp = app/'lib'/'screens'/'login_screen.dart'
    login = loginp.read_text(encoding='utf-8')
    login = replace_once(
      login,
      "class LoginScreen extends StatefulWidget {\n  const LoginScreen({super.key});",
      "class LoginScreen extends StatefulWidget {\n  final String initialMessage;\n\n  const LoginScreen({super.key, this.initialMessage = ''});",
      'LoginScreen mensagem',
    )
    marker = "class _LoginScreenState extends State<LoginScreen> {\n"
    replacement = "class _LoginScreenState extends State<LoginScreen> {\n  @override\n  void initState() {\n    super.initState();\n    error = widget.initialMessage;\n  }\n\n"
    login = replace_once(login, marker, replacement, 'init login')
    loginp.write_text(login, encoding='utf-8')

    assert 'version: 3.35.1+154' in pub.read_text(encoding='utf-8')
    m = mainp.read_text(encoding='utf-8')
    assert 'void main()' in m and 'runApp(const AuditarSstApp());' in m
    assert 'AuthService.initialize' not in m
    s = splashp.read_text(encoding='utf-8')
    assert 'StartupService.preparePlatform()' in s
    assert 'AuthService.activateSavedSession()' in s
    a = authp.read_text(encoding='utf-8')
    assert "Platform.environment['LOCALAPPDATA']" in a
    assert (app/'lib'/'ready_checklists.dart').read_text(encoding='utf-8').count('  ReadyChecklistDefinition(') == 44
    assert "'syncProtocol': 2" in (app/'lib'/'services'/'device_sync_service.dart').read_text(encoding='utf-8')
    print(f'Fonte v3.35.1 montada em {app}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

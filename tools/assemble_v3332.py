#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Trecho esperado não encontrado: {label}')
    return text.replace(old, new, 1)


def sub_once(text: str, pattern: str, repl: str, label: str) -> str:
    updated, count = re.subn(pattern, repl, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f'Trecho esperado não encontrado: {label}')
    return updated


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'assemble_v3331.py')],
        cwd=repo,
        check=True,
    )

    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'

    pubspec_path = app / 'pubspec.yaml'
    pubspec = pubspec_path.read_text(encoding='utf-8')
    pubspec = replace_once(
        pubspec,
        'version: 3.33.1+150',
        'version: 3.33.2+151',
        'versão pubspec',
    )
    pubspec_path.write_text(pubspec, encoding='utf-8')

    home_path = app / 'lib' / 'screens' / 'home_screen.dart'
    home = home_path.read_text(encoding='utf-8')
    home = sub_once(
        home,
        r"_deviceSyncSubscription\s*=\s*DeviceSyncService\.events\.listen\(\(result\)\s*\{\s*if\s*\(mounted\s*&&\s*result\.received\s*>\s*0\)\s*_refresh\(\);\s*\}\);",
        "_deviceSyncSubscription = DeviceSyncService.events.listen((result) {\n      if (mounted && result.received > 0) {\n        unawaited(_refresh(showLoading: false));\n      }\n    });",
        'evento de sincronização da home',
    )
    home = replace_once(
        home,
        'Future<void> _refresh() async {',
        'Future<void> _refresh({bool showLoading = true}) async {',
        'assinatura do refresh da home',
    )
    home = sub_once(
        home,
        r"Future<void> _refresh\(\{bool showLoading = true\}\) async \{\s*if \(mounted\)\s*setState\(\(\) \{\s*loading = true;\s*loadError = '';\s*\}\);",
        "Future<void> _refresh({bool showLoading = true}) async {\n    if (showLoading && mounted) {\n      setState(() {\n        loading = true;\n        loadError = '';\n      });\n    }",
        'loading silencioso da home',
    )
    home = sub_once(
        home,
        r"\} catch \(e\) \{\s*if \(!mounted\) return;\s*setState\(\(\) \{\s*loading = false;\s*loadError = '\$e'\.replaceFirst\('Bad state: ', ''\)\.trim\(\);\s*\}\);\s*\}",
        "} catch (e) {\n      if (!mounted) return;\n      if (showLoading) {\n        setState(() {\n          loading = false;\n          loadError = '$e'.replaceFirst('Bad state: ', '').trim();\n        });\n      }\n    }",
        'erro silencioso da home',
    )
    open_start = home.find('Future<void> _open(Widget page) async {')
    open_end = home.find('Future<void> _showModules()', open_start)
    if open_start < 0 or open_end < 0:
        raise RuntimeError('Bloco _open da home não localizado.')
    open_block = home[open_start:open_end]
    open_block = replace_once(
        open_block,
        'await _refresh();',
        'await _refresh(showLoading: false);',
        'refresh após navegação',
    )
    home = home[:open_start] + open_block + home[open_end:]
    home = replace_once(
        home,
        'onPressed: _refresh,',
        'onPressed: () => _refresh(showLoading: false),',
        'botão atualizar da home',
    )
    home_path.write_text(home, encoding='utf-8')

    sync_path = app / 'lib' / 'services' / 'sync_coordinator.dart'
    sync = sync_path.read_text(encoding='utf-8')
    sync = replace_once(
        sync,
        "  _SyncTone _statusTone = _SyncTone.neutral;",
        "  _SyncTone _statusTone = _SyncTone.neutral;\n  final ValueNotifier<int> _indicatorRevision = ValueNotifier<int>(0);",
        'notifier do indicador',
    )
    sync = replace_once(
        sync,
        "    _indicatorTimer?.cancel();\n    super.dispose();",
        "    _indicatorTimer?.cancel();\n    _indicatorRevision.dispose();\n    super.dispose();",
        'dispose do notifier',
    )

    status_start = sync.find('  void _setDesktopStatus(')
    status_end = sync.find('  void _handleConnectivity', status_start)
    if status_start < 0 or status_end < 0:
        raise RuntimeError('Bloco de status da sincronização não localizado.')
    status_block = """  void _setDesktopStatus({required String label, required _SyncTone tone}) {
    if (!Platform.isWindows || !mounted) return;

    _indicatorTimer?.cancel();
    _statusLabel = label;
    _statusTone = tone;
    _showIndicator = tone != _SyncTone.neutral;
    _indicatorRevision.value += 1;

    if (tone == _SyncTone.ok) {
      _indicatorTimer = Timer(const Duration(seconds: 3), () {
        if (!mounted || _statusTone != _SyncTone.ok) return;
        _showIndicator = false;
        _indicatorRevision.value += 1;
      });
    }
  }

"""
    sync = sync[:status_start] + status_block + sync[status_end:]

    build_start = sync.find('  @override\n  Widget build(BuildContext context) {')
    build_end = sync.find('\n}\n\nenum _SyncTone', build_start)
    if build_start < 0 or build_end < 0:
        raise RuntimeError('Build do coordenador de sincronização não localizado.')
    build_block = """  @override
  Widget build(BuildContext context) {
    // A estrutura do app permanece fixa durante a sincronização. Somente o
    // pequeno indicador é redesenhado, evitando reconstruir a tela inteira.
    return Stack(
      fit: StackFit.expand,
      children: [
        RepaintBoundary(child: widget.child),
        if (Platform.isWindows)
          Positioned(
            right: 18,
            bottom: 16,
            child: IgnorePointer(
              child: ValueListenableBuilder<int>(
                valueListenable: _indicatorRevision,
                builder: (context, _, __) {
                  return AnimatedOpacity(
                    opacity: _showIndicator ? 1 : 0,
                    duration: const Duration(milliseconds: 160),
                    child: _SyncIndicator(
                      label: _statusLabel,
                      tone: _statusTone,
                    ),
                  );
                },
              ),
            ),
          ),
      ],
    );
  }
"""
    sync = sync[:build_start] + build_block + sync[build_end:]
    sync_path.write_text(sync, encoding='utf-8')

    if 'version: 3.33.2+151' not in pubspec_path.read_text(encoding='utf-8'):
        raise RuntimeError('A versão v3.33.2+151 não foi aplicada.')

    final_home = home_path.read_text(encoding='utf-8')
    for marker in (
        '_refresh(showLoading: false)',
        'unawaited(_refresh(showLoading: false))',
        'if (showLoading && mounted)',
    ):
        if marker not in final_home:
            raise RuntimeError(f'Atualização silenciosa ausente: {marker}')

    final_sync = sync_path.read_text(encoding='utf-8')
    for marker in (
        'ValueNotifier<int> _indicatorRevision',
        'ValueListenableBuilder<int>',
        'StackFit.expand',
        'RepaintBoundary(child: widget.child)',
    ):
        if marker not in final_sync:
            raise RuntimeError(f'Proteção visual da sincronização ausente: {marker}')

    status_start = final_sync.find('void _setDesktopStatus')
    status_end = final_sync.find('void _handleConnectivity', status_start)
    if 'setState' in final_sync[status_start:status_end]:
        raise RuntimeError('O status da sincronização ainda reconstrói a tela inteira.')

    if "'syncProtocol': 2" not in (app / 'lib' / 'services' / 'device_sync_service.dart').read_text(encoding='utf-8'):
        raise RuntimeError('Sincronização bidirecional v3.33.0 foi perdida.')

    print(f'Fonte v3.33.2 montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

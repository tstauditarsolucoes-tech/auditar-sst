#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print('uso: patch_ai_transport_v32911.py <raiz-do-app>', file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    service = root / 'lib/services/ai_assistant_service.dart'
    pubspec = root / 'pubspec.yaml'
    if not service.exists() or not pubspec.exists():
        raise RuntimeError(f'raiz inválida: {root}')

    text = service.read_text(encoding='utf-8')
    old = "const transientHttp = <int>{408, 500, 502, 503, 504};\n    const maxAttempts = 2;"
    new = "const transientHttp = <int>{404, 408, 429, 500, 502, 503, 504};\n    const maxAttempts = 3;"
    if old not in text:
        raise RuntimeError('bloco de retry da v3.29.10 não encontrado')
    text = text.replace(old, new, 1)

    old_msg = "message: transientHttp.contains(response.statusCode)\n                ? 'A Central Online ficou temporariamente indisponível. Tente novamente em alguns instantes.'\n                : 'O serviço respondeu com erro ${response.statusCode}.',"
    new_msg = "message: transientHttp.contains(response.statusCode)\n                ? 'A Central Online ficou temporariamente indisponível após novas tentativas. O relatório não foi alterado; tente novamente em alguns instantes.'\n                : 'O serviço respondeu com erro ${response.statusCode}.',"
    if old_msg not in text:
        raise RuntimeError('mensagem HTTP da v3.29.10 não encontrada')
    text = text.replace(old_msg, new_msg, 1)
    service.write_text(text, encoding='utf-8')

    pub = pubspec.read_text(encoding='utf-8')
    if 'version: 3.29.10+153' not in pub:
        raise RuntimeError('versão-base 3.29.10+153 não encontrada')
    pubspec.write_text(pub.replace('version: 3.29.10+153', 'version: 3.29.11+154', 1), encoding='utf-8')

    home = root / 'lib/screens/home_screen.dart'
    if home.exists():
        home_text = home.read_text(encoding='utf-8')
        if '3.29.10' in home_text:
            home.write_text(home_text.replace('3.29.10', '3.29.11'), encoding='utf-8')

    final = service.read_text(encoding='utf-8')
    for marker in (
        'const transientHttp = <int>{404, 408, 429, 500, 502, 503, 504};',
        'const maxAttempts = 3;',
        "'mode': 'report_review_chat'",
    ):
        if marker not in final:
            raise RuntimeError(f'v3.29.11 incompleta: {marker}')

    print('v3.29.11: retry ampliado para respostas 404/429 e falhas temporárias da Central Online')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

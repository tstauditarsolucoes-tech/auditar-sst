#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print('uso: patch_ai_performance_v32913.py <raiz-do-app>', file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    service = root / 'lib/services/ai_assistant_service.dart'
    http_file = root / 'lib/services/apps_script_http.dart'
    pubspec = root / 'pubspec.yaml'
    if not service.exists() or not http_file.exists() or not pubspec.exists():
        raise RuntimeError(f'raiz inválida: {root}')

    text = service.read_text(encoding='utf-8')

    old = """    const transientHttp = <int>{404, 408, 429, 500, 502, 503, 504};
    const maxAttempts = 4;

    for (var attempt = 0; attempt < maxAttempts; attempt++) {"""
    new = """    final aiMode = '${payload['mode'] ?? ''}';
    final requestTimeout =
        aiMode == 'checklist_photo' || aiMode == 'safety_observation_photo'
            ? const Duration(seconds: 55)
            : aiMode == 'report_review_chat'
                ? const Duration(seconds: 75)
                : const Duration(seconds: 65);
    const transientHttp = <int>{404, 408, 429, 500, 502, 503, 504};
    const maxAttempts = 2;

    for (var attempt = 0; attempt < maxAttempts; attempt++) {"""
    if old not in text:
        raise RuntimeError('bloco principal de retry v3.29.12 não encontrado')
    text = text.replace(old, new, 1)

    old = "timeout: const Duration(seconds: 120),"
    if old not in text:
        raise RuntimeError('timeout de 120s não encontrado')
    text = text.replace(old, 'timeout: requestTimeout,', 1)

    old = """      } on TimeoutException {
        if (attempt + 1 < maxAttempts) {
          await Future<void>.delayed(const Duration(milliseconds: 900));
          continue;
        }
        return const AiAssistantReply(
          success: false,
          message:
              'A Central Online demorou mais que o esperado para responder. O relatório não foi alterado. Tente novamente em alguns instantes.',
        );
"""
    new = """      } on TimeoutException {
        return const AiAssistantReply(
          success: false,
          message:
              'A IA demorou mais que o limite desta análise. O carregamento foi encerrado para não deixar o app preso. Tente novamente em alguns instantes.',
        );
"""
    if old not in text:
        raise RuntimeError('bloco TimeoutException v3.29.12 não encontrado')
    text = text.replace(old, new, 1)

    # Reduz o peso de upload das fotos sem perder resolução operacional.
    text = text.replace('prepared.width > 1280 || prepared.height > 1280',
                        'prepared.width > 1024 || prepared.height > 1024', 1)
    text = text.replace('img.copyResize(prepared, width: 1280)',
                        'img.copyResize(prepared, width: 1024)', 1)
    text = text.replace('img.copyResize(prepared, height: 1280)',
                        'img.copyResize(prepared, height: 1024)', 1)
    text = text.replace('img.encodeJpg(sanitized, quality: 72)',
                        'img.encodeJpg(sanitized, quality: 68)', 1)

    service.write_text(text, encoding='utf-8')

    http_text = http_file.read_text(encoding='utf-8')
    old_http = "final response = await http.Response.fromStream(streamed);"
    new_http = "final response = await http.Response.fromStream(streamed).timeout(timeout);"
    if old_http not in http_text:
        raise RuntimeError('leitura do corpo HTTP sem timeout não encontrada')
    http_text = http_text.replace(old_http, new_http, 1)
    http_file.write_text(http_text, encoding='utf-8')

    pub = pubspec.read_text(encoding='utf-8')
    if 'version: 3.29.12+155' not in pub:
        raise RuntimeError('versão-base 3.29.12+155 não encontrada')
    pubspec.write_text(
        pub.replace('version: 3.29.12+155', 'version: 3.29.13+156', 1),
        encoding='utf-8',
    )

    home = root / 'lib/screens/home_screen.dart'
    if home.exists():
        home_text = home.read_text(encoding='utf-8')
        if '3.29.12' in home_text:
            home.write_text(home_text.replace('3.29.12', '3.29.13'), encoding='utf-8')

    final = service.read_text(encoding='utf-8')
    final_http = http_file.read_text(encoding='utf-8')
    for marker in (
        'const maxAttempts = 2;',
        "const Duration(seconds: 55)",
        "const Duration(seconds: 75)",
        'timeout: requestTimeout,',
        'width: 1024',
        'quality: 68',
        'O carregamento foi encerrado para não deixar o app preso.',
    ):
        if marker not in final:
            raise RuntimeError(f'v3.29.13 incompleta em ai_assistant_service: {marker}')
    if 'http.Response.fromStream(streamed).timeout(timeout)' not in final_http:
        raise RuntimeError('timeout do corpo HTTP não aplicado')

    print('v3.29.13: IA com timeout total, menos retry e fotos menores para reduzir espera')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

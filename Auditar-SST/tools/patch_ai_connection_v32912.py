#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print('uso: patch_ai_connection_v32912.py <raiz-do-app>', file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    service = root / 'lib/services/ai_assistant_service.dart'
    pubspec = root / 'pubspec.yaml'
    if not service.exists() or not pubspec.exists():
        raise RuntimeError(f'raiz inválida: {root}')

    text = service.read_text(encoding='utf-8')

    old_attempts = 'const maxAttempts = 3;'
    if old_attempts not in text:
        raise RuntimeError('maxAttempts da v3.29.11 não encontrado')
    text = text.replace(old_attempts, 'const maxAttempts = 4;', 1)

    old_socket = """      } on SocketException {
        return const AiAssistantReply(
          success: false,
          message:
              'A IA precisa de internet. A vistoria continua funcionando offline.',
        );
      } on TimeoutException {"""
    new_socket = """      } on SocketException {
        if (attempt + 1 < maxAttempts) {
          await Future<void>.delayed(
            Duration(milliseconds: 700 + (attempt * 500)),
          );
          continue;
        }
        return const AiAssistantReply(
          success: false,
          message:
              'A conexão com a Central Online foi interrompida durante a consulta à IA. A vistoria não foi alterada. Verifique a internet e tente novamente.',
        );
      } on TimeoutException {"""
    if old_socket not in text:
        raise RuntimeError('bloco SocketException da v3.29.11 não encontrado')
    text = text.replace(old_socket, new_socket, 1)

    old_catch = """      } catch (error) {
        return AiAssistantReply(
          success: false,
          message: 'Não foi possível consultar a IA: $error',
        );
      }
"""
    new_catch = """      } catch (error) {
        final message = error.toString().toLowerCase();
        final transientNetworkError =
            message.contains('clientexception') ||
            message.contains('connection reset') ||
            message.contains('connection abort') ||
            message.contains('connection closed') ||
            message.contains('connection terminated') ||
            message.contains('broken pipe') ||
            message.contains('software caused connection abort') ||
            message.contains('connection refused') ||
            message.contains('unexpected eof');

        if (transientNetworkError && attempt + 1 < maxAttempts) {
          await Future<void>.delayed(
            Duration(milliseconds: 700 + (attempt * 500)),
          );
          continue;
        }

        if (transientNetworkError) {
          return const AiAssistantReply(
            success: false,
            message:
                'A conexão com a Central Online foi interrompida pelo Google ou pela rede durante a consulta. A vistoria não foi alterada. Tente novamente em alguns instantes.',
          );
        }

        return AiAssistantReply(
          success: false,
          message: 'Não foi possível consultar a IA: $error',
        );
      }
"""
    if old_catch not in text:
        raise RuntimeError('catch genérico da v3.29.11 não encontrado')
    text = text.replace(old_catch, new_catch, 1)
    service.write_text(text, encoding='utf-8')

    pub = pubspec.read_text(encoding='utf-8')
    if 'version: 3.29.11+154' not in pub:
        raise RuntimeError('versão-base 3.29.11+154 não encontrada')
    pubspec.write_text(
        pub.replace('version: 3.29.11+154', 'version: 3.29.12+155', 1),
        encoding='utf-8',
    )

    home = root / 'lib/screens/home_screen.dart'
    if home.exists():
        home_text = home.read_text(encoding='utf-8')
        if '3.29.11' in home_text:
            home.write_text(home_text.replace('3.29.11', '3.29.12'), encoding='utf-8')

    final = service.read_text(encoding='utf-8')
    for marker in (
        'const maxAttempts = 4;',
        "message.contains('connection reset')",
        "message.contains('software caused connection abort')",
        'A conexão com a Central Online foi interrompida',
        "'mode': 'report_review_chat'",
    ):
        if marker not in final:
            raise RuntimeError(f'hotfix v3.29.12 incompleto: {marker}')

    print('v3.29.12: retry de conexão reset/abort aplicado em todos os modos de IA')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

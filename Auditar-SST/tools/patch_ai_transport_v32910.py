#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print('uso: patch_ai_transport_v32910.py <raiz-do-app>', file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    service = root / 'lib/services/ai_assistant_service.dart'
    pubspec = root / 'pubspec.yaml'
    if not service.exists() or not pubspec.exists():
        raise RuntimeError(f'raiz inválida: {root}')

    text = service.read_text(encoding='utf-8')
    if "import 'dart:async';" not in text:
        text = text.replace("import 'dart:convert';", "import 'dart:async';\nimport 'dart:convert';", 1)

    pattern = re.compile(
        r"  static Future<AiAssistantReply> _send\(\n"
        r"    Map<String, Object\?> payload,\n"
        r"  \) async \{.*?\n"
        r"  \}\n\n"
        r"  static Uint8List _prepareImage",
        re.S,
    )

    replacement = r'''  static Future<AiAssistantReply> _send(
    Map<String, Object?> payload,
  ) async {
    final db = AppDatabase.instance;
    final endpoint = (await db.getSetting(
      'management_panel_endpoint',
      fallback: '',
    ))
        .trim();
    final syncKey = (await db.getSetting(
      'management_panel_sync_key',
      fallback: '',
    ))
        .trim();

    if (endpoint.isEmpty || syncKey.isEmpty) {
      return const AiAssistantReply(
        success: false,
        message:
            'Configure primeiro a publicação web em Configurações. Ela também faz a conexão segura com a IA.',
      );
    }

    final endpointUri = Uri.tryParse(endpoint);
    if (endpointUri == null ||
        endpointUri.scheme != 'https' ||
        endpointUri.host != 'script.google.com' ||
        !endpointUri.path.startsWith('/macros/s/') ||
        !endpointUri.path.endsWith('/exec')) {
      return const AiAssistantReply(
        success: false,
        message:
            'A URL salva não é a publicação permanente do Apps Script. Em Configurações, use o link https://script.google.com/macros/s/.../exec.',
      );
    }

    const transientHttp = <int>{408, 500, 502, 503, 504};
    const maxAttempts = 2;

    for (var attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        final response = await AppsScriptHttp.postJson(
          Uri.parse(endpoint),
          {
            'action': 'ai_assistant',
            'syncKey': syncKey,
            'authToken': AuthService.sessionToken,
            'payload': payload,
          },
          timeout: const Duration(seconds: 120),
        );

        if (transientHttp.contains(response.statusCode) &&
            attempt + 1 < maxAttempts) {
          await Future<void>.delayed(const Duration(milliseconds: 900));
          continue;
        }

        if (response.statusCode < 200 || response.statusCode >= 300) {
          return AiAssistantReply(
            success: false,
            message: transientHttp.contains(response.statusCode)
                ? 'A Central Online ficou temporariamente indisponível. Tente novamente em alguns instantes.'
                : 'O serviço respondeu com erro ${response.statusCode}.',
          );
        }

        final responseText = utf8.decode(
          response.bodyBytes,
          allowMalformed: true,
        );

        dynamic decodedValue;
        try {
          decodedValue = jsonDecode(responseText);
        } on FormatException {
          if (attempt + 1 < maxAttempts) {
            await Future<void>.delayed(const Duration(milliseconds: 900));
            continue;
          }

          final normalized = responseText.trimLeft().toLowerCase();
          final htmlResponse = normalized.startsWith('<!doctype') ||
              normalized.startsWith('<html') ||
              normalized.contains('<body') ||
              normalized.contains('googleusercontent');
          return AiAssistantReply(
            success: false,
            message: htmlResponse
                ? 'A Central Online recebeu uma página temporária do Google em vez da resposta da IA. O relatório não foi alterado. Tente novamente em alguns instantes.'
                : 'A Central Online retornou uma resposta que não pôde ser interpretada. O relatório não foi alterado; tente novamente.',
          );
        }

        if (decodedValue is! Map) {
          if (attempt + 1 < maxAttempts) {
            await Future<void>.delayed(const Duration(milliseconds: 700));
            continue;
          }
          return const AiAssistantReply(
            success: false,
            message:
                'A Central Online retornou uma resposta incompleta. O relatório não foi alterado.',
          );
        }

        final decoded = Map<String, dynamic>.from(decodedValue);
        if (decoded['ok'] != true) {
          return AiAssistantReply(
            success: false,
            message: '${decoded['message'] ?? 'A análise não foi concluída.'}',
          );
        }
        final result = decoded['result'];
        if (result is! Map) {
          return const AiAssistantReply(
            success: false,
            message: 'A IA retornou uma resposta incompleta.',
          );
        }
        return AiAssistantReply(
          success: true,
          message: attempt == 0
              ? 'Sugestão preparada para sua revisão.'
              : 'Sugestão preparada após uma nova tentativa automática.',
          result: Map<String, dynamic>.from(result),
        );
      } on SocketException {
        return const AiAssistantReply(
          success: false,
          message:
              'A IA precisa de internet. A vistoria continua funcionando offline.',
        );
      } on TimeoutException {
        if (attempt + 1 < maxAttempts) {
          await Future<void>.delayed(const Duration(milliseconds: 900));
          continue;
        }
        return const AiAssistantReply(
          success: false,
          message:
              'A Central Online demorou mais que o esperado para responder. O relatório não foi alterado. Tente novamente em alguns instantes.',
        );
      } catch (error) {
        return AiAssistantReply(
          success: false,
          message: 'Não foi possível consultar a IA: $error',
        );
      }
    }

    return const AiAssistantReply(
      success: false,
      message:
          'A IA não respondeu após a nova tentativa automática. Tente novamente em alguns instantes.',
    );
  }

  static Uint8List _prepareImage'''

    text, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise RuntimeError('não foi possível localizar _send em ai_assistant_service.dart')
    service.write_text(text, encoding='utf-8')

    pub = pubspec.read_text(encoding='utf-8')
    if 'version: 3.29.9+152' not in pub:
        raise RuntimeError('versão-base 3.29.9+152 não encontrada')
    pubspec.write_text(pub.replace('version: 3.29.9+152', 'version: 3.29.10+153', 1), encoding='utf-8')

    home = root / 'lib/screens/home_screen.dart'
    if home.exists():
        home_text = home.read_text(encoding='utf-8')
        if '3.29.9' in home_text:
            home.write_text(home_text.replace('3.29.9', '3.29.10'), encoding='utf-8')

    final = service.read_text(encoding='utf-8')
    for marker in (
        'const maxAttempts = 2;',
        'página temporária do Google',
        'Sugestão preparada após uma nova tentativa automática.',
        'on TimeoutException',
        "'mode': 'report_review_chat'",
    ):
        if marker not in final:
            raise RuntimeError(f'hotfix v3.29.10 incompleto: {marker}')

    print('v3.29.10: tolerância a resposta HTML/temporária da Central Online aplicada')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

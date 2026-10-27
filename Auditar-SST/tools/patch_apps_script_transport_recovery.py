#!/usr/bin/env python3
from pathlib import Path
import sys

CONTENT = r'''import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

/// Cliente HTTP resiliente para publicações do Google Apps Script.
///
/// O ContentService normalmente responde ao POST em /exec com um redirecionamento
/// para script.googleusercontent.com. Esse endereço é temporário. Em alguns
/// aparelhos/conexões ele pode abortar durante a troca de host ou devolver 404
/// quando o token temporário expira. A URL permanente /exec continua sendo a
/// fonte de verdade e é usada novamente em uma única recuperação automática.
class AppsScriptHttp {
  static const Set<int> _redirectCodes = {301, 302, 303, 307, 308};
  static const int _maxRedirects = 5;
  static const int _maxRootAttempts = 2;

  // No Windows há várias rotinas que podem atingir o mesmo Apps Script.
  // Mantemos a serialização já adotada para evitar disputa de lock no backend.
  static Future<void> _windowsTail = Future<void>.value();

  static Future<T> _windowsSerial<T>(Future<T> Function() action) async {
    if (!Platform.isWindows) return action();

    final previous = _windowsTail;
    final release = Completer<void>();
    _windowsTail = release.future;
    try {
      try {
        await previous;
      } catch (_) {
        // Uma falha anterior nunca deve travar a fila seguinte.
      }
      return await action();
    } finally {
      if (!release.isCompleted) release.complete();
    }
  }

  static Future<http.Response> postJson(
    Uri endpoint,
    Object? payload, {
    Duration timeout = const Duration(seconds: 30),
  }) {
    return _windowsSerial(() => _postJsonDirect(endpoint, payload, timeout));
  }

  static Future<http.Response> _postJsonDirect(
    Uri endpoint,
    Object? payload,
    Duration timeout,
  ) async {
    final encodedBody = jsonEncode(payload);
    Object? lastTransportError;

    for (var rootAttempt = 0; rootAttempt < _maxRootAttempts; rootAttempt++) {
      var uri = endpoint;
      var method = 'POST';
      var redirectedToTemporaryHost = false;

      try {
        for (var redirectCount = 0;
            redirectCount <= _maxRedirects;
            redirectCount++) {
          // Cliente novo por salto. Isso evita reaproveitar a conexão TLS/TCP do
          // script.google.com ao trocar para script.googleusercontent.com, causa
          // observada de abortos em alguns Android/Windows.
          final client = http.Client();
          http.Response response;
          try {
            final request = http.Request(method, uri)
              ..followRedirects = false
              ..headers['Accept'] = 'application/json'
              ..headers['Cache-Control'] = 'no-cache';

            if (method == 'POST') {
              request.headers['Content-Type'] =
                  'application/json; charset=utf-8';
              request.body = encodedBody;
            }

            final streamed = await client.send(request).timeout(timeout);
            response = await http.Response.fromStream(streamed).timeout(timeout);
          } finally {
            client.close();
          }

          final temporaryHost = _isTemporaryGoogleHost(uri);

          // Um 404 no host temporário não significa que a implantação /exec
          // morreu. Recomeçamos pela URL permanente para obter um redirect novo.
          if (response.statusCode == 404 &&
              temporaryHost &&
              rootAttempt + 1 < _maxRootAttempts) {
            await Future<void>.delayed(const Duration(milliseconds: 250));
            break;
          }

          if (!_redirectCodes.contains(response.statusCode)) {
            return response;
          }

          final location = response.headers['location'];
          if (location == null || location.trim().isEmpty) {
            return response;
          }

          uri = uri.resolve(location);
          redirectedToTemporaryHost =
              redirectedToTemporaryHost || _isTemporaryGoogleHost(uri);

          if (response.statusCode == 301 ||
              response.statusCode == 302 ||
              response.statusCode == 303) {
            // ContentService converte o POST inicial para GET no recurso
            // temporário que contém a resposta JSON.
            method = 'GET';
          }

          if (redirectCount == _maxRedirects) {
            return http.Response(
              'A publicação web excedeu o limite de redirecionamentos.',
              508,
            );
          }
        }
      } on TimeoutException catch (error) {
        lastTransportError = error;
        if (rootAttempt + 1 >= _maxRootAttempts) rethrow;
        await Future<void>.delayed(const Duration(milliseconds: 300));
        continue;
      } on SocketException catch (error) {
        lastTransportError = error;
        if (rootAttempt + 1 >= _maxRootAttempts) rethrow;
        await Future<void>.delayed(const Duration(milliseconds: 300));
        continue;
      } on http.ClientException catch (error) {
        lastTransportError = error;
        if (rootAttempt + 1 >= _maxRootAttempts) rethrow;
        await Future<void>.delayed(const Duration(milliseconds: 300));
        continue;
      }

      // Se o loop foi interrompido por 404 no endereço temporário, tenta
      // novamente a partir do /exec. Fora disso, não mascara respostas reais.
      if (!redirectedToTemporaryHost || rootAttempt + 1 >= _maxRootAttempts) {
        break;
      }
    }

    if (lastTransportError != null) {
      throw lastTransportError;
    }
    return http.Response(
      'Não foi possível concluir a resposta temporária do Google Apps Script.',
      503,
    );
  }

  static bool _isTemporaryGoogleHost(Uri uri) {
    final host = uri.host.toLowerCase();
    return host == 'script.googleusercontent.com' ||
        host.endsWith('.googleusercontent.com');
  }
}
'''


def main() -> int:
    if len(sys.argv) != 2:
        print('uso: patch_apps_script_transport_recovery.py <app_dir>', file=sys.stderr)
        return 2
    app = Path(sys.argv[1])
    target = app / 'lib/services/apps_script_http.dart'
    if not target.exists():
        raise FileNotFoundError(target)
    target.write_text(CONTENT, encoding='utf-8')
    print('Transporte Apps Script resiliente aplicado.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

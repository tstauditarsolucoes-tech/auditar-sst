#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
pubp = root / 'pubspec.yaml'
httpp = root / 'lib/services/apps_script_http.dart'

pub = pubp.read_text(encoding='utf-8')
if 'version: 3.29.42+184' not in pub:
    if 'version: 3.29.41+183' not in pub:
        raise RuntimeError('Base Android v3.29.41+183 não encontrada')
    pub = pub.replace('version: 3.29.41+183', 'version: 3.29.42+184', 1)

content = r'''import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:http/http.dart' as http;
import 'package:http/io_client.dart';

class CentralTransportException implements Exception {
  final String message;
  const CentralTransportException(this.message);

  @override
  String toString() => message;
}

/// Cliente HTTP resiliente para o Google Apps Script.
///
/// O fluxo normal continua usando o DNS do Android. Se o aparelho devolver
/// "Failed host lookup" para os hosts do Apps Script, o cliente resolve o
/// endereço A diretamente por DNS público (1.1.1.1 / 8.8.8.8) e abre a conexão
/// TLS para o IP encontrado preservando o hostname/SNI original. Assim uma
/// falha do DNS privado/roteador não derruba toda a sincronização.
class AppsScriptHttp {
  static const Set<int> _redirectCodes = {301, 302, 303, 307, 308};
  static const int _maxRedirects = 5;
  static const int _maxRootAttempts = 2;

  /// Somente para teste de integração no CI. Em produção permanece false.
  static bool forceDnsFallbackForTesting = false;

  static Future<void> _windowsTail = Future<void>.value();

  static Future<T> _windowsSerial<T>(Future<T> Function() action) async {
    if (!Platform.isWindows) return action();
    final previous = _windowsTail;
    final release = Completer<void>();
    _windowsTail = release.future;
    try {
      try {
        await previous;
      } catch (_) {}
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
    final effectiveTimeout = Platform.isAndroid &&
            timeout.compareTo(const Duration(seconds: 24)) > 0
        ? const Duration(seconds: 24)
        : timeout;
    Object? lastTransportError;

    for (var rootAttempt = 0; rootAttempt < _maxRootAttempts; rootAttempt++) {
      var uri = endpoint;
      var method = 'POST';
      var redirectedToTemporaryHost = false;

      try {
        for (var redirectCount = 0;
            redirectCount <= _maxRedirects;
            redirectCount++) {
          final response = await _sendHopWithDnsFallback(
            method: method,
            uri: uri,
            encodedBody: encodedBody,
            timeout: effectiveTimeout,
          );

          final temporaryHost = _isTemporaryGoogleHost(uri);
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
        if (Platform.isAndroid) {
          throw const CentralTransportException(
            'A Central Online não respondeu a tempo. Seus dados continuam salvos no aparelho. Tente novamente quando a conexão estiver estável.',
          );
        }
        if (rootAttempt + 1 >= _maxRootAttempts) {
          throw const CentralTransportException(
            'A Central Online não respondeu a tempo. Seus dados continuam salvos e poderão ser sincronizados depois.',
          );
        }
        await Future<void>.delayed(const Duration(milliseconds: 300));
        continue;
      } on SocketException catch (error) {
        lastTransportError = error;
        if (_isDnsFailure(error)) {
          throw const CentralTransportException(
            'A Central Online continua inacessível mesmo após a recuperação automática de DNS. Seus dados continuam salvos no aparelho. Tente novamente em alguns instantes.',
          );
        }
        if (rootAttempt + 1 >= _maxRootAttempts) {
          throw const CentralTransportException(
            'A conexão com a Central Online foi interrompida. Seus dados continuam salvos no aparelho e poderão ser sincronizados depois.',
          );
        }
        await Future<void>.delayed(const Duration(milliseconds: 300));
        continue;
      } on http.ClientException catch (error) {
        lastTransportError = error;
        if (_isDnsFailure(error)) {
          throw const CentralTransportException(
            'A Central Online continua inacessível mesmo após a recuperação automática de DNS. Seus dados continuam salvos no aparelho. Tente novamente em alguns instantes.',
          );
        }
        if (rootAttempt + 1 >= _maxRootAttempts) {
          throw const CentralTransportException(
            'Não foi possível concluir a comunicação com a Central Online. Seus dados continuam salvos no aparelho e poderão ser sincronizados depois.',
          );
        }
        await Future<void>.delayed(const Duration(milliseconds: 300));
        continue;
      }

      if (!redirectedToTemporaryHost || rootAttempt + 1 >= _maxRootAttempts) {
        break;
      }
    }

    if (lastTransportError != null) {
      throw const CentralTransportException(
        'Não foi possível concluir a comunicação com a Central Online. Seus dados continuam salvos no aparelho e poderão ser sincronizados depois.',
      );
    }
    return http.Response(
      'Não foi possível concluir a resposta temporária do Google Apps Script.',
      503,
    );
  }

  static Future<http.Response> _sendHopWithDnsFallback({
    required String method,
    required Uri uri,
    required String encodedBody,
    required Duration timeout,
  }) async {
    if (forceDnsFallbackForTesting && _isGoogleScriptHost(uri.host)) {
      final address = await _resolveWithPublicDns(uri.host);
      if (address == null) {
        throw SocketException('DNS fallback sem resposta para ${uri.host}');
      }
      return _sendHop(
        method: method,
        uri: uri,
        encodedBody: encodedBody,
        timeout: timeout,
        addressOverride: address,
      );
    }

    try {
      return await _sendHop(
        method: method,
        uri: uri,
        encodedBody: encodedBody,
        timeout: timeout,
      );
    } on SocketException catch (error) {
      if (!_isDnsFailure(error) || !_isGoogleScriptHost(uri.host)) rethrow;
      final address = await _resolveWithPublicDns(uri.host);
      if (address == null) rethrow;
      return _sendHop(
        method: method,
        uri: uri,
        encodedBody: encodedBody,
        timeout: timeout,
        addressOverride: address,
      );
    } on http.ClientException catch (error) {
      if (!_isDnsFailure(error) || !_isGoogleScriptHost(uri.host)) rethrow;
      final address = await _resolveWithPublicDns(uri.host);
      if (address == null) rethrow;
      return _sendHop(
        method: method,
        uri: uri,
        encodedBody: encodedBody,
        timeout: timeout,
        addressOverride: address,
      );
    }
  }

  static Future<http.Response> _sendHop({
    required String method,
    required Uri uri,
    required String encodedBody,
    required Duration timeout,
    InternetAddress? addressOverride,
  }) async {
    final client = addressOverride == null
        ? http.Client()
        : _clientForResolvedAddress(addressOverride);
    try {
      final request = http.Request(method, uri)
        ..followRedirects = false
        ..persistentConnection = false
        ..headers['Accept'] = 'application/json'
        ..headers['Cache-Control'] = 'no-cache';

      if (method == 'POST') {
        request.headers['Content-Type'] = 'application/json; charset=utf-8';
        request.body = encodedBody;
      }

      final streamed = await client.send(request).timeout(timeout);
      return await http.Response.fromStream(streamed).timeout(timeout);
    } finally {
      client.close();
    }
  }

  static http.Client _clientForResolvedAddress(InternetAddress address) {
    final io = HttpClient()
      ..findProxy = (_) => 'DIRECT'
      ..connectionFactory = (uri, proxyHost, proxyPort) async {
        if (proxyHost != null || proxyPort != null) {
          throw const SocketException('Proxy não suportado no fallback DNS');
        }
        final port = uri.hasPort
            ? uri.port
            : (uri.scheme.toLowerCase() == 'https' ? 443 : 80);
        final task = await Socket.startConnect(address, port);
        if (uri.scheme.toLowerCase() != 'https') {
          return task;
        }
        final secure = task.socket.then<Socket>(
          (socket) => SecureSocket.secure(socket, host: uri.host),
        );
        return ConnectionTask.fromSocket<Socket>(secure, task.cancel);
      };
    return IOClient(io);
  }

  static bool _isDnsFailure(Object error) {
    final text = error.toString().toLowerCase();
    return text.contains('failed host lookup') ||
        text.contains('no address associated with hostname') ||
        text.contains('nodename nor servname provided') ||
        text.contains('name or service not known') ||
        text.contains('temporary failure in name resolution');
  }

  static bool _isGoogleScriptHost(String host) {
    final value = host.toLowerCase();
    return value == 'script.google.com' ||
        value == 'script.googleusercontent.com' ||
        value.endsWith('.googleusercontent.com');
  }

  static Future<InternetAddress?> _resolveWithPublicDns(String host) async {
    for (final resolver in const ['1.1.1.1', '8.8.8.8']) {
      try {
        final address = await _queryDnsA(host, resolver)
            .timeout(const Duration(seconds: 4));
        if (address != null) return address;
      } catch (_) {}
    }
    return null;
  }

  static Future<InternetAddress?> _queryDnsA(
    String host,
    String resolver,
  ) async {
    final socket = await RawDatagramSocket.bind(InternetAddress.anyIPv4, 0);
    final id = DateTime.now().microsecondsSinceEpoch & 0xffff;
    final query = _buildDnsQuery(host, id);
    final completer = Completer<InternetAddress?>();
    late final StreamSubscription<RawSocketEvent> subscription;

    subscription = socket.listen(
      (event) {
        if (event != RawSocketEvent.read) return;
        final packet = socket.receive();
        if (packet == null) return;
        final answer = _parseDnsA(packet.data, id);
        if (!completer.isCompleted) completer.complete(answer);
      },
      onError: (Object error) {
        if (!completer.isCompleted) completer.completeError(error);
      },
    );

    try {
      socket.send(query, InternetAddress(resolver), 53);
      return await completer.future.timeout(const Duration(seconds: 3));
    } finally {
      await subscription.cancel();
      socket.close();
    }
  }

  static Uint8List _buildDnsQuery(String host, int id) {
    final bytes = BytesBuilder(copy: false);
    bytes.add([
      (id >> 8) & 0xff,
      id & 0xff,
      0x01,
      0x00,
      0x00,
      0x01,
      0x00,
      0x00,
      0x00,
      0x00,
      0x00,
      0x00,
    ]);
    for (final label in host.split('.')) {
      final encoded = ascii.encode(label);
      if (encoded.isEmpty || encoded.length > 63) {
        throw const FormatException('Hostname inválido para DNS');
      }
      bytes.addByte(encoded.length);
      bytes.add(encoded);
    }
    bytes.add([0x00, 0x00, 0x01, 0x00, 0x01]);
    return bytes.toBytes();
  }

  static InternetAddress? _parseDnsA(Uint8List data, int expectedId) {
    if (data.length < 12) return null;
    final id = _u16(data, 0);
    if (id != expectedId) return null;
    final flags = _u16(data, 2);
    if ((flags & 0x8000) == 0 || (flags & 0x000f) != 0) return null;

    final questions = _u16(data, 4);
    final answers = _u16(data, 6);
    final authorities = _u16(data, 8);
    final additionals = _u16(data, 10);
    var offset = 12;

    for (var i = 0; i < questions; i++) {
      offset = _skipDnsName(data, offset);
      if (offset < 0 || offset + 4 > data.length) return null;
      offset += 4;
    }

    final records = answers + authorities + additionals;
    for (var i = 0; i < records; i++) {
      offset = _skipDnsName(data, offset);
      if (offset < 0 || offset + 10 > data.length) return null;
      final type = _u16(data, offset);
      final klass = _u16(data, offset + 2);
      final length = _u16(data, offset + 8);
      offset += 10;
      if (offset + length > data.length) return null;
      if (type == 1 && klass == 1 && length == 4) {
        final ip = '${data[offset]}.${data[offset + 1]}.${data[offset + 2]}.${data[offset + 3]}';
        return InternetAddress(ip);
      }
      offset += length;
    }
    return null;
  }

  static int _skipDnsName(Uint8List data, int offset) {
    var cursor = offset;
    var guard = 0;
    while (cursor < data.length && guard++ < 128) {
      final length = data[cursor];
      if (length == 0) return cursor + 1;
      if ((length & 0xc0) == 0xc0) {
        return cursor + 2 <= data.length ? cursor + 2 : -1;
      }
      if ((length & 0xc0) != 0) return -1;
      cursor += 1 + length;
    }
    return -1;
  }

  static int _u16(Uint8List data, int offset) =>
      (data[offset] << 8) | data[offset + 1];

  static bool _isTemporaryGoogleHost(Uri uri) {
    final host = uri.host.toLowerCase();
    return host == 'script.googleusercontent.com' ||
        host.endsWith('.googleusercontent.com');
  }
}
'''

pubp.write_text(pub, encoding='utf-8', newline='\n')
httpp.write_text(content, encoding='utf-8', newline='\n')

assert 'version: 3.29.42+184' in pubp.read_text(encoding='utf-8')
final_http = httpp.read_text(encoding='utf-8')
assert 'forceDnsFallbackForTesting' in final_http
assert "const ['1.1.1.1', '8.8.8.8']" in final_http
assert 'SecureSocket.secure(socket, host: uri.host)' in final_http
assert 'Central Online continua inacessível mesmo após a recuperação automática de DNS' in final_http
print('Android v3.29.42+184: fallback DNS direto + TLS/SNI aplicado sem alterar telas.')

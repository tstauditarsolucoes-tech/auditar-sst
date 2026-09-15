#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
pubp = root / 'pubspec.yaml'
httpp = root / 'lib/services/apps_script_http.dart'

pub = pubp.read_text(encoding='utf-8')
http = httpp.read_text(encoding='utf-8')

if 'version: 3.29.49+191' not in pub:
    if 'version: 3.29.48+190' not in pub:
        raise RuntimeError('Base v3.29.48+190 não encontrada')
    pub = pub.replace('version: 3.29.48+190', 'version: 3.29.49+191', 1)

# O teste no aparelho provou que script.google.com abre no Chrome, e o diagnóstico
# real provou que o POST do Apps Script responde 302 -> script.googleusercontent.com.
# No Android passamos a preferir IPv4 resolvido dinamicamente em cada hop Google,
# preservando TLS/SNI. Isso evita o caminho que estava ficando preso até o timeout
# no runtime Android sem usar IP fixo. Se o caminho direto falhar, tentamos o cliente
# padrão uma vez antes de reportar o host/etapa que falhou.
field_marker = '  static bool forceDnsFallbackForTesting = false;\n'
field_extra = '''  /// Testa no CI o mesmo caminho IPv4 direto preferido pelo Android.\n  static bool forceAndroidDirectForTesting = false;\n'''
if 'forceAndroidDirectForTesting' not in http:
    if field_marker not in http:
        raise RuntimeError('Campo de teste DNS não localizado')
    http = http.replace(field_marker, field_marker + field_extra, 1)

# Limite por hop. O servidor real respondeu entre ~1 e 5 s no diagnóstico; 10 s
# oferece margem sem deixar o usuário esperando 24+ s em cada etapa.
old_timeout = '''    final effectiveTimeout = Platform.isAndroid &&\n            timeout.compareTo(const Duration(seconds: 24)) > 0\n        ? const Duration(seconds: 24)\n        : timeout;\n'''
new_timeout = '''    final effectiveTimeout = (Platform.isAndroid || forceAndroidDirectForTesting)\n        ? const Duration(seconds: 10)\n        : timeout;\n'''
if new_timeout not in http:
    if old_timeout not in http:
        raise RuntimeError('Timeout Android antigo não localizado')
    http = http.replace(old_timeout, new_timeout, 1)

start = http.find('  static Future<http.Response> _sendHopWithDnsFallback({')
end = http.find('  static Future<http.Response> _sendHop({', start)
if start < 0 or end < 0:
    raise RuntimeError('Bloco _sendHopWithDnsFallback não localizado')

new_send = r'''  static Future<http.Response> _sendHopWithDnsFallback({
    required String method,
    required Uri uri,
    required String encodedBody,
    required Duration timeout,
  }) async {
    final androidDirect = Platform.isAndroid || forceAndroidDirectForTesting;

    // No Android, para os dois hosts usados pelo Apps Script, preferimos uma
    // conexão IPv4 resolvida dinamicamente. O hostname original continua sendo
    // usado no TLS/SNI, portanto a validação HTTPS permanece correta.
    if (androidDirect && _isGoogleScriptHost(uri.host)) {
      Object? directError;
      try {
        final address = await _resolvePreferredIpv4(uri.host);
        if (address != null) {
          return await _sendHop(
            method: method,
            uri: uri,
            encodedBody: encodedBody,
            timeout: timeout,
            addressOverride: address,
          );
        }
      } catch (error) {
        directError = error;
      }

      // Segunda e última rota: pilha normal do Android. Isso cobre redes em que
      // VPN/proxy exige a conexão padrão, sem criar ciclo infinito de tentativas.
      try {
        return await _sendHop(
          method: method,
          uri: uri,
          encodedBody: encodedBody,
          timeout: timeout,
        );
      } catch (normalError) {
        final detail = directError == null
            ? normalError.runtimeType.toString()
            : '${directError.runtimeType}/${normalError.runtimeType}';
        throw CentralTransportException(
          'Não foi possível concluir a comunicação com ${uri.host} ($detail). Seus dados continuam salvos no aparelho.',
        );
      }
    }

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

  static Future<InternetAddress?> _resolvePreferredIpv4(String host) async {
    try {
      final addresses = await InternetAddress.lookup(
        host,
        type: InternetAddressType.IPv4,
      ).timeout(const Duration(seconds: 3));
      if (addresses.isNotEmpty) return addresses.first;
    } catch (_) {}
    // Fallback dinâmico somente se o resolvedor do Android falhar. Nunca há IP
    // Google fixo embutido no aplicativo.
    return _resolveWithPublicDns(host);
  }

'''
http = http[:start] + new_send + http[end:]

# A conexão direta também recebe connectionTimeout explícito. A validação TLS
# continua no hostname de uri.host dentro de SecureSocket.secure.
old_client = '''  static http.Client _clientForResolvedAddress(InternetAddress address) {\n    final io = HttpClient()\n      ..findProxy = (_) => 'DIRECT'\n'''
new_client = '''  static http.Client _clientForResolvedAddress(InternetAddress address) {\n    final io = HttpClient()\n      ..connectionTimeout = const Duration(seconds: 8)\n      ..findProxy = (_) => 'DIRECT'\n'''
if new_client not in http:
    if old_client not in http:
        raise RuntimeError('Cliente de endereço resolvido não localizado')
    http = http.replace(old_client, new_client, 1)

# A exceção final de Timeout no Android agora identifica que as duas rotas do hop
# já foram tentadas; normalmente o bloco acima converte a falha com o hostname.
old_timeout_catch = '''      } on TimeoutException catch (error) {\n        lastTransportError = error;\n        if (Platform.isAndroid) {\n          throw const CentralTransportException(\n            'A Central Online não respondeu a tempo. Seus dados continuam salvos no aparelho. Tente novamente quando a conexão estiver estável.',\n          );\n        }\n'''
new_timeout_catch = '''      } on TimeoutException catch (error) {\n        lastTransportError = error;\n        if (Platform.isAndroid || forceAndroidDirectForTesting) {\n          throw CentralTransportException(\n            'A Central Online não respondeu a tempo na etapa ${uri.host}. Seus dados continuam salvos no aparelho.',\n          );\n        }\n'''
if new_timeout_catch not in http:
    if old_timeout_catch not in http:
        raise RuntimeError('Catch de timeout Android não localizado')
    http = http.replace(old_timeout_catch, new_timeout_catch, 1)

pubp.write_text(pub, encoding='utf-8', newline='\n')
httpp.write_text(http, encoding='utf-8', newline='\n')

final_pub = pubp.read_text(encoding='utf-8')
final_http = httpp.read_text(encoding='utf-8')
assert 'version: 3.29.49+191' in final_pub
assert 'forceAndroidDirectForTesting' in final_http
assert '_resolvePreferredIpv4' in final_http
assert 'InternetAddressType.IPv4' in final_http
assert 'connectionTimeout = const Duration(seconds: 8)' in final_http
assert 'timeout: timeout,\n            addressOverride: address' in final_http
assert 'Não foi possível concluir a comunicação com ${uri.host}' in final_http
assert 'A Central Online não respondeu a tempo na etapa ${uri.host}' in final_http
assert "method = 'GET';" in final_http
assert "_redirectCodes = {301, 302, 303, 307, 308}" in final_http
print('Android v3.29.49+191: transporte Google em IPv4 dinâmico + recuperação de redirect aplicado.')

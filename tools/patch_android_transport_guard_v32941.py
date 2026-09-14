#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
pubp = root / 'pubspec.yaml'
httpp = root / 'lib/services/apps_script_http.dart'

pub = pubp.read_text(encoding='utf-8')
http = httpp.read_text(encoding='utf-8')

if 'version: 3.29.41+183' not in pub:
    if 'version: 3.29.40+182' not in pub:
        raise RuntimeError('Base Android v3.29.40+182 não encontrada')
    pub = pub.replace('version: 3.29.40+182', 'version: 3.29.41+183', 1)

# Exceção com toString limpo: a UI antiga pode exibir e.toString() diretamente,
# então nunca mostramos ClientException/SocketException/TimeoutException crus.
exception_class = r'''class CentralTransportException implements Exception {
  final String message;
  const CentralTransportException(this.message);

  @override
  String toString() => message;
}

'''
marker = 'class AppsScriptHttp {'
if 'class CentralTransportException implements Exception' not in http:
    if marker not in http:
        raise RuntimeError('AppsScriptHttp não encontrado')
    http = http.replace(marker, exception_class + marker, 1)

# O Android possui uma tela histórica que limita a ação manual a ~30 s. Para não
# deixar uma Future de rede viva em segundo plano depois de a tela desistir, cada
# tentativa de transporte no Android recebe no máximo 24 s. Windows preserva os
# timeouts próprios mais longos.
old = '''  static Future<http.Response> _postJsonDirect(
    Uri endpoint,
    Object? payload,
    Duration timeout,
  ) async {
    final encodedBody = jsonEncode(payload);
    Object? lastTransportError;
'''
new = '''  static Future<http.Response> _postJsonDirect(
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
'''
if 'final effectiveTimeout = Platform.isAndroid' not in http:
    if old not in http:
        raise RuntimeError('Cabeçalho _postJsonDirect não localizado')
    http = http.replace(old, new, 1)

http = http.replace('client.send(request).timeout(timeout)', 'client.send(request).timeout(effectiveTimeout)')
http = http.replace('http.Response.fromStream(streamed).timeout(timeout)', 'http.Response.fromStream(streamed).timeout(effectiveTimeout)')

# Em falha DNS não adianta repetir imediatamente duas vezes; isso era responsável
# por esperas longas e mensagens técnicas. Timeout no Android também não é
# repetido dentro do transporte, evitando ultrapassar o limite da tela.
old_catches = r'''      } on TimeoutException catch (error) {
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
'''
new_catches = r'''      } on TimeoutException catch (error) {
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
        final text = error.toString().toLowerCase();
        final dnsFailure = text.contains('failed host lookup') ||
            text.contains('no address associated with hostname') ||
            text.contains('nodename nor servname provided');
        if (dnsFailure) {
          throw const CentralTransportException(
            'Sem acesso à Central Online no momento. O celular não conseguiu localizar o servidor do Google. Seus dados continuam salvos no aparelho. Verifique Wi-Fi, dados móveis ou DNS privado e tente novamente.',
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
        final text = error.toString().toLowerCase();
        final dnsFailure = text.contains('failed host lookup') ||
            text.contains('no address associated with hostname');
        if (dnsFailure) {
          throw const CentralTransportException(
            'Sem acesso à Central Online no momento. O celular não conseguiu localizar o servidor do Google. Seus dados continuam salvos no aparelho. Verifique Wi-Fi, dados móveis ou DNS privado e tente novamente.',
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
'''
if 'O celular não conseguiu localizar o servidor do Google' not in http:
    if old_catches not in http:
        raise RuntimeError('Bloco de tratamento HTTP não localizado')
    http = http.replace(old_catches, new_catches, 1)

# Caso o fluxo saia do loop por uma falha de transporte já capturada, não volte a
# lançar o objeto técnico cru.
old_tail = '''    if (lastTransportError != null) {
      throw lastTransportError;
    }
'''
new_tail = '''    if (lastTransportError != null) {
      throw const CentralTransportException(
        'Não foi possível concluir a comunicação com a Central Online. Seus dados continuam salvos no aparelho e poderão ser sincronizados depois.',
      );
    }
'''
if old_tail in http:
    http = http.replace(old_tail, new_tail, 1)

pubp.write_text(pub, encoding='utf-8', newline='\n')
httpp.write_text(http, encoding='utf-8', newline='\n')

assert 'version: 3.29.41+183' in pubp.read_text(encoding='utf-8')
final_http = httpp.read_text(encoding='utf-8')
assert 'class CentralTransportException implements Exception' in final_http
assert 'const Duration(seconds: 24)' in final_http
assert 'O celular não conseguiu localizar o servidor do Google' in final_http
print('Android v3.29.41+183: DNS/timeout tratados sem Future órfã nem erro técnico cru.')

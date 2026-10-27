#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('app/Auditar_SST_v1_5_dashboard')
pubp = root / 'pubspec.yaml'
httpp = root / 'lib/services/apps_script_http.dart'
aip = root / 'lib/services/ai_assistant_service.dart'

pub = pubp.read_text(encoding='utf-8')
http = httpp.read_text(encoding='utf-8')
ai = aip.read_text(encoding='utf-8')


def once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Marcador ausente: {label}')
    return text.replace(old, new, 1)

pub = once(pub, 'version: 3.29.58+200', 'version: 3.29.59+201', 'versao 3.29.58')

# Mantem o timeout curto do Android para sincronizacao e demais operacoes rapidas,
# mas permite chamadas longas explicitamente marcadas (IA/Gemini).
http = once(
    http,
    """  static Future<http.Response> postJson(\n    Uri endpoint,\n    Object? payload, {\n    Duration timeout = const Duration(seconds: 30),\n  }) {\n    return _windowsSerial(() => _postJsonDirect(endpoint, payload, timeout));\n  }\n\n  static Future<http.Response> _postJsonDirect(\n    Uri endpoint,\n    Object? payload,\n    Duration timeout,\n  ) async {\n    final encodedBody = jsonEncode(payload);\n    final effectiveTimeout = (Platform.isAndroid || forceAndroidDirectForTesting)\n        ? const Duration(seconds: 10)\n        : timeout;\n""",
    """  static Future<http.Response> postJson(\n    Uri endpoint,\n    Object? payload, {\n    Duration timeout = const Duration(seconds: 30),\n    bool allowLongAndroidRequest = false,\n  }) {\n    return _windowsSerial(\n      () => _postJsonDirect(\n        endpoint,\n        payload,\n        timeout,\n        allowLongAndroidRequest,\n      ),\n    );\n  }\n\n  static Future<http.Response> _postJsonDirect(\n    Uri endpoint,\n    Object? payload,\n    Duration timeout,\n    bool allowLongAndroidRequest,\n  ) async {\n    final encodedBody = jsonEncode(payload);\n    final androidDirect = Platform.isAndroid || forceAndroidDirectForTesting;\n    final effectiveTimeout = androidDirect && !allowLongAndroidRequest\n        ? const Duration(seconds: 10)\n        : timeout;\n""",
    'assinatura e timeout do AppsScriptHttp',
)

http = once(
    http,
    """          final response = await _sendHopWithDnsFallback(\n            method: method,\n            uri: uri,\n            encodedBody: encodedBody,\n            timeout: effectiveTimeout,\n          );\n""",
    """          final response = await _sendHopWithDnsFallback(\n            method: method,\n            uri: uri,\n            encodedBody: encodedBody,\n            timeout: effectiveTimeout,\n            retryAlternateRouteAfterTimeout: !allowLongAndroidRequest,\n          );\n""",
    'chamada DNS fallback',
)

http = once(
    http,
    """  static Future<http.Response> _sendHopWithDnsFallback({\n    required String method,\n    required Uri uri,\n    required String encodedBody,\n    required Duration timeout,\n  }) async {\n""",
    """  static Future<http.Response> _sendHopWithDnsFallback({\n    required String method,\n    required Uri uri,\n    required String encodedBody,\n    required Duration timeout,\n    bool retryAlternateRouteAfterTimeout = true,\n  }) async {\n""",
    'assinatura DNS fallback',
)

http = once(
    http,
    """      } catch (error) {\n        directError = error;\n      }\n\n      // Segunda e última rota: pilha normal do Android. Isso cobre redes em que\n""",
    """      } catch (error) {\n        directError = error;\n        // Em chamadas longas (IA), um timeout significa que o Apps Script pode\n        // ainda estar processando a mesma requisicao. Nao repetimos o POST pela\n        // rota normal para evitar analise duplicada e custo/espera em dobro.\n        if (!retryAlternateRouteAfterTimeout && error is TimeoutException) {\n          rethrow;\n        }\n      }\n\n      // Segunda e última rota: pilha normal do Android. Isso cobre redes em que\n""",
    'nao duplicar POST longo apos timeout',
)

# A IA da Ronda e demais modos do assistente usam o timeout escolhido no proprio
# servico (55/65/75 s), sem herdar o teto de 10 s da sincronizacao Android.
ai = once(
    ai,
    """          timeout: requestTimeout,\n        );\n""",
    """          timeout: requestTimeout,\n          allowLongAndroidRequest: true,\n        );\n""",
    'IA com request longo no Android',
)

# Mensagem amigavel para eventual timeout real, sem expor TimeoutException/TimeoutException.
ai = once(
    ai,
    """      } catch (error) {\n        final message = error.toString().toLowerCase();\n        final transientNetworkError =\n""",
    """      } on CentralTransportException catch (error) {\n        final message = error.message.toLowerCase();\n        if (message.contains('não respondeu a tempo') ||\n            message.contains('timeoutexception')) {\n          return const AiAssistantReply(\n            success: false,\n            message:\n                'A análise da foto demorou além do limite da IA. O registro continua salvo; tente novamente em alguns instantes.',\n          );\n        }\n        return AiAssistantReply(\n          success: false,\n          message:\n              'Não foi possível concluir a comunicação com a IA. ${error.message}',\n        );\n      } catch (error) {\n        final message = error.toString().toLowerCase();\n        final transientNetworkError =\n""",
    'mensagem amigavel de transporte da IA',
)

for path, text in [(pubp, pub), (httpp, http), (aip, ai)]:
    path.write_text(text, encoding='utf-8', newline='\n')

# Regressao: sincronizacao continua com teto curto; somente a IA opta pelo longo.
assert 'version: 3.29.59+201' in pub
assert 'bool allowLongAndroidRequest = false' in http
assert 'androidDirect && !allowLongAndroidRequest' in http
assert 'const Duration(seconds: 10)' in http
assert 'retryAlternateRouteAfterTimeout: !allowLongAndroidRequest' in http
assert 'error is TimeoutException' in http
assert 'allowLongAndroidRequest: true' in ai
assert 'final requestTimeout =' in ai
assert 'const Duration(seconds: 55)' in ai
assert 'A análise da foto demorou além do limite da IA.' in ai
print('Android v3.29.59+201: IA da Ronda usa timeout proprio; sincronizacao rapida preservada.')

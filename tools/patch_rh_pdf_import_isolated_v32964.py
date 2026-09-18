#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/Auditar_SST_v1_5_dashboard')
svc = root / 'lib/services/worker_import_service.dart'
text = svc.read_text(encoding='utf-8')

# A importacao RH passa a ter cliente proprio. Nao toca no AppsScriptHttp usado
# pela sincronizacao, login, Central ou Drive.
if "import 'package:http/http.dart' as http;" not in text:
    anchor = "import 'package:file_picker/file_picker.dart';\n"
    if anchor not in text:
        raise SystemExit('Import de file_picker nao encontrado.')
    text = text.replace(
        anchor,
        anchor + "import 'package:http/http.dart' as http;\n",
        1,
    )

# O servico RH deixa de depender do transporte compartilhado.
text = text.replace("import 'apps_script_http.dart';\n", "")

old_call = """      final response = await AppsScriptHttp.postJson(
        Uri.parse(endpoint),
        {
          'action': 'ai_assistant',
          'syncKey': syncKey,
          'authToken': AuthService.sessionToken,
          'payload': {
            'mode': 'employee_pdf_import',
            'document': 'data:application/pdf;base64,${base64Encode(bytes)}',
          },
        },
        timeout: const Duration(seconds: 180),
      );"""

new_call = """      final response = await _postPdfImportDedicated(
        endpoint: Uri.parse(endpoint),
        payload: {
          'action': 'ai_assistant',
          'syncKey': syncKey,
          'authToken': AuthService.sessionToken,
          'payload': {
            'mode': 'employee_pdf_import',
            'document': 'data:application/pdf;base64,${base64Encode(bytes)}',
          },
        },
      );"""

if old_call not in text:
    # Tambem aceita a fonte ja marcada pela v3.29.63 para evitar patch fragil.
    old_call_63 = old_call.replace(
        "        timeout: const Duration(seconds: 180),\n      );",
        "        timeout: const Duration(seconds: 180),\n"
        "        // A leitura do PDF usa IA e pode demorar bem mais que o sync normal.\n"
        "        // Sem esta flag, o transporte Android reduz a chamada para 10 s.\n"
        "        // Esta opção vale SOMENTE para este POST de importação do RH.\n"
        "        allowLongAndroidRequest: true,\n"
        "      );",
    )
    if old_call_63 in text:
        text = text.replace(old_call_63, new_call, 1)
    else:
        raise SystemExit('Chamada employee_pdf_import nao encontrada.')
else:
    text = text.replace(old_call, new_call, 1)

helper_anchor = "  static Future<WorkerImportPreview> _prepare({\n"
helper = """  static Future<http.Response> _postPdfImportDedicated({
    required Uri endpoint,
    required Map<String, dynamic> payload,
  }) async {
    // Cliente exclusivo da importacao do RH. Ele nao usa a rota IPv4 direta,
    // fila, retry ou timeout do transporte da sincronizacao.
    final client = http.Client();
    try {
      return await client
          .post(
            endpoint,
            headers: const {
              'Content-Type': 'application/json; charset=utf-8',
              'Accept': 'application/json',
            },
            body: jsonEncode(payload),
          )
          .timeout(
            const Duration(seconds: 90),
            onTimeout: () {
              // Fecha o socket desta importacao sem afetar qualquer requisicao
              // de sincronizacao que esteja acontecendo em paralelo.
              client.close();
              throw const WorkerImportException(
                'A leitura do PDF passou de 90 segundos e foi cancelada. '
                'Nenhum trabalhador existente foi alterado. '
                'Tente novamente com internet estavel ou com um PDF mais leve.',
              );
            },
          );
    } on WorkerImportException {
      rethrow;
    } on http.ClientException {
      throw const WorkerImportException(
        'Nao foi possivel concluir a leitura do PDF pela internet. '
        'Nenhum trabalhador existente foi alterado. Tente novamente.',
      );
    } finally {
      client.close();
    }
  }

"""

if "_postPdfImportDedicated({" not in text:
    if helper_anchor not in text:
        raise SystemExit('Ancora para helper do PDF nao encontrada.')
    text = text.replace(helper_anchor, helper + helper_anchor, 1)

# Remove tratamento especifico da v3.29.63 caso esta fonte seja usada por engano.
text = re.sub(
    r"""    } on CentralTransportException catch \(error\) \{.*?    } on SocketException \{""",
    "    } on SocketException {",
    text,
    count=1,
    flags=re.S,
)

svc.write_text(text, encoding='utf-8', newline='\n')

pub = root / 'pubspec.yaml'
ptext = pub.read_text(encoding='utf-8')
ptext, count = re.subn(
    r'^version:\s*[^\n]+',
    'version: 3.29.64+206',
    ptext,
    count=1,
    flags=re.M,
)
if count != 1:
    raise SystemExit('Versao nao encontrada no pubspec.')
pub.write_text(ptext, encoding='utf-8', newline='\n')

print('Android v3.29.64+206: importacao RH isolada do transporte de sincronizacao.')

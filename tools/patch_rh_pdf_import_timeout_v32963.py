#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/Auditar_SST_v1_5_dashboard')
svc = root / 'lib/services/worker_import_service.dart'
text = svc.read_text(encoding='utf-8')

old = """        timeout: const Duration(seconds: 180),
      );"""
new = """        timeout: const Duration(seconds: 180),
        // A leitura do PDF usa IA e pode demorar bem mais que o sync normal.
        // Sem esta flag, o transporte Android reduz a chamada para 10 s.
        // Esta opção vale SOMENTE para este POST de importação do RH.
        allowLongAndroidRequest: true,
      );"""

if new not in text:
    if old not in text:
        raise SystemExit('Âncora da chamada employee_pdf_import não encontrada.')
    text = text.replace(old, new, 1)

# Mensagem específica para falha de transporte nessa função, sem alterar
# AppsScriptHttp (que também é usado pela sincronização).
catch_old = """    } on SocketException {
      throw const WorkerImportException(
        'A leitura do PDF precisa de internet. Tente novamente quando estiver conectado.',
      );"""
catch_new = """    } on CentralTransportException catch (error) {
      final detail = error.message.toLowerCase();
      if (detail.contains('tempo') || detail.contains('timeout')) {
        throw const WorkerImportException(
          'A leitura do PDF demorou mais que o esperado. Verifique a internet e tente novamente. Nenhum trabalhador existente foi alterado.',
        );
      }
      throw const WorkerImportException(
        'Não foi possível concluir a leitura do PDF pela internet. Tente novamente em alguns instantes. Nenhum trabalhador existente foi alterado.',
      );
    } on SocketException {
      throw const WorkerImportException(
        'A leitura do PDF precisa de internet. Tente novamente quando estiver conectado.',
      );"""

if catch_new not in text:
    if catch_old not in text:
        raise SystemExit('Âncora de tratamento de erro da importação RH não encontrada.')
    text = text.replace(catch_old, catch_new, 1)

svc.write_text(text, encoding='utf-8', newline='\n')

pub = root / 'pubspec.yaml'
ptext = pub.read_text(encoding='utf-8')
ptext, count = re.subn(r'^version:\s*[^\n]+', 'version: 3.29.63+205', ptext, count=1, flags=re.M)
if count != 1:
    raise SystemExit('Versão não encontrada no pubspec.')
pub.write_text(ptext, encoding='utf-8', newline='\n')

print('Android v3.29.63+205: importação PDF do RH usa timeout longo próprio; sync não alterado.')

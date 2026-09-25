#!/usr/bin/env python3
"""Fix only PDF model AI import on Android/Windows. Keep GS, sync and checklist AI unchanged."""
from pathlib import Path
import sys

root=Path(sys.argv[1])
platform=sys.argv[2]
assert platform in ('android','windows')
rel='lib/services/report_template_ai_import_service.dart'
file=root/rel
s=file.read_text(encoding='utf-8')

def change(old,new,label):
    global s
    n=s.count(old)
    if n != 1: raise RuntimeError(f'{label}: expected once, found {n}')
    s=s.replace(old,new,1)

change("import 'dart:convert';",
       "import 'dart:async';\nimport 'dart:convert';",
       'import TimeoutException')
# AppsScriptHttp otherwise substitutes a 10-second Android timeout for
# the requested 105 seconds. Opt in only for this AI PDF import.
change("          timeout: const Duration(seconds: 105),\n        );",
       "          timeout: const Duration(seconds: 105),\n          allowLongAndroidRequest: true,\n        );",
       'long request opt-in')
# A timed-out POST may still be running in Apps Script. Do not duplicate it.
change("""      } on SocketException catch (error) {
        lastError = error;""",
"""      } on TimeoutException {
        throw const ReportTemplateAiImportException(
          'A análise do PDF ultrapassou o tempo de resposta da Central. '
          'O modelo não foi cadastrado nem alterado. '
          'Tente novamente com um PDF menor ou com menos páginas.',
        );
      } on CentralTransportException catch (error) {
        throw ReportTemplateAiImportException(
          'A Central não concluiu a análise deste PDF: ${error.message} '
          'Nenhum modelo foi cadastrado. Tente novamente quando a conexão estabilizar.',
        );
      } on SocketException catch (error) {
        lastError = error;""",
       'no blind timeout replay')
change("""      } catch (error) {
        lastError = error;
        if (attempt == 0) {
          await Future<void>.delayed(const Duration(seconds: 2));
          continue;
        }
      }
    }

    if (decoded == null) {""",
"""      } catch (error) {
        lastError = error;
        // Unknown transport failures are not automatically retried: the
        // server may already be processing the previous large PDF upload.
        break;
      }
    }

    if (decoded == null) {""",
       'no duplicate POST for unknown failure')
change("""        'Não foi possível consultar a IA para analisar o modelo. $lastError',""",
"""        'Não foi possível concluir a análise do PDF na Central. '
        'Nenhum modelo foi cadastrado. Confira a conexão e tente novamente. '
        'Detalhe técnico: $lastError',""",
       'failure message')

file.write_text(s,encoding='utf-8',newline='\n')
pub=root/'pubspec.yaml';v=pub.read_text(encoding='utf-8')
old,new=('3.29.121+263','3.29.122+264') if platform=='android' else ('3.30.45+232','3.30.46+233')
assert v.count('version: '+old)==1,[x for x in v.splitlines() if x.startswith('version:')]
pub.write_text(v.replace('version: '+old,'version: '+new,1),encoding='utf-8',newline='\n')

assert s.count('allowLongAndroidRequest: true')==1
assert "on TimeoutException {" in s and "on CentralTransportException catch" in s
assert "mode': 'report_template_import'" in s
print('REPORT_TEMPLATE_AI_LONG_REQUEST_FIXED',platform,new)

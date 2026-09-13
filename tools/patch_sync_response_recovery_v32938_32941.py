#!/usr/bin/env python3
from pathlib import Path
import re, sys

root=Path(sys.argv[1]); platform=sys.argv[2].lower()
if platform not in {'android','windows'}: raise SystemExit('platform')
pubp=root/'pubspec.yaml'; syncp=root/'lib/services/device_sync_service.dart'; httpp=root/'lib/services/apps_script_http.dart'
pub=pubp.read_text(); sync=syncp.read_text(); http=httpp.read_text()
expected='version: 3.29.36+178' if platform=='android' else 'version: 3.29.39+181'
target='version: 3.29.38+180' if platform=='android' else 'version: 3.29.41+183'
if target not in pub:
    if expected not in pub: raise RuntimeError(f'version missing {expected}')
    pub=pub.replace(expected,target,1)

# Evita reutilizacao de conexao nos saltos temporarios do Apps Script.
if '..persistentConnection = false' not in http:
    old="""            final request = http.Request(method, uri)\n              ..followRedirects = false\n"""
    new="""            final request = http.Request(method, uri)\n              ..followRedirects = false\n              ..persistentConnection = false\n"""
    if old not in http: raise RuntimeError('http request marker missing')
    http=http.replace(old,new,1)

# Reduz resposta de pull para evitar respostas muito grandes do ContentService.
if platform=='android':
    sync=sync.replace("'limit': 300,", "'limit': 100,", 1)
else:
    sync=sync.replace('final pullLimit = isWindows ? 150 : 300;', 'final pullLimit = isWindows ? 100 : 100;', 1)

# Tenta novamente respostas HTTP 2xx que nao sejam JSON valido.
post_re = re.compile(r"  static Future<Map<String, dynamic>> _post\(.*?\n  \}\n\n  static int _asInt", re.S)
if not post_re.search(sync): raise RuntimeError('_post block missing')
new_post = r'''  static Future<Map<String, dynamic>> _post(
    Uri endpoint,
    Map<String, Object?> payload, {
    Duration? timeout,
  }) async {
    final action = '${payload['action'] ?? 'sync'}';
    String lastType = '';
    int lastStatus = 0;

    for (var attempt = 0; attempt < 3; attempt++) {
      final response = await AppsScriptHttp.postJson(
        endpoint,
        payload,
        timeout: timeout ?? const Duration(seconds: 30),
      );
      lastStatus = response.statusCode;
      lastType = '${response.headers['content-type'] ?? ''}'.trim();

      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw StateError(
          'A Central Online respondeu com erro ${response.statusCode}.',
        );
      }

      var body = utf8.decode(response.bodyBytes, allowMalformed: true).trim();
      if (body.isNotEmpty && body.codeUnitAt(0) == 0xFEFF) {
        body = body.substring(1).trimLeft();
      }

      dynamic decoded;
      try {
        decoded = jsonDecode(body);
      } catch (_) {
        if (attempt < 2) {
          await Future<void>.delayed(Duration(milliseconds: 350 + (attempt * 300)));
          continue;
        }
        throw StateError(
          'A Central Online retornou uma resposta inválida em $action '
          '(HTTP $lastStatus${lastType.isEmpty ? '' : ', $lastType'}).',
        );
      }

      if (decoded is! Map) {
        if (attempt < 2) {
          await Future<void>.delayed(Duration(milliseconds: 350 + (attempt * 300)));
          continue;
        }
        throw StateError(
          'Resposta inválida da Central Online em $action '
          '(HTTP $lastStatus${lastType.isEmpty ? '' : ', $lastType'}).',
        );
      }

      final result = Map<String, dynamic>.from(decoded);
      if (result['ok'] != true) {
        throw StateError('${result['message'] ?? 'Falha na sincronização.'}');
      }
      return result;
    }

    throw StateError(
      'A Central Online não concluiu $action após novas tentativas.',
    );
  }

  static bool _invalidCentralResponse(Object error) {
    final value = '$error'.toLowerCase();
    return value.contains('resposta inválida') || value.contains('resposta invalida');
  }

  static Future<int> _pushChangesSafely({
    required Database db,
    required Uri endpoint,
    required String syncKey,
    required String deviceId,
    required List<Map<String, Object?>> changes,
    Duration? timeout,
  }) async {
    if (changes.isEmpty) return 0;
    try {
      final response = await _post(
        endpoint,
        {
          'action': 'device_sync_push',
          'syncKey': syncKey,
          'authToken': AuthService.sessionToken,
          'deviceId': deviceId,
          'platform': isWindows ? 'windows' : 'android',
          'changes': changes,
        },
        timeout: timeout,
      );
      if (response.containsKey('accepted')) {
        final accepted = _asInt(response['accepted']);
        if (accepted != changes.length) {
          throw StateError(
            'A Central Online confirmou $accepted de ${changes.length} alterações. '
            'Nada foi marcado como enviado para evitar perda de dados.',
          );
        }
      }
      await _acknowledgeChanges(db, changes);
      return changes.length;
    } catch (error) {
      // Se o Google devolver HTML/pagina temporaria para um lote, divide o lote
      // e preserva o progresso dos registros que responderem corretamente.
      if (!_invalidCentralResponse(error) || changes.length == 1) {
        if (changes.length == 1 && _invalidCentralResponse(error)) {
          final item = changes.first;
          throw StateError(
            '${_friendlyError(error)} Registro: ${item['table']}/${item['id']}.',
          );
        }
        rethrow;
      }
      final middle = changes.length ~/ 2;
      final left = changes.sublist(0, middle);
      final right = changes.sublist(middle);
      var sent = 0;
      sent += await _pushChangesSafely(
        db: db,
        endpoint: endpoint,
        syncKey: syncKey,
        deviceId: deviceId,
        changes: left,
        timeout: timeout,
      );
      sent += await _pushChangesSafely(
        db: db,
        endpoint: endpoint,
        syncKey: syncKey,
        deviceId: deviceId,
        changes: right,
        timeout: timeout,
      );
      return sent;
    }
  }

  static int _asInt'''
sync=post_re.sub(new_post,sync, count=1)

# Troca envio monolitico por envio com fallback/divisao de lote.
old=re.compile(r"        final pushResponse = await _post\(uri, \{\n          'action': 'device_sync_push',.*?        sent \+= changes.length;\n", re.S)
if platform=='android':
    replacement="""        sent += await _pushChangesSafely(\n          db: db,\n          endpoint: uri,\n          syncKey: syncKey,\n          deviceId: deviceId,\n          changes: changes,\n          timeout: const Duration(seconds: 30),\n        );\n"""
else:
    replacement="""        sent += await _pushChangesSafely(\n          db: db,\n          endpoint: uri,\n          syncKey: syncKey,\n          deviceId: deviceId,\n          changes: changes,\n          timeout: force\n              ? const Duration(seconds: 45)\n              : const Duration(seconds: 35),\n        );\n"""
if not old.search(sync): raise RuntimeError('push block missing')
sync=old.sub(replacement,sync,count=1)

pubp.write_text(pub); syncp.write_text(sync); httpp.write_text(http)
assert target in pub
assert '_pushChangesSafely' in sync
assert 'resposta inválida em $action' in sync
assert 'persistentConnection = false' in http
print(f'JSON/sync recovery applied: {target}')

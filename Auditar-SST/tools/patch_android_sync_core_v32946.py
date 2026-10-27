#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
pubp = root / 'pubspec.yaml'
authp = root / 'lib/services/auth_service.dart'
syncp = root / 'lib/services/device_sync_service.dart'

pub = pubp.read_text(encoding='utf-8')
auth = authp.read_text(encoding='utf-8')
sync = syncp.read_text(encoding='utf-8')


def once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Marcador ausente: {label}')
    return text.replace(old, new, 1)

# Versão
if 'version: 3.29.46+188' not in pub:
    pub = once(pub, 'version: 3.29.45+187', 'version: 3.29.46+188', 'versão 3.29.45')

# 1) Login fresco não pode zerar o cursor de sincronização de uma conta já existente.
# Banco novo já começa naturalmente em 0; banco existente mantém o último cursor confirmado.
# Há mais de um caminho de aceitação de sessão no AuthService montado; nenhum deles deve
# reiniciar o cursor porque cada usuário já possui seu próprio banco SQLite.
auth = auth.replace(
    "    await AppDatabase.instance.setSetting('device_sync_server_version', '0');\n",
    '',
)

# 2) Se há rede e o login online falha por DNS/timeout/transporte, não mascarar o erro
# entrando silenciosamente com uma sessão offline antiga. O login offline continua válido
# quando o Android realmente informa ConnectivityResult.none.
old_online_fallback = r'''    } catch (error) {
      if (!_isOfflineTransportError(error)) rethrow;
      return _loginOffline(identifier: identifier, password: password);
    }
'''
new_online_fallback = r'''    } catch (error) {
      // Com rede disponível, o usuário precisa de uma sessão nova confirmada pela
      // Central. Não reutilizamos silenciosamente token antigo em caso de timeout/DNS.
      rethrow;
    }
'''
if new_online_fallback not in auth:
    if old_online_fallback not in auth:
        raise RuntimeError('Fallback online->offline não localizado')
    auth = auth.replace(old_online_fallback, new_online_fallback, 1)

# 3) Explicitar falta de escopo de empresa antes de iniciar uma sincronização que
# inevitavelmente voltaria vazia para um técnico sem empresas liberadas.
marker_auth_guard = """      if (!AuthService.isSignedIn || AuthService.sessionToken.isEmpty) {\n        throw StateError('Faça login para sincronizar este dispositivo.');\n      }\n\n"""
scoped_guard = marker_auth_guard + """      final signedUser = AuthService.currentUser;\n      if (signedUser != null &&\n          !signedUser.isAdmin &&\n          !signedUser.allCompanies &&\n          signedUser.companyIds.isEmpty) {\n        throw StateError(\n          'Seu usuário não possui nenhuma empresa liberada na Central Online.',\n        );\n      }\n\n"""
if "Seu usuário não possui nenhuma empresa liberada" not in sync:
    if marker_auth_guard not in sync:
        raise RuntimeError('Guard de autenticação do DeviceSyncService ausente')
    sync = sync.replace(marker_auth_guard, scoped_guard, 1)

# 4) A Central real possui mais de 1.200 registros. Com limit=100 e apenas 12 páginas,
# uma sincronização podia parar no meio do snapshot. Ampliamos o limite de páginas para
# concluir o backlog real em um único ciclo, mantendo lotes pequenos por estabilidade.
sync = sync.replace('for (var page = 0; page < 12; page++) {',
                    'for (var page = 0; page < 60; page++) {')

# 5) Antes do envio local, fazer um pull completo. Assim um lote local problemático não
# impede o aparelho de receber empresas/colaboradores/vistorias da Central.
# Para não perder edição local não enviada, _applyRemoteChanges passa a ignorar somente
# o registro remoto que conflita com dirty=1; depois do push, o segundo pull reconcilia.
old_push_start = """      var sent = 0;\n      for (var page = 0; page < 8; page++) {\n"""
bootstrap_pull = """      var received = 0;\n\n      // Primeiro RECEBE a Central. Isso garante atualização mesmo se algum envio\n      // local estiver com problema. Registros locais ainda dirty são preservados.\n      for (var page = 0; page < 60; page++) {\n        final since = int.tryParse(\n              await appDb.getSetting(\n                _serverVersionSetting,\n                fallback: '0',\n              ),\n            ) ??\n            0;\n        final response = await _post(uri, {\n          'action': 'device_sync_pull',\n          'syncKey': syncKey,\n          'authToken': AuthService.sessionToken,\n          'deviceId': deviceId,\n          'platform': isWindows ? 'windows' : 'android',\n          'sinceVersion': since,\n          'limit': 100,\n        });\n\n        final rawChanges = response['changes'];\n        final changes = rawChanges is List ? rawChanges : const [];\n        if (changes.isNotEmpty) {\n          await _applyRemoteChanges(db, changes);\n          received += changes.length;\n        }\n\n        final nextVersion = _asInt(response['nextVersion']);\n        final currentVersion = _asInt(response['version']);\n        final savedVersion = nextVersion > 0 ? nextVersion : currentVersion;\n        if (savedVersion >= since) {\n          await appDb.setSetting(_serverVersionSetting, '$savedVersion');\n        }\n        if (response['hasMore'] != true) break;\n        if (savedVersion <= since) {\n          throw StateError('A Central Online não avançou o cursor de sincronização.');\n        }\n      }\n\n      var sent = 0;\n      for (var page = 0; page < 8; page++) {\n"""
if '// Primeiro RECEBE a Central.' not in sync:
    if old_push_start not in sync:
        raise RuntimeError('Início do push não localizado')
    sync = sync.replace(old_push_start, bootstrap_pull, 1)

# O pull que já existia depois do push permanece como reconciliação, sem redeclarar received.
old_second_pull = """      var received = 0;\n      for (var page = 0; page < 60; page++) {\n"""
new_second_pull = """      // Segundo pull: reconcilia o que acabou de ser enviado e captura\n      // alterações que chegaram enquanto o primeiro pull estava em andamento.\n      for (var page = 0; page < 60; page++) {\n"""
if old_second_pull in sync:
    # Há duas ocorrências após a inserção do bootstrap. A primeira é a nova; substitui a última.
    idx = sync.rfind(old_second_pull)
    sync = sync[:idx] + new_second_pull + sync[idx + len(old_second_pull):]
elif '// Segundo pull: reconcilia' not in sync:
    raise RuntimeError('Segundo pull não localizado')

# 6) Não sobrescrever uma edição local ainda não enviada quando o primeiro pull recebe
# uma versão remota do mesmo registro. O cursor pode avançar porque, após o push local,
# o servidor gera nova serverVersion e o segundo pull fará a reconciliação.
apply_marker = """        final deleted = change['deleted'] == true;\n        if (deleted) {\n"""
apply_guard = """        final localDirty = await txn.query(\n          _changesTable,\n          columns: ['dirty'],\n          where: 'table_name = ? AND record_id = ?',\n          whereArgs: [table, recordId],\n          limit: 1,\n        );\n        if (localDirty.isNotEmpty && _asInt(localDirty.first['dirty']) == 1) {\n          // Mantém a edição local até ela ser enviada. O segundo pull receberá a\n          // versão reconciliada do servidor depois do push.\n          continue;\n        }\n\n        final deleted = change['deleted'] == true;\n        if (deleted) {\n"""
if 'final localDirty = await txn.query(' not in sync:
    if apply_marker not in sync:
        raise RuntimeError('Ponto de proteção de conflito remoto ausente')
    sync = sync.replace(apply_marker, apply_guard, 1)

pubp.write_text(pub, encoding='utf-8', newline='\n')
authp.write_text(auth, encoding='utf-8', newline='\n')
syncp.write_text(sync, encoding='utf-8', newline='\n')

# Regressões essenciais
final_pub = pubp.read_text(encoding='utf-8')
final_auth = authp.read_text(encoding='utf-8')
final_sync = syncp.read_text(encoding='utf-8')
assert 'version: 3.29.46+188' in final_pub
assert "setSetting('device_sync_server_version', '0')" not in final_auth
assert 'Não reutilizamos silenciosamente token antigo' in final_auth
assert 'Seu usuário não possui nenhuma empresa liberada' in final_sync
assert final_sync.count('for (var page = 0; page < 60; page++) {') >= 2
assert final_sync.find('// Primeiro RECEBE a Central.') < final_sync.find('var sent = 0;')
assert final_sync.find('var sent = 0;') < final_sync.find('// Segundo pull: reconcilia')
assert 'final localDirty = await txn.query(' in final_sync
assert "'limit': 100," in final_sync
print('Android v3.29.46+188: núcleo de sincronização corrigido (cursor, sessão, pull-first, backlog completo e conflito local protegido).')

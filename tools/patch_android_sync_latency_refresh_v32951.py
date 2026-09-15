#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
pubp = root / 'pubspec.yaml'
syncp = root / 'lib/services/device_sync_service.dart'
coordp = root / 'lib/services/sync_coordinator.dart'

pub = pubp.read_text(encoding='utf-8')
sync = syncp.read_text(encoding='utf-8')
coord = coordp.read_text(encoding='utf-8')

if 'version: 3.29.51+193' not in pub:
    if 'version: 3.29.50+192' not in pub:
        raise RuntimeError('Base v3.29.50+192 não encontrada')
    pub = pub.replace('version: 3.29.50+192', 'version: 3.29.51+193', 1)

# A Central aceita até 500 registros por pull. A v3.29.46 estava usando 100,
# obrigando ~22 viagens para um snapshot de ~2.200 alterações. Com 500, o
# mesmo snapshot exige cerca de 5 viagens e mantém o cursor incremental depois.
sync = sync.replace("'limit': 100,", "'limit': 500,")

# Atualiza a interface assim que CADA página recebida é gravada no SQLite.
# Antes o evento só saía quando todo o ciclo terminava; por isso apertar
# 'Atualizar' mostrava dados que já estavam no banco, mas a tela não sabia disso.
old_apply = """        if (changes.isNotEmpty) {
          await _applyRemoteChanges(db, changes);
          received += changes.length;
        }
"""
new_apply = """        if (changes.isNotEmpty) {
          await _applyRemoteChanges(db, changes);
          received += changes.length;
          // Notifica as telas imediatamente após a transação local. Assim
          // empresas, inspeções e indicadores aparecem sem atualização manual.
          _events.add(DeviceSyncResult(received: changes.length));
        }
"""
count = sync.count(old_apply)
if count < 2:
    raise RuntimeError(f'Esperadas 2 rotas de apply remoto, encontradas {count}')
sync = sync.replace(old_apply, new_apply)

# O segundo pull só é necessário quando houve PUSH local. Em um ciclo limpo,
# fazer pull->push vazio->pull duplicava o tráfego e podia manter o app em
# 'Sincronizando...' quase continuamente.
start_marker = """      // Segundo pull: reconcilia o que acabou de ser enviado e captura
      // alterações que chegaram enquanto o primeiro pull estava em andamento.
      for (var page = 0; page < 60; page++) {
"""
if start_marker not in sync:
    raise RuntimeError('Segundo pull não localizado')
sync = sync.replace(
    start_marker,
    """      // Segundo pull só é útil depois de enviar algo local. Em ciclos
      // somente de recebimento, encerramos após o primeiro pull para reduzir
      // latência, bateria e chamadas ao Apps Script.
      if (sent > 0) {
        for (var page = 0; page < 60; page++) {
""",
    1,
)

end_marker = """        if (response['hasMore'] != true) break;
        if (savedVersion <= since) {
          throw StateError('A Central Online não avançou o cursor de sincronização.');
        }
      }

      // Os dados estruturados terminam aqui. Fotos/assinaturas são uma
"""
if end_marker not in sync:
    raise RuntimeError('Fim do segundo pull não localizado')
sync = sync.replace(
    end_marker,
    """          if (response['hasMore'] != true) break;
          if (savedVersion <= since) {
            throw StateError('A Central Online não avançou o cursor de sincronização.');
          }
        }
      }

      // Os dados estruturados terminam aqui. Fotos/assinaturas são uma
""",
    1,
)

# O timer de 2 s permanece apenas como detector LOCAL: ele consulta SQLite e
# só abre rede quando existe alteração pendente. O pull remoto fica em 10 s,
# mas agora custa apenas uma chamada quando não há envio local.
if 'const Duration(seconds: 2)' not in coord:
    raise RuntimeError('Detector local de 2 s não localizado')
if 'const Duration(seconds: 10)' not in coord:
    raise RuntimeError('Pull remoto de 10 s não localizado')

pubp.write_text(pub, encoding='utf-8', newline='\n')
syncp.write_text(sync, encoding='utf-8', newline='\n')
coordp.write_text(coord, encoding='utf-8', newline='\n')

final_pub = pubp.read_text(encoding='utf-8')
final_sync = syncp.read_text(encoding='utf-8')
final_coord = coordp.read_text(encoding='utf-8')
assert 'version: 3.29.51+193' in final_pub
assert final_sync.count("'limit': 500,") >= 2
assert final_sync.count('_events.add(DeviceSyncResult(received: changes.length));') >= 2
assert 'if (sent > 0) {' in final_sync
assert 'Duration(seconds: 2)' in final_coord
assert 'Duration(seconds: 10)' in final_coord
print('Android v3.29.51+193: pull 500, refresh por página e segundo pull evitado quando não há envio local.')

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

sync = sync.replace("'limit': 100,", "'limit': 500,")

old_apply = """        if (changes.isNotEmpty) {
          await _applyRemoteChanges(db, changes);
          received += changes.length;
        }
"""
new_apply = """        if (changes.isNotEmpty) {
          await _applyRemoteChanges(db, changes);
          received += changes.length;
          _events.add(DeviceSyncResult(received: changes.length));
        }
"""
if sync.count(old_apply) < 2:
    raise RuntimeError('Blocos de recebimento não localizados')
sync = sync.replace(old_apply, new_apply)

comment = """      // Segundo pull: reconcilia o que acabou de ser enviado e captura
      // alterações que chegaram enquanto o primeiro pull estava em andamento.
"""
next_block = "      // Os dados estruturados terminam aqui. Fotos/assinaturas são uma\n"
start = sync.find(comment)
end = sync.find(next_block, start)
if start < 0 or end < 0:
    raise RuntimeError('Bloco do segundo pull não localizado')
segment = sync[start:end]
loop = '      for (var page = 0; page < 60; page++) {\n'
if loop not in segment:
    raise RuntimeError('Loop do segundo pull não localizado')
segment = segment.replace(
    comment + loop,
    """      // Reconcilia novamente somente quando houve envio local.
      if (sent > 0) {
        for (var page = 0; page < 60; page++) {
""",
    1,
)
segment = segment.rstrip() + '\n      }\n\n'
sync = sync[:start] + segment + sync[end:]

if 'const Duration(seconds: 2)' not in coord:
    raise RuntimeError('Detector local de 2 s não localizado')
if 'const Duration(seconds: 10)' not in coord:
    raise RuntimeError('Pull remoto de 10 s não localizado')

pubp.write_text(pub, encoding='utf-8', newline='\n')
syncp.write_text(sync, encoding='utf-8', newline='\n')
coordp.write_text(coord, encoding='utf-8', newline='\n')

assert 'version: 3.29.51+193' in pubp.read_text(encoding='utf-8')
final_sync = syncp.read_text(encoding='utf-8')
assert final_sync.count("'limit': 500,") >= 2
assert final_sync.count('_events.add(DeviceSyncResult(received: changes.length));') >= 2
assert 'if (sent > 0) {' in final_sync
print('v3.29.51 aplicada: lote 500, atualização visual por página e pull duplicado removido quando ocioso.')

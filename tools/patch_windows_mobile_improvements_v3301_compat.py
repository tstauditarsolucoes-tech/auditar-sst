#!/usr/bin/env python3
from pathlib import Path
import runpy
import sys

if len(sys.argv) < 2:
    raise SystemExit('Uso: patch_windows_mobile_improvements_v3301_compat.py <app_dir>')

root = Path(sys.argv[1])
syncp = root / 'lib/services/device_sync_service.dart'
coordp = root / 'lib/services/sync_coordinator.dart'

# Estrutura real do Windows: pullLimit/pullPages em variáveis.
sync = syncp.read_text(encoding='utf-8')
sync = sync.replace(
    'final pullLimit = isWindows ? 100 : 100;',
    'final pullLimit = isWindows ? 500 : 100;',
    1,
)
sync = sync.replace(
    'final pullLimit = isWindows ? 150 : 300;',
    'final pullLimit = isWindows ? 500 : 300;',
    1,
)
sync = sync.replace(
    'final pullPages = isWindows ? (force ? 5 : 2) : 12;',
    'final pullPages = isWindows ? (force ? 60 : 4) : 12;',
    1,
)
syncp.write_text(sync, encoding='utf-8', newline='\n')

# Aplica histórico DDS + ficha PDF + retry de mídia do patch consolidado.
# A asserção final do patch original procura a forma Android literal de limit;
# no Windows as alterações funcionais já foram gravadas, então validamos abaixo.
old_argv = sys.argv[:]
try:
    sys.argv = [
        str(Path(__file__).with_name('patch_windows_mobile_improvements_v3301.py')),
        str(root),
    ]
    try:
        runpy.run_path(sys.argv[0], run_name='__main__')
    except AssertionError:
        pass
finally:
    sys.argv = old_argv

# Coordenador real do Windows v3.30.0. O patch principal pode ter alterado o
# callback antes desta camada; por isso o intervalo é trocado separadamente.
coord = coordp.read_text(encoding='utf-8')
coord = coord.replace(
    '? const Duration(seconds: 75)',
    '? const Duration(seconds: 10)',
    1,
)

# Garante callback de consulta remota mesmo quando não existe fila local.
coord = coord.replace(
    '      (_) => _trySync(deviceOnly: true),',
    """      (_) => _trySync(
        deviceOnly: true,
        force: true,
        pullWhenClean: true,
      ),""",
    1,
)

coord = coord.replace(
    '  Future<void> _trySync({bool deviceOnly = false}) async {',
    """  Future<void> _trySync({
    bool deviceOnly = false,
    bool force = false,
    bool pullWhenClean = false,
  }) async {""",
    1,
)

coord = coord.replace(
    """    if (deviceOnly) {
      try {
        final localPending = await DeviceSyncService.pendingChangesCount();
        if (localPending == 0) return;
      } catch (_) {
        return;
      }
    }
""",
    """    if (deviceOnly && !pullWhenClean) {
      try {
        final localPending = await DeviceSyncService.pendingChangesCount();
        if (localPending == 0) return;
      } catch (_) {
        return;
      }
    }
""",
    1,
)

coord = coord.replace(
    '    if (nextAttempt != null && DateTime.now().isBefore(nextAttempt)) return;',
    '    if (!force && nextAttempt != null && DateTime.now().isBefore(nextAttempt)) return;',
    1,
)

coord = coord.replace(
    """        result = await DeviceSyncService.synchronize(
          syncMedia: Platform.isWindows ? false : null,
        );
""",
    """        result = await DeviceSyncService.synchronize(
          force: force,
          syncMedia: Platform.isWindows ? false : null,
        );
""",
    1,
)
coordp.write_text(coord, encoding='utf-8', newline='\n')

# Validação funcional específica do Windows.
pub = (root / 'pubspec.yaml').read_text(encoding='utf-8')
sync = syncp.read_text(encoding='utf-8')
coord = coordp.read_text(encoding='utf-8')
dds = (root / 'lib/screens/sst_records_screen.dart').read_text(encoding='utf-8')
media = (root / 'lib/services/media_sync_service.dart').read_text(encoding='utf-8')
db = (root / 'lib/database.dart').read_text(encoding='utf-8')

assert 'version: 3.30.1+188' in pub
assert 'final pullLimit = isWindows ? 500 : 100;' in sync
assert 'final pullPages = isWindows ? (force ? 60 : 4) : 12;' in sync
assert '? const Duration(seconds: 10)' in coord
assert 'pullWhenClean: true' in coord
assert 'bool pullWhenClean = false' in coord
assert 'force: force' in coord
assert 'if (!force && nextAttempt != null' in coord
assert 'Retirar ficha do DDS' in dds
assert 'Histórico permanente de DDS' in dds
assert 'FICHA_DDS_' in dds
assert "type == 'DDS' ? 'date DESC'" in db
assert '_postReliable(' in media
assert 'continuam salvas no computador' in media
print('Windows v3.30.1 compatível: pull 500/60 páginas + consulta 10s + DDS histórico/ficha + mídia resiliente.')

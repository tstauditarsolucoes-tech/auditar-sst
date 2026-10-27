#!/usr/bin/env python3
"""Windows: receive an initial page before the potentially long upload backlog."""
from pathlib import Path
import re,sys
root=Path(sys.argv[1])
p=root/"lib/services/device_sync_service.dart"
pubp=root/"pubspec.yaml"
src=p.read_text(encoding="utf-8")
pub=pubp.read_text(encoding="utf-8")
if "var received = 0;" not in src or "final pushPages = isWindows ? (force ? 5 : 1) : 8;" not in src:
    raise RuntimeError("Unexpected Windows sync implementation")

# The prior Windows implementation could spend 75 s pushing five batches
# before its first pull, leaving the Home showing a stale company count.
anchor="""      var sent = 0;
      final watch = Stopwatch()..start();
"""
bootstrap="""      // Dados remotos primeiro: salva a primeira página já no banco, emite o
      // evento para atualizar a Home, e só então esvazia a fila local.
      // A própria _applyRemoteChanges protege registros dirty=1.
      var received = 0;
      var bootstrapHasMore = false;
      final firstSince = int.tryParse(
            await appDb.getSetting(_serverVersionSetting, fallback: '0'),
          ) ??
          0;
      _emitProgress(12, 'Recebendo dados da Central');
      final firstResponse = await _post(uri, {
        'action': 'device_sync_pull',
        'syncKey': syncKey,
        'authToken': AuthService.sessionToken,
        'deviceId': deviceId,
        'platform': 'windows',
        'sinceVersion': firstSince,
        'limit': 500,
      }, timeout: const Duration(seconds: 35));
      final firstRaw = firstResponse['changes'];
      final firstChanges = firstRaw is List ? firstRaw : const [];
      if (firstChanges.isNotEmpty) {
        await _applyRemoteChanges(db, firstChanges);
        received += firstChanges.length;
        _events.add(DeviceSyncResult(received: firstChanges.length));
      }
      final firstNext = _asInt(firstResponse['nextVersion']);
      final firstCurrent = _asInt(firstResponse['version']);
      final firstSaved = firstNext > 0 ? firstNext : firstCurrent;
      if (firstResponse['hasMore'] == true && firstSaved <= firstSince) {
        throw StateError('A Central não avançou a versão do primeiro lote.');
      }
      if (firstSaved >= firstSince) {
        await appDb.setSetting(_serverVersionSetting, '$firstSaved');
      }
      bootstrapHasMore = firstResponse['hasMore'] == true;

      var sent = 0;
      final watch = Stopwatch()..start();
"""
if src.count(anchor)!=1: raise RuntimeError("push entry not found once")
src=src.replace(anchor,bootstrap,1)
after="""      var received = 0;
      var remoteHasMore = false;
"""
if src.count(after)!=1: raise RuntimeError("second pull entry not found once")
src=src.replace(after,"""      // Se o primeiro pull estava limpo e não houve envio local, evite
      // repetir a mesma consulta à Central no mesmo ciclo.
      var remoteHasMore = bootstrapHasMore;
""",1)
needle="      for (var page = 0; page < pullPages; page++) {\n"
if src.count(needle)!=1: raise RuntimeError("second pull loop not found once")
src=src.replace(needle,"      for (var page = 0; page < pullPages && (remoteHasMore || sent > 0); page++) {\n",1)

pub,n=re.subn(r"(?m)^version:\s*[^\r\n]+$", "version: 3.30.24+211",pub,count=1)
if n!=1: raise RuntimeError("version missing")
p.write_text(src,encoding="utf-8",newline="\n")
pubp.write_text(pub,encoding="utf-8",newline="\n")
assert src.index("final firstResponse = await _post(") < src.index("var sent = 0;")
assert src.index("received += firstChanges.length;") < src.index("_pushChangesSafely(")
assert src.count("var received = 0;")==1
assert "if (firstSaved >= firstSince)" in src
assert "pullPages && (remoteHasMore || sent > 0)" in src
print("WINDOWS_FIRST_PULL_BEFORE_PUSH_OK 3.30.24+211")

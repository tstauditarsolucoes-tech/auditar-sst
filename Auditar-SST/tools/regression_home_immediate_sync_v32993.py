#!/usr/bin/env python3
from pathlib import Path
import sys

root=Path(sys.argv[1])
version=sys.argv[2] if len(sys.argv)>2 else ""

home=(root/"lib/screens/home_screen.dart").read_text(encoding="utf-8")
assert "_homeEntrySyncStarted" in home
assert "WidgetsBinding.instance.addPostFrameCallback" in home
assert "_syncImmediatelyOnHomeEntry()" in home
assert "DeviceSyncService.synchronize(" in home
assert "force: true" in home
assert "Duration(seconds: 15)" in home
assert "_refresh(showLoading: false)" in home

# O nucleo global continua existindo: a Home so acrescenta o gatilho imediato.
coord=(root/"lib/services/sync_coordinator.dart").read_text(encoding="utf-8")
sync=(root/"lib/services/device_sync_service.dart").read_text(encoding="utf-8")

# Android preserva exatamente o coordenador rapido aprovado (2 s / 5 s)
# e a fila force do sync estruturado. Windows tem implementacao multiusuario
# propria, por isso valida o contrato publico sem exigir a assinatura Android.
if not version.startswith("3.30."):
    assert "static Future<DeviceSyncResult> synchronize({bool force = false})" in sync
    assert "_queuedForceSync" in sync
    assert "AuthService.sessionReadyEvents.listen" in coord
    assert "Duration(seconds: 2)" in coord
    assert "Duration(seconds: 5)" in coord
    assert "pullWhenClean: true" in coord
else:
    assert "synchronize(" in sync
    assert "_trySync" in coord
    assert "DeviceSyncService.synchronize" in coord

if version:
    pub=(root/"pubspec.yaml").read_text(encoding="utf-8")
    assert f"version: {version}" in pub

print("HOME_IMMEDIATE_SYNC_REGRESSION_OK",version)

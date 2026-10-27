#!/usr/bin/env python3
"""Minimal fix for duplicate forced pulls; original coordinator schedules first pull."""
from pathlib import Path
import re, sys
if len(sys.argv) < 2:
    raise SystemExit("uso: patch_sync_singleflight_v329100.py <APP_DIR> [android|windows]")
root=Path(sys.argv[1])
platform=(sys.argv[2] if len(sys.argv)>2 else "android").lower()
if platform not in ("android","windows"):
    raise SystemExit("plataforma desconhecida")

syncp=root/"lib/services/device_sync_service.dart"
homep=root/"lib/screens/home_screen.dart"
pubp=root/"pubspec.yaml"
s=syncp.read_text(encoding="utf-8")
h=homep.read_text(encoding="utf-8")
pub=pubp.read_text(encoding="utf-8")

# The old Home patch launched a separate force:true while the coordinator was
# already doing the first pull. A second forced pull was then queued by the sync
# service. On a slow Apps Script call this made the initial load repeat.
start=s.index("  static Future<DeviceSyncResult> synchronize({bool force = false}) {")
end=s.index("  static Future<DeviceSyncResult> _synchronizeOnce({", start)
old=s[start:end]
checks=["_queuedForceSync","_activeSync","_synchronizeOnce(force: force)"]
if not all(x in old for x in checks):
    raise RuntimeError("Nucleo de sincronizacao diferente do esperado")
replacement="""  static Future<DeviceSyncResult> synchronize({bool force = false}) {
    // SINGLE FLIGHT: login, timers e Home compartilham o mesmo pull em curso.
    // Nunca agenda uma segunda varredura completa enquanto a primeira roda.
    // Se surgirem edicoes no meio, o timer local de 2 s cuidara do proximo
    // ciclo. Os dados dirty e o cursor permanecem no banco, sem reset.
    final active = _activeSync;
    if (active != null) return active;

    late final Future<DeviceSyncResult> operation;
    operation = _synchronizeOnce(force: force).whenComplete(() {
      if (identical(_activeSync, operation)) _activeSync = null;
    });
    _activeSync = operation;
    return operation;
  }

"""
s=s[:start]+replacement+s[end:]
needle="  static Future<DeviceSyncResult>? _queuedForceSync;\n"
if s.count(needle)!=1:
    raise RuntimeError("Fila de sync forçado diferente do esperado")
s=s.replace(needle,"",1)

# Restore v3.29.66/v3.29.58 Home behavior: local data first; the global
# SyncCoordinator already listens to sessionReadyEvents and pulls immediately.
field="  bool _homeEntrySyncStarted = false;\n"
if h.count(field)!=1:
    raise RuntimeError("Gatilho duplicado na Home ausente")
h=h.replace(field,"",1)
start=h.index("    WidgetsBinding.instance.addPostFrameCallback((_) {\n      unawaited(_syncImmediatelyOnHomeEntry());\n    });")
end=h.index("  @override\n  void dispose() {",start)
part=h[start:end]
if "_syncImmediatelyOnHomeEntry" not in part or "DeviceSyncService.synchronize" not in part:
    raise RuntimeError("Bloco Home diferente do esperado")
h=h[:start]+"  }\n\n"+h[end:]

# Keep the proven 2 s local / 5 s remote coordinator, push-before-reconcile,
# media queue, Central URL, user database, auth, and all screens unchanged.
version="3.29.100+242" if platform=="android" else "3.30.24+211"
pub,n=re.subn(r"(?m)^version:\s*[^\r\n]+$",f"version: {version}",pub,count=1)
if n!=1: raise RuntimeError("Version field missing")

syncp.write_text(s,encoding="utf-8",newline="\n")
homep.write_text(h,encoding="utf-8",newline="\n")
pubp.write_text(pub,encoding="utf-8",newline="\n")

assert "_queuedForceSync" not in s
assert "if (active != null) return active;" in s
assert "_syncImmediatelyOnHomeEntry" not in h
assert "DeviceSyncService.events.listen" in h
assert "    _refresh();\n  }\n\n  @override\n  void dispose()" in h
assert f"version: {version}" in pub
print("SYNC_SINGLEFLIGHT_AND_HOME_RESTORE_OK",platform,version)

#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) < 2:
    raise SystemExit("uso: patch_home_immediate_sync_v32993_v33020.py <APP_DIR> [android|windows]")

root=Path(sys.argv[1])
platform=(sys.argv[2] if len(sys.argv)>2 else "android").lower()

def read(rel):
    return (root/rel).read_text(encoding="utf-8")

def write(rel,text):
    (root/rel).write_text(text,encoding="utf-8",newline="\n")

rel="lib/screens/home_screen.dart"
s=read(rel)

# Evita repetir o gatilho dentro da mesma instancia da Home.
marker="""  bool loading = true;
  String loadError = '';
"""
replacement="""  bool loading = true;
  String loadError = '';
  bool _homeEntrySyncStarted = false;
"""
if "_homeEntrySyncStarted" not in s:
    if marker not in s:
        raise RuntimeError("campos da Home nao localizados")
    s=s.replace(marker,replacement,1)

# Disparo imediatamente depois do primeiro frame. A leitura local continua
# aparecendo sem esperar rede; o sync estruturado roda em segundo plano.
old="""    _refresh();
  }

  @override
  void dispose() {
"""
new="""    _refresh();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      unawaited(_syncImmediatelyOnHomeEntry());
    });
  }

  Future<void> _syncImmediatelyOnHomeEntry() async {
    if (_homeEntrySyncStarted) return;
    _homeEntrySyncStarted = true;

    try {
      final result = await DeviceSyncService.synchronize(
        force: true,
      ).timeout(const Duration(seconds: 15));

      if (!mounted) return;
      // O listener de DeviceSyncService ja atualiza quando chegam paginas
      // remotas. Este refresh final cobre tambem envio local/resultado limpo.
      if (result.sent > 0 || result.received > 0 || !result.skipped) {
        await _refresh(showLoading: false);
      }
    } catch (_) {
      // A Home nunca fica presa por rede. O coordenador global continua
      // tentando normalmente em retorno de internet e nos ciclos seguintes.
    }
  }

  @override
  void dispose() {
"""
if "_syncImmediatelyOnHomeEntry()" not in s:
    if old not in s:
        raise RuntimeError("initState da Home nao localizado")
    s=s.replace(old,new,1)

write(rel,s)

# Versao
rel="pubspec.yaml"
pub=read(rel)
version="3.30.20+207" if platform=="windows" else "3.29.93+235"
pub,count=re.subn(r"(?m)^version:\s*[^\r\n]+","version: "+version,pub,count=1)
if count!=1:
    raise RuntimeError("versao nao localizada")
write(rel,pub)

# Garantias: alteracao fica na Home, sem tocar no nucleo de sync.
home=read("lib/screens/home_screen.dart")
assert "WidgetsBinding.instance.addPostFrameCallback" in home
assert "DeviceSyncService.synchronize(" in home
assert "force: true" in home
assert "Duration(seconds: 15)" in home
assert "_refresh(showLoading: false)" in home
assert f"version: {version}" in read("pubspec.yaml")
print("HOME_IMMEDIATE_SYNC_OK",platform,version)

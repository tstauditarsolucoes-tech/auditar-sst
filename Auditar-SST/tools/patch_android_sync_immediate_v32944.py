#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
pubp = root / 'pubspec.yaml'
authp = root / 'lib/services/auth_service.dart'
coordp = root / 'lib/services/sync_coordinator.dart'

pub = pubp.read_text(encoding='utf-8')
auth = authp.read_text(encoding='utf-8')
coord = coordp.read_text(encoding='utf-8')

if 'version: 3.29.44+186' not in pub:
    if 'version: 3.29.43+185' not in pub:
        raise RuntimeError('Base Android v3.29.43+185 não encontrada')
    pub = pub.replace('version: 3.29.43+185', 'version: 3.29.44+186', 1)

if "import 'dart:async';" not in auth:
    auth = "import 'dart:async';\n" + auth

if '_sessionReadyEvents' not in auth:
    marker = "  static bool _offlineMode = false;\n\n  static bool get isOfflineMode => _offlineMode;\n"
    replacement = "  static bool _offlineMode = false;\n  static final StreamController<void> _sessionReadyEvents =\n      StreamController<void>.broadcast();\n\n  static bool get isOfflineMode => _offlineMode;\n  static Stream<void> get sessionReadyEvents => _sessionReadyEvents.stream;\n"
    if marker not in auth:
        raise RuntimeError('Campos offline do AuthService não localizados')
    auth = auth.replace(marker, replacement, 1)

online_marker = "      } catch (_) {}\n      return user;\n    } catch (error) {\n"
if '_sessionReadyEvents.add(null);\n      return user;' not in auth:
    if online_marker not in auth:
        raise RuntimeError('Retorno do login online não localizado')
    auth = auth.replace(
        online_marker,
        "      } catch (_) {}\n      _sessionReadyEvents.add(null);\n      return user;\n    } catch (error) {\n",
        1,
    )

offline_marker = "    await AppDatabase.instance.setSetting(\n      'last_device_sync_status',\n      'Modo offline • aguardando internet',\n    );\n    return user;\n"
if auth.count('_sessionReadyEvents.add(null);') < 2:
    if offline_marker not in auth:
        raise RuntimeError('Retorno do login offline não localizado')
    auth = auth.replace(
        offline_marker,
        "    await AppDatabase.instance.setSetting(\n      'last_device_sync_status',\n      'Modo offline • aguardando internet',\n    );\n    _sessionReadyEvents.add(null);\n    return user;\n",
        1,
    )

# O coordenador fica vivo também na tela de login. Escutar o evento de sessão
# elimina a janela em que a sincronização inicial era perdida por acontecer
# antes de o usuário terminar o login.
if '_sessionSubscription' not in coord:
    marker = "  StreamSubscription<List<ConnectivityResult>>? _subscription;\n"
    if marker not in coord:
        raise RuntimeError('Subscription de conectividade não localizada')
    coord = coord.replace(
        marker,
        marker + "  StreamSubscription<void>? _sessionSubscription;\n",
        1,
    )

if 'AuthService.sessionReadyEvents.listen' not in coord:
    marker = "    _subscription = Connectivity()\n        .onConnectivityChanged\n        .listen(_handleConnectivity);\n\n"
    replacement = "    _subscription = Connectivity()\n        .onConnectivityChanged\n        .listen(_handleConnectivity);\n\n    _sessionSubscription = AuthService.sessionReadyEvents.listen((_) {\n      unawaited(_syncImmediatelyAfterLogin());\n    });\n\n"
    if marker not in coord:
        raise RuntimeError('Inicialização da conectividade não localizada')
    coord = coord.replace(marker, replacement, 1)

coord = coord.replace(
    "      const Duration(seconds: 45),\n      (_) => _trySync(deviceOnly: true),\n",
    "      const Duration(seconds: 10),\n      (_) => _trySync(deviceOnly: true, force: true),\n",
    1,
)

if '_sessionSubscription?.cancel();' not in coord:
    marker = "    _subscription?.cancel();\n"
    if marker not in coord:
        raise RuntimeError('Dispose da conectividade não localizado')
    coord = coord.replace(marker, marker + "    _sessionSubscription?.cancel();\n", 1)

if 'Future<void> _syncImmediatelyAfterLogin()' not in coord:
    marker = "  Future<void> _tryAutoBackup() async {\n"
    helper = "  Future<void> _syncImmediatelyAfterLogin() async {\n    // Dá um instante para a ativação do banco do usuário terminar e então\n    // força o primeiro pull/push. Não espera o timer de 5 minutos.\n    await Future<void>.delayed(const Duration(milliseconds: 250));\n    if (!mounted || !AuthService.isSignedIn) return;\n    await _trySync(force: true);\n  }\n\n"
    if marker not in coord:
        raise RuntimeError('Ponto de inserção do sync pós-login não localizado')
    coord = coord.replace(marker, helper + marker, 1)

# Ao voltar para o app ou quando a rede reaparece, sincroniza imediatamente,
# ignorando o intervalo mínimo de 60 s que existe para tentativas automáticas.
coord = coord.replace(
    "      _trySync(deviceOnly: true);\n      _tryAutoBackup();\n",
    "      _trySync(force: true);\n      _tryAutoBackup();\n",
    1,
)
coord = coord.replace("    _trySync();\n  }\n\n  Future<void> _trySync({bool deviceOnly = false}) async {\n",
                      "    _trySync(force: true);\n  }\n\n  Future<void> _trySync({bool deviceOnly = false, bool force = false}) async {\n",
                      1)

if 'Future<void> _trySync({bool deviceOnly = false, bool force = false})' not in coord:
    raise RuntimeError('Assinatura force do _trySync não aplicada')

old_call = "        result = await DeviceSyncService.synchronize();\n"
new_call = "        result = await DeviceSyncService.synchronize(force: force);\n"
if new_call not in coord:
    if old_call not in coord:
        raise RuntimeError('Chamada DeviceSyncService.synchronize não localizada')
    coord = coord.replace(old_call, new_call, 1)

pubp.write_text(pub, encoding='utf-8', newline='\n')
authp.write_text(auth, encoding='utf-8', newline='\n')
coordp.write_text(coord, encoding='utf-8', newline='\n')

final_pub = pubp.read_text(encoding='utf-8')
final_auth = authp.read_text(encoding='utf-8')
final_coord = coordp.read_text(encoding='utf-8')
assert 'version: 3.29.44+186' in final_pub
assert 'sessionReadyEvents' in final_auth
assert final_auth.count('_sessionReadyEvents.add(null);') >= 2
assert '_sessionSubscription' in final_coord
assert 'Duration(seconds: 10)' in final_coord
assert '_trySync(force: true)' in final_coord
assert 'DeviceSyncService.synchronize(force: force)' in final_coord
print('Android v3.29.44+186: sincronização imediata após login, retorno de rede e retomada aplicada.')

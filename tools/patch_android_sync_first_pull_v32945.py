#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
pubp = root / 'pubspec.yaml'
coordp = root / 'lib/services/sync_coordinator.dart'
syncp = root / 'lib/services/device_sync_service.dart'

pub = pubp.read_text(encoding='utf-8')
coord = coordp.read_text(encoding='utf-8')
sync = syncp.read_text(encoding='utf-8')

def once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Marcador ausente: {label}')
    return text.replace(old, new, 1)

if 'version: 3.29.45+187' not in pub:
    pub = once(pub, 'version: 3.29.44+186', 'version: 3.29.45+187', 'versão')

# Dados estruturados têm prioridade. Fotos/Drive não podem segurar a primeira
# carga de empresas, vistorias e cadastros.
sync = once(
    sync,
    """  static Future<DeviceSyncResult>? _activeSync;\n  static bool _changeTrackingReady = false;\n""",
    """  static Future<DeviceSyncResult>? _activeSync;\n  static Future<DeviceSyncResult>? _queuedForceSync;\n  static Future<void>? _activeMediaSync;\n  static bool _changeTrackingReady = false;\n""",
    'campos de fila de sync',
)

sync = once(
    sync,
    """  static Future<DeviceSyncResult> synchronize({bool force = false}) {\n    final active = _activeSync;\n    if (active != null) return active;\n\n    late final Future<DeviceSyncResult> operation;\n""",
    """  static Future<DeviceSyncResult> synchronize({bool force = false}) {\n    final active = _activeSync;\n    if (active != null) {\n      if (!force) return active;\n\n      // Login, volta da internet e ação manual não podem ser engolidos por\n      // uma tentativa anterior que ainda esteja encerrando.\n      final queued = _queuedForceSync;\n      if (queued != null) return queued;\n      late final Future<DeviceSyncResult> followUp;\n      followUp = active.then<DeviceSyncResult>(\n        (_) => synchronize(force: true),\n        onError: (Object _, StackTrace __) => synchronize(force: true),\n      ).whenComplete(() {\n        if (identical(_queuedForceSync, followUp)) _queuedForceSync = null;\n      });\n      _queuedForceSync = followUp;\n      return followUp;\n    }\n\n    late final Future<DeviceSyncResult> operation;\n""",
    'force não pode ser perdido',
)

sync = once(
    sync,
    """      await appDb.setSetting(\n        _lastAttemptSetting,\n        DateTime.now().toUtc().toIso8601String(),\n      );\n\n      final db = await appDb.database;\n      await _ensureChangeTracking(db);\n      try {\n        await MediaSyncService.uploadPending();\n      } catch (_) {\n        // A falha de uma foto não bloqueia a sincronização dos demais dados.\n      }\n      final deviceId = await AuthService.deviceId();\n""",
    """      await appDb.setSetting(\n        _lastAttemptSetting,\n        DateTime.now().toUtc().toIso8601String(),\n      );\n      await appDb.setSetting(_lastStatusSetting, 'Sincronizando dados...');\n      await appDb.setSetting(_lastErrorSetting, '');\n\n      final db = await appDb.database;\n      await _ensureChangeTracking(db);\n      final deviceId = await AuthService.deviceId();\n""",
    'mídia antes dos dados',
)

sync = once(
    sync,
    """      try {\n        await MediaSyncService.downloadMissing();\n      } catch (_) {\n        // O download de evidências será tentado novamente no próximo ciclo.\n      }\n\n      final now = DateTime.now().toUtc().toIso8601String();\n      await appDb.setSetting(_lastSuccessSetting, now);\n      await appDb.setSetting(\n        _lastStatusSetting,\n        sent == 0 && received == 0\n            ? 'Tudo atualizado'\n            : 'Enviados: $sent • Recebidos: $received',\n      );\n      await appDb.setSetting(_lastErrorSetting, '');\n      final result = DeviceSyncResult(sent: sent, received: received);\n      _events.add(result);\n      return result;\n""",
    """      // Os dados estruturados terminam aqui. Fotos/assinaturas são uma\n      // fila independente e não atrasam mais a primeira carga da Central.\n      final now = DateTime.now().toUtc().toIso8601String();\n      await appDb.setSetting(_lastSuccessSetting, now);\n      await appDb.setSetting(\n        _lastStatusSetting,\n        sent == 0 && received == 0\n            ? 'Tudo atualizado'\n            : 'Enviados: $sent • Recebidos: $received',\n      );\n      await appDb.setSetting(_lastErrorSetting, '');\n      final result = DeviceSyncResult(sent: sent, received: received);\n      _events.add(result);\n      unawaited(_syncMediaBestEffort());\n      return result;\n""",
    'finalização estruturada antes da mídia',
)

helper_marker = "  static Future<bool> _attemptIsDue(AppDatabase db) async {\n"
helper = """  static Future<void> _syncMediaBestEffort() {\n    final active = _activeMediaSync;\n    if (active != null) return active;\n\n    late final Future<void> operation;\n    operation = (() async {\n      try {\n        await MediaSyncService.uploadPending().timeout(\n          const Duration(seconds: 45),\n        );\n      } catch (_) {}\n      try {\n        await MediaSyncService.downloadMissing().timeout(\n          const Duration(seconds: 45),\n        );\n      } catch (_) {}\n    })().whenComplete(() {\n      if (identical(_activeMediaSync, operation)) _activeMediaSync = null;\n    });\n    _activeMediaSync = operation;\n    return operation;\n  }\n\n"""
if 'static Future<void> _syncMediaBestEffort() {' not in sync:
    if helper_marker not in sync:
        raise RuntimeError('Ponto para helper de mídia ausente')
    sync = sync.replace(helper_marker, helper + helper_marker, 1)

# O ciclo rápido deve insistir na PRIMEIRA sincronização mesmo com fila local
# vazia. Depois da primeira conclusão ele só envia rápido quando há alteração;
# um pull remoto leve a cada 30 s mantém PC e celular próximos em tempo real.
coord = once(
    coord,
    """    _maintenanceTimer = Timer.periodic(\n      const Duration(minutes: 5),\n      (_) {\n        _trySync();\n        _tryAutoBackup();\n      },\n    );\n""",
    """    _maintenanceTimer = Timer.periodic(\n      const Duration(seconds: 30),\n      (_) {\n        _trySync(deviceOnly: true, force: true, pullWhenClean: true);\n        _tryAutoBackup();\n      },\n    );\n""",
    'pull remoto periódico',
)

coord = once(
    coord,
    """      _trySync(force: true);\n      _tryAutoBackup();\n""",
    """      _trySync(deviceOnly: true, force: true, pullWhenClean: true);\n      _tryAutoBackup();\n""",
    'retomada do app',
)

coord = once(
    coord,
    """    await _trySync(force: true);\n  }\n\n  Future<void> _tryAutoBackup() async {\n""",
    """    await _trySync(deviceOnly: true, force: true, pullWhenClean: true);\n  }\n\n  Future<void> _tryAutoBackup() async {\n""",
    'primeiro sync pós-login',
)

coord = once(
    coord,
    """    _trySync(force: true);\n  }\n\n  Future<void> _trySync({bool deviceOnly = false, bool force = false}) async {\n""",
    """    _trySync(deviceOnly: true, force: true, pullWhenClean: true);\n  }\n\n  Future<void> _trySync({\n    bool deviceOnly = false,\n    bool force = false,\n    bool pullWhenClean = false,\n  }) async {\n""",
    'rede voltou e assinatura _trySync',
)

coord = once(
    coord,
    """    if (deviceOnly) {\n      try {\n        final localPending = await DeviceSyncService.pendingChangesCount();\n        if (localPending == 0) return;\n      } catch (_) {\n        return;\n      }\n    }\n\n    final connectivity = await Connectivity().checkConnectivity();\n""",
    """    if (deviceOnly && !pullWhenClean) {\n      try {\n        final localPending = await DeviceSyncService.pendingChangesCount();\n        if (localPending == 0) {\n          final lastSuccess = (await AppDatabase.instance.getSetting(\n            'last_device_sync_success',\n          ))\n              .trim();\n          // Sem uma conclusão anterior, fila local vazia não significa que o\n          // aparelho está atualizado: ainda falta baixar a Central.\n          if (lastSuccess.isNotEmpty) return;\n        }\n      } catch (_) {\n        // Em caso de dúvida, tenta a Central em vez de abandonar o 1º pull.\n      }\n    }\n\n    final connectivity = await Connectivity().checkConnectivity();\n""",
    'gate que bloqueava primeiro pull',
)

pubp.write_text(pub, encoding='utf-8', newline='\n')
coordp.write_text(coord, encoding='utf-8', newline='\n')
syncp.write_text(sync, encoding='utf-8', newline='\n')

final_pub = pubp.read_text(encoding='utf-8')
final_coord = coordp.read_text(encoding='utf-8')
final_sync = syncp.read_text(encoding='utf-8')
assert 'version: 3.29.45+187' in final_pub
assert '_queuedForceSync' in final_sync
assert 'Sincronizando dados...' in final_sync
assert 'unawaited(_syncMediaBestEffort());' in final_sync
assert final_sync.find('final deviceId = await AuthService.deviceId();') < final_sync.find('MediaSyncService.uploadPending()')
assert 'Duration(seconds: 30)' in final_coord
assert 'pullWhenClean: true' in final_coord
assert 'if (lastSuccess.isNotEmpty) return;' in final_coord
print('Android v3.29.45+187: primeiro pull garantido, mídia desacoplada e force não perdido.')

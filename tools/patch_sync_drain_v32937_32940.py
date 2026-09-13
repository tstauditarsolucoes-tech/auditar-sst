#!/usr/bin/env python3
"""Auditar SST: garante drenagem da fila de sincronizacao sem alterar a interface.

Android: 3.29.36+178 -> 3.29.37+179
Windows: 3.29.39+181 -> 3.29.40+182

Correcoes:
- um clique manual com force=true nunca e mais descartado quando ja existe sync ativo;
- no Windows, uma atualizacao parcial agenda continuacao real em 20 s;
- o ciclo automatico do Windows pode enviar duas paginas curtas, respeitando o mesmo budget;
- adiciona teste de regressao para a fila de force=true.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
platform = (sys.argv[2] if len(sys.argv) > 2 else '').strip().lower()
if platform not in {'android', 'windows'}:
    raise SystemExit('Uso: patch_sync_drain_v32937_32940.py <app_root> <android|windows>')


def read(rel: str) -> str:
    return (root / rel).read_text(encoding='utf-8')


def write(rel: str, text: str) -> None:
    (root / rel).write_text(text, encoding='utf-8')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Marcador nao encontrado: {label}')
    return text.replace(old, new, 1)

# Versao
pub = read('pubspec.yaml')
if platform == 'android':
    expected = 'version: 3.29.36+178'
    target = 'version: 3.29.37+179'
else:
    expected = 'version: 3.29.39+181'
    target = 'version: 3.29.40+182'
if target not in pub:
    if expected not in pub:
        raise RuntimeError(f'Versao esperada ausente: {expected}')
    pub = pub.replace(expected, target, 1)
write('pubspec.yaml', pub)

# 1) DeviceSyncService: force manual deve virar uma passada garantida apos o
# sync que ja estava ativo, em vez de simplesmente devolver o Future antigo.
sync = read('lib/services/device_sync_service.dart')
sync = replace_once(
    sync,
    """  static Future<DeviceSyncResult>? _activeSync;\n  static bool _changeTrackingReady = false;\n""",
    """  static Future<DeviceSyncResult>? _activeSync;\n  static Future<DeviceSyncResult>? _queuedForceSync;\n  static bool _changeTrackingReady = false;\n""",
    'fila de force',
)
old_start = """  static Future<DeviceSyncResult> synchronize({\n    bool force = false,\n    bool? syncMedia,\n  }) {\n    final active = _activeSync;\n    if (active != null) return active;\n\n    final shouldSyncMedia = syncMedia ?? !isWindows;\n"""
new_start = """  static Future<DeviceSyncResult> synchronize({\n    bool force = false,\n    bool? syncMedia,\n  }) {\n    final active = _activeSync;\n    if (active != null) {\n      if (!force) return active;\n\n      // Um clique em \"Sincronizar tudo agora\" pode acontecer enquanto o\n      // ciclo automatico ainda esta terminando. Antes, o force=true era\n      // descartado e o usuario recebia somente o resultado do ciclo antigo.\n      // Agora enfileiramos exatamente uma passada forçada logo depois dele.\n      final queued = _queuedForceSync;\n      if (queued != null) return queued;\n\n      late final Future<DeviceSyncResult> followUp;\n      followUp = active.then<DeviceSyncResult>(\n        (_) => synchronize(force: true, syncMedia: syncMedia),\n        onError: (Object _, StackTrace __) =>\n            synchronize(force: true, syncMedia: syncMedia),\n      ).whenComplete(() {\n        if (identical(_queuedForceSync, followUp)) _queuedForceSync = null;\n      });\n      _queuedForceSync = followUp;\n      return followUp;\n    }\n\n    final shouldSyncMedia = syncMedia ?? !isWindows;\n"""
sync = replace_once(sync, old_start, new_start, 'force nao pode ser descartado')
sync = replace_once(
    sync,
    """      final pushPages = isWindows ? (force ? 5 : 1) : 8;\n""",
    """      final pushPages = isWindows ? (force ? 5 : 2) : 8;\n""",
    'duas paginas curtas no Windows',
)
write('lib/services/device_sync_service.dart', sync)

# 2) SyncCoordinator: se o proprio resultado diz que ainda ha fila, agenda de
# verdade uma continuacao curta. O metodo existente continua respeitando rede,
# login, lock e backoff, portanto nao cria loop agressivo.
coord = read('lib/services/sync_coordinator.dart')
coord = replace_once(
    coord,
    """  Timer? _maintenanceTimer;\n  DateTime? _lastSessionVerification;\n""",
    """  Timer? _maintenanceTimer;\n  Timer? _continuationTimer;\n  DateTime? _lastSessionVerification;\n""",
    'timer de continuacao',
)
coord = replace_once(
    coord,
    """    _maintenanceTimer?.cancel();\n    _indicatorTimer?.cancel();\n""",
    """    _maintenanceTimer?.cancel();\n    _continuationTimer?.cancel();\n    _indicatorTimer?.cancel();\n""",
    'cancelar timer de continuacao',
)
marker = """  Future<void> _tryAutoBackup() async {\n    if (!AuthService.isSignedIn) return;\n    try {\n      await BackupService.createAutomaticBackupIfDue();\n    } catch (_) {}\n  }\n\n"""
insert = marker + """  void _schedulePartialContinuation() {\n    if (!Platform.isWindows || !mounted || !AuthService.isSignedIn) return;\n    _continuationTimer?.cancel();\n    _continuationTimer = Timer(const Duration(seconds: 20), () {\n      _continuationTimer = null;\n      if (!mounted || !AuthService.isSignedIn) return;\n      _trySync(deviceOnly: true);\n    });\n  }\n\n  void _clearPartialContinuation() {\n    _continuationTimer?.cancel();\n    _continuationTimer = null;\n  }\n\n"""
coord = replace_once(coord, marker, insert, 'metodos de continuacao')
old_result = """      if (result != null) {\n        _setDesktopStatus(\n          label: result.partial ? 'Atualização continuará em segundo plano' : 'Dados atualizados',\n          tone: result.partial ? _SyncTone.warning : _SyncTone.ok,\n        );\n      }\n"""
new_result = """      if (result != null) {\n        if (result.partial) {\n          _schedulePartialContinuation();\n        } else {\n          _clearPartialContinuation();\n        }\n        _setDesktopStatus(\n          label: result.partial ? 'Atualização continuará em segundo plano' : 'Dados atualizados',\n          tone: result.partial ? _SyncTone.warning : _SyncTone.ok,\n        );\n      }\n"""
coord = replace_once(coord, old_result, new_result, 'continuacao apos resultado parcial')
write('lib/services/sync_coordinator.dart', coord)

# 3) Teste de regressao: duas chamadas force=true simultaneas nao podem apontar
# para o mesmo Future; a segunda deve ser executada como follow-up.
test_path = root / 'test/device_sync_roundtrip_test.dart'
if test_path.exists():
    test = test_path.read_text(encoding='utf-8')
    test_marker = """  test(\n    'sincroniza inclusão, alteração e exclusão entre dois bancos locais',\n"""
    if test_marker not in test:
        raise RuntimeError('Teste principal de sincronizacao nao encontrado')
    regression_name = 'force manual durante sync ativo ganha uma passada propria'
    if regression_name not in test:
        closing = """    timeout: const Timeout(Duration(seconds: 45)),\n  );\n}\n"""
        addition = """    timeout: const Timeout(Duration(seconds: 45)),\n  );\n\n  test(\n    'force manual durante sync ativo ganha uma passada propria',\n    () async {\n      await _writeSession(\n        supportDir: supportDir,\n        userId: 'sync-force-user',\n        deviceId: 'force-device',\n        token: 'token-force',\n      );\n      await _configureSync(central.endpoint);\n\n      final db = await AppDatabase.instance.database;\n      await db.insert('companies', {\n        'id': 'empresa-force-${DateTime.now().microsecondsSinceEpoch}',\n        'name': 'Empresa para testar fila force',\n      });\n\n      final automaticLikeRun = DeviceSyncService.synchronize(force: true);\n      final manualForcedRun = DeviceSyncService.synchronize(force: true);\n\n      // Antes da correção, as duas variáveis eram exatamente o mesmo Future e\n      // o clique manual era perdido se um sync já estivesse ativo.\n      expect(identical(automaticLikeRun, manualForcedRun), isFalse);\n\n      await automaticLikeRun;\n      final followUp = await manualForcedRun;\n      expect(followUp.pending, 0);\n      expect(await DeviceSyncService.pendingChangesCount(), 0);\n    },\n    timeout: const Timeout(Duration(seconds: 45)),\n  );\n}\n"""
        if closing not in test:
            raise RuntimeError('Fim do arquivo de teste nao encontrado')
        test = test.replace(closing, addition, 1)
        test_path.write_text(test, encoding='utf-8')

# Validacoes
sync_check = read('lib/services/device_sync_service.dart')
coord_check = read('lib/services/sync_coordinator.dart')
assert target in read('pubspec.yaml')
assert 'static Future<DeviceSyncResult>? _queuedForceSync;' in sync_check
assert 'if (!force) return active;' in sync_check
assert 'final pushPages = isWindows ? (force ? 5 : 2) : 8;' in sync_check
assert 'Timer? _continuationTimer;' in coord_check
assert 'Timer(const Duration(seconds: 20)' in coord_check
print(f'Sync drain aplicado em {platform}: {target}')

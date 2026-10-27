#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('app/Auditar_SST_v1_5_dashboard')

pubp = root / 'pubspec.yaml'
coordp = root / 'lib/services/sync_coordinator.dart'
devp = root / 'lib/services/device_sync_service.dart'
mediap = root / 'lib/services/media_sync_service.dart'
homep = root / 'lib/screens/home_screen.dart'
companiesp = root / 'lib/screens/companies_screen.dart'
workersp = root / 'lib/screens/workers_screen.dart'
dashp = root / 'lib/screens/dashboard_screen.dart'

pub = pubp.read_text(encoding='utf-8')
coord = coordp.read_text(encoding='utf-8')
dev = devp.read_text(encoding='utf-8')
media = mediap.read_text(encoding='utf-8')
home = homep.read_text(encoding='utf-8')
companies = companiesp.read_text(encoding='utf-8')
workers = workersp.read_text(encoding='utf-8')
dash = dashp.read_text(encoding='utf-8')


def once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Marcador ausente: {label}')
    return text.replace(old, new, 1)


# Versão.
pub = once(pub, 'version: 3.29.57+199', 'version: 3.29.58+200', 'versão 3.29.57')

# 1) Pull remoto mais curto. O timer local de 2 s permanece igual à linha rápida aprovada.
coord = once(
    coord,
    """    _maintenanceTimer = Timer.periodic(\n      const Duration(seconds: 10),\n      (_) {\n        _trySync(deviceOnly: true, force: true, pullWhenClean: true);\n      },\n    );\n""",
    """    _maintenanceTimer = Timer.periodic(\n      const Duration(seconds: 5),\n      (_) {\n        _trySync(deviceOnly: true, force: true, pullWhenClean: true);\n      },\n    );\n""",
    'poll remoto 10 s',
)

# 2) Mídia não pode ocupar a rede continuamente. Ela continua automática, mas só
#    quando o ciclo estruturado terminou limpo, no máximo 1 vez por minuto.
field_marker = """  static Future<DeviceSyncResult>? _queuedForceSync;\n  static Future<void>? _activeMediaSync;\n  static bool _changeTrackingReady = false;\n"""
field_new = """  static Future<DeviceSyncResult>? _queuedForceSync;\n  static Future<void>? _activeMediaSync;\n  static DateTime? _lastAutoMediaKick;\n  static bool _changeTrackingReady = false;\n"""
dev = once(dev, field_marker, field_new, 'controle de mídia automática')

old_finish = """      final result = DeviceSyncResult(sent: sent, received: received);\n      _events.add(result);\n      unawaited(_syncMediaBestEffort());\n      return result;\n"""
new_finish = """      final result = DeviceSyncResult(sent: sent, received: received);\n      _events.add(result);\n\n      // Mídia é baixa prioridade. Só inicia quando este ciclo não teve dados\n      // estruturados para enviar/receber e no máximo uma vez por minuto.\n      if (sent == 0 && received == 0) {\n        final mediaNow = DateTime.now().toUtc();\n        final lastMediaKick = _lastAutoMediaKick;\n        if (lastMediaKick == null ||\n            mediaNow.difference(lastMediaKick) >= const Duration(minutes: 1)) {\n          _lastAutoMediaKick = mediaNow;\n          unawaited(_syncMediaBestEffort());\n        }\n      }\n      return result;\n"""
dev = once(dev, old_finish, new_finish, 'mídia disparada em todo sync')

old_media_helper = """    operation = (() async {\n      try {\n        await MediaSyncService.uploadPending().timeout(\n          const Duration(seconds: 45),\n        );\n      } catch (_) {}\n      try {\n        await MediaSyncService.downloadMissing().timeout(\n          const Duration(seconds: 45),\n        );\n      } catch (_) {}\n    })().whenComplete(() {\n"""
new_media_helper = """    operation = (() async {\n      try {\n        // Um único arquivo por ciclo automático evita disputar banda com o\n        // próximo pull estruturado. Recuperação de mídia continua sob demanda.\n        await MediaSyncService.uploadPending(limit: 1).timeout(\n          const Duration(seconds: 30),\n        );\n      } catch (_) {}\n    })().whenComplete(() {\n"""
dev = once(dev, old_media_helper, new_media_helper, 'helper de mídia pesado')

# uploadPending mantém 40 arquivos para ações manuais/reparo, mas aceita lote pequeno
# para a rotina automática de baixa prioridade.
media = once(
    media,
    '  static Future<MediaSyncSummary> uploadPending() async {\n',
    '  static Future<MediaSyncSummary> uploadPending({int limit = 40}) async {\n',
    'assinatura uploadPending',
)
media = once(
    media,
    """    await _discoverLocalMedia(db);\n\n    final rows = await db.query(\n""",
    """    await _discoverLocalMedia(db);\n    final batchLimit = limit < 1 ? 1 : (limit > 40 ? 40 : limit);\n\n    final rows = await db.query(\n""",
    'limite de lote de mídia',
)
media = once(media, '      limit: 40,\n', '      limit: batchLimit,\n', 'query de mídia limitada')

# 3) Home: v3.29.51 emite evento por página. Sem debounce isso pode abrir várias
#    consultas pesadas ao SQLite ao mesmo tempo durante backlog.
home = once(
    home,
    """  StreamSubscription<DeviceSyncResult>? _deviceSyncSubscription;\n  final ScrollController _mobileScrollController = ScrollController();\n""",
    """  StreamSubscription<DeviceSyncResult>? _deviceSyncSubscription;\n  Timer? _deviceRefreshDebounce;\n  final ScrollController _mobileScrollController = ScrollController();\n""",
    'campo debounce Home',
)
home = once(
    home,
    """    _deviceSyncSubscription = DeviceSyncService.events.listen((result) {\n      if (mounted && result.received > 0) {\n        unawaited(_refresh(showLoading: false));\n      }\n    });\n""",
    """    _deviceSyncSubscription = DeviceSyncService.events.listen((result) {\n      if (!mounted || result.received <= 0) return;\n      _deviceRefreshDebounce?.cancel();\n      _deviceRefreshDebounce = Timer(const Duration(milliseconds: 250), () {\n        if (mounted) unawaited(_refresh(showLoading: false));\n      });\n    });\n""",
    'listener Home',
)
home = once(
    home,
    """    _deviceSyncSubscription?.cancel();\n    _mobileScrollController.dispose();\n""",
    """    _deviceSyncSubscription?.cancel();\n    _deviceRefreshDebounce?.cancel();\n    _mobileScrollController.dispose();\n""",
    'dispose Home',
)

# 4) Empresas: atualizar a tela aberta assim que o banco receber dados.
if "import 'dart:async';" not in companies:
    companies = companies.replace("import 'dart:io';\n", "import 'dart:async';\nimport 'dart:io';\n", 1)
companies = once(
    companies,
    """class _CompaniesScreenState extends State<CompaniesScreen> {\n  final ImagePicker picker = ImagePicker();\n""",
    """class _CompaniesScreenState extends State<CompaniesScreen> {\n  StreamSubscription<DeviceSyncResult>? _deviceSyncSubscription;\n  Timer? _syncRefreshDebounce;\n  final ImagePicker picker = ImagePicker();\n""",
    'campos Empresas',
)
companies = once(
    companies,
    """    searchController.addListener(() => setState(() {}));\n    _load();\n""",
    """    searchController.addListener(() => setState(() {}));\n    _deviceSyncSubscription = DeviceSyncService.events.listen((result) {\n      if (!mounted || result.received <= 0) return;\n      _syncRefreshDebounce?.cancel();\n      _syncRefreshDebounce = Timer(const Duration(milliseconds: 250), () {\n        if (mounted) unawaited(_load());\n      });\n    });\n    _load();\n""",
    'listener Empresas',
)
companies = once(
    companies,
    """  void dispose() {\n    searchController.dispose();\n    super.dispose();\n  }\n""",
    """  void dispose() {\n    _deviceSyncSubscription?.cancel();\n    _syncRefreshDebounce?.cancel();\n    searchController.dispose();\n    super.dispose();\n  }\n""",
    'dispose Empresas',
)

# 5) Colaboradores: mesma atualização em tempo real, sem piscar loading a cada pull.
if "import 'dart:async';" not in workers:
    workers = "import 'dart:async';\n" + workers
if "../services/device_sync_service.dart" not in workers:
    workers = workers.replace(
        "import '../services/worker_import_service.dart';\n",
        "import '../services/device_sync_service.dart';\nimport '../services/worker_import_service.dart';\n",
        1,
    )
workers = once(
    workers,
    """class _WorkersScreenState extends State<WorkersScreen> {\n  final searchController = TextEditingController();\n""",
    """class _WorkersScreenState extends State<WorkersScreen> {\n  StreamSubscription<DeviceSyncResult>? _deviceSyncSubscription;\n  Timer? _syncRefreshDebounce;\n  final searchController = TextEditingController();\n""",
    'campos Colaboradores',
)
workers = once(
    workers,
    """  void initState() {\n    super.initState();\n    _initialize();\n  }\n""",
    """  void initState() {\n    super.initState();\n    _deviceSyncSubscription = DeviceSyncService.events.listen((result) {\n      if (!mounted || result.received <= 0) return;\n      _syncRefreshDebounce?.cancel();\n      _syncRefreshDebounce = Timer(const Duration(milliseconds: 250), () {\n        if (mounted) unawaited(_load(showLoading: false));\n      });\n    });\n    _initialize();\n  }\n""",
    'listener Colaboradores',
)
workers = once(
    workers,
    """  void dispose() {\n    searchController.dispose();\n    super.dispose();\n  }\n\n  Future<void> _load() async {\n    if (mounted) setState(() => loading = true);\n""",
    """  void dispose() {\n    _deviceSyncSubscription?.cancel();\n    _syncRefreshDebounce?.cancel();\n    searchController.dispose();\n    super.dispose();\n  }\n\n  Future<void> _load({bool showLoading = true}) async {\n    if (showLoading && mounted) setState(() => loading = true);\n""",
    'load/dispose Colaboradores',
)

# 6) Dashboard: atualizar empresas/indicadores mantendo filtros atuais.
if "import 'dart:async';" not in dash:
    dash = "import 'dart:async';\n" + dash
if "../services/device_sync_service.dart" not in dash:
    dash = dash.replace(
        "import '../models.dart';\n",
        "import '../models.dart';\nimport '../services/device_sync_service.dart';\n",
        1,
    )
dash = once(
    dash,
    """class _DashboardScreenState extends State<DashboardScreen> {\n  List<Company> companies = [];\n""",
    """class _DashboardScreenState extends State<DashboardScreen> {\n  StreamSubscription<DeviceSyncResult>? _deviceSyncSubscription;\n  Timer? _syncRefreshDebounce;\n  List<Company> companies = [];\n""",
    'campos Dashboard',
)
dash = once(
    dash,
    """  void initState() {\n    super.initState();\n    _loadInitial();\n  }\n\n  Future<void> _loadInitial() async {\n""",
    """  void initState() {\n    super.initState();\n    _deviceSyncSubscription = DeviceSyncService.events.listen((result) {\n      if (!mounted || result.received <= 0) return;\n      _syncRefreshDebounce?.cancel();\n      _syncRefreshDebounce = Timer(const Duration(milliseconds: 250), () {\n        if (mounted) unawaited(_refreshFromSync());\n      });\n    });\n    _loadInitial();\n  }\n\n  @override\n  void dispose() {\n    _deviceSyncSubscription?.cancel();\n    _syncRefreshDebounce?.cancel();\n    super.dispose();\n  }\n\n  Future<void> _loadInitial() async {\n""",
    'listener Dashboard',
)
dash = once(
    dash,
    """  Future<void> _refreshSummary() async {\n    if (mounted) {\n      setState(() => loading = true);\n    }\n""",
    """  Future<void> _refreshFromSync() async {\n    final loadedCompanies = await AppDatabase.instance.getCompanies();\n    if (!mounted) return;\n    setState(() => companies = loadedCompanies);\n    await _refreshSummary(showLoading: false);\n  }\n\n  Future<void> _refreshSummary({bool showLoading = true}) async {\n    if (showLoading && mounted) {\n      setState(() => loading = true);\n    }\n""",
    'refresh Dashboard',
)

# Persistir arquivos.
for path, text in [
    (pubp, pub),
    (coordp, coord),
    (devp, dev),
    (mediap, media),
    (homep, home),
    (companiesp, companies),
    (workersp, workers),
    (dashp, dash),
]:
    path.write_text(text, encoding='utf-8', newline='\n')

# Regressões essenciais.
assert 'version: 3.29.58+200' in pub
assert 'const Duration(seconds: 2)' in coord
assert 'const Duration(seconds: 5)' in coord
assert "'limit': 500," in dev
assert '_lastAutoMediaKick' in dev
assert 'MediaSyncService.uploadPending(limit: 1)' in dev
assert 'MediaSyncService.downloadMissing().timeout' not in dev
assert 'uploadPending({int limit = 40})' in media
assert 'limit: batchLimit' in media
assert '_deviceRefreshDebounce' in home
assert '_syncRefreshDebounce' in companies
assert '_syncRefreshDebounce' in workers
assert '_syncRefreshDebounce' in dash
assert 'DeviceSyncService.events.listen' in companies
assert 'DeviceSyncService.events.listen' in workers
assert 'DeviceSyncService.events.listen' in dash
print('Android v3.29.58+200: sync rápido restaurado, pull 5 s, mídia baixa prioridade e telas com atualização imediata.')

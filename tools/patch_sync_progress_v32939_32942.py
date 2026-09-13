#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
if platform not in {'android', 'windows'}:
    raise SystemExit('Uso: patch_sync_progress_v32939_32942.py <app_dir> <android|windows>')

pubp = root / 'pubspec.yaml'
syncp = root / 'lib/services/device_sync_service.dart'
screenp = root / 'lib/screens/data_safety_screen.dart'

pub = pubp.read_text(encoding='utf-8')
sync = syncp.read_text(encoding='utf-8')

expected = 'version: 3.29.38+180' if platform == 'android' else 'version: 3.29.41+183'
target = 'version: 3.29.39+181' if platform == 'android' else 'version: 3.29.42+184'
if target not in pub:
    if expected not in pub:
        raise RuntimeError(f'Versão base ausente: {expected}')
    pub = pub.replace(expected, target, 1)

progress_model = '''class DeviceSyncProgress {
  final int percent;
  final String phase;
  final int pending;
  final bool running;

  const DeviceSyncProgress({
    required this.percent,
    required this.phase,
    this.pending = 0,
    this.running = true,
  });
}

'''
marker = '/// Sincronização automática dos dados estruturados entre celular e computador.'
if 'class DeviceSyncProgress' not in sync:
    if marker not in sync:
        raise RuntimeError('Marcador do serviço de sincronização não encontrado')
    sync = sync.replace(marker, progress_model + marker, 1)

stream_marker = '  static Stream<DeviceSyncResult> get events => _events.stream;\n'
progress_stream = '''  static final StreamController<DeviceSyncProgress> _progressEvents =
      StreamController<DeviceSyncProgress>.broadcast();
  static DeviceSyncProgress _lastProgress = const DeviceSyncProgress(
    percent: 0,
    phase: 'Aguardando sincronização',
    running: false,
  );

  static Stream<DeviceSyncProgress> get progressEvents => _progressEvents.stream;
  static DeviceSyncProgress get lastProgress => _lastProgress;

  static void _emitProgress(
    int percent,
    String phase, {
    int pending = 0,
    bool running = true,
  }) {
    final safePercent = percent < 0 ? 0 : (percent > 100 ? 100 : percent);
    final progress = DeviceSyncProgress(
      percent: safePercent,
      phase: phase,
      pending: pending < 0 ? 0 : pending,
      running: running,
    );
    _lastProgress = progress;
    _progressEvents.add(progress);
  }

'''
if 'static Stream<DeviceSyncProgress> get progressEvents' not in sync:
    if stream_marker not in sync:
        raise RuntimeError('Stream de eventos original não encontrado')
    sync = sync.replace(stream_marker, stream_marker + '\n' + progress_stream, 1)

start_marker = '    final appDb = AppDatabase.instance;\n    try {'
if "_emitProgress(2, 'Preparando sincronização');" not in sync:
    if start_marker not in sync:
        raise RuntimeError('Início da sincronização não encontrado')
    sync = sync.replace(
        start_marker,
        "    final appDb = AppDatabase.instance;\n    _emitProgress(2, 'Preparando sincronização');\n    try {",
        1,
    )

skip_marker = '''      if (!force && !await _attemptIsDue(appDb)) {
        return const DeviceSyncResult(skipped: true);
      }
'''
if "'Sincronização já está atualizada'" not in sync:
    if skip_marker not in sync:
        raise RuntimeError('Bloco de sincronização não devida não encontrado')
    sync = sync.replace(
        skip_marker,
        '''      if (!force && !await _attemptIsDue(appDb)) {
        _emitProgress(
          100,
          'Sincronização já está atualizada',
          running: false,
        );
        return const DeviceSyncResult(skipped: true);
      }
''',
        1,
    )

uri_marker = '      final uri = Uri.parse(endpoint);\n\n      var sent = 0;'
if 'final initialPending = await pendingChangesCount();' not in sync:
    if uri_marker not in sync:
        raise RuntimeError('Marcador após endpoint não encontrado')
    sync = sync.replace(
        uri_marker,
        '''      final uri = Uri.parse(endpoint);
      final initialPending = await pendingChangesCount();
      _emitProgress(
        10,
        initialPending > 0
            ? 'Preparando envio de $initialPending alteração(ões)'
            : 'Verificando alterações locais',
        pending: initialPending,
      );

      var sent = 0;''',
        1,
    )

push_marker = '''        sent += await _pushChangesSafely(
          db: db,
          endpoint: uri,
          syncKey: syncKey,
          deviceId: deviceId,
          changes: changes,
          timeout: force
              ? const Duration(seconds: 45)
              : const Duration(seconds: 35),
        );
'''
if "'Enviando dados • $sent/$initialPending'" not in sync:
    if push_marker not in sync:
        # Android can have a fixed timeout after the same recovery patch.
        push_marker = '''        sent += await _pushChangesSafely(
          db: db,
          endpoint: uri,
          syncKey: syncKey,
          deviceId: deviceId,
          changes: changes,
          timeout: const Duration(seconds: 30),
        );
'''
    if push_marker not in sync:
        raise RuntimeError('Bloco de envio seguro não encontrado')
    sync = sync.replace(
        push_marker,
        push_marker + '''        final remaining = initialPending > sent ? initialPending - sent : 0;
        final calculated = initialPending <= 0
            ? 65
            : 10 + ((sent * 55) ~/ initialPending);
        _emitProgress(
          calculated > 65 ? 65 : calculated,
          'Enviando dados • $sent/$initialPending',
          pending: remaining,
        );
''',
        1,
    )

pull_start = '      var received = 0;\n'
if "_emitProgress(68, 'Verificando dados da Central'" not in sync:
    if pull_start not in sync:
        raise RuntimeError('Início do recebimento não encontrado')
    sync = sync.replace(
        pull_start,
        "      _emitProgress(68, 'Verificando dados da Central', pending: await pendingChangesCount());\n\n" + pull_start,
        1,
    )

pull_progress_marker = '''        remoteHasMore = response['hasMore'] == true;
        if (!remoteHasMore) break;
'''
if "'Recebendo atualizações da Central'" not in sync:
    if pull_progress_marker not in sync:
        raise RuntimeError('Marcador de paginação remota não encontrado')
    sync = sync.replace(
        pull_progress_marker,
        '''        remoteHasMore = response['hasMore'] == true;
        final receivePercent = 68 + (((page + 1) * 22) ~/ pullPages);
        _emitProgress(
          receivePercent > 90 ? 90 : receivePercent,
          remoteHasMore
              ? 'Recebendo atualizações da Central'
              : 'Dados da Central verificados',
          pending: await pendingChangesCount(),
        );
        if (!remoteHasMore) break;
''',
        1,
    )

media_marker = '''      if (syncMedia) {
        try {
          await MediaSyncService.downloadMissing();
'''
if "'Atualizando fotos e assinaturas'" not in sync:
    if media_marker not in sync:
        raise RuntimeError('Bloco de mídia não encontrado')
    sync = sync.replace(
        media_marker,
        '''      if (syncMedia) {
        _emitProgress(
          92,
          'Atualizando fotos e assinaturas',
          pending: await pendingChangesCount(),
        );
        try {
          await MediaSyncService.downloadMissing();
''',
        1,
    )

final_marker = '      final pending = await pendingChangesCount();\n'
if "_emitProgress(96, 'Finalizando sincronização'" not in sync:
    if final_marker not in sync:
        raise RuntimeError('Finalização da sincronização não encontrada')
    sync = sync.replace(
        final_marker,
        "      _emitProgress(96, 'Finalizando sincronização', pending: await pendingChangesCount());\n" + final_marker,
        1,
    )

result_marker = '''      _events.add(result);
      return result;
'''
if "'Sincronização concluída'" not in sync.split(result_marker)[0][-1200:]:
    if result_marker not in sync:
        raise RuntimeError('Retorno final da sincronização não encontrado')
    sync = sync.replace(
        result_marker,
        '''      _events.add(result);
      _emitProgress(
        100,
        partial
            ? 'Ciclo concluído • $pending pendente(s)'
            : 'Sincronização concluída',
        pending: pending,
        running: false,
      );
      return result;
''',
        1,
    )

catch_marker = '''    } catch (error) {
      await appDb.setSetting(_lastStatusSetting, 'Sincronização pendente');
'''
if "'Sincronização interrompida'" not in sync:
    if catch_marker not in sync:
        raise RuntimeError('Catch de sincronização não encontrado')
    sync = sync.replace(
        catch_marker,
        '''    } catch (error) {
      _emitProgress(
        _lastProgress.percent,
        'Sincronização interrompida',
        pending: _lastProgress.pending,
        running: false,
      );
      await appDb.setSetting(_lastStatusSetting, 'Sincronização pendente');
''',
        1,
    )

screen = r'''import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';

import '../brand.dart';
import '../database.dart';
import '../services/backup_service.dart';
import '../services/device_sync_service.dart';
import '../services/media_sync_service.dart';

class DataSafetyScreen extends StatefulWidget {
  const DataSafetyScreen({super.key});

  @override
  State<DataSafetyScreen> createState() => _DataSafetyScreenState();
}

class _DataSafetyScreenState extends State<DataSafetyScreen> {
  bool loading = true;
  bool busy = false;
  bool syncRunning = false;
  int syncPercent = 0;
  String syncPhase = '';
  String loadMessage = 'Carregando status…';
  String structuredStatus = '';
  String structuredLast = '';
  String structuredError = '';
  int structuredPending = 0;
  int mediaPending = 0;
  int reportPending = 0;
  String mediaLast = '';
  String mediaError = '';
  String backupLast = '';
  int backupCount = 0;
  StreamSubscription<DeviceSyncProgress>? _progressSubscription;

  @override
  void initState() {
    super.initState();
    final last = DeviceSyncService.lastProgress;
    syncPercent = Platform.isWindows ? ((last.percent * 90) ~/ 100) : last.percent;
    syncPhase = last.phase;
    syncRunning = last.running;
    _progressSubscription = DeviceSyncService.progressEvents.listen((progress) {
      if (!mounted) return;
      final shownPercent = Platform.isWindows
          ? ((progress.percent * 90) ~/ 100)
          : progress.percent;
      setState(() {
        syncPercent = shownPercent.clamp(0, 100);
        syncPhase = progress.phase;
        syncRunning = progress.running;
        structuredPending = progress.pending;
      });
    });
    unawaited(_load());
  }

  @override
  void dispose() {
    _progressSubscription?.cancel();
    super.dispose();
  }

  Future<T> _safe<T>(
    Future<T> Function() task,
    T fallback, {
    Duration timeout = const Duration(seconds: 4),
  }) async {
    try {
      return await task().timeout(timeout);
    } catch (_) {
      return fallback;
    }
  }

  Future<void> _load() async {
    if (!mounted) return;
    setState(() {
      loading = true;
      loadMessage = 'Atualizando informações…';
    });

    final db = AppDatabase.instance;
    final results = await Future.wait<Object?>([
      _safe<Map<String, Object?>>(
        () => BackupService.backupStatus(),
        <String, Object?>{'count': backupCount, 'latestAt': backupLast},
      ),
      _safe<int>(() => DeviceSyncService.pendingChangesCount(), structuredPending),
      _safe<int>(() => MediaSyncService.pendingCount(), mediaPending),
      _safe<int>(() => db.pendingDriveUploadsCount(), reportPending),
      _safe<String>(
        () => db.getSetting(
          'last_device_sync_status',
          fallback: 'Aguardando a primeira sincronização',
        ),
        structuredStatus.isEmpty
            ? 'Status temporariamente indisponível'
            : structuredStatus,
      ),
      _safe<String>(() => db.getSetting('last_device_sync_success'), structuredLast),
      _safe<String>(() => db.getSetting('last_device_sync_error'), structuredError),
      _safe<String>(() => db.getSetting('media_sync_last_success'), mediaLast),
      _safe<String>(() => db.getSetting('media_sync_last_error'), mediaError),
    ]);

    if (!mounted) return;
    final info = results[0] as Map<String, Object?>;
    setState(() {
      structuredPending = results[1] as int;
      mediaPending = results[2] as int;
      reportPending = results[3] as int;
      structuredStatus = results[4] as String;
      structuredLast = results[5] as String;
      structuredError = results[6] as String;
      mediaLast = results[7] as String;
      mediaError = results[8] as String;
      backupLast = '${info['latestAt'] ?? backupLast}';
      backupCount = (info['count'] as int?) ?? backupCount;
      loading = false;
      loadMessage = '';
    });
  }

  String _date(String value) {
    final parsed = DateTime.tryParse(value)?.toLocal();
    if (parsed == null) return 'Ainda não concluído';
    String two(int number) => number.toString().padLeft(2, '0');
    return '${two(parsed.day)}/${two(parsed.month)}/${parsed.year} '
        '${two(parsed.hour)}:${two(parsed.minute)}';
  }

  Future<void> _syncNow() async {
    if (busy || syncRunning) return;
    final pending = await _safe<int>(
      () => DeviceSyncService.pendingChangesCount(),
      structuredPending,
    );
    if (!mounted) return;
    setState(() {
      busy = true;
      syncRunning = true;
      syncPercent = 1;
      syncPhase = pending > 0
          ? 'Preparando $pending alteração(ões) para envio'
          : 'Verificando atualizações';
      structuredPending = pending;
    });

    try {
      final structured = await DeviceSyncService.synchronize(
        force: true,
        syncMedia: !Platform.isWindows,
      ).timeout(const Duration(seconds: 120));

      if (Platform.isWindows && !structured.partial) {
        if (mounted) {
          setState(() {
            syncRunning = true;
            syncPercent = 92;
            syncPhase = 'Sincronizando fotos e assinaturas';
          });
        }
        try {
          await MediaSyncService.syncBackgroundBatch(
            uploadLimit: 5,
            downloadLimit: 8,
          ).timeout(const Duration(seconds: 50));
        } catch (_) {}
        if (mounted) {
          setState(() {
            syncPercent = 98;
            syncPhase = 'Atualizando status final';
          });
        }
      }

      if (mounted) {
        setState(() {
          syncPercent = 100;
          syncRunning = false;
          syncPhase = structured.partial
              ? 'Ciclo concluído • ${structured.pending} pendente(s)'
              : 'Sincronização concluída';
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              structured.partial
                  ? 'Sincronização parcial. ${structured.pending} alteração(ões) continuam pendentes.'
                  : 'Sincronização concluída.',
            ),
          ),
        );
      }
    } on TimeoutException {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'A sincronização continua em segundo plano. O progresso permanecerá visível nesta tela.',
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          syncRunning = false;
          syncPhase = 'Sincronização pendente';
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString().replaceFirst('Bad state: ', ''))),
        );
      }
    } finally {
      if (mounted) setState(() => busy = false);
      unawaited(_load());
    }
  }

  Future<void> _backupNow() async {
    if (busy || syncRunning) return;
    setState(() => busy = true);
    try {
      final path = await BackupService.createBackup()
          .timeout(const Duration(minutes: 3));
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Backup criado: ${File(path).uri.pathSegments.last}')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Falha no backup: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => busy = false);
      unawaited(_load());
    }
  }

  Widget _syncProgressCard() {
    final visible = syncRunning || syncPercent > 0;
    if (!visible) return const SizedBox.shrink();
    final value = syncPercent.clamp(0, 100) / 100.0;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  syncRunning ? Icons.sync : Icons.cloud_done_outlined,
                  color: syncRunning ? AuditarBrand.navy : AuditarBrand.green,
                ),
                const SizedBox(width: 10),
                const Expanded(
                  child: Text(
                    'Progresso da sincronização',
                    style: TextStyle(fontWeight: FontWeight.w800),
                  ),
                ),
                Text(
                  '$syncPercent%',
                  style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 18),
                ),
              ],
            ),
            const SizedBox(height: 10),
            ClipRRect(
              borderRadius: BorderRadius.circular(999),
              child: LinearProgressIndicator(value: value, minHeight: 10),
            ),
            const SizedBox(height: 8),
            Text(syncPhase.isEmpty ? 'Aguardando sincronização' : syncPhase),
            if (syncRunning && structuredPending > 0) ...[
              const SizedBox(height: 3),
              Text(
                '$structuredPending alteração(ões) ainda aguardando envio',
                style: const TextStyle(fontSize: 12.5, color: Colors.black54),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _statusCard({
    required IconData icon,
    required String title,
    required String main,
    required String detail,
    bool warning = false,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: warning ? Colors.deepOrange : AuditarBrand.green),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
                  const SizedBox(height: 4),
                  Text(main),
                  const SizedBox(height: 3),
                  Text(
                    detail,
                    style: const TextStyle(fontSize: 12.5, color: Colors.black54),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Segurança dos dados')),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(14, 14, 14, 28),
          children: [
            if (loading) ...[
              ClipRRect(
                borderRadius: BorderRadius.circular(999),
                child: const LinearProgressIndicator(minHeight: 4),
              ),
              const SizedBox(height: 6),
              Text(
                loadMessage,
                style: const TextStyle(fontSize: 12, color: Colors.black54),
              ),
              const SizedBox(height: 8),
            ],
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AuditarBrand.navy,
                borderRadius: BorderRadius.circular(18),
              ),
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Proteção e recuperação',
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w900,
                      fontSize: 18,
                    ),
                  ),
                  SizedBox(height: 6),
                  Text(
                    'O app mantém o trabalho local para uso offline, sincroniza os dados estruturados e também envia fotos e assinaturas para a Central/Drive.',
                    style: TextStyle(color: Colors.white70, height: 1.35),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 10),
            _syncProgressCard(),
            if (syncRunning || syncPercent > 0) const SizedBox(height: 2),
            _statusCard(
              icon: structuredPending == 0
                  ? Icons.cloud_done_outlined
                  : Icons.sync_problem_outlined,
              title: 'Dados do aplicativo',
              main: structuredPending == 0
                  ? structuredStatus
                  : '$structuredPending alteração(ões) aguardando envio',
              detail:
                  'Última conclusão: ${_date(structuredLast)}${structuredError.isEmpty ? '' : ' • $structuredError'}',
              warning: structuredPending > 0 || structuredError.isNotEmpty,
            ),
            _statusCard(
              icon: mediaPending == 0
                  ? Icons.photo_library_outlined
                  : Icons.cloud_upload_outlined,
              title: 'Fotos e assinaturas',
              main: mediaPending == 0
                  ? 'Evidências locais protegidas/sincronizadas'
                  : '$mediaPending arquivo(s) aguardando envio',
              detail:
                  'Última movimentação: ${_date(mediaLast)}${mediaError.isEmpty ? '' : ' • $mediaError'}',
              warning: mediaPending > 0 || mediaError.isNotEmpty,
            ),
            _statusCard(
              icon: reportPending == 0
                  ? Icons.picture_as_pdf_outlined
                  : Icons.pending_actions_outlined,
              title: 'Relatórios PDF',
              main: reportPending == 0
                  ? 'Nenhum envio pendente'
                  : '$reportPending relatório(s) aguardando Drive',
              detail: 'Os relatórios continuam salvos localmente até o envio.',
              warning: reportPending > 0,
            ),
            _statusCard(
              icon: backupCount > 0
                  ? Icons.backup_outlined
                  : Icons.warning_amber_rounded,
              title: 'Backup local automático',
              main: backupCount > 0
                  ? '$backupCount backup(s) disponível(is)'
                  : 'Nenhum backup automático encontrado',
              detail:
                  'Último backup: ${_date(backupLast)} • retenção automática de até 7 cópias.',
              warning: backupCount == 0,
            ),
            const SizedBox(height: 10),
            FilledButton.icon(
              onPressed: (busy || syncRunning) ? null : _syncNow,
              icon: const Icon(Icons.sync),
              label: Text(
                syncRunning
                    ? 'Sincronizando • $syncPercent%'
                    : busy
                        ? 'Aguarde...'
                        : 'Sincronizar tudo agora',
              ),
            ),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: (busy || syncRunning) ? null : _backupNow,
              icon: const Icon(Icons.backup_outlined),
              label: const Text('Criar backup agora'),
            ),
            const SizedBox(height: 10),
            const Text(
              'Importante: o backup local protege contra erro e permite restauração manual. Para perda completa do aparelho, a recuperação depende do que já tiver sido sincronizado com a Central/Drive.',
              style: TextStyle(fontSize: 12.5, color: Colors.black54, height: 1.35),
            ),
          ],
        ),
      ),
    );
  }
}
'''

pubp.write_text(pub, encoding='utf-8', newline='\n')
syncp.write_text(sync, encoding='utf-8', newline='\n')
screenp.write_text(screen, encoding='utf-8', newline='\n')

assert target in pubp.read_text(encoding='utf-8')
final_sync = syncp.read_text(encoding='utf-8')
final_screen = screenp.read_text(encoding='utf-8')
assert 'class DeviceSyncProgress' in final_sync
assert 'progressEvents' in final_sync
assert "'Enviando dados • $sent/$initialPending'" in final_sync
assert "'Sincronização concluída'" in final_sync
assert 'Progresso da sincronização' in final_screen
assert 'CircularProgressIndicator' not in final_screen
assert 'LinearProgressIndicator(value: value' in final_screen
print(f'Progresso percentual aplicado em {platform}: {target}')

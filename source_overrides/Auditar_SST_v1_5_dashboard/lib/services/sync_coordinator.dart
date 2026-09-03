import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/material.dart';

import '../database.dart';
import 'device_sync_service.dart';
import 'drive_service.dart';
import 'management_panel_service.dart';

class SyncCoordinator extends StatefulWidget {
  final Widget child;

  const SyncCoordinator({
    super.key,
    required this.child,
  });

  @override
  State<SyncCoordinator> createState() => _SyncCoordinatorState();
}

class _SyncCoordinatorState extends State<SyncCoordinator>
    with WidgetsBindingObserver {
  StreamSubscription<List<ConnectivityResult>>? _subscription;
  Timer? _automaticTimer;
  Timer? _maintenanceTimer;
  bool _syncing = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);

    _subscription = Connectivity()
        .onConnectivityChanged
        .listen(_handleConnectivity);

    // Verifica os dados com frequência enquanto celular e PC estão abertos.
    _automaticTimer = Timer.periodic(
      const Duration(seconds: 20),
      (_) => _trySync(deviceOnly: true),
    );

    // Tarefas mais pesadas permanecem em um intervalo separado.
    _maintenanceTimer = Timer.periodic(
      const Duration(minutes: 2),
      (_) => _trySync(),
    );

    WidgetsBinding.instance.addPostFrameCallback((_) {
      _trySync();
    });
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _subscription?.cancel();
    _automaticTimer?.cancel();
    _maintenanceTimer?.cancel();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _trySync();
    }
  }

  void _handleConnectivity(List<ConnectivityResult> results) {
    final hasNetwork = results.any(
      (result) => result != ConnectivityResult.none,
    );

    if (hasNetwork) {
      _trySync();
    }
  }

  Future<void> _trySync({bool deviceOnly = false}) async {
    if (_syncing) return;

    final connectivity = await Connectivity().checkConnectivity();
    if (!connectivity.any((result) => result != ConnectivityResult.none)) {
      return;
    }

    _syncing = true;

    try {
      try {
        await DeviceSyncService.synchronize();
      } catch (_) {
        // O aplicativo segue offline e tenta novamente automaticamente.
      }
      if (!deviceOnly) {
        await _syncManagementPanelsIfNeeded();
        await _syncDriveIfNeeded();
      }
    } finally {
      _syncing = false;
    }
  }

  Future<void> _syncManagementPanelsIfNeeded() async {
    final db = AppDatabase.instance;
    final autoSync = await db.getSetting(
      'management_panel_auto_sync',
      fallback: 'true',
    );
    final endpoint = await db.getSetting('management_panel_endpoint');
    final syncKey = await db.getSetting('management_panel_sync_key');
    if (autoSync != 'true' ||
        endpoint.trim().isEmpty ||
        syncKey.trim().isEmpty) {
      return;
    }

    final lastValue = await db.getSetting('last_automatic_panel_sync');
    final last = DateTime.tryParse(lastValue);
    if (last != null &&
        DateTime.now().difference(last) < const Duration(minutes: 5)) {
      return;
    }

    final companies = await db.getCompanies();
    var attempted = false;
    var allSuccessful = true;
    for (final company in companies) {
      final panel = await db.ensureManagementPanel(company.id);
      if ((panel['enabled'] as int? ?? 1) != 1) continue;
      attempted = true;
      final result = await ManagementPanelService.syncCompany(company);
      if (!result.success) allSuccessful = false;
    }
    if (attempted && allSuccessful) {
      await db.setSetting(
        'last_automatic_panel_sync',
        DateTime.now().toIso8601String(),
      );
    }
  }

  Future<void> _syncDriveIfNeeded() async {
    final db = AppDatabase.instance;

    final driveEnabled = await db.getSetting(
      'drive_enabled',
      fallback: 'false',
    );

    final autoUpload = await db.getSetting(
      'drive_auto_upload',
      fallback: 'true',
    );

    if (driveEnabled != 'true' || autoUpload != 'true') {
      return;
    }

    final pending = await db.pendingDriveUploadsCount();
    if (pending == 0) return;

    try {
      // Não abre tela de login. Usa apenas autenticação leve já autorizada.
      await DriveService.syncPending(interactive: false);
    } catch (_) {
      // Os itens continuam na fila para a próxima tentativa.
    }
  }

  @override
  Widget build(BuildContext context) => widget.child;
}

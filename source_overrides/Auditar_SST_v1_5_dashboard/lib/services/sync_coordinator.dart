import 'dart:async';
import 'dart:io';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/material.dart';

import '../brand.dart';
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
  Timer? _indicatorTimer;
  bool _syncing = false;
  bool _showIndicator = false;
  String _statusLabel = '';
  _SyncTone _statusTone = _SyncTone.neutral;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);

    _subscription = Connectivity()
        .onConnectivityChanged
        .listen(_handleConnectivity);

    _automaticTimer = Timer.periodic(
      const Duration(seconds: 20),
      (_) => _trySync(deviceOnly: true),
    );

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
    _indicatorTimer?.cancel();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _trySync();
    }
  }

  void _setDesktopStatus({
    required String label,
    required _SyncTone tone,
  }) {
    if (!Platform.isWindows || !mounted) return;

    _indicatorTimer?.cancel();
    setState(() {
      _statusLabel = label;
      _statusTone = tone;
      _showIndicator = tone != _SyncTone.neutral;
    });

    if (tone == _SyncTone.ok) {
      _indicatorTimer = Timer(const Duration(seconds: 3), () {
        if (!mounted || _statusTone != _SyncTone.ok) return;
        setState(() => _showIndicator = false);
      });
    }
  }

  void _handleConnectivity(List<ConnectivityResult> results) {
    final hasNetwork = results.any(
      (result) => result != ConnectivityResult.none,
    );

    if (!hasNetwork) {
      _setDesktopStatus(
        label: 'Offline',
        tone: _SyncTone.offline,
      );
      return;
    }

    _trySync();
  }

  Future<void> _trySync({bool deviceOnly = false}) async {
    if (_syncing) return;

    final connectivity = await Connectivity().checkConnectivity();
    final hasNetwork = connectivity.any(
      (result) => result != ConnectivityResult.none,
    );
    if (!hasNetwork) {
      _setDesktopStatus(
        label: 'Offline',
        tone: _SyncTone.offline,
      );
      return;
    }

    _syncing = true;
    _setDesktopStatus(
      label: '',
      tone: _SyncTone.syncing,
    );

    try {
      DeviceSyncResult? result;
      try {
        result = await DeviceSyncService.synchronize();
      } catch (_) {
        _setDesktopStatus(
          label: 'Erro ao sincronizar',
          tone: _SyncTone.warning,
        );
      }

      if (result != null) {
        _setDesktopStatus(
          label: '',
          tone: _SyncTone.ok,
        );
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
      await DriveService.syncPending(interactive: false);
    } catch (_) {
      // Os itens continuam na fila para a próxima tentativa.
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!Platform.isWindows || !_showIndicator) {
      return widget.child;
    }

    return Stack(
      children: [
        widget.child,
        Positioned(
          right: 18,
          bottom: 16,
          child: IgnorePointer(
            child: _SyncIndicator(
              label: _statusLabel,
              tone: _statusTone,
            ),
          ),
        ),
      ],
    );
  }
}

enum _SyncTone { neutral, syncing, ok, warning, offline }

class _SyncIndicator extends StatelessWidget {
  final String label;
  final _SyncTone tone;

  const _SyncIndicator({
    required this.label,
    required this.tone,
  });

  @override
  Widget build(BuildContext context) {
    final (Color background, Color foreground, IconData icon) = switch (tone) {
      _SyncTone.ok => (
          AuditarBrand.greenSoft,
          AuditarBrand.greenDark,
          Icons.check_rounded,
        ),
      _SyncTone.syncing => (
          AuditarBrand.navySoft,
          AuditarBrand.navy,
          Icons.sync_rounded,
        ),
      _SyncTone.warning => (
          const Color(0xFFFFF4E1),
          const Color(0xFF9A5A00),
          Icons.cloud_sync_outlined,
        ),
      _SyncTone.offline => (
          const Color(0xFFF1F3F5),
          const Color(0xFF5F6670),
          Icons.cloud_off_outlined,
        ),
      _ => (
          const Color(0xFFF1F3F5),
          const Color(0xFF5F6670),
          Icons.cloud_outlined,
        ),
    };

    final showText = tone == _SyncTone.warning || tone == _SyncTone.offline;

    return Material(
      color: Colors.transparent,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        constraints: BoxConstraints(maxWidth: showText ? 180 : 36),
        width: showText ? null : 36,
        height: 36,
        padding: EdgeInsets.symmetric(horizontal: showText ? 10 : 0),
        decoration: BoxDecoration(
          color: background.withValues(alpha: .96),
          borderRadius: BorderRadius.circular(999),
          border: Border.all(color: foreground.withValues(alpha: .18)),
          boxShadow: const [
            BoxShadow(
              color: Color(0x140E1A43),
              blurRadius: 8,
              offset: Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (tone == _SyncTone.syncing)
              SizedBox(
                width: 15,
                height: 15,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: foreground,
                ),
              )
            else
              Icon(icon, size: 17, color: foreground),
            if (showText) ...[
              const SizedBox(width: 6),
              Flexible(
                child: Text(
                  label,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: foreground,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

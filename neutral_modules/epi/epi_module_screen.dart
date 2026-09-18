import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';
import 'package:webview_flutter_windows/webview_flutter_windows.dart' as win;

import '../database.dart';
import '../services/auth_service.dart';

class EpiModuleScreen extends StatefulWidget {
  const EpiModuleScreen({super.key});

  @override
  State<EpiModuleScreen> createState() => _EpiModuleScreenState();
}

class _EpiModuleScreenState extends State<EpiModuleScreen> {
  static const _endpoint = String.fromEnvironment('SST_APPS_SCRIPT_URL');
  static const _syncKey = String.fromEnvironment('SST_SYNC_KEY');

  WebViewController? _androidController;
  win.WebviewController? _windowsController;
  bool _management = Platform.isWindows;
  bool _loading = true;
  String _error = '';

  @override
  void initState() {
    super.initState();
    _open();
  }

  Future<Map<String, dynamic>> _bootstrap() async {
    final db = AppDatabase.instance;
    final companies = await db.getCompanies(onlyActive: false);
    final companyRows = <Map<String, dynamic>>[];
    final workerRows = <Map<String, dynamic>>[];

    for (final company in companies) {
      final map = Map<String, Object?>.from(company.toMap());
      final companyId = map['id']?.toString() ?? '';
      companyRows.add({
        'id': companyId,
        'name': map['name']?.toString() ?? '',
        'cnpj': map['cnpj']?.toString() ?? '',
        'active': (map['active'] ?? 1).toString() != '0',
      });

      final sectors = await db.getSectors(companyId, onlyActive: false);
      final sectorNames = <String, String>{};
      for (final sector in sectors) {
        final sectorMap = Map<String, Object?>.from(sector.toMap());
        sectorNames[sectorMap['id']?.toString() ?? ''] =
            sectorMap['name']?.toString() ?? '';
      }

      final workers = await db.getWorkers(
        companyId: companyId,
        onlyActive: false,
      );
      for (final worker in workers) {
        final workerMap = Map<String, Object?>.from(worker.toMap());
        final sectorId = workerMap['sector_id']?.toString() ?? '';
        workerRows.add({
          'id': workerMap['id']?.toString() ?? '',
          'companyId': workerMap['company_id']?.toString() ?? companyId,
          'name': workerMap['name']?.toString() ?? '',
          'cpf': workerMap['cpf']?.toString() ?? '',
          'reg': '',
          'role': workerMap['role']?.toString() ?? '',
          'sector': sectorNames[sectorId] ?? '',
          'active': (workerMap['active'] ?? 1).toString() != '0',
        });
      }
    }

    final user = AuthService.currentUser;
    return {
      'companies': companyRows,
      'workers': workerRows,
      'user': user == null
          ? null
          : {
              'id': user.id,
              'name': user.name,
              'role': user.role,
            },
    };
  }

  Future<String> _html() async {
    if (_endpoint.isEmpty || _syncKey.isEmpty) {
      throw StateError(
        'A Central SST Gestão ainda não foi configurada para o módulo de EPI.',
      );
    }

    final asset = _management
        ? 'assets/epi_module/management.html'
        : 'assets/epi_module/field.html';

    var html = await rootBundle.loadString(asset);
    html = html
        .replaceAll('__SST_EPI_ENDPOINT_JSON__', jsonEncode(_endpoint))
        .replaceAll('__SST_EPI_SYNC_KEY_JSON__', jsonEncode(_syncKey))
        .replaceAll(
          '__SST_EPI_BOOTSTRAP_JSON__',
          jsonEncode(await _bootstrap()),
        );
    return html;
  }

  Future<void> _open() async {
    if (mounted) {
      setState(() {
        _loading = true;
        _error = '';
      });
    }

    try {
      final html = await _html();

      if (Platform.isWindows) {
        _windowsController ??= win.WebviewController();
        if (!_windowsController!.value.isInitialized) {
          await _windowsController!.initialize();
          await _windowsController!.setPopupWindowPolicy(
            win.WebviewPopupWindowPolicy.deny,
          );
          await _windowsController!.setDefaultContextMenusEnabled(true);
        }
        await _windowsController!.loadStringContent(html);
      } else {
        final controller = _androidController ??= WebViewController()
          ..setJavaScriptMode(JavaScriptMode.unrestricted)
          ..addJavaScriptChannel(
            'SSTNative',
            onMessageReceived: (message) async {
              final value = message.message.trim().toLowerCase();
              if (value == 'orientation:landscape') {
                await SystemChrome.setPreferredOrientations(const [
                  DeviceOrientation.landscapeLeft,
                  DeviceOrientation.landscapeRight,
                ]);
              } else if (value == 'orientation:portrait') {
                await SystemChrome.setPreferredOrientations(const [
                  DeviceOrientation.portraitUp,
                ]);
              } else if (value == 'orientation:auto') {
                await SystemChrome.setPreferredOrientations(DeviceOrientation.values);
              }
            },
          )
          ..setNavigationDelegate(
            NavigationDelegate(
              onWebResourceError: (error) {
                if (error.isForMainFrame == true && mounted) {
                  setState(() => _error = error.description);
                }
              },
            ),
          );

        if (controller.platform is AndroidWebViewController) {
          final android = controller.platform as AndroidWebViewController;
          await android.setOnPlatformPermissionRequest((request) {
            request.grant();
          });
        }

        if (!_management) {
          await Permission.camera.request();
        }

        await controller.loadHtmlString(html);
      }

      if (mounted) {
        setState(() => _loading = false);
      }
    } catch (error) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = error.toString();
        });
      }
    }
  }

  Future<void> _setMode(bool management) async {
    if (_management == management) return;
    setState(() => _management = management);
    await _open();
  }

  @override
  void dispose() {
    _windowsController?.dispose();
    if (!Platform.isWindows) {
      SystemChrome.setPreferredOrientations(DeviceOrientation.values);
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F8FA),
      appBar: AppBar(
        titleSpacing: 12,
        title: Row(
          children: [
            Container(
              width: 34,
              height: 34,
              decoration: BoxDecoration(
                color: const Color(0xFFE8F8F5),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(
                Icons.health_and_safety_rounded,
                color: Color(0xFF0F766E),
                size: 21,
              ),
            ),
            const SizedBox(width: 10),
            Text(_management ? 'EPI • Gestão' : 'EPI • Campo'),
          ],
        ),
        actions: [
          PopupMenuButton<bool>(
            tooltip: 'Alternar modo',
            initialValue: _management,
            onSelected: _setMode,
            icon: const Icon(Icons.swap_horiz_rounded),
            itemBuilder: (context) => const [
              PopupMenuItem(
                value: false,
                child: ListTile(
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(Icons.phone_android_rounded),
                  title: Text('Campo'),
                ),
              ),
              PopupMenuItem(
                value: true,
                child: ListTile(
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(Icons.monitor_rounded),
                  title: Text('Gestão'),
                ),
              ),
            ],
          ),
          IconButton(
            tooltip: 'Atualizar módulo',
            onPressed: _open,
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: _error.isNotEmpty
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.cloud_off_rounded, size: 52),
                    const SizedBox(height: 12),
                    const Text(
                      'Não foi possível abrir o módulo de EPI.',
                      style: TextStyle(fontWeight: FontWeight.w800),
                    ),
                    const SizedBox(height: 8),
                    Text(_error, textAlign: TextAlign.center),
                    const SizedBox(height: 16),
                    FilledButton.icon(
                      onPressed: _open,
                      icon: const Icon(Icons.refresh_rounded),
                      label: const Text('Tentar novamente'),
                    ),
                  ],
                ),
              ),
            )
          : Stack(
              children: [
                Positioned.fill(child: _webview()),
                if (_loading)
                  const Positioned.fill(
                    child: ColoredBox(
                      color: Colors.white,
                      child: Center(child: CircularProgressIndicator()),
                    ),
                  ),
              ],
            ),
    );
  }

  Widget _webview() {
    if (Platform.isWindows) {
      final controller = _windowsController;
      if (controller == null || !controller.value.isInitialized) {
        return const SizedBox.shrink();
      }

      return win.Webview(
        controller,
        permissionRequested: (url, kind, isUserInitiated) {
          if (kind == win.WebviewPermissionKind.camera ||
              kind == win.WebviewPermissionKind.microphone) {
            return win.WebviewPermissionDecision.allow;
          }
          return win.WebviewPermissionDecision.deny;
        },
      );
    }

    final controller = _androidController;
    return controller == null
        ? const SizedBox.shrink()
        : WebViewWidget(controller: controller);
  }
}
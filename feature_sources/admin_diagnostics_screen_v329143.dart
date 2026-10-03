import 'dart:io';

import 'package:flutter/material.dart';

import '../brand.dart';
import '../database.dart';
import '../services/auth_service.dart';
import '../services/device_sync_service.dart';
import '../services/media_sync_service.dart';

class AdminDiagnosticsScreen extends StatefulWidget {
  const AdminDiagnosticsScreen({super.key});

  @override
  State<AdminDiagnosticsScreen> createState() => _AdminDiagnosticsScreenState();
}

class _AdminDiagnosticsScreenState extends State<AdminDiagnosticsScreen> {
  bool loading = true;
  String error = '';
  Map<String, String> values = const {};

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    if (!AuthService.isAdmin) {
      if (mounted) {
        setState(() {
          loading = false;
          error = 'Diagnóstico técnico disponível somente para a conta ADM.';
        });
      }
      return;
    }
    if (mounted) setState(() {
      loading = true;
      error = '';
    });
    try {
      final db = AppDatabase.instance;
      final structured = await DeviceSyncService.pendingChangesCount();
      final media = await MediaSyncService.pendingCount();
      final result = <String, String>{
        'Versão': Platform.isWindows ? '3.30.62' : '3.29.143',
        'Plataforma': Platform.isWindows ? 'Windows' : (Platform.isAndroid ? 'Android' : Platform.operatingSystem),
        'Usuário': AuthService.currentUser?.name ?? 'ADM',
        'Perfil': AuthService.currentUser?.role ?? 'admin',
        'Alterações aguardando sincronização': '$structured',
        'Mídias aguardando envio': '$media',
        'Última tentativa': (await db.getSetting('last_device_sync_attempt')).trim(),
        'Última sincronização concluída': (await db.getSetting('last_device_sync_success')).trim(),
        'Status da sincronização': (await db.getSetting('last_device_sync_status')).trim(),
        'Último erro de sincronização': (await db.getSetting('last_device_sync_error')).trim(),
        'Último envio de mídia': (await db.getSetting('media_sync_last_success')).trim(),
        'Último erro de mídia': (await db.getSetting('media_sync_last_error')).trim(),
        'Central Online': (await db.getSetting('management_panel_endpoint')).trim().isEmpty
            ? 'Não configurada neste aparelho'
            : 'Configurada',
      };
      if (!mounted) return;
      setState(() {
        values = result;
        loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        loading = false;
        error = 'Não foi possível carregar o diagnóstico: $e';
      });
    }
  }

  String _display(String value) => value.trim().isEmpty ? 'Sem registro' : value.trim();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Diagnóstico técnico')),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Card(
              color: const Color(0xFFF5F8FC),
              child: const Padding(
                padding: EdgeInsets.all(14),
                child: Text(
                  'Tela somente de leitura para diagnóstico da conta ADM. Ela não altera sincronização, banco, fotos ou configurações.',
                  style: TextStyle(height: 1.35),
                ),
              ),
            ),
            const SizedBox(height: 10),
            if (loading)
              const Center(child: Padding(
                padding: EdgeInsets.all(28),
                child: CircularProgressIndicator(),
              ))
            else if (error.isNotEmpty)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      Text(error, textAlign: TextAlign.center),
                      const SizedBox(height: 10),
                      FilledButton.icon(
                        onPressed: _load,
                        icon: const Icon(Icons.refresh_rounded),
                        label: const Text('Atualizar'),
                      ),
                    ],
                  ),
                ),
              )
            else ...[
              for (final entry in values.entries)
                Card(
                  child: ListTile(
                    dense: true,
                    title: Text(
                      entry.key,
                      style: const TextStyle(
                        color: AuditarBrand.navy,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    subtitle: Text(_display(entry.value)),
                  ),
                ),
              const SizedBox(height: 10),
              FilledButton.icon(
                onPressed: _load,
                icon: const Icon(Icons.refresh_rounded),
                label: const Text('Atualizar diagnóstico'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

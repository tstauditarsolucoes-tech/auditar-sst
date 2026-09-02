import 'package:flutter/material.dart';

import '../database.dart';
import '../services/backup_service.dart';
import '../services/drive_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final technician = TextEditingController();
  final appName = TextEditingController();
  final footer = TextEditingController();
  final panelEndpoint = TextEditingController();
  final panelSyncKey = TextEditingController();

  bool loading = true;
  bool driveLinked = false;
  bool driveAutoUpload = true;
  String driveEmail = '';
  int drivePending = 0;
  bool driveBusy = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    technician.dispose();
    appName.dispose();
    footer.dispose();
    panelEndpoint.dispose();
    panelSyncKey.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    final db = AppDatabase.instance;

    technician.text = await db.getSetting(
      'default_technician',
      fallback: '',
    );

    appName.text = await db.getSetting(
      'app_name',
      fallback: 'Auditar SST',
    );

    footer.text = await db.getSetting(
      'report_footer',
      fallback: 'Relatório de Inspeção de Segurança do Trabalho',
    );

    panelEndpoint.text = await db.getSetting(
      'management_panel_endpoint',
      fallback: '',
    );

    panelSyncKey.text = await db.getSetting(
      'management_panel_sync_key',
      fallback: '',
    );

    final enabled = await db.getSetting(
      'drive_enabled',
      fallback: 'false',
    );

    final autoUpload = await db.getSetting(
      'drive_auto_upload',
      fallback: 'true',
    );

    final email = await db.getSetting(
      'drive_account_email',
      fallback: '',
    );

    final pending = await db.pendingDriveUploadsCount();

    if (!mounted) return;

    setState(() {
      driveLinked = enabled == 'true';
      driveAutoUpload = autoUpload == 'true';
      driveEmail = email;
      drivePending = pending;
      loading = false;
    });
  }

  String? _appsScriptUrlError(String value) {
    final text = value.trim();
    if (text.isEmpty) return null;

    final uri = Uri.tryParse(text);
    if (uri == null || uri.scheme != 'https') {
      return 'Informe uma URL HTTPS válida do Google Apps Script.';
    }

    if (uri.host == 'script.googleusercontent.com' ||
        uri.host.endsWith('.googleusercontent.com')) {
      return 'Esse é um link temporário e pode expirar. Use a URL permanente do Apps Script terminada em /exec.';
    }

    if (uri.host != 'script.google.com' ||
        !uri.path.startsWith('/macros/s/') ||
        !uri.path.endsWith('/exec')) {
      return 'Use a URL da implantação do Google Apps Script no formato https://script.google.com/macros/s/.../exec.';
    }

    return null;
  }

  Future<void> _save() async {
    final endpointError = _appsScriptUrlError(panelEndpoint.text);
    if (endpointError != null) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(endpointError)),
      );
      return;
    }

    final db = AppDatabase.instance;

    await db.setSetting(
      'default_technician',
      technician.text.trim(),
    );
    await db.setSetting(
      'app_name',
      appName.text.trim().isEmpty
          ? 'Auditar SST'
          : appName.text.trim(),
    );
    await db.setSetting(
      'report_footer',
      footer.text.trim(),
    );
    await db.setSetting(
      'drive_auto_upload',
      driveAutoUpload ? 'true' : 'false',
    );

    await db.setSetting(
      'management_panel_endpoint',
      panelEndpoint.text.trim(),
    );
    await db.setSetting(
      'management_panel_sync_key',
      panelSyncKey.text.trim(),
    );

    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Configurações salvas.')),
    );
  }

  Future<void> _connectDrive() async {
    setState(() => driveBusy = true);

    try {
      final result = await DriveService.connect();

      if (!mounted) return;

      setState(() {
        driveLinked = true;
        driveEmail = result.email;
        driveAutoUpload = true;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Google Drive conectado. A pasta “Auditar SST” foi preparada.',
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Não foi possível conectar o Google Drive: $e',
          ),
        ),
      );
    } finally {
      if (mounted) {
        setState(() => driveBusy = false);
      }
      await _load();
    }
  }

  Future<void> _disconnectDrive() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Desconectar Google Drive?'),
        content: const Text(
          'Os relatórios já enviados continuarão no Drive. '
          'O aplicativo continuará funcionando normalmente offline.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Desconectar'),
          ),
        ],
      ),
    );

    if (confirm != true) return;

    setState(() => driveBusy = true);

    try {
      await DriveService.disconnect();
    } finally {
      if (mounted) {
        setState(() {
          driveBusy = false;
          driveLinked = false;
          driveEmail = '';
        });
      }
      await _load();
    }
  }

  Future<void> _syncDrive() async {
    setState(() => driveBusy = true);

    try {
      final sent = await DriveService.syncPending(interactive: true);

      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            sent == 0
                ? 'Nenhum relatório pendente foi enviado.'
                : '$sent relatório(s) enviado(s) ao Google Drive.',
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Não foi possível sincronizar: $e'),
        ),
      );
    } finally {
      if (mounted) setState(() => driveBusy = false);
      await _load();
    }
  }

  Future<void> _backup() async {
    try {
      await BackupService.shareBackup();

      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Backup criado. Escolha onde deseja salvá-lo.',
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Não foi possível criar o backup: $e',
          ),
        ),
      );
    }
  }

  Future<void> _restore() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Restaurar backup?'),
        content: const Text(
          'Os dados atuais do aplicativo serão substituídos pelos dados do arquivo escolhido.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Continuar'),
          ),
        ],
      ),
    );

    if (confirm != true) return;

    try {
      final restored = await BackupService.restoreBackup();

      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            restored
                ? 'Backup restaurado com sucesso.'
                : 'Restauração cancelada.',
          ),
        ),
      );

      if (restored) {
        await _load();
      }
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Não foi possível restaurar o backup: $e',
          ),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (loading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Configurações')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            'Preferências',
            style: Theme.of(context)
                .textTheme
                .titleMedium
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: technician,
            decoration: const InputDecoration(
              labelText: 'Técnico padrão',
              hintText:
                  'Fica preenchido automaticamente na nova vistoria',
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: appName,
            decoration: const InputDecoration(
              labelText: 'Nome do aplicativo',
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: footer,
            maxLines: 2,
            decoration: const InputDecoration(
              labelText: 'Texto do rodapé dos relatórios',
            ),
          ),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: _save,
            icon: const Icon(Icons.save),
            label: const Text('Salvar configurações'),
          ),
          const SizedBox(height: 28),
          Text(
            'Google Drive',
            style: Theme.of(context)
                .textTheme
                .titleMedium
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 6),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        driveLinked
                            ? Icons.cloud_done_outlined
                            : Icons.cloud_off_outlined,
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          driveLinked
                              ? 'Google Drive conectado'
                              : 'Google Drive não conectado',
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                  if (driveLinked && driveEmail.isNotEmpty) ...[
                    const SizedBox(height: 5),
                    Text(driveEmail),
                  ],
                  const SizedBox(height: 8),
                  const Text(
                    'Os relatórios ficam salvos no celular e são enviados para '
                    'Auditar SST → Nome da empresa no Google Drive.',
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'A conexão usa a Central Online configurada abaixo. Não é necessário entrar com uma Conta Google no celular.',
                    style: TextStyle(fontSize: 12.5, color: Colors.black54),
                  ),
                  if (driveLinked) ...[
                    const SizedBox(height: 8),
                    SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text(
                        'Enviar relatório automaticamente',
                      ),
                      subtitle: const Text(
                        'Sem internet, o envio fica pendente.',
                      ),
                      value: driveAutoUpload,
                      onChanged: driveBusy
                          ? null
                          : (value) async {
                              setState(
                                () => driveAutoUpload = value,
                              );
                              await AppDatabase.instance.setSetting(
                                'drive_auto_upload',
                                value ? 'true' : 'false',
                              );
                            },
                    ),
                    Text(
                      '$drivePending envio(s) pendente(s)',
                    ),
                    const SizedBox(height: 8),
                    FilledButton.icon(
                      onPressed: driveBusy ? null : _syncDrive,
                      icon: const Icon(Icons.sync),
                      label: const Text(
                        'Sincronizar pendentes',
                      ),
                    ),
                    const SizedBox(height: 8),
                    OutlinedButton.icon(
                      onPressed:
                          driveBusy ? null : _disconnectDrive,
                      icon: const Icon(Icons.link_off),
                      label: const Text(
                        'Desconectar Google Drive',
                      ),
                    ),
                  ] else ...[
                    const SizedBox(height: 12),
                    FilledButton.icon(
                      onPressed:
                          driveBusy ? null : _connectDrive,
                      icon: const Icon(Icons.add_to_drive),
                      label: const Text(
                        'Conectar Google Drive',
                      ),
                    ),
                  ],
                  if (driveBusy) ...[
                    const SizedBox(height: 12),
                    const LinearProgressIndicator(),
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(height: 28),
          Text(
            'Serviços web gratuitos',
            style: Theme.of(context)
                .textTheme
                .titleMedium
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 6),
          const Text(
            'A mesma publicação do Google Apps Script atende o Painel Gerencial, a votação CIPA por QR Code e a conexão segura do Assistente IA.',
            style: TextStyle(fontSize: 12.5, color: Colors.black54),
          ),
          const SizedBox(height: 6),
          const Text(
            'Configuração única usada para publicar os links individuais das empresas. Depois de configurada, cada empresa terá seu próprio endereço de consulta.',
          ),
          const SizedBox(height: 12),
          TextField(
            controller: panelEndpoint,
            keyboardType: TextInputType.url,
            autocorrect: false,
            decoration: const InputDecoration(
              labelText: 'URL do Google Apps Script',
              hintText: 'https://script.google.com/macros/s/.../exec',
              prefixIcon: Icon(Icons.language_rounded),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: panelSyncKey,
            obscureText: true,
            autocorrect: false,
            enableSuggestions: false,
            decoration: const InputDecoration(
              labelText: 'Chave de sincronização',
              hintText: 'Chave criada na configuração do painel',
              prefixIcon: Icon(Icons.key_rounded),
            ),
          ),
          const SizedBox(height: 8),
          const Card(
            child: Padding(
              padding: EdgeInsets.all(12),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.info_outline_rounded),
                  SizedBox(width: 9),
                  Expanded(
                    child: Text(
                      'Use sempre a URL permanente da implantação, terminada em /exec. Não copie links script.googleusercontent.com, porque eles são temporários e podem expirar.',
                      style: TextStyle(fontSize: 12.5),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 10),
          FilledButton.icon(
            onPressed: _save,
            icon: const Icon(Icons.save_outlined),
            label: const Text('Salvar painel web'),
          ),
          const SizedBox(height: 14),
          const Card(
            child: Padding(
              padding: EdgeInsets.all(14),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.auto_awesome_outlined),
                  SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Assistente IA do técnico',
                          style: TextStyle(fontWeight: FontWeight.w800),
                        ),
                        SizedBox(height: 5),
                        Text(
                          'A IA gratuita do Gemini aparece nas fotos dos itens não conformes, nos registros de atos e condições inseguras, na conclusão do relatório e na leitura da lista de funcionários em PDF. Ela só usa internet quando você solicitar. A chave fica protegida no Apps Script e não é salva no aplicativo. No plano gratuito, o conteúdo pode ser usado pelo Google para melhorar seus produtos.',
                          style: TextStyle(fontSize: 12.5, height: 1.35),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 28),
          Text(
            'Backup completo do aplicativo',
            style: Theme.of(context)
                .textTheme
                .titleMedium
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 6),
          const Text(
            'O backup completo inclui banco de dados, fotos, logos, assinaturas e PDFs. '
            'O Google Drive acima é usado para arquivar os relatórios PDF.',
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: _backup,
            icon: const Icon(Icons.backup_outlined),
            label: const Text('Exportar backup'),
          ),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: _restore,
            icon: const Icon(Icons.restore),
            label: const Text('Restaurar backup'),
          ),
        ],
      ),
    );
  }
}

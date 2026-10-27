#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
pubp = root / 'pubspec.yaml'
formp = root / 'lib/screens/sst_record_form_screen.dart'
mediap = root / 'lib/services/media_sync_service.dart'
capturep = root / 'lib/screens/dds_signature_capture_screen.dart'

pub = pubp.read_text(encoding='utf-8')
form = formp.read_text(encoding='utf-8')
media = mediap.read_text(encoding='utf-8')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Marcador não encontrado: {label}')
    return text.replace(old, new, 1)

# Versão
if 'version: 3.29.47+189' not in pub:
    pub = replace_once(pub, 'version: 3.29.46+188', 'version: 3.29.47+189', 'versão 3.29.46')

# Tela dedicada de assinatura DDS.
capture = r'''import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:signature/signature.dart';

import '../brand.dart';
import '../services/storage_service.dart';

class DdsSignatureCaptureResult {
  final String name;
  final String localPath;
  final DateTime signedAt;

  const DdsSignatureCaptureResult({
    required this.name,
    required this.localPath,
    required this.signedAt,
  });
}

class DdsSignatureCaptureScreen extends StatefulWidget {
  final String initialName;

  const DdsSignatureCaptureScreen({
    super.key,
    this.initialName = '',
  });

  @override
  State<DdsSignatureCaptureScreen> createState() =>
      _DdsSignatureCaptureScreenState();
}

class _DdsSignatureCaptureScreenState
    extends State<DdsSignatureCaptureScreen> {
  late final TextEditingController nameController;
  final signatureController = SignatureController(
    penStrokeWidth: 3,
    penColor: Colors.black,
    exportBackgroundColor: Colors.white,
  );
  bool saving = false;

  @override
  void initState() {
    super.initState();
    nameController = TextEditingController(text: widget.initialName);
  }

  @override
  void dispose() {
    nameController.dispose();
    signatureController.dispose();
    super.dispose();
  }

  Future<void> _openFullScreen() async {
    FocusScope.of(context).unfocus();
    final forceLandscape = Platform.isAndroid;
    if (forceLandscape) {
      await SystemChrome.setPreferredOrientations(const [
        DeviceOrientation.landscapeLeft,
        DeviceOrientation.landscapeRight,
      ]);
    }
    try {
      if (!mounted) return;
      await Navigator.of(context).push<void>(
        MaterialPageRoute(
          fullscreenDialog: true,
          builder: (_) => _DdsFullSignatureCanvas(
            controller: signatureController,
          ),
        ),
      );
    } finally {
      if (forceLandscape) {
        await SystemChrome.setPreferredOrientations(
          const <DeviceOrientation>[],
        );
      }
    }
    if (mounted) setState(() {});
  }

  Future<void> _confirm() async {
    final name = nameController.text.trim();
    if (name.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Informe o nome do participante.')),
      );
      return;
    }
    if (signatureController.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Colete a assinatura do participante.')),
      );
      return;
    }

    setState(() => saving = true);
    try {
      final bytes = await signatureController.toPngBytes(
        height: 320,
        width: 900,
      );
      if (bytes == null || bytes.isEmpty) {
        throw StateError('Não foi possível gerar a assinatura.');
      }
      final path = await StorageService.persistPngBytes(
        bytes,
        folder: 'dds_assinaturas',
      );
      if (!mounted) return;
      Navigator.pop(
        context,
        DdsSignatureCaptureResult(
          name: name,
          localPath: path,
          signedAt: DateTime.now(),
        ),
      );
    } catch (error) {
      if (!mounted) return;
      setState(() => saving = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Falha ao salvar assinatura: $error')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Assinatura do DDS'),
      ),
      bottomNavigationBar: SafeArea(
        minimum: const EdgeInsets.all(12),
        child: FilledButton.icon(
          onPressed: saving ? null : _confirm,
          icon: saving
              ? const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.check_circle_outline),
          label: const Padding(
            padding: EdgeInsets.symmetric(vertical: 14),
            child: Text('Confirmar assinatura'),
          ),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(14),
        children: [
          TextField(
            controller: nameController,
            textCapitalization: TextCapitalization.words,
            decoration: const InputDecoration(
              labelText: 'Nome do participante *',
              prefixIcon: Icon(Icons.person_outline),
            ),
          ),
          const SizedBox(height: 14),
          const Text(
            'Assine abaixo com o dedo',
            style: TextStyle(
              color: AuditarBrand.navy,
              fontWeight: FontWeight.w800,
              fontSize: 16,
            ),
          ),
          const SizedBox(height: 8),
          Container(
            height: 250,
            decoration: BoxDecoration(
              color: Colors.white,
              border: Border.all(color: const Color(0xFFD8DDE8)),
              borderRadius: BorderRadius.circular(14),
            ),
            clipBehavior: Clip.antiAlias,
            child: Signature(
              controller: signatureController,
              backgroundColor: Colors.white,
            ),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () {
                    signatureController.clear();
                    setState(() {});
                  },
                  icon: const Icon(Icons.delete_outline),
                  label: const Text('Limpar'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: FilledButton.tonalIcon(
                  onPressed: _openFullScreen,
                  icon: const Icon(Icons.fullscreen),
                  label: const Text('Tela cheia'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          const Text(
            'A assinatura fica vinculada ao participante e ao registro deste DDS.',
            style: TextStyle(color: Colors.black54, fontSize: 12.5),
          ),
        ],
      ),
    );
  }
}

class _DdsFullSignatureCanvas extends StatelessWidget {
  final SignatureController controller;

  const _DdsFullSignatureCanvas({required this.controller});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Assinar em tela cheia'),
        actions: [
          IconButton(
            onPressed: controller.clear,
            tooltip: 'Limpar',
            icon: const Icon(Icons.delete_outline),
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(10),
          child: Container(
            decoration: BoxDecoration(
              color: Colors.white,
              border: Border.all(color: const Color(0xFFD8DDE8)),
              borderRadius: BorderRadius.circular(14),
            ),
            clipBehavior: Clip.antiAlias,
            child: Signature(
              controller: controller,
              backgroundColor: Colors.white,
            ),
          ),
        ),
      ),
      bottomNavigationBar: SafeArea(
        minimum: const EdgeInsets.fromLTRB(12, 6, 12, 12),
        child: FilledButton.icon(
          onPressed: () => Navigator.pop(context),
          icon: const Icon(Icons.check),
          label: const Padding(
            padding: EdgeInsets.symmetric(vertical: 12),
            child: Text('Concluir assinatura'),
          ),
        ),
      ),
    );
  }
}
'''
capturep.write_text(capture, encoding='utf-8', newline='\n')

# Integração com a biblioteca de mídia/Drive.
media_marker = r'''  static Future<void> registerCompanyLogo({required String companyId, required String localPath}) async {
'''
media_helpers = r'''  static Future<void> registerDdsSignature({
    required String companyId,
    required String signatureId,
    required String localPath,
  }) async {
    if (companyId.trim().isEmpty ||
        signatureId.trim().isEmpty ||
        localPath.trim().isEmpty) {
      return;
    }
    final db = await AppDatabase.instance.database;
    final mediaId = _assetId('dds_signature', signatureId);
    await db.insert(
      'media_assets',
      {
        'id': mediaId,
        'company_id': companyId,
        'entity_type': 'dds_signature',
        'entity_id': signatureId,
        'local_path': localPath,
        'drive_file_id': '',
        'file_name': p.basename(localPath),
        'mime_type': _mimeTypeFor(localPath),
        'updated_at': DateTime.now().toUtc().toIso8601String(),
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  static Future<String?> ddsSignatureLocalPath({
    required String companyId,
    required String signatureId,
    bool restoreIfMissing = true,
  }) async {
    if (companyId.trim().isEmpty || signatureId.trim().isEmpty) return null;
    final db = await AppDatabase.instance.database;
    final mediaId = _assetId('dds_signature', signatureId);

    Future<String?> currentPath() async {
      final rows = await db.query(
        'media_assets',
        where: 'id = ?',
        whereArgs: [mediaId],
        limit: 1,
      );
      if (rows.isEmpty) return null;
      final path = '${rows.first['local_path'] ?? ''}'.trim();
      if (path.isEmpty) return null;
      return await File(path).exists() ? path : null;
    }

    final local = await currentPath();
    if (local != null || !restoreIfMissing || !AuthService.isSignedIn) {
      return local;
    }

    await _restoreEntities(
      db,
      companyId,
      [
        {'type': 'dds_signature', 'id': signatureId},
      ],
    );
    return currentPath();
  }

  static Future<void> removeDdsSignature({
    required String signatureId,
    bool deleteLocalFile = true,
  }) async {
    if (signatureId.trim().isEmpty) return;
    final db = await AppDatabase.instance.database;
    final mediaId = _assetId('dds_signature', signatureId);
    final rows = await db.query(
      'media_assets',
      where: 'id = ?',
      whereArgs: [mediaId],
      limit: 1,
    );
    if (deleteLocalFile && rows.isNotEmpty) {
      final localPath = '${rows.first['local_path'] ?? ''}'.trim();
      if (localPath.isNotEmpty) {
        try {
          final file = File(localPath);
          if (await file.exists()) await file.delete();
        } catch (_) {}
      }
    }
    await db.delete('media_assets', where: 'id = ?', whereArgs: [mediaId]);
  }

'''
if 'registerDdsSignature({' not in media:
    if media_marker not in media:
        raise RuntimeError('Ponto de integração do MediaSyncService não localizado')
    media = media.replace(media_marker, media_helpers + media_marker, 1)

# Imports do formulário.
form = replace_once(
    form,
    "import 'package:flutter/material.dart';\n",
    "import 'dart:async';\nimport 'dart:io';\n\nimport 'package:flutter/material.dart';\n",
    'imports Dart do formulário',
)
form = replace_once(
    form,
    "import '../models.dart';\n",
    "import '../models.dart';\nimport '../services/media_sync_service.dart';\nimport 'dds_signature_capture_screen.dart';\n",
    'imports DDS do formulário',
)

# Estado de assinaturas.
state_marker = "  String subtype = '';\n"
state_extra = r'''  final List<Map<String, dynamic>> ddsSignatures = [];
  final Map<String, String> ddsSignaturePaths = {};
  bool restoringDdsSignatures = false;
'''
if 'final List<Map<String, dynamic>> ddsSignatures' not in form:
    form = replace_once(form, state_marker, state_marker + state_extra, 'estado de assinaturas')

# Carregar metadados existentes do payload.
init_marker = "      subtype = '${p['subtype'] ?? ''}';\n"
init_extra = r'''      if (widget.type == 'DDS') {
        final rawSignatures = p['dds_signatures'];
        if (rawSignatures is List) {
          for (final raw in rawSignatures.whereType<Map>()) {
            final item = Map<String, dynamic>.from(raw);
            final id = '${item['id'] ?? ''}'.trim();
            final name = '${item['name'] ?? ''}'.trim();
            if (id.isEmpty || name.isEmpty) continue;
            ddsSignatures.add({
              'id': id,
              'name': name,
              'signedAt': '${item['signedAt'] ?? item['signed_at'] ?? ''}',
            });
          }
        }
      }
'''
if "final rawSignatures = p['dds_signatures'];" not in form:
    form = replace_once(form, init_marker, init_marker + init_extra, 'carga de assinaturas DDS')

# Restaurar assinatura do Drive após carregar empresa/setores.
load_marker = r'''    setState(() {
      companies = loaded;
      loading = false;
    });
  }
'''
load_new = r'''    setState(() {
      companies = loaded;
      loading = false;
    });
    if (widget.type == 'DDS' && ddsSignatures.isNotEmpty) {
      await _restoreDdsSignaturePaths();
    }
  }
'''
if 'await _restoreDdsSignaturePaths();' not in form:
    form = replace_once(form, load_marker, load_new, 'restauração das assinaturas DDS')

# Persistir somente metadados estruturados no payload; bytes ficam no Drive.
payload_marker = "      'subtype': subtype,\n"
payload_new = "      'subtype': subtype,\n      if (widget.type == 'DDS') 'dds_signatures': ddsSignatures,\n"
if "'dds_signatures': ddsSignatures" not in form:
    form = replace_once(form, payload_marker, payload_new, 'payload das assinaturas DDS')

# Inserir o módulo visual entre participantes e observações.
dds_fields_old = r'''      add(TextFormField(controller: responsibleController, decoration: const InputDecoration(labelText: 'Instrutor / responsável')));
      add(TextFormField(controller: participantsController, maxLines: 4, decoration: const InputDecoration(labelText: 'Participantes', hintText: 'Um nome por linha ou observação da lista')));
      add(TextFormField(controller: notesController, maxLines: 3, decoration: const InputDecoration(labelText: 'Observações / conteúdo abordado')));
'''
dds_fields_new = r'''      add(TextFormField(controller: responsibleController, decoration: const InputDecoration(labelText: 'Instrutor / responsável')));
      add(TextFormField(controller: participantsController, maxLines: 4, decoration: const InputDecoration(labelText: 'Participantes', hintText: 'Um nome por linha ou observação da lista')));
      add(_ddsSignaturesCard());
      add(TextFormField(controller: notesController, maxLines: 3, decoration: const InputDecoration(labelText: 'Observações / conteúdo abordado')));
'''
if 'add(_ddsSignaturesCard());' not in form:
    form = replace_once(form, dds_fields_old, dds_fields_new, 'card de assinaturas no DDS')

# Métodos do módulo DDS antes de _section.
methods_marker = "  Widget _section(String text) => Padding(\n"
methods = r'''  List<String> _ddsParticipantNames() {
    final seen = <String>{};
    final result = <String>[];
    for (final raw in participantsController.text.split(RegExp(r'[\r\n]+'))) {
      final name = raw.trim();
      if (name.isEmpty) continue;
      final key = name.toLowerCase();
      if (seen.add(key)) result.add(name);
    }
    return result;
  }

  Future<void> _restoreDdsSignaturePaths() async {
    final companyId = selectedCompanyId;
    if (companyId == null || companyId.isEmpty || ddsSignatures.isEmpty) return;
    if (mounted) setState(() => restoringDdsSignatures = true);
    try {
      for (final item in ddsSignatures) {
        final id = '${item['id'] ?? ''}'.trim();
        if (id.isEmpty) continue;
        final path = await MediaSyncService.ddsSignatureLocalPath(
          companyId: companyId,
          signatureId: id,
        );
        if (path != null && path.isNotEmpty) ddsSignaturePaths[id] = path;
      }
    } finally {
      if (mounted) setState(() => restoringDdsSignatures = false);
    }
  }

  Future<void> _collectDdsSignature([Map<String, dynamic>? current]) async {
    final companyId = selectedCompanyId;
    if (companyId == null || companyId.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Selecione a empresa antes de coletar a assinatura.')),
      );
      return;
    }

    String initialName = '${current?['name'] ?? ''}'.trim();
    if (initialName.isEmpty) {
      final signed = ddsSignatures
          .map((item) => '${item['name'] ?? ''}'.trim().toLowerCase())
          .toSet();
      for (final name in _ddsParticipantNames()) {
        if (!signed.contains(name.toLowerCase())) {
          initialName = name;
          break;
        }
      }
    }

    final result = await Navigator.of(context).push<DdsSignatureCaptureResult>(
      MaterialPageRoute(
        fullscreenDialog: true,
        builder: (_) => DdsSignatureCaptureScreen(initialName: initialName),
      ),
    );
    if (result == null || !mounted) return;

    Map<String, dynamic>? existing = current;
    existing ??= ddsSignatures.cast<Map<String, dynamic>?>().firstWhere(
          (item) =>
              '${item?['name'] ?? ''}'.trim().toLowerCase() ==
              result.name.toLowerCase(),
          orElse: () => null,
        );
    final signatureId = '${existing?['id'] ?? ''}'.trim().isNotEmpty
        ? '${existing!['id']}'
        : const Uuid().v4();

    await MediaSyncService.registerDdsSignature(
      companyId: companyId,
      signatureId: signatureId,
      localPath: result.localPath,
    );

    final updated = <String, dynamic>{
      'id': signatureId,
      'name': result.name,
      'signedAt': result.signedAt.toUtc().toIso8601String(),
    };
    setState(() {
      if (existing != null) {
        final index = ddsSignatures.indexWhere(
          (item) => '${item['id'] ?? ''}' == signatureId,
        );
        if (index >= 0) {
          ddsSignatures[index] = updated;
        } else {
          ddsSignatures.add(updated);
        }
      } else {
        ddsSignatures.add(updated);
      }
      ddsSignaturePaths[signatureId] = result.localPath;

      final participants = _ddsParticipantNames();
      final alreadyListed = participants.any(
        (name) => name.toLowerCase() == result.name.toLowerCase(),
      );
      if (!alreadyListed) {
        final currentText = participantsController.text.trimRight();
        participantsController.text = currentText.isEmpty
            ? result.name
            : '$currentText\n${result.name}';
      }
    });

    unawaited(MediaSyncService.uploadPending());
  }

  Future<void> _removeDdsSignature(Map<String, dynamic> item) async {
    final id = '${item['id'] ?? ''}'.trim();
    final name = '${item['name'] ?? 'Participante'}'.trim();
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Remover assinatura?'),
        content: Text('A assinatura de $name será retirada deste DDS.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Remover'),
          ),
        ],
      ),
    );
    if (ok != true) return;
    if (id.isNotEmpty) {
      await MediaSyncService.removeDdsSignature(signatureId: id);
    }
    if (!mounted) return;
    setState(() {
      ddsSignatures.removeWhere((entry) => '${entry['id'] ?? ''}' == id);
      ddsSignaturePaths.remove(id);
    });
  }

  String _ddsSignedAt(Map<String, dynamic> item) {
    final raw = '${item['signedAt'] ?? ''}'.trim();
    final parsed = DateTime.tryParse(raw)?.toLocal();
    if (parsed == null) return 'Assinatura registrada';
    return 'Assinado em ${DateFormat('dd/MM/yyyy HH:mm').format(parsed)}';
  }

  Widget _ddsSignaturesCard() {
    final participants = _ddsParticipantNames();
    final signedNames = ddsSignatures
        .map((item) => '${item['name'] ?? ''}'.trim().toLowerCase())
        .where((name) => name.isNotEmpty)
        .toSet();
    final missing = participants
        .where((name) => !signedNames.contains(name.toLowerCase()))
        .toList();

    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.draw_outlined, color: AuditarBrand.greenDark),
                const SizedBox(width: 8),
                const Expanded(
                  child: Text(
                    'Assinaturas digitais',
                    style: TextStyle(
                      fontWeight: FontWeight.w800,
                      color: AuditarBrand.navy,
                    ),
                  ),
                ),
                if (restoringDdsSignatures)
                  const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
              ],
            ),
            const SizedBox(height: 5),
            Text(
              participants.isEmpty
                  ? '${ddsSignatures.length} assinatura(s) registrada(s).'
                  : '${ddsSignatures.length} de ${participants.length} participante(s) assinado(s).',
              style: const TextStyle(color: Colors.black54, fontSize: 12.5),
            ),
            if (missing.isNotEmpty) ...[
              const SizedBox(height: 5),
              Text(
                'Sem assinatura: ${missing.take(3).join(', ')}${missing.length > 3 ? ' e mais ${missing.length - 3}' : ''}',
                style: const TextStyle(color: Color(0xFF8A5A00), fontSize: 12),
              ),
            ],
            const SizedBox(height: 10),
            SizedBox(
              width: double.infinity,
              child: FilledButton.tonalIcon(
                onPressed: _collectDdsSignature,
                icon: const Icon(Icons.draw_outlined),
                label: const Text('Coletar assinatura'),
              ),
            ),
            if (ddsSignatures.isEmpty) ...[
              const SizedBox(height: 10),
              const Text(
                'Nenhuma assinatura coletada neste DDS.',
                style: TextStyle(color: Colors.black45, fontSize: 12.5),
              ),
            ] else ...[
              const SizedBox(height: 10),
              ...ddsSignatures.map((item) {
                final id = '${item['id'] ?? ''}'.trim();
                final path = ddsSignaturePaths[id];
                final hasPreview = path != null && File(path).existsSync();
                return Container(
                  margin: const EdgeInsets.only(bottom: 8),
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF7F9FC),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFFE1E5ED)),
                  ),
                  child: Column(
                    children: [
                      Row(
                        children: [
                          const Icon(
                            Icons.verified_rounded,
                            color: AuditarBrand.greenDark,
                            size: 22,
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  '${item['name'] ?? ''}',
                                  style: const TextStyle(fontWeight: FontWeight.w700),
                                ),
                                Text(
                                  _ddsSignedAt(item),
                                  style: const TextStyle(
                                    color: Colors.black54,
                                    fontSize: 11.5,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          PopupMenuButton<String>(
                            onSelected: (value) {
                              if (value == 'redo') _collectDdsSignature(item);
                              if (value == 'remove') _removeDdsSignature(item);
                            },
                            itemBuilder: (_) => const [
                              PopupMenuItem(
                                value: 'redo',
                                child: Text('Refazer assinatura'),
                              ),
                              PopupMenuItem(
                                value: 'remove',
                                child: Text('Remover assinatura'),
                              ),
                            ],
                          ),
                        ],
                      ),
                      if (hasPreview) ...[
                        const SizedBox(height: 6),
                        Container(
                          width: double.infinity,
                          height: 64,
                          color: Colors.white,
                          child: Image.file(
                            File(path),
                            fit: BoxFit.contain,
                          ),
                        ),
                      ],
                    ],
                  ),
                );
              }),
            ],
          ],
        ),
      ),
    );
  }

'''
if 'Widget _ddsSignaturesCard()' not in form:
    form = replace_once(form, methods_marker, methods + methods_marker, 'métodos do módulo DDS')

pubp.write_text(pub, encoding='utf-8', newline='\n')
formp.write_text(form, encoding='utf-8', newline='\n')
mediap.write_text(media, encoding='utf-8', newline='\n')

# Regressões básicas.
assert 'version: 3.29.47+189' in pubp.read_text(encoding='utf-8')
final_form = formp.read_text(encoding='utf-8')
final_media = mediap.read_text(encoding='utf-8')
assert "'dds_signatures': ddsSignatures" in final_form
assert 'Assinaturas digitais' in final_form
assert 'Coletar assinatura' in final_form
assert 'DdsSignatureCaptureScreen' in final_form
assert 'registerDdsSignature({' in final_media
assert 'ddsSignatureLocalPath({' in final_media
assert "entity_type': 'dds_signature'" in final_media
assert capturep.exists()
print('Android v3.29.47+189: módulo de DDS com assinaturas digitais por participante aplicado.')

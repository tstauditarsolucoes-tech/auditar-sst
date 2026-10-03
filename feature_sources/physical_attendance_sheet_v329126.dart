import 'dart:async';
import 'dart:io';
import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:printing/printing.dart';
import 'package:sqflite/sqflite.dart';
import 'package:uuid/uuid.dart';

import '../brand.dart';
import '../database.dart';
import '../services/media_sync_service.dart';

class PhysicalAttendanceSheetScreen extends StatefulWidget {
  final String companyId;
  final String entityType;
  final String title;
  final List<String> initialIds;
  final Future<void> Function(List<String> ids) onChanged;

  const PhysicalAttendanceSheetScreen({
    super.key,
    required this.companyId,
    required this.entityType,
    required this.title,
    required this.initialIds,
    required this.onChanged,
  });

  @override
  State<PhysicalAttendanceSheetScreen> createState() =>
      _PhysicalAttendanceSheetScreenState();
}

class _PhysicalAttendanceSheetScreenState
    extends State<PhysicalAttendanceSheetScreen> {
  final ImagePicker _picker = ImagePicker();
  late final List<String> _ids = List<String>.from(widget.initialIds);
  List<Map<String, Object?>> _assets = const [];
  bool _loading = true;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  Future<void> _reload() async {
    if (mounted) setState(() => _loading = true);
    final rows = <Map<String, Object?>>[];
    for (final id in _ids) {
      final row = await PhysicalAttendanceStorage.resolve(
        companyId: widget.companyId,
        entityType: widget.entityType,
        entityId: id,
      );
      if (row != null) rows.add(row);
    }
    if (!mounted) return;
    setState(() {
      _assets = rows;
      _loading = false;
    });
  }

  Future<void> _addPdf() async {
    if (_busy) return;
    final picked = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['pdf'],
      withData: true,
      allowMultiple: true,
    );
    if (picked == null || picked.files.isEmpty) return;
    await _storeFiles(picked.files);
  }

  Future<void> _addImage(ImageSource source) async {
    if (_busy) return;
    final image = await _picker.pickImage(
      source: source,
      imageQuality: 86,
      maxWidth: 2200,
    );
    if (image == null) return;
    await _storeFiles([
      PlatformFile(
        name: image.name,
        path: image.path,
        size: await File(image.path).length(),
      ),
    ]);
  }

  Future<void> _storeFiles(List<PlatformFile> files) async {
    setState(() => _busy = true);
    try {
      for (final file in files) {
        final id = await PhysicalAttendanceStorage.register(
          companyId: widget.companyId,
          entityType: widget.entityType,
          picked: file,
        );
        if (!_ids.contains(id)) _ids.add(id);
      }
      await widget.onChanged(List<String>.unmodifiable(_ids));
      unawaited(MediaSyncService.uploadPending(limit: 8));
      await _reload();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Ficha anexada. O backup será realizado pela fila de evidências já existente.'),
          ),
        );
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Não foi possível anexar a ficha: $error')),
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _openAsset(Map<String, Object?> row) async {
    final entityId = '${row['entity_id'] ?? ''}'.trim();
    if (entityId.isEmpty) return;
    final restored = await PhysicalAttendanceStorage.resolve(
      companyId: widget.companyId,
      entityType: widget.entityType,
      entityId: entityId,
    );
    final path = '${restored?['local_path'] ?? ''}'.trim();
    if (path.isEmpty || !File(path).existsSync()) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Arquivo ainda não está disponível neste aparelho.')),
        );
      }
      return;
    }
    final mime = '${restored?['mime_type'] ?? ''}'.toLowerCase();
    if (mime == 'application/pdf' || path.toLowerCase().endsWith('.pdf')) {
      final bytes = await File(path).readAsBytes();
      if (!mounted) return;
      await Navigator.of(context).push(
        MaterialPageRoute<void>(
          builder: (_) => Scaffold(
            appBar: AppBar(title: Text('${restored?['file_name'] ?? 'Ficha assinada'}')),
            body: PdfPreview(
              build: (_) async => bytes,
              allowPrinting: true,
              allowSharing: true,
              pdfFileName: '${restored?['file_name'] ?? 'ficha_assinada.pdf'}',
            ),
          ),
        ),
      );
      return;
    }
    if (!mounted) return;
    await showDialog<void>(
      context: context,
      builder: (_) => Dialog(
        insetPadding: const EdgeInsets.all(14),
        child: Stack(
          children: [
            Padding(
              padding: const EdgeInsets.all(12),
              child: InteractiveViewer(
                minScale: .7,
                maxScale: 6,
                child: Image.file(File(path), fit: BoxFit.contain),
              ),
            ),
            Positioned(
              right: 4,
              top: 4,
              child: IconButton(
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.close_rounded),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _assetCard(Map<String, Object?> row) {
    final driveId = '${row['drive_file_id'] ?? ''}'.trim();
    final local = '${row['local_path'] ?? ''}'.trim();
    final name = '${row['file_name'] ?? 'Ficha assinada'}'.trim();
    final isPdf = '${row['mime_type'] ?? ''}'.toLowerCase() == 'application/pdf' ||
        name.toLowerCase().endsWith('.pdf');
    return Card(
      child: ListTile(
        onTap: () => _openAsset(row),
        leading: Icon(isPdf ? Icons.picture_as_pdf_outlined : Icons.image_outlined),
        title: Text(name.isEmpty ? 'Ficha assinada' : name),
        subtitle: Text(
          driveId.isNotEmpty
              ? 'Backup confirmado • toque para visualizar'
              : local.isNotEmpty
                  ? 'Salvo no aparelho • aguardando backup'
                  : 'Aguardando recuperação',
        ),
        trailing: Icon(
          driveId.isNotEmpty ? Icons.cloud_done_outlined : Icons.cloud_upload_outlined,
          color: driveId.isNotEmpty ? AuditarBrand.greenDark : null,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(14, 14, 14, 100),
        children: [
          const Card(
            child: Padding(
              padding: EdgeInsets.all(14),
              child: Text(
                'Use este espaço quando a presença foi registrada em ficha de papel. '
                'O arquivo original fica vinculado ao DDS ou treinamento e não exige nova assinatura no celular.',
              ),
            ),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              FilledButton.tonalIcon(
                onPressed: _busy ? null : _addPdf,
                icon: const Icon(Icons.upload_file_outlined),
                label: const Text('Importar PDF'),
              ),
              if (!Platform.isWindows)
                FilledButton.tonalIcon(
                  onPressed: _busy ? null : () => _addImage(ImageSource.camera),
                  icon: const Icon(Icons.photo_camera_outlined),
                  label: const Text('Tirar foto'),
                ),
              FilledButton.tonalIcon(
                onPressed: _busy ? null : () => _addImage(ImageSource.gallery),
                icon: const Icon(Icons.photo_library_outlined),
                label: const Text('Galeria'),
              ),
              OutlinedButton.icon(
                onPressed: _busy ? null : _reload,
                icon: const Icon(Icons.refresh),
                label: const Text('Atualizar'),
              ),
            ],
          ),
          const SizedBox(height: 14),
          if (_busy) const LinearProgressIndicator(),
          if (_loading)
            const Padding(
              padding: EdgeInsets.all(24),
              child: Center(child: CircularProgressIndicator()),
            )
          else if (_assets.isEmpty)
            const Card(
              child: Padding(
                padding: EdgeInsets.all(18),
                child: Text('Nenhuma ficha física anexada neste registro.'),
              ),
            )
          else
            ..._assets.map(_assetCard),
        ],
      ),
    );
  }
}

class PhysicalAttendanceStorage {
  PhysicalAttendanceStorage._();

  static const _uuid = Uuid();
  static const _maxBytes = 12 * 1024 * 1024;

  static String _assetId(String type, String entityId) {
    final clean = ('${type}_${entityId}')
        .replaceAll(RegExp(r'[^A-Za-z0-9_-]'), '_');
    return clean.length <= 190
        ? 'media_$clean'
        : 'media_${clean.substring(0, 184)}';
  }

  static Future<String> register({
    required String companyId,
    required String entityType,
    required PlatformFile picked,
  }) async {
    if (companyId.trim().isEmpty || entityType.trim().isEmpty) {
      throw StateError('Empresa ou tipo de ficha não informado.');
    }
    final bytes = picked.bytes ??
        (picked.path == null ? null : await File(picked.path!).readAsBytes());
    if (bytes == null || bytes.isEmpty) {
      throw StateError('Não foi possível ler o arquivo selecionado.');
    }
    if (bytes.length > _maxBytes) {
      throw StateError('Cada arquivo deve ter no máximo 12 MB.');
    }

    final entityId = _uuid.v4();
    final base = await getApplicationDocumentsDirectory();
    final dir = Directory(
      p.join(base.path, 'auditar_fichas_assinadas', companyId),
    );
    await dir.create(recursive: true);
    var ext = p.extension(picked.name).toLowerCase();
    if (ext.isEmpty && picked.path != null) ext = p.extension(picked.path!).toLowerCase();
    if (ext.isEmpty) ext = '.jpg';
    final safeBase = p.basenameWithoutExtension(picked.name)
        .replaceAll(RegExp(r'[\\/:*?"<>|]'), '_')
        .trim();
    final fileName =
        '${safeBase.isEmpty ? 'ficha_assinada' : safeBase}_${entityId.substring(0, 8)}$ext';
    final local = File(p.join(dir.path, fileName));
    await local.writeAsBytes(Uint8List.fromList(bytes), flush: true);

    final mime = ext == '.pdf'
        ? 'application/pdf'
        : ext == '.png'
            ? 'image/png'
            : ext == '.webp'
                ? 'image/webp'
                : 'image/jpeg';

    final db = await AppDatabase.instance.database;
    await db.insert(
      'media_assets',
      {
        'id': _assetId(entityType, entityId),
        'company_id': companyId,
        'entity_type': entityType,
        'entity_id': entityId,
        'local_path': local.path,
        'drive_file_id': '',
        'file_name': fileName,
        'mime_type': mime,
        'updated_at': DateTime.now().toUtc().toIso8601String(),
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
    return entityId;
  }

  static Future<Map<String, Object?>?> resolve({
    required String companyId,
    required String entityType,
    required String entityId,
  }) async {
    if (entityId.trim().isEmpty) return null;
    try {
      await MediaSyncService.trainingRecordMediaLocalPath(
        companyId: companyId,
        entityType: entityType,
        entityId: entityId,
        restoreIfMissing: true,
      );
    } catch (_) {}
    final db = await AppDatabase.instance.database;
    final rows = await db.query(
      'media_assets',
      where: 'company_id = ? AND entity_type = ? AND entity_id = ?',
      whereArgs: [companyId, entityType, entityId],
      limit: 1,
    );
    return rows.isEmpty ? null : Map<String, Object?>.from(rows.first);
  }
}

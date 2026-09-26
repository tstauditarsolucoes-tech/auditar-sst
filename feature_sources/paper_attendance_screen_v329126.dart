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
import '../models.dart';
import '../services/media_sync_service.dart';

/// Preserves the original paper sheet. It is not a digitally captured signature.
/// Consumes the existing media queue without modifying synchronization or schema.
class PaperAttendanceScreen extends StatefulWidget {
  final String companyId;
  final String recordId;
  final String recordType;
  const PaperAttendanceScreen({
    super.key,
    required this.companyId,
    required this.recordId,
    required this.recordType,
  });

  @override
  State<PaperAttendanceScreen> createState() => _PaperAttendanceScreenState();
}

class _PaperAttendanceScreenState extends State<PaperAttendanceScreen> {
  static const maxBytes = 12 * 1024 * 1024;
  final _otherNames = TextEditingController();
  final _selected = <String>{};
  SstRecord? _record;
  List<Map<String, dynamic>> _files = [];
  bool _loading = true;
  bool _busy = false;

  bool get _training => widget.recordType == 'TREINAMENTO_SESSAO';
  String get _mediaType =>
      _training ? 'paper_training_attendance' : 'paper_dds_attendance';

  List<Map<String, dynamic>> _maps(Object? raw) =>
      raw is List ? raw.whereType<Map>()
          .map((e) => Map<String, dynamic>.from(e)).toList()
          : <Map<String, dynamic>>[];

  List<Map<String, dynamic>> get _people =>
      _maps(_record?.payload[_training ? 'participants' : 'dds_participants']);

  String _personId(Map<String, dynamic> p) {
    if (_training) return (p['id'] ?? '').toString().trim();
    final id = (p['workerId'] ?? '').toString().trim();
    if (id.isNotEmpty) return 'worker:' + id;
    final pre = (p['preAdmissionId'] ?? '').toString().trim();
    return pre.isEmpty ? '' : 'pre:' + pre;
  }

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _otherNames.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    final rows = await AppDatabase.instance.getSstRecords(
      type: widget.recordType, companyId: widget.companyId,
    );
    SstRecord? found;
    for (final r in rows) {
      if (r.id == widget.recordId) { found = r; break; }
    }
    final db = await AppDatabase.instance.database;
    final entries = <Map<String, dynamic>>[];
    for (final entry in _maps(found?.payload['paper_attendance'])) {
      final id = (entry['id'] ?? '').toString();
      final asset = await db.query('media_assets',
        where: 'id = ? AND company_id = ?',
        whereArgs: ['media_' + _mediaType + '_' + id, widget.companyId],
        limit: 1,
      );
      final row = asset.isEmpty ? const <String, Object?>{} : asset.first;
      entries.add({
        ...entry,
        'localPath': (row['local_path'] ?? '').toString(),
        'backedUp': (row['drive_file_id'] ?? '').toString().trim().isNotEmpty,
      });
    }
    if (!mounted) return;
    setState(() { _record = found; _files = entries; _loading = false; });
  }

  void _notify(String value) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(value)));
  }

  String _mime(Uint8List bytes, String name) {
    final ext = p.extension(name).toLowerCase();
    final pdf = bytes.length >= 4 && bytes[0] == 0x25 &&
        bytes[1] == 0x50 && bytes[2] == 0x44 && bytes[3] == 0x46;
    final jpg = bytes.length >= 3 && bytes[0] == 0xFF &&
        bytes[1] == 0xD8 && bytes[2] == 0xFF;
    final png = bytes.length >= 8 && bytes[0] == 0x89 &&
        bytes[1] == 0x50 && bytes[2] == 0x4E && bytes[3] == 0x47;
    if (ext == '.pdf' && pdf) return 'application/pdf';
    if ((ext == '.jpg' || ext == '.jpeg') && jpg) return 'image/jpeg';
    if (ext == '.png' && png) return 'image/png';
    throw StateError('Formato inválido. Use PDF, JPG ou PNG.');
  }

  DateTime? _expiry(DateTime day, int months) {
    if (months <= 0) return null;
    final index = day.month - 1 + months;
    final y = day.year + index ~/ 12;
    final m = index % 12 + 1;
    final next = m == 12 ? DateTime(y + 1, 1, 1) : DateTime(y, m + 1, 1);
    final last = next.subtract(const Duration(days: 1)).day;
    return DateTime(y, m, day.day > last ? last : day.day);
  }

  Future<void> _save(Uint8List bytes, String name) async {
    if (_busy) return;
    if (bytes.isEmpty || bytes.length > maxBytes) {
      _notify('Cada arquivo deve ter até 12 MB.');
      return;
    }
    setState(() => _busy = true);
    try {
      final current = _record;
      if (current == null || current.companyId != widget.companyId ||
          current.type != widget.recordType) {
        throw StateError('Registro ou empresa não encontrado.');
      }
      final mime = _mime(bytes, name);
      final id = const Uuid().v4();
      final dir = Directory(p.join(
        (await getApplicationDocumentsDirectory()).path,
        'auditar_fichas_fisicas', widget.companyId, widget.recordId,
      ));
      await dir.create(recursive: true);
      final local = File(p.join(dir.path, id + p.extension(name).toLowerCase()));
      await local.writeAsBytes(bytes, flush: true);
      final db = await AppDatabase.instance.database;
      await db.insert('media_assets', {
        'id': 'media_' + _mediaType + '_' + id,
        'company_id': widget.companyId,
        'entity_type': _mediaType,
        'entity_id': id,
        'local_path': local.path,
        'drive_file_id': '',
        'file_name': p.basename(local.path),
        'mime_type': mime,
        'updated_at': DateTime.now().toUtc().toIso8601String(),
      }, conflictAlgorithm: ConflictAlgorithm.abort);

      final manual = _otherNames.text
          .split(RegExp(r'[\r\n]+'))
          .map((x) => x.trim()).where((x) => x.isNotEmpty).toList();
      final attachments = _maps(current.payload['paper_attendance']);
      attachments.add({
        'id': id,
        'fileName': name,
        'mimeType': mime,
        'registeredAt': DateTime.now().toUtc().toIso8601String(),
        'participantIds': _selected.toList(),
        'manualNames': manual,
      });
      final payload = Map<String, dynamic>.from(current.payload)
        ..['paper_attendance'] = attachments;
      final controls = <TrainingControl>[];
      if (_training) {
        final people = _maps(payload['participants']);
        final code = (payload['code'] ?? '').toString().trim().toUpperCase();
        final months = int.tryParse((payload['validityMonths'] ?? 0).toString()) ?? 0;
        payload['participants'] = people.map((person) {
          if (!_selected.contains(_personId(person))) return person;
          if ((person['status'] ?? '').toString() == 'ASSINADO') return person;
          final next = <String, dynamic>{
            ...person,
            'status': 'FICHA_FISICA',
            'paperEvidenceId': id,
            'signatureId': '',
            'signedAt': '',
            'confirmationMethod': 'paper',
          };
          final workerId = (person['workerId'] ?? '').toString().trim();
          if (current.status.toUpperCase() == 'FINALIZADO' &&
              workerId.isNotEmpty) {
            controls.add(TrainingControl(
              id: current.id + '_' + workerId,
              workerId: workerId,
              code: code,
              title: current.title,
              trainingDate: current.date,
              expiryDate: _expiry(current.date, months),
              notes: 'Presença comprovada por ficha física • sessão ' + current.id,
            ));
          }
          return next;
        }).toList();
      } else if (manual.isNotEmpty) {
        final names = <String>[];
        final seen = <String>{};
        for (final name in <String>[
          ...(payload['dds_manual_participants'] ?? '').toString()
              .split(RegExp(r'[\r\n]+')), ...manual
        ]) {
          final n = name.trim();
          if (n.isNotEmpty && seen.add(n.toLowerCase())) names.add(n);
        }
        payload['dds_manual_participants'] = names.join('\n');
        final all = <String>[];
        final known = <String>{};
        for (final name in <String>[
          ...(payload['participants'] ?? '').toString()
              .split(RegExp(r'[\r\n]+')), ...names
        ]) {
          final n = name.trim();
          if (n.isNotEmpty && known.add(n.toLowerCase())) all.add(n);
        }
        payload['participants'] = all.join('\n');
      }
      await AppDatabase.instance.upsertSstRecord(SstRecord(
        id: current.id, companyId: current.companyId,
        sectorId: current.sectorId, type: current.type, title: current.title,
        date: current.date, dueDate: current.dueDate, status: current.status,
        priority: current.priority, payload: payload,
      ));
      if (controls.isNotEmpty) {
        await AppDatabase.instance.upsertTrainingControlsBatch(controls);
      }
      unawaited(MediaSyncService.uploadPending(limit: 6)
          .then((_) {}, onError: (Object _) {}));
      _selected.clear();
      _otherNames.clear();
      await _load();
      _notify('Ficha registrada. Confirme o backup antes de excluir o original em papel.');
    } catch (e) {
      _notify('Não foi possível registrar a ficha: ' + e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _selectFiles() async {
    if (_busy) return;
    final picked = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['pdf', 'jpg', 'jpeg', 'png'],
      allowMultiple: true,
      withData: true,
    );
    if (picked == null) return;
    for (final item in picked.files) {
      final bytes = item.bytes ??
          (item.path == null ? null : await File(item.path!).readAsBytes());
      if (bytes == null) { _notify('Arquivo não pôde ser lido: ' + item.name); continue; }
      await _save(bytes, item.name);
    }
  }

  Future<void> _cameraPhoto() async {
    if (_busy || Platform.isWindows) return;
    final file = await ImagePicker().pickImage(
      source: ImageSource.camera, imageQuality: 82, maxWidth: 1800,
    );
    if (file != null) await _save(await file.readAsBytes(), file.name);
  }

  Future<void> _open(Map<String, dynamic> item) async {
    final id = (item['id'] ?? '').toString();
    var path = (item['localPath'] ?? '').toString();
    if (path.isEmpty || !await File(path).exists()) {
      _notify('Tentando recuperar a ficha do backup...');
      path = await MediaSyncService.trainingRecordMediaLocalPath(
        companyId: widget.companyId, entityType: _mediaType, entityId: id,
      ) ?? '';
      await _load();
    }
    if (path.isEmpty || !await File(path).exists()) {
      _notify('Arquivo indisponível. Confira a situação do backup.');
      return;
    }
    if (!mounted) return;
    final file = File(path);
    if ((item['mimeType'] ?? '') == 'application/pdf') {
      await Navigator.of(context).push(MaterialPageRoute<void>(
        builder: (_) => Scaffold(
          appBar: AppBar(title: const Text('Ficha física original')),
          body: PdfPreview(
            build: (_) async => file.readAsBytes(),
            pdfFileName: (item['fileName'] ?? 'ficha.pdf').toString(),
            allowPrinting: true, allowSharing: true,
          ),
        ),
      ));
    } else {
      await showDialog<void>(context: context, builder: (_) => Dialog(
        child: InteractiveViewer(
          minScale: 0.8, maxScale: 6,
          child: Image.file(file, fit: BoxFit.contain),
        ),
      ));
    }
  }

  @override
  Widget build(BuildContext context) {
    final record = _record;
    return Scaffold(
      appBar: AppBar(title: const Text('Ficha de presença em papel')),
      body: _loading ? const Center(child: CircularProgressIndicator()) :
        record == null ? const Center(child: Text('Registro não encontrado.')) :
        ListView(
          padding: const EdgeInsets.fromLTRB(14, 14, 14, 90),
          children: [
            Text(record.title, style: const TextStyle(
              fontSize: 18, fontWeight: FontWeight.w800)),
            const SizedBox(height: 7),
            const Text('Anexe a ficha original em PDF ou fotografe cada página. '
                'A ficha física não equivale a uma assinatura digital.'),
            const SizedBox(height: 14),
            const Text('Selecione quem está na ficha:',
                style: TextStyle(fontWeight: FontWeight.w800)),
            if (_people.isEmpty) const Padding(
              padding: EdgeInsets.symmetric(vertical: 10),
              child: Text('Nenhum participante cadastrado nesta atividade. '
                  'Cadastre-o no DDS ou na turma antes de associar a presença.'),
            ),
            ..._people.map((person) {
              final key = _personId(person);
              return CheckboxListTile(
                dense: true,
                value: _selected.contains(key),
                title: Text((person['name'] ?? 'Participante').toString()),
                subtitle: Text((person['status'] ?? '').toString()),
                onChanged: key.isEmpty || _busy ? null : (checked) => setState(() {
                  if (checked == true) { _selected.add(key); }
                  else { _selected.remove(key); }
                }),
              );
            }),
            if (!_training) TextField(
              controller: _otherNames, maxLines: 3,
              decoration: const InputDecoration(
                labelText: 'Outros nomes legíveis (opcional)',
                hintText: 'Um nome por linha',
              ),
            ),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: _busy ? null : _selectFiles,
              icon: const Icon(Icons.upload_file_outlined),
              label: const Text('Selecionar PDF ou fotos'),
            ),
            if (!Platform.isWindows) ...[
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: _busy ? null : _cameraPhoto,
                icon: const Icon(Icons.camera_alt_outlined),
                label: const Text('Fotografar ficha'),
              ),
            ],
            if (_busy) ...[
              const SizedBox(height: 8),
              const LinearProgressIndicator(),
              const Text('Salvando ficha original...'),
            ],
            const SizedBox(height: 16),
            Text('Fichas anexadas (' + _files.length.toString() + ')',
                style: const TextStyle(fontWeight: FontWeight.w800)),
            if (_files.isEmpty) const Text('Nenhuma ficha anexada.'),
            ..._files.map((item) => Card(
              child: ListTile(
                leading: Icon((item['mimeType'] ?? '') == 'application/pdf'
                    ? Icons.picture_as_pdf_outlined : Icons.image_outlined,
                    color: AuditarBrand.greenDark),
                title: Text((item['fileName'] ?? 'Ficha').toString()),
                subtitle: Text(item['backedUp'] == true
                    ? 'Backup confirmado'
                    : 'Backup pendente de confirmação'),
                trailing: const Icon(Icons.open_in_new),
                onTap: _busy ? null : () => _open(item),
              ),
            )),
            OutlinedButton.icon(
              onPressed: _busy ? null : _load,
              icon: const Icon(Icons.refresh),
              label: const Text('Atualizar estado do backup'),
            ),
          ],
        ),
    );
  }
}

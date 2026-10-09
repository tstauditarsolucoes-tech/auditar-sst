import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';
import 'package:sqflite/sqflite.dart';
import 'package:uuid/uuid.dart';

import '../brand.dart';
import '../database.dart';
import '../models.dart';
import '../services/apps_script_http.dart';
import '../services/auth_service.dart';
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
  bool _aiBusy = false;

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
      // Keep selected names for the next page of the same paper sheet.
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


  // Uses the ALREADY INSTALLED training_record_import PDF analysis endpoint.
  // Images are wrapped in a PDF locally. Nothing in the GS, transport or
  // synchronization pipeline is changed. IA never confirms presence alone.
  String _normalName(String input) {
    var s = input.toLowerCase().trim();
    const accented = 'áàâãäéèêëíìîïóòôõöúùûüçñ';
    const plain = 'aaaaaeeeeiiiiooooouuuucn';
    for (var i = 0; i < accented.length; i++) {
      s = s.replaceAll(accented[i], plain[i]);
    }
    return s.replaceAll(RegExp(r'[^a-z ]'), ' ')
        .replaceAll(RegExp(r'\s+'), ' ').trim();
  }

  Future<Uint8List> _pdfForAi(Uint8List bytes, String mime) async {
    if (mime == 'application/pdf') return bytes;
    if (mime != 'image/jpeg' && mime != 'image/png') {
      throw StateError('A IA aceita PDF, JPG ou PNG.');
    }
    final document = pw.Document();
    final image = pw.MemoryImage(bytes);
    document.addPage(pw.Page(
      pageFormat: PdfPageFormat.a4,
      margin: const pw.EdgeInsets.all(14),
      build: (_) => pw.Center(
        child: pw.Image(image, fit: pw.BoxFit.contain),
      ),
    ));
    return Uint8List.fromList(await document.save());
  }

  Future<void> _readNamesWithAi(Map<String, dynamic> item) async {
    if (_busy || _aiBusy || !mounted) return;
    final id = (item['id'] ?? '').toString().trim();
    if (id.isEmpty) return;
    final endpoint = (await AppDatabase.instance.getSetting(
      'management_panel_endpoint', fallback: '')).trim();
    final syncKey = (await AppDatabase.instance.getSetting(
      'management_panel_sync_key', fallback: '')).trim();
    if (endpoint.isEmpty || syncKey.isEmpty) {
      _notify('Configure a Central Online para usar a leitura por IA. A ficha original permanece salva.');
      return;
    }
    if (!mounted) return;
    setState(() => _aiBusy = true);
    try {
      var path = (item['localPath'] ?? '').toString().trim();
      if (path.isEmpty || !await File(path).exists()) {
        path = await MediaSyncService.trainingRecordMediaLocalPath(
          companyId: widget.companyId,
          entityType: _mediaType,
          entityId: id,
        ) ?? '';
      }
      if (path.isEmpty || !await File(path).exists()) {
        throw StateError('Ficha original indisponível neste aparelho.');
      }
      final bytes = await File(path).readAsBytes();
      final mime = _mime(bytes, (item['fileName'] ?? p.basename(path)).toString());
      final pdf = await _pdfForAi(bytes, mime);
      final response = await AppsScriptHttp.postJson(
        Uri.parse(endpoint),
        {
          'action': 'ai_assistant',
          'syncKey': syncKey,
          'authToken': AuthService.sessionToken,
          'payload': {
            'mode': 'training_record_import',
            'document': 'data:application/pdf;base64,${base64Encode(pdf)}',
          },
        },
        timeout: const Duration(seconds: 65),
        allowLongAndroidRequest: true,
      );
      final decoded = jsonDecode(utf8.decode(
        response.bodyBytes, allowMalformed: true,
      ));
      if (response.statusCode < 200 || response.statusCode >= 300 ||
          decoded is! Map || decoded['ok'] != true) {
        final message = decoded is Map
            ? (decoded['message'] ?? 'A IA não concluiu a leitura.').toString()
            : 'A Central retornou uma resposta inválida.';
        throw StateError(message);
      }
      final result = decoded['result'];
      final rows = result is Map ? result['participants'] : null;
      if (rows is! List) {
        throw StateError('A IA não retornou uma lista de participantes.');
      }
      final names = <String>[];
      final seen = <String>{};
      for (final row in rows) {
        if (row is! Map) continue;
        final name = (row['name'] ?? '').toString().trim();
        final normalized = _normalName(name);
        if (normalized.length < 3 || !seen.add(normalized)) continue;
        names.add(name);
      }
      if (names.isEmpty) {
        _notify('Não foi possível reconhecer nomes com segurança. Confira a ficha e selecione manualmente.');
        return;
      }
      if (!mounted) return;
      await _reviewAiNames(item, names);
    } catch (error) {
      _notify('Não foi possível ler a ficha com IA: $error. Confira manualmente; o arquivo continua salvo.');
    } finally {
      if (mounted) setState(() => _aiBusy = false);
    }
  }

  Future<void> _reviewAiNames(
    Map<String, dynamic> item, List<String> suggestedNames,
  ) async {
    final currentIds = (item['participantIds'] is List)
        ? (item['participantIds'] as List)
            .map((x) => x.toString()).toSet()
        : <String>{};
    final selected = <String>{...currentIds};
    final matched = <String>{};
    final normalizedNames = suggestedNames.map(_normalName).toSet();
    final counts = <String, int>{};
    for (final person in _people) {
      final name = _normalName((person['name'] ?? '').toString());
      if (name.isNotEmpty) counts[name] = (counts[name] ?? 0) + 1;
    }
    for (final person in _people) {
      final key = _personId(person);
      final name = _normalName((person['name'] ?? '').toString());
      if (key.isEmpty || !normalizedNames.contains(name)) continue;
      matched.add(name);
      // Two registered workers with the same name require an explicit choice.
      if (counts[name] == 1) selected.add(key);
    }
    final unmatched = suggestedNames
        .where((name) => !matched.contains(_normalName(name))).toList();
    final manualController = TextEditingController(
      text: _training ? '' : unmatched.join('\n'),
    );
    try {
      final accepted = await showDialog<bool>(
        context: context,
        barrierDismissible: false,
        builder: (dialogContext) => StatefulBuilder(
          builder: (dialogContext, update) => AlertDialog(
            title: const Text('Conferir nomes reconhecidos pela IA'),
            content: SizedBox(
              width: 480,
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('A IA encontrou ${suggestedNames.length} nome(s). '
                        'Confira quem realmente assinou antes de confirmar.'),
                    const SizedBox(height: 10),
                    for (final person in _people)
                      if (_personId(person).isNotEmpty)
                        CheckboxListTile(
                          dense: true,
                          contentPadding: EdgeInsets.zero,
                          title: Text((person['name'] ?? '').toString()),
                          subtitle: normalizedNames.contains(
                              _normalName((person['name'] ?? '').toString()))
                              ? const Text('Nome reconhecido — confira a assinatura')
                              : const Text('Não reconhecido — seleção manual'),
                          value: selected.contains(_personId(person)),
                          onChanged: (on) => update(() {
                            if (on == true) {
                              selected.add(_personId(person));
                            } else {
                              selected.remove(_personId(person));
                            }
                          }),
                        ),
                    if (unmatched.isNotEmpty) ...[
                      const SizedBox(height: 10),
                      const Text('Sem correspondência no cadastro:',
                          style: TextStyle(fontWeight: FontWeight.w700)),
                      Text(unmatched.join('\n')),
                      if (_training)
                        const Text('Cadastre os participantes na turma para vinculá-los. '
                            'Nomes sem correspondência não serão lançados automaticamente.'),
                    ],
                    if (!_training) ...[
                      const SizedBox(height: 10),
                      TextField(
                        controller: manualController,
                        maxLines: 4,
                        decoration: const InputDecoration(
                          labelText: 'Outros nomes legíveis — confira e edite',
                          hintText: 'Um nome por linha',
                        ),
                      ),
                    ],
                    const SizedBox(height: 8),
                    const Text('Os nomes são apenas sugestões. Nenhuma assinatura digital '
                        'será criada pela IA.'),
                  ],
                ),
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(dialogContext, false),
                child: const Text('Cancelar'),
              ),
              FilledButton(
                onPressed: () => Navigator.pop(dialogContext, true),
                child: const Text('Confirmar participantes'),
              ),
            ],
          ),
        ),
      );
      if (accepted != true) return;
      final manual = _training ? <String>[] : manualController.text
          .split(RegExp(r'[\r\n]+'))
          .map((name) => name.trim())
          .where((name) => name.isNotEmpty)
          .toList();
      await _confirmAiReview(
        item, suggestedNames, selected.toList(), manual,
      );
    } finally {
      manualController.dispose();
    }
  }

  Future<void> _confirmAiReview(
    Map<String, dynamic> item,
    List<String> suggestedNames,
    List<String> participantIds,
    List<String> manualNames,
  ) async {
    final id = (item['id'] ?? '').toString();
    final rows = await AppDatabase.instance.getSstRecords(
      type: widget.recordType, companyId: widget.companyId,
    );
    SstRecord? current;
    for (final record in rows) {
      if (record.id == widget.recordId) {
        current = record;
        break;
      }
    }
    if (current == null || current.companyId != widget.companyId) {
      throw StateError('O registro foi alterado. Abra a ficha novamente.');
    }
    final attachments = _maps(current.payload['paper_attendance']);
    final index = attachments.indexWhere((entry) => entry['id'] == id);
    if (index < 0) throw StateError('A ficha não está vinculada ao registro.');
    final original = attachments[index];
    attachments[index] = <String, dynamic>{
      ...original,
      'participantIds': participantIds,
      'manualNames': manualNames,
      'aiRecognizedNames': suggestedNames,
      'reviewedAt': DateTime.now().toUtc().toIso8601String(),
      'reviewMethod': 'ai_with_human_confirmation',
    };
    final payload = Map<String, dynamic>.from(current.payload)
      ..['paper_attendance'] = attachments;
    final selectedIds = participantIds.toSet();
    final controls = <TrainingControl>[];
    if (_training) {
      final people = _maps(payload['participants']);
      final code = (payload['code'] ?? '').toString().trim().toUpperCase();
      final months = int.tryParse(
        (payload['validityMonths'] ?? 0).toString(),
      ) ?? 0;
      payload['participants'] = people.map((person) {
        if (!selectedIds.contains(_personId(person)) ||
            (person['status'] ?? '').toString() == 'ASSINADO') {
          return person;
        }
        final updated = <String, dynamic>{
          ...person,
          'status': 'FICHA_FISICA',
          'paperEvidenceId': id,
          'signatureId': '',
          'signedAt': '',
          'confirmationMethod': 'paper',
        };
        final workerId = (person['workerId'] ?? '').toString().trim();
        if (current!.status.toUpperCase() == 'FINALIZADO' &&
            workerId.isNotEmpty) {
          controls.add(TrainingControl(
            id: current.id + '_' + workerId,
            workerId: workerId,
            code: code,
            title: current.title,
            trainingDate: current.date,
            expiryDate: _expiry(current.date, months),
            notes: 'Presença confirmada na ficha física após revisão • sessão ' + current.id,
          ));
        }
        return updated;
      }).toList();
    } else {
      final names = <String>[];
      final seen = <String>{};
      for (final name in <String>[
        ...(payload['dds_manual_participants'] ?? '').toString()
            .split(RegExp(r'[\r\n]+')),
        ...manualNames,
      ]) {
        final clean = name.trim();
        if (clean.isNotEmpty && seen.add(_normalName(clean))) names.add(clean);
      }
      payload['dds_manual_participants'] = names.join('\n');
      final all = <String>[];
      final allSeen = <String>{};
      for (final name in <String>[
        ...(payload['participants'] ?? '').toString().split(RegExp(r'[\r\n]+')),
        ...names,
      ]) {
        final clean = name.trim();
        if (clean.isNotEmpty && allSeen.add(_normalName(clean))) all.add(clean);
      }
      payload['participants'] = all.join('\n');
    }
    await AppDatabase.instance.upsertSstRecord(SstRecord(
      id: current.id,
      companyId: current.companyId,
      sectorId: current.sectorId,
      type: current.type,
      title: current.title,
      date: current.date,
      dueDate: current.dueDate,
      status: current.status,
      priority: current.priority,
      payload: payload,
    ));
    if (controls.isNotEmpty) {
      await AppDatabase.instance.upsertTrainingControlsBatch(controls);
    }
    await _load();
    _notify('Nomes conferidos e vinculados à ficha original.');
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
              onPressed: _busy || _aiBusy ? null : _selectFiles,
              icon: const Icon(Icons.upload_file_outlined),
              label: const Text('Selecionar PDF ou fotos'),
            ),
            if (!Platform.isWindows) ...[
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: _busy || _aiBusy ? null : _cameraPhoto,
                icon: const Icon(Icons.camera_alt_outlined),
                label: const Text('Fotografar ficha'),
              ),
            ],
            if (_aiBusy) ...[
              const SizedBox(height: 8),
              const LinearProgressIndicator(),
              const Text('A IA está lendo os nomes. Aguarde a conferência...'),
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
            if (_files.isNotEmpty)
              const Padding(
                padding: EdgeInsets.only(bottom: 8),
                child: Text('Toque no ícone de estrelas ao lado de cada ficha para ler os nomes com IA e confirmar os participantes.'),
              ),
            ..._files.map((item) => Card(
              child: ListTile(
                leading: Icon((item['mimeType'] ?? '') == 'application/pdf'
                    ? Icons.picture_as_pdf_outlined : Icons.image_outlined,
                    color: AuditarBrand.greenDark),
                title: Text((item['fileName'] ?? 'Ficha').toString()),
                subtitle: Text(item['backedUp'] == true
                    ? 'Backup confirmado'
                    : 'Backup pendente de confirmação'),
                trailing: IconButton(
                  tooltip: 'Ler nomes da ficha com IA',
                  icon: const Icon(Icons.auto_awesome_outlined),
                  onPressed: _busy || _aiBusy ? null : () => _readNamesWithAi(item),
                ),
                onTap: _busy || _aiBusy ? null : () => _open(item),
              ),
            )),
            OutlinedButton.icon(
              onPressed: _busy || _aiBusy ? null : _load,
              icon: const Icon(Icons.refresh),
              label: const Text('Atualizar estado do backup'),
            ),
          ],
        ),
    );
  }
}

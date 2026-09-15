#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
pubp = root / 'pubspec.yaml'
formp = root / 'lib/screens/sst_record_form_screen.dart'
listp = root / 'lib/screens/sst_records_screen.dart'
pdfp = root / 'lib/services/dds_pdf_service.dart'

pub = pubp.read_text(encoding='utf-8')
form = formp.read_text(encoding='utf-8')
listing = listp.read_text(encoding='utf-8')


def once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Marcador ausente: {label}')
    return text.replace(old, new, 1)

if 'version: 3.29.48+190' not in pub:
    pub = once(pub, 'version: 3.29.47+189', 'version: 3.29.48+190', 'version')

controller_marker = "  final notesController = TextEditingController();\n"
controller_extra = """  final instructorRoleController = TextEditingController();
  final ddsTimeController = TextEditingController();
  final ddsDurationController = TextEditingController();
"""
if 'final instructorRoleController' not in form:
    form = once(form, controller_marker, controller_marker + controller_extra, 'dds controllers')

state_marker = "  bool restoringDdsSignatures = false;\n"
state_extra = """  List<Worker> ddsWorkers = [];
  final Set<String> selectedDdsWorkerIds = <String>{};
"""
if 'List<Worker> ddsWorkers' not in form:
    form = once(form, state_marker, state_marker + state_extra, 'dds worker state')

form = form.replace(
    "      participantsController.text = '${p['participants'] ?? ''}';\n",
    "      participantsController.text = '${p['dds_manual_participants'] ?? p['participants'] ?? ''}';\n",
    1,
)
init_marker = "      subtype = '${p['subtype'] ?? ''}';\n"
init_extra = """      instructorRoleController.text = '${p['instructor_role'] ?? ''}';
      ddsTimeController.text = '${p['dds_time'] ?? ''}';
      ddsDurationController.text = '${p['dds_duration'] ?? ''}';
"""
if "p['instructor_role']" not in form:
    form = once(form, init_marker, init_marker + init_extra, 'init DDS details')

sig_start = "      if (widget.type == 'DDS') {\n        final rawSignatures = p['dds_signatures'];\n"
participant_load = """      if (widget.type == 'DDS') {
        final rawParticipants = p['dds_participants'];
        if (rawParticipants is List) {
          for (final raw in rawParticipants.whereType<Map>()) {
            final workerId = '${raw['workerId'] ?? raw['worker_id'] ?? ''}'.trim();
            if (workerId.isNotEmpty) selectedDdsWorkerIds.add(workerId);
          }
        }
      }
"""
if "final rawParticipants = p['dds_participants'];" not in form:
    form = once(form, sig_start, participant_load + sig_start, 'load DDS participants')

new_marker = "      status = _statuses().first;\n"
new_extra = """      if (widget.type == 'DDS') {
        ddsTimeController.text = DateFormat('HH:mm').format(DateTime.now());
        ddsDurationController.text = '15 min';
      }
"""
if "ddsDurationController.text = '15 min';" not in form:
    form = once(form, new_marker, new_marker + new_extra, 'new DDS defaults')

form = once(
    form,
    "      notesController,\n",
    "      notesController,\n      instructorRoleController,\n      ddsTimeController,\n      ddsDurationController,\n",
    'dispose DDS controllers',
)

load_marker = "    await _loadSectors(selectedCompanyId, notify: false);\n"
if 'await _loadDdsWorkers(selectedCompanyId, notify: false);' not in form:
    form = once(form, load_marker, load_marker + "    if (widget.type == 'DDS') await _loadDdsWorkers(selectedCompanyId, notify: false);\n", 'load DDS workers')

method_marker = "  Future<void> _pickDate({required bool due}) async {\n"
load_workers_method = r'''  Future<void> _loadDdsWorkers(String? companyId, {bool notify = true}) async {
    final loaded = companyId == null || companyId.isEmpty
        ? <Worker>[]
        : await AppDatabase.instance.getWorkers(companyId: companyId);
    selectedDdsWorkerIds.removeWhere(
      (id) => !loaded.any((worker) => worker.id == id),
    );
    if (!mounted) return;
    if (notify) {
      setState(() => ddsWorkers = loaded);
    } else {
      ddsWorkers = loaded;
    }
  }

'''
if 'Future<void> _loadDdsWorkers(' not in form:
    form = once(form, method_marker, load_workers_method + method_marker, 'load workers method')

company_change_old = """                        setState(() {
                          selectedCompanyId = value;
                          selectedSectorId = null;
                        });
                        await _loadSectors(value);
"""
company_change_new = """                        setState(() {
                          selectedCompanyId = value;
                          selectedSectorId = null;
                          selectedDdsWorkerIds.clear();
                        });
                        await _loadSectors(value);
                        if (widget.type == 'DDS') await _loadDdsWorkers(value);
"""
if 'selectedDdsWorkerIds.clear();' not in form:
    form = once(form, company_change_old, company_change_new, 'company change')

save_marker = "    final payload = <String, dynamic>{\n"
save_prep = """    final ddsParticipantNames = widget.type == 'DDS' ? _ddsParticipantNames() : const <String>[];
    final ddsParticipantRows = widget.type == 'DDS' ? _ddsStructuredParticipants() : const <Map<String, dynamic>>[];
"""
if 'final ddsParticipantNames' not in form:
    form = once(form, save_marker, save_prep + save_marker, 'save participant prep')

form = form.replace(
    "      'participants': participantsController.text.trim(),\n",
    "      'participants': widget.type == 'DDS' ? ddsParticipantNames.join('\\n') : participantsController.text.trim(),\n",
    1,
)
payload_marker = "      if (widget.type == 'DDS') 'dds_signatures': ddsSignatures,\n"
payload_extra = """      if (widget.type == 'DDS') 'dds_signatures': ddsSignatures,
      if (widget.type == 'DDS') 'dds_participants': ddsParticipantRows,
      if (widget.type == 'DDS') 'dds_manual_participants': participantsController.text.trim(),
      if (widget.type == 'DDS') 'instructor_role': instructorRoleController.text.trim(),
      if (widget.type == 'DDS') 'dds_time': ddsTimeController.text.trim(),
      if (widget.type == 'DDS') 'dds_duration': ddsDurationController.text.trim(),
"""
if "'dds_participants': ddsParticipantRows" not in form:
    form = once(form, payload_marker, payload_extra, 'DDS payload details')

old_dds_fields = """    } else if (widget.type == 'DDS') {
      add(TextFormField(controller: responsibleController, decoration: const InputDecoration(labelText: 'Instrutor / responsável')));
      add(TextFormField(controller: participantsController, maxLines: 4, decoration: const InputDecoration(labelText: 'Participantes', hintText: 'Um nome por linha ou observação da lista')));
      add(_ddsSignaturesCard());
      add(TextFormField(controller: notesController, maxLines: 3, decoration: const InputDecoration(labelText: 'Observações / conteúdo abordado')));
"""
new_dds_fields = """    } else if (widget.type == 'DDS') {
      add(TextFormField(controller: responsibleController, decoration: const InputDecoration(labelText: 'Instrutor / responsável *'), validator: (v) => v == null || v.trim().isEmpty ? 'Informe o instrutor/responsável.' : null));
      add(TextFormField(controller: instructorRoleController, decoration: const InputDecoration(labelText: 'Cargo / função do instrutor')));
      add(TextFormField(controller: locationController, decoration: const InputDecoration(labelText: 'Local do DDS')));
      add(LayoutBuilder(builder: (context, constraints) {
        final time = TextFormField(controller: ddsTimeController, decoration: const InputDecoration(labelText: 'Horário', hintText: 'Ex.: 07:30'));
        final duration = TextFormField(controller: ddsDurationController, decoration: const InputDecoration(labelText: 'Duração / carga horária', hintText: 'Ex.: 15 min'));
        if (constraints.maxWidth < 430) return Column(children: [time, const SizedBox(height: 10), duration]);
        return Row(children: [Expanded(child: time), const SizedBox(width: 8), Expanded(child: duration)]);
      }));
      add(_ddsParticipantsCard());
      add(TextFormField(controller: participantsController, maxLines: 3, decoration: const InputDecoration(labelText: 'Participantes adicionais (opcional)', hintText: 'Um nome por linha para quem não está cadastrado')));
      add(_ddsSignaturesCard());
      add(TextFormField(controller: notesController, maxLines: 5, decoration: const InputDecoration(labelText: 'Conteúdo abordado / orientações *'), validator: (v) => v == null || v.trim().isEmpty ? 'Informe o conteúdo abordado.' : null));
"""
if 'Participantes adicionais (opcional)' not in form:
    form = once(form, old_dds_fields, new_dds_fields, 'DDS fields UI')

old_names = r'''  List<String> _ddsParticipantNames() {
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
'''
new_names = r'''  List<String> _ddsParticipantNames() {
    final seen = <String>{};
    final result = <String>[];
    for (final worker in ddsWorkers) {
      if (!selectedDdsWorkerIds.contains(worker.id)) continue;
      final name = worker.name.trim();
      if (name.isEmpty) continue;
      if (seen.add(name.toLowerCase())) result.add(name);
    }
    for (final raw in participantsController.text.split(RegExp(r'[\r\n]+'))) {
      final name = raw.trim();
      if (name.isEmpty) continue;
      final key = name.toLowerCase();
      if (seen.add(key)) result.add(name);
    }
    return result;
  }

  List<Map<String, dynamic>> _ddsStructuredParticipants() {
    final sectorById = {for (final sector in sectors) sector.id: sector.name};
    final result = <Map<String, dynamic>>[];
    for (final worker in ddsWorkers) {
      if (!selectedDdsWorkerIds.contains(worker.id)) continue;
      result.add({
        'workerId': worker.id,
        'name': worker.name,
        'cpf': worker.cpf,
        'role': worker.role,
        'sectorId': worker.sectorId ?? '',
        'sector': worker.sectorId == null ? '' : (sectorById[worker.sectorId] ?? ''),
      });
    }
    return result;
  }

  Future<void> _selectDdsWorkers() async {
    if (selectedCompanyId == null || selectedCompanyId!.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Selecione a empresa antes de escolher os participantes.')),
      );
      return;
    }
    if (ddsWorkers.isEmpty) {
      await _loadDdsWorkers(selectedCompanyId);
    }
    if (!mounted) return;
    final chosen = <String>{...selectedDdsWorkerIds};
    final search = TextEditingController();
    final result = await showDialog<Set<String>>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) {
          final query = search.text.trim().toLowerCase();
          final visible = ddsWorkers.where((worker) {
            if (query.isEmpty) return true;
            return worker.name.toLowerCase().contains(query) ||
                worker.role.toLowerCase().contains(query) ||
                worker.cpf.toLowerCase().contains(query);
          }).toList();
          final sectorName = {for (final sector in sectors) sector.id: sector.name};
          return AlertDialog(
            title: const Text('Participantes do DDS'),
            content: SizedBox(
              width: 520,
              height: 520,
              child: Column(
                children: [
                  TextField(
                    controller: search,
                    onChanged: (_) => setDialogState(() {}),
                    decoration: const InputDecoration(
                      prefixIcon: Icon(Icons.search),
                      labelText: 'Buscar colaborador',
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      TextButton(
                        onPressed: () => setDialogState(() {
                          for (final worker in visible) chosen.add(worker.id);
                        }),
                        child: const Text('Selecionar exibidos'),
                      ),
                      TextButton(
                        onPressed: () => setDialogState(chosen.clear),
                        child: const Text('Limpar'),
                      ),
                    ],
                  ),
                  Expanded(
                    child: visible.isEmpty
                        ? const Center(child: Text('Nenhum colaborador encontrado.'))
                        : ListView.builder(
                            itemCount: visible.length,
                            itemBuilder: (_, index) {
                              final worker = visible[index];
                              final sector = worker.sectorId == null
                                  ? ''
                                  : (sectorName[worker.sectorId] ?? '');
                              final details = <String>[
                                if (worker.role.trim().isNotEmpty) worker.role.trim(),
                                if (sector.trim().isNotEmpty) sector.trim(),
                                if (worker.cpf.trim().isNotEmpty) 'CPF ${worker.cpf.trim()}',
                              ].join(' • ');
                              return CheckboxListTile(
                                dense: true,
                                value: chosen.contains(worker.id),
                                title: Text(worker.name),
                                subtitle: details.isEmpty ? null : Text(details),
                                onChanged: (value) => setDialogState(() {
                                  if (value == true) {
                                    chosen.add(worker.id);
                                  } else {
                                    chosen.remove(worker.id);
                                  }
                                }),
                              );
                            },
                          ),
                  ),
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(dialogContext),
                child: const Text('Cancelar'),
              ),
              FilledButton(
                onPressed: () => Navigator.pop(dialogContext, chosen),
                child: Text('Confirmar (${chosen.length})'),
              ),
            ],
          );
        },
      ),
    );
    search.dispose();
    if (result == null || !mounted) return;
    setState(() {
      selectedDdsWorkerIds
        ..clear()
        ..addAll(result);
    });
  }

  Widget _ddsParticipantsCard() {
    final selected = ddsWorkers
        .where((worker) => selectedDdsWorkerIds.contains(worker.id))
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
                const Icon(Icons.groups_2_outlined, color: AuditarBrand.greenDark),
                const SizedBox(width: 8),
                const Expanded(
                  child: Text(
                    'Participantes do DDS',
                    style: TextStyle(
                      fontWeight: FontWeight.w800,
                      color: AuditarBrand.navy,
                    ),
                  ),
                ),
                Text('${selected.length}', style: const TextStyle(fontWeight: FontWeight.w800)),
              ],
            ),
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: FilledButton.tonalIcon(
                onPressed: _selectDdsWorkers,
                icon: const Icon(Icons.person_add_alt_1_outlined),
                label: const Text('Selecionar colaboradores'),
              ),
            ),
            if (selected.isNotEmpty) ...[
              const SizedBox(height: 8),
              ...selected.take(6).map(
                    (worker) => Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Row(
                        children: [
                          const Icon(Icons.check_circle, size: 16, color: AuditarBrand.greenDark),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              worker.role.trim().isEmpty
                                  ? worker.name
                                  : '${worker.name} • ${worker.role}',
                              style: const TextStyle(fontSize: 12.5),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
              if (selected.length > 6)
                Text(
                  '+ ${selected.length - 6} participante(s)',
                  style: const TextStyle(color: Colors.black54, fontSize: 12),
                ),
            ],
          ],
        ),
      ),
    );
  }
'''
if 'List<Map<String, dynamic>> _ddsStructuredParticipants()' not in form:
    form = once(form, old_names, new_names, 'participant methods')

updated_marker = """    final updated = <String, dynamic>{
      'id': signatureId,
      'name': result.name,
      'signedAt': result.signedAt.toUtc().toIso8601String(),
    };
"""
updated_new = """    final matchedWorker = ddsWorkers.cast<Worker?>().firstWhere(
          (worker) =>
              worker != null &&
              (worker.id == '${existing?['workerId'] ?? ''}' ||
                  worker.name.trim().toLowerCase() == result.name.trim().toLowerCase()),
          orElse: () => null,
        );
    final sectorById = {for (final sector in sectors) sector.id: sector.name};
    final updated = <String, dynamic>{
      'id': signatureId,
      'name': result.name,
      'signedAt': result.signedAt.toUtc().toIso8601String(),
      if (matchedWorker != null) 'workerId': matchedWorker.id,
      if (matchedWorker != null) 'cpf': matchedWorker.cpf,
      if (matchedWorker != null) 'role': matchedWorker.role,
      if (matchedWorker != null) 'sectorId': matchedWorker.sectorId ?? '',
      if (matchedWorker != null) 'sector': matchedWorker.sectorId == null ? '' : (sectorById[matchedWorker.sectorId] ?? ''),
    };
"""
if "'workerId': matchedWorker.id" not in form:
    form = once(form, updated_marker, updated_new, 'signature metadata')

old_sig_add = """            ddsSignatures.add({
              'id': id,
              'name': name,
              'signedAt': '${item['signedAt'] ?? item['signed_at'] ?? ''}',
            });
"""
new_sig_add = """            ddsSignatures.add({
              'id': id,
              'name': name,
              'signedAt': '${item['signedAt'] ?? item['signed_at'] ?? ''}',
              if ('${item['workerId'] ?? item['worker_id'] ?? ''}'.trim().isNotEmpty)
                'workerId': '${item['workerId'] ?? item['worker_id']}',
              if ('${item['cpf'] ?? ''}'.trim().isNotEmpty) 'cpf': '${item['cpf']}',
              if ('${item['role'] ?? ''}'.trim().isNotEmpty) 'role': '${item['role']}',
              if ('${item['sectorId'] ?? item['sector_id'] ?? ''}'.trim().isNotEmpty)
                'sectorId': '${item['sectorId'] ?? item['sector_id']}',
              if ('${item['sector'] ?? ''}'.trim().isNotEmpty) 'sector': '${item['sector']}',
            });
"""
if "'cpf': '${item['cpf']}'" not in form:
    form = once(form, old_sig_add, new_sig_add, 'signature metadata load')

pdf_service = r'''import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import '../database.dart';
import '../models.dart';
import 'media_sync_service.dart';

class DdsPdfService {
  static Future<Uint8List> generate(SstRecord record) async {
    if (record.type != 'DDS') {
      throw ArgumentError('O registro informado não é um DDS.');
    }
    final companyId = record.companyId ?? '';
    final companies = await AppDatabase.instance.getCompanies(onlyActive: false);
    Company? company;
    for (final item in companies) {
      if (item.id == companyId) {
        company = item;
        break;
      }
    }
    if (company == null) throw StateError('Empresa do DDS não encontrada.');

    final sectors = await AppDatabase.instance.getSectors(companyId, onlyActive: false);
    final workers = await AppDatabase.instance.getWorkers(companyId: companyId, onlyActive: false);
    final sectorById = {for (final item in sectors) item.id: item.name};
    final workerById = {for (final item in workers) item.id: item};
    final workerByName = {
      for (final item in workers) item.name.trim().toLowerCase(): item,
    };

    final payload = record.payload;
    final participantRows = <Map<String, dynamic>>[];
    final seenNames = <String>{};
    final rawStructured = payload['dds_participants'];
    if (rawStructured is List) {
      for (final raw in rawStructured.whereType<Map>()) {
        final map = Map<String, dynamic>.from(raw);
        final workerId = '${map['workerId'] ?? map['worker_id'] ?? ''}'.trim();
        final worker = workerId.isEmpty ? null : workerById[workerId];
        final name = (worker?.name ?? '${map['name'] ?? ''}').trim();
        if (name.isEmpty) continue;
        seenNames.add(name.toLowerCase());
        participantRows.add({
          'workerId': worker?.id ?? workerId,
          'name': name,
          'cpf': worker?.cpf ?? '${map['cpf'] ?? ''}',
          'role': worker?.role ?? '${map['role'] ?? ''}',
          'sector': worker?.sectorId == null
              ? '${map['sector'] ?? ''}'
              : (sectorById[worker!.sectorId] ?? '${map['sector'] ?? ''}'),
        });
      }
    }

    final namesText = '${payload['participants'] ?? ''}';
    for (final raw in namesText.split(RegExp(r'[\r\n]+'))) {
      final name = raw.trim();
      if (name.isEmpty || !seenNames.add(name.toLowerCase())) continue;
      final worker = workerByName[name.toLowerCase()];
      participantRows.add({
        'workerId': worker?.id ?? '',
        'name': name,
        'cpf': worker?.cpf ?? '',
        'role': worker?.role ?? '',
        'sector': worker?.sectorId == null ? '' : (sectorById[worker!.sectorId] ?? ''),
      });
    }

    final signatures = <Map<String, dynamic>>[];
    final rawSignatures = payload['dds_signatures'];
    if (rawSignatures is List) {
      for (final raw in rawSignatures.whereType<Map>()) {
        final map = Map<String, dynamic>.from(raw);
        final id = '${map['id'] ?? ''}'.trim();
        final name = '${map['name'] ?? ''}'.trim();
        if (id.isEmpty || name.isEmpty) continue;
        signatures.add(map);
      }
    }

    final signaturesByWorker = <String, Map<String, dynamic>>{};
    final signaturesByName = <String, Map<String, dynamic>>{};
    for (final signature in signatures) {
      final workerId = '${signature['workerId'] ?? signature['worker_id'] ?? ''}'.trim();
      final name = '${signature['name'] ?? ''}'.trim().toLowerCase();
      if (workerId.isNotEmpty) signaturesByWorker[workerId] = signature;
      if (name.isNotEmpty) signaturesByName[name] = signature;
    }

    for (final row in participantRows) {
      final workerId = '${row['workerId'] ?? ''}'.trim();
      final name = '${row['name'] ?? ''}'.trim().toLowerCase();
      final signature = workerId.isNotEmpty
          ? (signaturesByWorker[workerId] ?? signaturesByName[name])
          : signaturesByName[name];
      if (signature == null) continue;
      row['signatureId'] = '${signature['id'] ?? ''}';
      row['signedAt'] = '${signature['signedAt'] ?? signature['signed_at'] ?? ''}';
      final signatureId = '${row['signatureId'] ?? ''}'.trim();
      if (signatureId.isEmpty) continue;
      try {
        final path = await MediaSyncService.ddsSignatureLocalPath(
          companyId: companyId,
          signatureId: signatureId,
        );
        if (path != null && path.isNotEmpty && await File(path).exists()) {
          row['signatureBytes'] = await File(path).readAsBytes();
        }
      } catch (_) {}
    }

    final doc = pw.Document();
    final companyLogo = await _loadFileImage(company.logoPath);
    final auditarLogo = await _loadAssetImage('assets/branding/auditar_logo.jpg');
    final selectedSector = record.sectorId == null ? '' : (sectorById[record.sectorId] ?? '');
    final content = '${payload['notes'] ?? ''}'.trim();
    final location = '${payload['location'] ?? ''}'.trim();
    final instructor = '${payload['responsible'] ?? payload['instructor'] ?? ''}'.trim();
    final instructorRole = '${payload['instructor_role'] ?? ''}'.trim();
    final time = '${payload['dds_time'] ?? ''}'.trim();
    final duration = '${payload['dds_duration'] ?? ''}'.trim();
    final signedCount = participantRows.where((row) => '${row['signatureId'] ?? ''}'.trim().isNotEmpty).length;
    final missing = participantRows
        .where((row) => '${row['signatureId'] ?? ''}'.trim().isEmpty)
        .map((row) => '${row['name'] ?? ''}'.trim())
        .where((name) => name.isNotEmpty)
        .toList();
    final issueDate = DateFormat('dd/MM/yyyy HH:mm').format(DateTime.now());

    doc.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.fromLTRB(28, 24, 28, 28),
        footer: (context) => pw.Container(
          padding: const pw.EdgeInsets.only(top: 6),
          decoration: const pw.BoxDecoration(
            border: pw.Border(top: pw.BorderSide(color: PdfColors.grey400, width: .5)),
          ),
          child: pw.Row(
            mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
            children: [
              pw.Text('DDS ${record.id}', style: const pw.TextStyle(fontSize: 6.5, color: PdfColors.grey700)),
              pw.Text('Página ${context.pageNumber} de ${context.pagesCount}', style: const pw.TextStyle(fontSize: 6.5, color: PdfColors.grey700)),
            ],
          ),
        ),
        build: (context) => [
          pw.Row(
            crossAxisAlignment: pw.CrossAxisAlignment.center,
            children: [
              if (companyLogo != null)
                pw.SizedBox(width: 72, height: 42, child: pw.Image(companyLogo, fit: pw.BoxFit.contain))
              else if (auditarLogo != null)
                pw.SizedBox(width: 72, height: 42, child: pw.Image(auditarLogo, fit: pw.BoxFit.contain)),
              pw.SizedBox(width: 12),
              pw.Expanded(
                child: pw.Column(
                  crossAxisAlignment: pw.CrossAxisAlignment.center,
                  children: [
                    pw.Text('REGISTRO DE DDS', style: pw.TextStyle(fontSize: 15, fontWeight: pw.FontWeight.bold)),
                    pw.SizedBox(height: 2),
                    pw.Text('Diálogo Diário de Segurança', style: const pw.TextStyle(fontSize: 9)),
                  ],
                ),
              ),
              if (companyLogo != null && auditarLogo != null) ...[
                pw.SizedBox(width: 12),
                pw.SizedBox(width: 72, height: 42, child: pw.Image(auditarLogo, fit: pw.BoxFit.contain)),
              ],
            ],
          ),
          pw.SizedBox(height: 10),
          _infoTable([
            ['Empresa', company.name, 'CNPJ', (company.cnpj ?? '').trim().isEmpty ? '-' : company.cnpj!.trim()],
            ['Tema do DDS', record.title, 'Situação', record.status],
            ['Data', DateFormat('dd/MM/yyyy').format(record.date), 'Horário', time.isEmpty ? '-' : time],
            ['Duração', duration.isEmpty ? '-' : duration, 'Setor', selectedSector.isEmpty ? 'Geral / não informado' : selectedSector],
            ['Local', location.isEmpty ? '-' : location, 'Prioridade', record.priority],
            ['Instrutor', instructor.isEmpty ? '-' : instructor, 'Cargo/Função', instructorRole.isEmpty ? '-' : instructorRole],
          ]),
          pw.SizedBox(height: 8),
          pw.Container(
            width: double.infinity,
            padding: const pw.EdgeInsets.all(8),
            decoration: pw.BoxDecoration(
              border: pw.Border.all(color: PdfColors.grey500, width: .6),
              borderRadius: pw.BorderRadius.circular(3),
            ),
            child: pw.Column(
              crossAxisAlignment: pw.CrossAxisAlignment.start,
              children: [
                pw.Text('CONTEÚDO ABORDADO / ORIENTAÇÕES', style: pw.TextStyle(fontSize: 8, fontWeight: pw.FontWeight.bold)),
                pw.SizedBox(height: 4),
                pw.Text(content.isEmpty ? '-' : content, style: const pw.TextStyle(fontSize: 8.5), textAlign: pw.TextAlign.justify),
              ],
            ),
          ),
          pw.SizedBox(height: 10),
          pw.Row(
            mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
            children: [
              pw.Text('LISTA DE PRESENÇA E ASSINATURAS', style: pw.TextStyle(fontSize: 9, fontWeight: pw.FontWeight.bold)),
              pw.Text('${participantRows.length} participante(s) • $signedCount assinado(s)', style: const pw.TextStyle(fontSize: 7.5, color: PdfColors.grey700)),
            ],
          ),
          pw.SizedBox(height: 5),
          if (participantRows.isEmpty)
            pw.Container(
              padding: const pw.EdgeInsets.all(10),
              decoration: pw.BoxDecoration(border: pw.Border.all(color: PdfColors.grey400)),
              child: pw.Text('Nenhum participante informado.', style: const pw.TextStyle(fontSize: 8)),
            )
          else
            _participantTable(participantRows),
          pw.SizedBox(height: 8),
          pw.Container(
            width: double.infinity,
            padding: const pw.EdgeInsets.all(7),
            color: PdfColors.grey100,
            child: pw.Column(
              crossAxisAlignment: pw.CrossAxisAlignment.start,
              children: [
                pw.Text('Resumo: ${participantRows.length} participante(s), $signedCount assinatura(s), ${missing.length} sem assinatura.', style: pw.TextStyle(fontSize: 7.5, fontWeight: pw.FontWeight.bold)),
                if (missing.isNotEmpty) ...[
                  pw.SizedBox(height: 3),
                  pw.Text('Sem assinatura / ausentes: ${missing.join(', ')}', style: const pw.TextStyle(fontSize: 7)),
                ],
                pw.SizedBox(height: 3),
                pw.Text('As assinaturas apresentadas foram coletadas eletronicamente no aplicativo Auditar SST e vinculadas a este registro.', style: const pw.TextStyle(fontSize: 6.8, color: PdfColors.grey700)),
                pw.Text('Identificador do DDS: ${record.id} • Documento emitido em $issueDate', style: const pw.TextStyle(fontSize: 6.8, color: PdfColors.grey700)),
              ],
            ),
          ),
        ],
      ),
    );
    return doc.save();
  }

  static pw.Widget _infoTable(List<List<String>> rows) {
    return pw.Table(
      border: pw.TableBorder.all(color: PdfColors.grey500, width: .5),
      columnWidths: const {
        0: pw.FixedColumnWidth(60),
        1: pw.FlexColumnWidth(2.2),
        2: pw.FixedColumnWidth(58),
        3: pw.FlexColumnWidth(1.5),
      },
      children: rows.map((row) {
        return pw.TableRow(
          children: [
            _cell(row[0], bold: true, background: PdfColors.grey200),
            _cell(row[1]),
            _cell(row[2], bold: true, background: PdfColors.grey200),
            _cell(row[3]),
          ],
        );
      }).toList(),
    );
  }

  static pw.Widget _participantTable(List<Map<String, dynamic>> rows) {
    final tableRows = <pw.TableRow>[
      pw.TableRow(
        repeat: true,
        decoration: const pw.BoxDecoration(color: PdfColors.grey300),
        children: [
          _cell('Nº', bold: true, fontSize: 6.7, align: pw.TextAlign.center),
          _cell('Nome', bold: true, fontSize: 6.7),
          _cell('CPF', bold: true, fontSize: 6.7),
          _cell('Cargo', bold: true, fontSize: 6.7),
          _cell('Setor', bold: true, fontSize: 6.7),
          _cell('Assinatura', bold: true, fontSize: 6.7, align: pw.TextAlign.center),
          _cell('Data/Hora', bold: true, fontSize: 6.7, align: pw.TextAlign.center),
        ],
      ),
    ];
    for (var i = 0; i < rows.length; i++) {
      final row = rows[i];
      final bytes = row['signatureBytes'];
      final signedAt = DateTime.tryParse('${row['signedAt'] ?? ''}')?.toLocal();
      tableRows.add(
        pw.TableRow(
          children: [
            _cell('${i + 1}', fontSize: 6.5, align: pw.TextAlign.center),
            _cell('${row['name'] ?? ''}', fontSize: 6.5),
            _cell('${row['cpf'] ?? ''}'.trim().isEmpty ? '-' : '${row['cpf']}', fontSize: 6.2),
            _cell('${row['role'] ?? ''}'.trim().isEmpty ? '-' : '${row['role']}', fontSize: 6.2),
            _cell('${row['sector'] ?? ''}'.trim().isEmpty ? '-' : '${row['sector']}', fontSize: 6.2),
            pw.Container(
              height: 32,
              padding: const pw.EdgeInsets.all(2),
              alignment: pw.Alignment.center,
              child: bytes is Uint8List && bytes.isNotEmpty
                  ? pw.Image(pw.MemoryImage(bytes), fit: pw.BoxFit.contain)
                  : pw.Text('Pendente', style: const pw.TextStyle(fontSize: 6, color: PdfColors.grey700)),
            ),
            _cell(signedAt == null ? '-' : DateFormat('dd/MM/yy\nHH:mm').format(signedAt), fontSize: 6.1, align: pw.TextAlign.center),
          ],
        ),
      );
    }
    return pw.Table(
      border: pw.TableBorder.all(color: PdfColors.grey500, width: .45),
      columnWidths: const {
        0: pw.FixedColumnWidth(18),
        1: pw.FlexColumnWidth(2.2),
        2: pw.FixedColumnWidth(66),
        3: pw.FixedColumnWidth(70),
        4: pw.FixedColumnWidth(62),
        5: pw.FixedColumnWidth(78),
        6: pw.FixedColumnWidth(54),
      },
      children: tableRows,
    );
  }

  static pw.Widget _cell(
    String text, {
    bool bold = false,
    PdfColor? background,
    double fontSize = 7.2,
    pw.TextAlign align = pw.TextAlign.left,
  }) {
    return pw.Container(
      color: background,
      padding: const pw.EdgeInsets.symmetric(horizontal: 4, vertical: 4),
      child: pw.Text(
        text,
        textAlign: align,
        style: pw.TextStyle(
          fontSize: fontSize,
          fontWeight: bold ? pw.FontWeight.bold : pw.FontWeight.normal,
        ),
      ),
    );
  }

  static Future<pw.MemoryImage?> _loadFileImage(String? path) async {
    final value = path?.trim() ?? '';
    if (value.isEmpty) return null;
    try {
      final file = File(value);
      if (!await file.exists()) return null;
      final bytes = await file.readAsBytes();
      if (bytes.isEmpty) return null;
      return pw.MemoryImage(bytes);
    } catch (_) {
      return null;
    }
  }

  static Future<pw.MemoryImage?> _loadAssetImage(String asset) async {
    try {
      final data = await rootBundle.load(asset);
      return pw.MemoryImage(data.buffer.asUint8List());
    } catch (_) {
      return null;
    }
  }
}
'''
pdfp.write_text(pdf_service, encoding='utf-8', newline='\n')

listing = once(
    listing,
    "import 'package:intl/intl.dart';\n",
    "import 'package:intl/intl.dart';\nimport 'package:printing/printing.dart';\n",
    'printing import',
)
listing = once(
    listing,
    "import '../models.dart';\n",
    "import '../models.dart';\nimport '../services/dds_pdf_service.dart';\n",
    'DDS PDF import',
)

list_method_marker = "  @override\n  Widget build(BuildContext context) {\n"
pdf_method = r'''  Future<void> _generateDdsPdf(SstRecord record) async {
    if (record.type != 'DDS') return;
    if (!mounted) return;
    showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (_) => const AlertDialog(
        content: Row(
          children: [
            CircularProgressIndicator(),
            SizedBox(width: 16),
            Expanded(child: Text('Gerando lista do DDS...')),
          ],
        ),
      ),
    );
    try {
      final bytes = await DdsPdfService.generate(record);
      if (mounted) Navigator.of(context, rootNavigator: true).pop();
      final safeTitle = record.title
          .replaceAll(RegExp(r'[^A-Za-z0-9À-ÿ _-]'), '')
          .trim()
          .replaceAll(RegExp(r'\s+'), '_');
      final filename = 'DDS_${safeTitle.isEmpty ? record.id : safeTitle}_${DateFormat('dd-MM-yyyy').format(record.date)}.pdf';
      await Printing.sharePdf(bytes: bytes, filename: filename);
    } catch (error) {
      if (mounted) {
        Navigator.of(context, rootNavigator: true).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Não foi possível gerar o PDF do DDS: $error')),
        );
      }
    }
  }

'''
if 'Future<void> _generateDdsPdf' not in listing:
    listing = once(listing, list_method_marker, pdf_method + list_method_marker, 'generate PDF method')

selection_old = """                onSelected: (value) {
                  if (value == 'edit') _edit(record);
                  if (value == 'delete') _delete(record);
                },
                itemBuilder: (_) => const [
                  PopupMenuItem(value: 'edit', child: Text('Editar')),
                  PopupMenuItem(value: 'delete', child: Text('Excluir')),
                ],
"""
selection_new = """                onSelected: (value) {
                  if (value == 'edit') _edit(record);
                  if (value == 'pdf') _generateDdsPdf(record);
                  if (value == 'delete') _delete(record);
                },
                itemBuilder: (_) => [
                  const PopupMenuItem(value: 'edit', child: Text('Editar')),
                  if (record.type == 'DDS')
                    const PopupMenuItem(
                      value: 'pdf',
                      child: ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: Icon(Icons.picture_as_pdf_outlined),
                        title: Text('Gerar PDF / lista de presença'),
                      ),
                    ),
                  const PopupMenuItem(value: 'delete', child: Text('Excluir')),
                ],
"""
if "value == 'pdf'" not in listing:
    listing = once(listing, selection_old, selection_new, 'PDF popup option')

pubp.write_text(pub, encoding='utf-8', newline='\n')
formp.write_text(form, encoding='utf-8', newline='\n')
listp.write_text(listing, encoding='utf-8', newline='\n')

assert 'version: 3.29.48+190' in pubp.read_text(encoding='utf-8')
ff = formp.read_text(encoding='utf-8')
ll = listp.read_text(encoding='utf-8')
pp = pdfp.read_text(encoding='utf-8')
for needle in [
    'Selecionar colaboradores',
    'Participantes adicionais (opcional)',
    'Duração / carga horária',
    "'dds_participants': ddsParticipantRows",
    "'instructor_role': instructorRoleController.text.trim()",
    "'dds_time': ddsTimeController.text.trim()",
    "'dds_duration': ddsDurationController.text.trim()",
]:
    assert needle in ff, needle
for needle in [
    'REGISTRO DE DDS',
    'LISTA DE PRESENÇA E ASSINATURAS',
    'Data/Hora',
    'Identificador do DDS',
    'Assinatura',
]:
    assert needle in pp, needle
assert 'Gerar PDF / lista de presença' in ll
print('Android v3.29.48+190: DDS formal com colaboradores cadastrados e PDF/lista de presença aplicado.')

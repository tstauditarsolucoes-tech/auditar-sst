#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
if platform not in {'android', 'windows'}:
    raise SystemExit('Uso: patch_training_records_media_v32968_v3306.py <app_dir> <android|windows>')

pubp = root / 'pubspec.yaml'
trainp = root / 'lib/screens/trainings_screen.dart'
mediap = root / 'lib/services/media_sync_service.dart'

pub = pubp.read_text(encoding='utf-8')
train = trainp.read_text(encoding='utf-8')
media = mediap.read_text(encoding='utf-8')

target = '3.29.68+210' if platform == 'android' else '3.30.6+193'
pub, count = re.subn(r'^version:\s*[^\n]+', 'version: ' + target, pub, count=1, flags=re.M)
if count != 1:
    raise RuntimeError('Versão não encontrada')

# ---------------------------------------------------------------------------
# Biblioteca de mídia: fotos e assinaturas do registro de treinamento.
# Usa a fila de mídia existente; não altera o DeviceSyncService.
# ---------------------------------------------------------------------------
media_marker = '  static Future<void> registerCompanyLogo('
media_helpers = r'''  static Future<void> registerTrainingRecordPhoto({
    required String companyId,
    required String photoId,
    required String localPath,
  }) async {
    if (companyId.trim().isEmpty || photoId.trim().isEmpty || localPath.trim().isEmpty) return;
    final db = await AppDatabase.instance.database;
    await _ensureAsset(
      db,
      companyId: companyId,
      entityType: 'training_record_photo',
      entityId: photoId,
      localPath: localPath,
    );
  }

  static Future<void> registerTrainingRecordSignature({
    required String companyId,
    required String signatureId,
    required String localPath,
  }) async {
    if (companyId.trim().isEmpty || signatureId.trim().isEmpty || localPath.trim().isEmpty) return;
    final db = await AppDatabase.instance.database;
    await _ensureAsset(
      db,
      companyId: companyId,
      entityType: 'training_record_signature',
      entityId: signatureId,
      localPath: localPath,
    );
  }

  static Future<String?> trainingRecordMediaLocalPath({
    required String companyId,
    required String entityType,
    required String entityId,
    bool restoreIfMissing = true,
  }) async {
    final cleanCompany = companyId.trim();
    final cleanType = entityType.trim();
    final cleanId = entityId.trim();
    if (cleanCompany.isEmpty || cleanType.isEmpty || cleanId.isEmpty) return null;

    final db = await AppDatabase.instance.database;
    final mediaId = _assetId(cleanType, cleanId);

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
      cleanCompany,
      [
        {'type': cleanType, 'id': cleanId},
      ],
    );
    return currentPath();
  }

  static Future<int> restoreTrainingRecordMedia({
    required String companyId,
    required Iterable<String> photoIds,
    required Iterable<String> signatureIds,
  }) async {
    if (!AuthService.isSignedIn) return 0;
    final refs = <Map<String, String>>[];
    for (final id in photoIds) {
      final clean = id.trim();
      if (clean.isNotEmpty) {
        refs.add({'type': 'training_record_photo', 'id': clean});
      }
    }
    for (final id in signatureIds) {
      final clean = id.trim();
      if (clean.isNotEmpty) {
        refs.add({'type': 'training_record_signature', 'id': clean});
      }
    }
    if (refs.isEmpty) return 0;
    final db = await AppDatabase.instance.database;
    return _restoreEntities(db, companyId, refs);
  }

'''
if 'registerTrainingRecordPhoto({' not in media:
    if media_marker not in media:
        raise RuntimeError('Ponto de mídia não encontrado')
    media = media.replace(media_marker, media_helpers + media_marker, 1)

# ---------------------------------------------------------------------------
# Entrada na tela Treinamentos.
# ---------------------------------------------------------------------------
if "import 'training_records_screen.dart';" not in train:
    marker = "import 'training_requirements_screen.dart';\n"
    if marker not in train:
        raise RuntimeError('Import de training_requirements_screen não encontrado')
    train = train.replace(marker, marker + "import 'training_records_screen.dart';\n", 1)

if "title: 'Fotos e fichas'" not in train:
    marker = """                _trainingActionCard(
                  icon: Icons.groups_rounded,
                  title: 'Criar turma',
"""
    card = """                _trainingActionCard(
                  icon: Icons.photo_library_outlined,
                  title: 'Fotos e fichas',
                  subtitle: 'Treinamentos realizados',
                  color: AuditarBrand.greenDark,
                  onTap: () async {
                    await Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => TrainingRecordsScreen(
                          companyId: widget.companyId!,
                        ),
                      ),
                    );
                    await _load();
                  },
                ),
"""
    if marker not in train:
        raise RuntimeError('Card Criar turma não encontrado')
    train = train.replace(marker, card + marker, 1)

# ---------------------------------------------------------------------------
# Nova tela compartilhada Android + Windows usando sst_records já sincronizado.
# ---------------------------------------------------------------------------
screen = r'''import 'dart:async';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import 'package:printing/printing.dart';
import 'package:signature/signature.dart';
import 'package:uuid/uuid.dart';

import '../brand.dart';
import '../database.dart';
import '../models.dart';
import '../services/media_sync_service.dart';
import '../services/storage_service.dart';
import '../services/training_record_pdf_service.dart';

const _trainingRecordType = 'TREINAMENTO_SESSAO';

List<Map<String, dynamic>> _mapList(Object? raw) {
  if (raw is! List) return <Map<String, dynamic>>[];
  return raw
      .whereType<Map>()
      .map((item) => Map<String, dynamic>.from(item))
      .toList();
}

class TrainingRecordsScreen extends StatefulWidget {
  final String companyId;

  const TrainingRecordsScreen({
    super.key,
    required this.companyId,
  });

  @override
  State<TrainingRecordsScreen> createState() => _TrainingRecordsScreenState();
}

class _TrainingRecordsScreenState extends State<TrainingRecordsScreen> {
  bool loading = true;
  Company? company;
  List<SstRecord> records = <SstRecord>[];
  List<Worker> workers = <Worker>[];
  List<Sector> sectors = <Sector>[];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    if (mounted) setState(() => loading = true);
    final db = AppDatabase.instance;
    final companies = await db.getCompanies(onlyActive: false);
    final result = await Future.wait<Object?>([
      db.getSstRecords(type: _trainingRecordType, companyId: widget.companyId),
      db.getWorkers(companyId: widget.companyId),
      db.getSectors(widget.companyId),
    ]);
    if (!mounted) return;
    setState(() {
      company = companies.where((item) => item.id == widget.companyId).firstOrNull;
      records = (result[0] as List).cast<SstRecord>();
      workers = (result[1] as List).cast<Worker>();
      sectors = (result[2] as List).cast<Sector>();
      loading = false;
    });
  }

  Future<void> _newRecord() async {
    final current = company;
    if (current == null) return;
    if (workers.where((worker) => worker.active).isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Cadastre colaboradores antes de registrar o treinamento.')),
      );
      return;
    }
    final id = await Navigator.of(context).push<String>(
      MaterialPageRoute(
        builder: (_) => TrainingRecordFormScreen(
          company: current,
          workers: workers,
          sectors: sectors,
        ),
      ),
    );
    if (id == null || !mounted) return;
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => TrainingRecordDetailScreen(
          company: current,
          recordId: id,
        ),
      ),
    );
    await _load();
  }

  Future<void> _open(SstRecord record) async {
    final current = company;
    if (current == null) return;
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => TrainingRecordDetailScreen(
          company: current,
          recordId: record.id,
        ),
      ),
    );
    await _load();
  }

  @override
  Widget build(BuildContext context) {
    final current = company;
    return Scaffold(
      appBar: AppBar(title: const Text('Treinamentos realizados')),
      floatingActionButton: current == null
          ? null
          : FloatingActionButton.extended(
              onPressed: _newRecord,
              icon: const Icon(Icons.add_rounded),
              label: const Text('Novo treinamento'),
            ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(14, 14, 14, 96),
          children: [
            Card(
              color: AuditarBrand.navySoft,
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Row(
                  children: [
                    const CircleAvatar(
                      backgroundColor: Colors.white,
                      child: Icon(Icons.photo_library_outlined, color: AuditarBrand.navy),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            current?.name ?? 'Empresa',
                            style: const TextStyle(
                              fontWeight: FontWeight.w900,
                              color: AuditarBrand.navyDark,
                            ),
                          ),
                          const SizedBox(height: 3),
                          const Text(
                            'Fotos do treinamento, participantes, assinaturas e ficha pronta para visualizar ou imprimir.',
                            style: TextStyle(fontSize: 12.5),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            if (loading)
              const Center(
                child: Padding(
                  padding: EdgeInsets.all(30),
                  child: CircularProgressIndicator(),
                ),
              )
            else if (records.isEmpty)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(22),
                  child: Column(
                    children: [
                      const Icon(Icons.school_outlined, size: 42, color: AuditarBrand.navy),
                      const SizedBox(height: 10),
                      const Text(
                        'Nenhum treinamento realizado registrado.',
                        style: TextStyle(fontWeight: FontWeight.w900),
                      ),
                      const SizedBox(height: 6),
                      const Text(
                        'Crie um registro para guardar fotos, colher assinaturas e emitir a ficha do treinamento.',
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 14),
                      FilledButton.icon(
                        onPressed: _newRecord,
                        icon: const Icon(Icons.add),
                        label: const Text('Criar primeiro registro'),
                      ),
                    ],
                  ),
                ),
              )
            else ...[
              const Text(
                'Histórico de treinamentos realizados',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w900,
                  color: AuditarBrand.navy,
                ),
              ),
              const SizedBox(height: 8),
              ...records.map((record) {
                final participants = _mapList(record.payload['participants']);
                final photos = _mapList(record.payload['photos']);
                final signed = participants
                    .where((item) => '${item['status']}' == 'ASSINADO')
                    .length;
                final finalized = record.status.toUpperCase() == 'FINALIZADO';
                final code = '${record.payload['code'] ?? ''}'.trim();
                return Card(
                  child: ListTile(
                    onTap: () => _open(record),
                    leading: CircleAvatar(
                      backgroundColor: finalized
                          ? const Color(0xFFE9F7ED)
                          : const Color(0xFFFFF4DE),
                      child: Icon(
                        finalized ? Icons.verified_outlined : Icons.edit_note_outlined,
                        color: finalized
                            ? AuditarBrand.greenDark
                            : const Color(0xFF8A5A00),
                      ),
                    ),
                    title: Text(
                      [if (code.isNotEmpty) code, record.title].join(' • '),
                      style: const TextStyle(fontWeight: FontWeight.w900),
                    ),
                    subtitle: Text(
                      '${DateFormat('dd/MM/yyyy').format(record.date)} • '
                      '$signed/${participants.length} assinatura(s) • '
                      '${photos.length} foto(s)',
                    ),
                    trailing: const Icon(Icons.chevron_right),
                  ),
                );
              }),
            ],
          ],
        ),
      ),
    );
  }
}

class _TrainingTemplate {
  final String code;
  final String title;
  final String workload;
  final String validity;
  final String content;

  const _TrainingTemplate(
    this.code,
    this.title, {
    this.workload = '',
    this.validity = '',
    this.content = '',
  });
}

const _trainingTemplates = <_TrainingTemplate>[
  _TrainingTemplate('NR 01', 'Disposições Gerais e Gerenciamento de Riscos Ocupacionais', workload: '4'),
  _TrainingTemplate('NR 06', 'Uso, guarda e conservação de EPI', workload: '4'),
  _TrainingTemplate('NR 10', 'Segurança em Instalações e Serviços em Eletricidade'),
  _TrainingTemplate('NR 11', 'Transporte, Movimentação, Armazenagem e Manuseio de Materiais'),
  _TrainingTemplate('NR 12', 'Segurança no Trabalho em Máquinas e Equipamentos'),
  _TrainingTemplate('NR 20', 'Segurança com Inflamáveis e Combustíveis'),
  _TrainingTemplate('NR 23', 'Proteção Contra Incêndios'),
  _TrainingTemplate('NR 33', 'Segurança em Espaços Confinados'),
  _TrainingTemplate('NR 35', 'Trabalho em Altura'),
  _TrainingTemplate('INTEGRAÇÃO', 'Integração de Segurança do Trabalho'),
  _TrainingTemplate('', 'Outro / personalizado'),
];

class TrainingRecordFormScreen extends StatefulWidget {
  final Company company;
  final List<Worker> workers;
  final List<Sector> sectors;

  const TrainingRecordFormScreen({
    super.key,
    required this.company,
    required this.workers,
    required this.sectors,
  });

  @override
  State<TrainingRecordFormScreen> createState() => _TrainingRecordFormScreenState();
}

class _TrainingRecordFormScreenState extends State<TrainingRecordFormScreen> {
  final code = TextEditingController();
  final title = TextEditingController();
  final workload = TextEditingController();
  final validityMonths = TextEditingController();
  final instructor = TextEditingController();
  final instructorRegistry = TextEditingController();
  final location = TextEditingController();
  final content = TextEditingController();
  final description = TextEditingController();
  final search = TextEditingController();

  DateTime date = DateTime.now();
  int templateIndex = 1;
  final Set<String> selected = <String>{};
  String query = '';
  bool saving = false;

  @override
  void initState() {
    super.initState();
    _applyTemplate(templateIndex);
  }

  @override
  void dispose() {
    for (final controller in [
      code,
      title,
      workload,
      validityMonths,
      instructor,
      instructorRegistry,
      location,
      content,
      description,
      search,
    ]) {
      controller.dispose();
    }
    super.dispose();
  }

  Sector? _sector(String? id) {
    if (id == null) return null;
    for (final sector in widget.sectors) {
      if (sector.id == id) return sector;
    }
    return null;
  }

  void _applyTemplate(int index) {
    final template = _trainingTemplates[index];
    setState(() {
      templateIndex = index;
      code.text = template.code;
      title.text = template.title == 'Outro / personalizado' ? '' : template.title;
      workload.text = template.workload;
      validityMonths.text = template.validity;
      if (content.text.trim().isEmpty) content.text = template.content;
    });
  }

  List<Worker> get visibleWorkers {
    final q = query.trim().toLowerCase();
    final rows = widget.workers.where((worker) => worker.active).where((worker) {
      if (q.isEmpty) return true;
      return worker.name.toLowerCase().contains(q) ||
          worker.role.toLowerCase().contains(q) ||
          worker.cpf.toLowerCase().contains(q);
    }).toList();
    rows.sort((a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()));
    return rows;
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: date,
      firstDate: DateTime(2000),
      lastDate: DateTime.now().add(const Duration(days: 730)),
    );
    if (picked != null && mounted) setState(() => date = picked);
  }

  Future<void> _save() async {
    if (title.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Informe o nome do treinamento.')),
      );
      return;
    }
    if (selected.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Selecione pelo menos um participante.')),
      );
      return;
    }

    setState(() => saving = true);
    final id = const Uuid().v4();
    final participants = <Map<String, dynamic>>[];
    for (final worker in widget.workers.where((item) => selected.contains(item.id))) {
      participants.add({
        'id': const Uuid().v4(),
        'workerId': worker.id,
        'name': worker.name,
        'cpf': worker.cpf,
        'role': worker.role,
        'sector': _sector(worker.sectorId)?.name ?? '',
        'status': 'PENDENTE',
        'signatureId': '',
        'signedAt': '',
      });
    }

    final record = SstRecord(
      id: id,
      companyId: widget.company.id,
      type: _trainingRecordType,
      title: title.text.trim(),
      date: DateTime(date.year, date.month, date.day),
      status: 'EM COLETA',
      priority: 'Média',
      payload: {
        'code': code.text.trim().toUpperCase(),
        'workloadHours': double.tryParse(workload.text.trim().replaceAll(',', '.')) ?? 0,
        'validityMonths': int.tryParse(validityMonths.text.trim()) ?? 0,
        'instructorName': instructor.text.trim(),
        'instructorRegistry': instructorRegistry.text.trim(),
        'location': location.text.trim(),
        'content': content.text.trim(),
        'description': description.text.trim(),
        'participants': participants,
        'photos': <Map<String, dynamic>>[],
        'createdAt': DateTime.now().toUtc().toIso8601String(),
        'finalizedAt': '',
      },
    );

    try {
      await AppDatabase.instance.upsertSstRecord(record);
      if (mounted) Navigator.pop(context, id);
    } catch (error) {
      if (!mounted) return;
      setState(() => saving = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Não foi possível criar o treinamento: $error')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final visible = visibleWorkers;
    final allVisible = visible.isNotEmpty &&
        visible.every((worker) => selected.contains(worker.id));

    return Scaffold(
      appBar: AppBar(title: const Text('Registrar treinamento realizado')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(14, 14, 14, 110),
        children: [
          Text(
            widget.company.name,
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w900,
              color: AuditarBrand.navy,
            ),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<int>(
            initialValue: templateIndex,
            isExpanded: true,
            decoration: const InputDecoration(
              labelText: 'Modelo / treinamento',
              prefixIcon: Icon(Icons.school_outlined),
            ),
            items: List.generate(
              _trainingTemplates.length,
              (index) {
                final item = _trainingTemplates[index];
                return DropdownMenuItem(
                  value: index,
                  child: Text(
                    item.code.isEmpty
                        ? item.title
                        : '${item.code} • ${item.title}',
                    overflow: TextOverflow.ellipsis,
                  ),
                );
              },
            ),
            onChanged: (value) {
              if (value != null) _applyTemplate(value);
            },
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                flex: 2,
                child: TextField(
                  controller: code,
                  decoration: const InputDecoration(labelText: 'NR / Código'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                flex: 5,
                child: TextField(
                  controller: title,
                  decoration: const InputDecoration(labelText: 'Treinamento *'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.calendar_today_outlined),
            title: const Text('Data do treinamento'),
            subtitle: Text(DateFormat('dd/MM/yyyy').format(date)),
            trailing: const Icon(Icons.edit_calendar_outlined),
            onTap: _pickDate,
          ),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: workload,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                    labelText: 'Carga horária (h)',
                    hintText: 'Ex.: 4',
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: TextField(
                  controller: validityMonths,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Validade (meses)',
                    hintText: '0 = sem vencimento',
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          TextField(
            controller: instructor,
            decoration: const InputDecoration(
              labelText: 'Instrutor / responsável',
              prefixIcon: Icon(Icons.badge_outlined),
            ),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: instructorRegistry,
            decoration: const InputDecoration(
              labelText: 'Registro / qualificação do instrutor',
            ),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: location,
            decoration: const InputDecoration(
              labelText: 'Local do treinamento',
              prefixIcon: Icon(Icons.location_on_outlined),
            ),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: content,
            maxLines: 5,
            decoration: const InputDecoration(
              labelText: 'Conteúdo programático / assuntos abordados',
            ),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: description,
            maxLines: 3,
            decoration: const InputDecoration(
              labelText: 'Observações',
            ),
          ),
          const SizedBox(height: 18),
          Row(
            children: [
              const Expanded(
                child: Text(
                  'Participantes',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w900,
                    color: AuditarBrand.navy,
                  ),
                ),
              ),
              Text('${selected.length} selecionado(s)'),
            ],
          ),
          const SizedBox(height: 8),
          TextField(
            controller: search,
            onChanged: (value) => setState(() => query = value),
            decoration: const InputDecoration(
              hintText: 'Buscar trabalhador ou cargo',
              prefixIcon: Icon(Icons.search),
            ),
          ),
          CheckboxListTile(
            contentPadding: EdgeInsets.zero,
            value: allVisible,
            tristate: true,
            title: Text(
              allVisible
                  ? 'Desmarcar trabalhadores exibidos'
                  : 'Selecionar trabalhadores exibidos',
              style: const TextStyle(fontWeight: FontWeight.w800),
            ),
            onChanged: (_) {
              setState(() {
                if (allVisible) {
                  selected.removeAll(visible.map((worker) => worker.id));
                } else {
                  selected.addAll(visible.map((worker) => worker.id));
                }
              });
            },
          ),
          ...visible.map(
            (worker) => CheckboxListTile(
              value: selected.contains(worker.id),
              title: Text(
                worker.name,
                style: const TextStyle(fontWeight: FontWeight.w700),
              ),
              subtitle: Text(
                [
                  worker.role,
                  if ((_sector(worker.sectorId)?.name ?? '').isNotEmpty)
                    _sector(worker.sectorId)!.name,
                ].where((item) => item.isNotEmpty).join(' • '),
              ),
              onChanged: (value) {
                setState(() {
                  if (value == true) {
                    selected.add(worker.id);
                  } else {
                    selected.remove(worker.id);
                  }
                });
              },
            ),
          ),
        ],
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: FilledButton.icon(
            onPressed: saving ? null : _save,
            icon: const Icon(Icons.check_circle_outline),
            label: Text(
              saving
                  ? 'Salvando...'
                  : 'Criar registro com ${selected.length} participante(s)',
            ),
          ),
        ),
      ),
    );
  }
}

class TrainingRecordDetailScreen extends StatefulWidget {
  final Company company;
  final String recordId;

  const TrainingRecordDetailScreen({
    super.key,
    required this.company,
    required this.recordId,
  });

  @override
  State<TrainingRecordDetailScreen> createState() => _TrainingRecordDetailScreenState();
}

class _TrainingRecordDetailScreenState extends State<TrainingRecordDetailScreen> {
  final picker = ImagePicker();
  bool loading = true;
  bool busy = false;
  SstRecord? record;
  List<Map<String, dynamic>> participants = <Map<String, dynamic>>[];
  List<Map<String, dynamic>> photos = <Map<String, dynamic>>[];
  final Map<String, String> mediaPaths = <String, String>{};

  bool get finalized => record?.status.toUpperCase() == 'FINALIZADO';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<SstRecord?> _findRecord() async {
    final rows = await AppDatabase.instance.getSstRecords(
      type: _trainingRecordType,
      companyId: widget.company.id,
    );
    for (final item in rows) {
      if (item.id == widget.recordId) return item;
    }
    return null;
  }

  Future<void> _load() async {
    if (mounted) setState(() => loading = true);
    final current = await _findRecord();
    if (current == null) {
      if (!mounted) return;
      setState(() {
        record = null;
        loading = false;
      });
      return;
    }

    final people = _mapList(current.payload['participants']);
    final gallery = _mapList(current.payload['photos']);
    try {
      await MediaSyncService.restoreTrainingRecordMedia(
        companyId: widget.company.id,
        photoIds: gallery.map((item) => '${item['id'] ?? ''}'),
        signatureIds: people.map((item) => '${item['signatureId'] ?? ''}'),
      ).timeout(const Duration(seconds: 45));
    } catch (_) {}

    final loadedPaths = <String, String>{};
    for (final photo in gallery) {
      final id = '${photo['id'] ?? ''}'.trim();
      if (id.isEmpty) continue;
      final path = await MediaSyncService.trainingRecordMediaLocalPath(
        companyId: widget.company.id,
        entityType: 'training_record_photo',
        entityId: id,
        restoreIfMissing: false,
      );
      if (path != null && path.isNotEmpty) loadedPaths['photo:$id'] = path;
    }
    for (final person in people) {
      final id = '${person['signatureId'] ?? ''}'.trim();
      if (id.isEmpty) continue;
      final path = await MediaSyncService.trainingRecordMediaLocalPath(
        companyId: widget.company.id,
        entityType: 'training_record_signature',
        entityId: id,
        restoreIfMissing: false,
      );
      if (path != null && path.isNotEmpty) loadedPaths['signature:$id'] = path;
    }

    if (!mounted) return;
    setState(() {
      record = current;
      participants = people;
      photos = gallery;
      mediaPaths
        ..clear()
        ..addAll(loadedPaths);
      loading = false;
    });
  }

  Future<void> _savePayload({
    String? status,
    Map<String, dynamic>? payload,
  }) async {
    final current = record;
    if (current == null) return;
    final updated = SstRecord(
      id: current.id,
      companyId: current.companyId,
      sectorId: current.sectorId,
      type: current.type,
      title: current.title,
      date: current.date,
      dueDate: current.dueDate,
      status: status ?? current.status,
      priority: current.priority,
      payload: payload ?? current.payload,
    );
    await AppDatabase.instance.upsertSstRecord(updated);
    record = updated;
  }

  Future<void> _sign(Map<String, dynamic> participant) async {
    if (finalized) return;
    final result = await Navigator.of(context).push<TrainingSignatureResult>(
      MaterialPageRoute(
        fullscreenDialog: true,
        builder: (_) => TrainingRecordSignatureScreen(
          participant: participant,
          trainingTitle: record?.title ?? '',
        ),
      ),
    );
    if (result == null || !mounted) return;

    await MediaSyncService.registerTrainingRecordSignature(
      companyId: widget.company.id,
      signatureId: result.signatureId,
      localPath: result.localPath,
    );
    final id = '${participant['id'] ?? ''}';
    final next = participants.map((item) {
      if ('${item['id'] ?? ''}' != id) return item;
      return <String, dynamic>{
        ...item,
        'status': 'ASSINADO',
        'signatureId': result.signatureId,
        'signedAt': result.signedAt.toUtc().toIso8601String(),
      };
    }).toList();

    final payload = Map<String, dynamic>.from(record!.payload)
      ..['participants'] = next;
    await _savePayload(payload: payload);
    mediaPaths['signature:${result.signatureId}'] = result.localPath;
    unawaited(MediaSyncService.uploadPending());
    await _load();
  }

  Future<void> _setParticipantStatus(
    Map<String, dynamic> participant,
    String status,
  ) async {
    if (finalized) return;
    final id = '${participant['id'] ?? ''}';
    final next = participants.map((item) {
      if ('${item['id'] ?? ''}' != id) return item;
      return <String, dynamic>{
        ...item,
        'status': status,
        if (status != 'ASSINADO') 'signatureId': '',
        if (status != 'ASSINADO') 'signedAt': '',
      };
    }).toList();
    final payload = Map<String, dynamic>.from(record!.payload)
      ..['participants'] = next;
    await _savePayload(payload: payload);
    await _load();
  }

  Future<void> _choosePhotoSource() async {
    ImageSource? source;
    if (Platform.isWindows) {
      source = ImageSource.gallery;
    } else {
      source = await showModalBottomSheet<ImageSource>(
        context: context,
        builder: (context) => SafeArea(
          child: Wrap(
            children: [
              ListTile(
                leading: const Icon(Icons.photo_camera_outlined),
                title: const Text('Tirar foto'),
                onTap: () => Navigator.pop(context, ImageSource.camera),
              ),
              ListTile(
                leading: const Icon(Icons.photo_library_outlined),
                title: const Text('Escolher da galeria'),
                onTap: () => Navigator.pop(context, ImageSource.gallery),
              ),
            ],
          ),
        ),
      );
    }
    if (source == null) return;

    final image = await picker.pickImage(
      source: source,
      imageQuality: 82,
      maxWidth: 1800,
    );
    if (image == null) return;

    final local = await StorageService.persistImage(
      image.path,
      folder: 'fotos_treinamentos',
    );
    final photoId = const Uuid().v4();
    await MediaSyncService.registerTrainingRecordPhoto(
      companyId: widget.company.id,
      photoId: photoId,
      localPath: local,
    );

    final next = <Map<String, dynamic>>[
      ...photos,
      {
        'id': photoId,
        'createdAt': DateTime.now().toUtc().toIso8601String(),
        'fileName': image.name,
      },
    ];
    final payload = Map<String, dynamic>.from(record!.payload)
      ..['photos'] = next;
    await _savePayload(payload: payload);
    mediaPaths['photo:$photoId'] = local;
    unawaited(MediaSyncService.uploadPending());
    await _load();
  }

  void _showPhoto(String path) {
    if (path.isEmpty || !File(path).existsSync()) return;
    showDialog<void>(
      context: context,
      builder: (context) => Dialog(
        insetPadding: const EdgeInsets.all(14),
        child: Stack(
          children: [
            Padding(
              padding: const EdgeInsets.all(12),
              child: InteractiveViewer(
                minScale: 0.7,
                maxScale: 6,
                child: Image.file(
                  File(path),
                  fit: BoxFit.contain,
                  width: double.infinity,
                ),
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

  int _count(String status) => participants
      .where((item) => '${item['status'] ?? 'PENDENTE'}' == status)
      .length;

  DateTime _addMonths(DateTime source, int months) {
    final targetMonth = source.month - 1 + months;
    final year = source.year + targetMonth ~/ 12;
    final month = targetMonth % 12 + 1;
    final firstNext = month == 12
        ? DateTime(year + 1, 1, 1)
        : DateTime(year, month + 1, 1);
    final lastDay = firstNext.subtract(const Duration(days: 1)).day;
    final day = source.day > lastDay ? lastDay : source.day;
    return DateTime(year, month, day);
  }

  Future<Uint8List> _pdfBytes() async {
    final current = record;
    if (current == null) throw StateError('Treinamento não encontrado.');

    final signatures = <String, String>{};
    for (final participant in participants) {
      final signatureId = '${participant['signatureId'] ?? ''}'.trim();
      if (signatureId.isEmpty) continue;
      final path = mediaPaths['signature:$signatureId'] ??
          await MediaSyncService.trainingRecordMediaLocalPath(
            companyId: widget.company.id,
            entityType: 'training_record_signature',
            entityId: signatureId,
          );
      if (path != null && path.isNotEmpty) signatures[signatureId] = path;
    }

    final gallery = <String>[];
    for (final photo in photos) {
      final photoId = '${photo['id'] ?? ''}'.trim();
      if (photoId.isEmpty) continue;
      final path = mediaPaths['photo:$photoId'] ??
          await MediaSyncService.trainingRecordMediaLocalPath(
            companyId: widget.company.id,
            entityType: 'training_record_photo',
            entityId: photoId,
          );
      if (path != null && path.isNotEmpty) gallery.add(path);
    }

    return TrainingRecordPdfService.generate(
      company: widget.company,
      record: current,
      participants: participants,
      signaturePaths: signatures,
      photoPaths: gallery,
    );
  }

  String _fileName() {
    final current = record;
    if (current == null) return 'Ficha_Treinamento.pdf';
    final safe = current.title
        .replaceAll(RegExp(r'[^A-Za-z0-9À-ÿ _-]'), '')
        .trim()
        .replaceAll(RegExp(r'\s+'), '_');
    return 'FICHA_TREINAMENTO_${safe.isEmpty ? current.id : safe}_${DateFormat('dd-MM-yyyy').format(current.date)}.pdf';
  }

  Future<void> _previewPdf() async {
    if (busy) return;
    setState(() => busy = true);
    try {
      final bytes = await _pdfBytes();
      await Printing.layoutPdf(
        onLayout: (_) async => bytes,
        name: _fileName(),
      );
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Não foi possível abrir a ficha: $error')),
        );
      }
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> _sharePdf() async {
    if (busy) return;
    setState(() => busy = true);
    try {
      final bytes = await _pdfBytes();
      await Printing.sharePdf(bytes: bytes, filename: _fileName());
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Não foi possível compartilhar a ficha: $error')),
        );
      }
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> _finalize() async {
    if (finalized || busy) return;
    final pending = _count('PENDENTE');
    if (pending > 0) {
      final markAbsent = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Participantes pendentes'),
          content: Text(
            'Existem $pending participante(s) sem assinatura. Deseja marcá-los como ausentes antes de finalizar?',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Voltar'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Marcar ausentes'),
            ),
          ],
        ),
      );
      if (markAbsent != true) return;
      participants = participants.map((item) {
        if ('${item['status']}' != 'PENDENTE') return item;
        return <String, dynamic>{...item, 'status': 'AUSENTE'};
      }).toList();
    }

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Finalizar treinamento?'),
        content: const Text(
          'As assinaturas ficarão bloqueadas. Os participantes assinados serão lançados automaticamente no controle de treinamentos.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Finalizar'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;

    setState(() => busy = true);
    try {
      final current = record!;
      final code = '${current.payload['code'] ?? ''}'.trim().toUpperCase();
      final validity = int.tryParse('${current.payload['validityMonths'] ?? 0}') ?? 0;
      final expiry = validity > 0 ? _addMonths(current.date, validity) : null;
      final controls = <TrainingControl>[];

      for (final participant in participants) {
        if ('${participant['status'] ?? ''}' != 'ASSINADO') continue;
        final workerId = '${participant['workerId'] ?? ''}'.trim();
        if (workerId.isEmpty) continue;
        controls.add(
          TrainingControl(
            id: '${current.id}_$workerId',
            workerId: workerId,
            code: code,
            title: current.title,
            trainingDate: current.date,
            expiryDate: expiry,
            notes: 'Ficha assinada no Auditar SST • sessão ${current.id}',
          ),
        );
      }

      if (controls.isNotEmpty) {
        await AppDatabase.instance.upsertTrainingControlsBatch(controls);
      }

      final payload = Map<String, dynamic>.from(current.payload)
        ..['participants'] = participants
        ..['finalizedAt'] = DateTime.now().toUtc().toIso8601String();
      await _savePayload(status: 'FINALIZADO', payload: payload);
      unawaited(MediaSyncService.uploadPending());
      await _load();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Treinamento finalizado e ficha pronta.')),
        );
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Não foi possível finalizar: $error')),
        );
      }
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> _delete() async {
    if (finalized) return;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Excluir registro?'),
        content: const Text(
          'O registro ainda não finalizado será removido. As mídias já enviadas ao Drive não são apagadas automaticamente.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Excluir'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    await AppDatabase.instance.deleteSstRecord(widget.recordId);
    if (mounted) Navigator.pop(context);
  }

  Widget _metric(String label, int value, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 12),
      decoration: BoxDecoration(
        border: Border.all(color: const Color(0xFFD7DCE5)),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '$value',
            style: TextStyle(
              fontWeight: FontWeight.w900,
              fontSize: 20,
              color: color,
            ),
          ),
          Text(label, style: const TextStyle(fontSize: 11.5)),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (loading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Registro do treinamento')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }
    final current = record;
    if (current == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Registro do treinamento')),
        body: const Center(child: Text('Registro não encontrado.')),
      );
    }

    final signed = _count('ASSINADO');
    final pending = _count('PENDENTE');
    final absent = _count('AUSENTE');
    final code = '${current.payload['code'] ?? ''}'.trim();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Registro do treinamento'),
        actions: [
          IconButton(
            onPressed: busy ? null : _previewPdf,
            tooltip: 'Visualizar / imprimir ficha',
            icon: const Icon(Icons.picture_as_pdf_outlined),
          ),
          IconButton(
            onPressed: busy ? null : _sharePdf,
            tooltip: 'Compartilhar ficha',
            icon: const Icon(Icons.share_outlined),
          ),
          if (!finalized)
            IconButton(
              onPressed: _delete,
              tooltip: 'Excluir',
              icon: const Icon(Icons.delete_outline),
            ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(14, 14, 14, 110),
          children: [
            Card(
              color: finalized
                  ? const Color(0xFFEAF7EE)
                  : AuditarBrand.navySoft,
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            [if (code.isNotEmpty) code, current.title].join(' • '),
                            style: const TextStyle(
                              fontSize: 17,
                              fontWeight: FontWeight.w900,
                              color: AuditarBrand.navyDark,
                            ),
                          ),
                        ),
                        Chip(
                          label: Text(finalized ? 'FINALIZADO' : 'EM COLETA'),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(
                      '${DateFormat('dd/MM/yyyy').format(current.date)} • '
                      '${current.payload['workloadHours'] ?? 0} h',
                    ),
                    if ('${current.payload['instructorName'] ?? ''}'.trim().isNotEmpty)
                      Text(
                        'Instrutor: ${current.payload['instructorName']}'
                        '${'${current.payload['instructorRegistry'] ?? ''}'.trim().isEmpty ? '' : ' • ${current.payload['instructorRegistry']}'}',
                      ),
                    if ('${current.payload['location'] ?? ''}'.trim().isNotEmpty)
                      Text('Local: ${current.payload['location']}'),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(child: _metric('Assinados', signed, AuditarBrand.greenDark)),
                const SizedBox(width: 7),
                Expanded(child: _metric('Pendentes', pending, const Color(0xFFF29D18))),
                const SizedBox(width: 7),
                Expanded(child: _metric('Ausentes', absent, const Color(0xFF7B8495))),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                const Expanded(
                  child: Text(
                    'Fotos do treinamento',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w900,
                      color: AuditarBrand.navy,
                    ),
                  ),
                ),
                FilledButton.tonalIcon(
                  onPressed: busy ? null : _choosePhotoSource,
                  icon: const Icon(Icons.add_a_photo_outlined, size: 18),
                  label: const Text('Adicionar'),
                ),
              ],
            ),
            const SizedBox(height: 8),
            if (photos.isEmpty)
              const Card(
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: Text(
                    'Nenhuma foto adicionada. Registre a turma, prática, instrutor, equipamento ou momento do treinamento.',
                  ),
                ),
              )
            else
              GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: photos.length,
                gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
                  maxCrossAxisExtent: 180,
                  mainAxisSpacing: 8,
                  crossAxisSpacing: 8,
                  childAspectRatio: 1.15,
                ),
                itemBuilder: (context, index) {
                  final photo = photos[index];
                  final id = '${photo['id'] ?? ''}';
                  final path = mediaPaths['photo:$id'] ?? '';
                  return Card(
                    clipBehavior: Clip.antiAlias,
                    margin: EdgeInsets.zero,
                    child: InkWell(
                      onTap: path.isEmpty ? null : () => _showPhoto(path),
                      child: path.isNotEmpty && File(path).existsSync()
                          ? Image.file(File(path), fit: BoxFit.cover)
                          : const Center(
                              child: Column(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(Icons.cloud_download_outlined),
                                  SizedBox(height: 4),
                                  Text('Carregando...', style: TextStyle(fontSize: 11)),
                                ],
                              ),
                            ),
                    ),
                  );
                },
              ),
            const SizedBox(height: 18),
            Row(
              children: [
                const Expanded(
                  child: Text(
                    'Participantes e assinaturas',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w900,
                      color: AuditarBrand.navy,
                    ),
                  ),
                ),
                Text('$signed/${participants.length}'),
              ],
            ),
            const SizedBox(height: 8),
            ...participants.map((participant) {
              final status = '${participant['status'] ?? 'PENDENTE'}';
              final color = status == 'ASSINADO'
                  ? AuditarBrand.greenDark
                  : status == 'AUSENTE'
                      ? const Color(0xFF7B8495)
                      : const Color(0xFFF29D18);
              final signatureId = '${participant['signatureId'] ?? ''}'.trim();
              final signaturePath = signatureId.isEmpty
                  ? ''
                  : mediaPaths['signature:$signatureId'] ?? '';

              return Card(
                child: Column(
                  children: [
                    ListTile(
                      onTap: finalized ? null : () => _sign(participant),
                      leading: CircleAvatar(
                        backgroundColor: color.withValues(alpha: .12),
                        child: Icon(
                          status == 'ASSINADO'
                              ? Icons.draw_outlined
                              : status == 'AUSENTE'
                                  ? Icons.person_off_outlined
                                  : Icons.pending_actions_outlined,
                          color: color,
                        ),
                      ),
                      title: Text(
                        '${participant['name'] ?? ''}',
                        style: const TextStyle(fontWeight: FontWeight.w800),
                      ),
                      subtitle: Text(
                        [
                          if ('${participant['role'] ?? ''}'.trim().isNotEmpty)
                            '${participant['role']}',
                          if ('${participant['sector'] ?? ''}'.trim().isNotEmpty)
                            '${participant['sector']}',
                          status,
                        ].join(' • '),
                      ),
                      trailing: finalized
                          ? Icon(
                              status == 'ASSINADO'
                                  ? Icons.verified_outlined
                                  : Icons.remove_circle_outline,
                              color: color,
                            )
                          : PopupMenuButton<String>(
                              onSelected: (value) {
                                if (value == 'sign') _sign(participant);
                                if (value == 'absent') {
                                  _setParticipantStatus(participant, 'AUSENTE');
                                }
                                if (value == 'pending') {
                                  _setParticipantStatus(participant, 'PENDENTE');
                                }
                              },
                              itemBuilder: (_) => [
                                PopupMenuItem(
                                  value: 'sign',
                                  child: Text(
                                    status == 'ASSINADO'
                                        ? 'Refazer assinatura'
                                        : 'Coletar assinatura',
                                  ),
                                ),
                                const PopupMenuItem(
                                  value: 'absent',
                                  child: Text('Marcar ausente'),
                                ),
                                if (status != 'PENDENTE')
                                  const PopupMenuItem(
                                    value: 'pending',
                                    child: Text('Voltar para pendente'),
                                  ),
                              ],
                            ),
                    ),
                    if (signaturePath.isNotEmpty &&
                        File(signaturePath).existsSync())
                      Container(
                        height: 58,
                        width: double.infinity,
                        margin: const EdgeInsets.fromLTRB(14, 0, 14, 12),
                        color: Colors.white,
                        child: Image.file(
                          File(signaturePath),
                          fit: BoxFit.contain,
                        ),
                      ),
                  ],
                ),
              );
            }),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: busy ? null : _previewPdf,
              icon: const Icon(Icons.print_outlined),
              label: const Text('Visualizar / imprimir ficha de assinaturas'),
            ),
          ],
        ),
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: finalized
              ? FilledButton.icon(
                  onPressed: busy ? null : _previewPdf,
                  icon: const Icon(Icons.picture_as_pdf_outlined),
                  label: const Text('Abrir ficha assinada'),
                )
              : FilledButton.icon(
                  onPressed: busy ? null : _finalize,
                  icon: const Icon(Icons.verified_outlined),
                  label: Text(
                    pending > 0
                        ? 'Finalizar ($pending pendente(s))'
                        : 'Finalizar treinamento',
                  ),
                ),
        ),
      ),
    );
  }
}

class TrainingSignatureResult {
  final String signatureId;
  final String localPath;
  final DateTime signedAt;

  const TrainingSignatureResult({
    required this.signatureId,
    required this.localPath,
    required this.signedAt,
  });
}

class TrainingRecordSignatureScreen extends StatefulWidget {
  final Map<String, dynamic> participant;
  final String trainingTitle;

  const TrainingRecordSignatureScreen({
    super.key,
    required this.participant,
    required this.trainingTitle,
  });

  @override
  State<TrainingRecordSignatureScreen> createState() => _TrainingRecordSignatureScreenState();
}

class _TrainingRecordSignatureScreenState extends State<TrainingRecordSignatureScreen> {
  final controller = SignatureController(
    penStrokeWidth: 3,
    penColor: Colors.black,
    exportBackgroundColor: Colors.white,
  );
  bool saving = false;

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (controller.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Faça a assinatura antes de confirmar.')),
      );
      return;
    }
    setState(() => saving = true);
    try {
      final bytes = await controller.toPngBytes(width: 700, height: 220);
      if (bytes == null || bytes.isEmpty) {
        throw StateError('Não foi possível gerar a assinatura.');
      }
      final path = await StorageService.persistPngBytes(
        bytes,
        folder: 'assinaturas_treinamentos',
      );
      if (!mounted) return;
      Navigator.pop(
        context,
        TrainingSignatureResult(
          signatureId: const Uuid().v4(),
          localPath: path,
          signedAt: DateTime.now(),
        ),
      );
    } catch (error) {
      if (!mounted) return;
      setState(() => saving = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Não foi possível salvar a assinatura: $error')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final name = '${widget.participant['name'] ?? ''}';
    final cpf = '${widget.participant['cpf'] ?? ''}'.trim();

    return Scaffold(
      appBar: AppBar(title: const Text('Assinatura do participante')),
      body: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              name,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w900,
                color: AuditarBrand.navy,
              ),
            ),
            if (cpf.isNotEmpty) Text('CPF: $cpf'),
            const SizedBox(height: 5),
            Text(
              widget.trainingTitle,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 10),
            const Text(
              'Ao assinar, o participante confirma sua presença no treinamento acima. A assinatura ficará vinculada à ficha, data e empresa.',
              style: TextStyle(fontSize: 12.5, color: Colors.black54),
            ),
            const SizedBox(height: 12),
            Expanded(
              child: Container(
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Colors.white,
                  border: Border.all(
                    color: const Color(0xFFBFC6D2),
                    width: 1.5,
                  ),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Signature(
                  controller: controller,
                  backgroundColor: Colors.white,
                ),
              ),
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: saving ? null : controller.clear,
                    icon: const Icon(Icons.delete_sweep_outlined),
                    label: const Text('Limpar'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  flex: 2,
                  child: FilledButton.icon(
                    onPressed: saving ? null : _save,
                    icon: const Icon(Icons.check_circle_outline),
                    label: Text(saving ? 'Salvando...' : 'Confirmar assinatura'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
'''

pdf = r'''import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import '../models.dart';

class TrainingRecordPdfService {
  static const navy = PdfColor(0.113725, 0.180392, 0.423529);
  static const line = PdfColors.grey500;

  static Future<Uint8List> generate({
    required Company company,
    required SstRecord record,
    required List<Map<String, dynamic>> participants,
    required Map<String, String> signaturePaths,
    required List<String> photoPaths,
  }) async {
    final doc = pw.Document();
    final auditarLogo = await _asset('assets/branding/auditar_logo.jpg');
    final companyLogo = await _fileImage(company.logoPath);
    final payload = record.payload;
    final code = '${payload['code'] ?? ''}'.trim();
    final workload = double.tryParse('${payload['workloadHours'] ?? 0}') ?? 0;
    final signed = participants
        .where((item) => '${item['status'] ?? ''}' == 'ASSINADO')
        .length;

    final participantRows = <pw.TableRow>[
      pw.TableRow(
        repeat: true,
        decoration: const pw.BoxDecoration(color: PdfColors.grey200),
        children: [
          _cell('Nº', bold: true, align: pw.TextAlign.center),
          _cell('Participante', bold: true),
          _cell('Cargo / setor', bold: true),
          _cell('Assinatura', bold: true, align: pw.TextAlign.center),
          _cell('Situação', bold: true, align: pw.TextAlign.center),
        ],
      ),
    ];

    for (var i = 0; i < participants.length; i++) {
      final person = participants[i];
      final status = '${person['status'] ?? 'PENDENTE'}';
      final signatureId = '${person['signatureId'] ?? ''}'.trim();
      final signature = signatureId.isEmpty
          ? null
          : await _fileImage(signaturePaths[signatureId]);
      participantRows.add(
        pw.TableRow(
          children: [
            _cell('${i + 1}', align: pw.TextAlign.center),
            _cell(
              '${person['name'] ?? '-'}'
              '${'${person['cpf'] ?? ''}'.trim().isEmpty ? '' : '\nCPF: ${person['cpf']}'}',
            ),
            _cell(
              [
                '${person['role'] ?? ''}',
                '${person['sector'] ?? ''}',
              ].where((item) => item.trim().isNotEmpty).join('\n'),
            ),
            pw.Container(
              height: 38,
              padding: const pw.EdgeInsets.all(3),
              alignment: pw.Alignment.center,
              child: signature == null
                  ? pw.Text(
                      status == 'AUSENTE' ? 'AUSENTE' : '',
                      style: const pw.TextStyle(
                        fontSize: 7,
                        color: PdfColors.grey700,
                      ),
                    )
                  : pw.Image(signature, height: 31, fit: pw.BoxFit.contain),
            ),
            _cell(status, align: pw.TextAlign.center),
          ],
        ),
      );
    }

    doc.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.fromLTRB(26, 22, 26, 28),
        header: (_) => _header(auditarLogo, companyLogo),
        footer: (context) => pw.Row(
          mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
          children: [
            pw.Text(
              'Auditar SST • $signed assinatura(s) eletrônica(s)',
              style: const pw.TextStyle(fontSize: 7, color: PdfColors.grey600),
            ),
            pw.Text(
              'Página ${context.pageNumber} de ${context.pagesCount}',
              style: const pw.TextStyle(fontSize: 7, color: PdfColors.grey600),
            ),
          ],
        ),
        build: (_) => [
          pw.SizedBox(height: 8),
          pw.Center(
            child: pw.Text(
              'FICHA DE REGISTRO DE TREINAMENTO',
              style: pw.TextStyle(
                fontSize: 13,
                fontWeight: pw.FontWeight.bold,
                color: navy,
              ),
            ),
          ),
          pw.SizedBox(height: 8),
          pw.Table(
            border: pw.TableBorder.all(color: line, width: .6),
            columnWidths: const {
              0: pw.FixedColumnWidth(76),
              1: pw.FlexColumnWidth(2.2),
              2: pw.FixedColumnWidth(62),
              3: pw.FlexColumnWidth(1.3),
            },
            children: [
              _infoRow('Empresa', company.name, 'CNPJ', (company.cnpj ?? '').trim()),
              _infoRow(
                'Treinamento',
                [if (code.isNotEmpty) code, record.title].join(' • '),
                'Data',
                DateFormat('dd/MM/yyyy').format(record.date),
              ),
              _infoRow(
                'Instrutor',
                '${payload['instructorName'] ?? ''}',
                'Registro',
                '${payload['instructorRegistry'] ?? ''}',
              ),
              _infoRow(
                'Local',
                '${payload['location'] ?? ''}',
                'Carga',
                workload <= 0
                    ? 'Não informada'
                    : '${_hours(workload)} h',
              ),
            ],
          ),
          if ('${payload['content'] ?? ''}'.trim().isNotEmpty) ...[
            pw.SizedBox(height: 7),
            _box(
              'CONTEÚDO PROGRAMÁTICO / ASSUNTOS ABORDADOS',
              '${payload['content']}',
            ),
          ],
          if ('${payload['description'] ?? ''}'.trim().isNotEmpty) ...[
            pw.SizedBox(height: 7),
            _box('OBSERVAÇÕES', '${payload['description']}'),
          ],
          pw.SizedBox(height: 9),
          pw.Text(
            'LISTA DE PRESENÇA E ASSINATURAS',
            style: pw.TextStyle(fontSize: 9, fontWeight: pw.FontWeight.bold),
          ),
          pw.SizedBox(height: 4),
          pw.Table(
            border: pw.TableBorder.all(color: line, width: .45),
            columnWidths: const {
              0: pw.FixedColumnWidth(24),
              1: pw.FlexColumnWidth(2.2),
              2: pw.FlexColumnWidth(1.8),
              3: pw.FixedColumnWidth(92),
              4: pw.FixedColumnWidth(58),
            },
            children: participantRows,
          ),
          pw.SizedBox(height: 8),
          pw.Text(
            'As assinaturas acima foram coletadas eletronicamente no aplicativo Auditar SST e vinculadas a este registro.',
            style: const pw.TextStyle(fontSize: 7.2, color: PdfColors.grey700),
          ),
          if (photoPaths.isNotEmpty) ...[
            pw.SizedBox(height: 14),
            pw.Text(
              'REGISTRO FOTOGRÁFICO',
              style: pw.TextStyle(fontSize: 9, fontWeight: pw.FontWeight.bold),
            ),
            pw.SizedBox(height: 6),
            ...await _photoRows(photoPaths),
          ],
        ],
      ),
    );

    return doc.save();
  }

  static Future<List<pw.Widget>> _photoRows(List<String> paths) async {
    final images = <pw.ImageProvider>[];
    for (final path in paths.take(8)) {
      final image = await _fileImage(path);
      if (image != null) images.add(image);
    }
    final rows = <pw.Widget>[];
    for (var i = 0; i < images.length; i += 2) {
      rows.add(
        pw.Row(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            pw.Expanded(
              child: pw.Container(
                height: 155,
                padding: const pw.EdgeInsets.all(3),
                decoration: pw.BoxDecoration(
                  border: pw.Border.all(color: PdfColors.grey400),
                ),
                child: pw.Image(images[i], fit: pw.BoxFit.contain),
              ),
            ),
            pw.SizedBox(width: 6),
            pw.Expanded(
              child: i + 1 < images.length
                  ? pw.Container(
                      height: 155,
                      padding: const pw.EdgeInsets.all(3),
                      decoration: pw.BoxDecoration(
                        border: pw.Border.all(color: PdfColors.grey400),
                      ),
                      child: pw.Image(images[i + 1], fit: pw.BoxFit.contain),
                    )
                  : pw.SizedBox(height: 155),
            ),
          ],
        ),
      );
      rows.add(pw.SizedBox(height: 6));
    }
    return rows;
  }

  static String _hours(double value) {
    if (value == value.roundToDouble()) return value.toInt().toString();
    return value.toStringAsFixed(1).replaceAll('.', ',');
  }

  static pw.Widget _box(String title, String body) => pw.Container(
        width: double.infinity,
        padding: const pw.EdgeInsets.all(7),
        decoration: pw.BoxDecoration(
          border: pw.Border.all(color: line, width: .6),
        ),
        child: pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            pw.Text(
              title,
              style: pw.TextStyle(fontSize: 7.5, fontWeight: pw.FontWeight.bold),
            ),
            pw.SizedBox(height: 3),
            pw.Text(body, style: const pw.TextStyle(fontSize: 8.2)),
          ],
        ),
      );

  static pw.TableRow _infoRow(String a, String b, String c, String d) =>
      pw.TableRow(
        children: [
          _cell(a, bold: true),
          _cell(b),
          _cell(c, bold: true),
          _cell(d),
        ],
      );

  static pw.Widget _cell(
    String text, {
    bool bold = false,
    pw.TextAlign? align,
  }) =>
      pw.Padding(
        padding: const pw.EdgeInsets.symmetric(horizontal: 4, vertical: 4),
        child: pw.Text(
          text.trim().isEmpty ? '-' : text,
          textAlign: align,
          style: pw.TextStyle(
            fontSize: 7.4,
            fontWeight: bold ? pw.FontWeight.bold : pw.FontWeight.normal,
          ),
        ),
      );

  static pw.Widget _header(
    pw.ImageProvider? auditarLogo,
    pw.ImageProvider? companyLogo,
  ) {
    return pw.Row(
      children: [
        if (auditarLogo != null)
          pw.SizedBox(
            width: 120,
            height: 42,
            child: pw.Image(auditarLogo, fit: pw.BoxFit.contain),
          ),
        pw.Spacer(),
        if (companyLogo != null)
          pw.SizedBox(
            width: 95,
            height: 42,
            child: pw.Image(companyLogo, fit: pw.BoxFit.contain),
          ),
      ],
    );
  }

  static Future<pw.ImageProvider?> _asset(String path) async {
    try {
      final data = await rootBundle.load(path);
      return pw.MemoryImage(data.buffer.asUint8List());
    } catch (_) {
      return null;
    }
  }

  static Future<pw.ImageProvider?> _fileImage(String? path) async {
    final value = (path ?? '').trim();
    if (value.isEmpty) return null;
    try {
      final file = File(value);
      if (!await file.exists()) return null;
      return pw.MemoryImage(await file.readAsBytes());
    } catch (_) {
      return null;
    }
  }
}
'''

(root / 'lib/screens/training_records_screen.dart').write_text(screen, encoding='utf-8', newline='\n')
(root / 'lib/services/training_record_pdf_service.dart').write_text(pdf, encoding='utf-8', newline='\n')

pubp.write_text(pub, encoding='utf-8', newline='\n')
trainp.write_text(train, encoding='utf-8', newline='\n')
mediap.write_text(media, encoding='utf-8', newline='\n')

final_train = trainp.read_text(encoding='utf-8')
final_media = mediap.read_text(encoding='utf-8')
assert 'version: ' + target in pubp.read_text(encoding='utf-8')
assert "title: 'Fotos e fichas'" in final_train
assert 'TrainingRecordsScreen(' in final_train
assert 'registerTrainingRecordPhoto({' in final_media
assert 'registerTrainingRecordSignature({' in final_media
assert 'restoreTrainingRecordMedia({' in final_media
assert (root / 'lib/screens/training_records_screen.dart').exists()
assert (root / 'lib/services/training_record_pdf_service.dart').exists()
print('TRAINING_RECORDS_MEDIA_OK', target, platform)

import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:printing/printing.dart';

import '../database.dart';
import '../models.dart';
import '../services/extinguisher_inspection_pdf_service.dart';

const String extinguisherMonthlyRecordType = 'EXTINTOR_INSPECAO_MENSAL';

class ExtinguisherMonthlyOverviewScreen extends StatefulWidget {
  final Company company;
  const ExtinguisherMonthlyOverviewScreen({super.key, required this.company});

  @override
  State<ExtinguisherMonthlyOverviewScreen> createState() =>
      _ExtinguisherMonthlyOverviewScreenState();
}

class _ExtinguisherMonthlyOverviewScreenState
    extends State<ExtinguisherMonthlyOverviewScreen> {
  bool loading = true;
  bool onlyIrregular = false;
  DateTime month = DateTime(DateTime.now().year, DateTime.now().month);
  List<SstRecord> extinguishers = const [];
  List<SstRecord> inspections = const [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => loading = true);
    final result = await Future.wait([
      AppDatabase.instance.getSstRecords(
        type: 'EXTINTOR',
        companyId: widget.company.id,
      ),
      AppDatabase.instance.getSstRecords(
        type: extinguisherMonthlyRecordType,
        companyId: widget.company.id,
      ),
    ]);
    if (!mounted) return;
    setState(() {
      extinguishers = result[0];
      inspections = result[1];
      loading = false;
    });
  }

  String _monthKey(DateTime value) =>
      '${value.year}-${value.month.toString().padLeft(2, '0')}';

  SstRecord? _inspectionFor(SstRecord extinguisher) {
    final key = _monthKey(month);
    for (final item in inspections.reversed) {
      if ('${item.payload['extinguisherId'] ?? ''}' == extinguisher.id &&
          '${item.payload['monthKey'] ?? ''}' == key) {
        return item;
      }
    }
    return null;
  }

  bool _isIrregular(SstRecord? inspection) {
    final status = '${inspection?.payload['result'] ?? ''}'.toLowerCase();
    return status == 'não conforme' ||
        status == 'nao conforme' ||
        status == 'não localizado' ||
        status == 'nao localizado';
  }

  DateTime? _expiry(SstRecord item) {
    final p = item.payload;
    final raw = [
      p['validade'],
      p['validadeCarga'],
      p['validade_carga'],
      p['expiryDate'],
      p['validity'],
    ].map((e) => '${e ?? ''}'.trim()).firstWhere(
          (e) => e.isNotEmpty,
          orElse: () => '',
        );
    if (raw.isEmpty) return null;
    final iso = DateTime.tryParse(raw);
    if (iso != null) return iso;
    final parts = raw.split('/');
    if (parts.length == 3) {
      final d = int.tryParse(parts[0]);
      final m = int.tryParse(parts[1]);
      final y = int.tryParse(parts[2]);
      if (d != null && m != null && y != null) {
        return DateTime(y, m, d);
      }
    }
    return null;
  }

  String _location(SstRecord item) {
    final p = item.payload;
    for (final key in ['location', 'local', 'localizacao', 'setor']) {
      final value = '${p[key] ?? ''}'.trim();
      if (value.isNotEmpty) return value;
    }
    return item.title;
  }

  String _typeLabel(SstRecord item) {
    final p = item.payload;
    for (final key in ['tipo', 'type', 'agent', 'agente']) {
      final value = '${p[key] ?? ''}'.trim();
      if (value.isNotEmpty) return value;
    }
    return 'Extintor';
  }

  Future<void> _chooseMonth() async {
    final selected = await showDatePicker(
      context: context,
      initialDate: month,
      firstDate: DateTime(DateTime.now().year - 5, 1),
      lastDate: DateTime(DateTime.now().year + 2, 12, 31),
      helpText: 'Escolha uma data do mês da inspeção',
    );
    if (selected == null || !mounted) return;
    setState(() => month = DateTime(selected.year, selected.month));
  }

  Future<void> _inspect(SstRecord extinguisher) async {
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ExtinguisherMonthlyInspectionScreen(
          company: widget.company,
          extinguisher: extinguisher,
          month: month,
        ),
      ),
    );
    await _load();
  }

  Future<void> _monthlyPdf() async {
    final bytes = await ExtinguisherInspectionPdfService.generateMonthly(
      company: widget.company,
      extinguishers: extinguishers,
      inspections: inspections,
      month: month,
    );
    if (!mounted) return;
    await Printing.layoutPdf(onLayout: (_) async => bytes);
  }

  @override
  Widget build(BuildContext context) {
    final inspected = extinguishers.where((e) => _inspectionFor(e) != null).length;
    final irregular =
        extinguishers.where((e) => _isIrregular(_inspectionFor(e))).length;
    final pending = extinguishers.length - inspected;
    final now = DateTime.now();
    final expiryAlerts = extinguishers.where((e) {
      final due = _expiry(e);
      if (due == null) return false;
      final days = due.difference(DateTime(now.year, now.month, now.day)).inDays;
      return days <= 30;
    }).length;

    final visible = extinguishers.where((item) {
      if (!onlyIrregular) return true;
      return _isIrregular(_inspectionFor(item));
    }).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Inspeção mensal de extintores'),
        actions: [
          IconButton(
            tooltip: 'Relatório mensal',
            onPressed: extinguishers.isEmpty ? null : _monthlyPdf,
            icon: const Icon(Icons.picture_as_pdf_outlined),
          ),
          IconButton(
            tooltip: 'Atualizar',
            onPressed: _load,
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  Card(
                    child: ListTile(
                      leading: const Icon(Icons.calendar_month_outlined),
                      title: Text(
                        'Competência ${month.month.toString().padLeft(2, '0')}/${month.year}',
                      ),
                      subtitle: const Text(
                        'Use os extintores já cadastrados. Não cria cadastro duplicado.',
                      ),
                      trailing: TextButton(
                        onPressed: _chooseMonth,
                        child: const Text('Alterar'),
                      ),
                    ),
                  ),
                  const SizedBox(height: 10),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      _Metric(label: 'Cadastrados', value: extinguishers.length),
                      _Metric(label: 'Inspecionados', value: inspected),
                      _Metric(label: 'Pendentes', value: pending),
                      _Metric(label: 'Irregulares', value: irregular),
                      if (expiryAlerts > 0)
                        _Metric(label: 'Validade ≤ 30 dias', value: expiryAlerts),
                    ],
                  ),
                  const SizedBox(height: 12),
                  SwitchListTile(
                    value: onlyIrregular,
                    onChanged: (value) => setState(() => onlyIrregular = value),
                    title: const Text('Mostrar somente irregulares'),
                    subtitle: const Text(
                      'Facilita a conferência de retorno e das correções pendentes.',
                    ),
                  ),
                  const SizedBox(height: 8),
                  if (extinguishers.isEmpty)
                    const Card(
                      child: Padding(
                        padding: EdgeInsets.all(18),
                        child: Text(
                          'Nenhum extintor cadastrado nesta empresa.',
                        ),
                      ),
                    ),
                  for (final extinguisher in visible)
                    Builder(builder: (context) {
                      final inspection = _inspectionFor(extinguisher);
                      final result =
                          '${inspection?.payload['result'] ?? 'Pendente'}';
                      final service =
                          '${inspection?.payload['serviceStatus'] ?? ''}';
                      final due = _expiry(extinguisher);
                      final expiryText = due == null
                          ? ''
                          : 'Validade: ${due.day.toString().padLeft(2, '0')}/${due.month.toString().padLeft(2, '0')}/${due.year}';
                      final bad = _isIrregular(inspection);
                      return Card(
                        margin: const EdgeInsets.only(bottom: 10),
                        child: ListTile(
                          leading: CircleAvatar(
                            child: Icon(
                              bad
                                  ? Icons.warning_amber_rounded
                                  : inspection == null
                                      ? Icons.schedule_rounded
                                      : Icons.check_rounded,
                            ),
                          ),
                          title: Text(extinguisher.title),
                          subtitle: Text(
                            [
                              _typeLabel(extinguisher),
                              _location(extinguisher),
                              if (expiryText.isNotEmpty) expiryText,
                              if (service.isNotEmpty) service,
                              'Mês: $result',
                            ].join(' • '),
                          ),
                          isThreeLine: true,
                          trailing: FilledButton.tonal(
                            onPressed: () => _inspect(extinguisher),
                            child: Text(inspection == null ? 'Inspecionar' : 'Abrir'),
                          ),
                        ),
                      );
                    }),
                ],
              ),
            ),
    );
  }
}

class ExtinguisherMonthlyInspectionScreen extends StatefulWidget {
  final Company company;
  final SstRecord extinguisher;
  final DateTime month;

  const ExtinguisherMonthlyInspectionScreen({
    super.key,
    required this.company,
    required this.extinguisher,
    required this.month,
  });

  @override
  State<ExtinguisherMonthlyInspectionScreen> createState() =>
      _ExtinguisherMonthlyInspectionScreenState();
}

class _ExtinguisherMonthlyInspectionScreenState
    extends State<ExtinguisherMonthlyInspectionScreen> {
  static const checks = <String, String>{
    'validade': 'Validade',
    'pressao': 'Pressão / indicador',
    'lacre': 'Lacre e pino',
    'sinalizacao': 'Sinalização',
    'acesso': 'Acesso livre',
    'mangueira': 'Mangueira / bico',
    'condicao': 'Condição geral',
  };

  final noteController = TextEditingController();
  final picker = ImagePicker();
  final values = <String, String>{};
  String serviceStatus = 'Operacional';
  bool notLocated = false;
  bool saving = false;
  String photoPath = '';
  SstRecord? existing;
  List<SstRecord> history = const [];

  String get monthKey =>
      '${widget.month.year}-${widget.month.month.toString().padLeft(2, '0')}';

  @override
  void initState() {
    super.initState();
    for (final key in checks.keys) {
      values[key] = 'Conforme';
    }
    _load();
  }

  @override
  void dispose() {
    noteController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    final all = await AppDatabase.instance.getSstRecords(
      type: extinguisherMonthlyRecordType,
      companyId: widget.company.id,
    );
    final own = all
        .where((e) => '${e.payload['extinguisherId'] ?? ''}' == widget.extinguisher.id)
        .toList()
      ..sort((a, b) => a.date.compareTo(b.date));
    SstRecord? current;
    for (final item in own) {
      if ('${item.payload['monthKey'] ?? ''}' == monthKey) current = item;
    }
    if (current != null) {
      for (final key in checks.keys) {
        final value = '${current.payload['check_$key'] ?? ''}'.trim();
        if (value.isNotEmpty) values[key] = value;
      }
      serviceStatus =
          '${current.payload['serviceStatus'] ?? 'Operacional'}';
      notLocated = current.payload['notLocated'] == true ||
          '${current.payload['result'] ?? ''}' == 'Não localizado';
      photoPath = '${current.payload['photoPath'] ?? ''}';
      noteController.text = '${current.payload['observation'] ?? ''}';
    }
    if (!mounted) return;
    setState(() {
      existing = current;
      history = own;
    });
  }

  Future<void> _takePhoto() async {
    final file = await picker.pickImage(
      source: Platform.isWindows ? ImageSource.gallery : ImageSource.camera,
      imageQuality: 82,
      maxWidth: 1800,
    );
    if (file == null || !mounted) return;
    setState(() => photoPath = file.path);
  }

  String _result() {
    if (notLocated) return 'Não localizado';
    if (values.values.any((value) => value == 'Não conforme')) {
      return 'Não conforme';
    }
    return 'Conforme';
  }

  Future<void> _save() async {
    setState(() => saving = true);
    try {
      final now = DateTime.now();
      final id = existing?.id ??
          'ext-month-${widget.extinguisher.id}-${widget.month.year}${widget.month.month.toString().padLeft(2, '0')}';
      final payload = <String, dynamic>{
        'extinguisherId': widget.extinguisher.id,
        'extinguisherTitle': widget.extinguisher.title,
        'monthKey': monthKey,
        'result': _result(),
        'serviceStatus': serviceStatus,
        'notLocated': notLocated,
        'observation': noteController.text.trim(),
        'photoPath': photoPath,
        'inspectedAt': now.toUtc().toIso8601String(),
        for (final entry in values.entries) 'check_${entry.key}': entry.value,
      };
      final record = SstRecord(
        id: id,
        companyId: widget.company.id,
        sectorId: widget.extinguisher.sectorId,
        type: extinguisherMonthlyRecordType,
        title: 'Inspeção mensal - ${widget.extinguisher.title}',
        date: now,
        priority: _result() == 'Conforme' ? 'Baixa' : 'Alta',
        payload: payload,
      );
      await AppDatabase.instance.upsertSstRecord(record);
      await _load();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Inspeção mensal salva.')),
      );
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  Future<void> _annualPdf() async {
    final bytes = await ExtinguisherInspectionPdfService.generateAnnualSheet(
      company: widget.company,
      extinguisher: widget.extinguisher,
      inspections: history,
      year: widget.month.year,
    );
    if (!mounted) return;
    await Printing.layoutPdf(onLayout: (_) async => bytes);
  }

  Color _monthColor(String result) {
    final value = result.toLowerCase();
    if (value.contains('não conforme') ||
        value.contains('nao conforme') ||
        value.contains('não localizado') ||
        value.contains('nao localizado')) {
      return Colors.red.shade100;
    }
    if (value == 'conforme') return Colors.green.shade100;
    return Colors.grey.shade100;
  }

  @override
  Widget build(BuildContext context) {
    final yearHistory = <int, SstRecord>{};
    for (final item in history) {
      final key = '${item.payload['monthKey'] ?? ''}';
      final parts = key.split('-');
      if (parts.length != 2) continue;
      final year = int.tryParse(parts[0]);
      final month = int.tryParse(parts[1]);
      if (year == widget.month.year && month != null) {
        yearHistory[month] = item;
      }
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Inspeção do extintor'),
        actions: [
          IconButton(
            tooltip: 'Ficha anual em PDF',
            onPressed: _annualPdf,
            icon: const Icon(Icons.picture_as_pdf_outlined),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: ListTile(
              leading: const Icon(Icons.fire_extinguisher_rounded),
              title: Text(widget.extinguisher.title),
              subtitle: Text(
                'Competência ${widget.month.month.toString().padLeft(2, '0')}/${widget.month.year}',
              ),
            ),
          ),
          SwitchListTile(
            value: notLocated,
            onChanged: (value) => setState(() => notLocated = value),
            title: const Text('Extintor não localizado'),
            subtitle: const Text(
              'Use quando o equipamento cadastrado não estiver no ponto previsto.',
            ),
          ),
          DropdownButtonFormField<String>(
            value: serviceStatus,
            decoration: const InputDecoration(
              labelText: 'Situação do equipamento',
            ),
            items: const [
              DropdownMenuItem(value: 'Operacional', child: Text('Operacional')),
              DropdownMenuItem(
                value: 'Em manutenção',
                child: Text('Em manutenção'),
              ),
              DropdownMenuItem(value: 'Em recarga', child: Text('Em recarga')),
              DropdownMenuItem(value: 'Substituído', child: Text('Substituído')),
            ],
            onChanged: notLocated
                ? null
                : (value) => setState(
                      () => serviceStatus = value ?? 'Operacional',
                    ),
          ),
          const SizedBox(height: 16),
          if (!notLocated) ...[
            const Text(
              'Checklist rápido',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            const SizedBox(height: 8),
            for (final entry in checks.entries)
              Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: DropdownButtonFormField<String>(
                  value: values[entry.key],
                  decoration: InputDecoration(labelText: entry.value),
                  items: const [
                    DropdownMenuItem(
                      value: 'Conforme',
                      child: Text('Conforme'),
                    ),
                    DropdownMenuItem(
                      value: 'Não conforme',
                      child: Text('Não conforme'),
                    ),
                    DropdownMenuItem(
                      value: 'Não se aplica',
                      child: Text('Não se aplica'),
                    ),
                  ],
                  onChanged: (value) =>
                      setState(() => values[entry.key] = value ?? 'Conforme'),
                ),
              ),
          ],
          TextField(
            controller: noteController,
            minLines: 3,
            maxLines: 6,
            decoration: const InputDecoration(
              labelText: 'Observação',
              hintText: 'Descreva somente quando houver algo relevante.',
              alignLabelWithHint: true,
            ),
          ),
          const SizedBox(height: 12),
          if (photoPath.isNotEmpty && File(photoPath).existsSync())
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Image.file(
                File(photoPath),
                height: 180,
                fit: BoxFit.cover,
              ),
            ),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: _takePhoto,
            icon: const Icon(Icons.photo_camera_outlined),
            label: Text(photoPath.isEmpty ? 'Adicionar foto' : 'Trocar foto'),
          ),
          const SizedBox(height: 18),
          FilledButton.icon(
            onPressed: saving ? null : _save,
            icon: saving
                ? const SizedBox.square(
                    dimension: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.save_outlined),
            label: Text(saving ? 'Salvando...' : 'Salvar inspeção mensal'),
          ),
          const SizedBox(height: 24),
          Row(
            children: [
              const Expanded(
                child: Text(
                  'Histórico do ano',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                ),
              ),
              TextButton.icon(
                onPressed: _annualPdf,
                icon: const Icon(Icons.picture_as_pdf_outlined),
                label: const Text('Ficha anual'),
              ),
            ],
          ),
          const SizedBox(height: 8),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: 12,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 4,
              mainAxisSpacing: 8,
              crossAxisSpacing: 8,
              childAspectRatio: 1.35,
            ),
            itemBuilder: (_, index) {
              final m = index + 1;
              final record = yearHistory[m];
              final result = '${record?.payload['result'] ?? 'Pendente'}';
              return Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: _monthColor(result),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      m.toString().padLeft(2, '0'),
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                    Text(
                      result,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 10),
                    ),
                  ],
                ),
              );
            },
          ),
        ],
      ),
    );
  }
}

class _Metric extends StatelessWidget {
  final String label;
  final int value;
  const _Metric({required this.label, required this.value});

  @override
  Widget build(BuildContext context) => Container(
        width: 112,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '$value',
              style: const TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
              ),
            ),
            Text(label, style: const TextStyle(fontSize: 11)),
          ],
        ),
      );
}

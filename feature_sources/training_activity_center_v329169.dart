import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../brand.dart';
import '../database.dart';
import '../models.dart';

class TrainingActivityCenterScreen extends StatefulWidget {
  final String? companyId;
  final String companyName;

  const TrainingActivityCenterScreen({
    super.key,
    this.companyId,
    this.companyName = '',
  });

  @override
  State<TrainingActivityCenterScreen> createState() =>
      _TrainingActivityCenterScreenState();
}

class _TrainingActivityCenterScreenState
    extends State<TrainingActivityCenterScreen> {
  bool loading = true;
  String error = '';
  String query = '';
  String filter = 'Todos';
  List<_TrainingActivity> rows = const [];
  Map<String, int> trainingSummary = const {};
  int missingRequiredTrainings = 0;

  static const filters = <String>[
    'Todos',
    'DDS',
    'Treinamentos',
    'Integrações',
    'Assinaturas pendentes',
  ];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    if (mounted) {
      setState(() {
        loading = true;
        error = '';
      });
    }
    try {
      final db = AppDatabase.instance;
      final result = await Future.wait([
        db.getSstRecords(type: 'DDS', companyId: widget.companyId),
        db.getSstRecords(
          type: 'TREINAMENTO_SESSAO',
          companyId: widget.companyId,
        ),
        db.getSstRecords(type: 'INTEGRACAO', companyId: widget.companyId),
      ]);
      final loaded = <_TrainingActivity>[
        ...result[0].map((record) => _TrainingActivity('DDS', record)),
        ...result[1].map(
          (record) => _TrainingActivity('Treinamento', record),
        ),
        ...result[2].map(
          (record) => _TrainingActivity('Integração', record),
        ),
      ]..sort((a, b) => b.record.date.compareTo(a.record.date));

      Map<String, int> loadedTrainingSummary = const {};
      var loadedMissingRequired = 0;
      if (widget.companyId != null && widget.companyId!.trim().isNotEmpty) {
        final summaryFuture =
            db.getTrainingSummary(companyId: widget.companyId);
        final missingFuture = db.getMissingRequiredTrainings(
          companyId: widget.companyId!,
        );
        loadedTrainingSummary = await summaryFuture;
        final missing = await missingFuture;
        loadedMissingRequired = missing.length;
      }

      if (!mounted) return;
      setState(() {
        rows = loaded;
        trainingSummary = loadedTrainingSummary;
        missingRequiredTrainings = loadedMissingRequired;
        loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        loading = false;
        error = '$e';
      });
    }
  }

  List<Map<String, dynamic>> _participants(SstRecord record) {
    final raw = record.payload['participants'];
    if (raw is! List) return const [];
    return raw
        .whereType<Map>()
        .map((item) => Map<String, dynamic>.from(item))
        .toList(growable: false);
  }

  bool _hasPendingSignature(SstRecord record) {
    final participants = _participants(record);
    if (participants.isEmpty) return false;
    return participants.any((item) {
      final status = '${item['status'] ?? ''}'.trim().toUpperCase();
      return status != 'ASSINADO';
    });
  }

  List<_TrainingActivity> get visibleRows {
    final term = query.trim().toLowerCase();
    return rows.where((item) {
      if (filter == 'DDS' && item.kind != 'DDS') return false;
      if (filter == 'Treinamentos' && item.kind != 'Treinamento') {
        return false;
      }
      if (filter == 'Integrações' && item.kind != 'Integração') {
        return false;
      }
      if (filter == 'Assinaturas pendentes' &&
          !_hasPendingSignature(item.record)) {
        return false;
      }
      if (term.isEmpty) return true;
      final participants = _participants(item.record)
          .map(
            (p) =>
                '${p['name'] ?? p['workerName'] ?? p['participantName'] ?? ''}',
          )
          .join(' ');
      return <String>[
        item.kind,
        item.record.title,
        item.record.status,
        '${item.record.payload['code'] ?? ''}',
        '${item.record.payload['sector'] ?? item.record.payload['sectorName'] ?? ''}',
        '${item.record.payload['instructor'] ?? item.record.payload['instructorName'] ?? ''}',
        participants,
      ].join(' ').toLowerCase().contains(term);
    }).toList(growable: false);
  }

  int get pendingSignatures =>
      rows.where((item) => _hasPendingSignature(item.record)).length;

  Widget _annualTrainingPlanCard() {
    final now = DateTime.now();
    final yearRows =
        rows.where((item) => item.record.date.year == now.year).toList();
    final months = yearRows.map((item) => item.record.date.month).toSet();
    final expired = trainingSummary['expired'] ?? 0;
    final action = expired > 0
        ? 'Regularizar primeiro os treinamentos vencidos.'
        : missingRequiredTrainings > 0
            ? 'Programar os treinamentos obrigatórios sem registro localizado.'
            : pendingSignatures > 0
                ? 'Concluir as assinaturas pendentes dos registros existentes.'
                : 'Manter o calendário anual e os registros de presença atualizados.';

    return Card(
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              const Icon(Icons.calendar_month_outlined, color: AuditarBrand.navy),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Planejamento anual • ' + now.year.toString(),
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: AuditarBrand.navy),
                ),
              ),
            ]),
            const SizedBox(height: 8),
            Text(
              yearRows.length.toString() + ' atividade(s) registrada(s) em ' +
              months.length.toString() + ' mês(es) do ano.',
            ),
            const SizedBox(height: 8),
            Wrap(spacing: 7, runSpacing: 7, children: [
              Chip(
                avatar: const Icon(Icons.event_busy_outlined, size: 17),
                label: Text(expired.toString() + ' vencido(s)'),
              ),
              Chip(
                avatar: const Icon(Icons.person_off_outlined, size: 17),
                label: Text(missingRequiredTrainings.toString() + ' obrigatório(s) sem registro'),
              ),
              Chip(
                avatar: const Icon(Icons.draw_outlined, size: 17),
                label: Text(pendingSignatures.toString() + ' assinatura(s) pendente(s)'),
              ),
            ]),
            const SizedBox(height: 8),
            Text(action, style: const TextStyle(fontWeight: FontWeight.w800)),
            const SizedBox(height: 4),
            const Text(
              'A visão anual usa os registros existentes e não substitui a definição técnica dos treinamentos exigíveis por função e risco.',
              style: TextStyle(fontSize: 11.5, color: AuditarBrand.neutral),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final visible = visibleRows;
    final dds = rows.where((item) => item.kind == 'DDS').length;
    final trainings =
        rows.where((item) => item.kind == 'Treinamento').length;
    final integrations =
        rows.where((item) => item.kind == 'Integração').length;

    return Scaffold(
      backgroundColor: AuditarBrand.background,
      appBar: AppBar(
        title: const Text('Capacitação e DDS'),
        actions: [
          IconButton(
            tooltip: 'Atualizar',
            onPressed: loading ? null : _load,
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : error.isNotEmpty
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Text(
                      'Não foi possível carregar os registros: $error',
                    ),
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView(
                    padding: const EdgeInsets.fromLTRB(14, 14, 14, 30),
                    children: [
                      Text(
                        widget.companyName.trim().isEmpty
                            ? 'Visão consolidada'
                            : widget.companyName,
                        style: const TextStyle(
                          fontSize: 19,
                          fontWeight: FontWeight.w900,
                          color: AuditarBrand.navy,
                        ),
                      ),
                      const SizedBox(height: 3),
                      const Text(
                        'Visão consolidada de DDS, treinamentos, integrações e pendências de capacitação.',
                        style: TextStyle(color: AuditarBrand.neutral),
                      ),
                      const SizedBox(height: 12),
                      _annualTrainingPlanCard(),
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          _metric('DDS', dds, Icons.record_voice_over_outlined),
                          _metric(
                            'Treinamentos',
                            trainings,
                            Icons.school_outlined,
                          ),
                          _metric(
                            'Integrações',
                            integrations,
                            Icons.person_add_alt_1_outlined,
                          ),
                          _metric(
                            'Assinaturas pendentes',
                            pendingSignatures,
                            Icons.draw_outlined,
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        onChanged: (value) => setState(() => query = value),
                        decoration: const InputDecoration(
                          labelText: 'Pesquisar registros',
                          hintText:
                              'Tema, colaborador, código, instrutor ou setor',
                          prefixIcon: Icon(Icons.search_rounded),
                        ),
                      ),
                      const SizedBox(height: 9),
                      SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: Row(
                          children: filters
                              .map(
                                (value) => Padding(
                                  padding: const EdgeInsets.only(right: 7),
                                  child: ChoiceChip(
                                    label: Text(value),
                                    selected: filter == value,
                                    onSelected: (_) =>
                                        setState(() => filter = value),
                                  ),
                                ),
                              )
                              .toList(growable: false),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '${visible.length} de ${rows.length} registro(s)',
                        style: const TextStyle(
                          fontSize: 11.5,
                          color: AuditarBrand.neutral,
                        ),
                      ),
                      const SizedBox(height: 6),
                      if (visible.isEmpty)
                        const Card(
                          child: Padding(
                            padding: EdgeInsets.all(18),
                            child: Text(
                              'Nenhum registro corresponde ao filtro selecionado.',
                            ),
                          ),
                        )
                      else
                        ...visible.map(_card),
                    ],
                  ),
                ),
    );
  }

  Widget _metric(String label, int value, IconData icon) => SizedBox(
        width: MediaQuery.sizeOf(context).width < 600 ? 165 : 205,
        child: Card(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Icon(icon, color: AuditarBrand.navy),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '$value',
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      Text(
                        label,
                        style: const TextStyle(
                          fontSize: 10.5,
                          color: AuditarBrand.neutral,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      );

  Widget _card(_TrainingActivity item) {
    final participants = _participants(item.record);
    final signed = participants
        .where(
          (p) => '${p['status'] ?? ''}'.trim().toUpperCase() == 'ASSINADO',
        )
        .length;
    final code = '${item.record.payload['code'] ?? ''}'.trim();
    final sector =
        '${item.record.payload['sector'] ?? item.record.payload['sectorName'] ?? ''}'
            .trim();
    return Card(
      margin: const EdgeInsets.only(bottom: 9),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: AuditarBrand.greenSoft,
          foregroundColor: AuditarBrand.greenDark,
          child: Icon(
            item.kind == 'DDS'
                ? Icons.record_voice_over_outlined
                : item.kind == 'Integração'
                    ? Icons.person_add_alt_1_outlined
                    : Icons.school_outlined,
          ),
        ),
        title: Text(
          [
            if (code.isNotEmpty) code,
            item.record.title,
          ].join(' • '),
          style: const TextStyle(fontWeight: FontWeight.w800),
        ),
        subtitle: Text(
          [
            item.kind,
            DateFormat('dd/MM/yyyy').format(item.record.date),
            if (sector.isNotEmpty) sector,
            if (participants.isNotEmpty)
              '$signed/${participants.length} assinatura(s)',
            if (item.record.status.trim().isNotEmpty) item.record.status,
          ].join(' • '),
        ),
        isThreeLine: true,
        trailing: _hasPendingSignature(item.record)
            ? const Tooltip(
                message: 'Há assinatura pendente',
                child: Icon(
                  Icons.edit_note_rounded,
                  color: Color(0xFFAD6409),
                ),
              )
            : const Icon(
                Icons.check_circle_outline,
                color: AuditarBrand.greenDark,
              ),
      ),
    );
  }
}

class _TrainingActivity {
  final String kind;
  final SstRecord record;

  const _TrainingActivity(this.kind, this.record);
}

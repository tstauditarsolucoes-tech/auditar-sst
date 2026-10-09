import 'dart:async';

import 'package:flutter/material.dart';
import '../brand.dart';
import '../database.dart';
import '../models.dart';
import '../services/correction_recurrence_detector.dart';

/// Painel executivo somente leitura.
///
/// Usa exclusivamente dados já existentes no Auditar SST. O índice exibido
/// nesta tela é um indicador gerencial interno e não representa certificação,
/// laudo, atendimento legal ou substituição da avaliação do profissional SST.
class ExecutiveDashboardScreen extends StatefulWidget {
  final Company company;

  const ExecutiveDashboardScreen({
    super.key,
    required this.company,
  });

  @override
  State<ExecutiveDashboardScreen> createState() =>
      _ExecutiveDashboardScreenState();
}

class _ExecutiveDashboardScreenState extends State<ExecutiveDashboardScreen> {
  bool loading = true;
  bool presentationMode = false;
  String error = '';

  List<Map<String, Object?>> ncs = const [];
  List<Map<String, Object?>> actions = const [];
  List<Map<String, Object?>> inspections = const [];
  List<SstRecord> activities = const [];
  Map<String, int> trainingSummary = const {};
  int missingRequiredTrainingCount = 0;
  List<CorrectionRecurrenceGroup> recurrenceGroups = const [];

  @override
  void initState() {
    super.initState();
    unawaited(_load());
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
      final ncsFuture = db.getNonConformityRows(
        companyId: widget.company.id,
        includeClosed: true,
      );
      final actionsFuture = db.getPendingActions(
        companyId: widget.company.id,
        includeCompleted: true,
      );
      final inspectionsFuture =
          db.getInspectionHistory(companyId: widget.company.id);
      final trainingFuture =
          db.getTrainingSummary(companyId: widget.company.id);
      final missingFuture =
          db.getMissingRequiredTrainings(companyId: widget.company.id);
      final activityFutures = <Future<List<SstRecord>>>[
        for (final type in const [
          'DDS',
          'TREINAMENTO_SESSAO',
          'INTEGRACAO',
          'OBSERVACAO_SEGURANCA',
          'CIPA_REUNIAO',
        ])
          db.getSstRecords(type: type, companyId: widget.company.id),
      ];

      final loadedNcs = await ncsFuture;
      final loadedActions = await actionsFuture;
      final loadedInspections = await inspectionsFuture;
      final loadedTraining = await trainingFuture;
      final missing = await missingFuture;
      final activityGroups = await Future.wait(activityFutures);

      if (!mounted) return;
      setState(() {
        ncs = loadedNcs;
        actions = loadedActions;
        inspections = loadedInspections;
        trainingSummary = loadedTraining;
        missingRequiredTrainingCount = missing.length;
        activities = [
          for (final group in activityGroups) ...group,
        ];
        recurrenceGroups = CorrectionRecurrenceDetector.detect(loadedNcs);
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

  String _value(Map<String, Object?> row, String key) =>
      '${row[key] ?? ''}'.trim();

  DateTime? _dateFrom(
    Map<String, Object?> row,
    List<String> keys,
  ) {
    for (final key in keys) {
      final parsed = DateTime.tryParse(_value(row, key));
      if (parsed != null) return parsed;
    }
    return null;
  }

  bool _closed(Map<String, Object?> row) {
    final status = _value(row, 'status').toLowerCase();
    return status.contains('conclu') ||
        status.contains('resolvid') ||
        status.contains('finaliz');
  }

  bool _sameMonth(DateTime? date, DateTime reference) =>
      date != null &&
      date.year == reference.year &&
      date.month == reference.month;

  DateTime get _now => DateTime.now();

  DateTime get _previousMonth {
    final now = _now;
    return now.month == 1
        ? DateTime(now.year - 1, 12)
        : DateTime(now.year, now.month - 1);
  }

  int get openNc => ncs.where((row) => !_closed(row)).length;

  int get resolvedNcThisMonth => ncs.where((row) {
        if (!_closed(row)) return false;
        final date = _dateFrom(row, const ['verified_at', 'completion_date']);
        return _sameMonth(date, _now);
      }).length;

  int get resolvedNcPreviousMonth => ncs.where((row) {
        if (!_closed(row)) return false;
        final date = _dateFrom(row, const ['verified_at', 'completion_date']);
        return _sameMonth(date, _previousMonth);
      }).length;

  int get newNcThisMonth => ncs.where((row) {
        final date = _dateFrom(
          row,
          const ['inspection_date', 'created_at', 'date'],
        );
        return _sameMonth(date, _now);
      }).length;

  int get highCriticalOpen => ncs.where((row) {
        if (_closed(row)) return false;
        final text = [
          _value(row, 'priority'),
          _value(row, 'classification'),
          _value(row, 'severity'),
        ].join(' ').toLowerCase();
        return text.contains('alta') ||
            text.contains('crit') ||
            text.contains('crít');
      }).length;

  int get overdueActions {
    final today = DateTime(_now.year, _now.month, _now.day);
    return actions.where((row) {
      if (_closed(row)) return false;
      final due = _dateFrom(row, const ['due_date', 'next_due_date']);
      if (due == null) return false;
      return DateTime(due.year, due.month, due.day).isBefore(today);
    }).length;
  }

  int get completedActionsThisMonth => actions.where((row) {
        if (!_closed(row)) return false;
        final date =
            _dateFrom(row, const ['completion_date', 'verified_at']);
        return _sameMonth(date, _now);
      }).length;

  int get expiredTrainings => trainingSummary['expired'] ?? 0;

  int get healthScore {
    var penalty = 0;
    penalty += (highCriticalOpen * 8).clamp(0, 32).toInt();
    penalty += (overdueActions * 5).clamp(0, 20).toInt();
    penalty += (expiredTrainings * 4).clamp(0, 16).toInt();
    penalty += (missingRequiredTrainingCount * 4).clamp(0, 16).toInt();
    penalty += (recurrenceGroups.length * 3).clamp(0, 12).toInt();
    penalty += openNc.clamp(0, 10).toInt();
    return (100 - penalty).clamp(0, 100).toInt();
  }

  String get healthLabel {
    final score = healthScore;
    if (score >= 90) return 'Situação controlada';
    if (score >= 75) return 'Acompanhamento preventivo';
    if (score >= 60) return 'Atenção gerencial';
    return 'Prioridade elevada';
  }

  Color get healthColor {
    final score = healthScore;
    if (score >= 90) return const Color(0xFF147D64);
    if (score >= 75) return const Color(0xFF2B6F91);
    if (score >= 60) return const Color(0xFFB36B00);
    return const Color(0xFFB3261E);
  }

  _ActivityStats _statsForMonth(DateTime reference) {
    var visits = 0;
    for (final row in inspections) {
      final date = _dateFrom(row, const ['date', 'inspection_date']);
      if (_sameMonth(date, reference)) visits++;
    }

    var dds = 0;
    var trainings = 0;
    var integrations = 0;
    var cipa = 0;
    var other = 0;
    final roundIds = <String>{};
    var rounds = 0;

    for (final record in activities) {
      if (!_sameMonth(record.date, reference) ||
          record.type == 'RONDA_RASCUNHO') {
        continue;
      }
      switch (record.type) {
        case 'DDS':
          dds++;
          break;
        case 'TREINAMENTO_SESSAO':
          trainings++;
          break;
        case 'INTEGRACAO':
          integrations++;
          break;
        case 'CIPA_REUNIAO':
          cipa++;
          break;
        case 'OBSERVACAO_SEGURANCA':
          final roundId = '${record.payload['roundId'] ?? ''}'.trim();
          final isRound =
              '${record.payload['roundType'] ?? ''}' == 'RONDA_EXPRESSA' ||
                  roundId.isNotEmpty;
          if (isRound) {
            if (roundId.isEmpty || roundIds.add(roundId)) rounds++;
          } else {
            other++;
          }
          break;
        default:
          other++;
      }
    }

    return _ActivityStats(
      visits: visits,
      dds: dds,
      trainings: trainings,
      integrations: integrations,
      cipa: cipa,
      rounds: rounds,
      other: other,
    );
  }

  _ActivityStats get thisMonthStats => _statsForMonth(_now);
  _ActivityStats get previousMonthStats => _statsForMonth(_previousMonth);

  List<_RiskItem> get topRisks {
    final rows = ncs.where((row) => !_closed(row)).map((row) {
      final text = [
        _value(row, 'priority'),
        _value(row, 'classification'),
        _value(row, 'severity'),
      ].join(' ').toLowerCase();
      var rank = 1;
      var label = 'Acompanhar';
      if (text.contains('crit') || text.contains('crít')) {
        rank = 4;
        label = 'Crítica';
      } else if (text.contains('alta')) {
        rank = 3;
        label = 'Alta';
      } else if (text.contains('média') || text.contains('media')) {
        rank = 2;
        label = 'Média';
      }
      final description = _value(row, 'description');
      final code = _value(row, 'code');
      final sector = _value(row, 'sector_name').isNotEmpty
          ? _value(row, 'sector_name')
          : _value(row, 'area');
      return _RiskItem(
        rank: rank,
        level: label,
        title: code.isNotEmpty
            ? '$code • ${description.isEmpty ? 'Não conformidade' : description}'
            : (description.isEmpty ? 'Não conformidade' : description),
        sector: sector,
      );
    }).toList();

    rows.sort((a, b) => b.rank.compareTo(a.rank));
    return rows.take(5).toList(growable: false);
  }

  String get executiveSummary {
    final parts = <String>[];
    if (resolvedNcThisMonth > 0) {
      parts.add(
        '$resolvedNcThisMonth não conformidade(s) foram verificadas como resolvidas no mês',
      );
    }
    if (completedActionsThisMonth > 0) {
      parts.add(
        '$completedActionsThisMonth ação(ões) foram concluídas no período',
      );
    }
    if (highCriticalOpen > 0) {
      parts.add(
        'permanecem $highCriticalOpen pendência(s) de alta ou crítica prioridade',
      );
    }
    if (overdueActions > 0) {
      parts.add('$overdueActions ação(ões) estão com prazo vencido');
    }
    if (expiredTrainings > 0 || missingRequiredTrainingCount > 0) {
      parts.add('há capacitações que exigem regularização');
    }
    if (parts.isEmpty) {
      return 'Os registros disponíveis não indicam pendência crítica neste momento. Manter o acompanhamento preventivo e o calendário SST atualizado.';
    }
    return '${parts.join('; ')}. O foco recomendado é priorizar riscos críticos, prazos vencidos e reincidências.';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AuditarBrand.background,
      appBar: AppBar(
        title: const Text('Painel Executivo Auditar'),
        actions: [
          IconButton(
            tooltip: presentationMode
                ? 'Sair do modo apresentação'
                : 'Modo apresentação',
            onPressed: () =>
                setState(() => presentationMode = !presentationMode),
            icon: Icon(
              presentationMode
                  ? Icons.close_fullscreen_rounded
                  : Icons.present_to_all_rounded,
            ),
          ),
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
                      'Não foi possível montar o Painel Executivo: $error',
                    ),
                  ),
                )
              : LayoutBuilder(
                  builder: (context, constraints) {
                    final wide = constraints.maxWidth >= 1100;
                    return RefreshIndicator(
                      onRefresh: _load,
                      child: ListView(
                        padding: EdgeInsets.fromLTRB(
                          wide ? 28 : 16,
                          20,
                          wide ? 28 : 16,
                          36,
                        ),
                        children: [
                          _hero(),
                          const SizedBox(height: 16),
                          _metricRow(),
                          const SizedBox(height: 16),
                          if (wide)
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Expanded(
                                  flex: 7,
                                  child: Column(
                                    children: [
                                      _monthlyResults(),
                                      const SizedBox(height: 14),
                                      _evolutionCard(),
                                      if (!presentationMode) ...[
                                        const SizedBox(height: 14),
                                        _topRisksCard(),
                                      ],
                                    ],
                                  ),
                                ),
                                const SizedBox(width: 16),
                                SizedBox(
                                  width: 390,
                                  child: Column(
                                    children: [
                                      _decisionCard(),
                                      const SizedBox(height: 14),
                                      _attentionCard(),
                                      if (!presentationMode) ...[
                                        const SizedBox(height: 14),
                                        _recurrenceCard(),
                                      ],
                                    ],
                                  ),
                                ),
                              ],
                            )
                          else ...[
                            _monthlyResults(),
                            const SizedBox(height: 14),
                            _evolutionCard(),
                            const SizedBox(height: 14),
                            _decisionCard(),
                            const SizedBox(height: 14),
                            _attentionCard(),
                            if (!presentationMode) ...[
                              const SizedBox(height: 14),
                              _topRisksCard(),
                              const SizedBox(height: 14),
                              _recurrenceCard(),
                            ],
                          ],
                          const SizedBox(height: 18),
                          const Center(
                            child: Text(
                              'Índice Auditar SST: indicador gerencial interno baseado nos registros disponíveis no aplicativo. Não substitui avaliação técnica, laudo ou obrigação legal.',
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                color: AuditarBrand.neutral,
                                fontSize: 10.5,
                              ),
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                ),
    );
  }

  Widget _hero() {
    final cnpj = widget.company.cnpj?.trim() ?? '';
    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: AuditarBrand.navy,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'PAINEL EXECUTIVO • SST',
                  style: TextStyle(
                    color: Color(0xFFA0E9D0),
                    fontSize: 11,
                    fontWeight: FontWeight.w900,
                    letterSpacing: .7,
                  ),
                ),
                const SizedBox(height: 7),
                Text(
                  widget.company.name,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 25,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                if (cnpj.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(
                    'CNPJ $cnpj',
                    style: const TextStyle(color: Colors.white70),
                  ),
                ],
                const SizedBox(height: 8),
                Text(
                  executiveSummary,
                  style: const TextStyle(
                    color: Colors.white,
                    height: 1.35,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 24),
          Container(
            width: 180,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: .08),
              borderRadius: BorderRadius.circular(18),
              border: Border.all(
                color: Colors.white.withValues(alpha: .14),
              ),
            ),
            child: Column(
              children: [
                const Text(
                  'ÍNDICE AUDITAR SST',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: Colors.white70,
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 7),
                Text(
                  '$healthScore',
                  style: TextStyle(
                    color: healthColor,
                    fontSize: 42,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                Text(
                  healthLabel,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w800,
                    fontSize: 11.5,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _metricRow() {
    final stats = thisMonthStats;
    return Wrap(
      spacing: 10,
      runSpacing: 10,
      children: [
        _metric('Atividades no mês', stats.total, Icons.event_note_outlined, AuditarBrand.info),
        _metric('NCs resolvidas', resolvedNcThisMonth, Icons.verified_outlined, AuditarBrand.greenDark),
        _metric('NCs abertas', openNc, Icons.warning_amber_rounded, const Color(0xFFB36B00)),
        _metric('Alta/Crítica', highCriticalOpen, Icons.priority_high_rounded, const Color(0xFFB3261E)),
        _metric('Ações vencidas', overdueActions, Icons.event_busy_outlined, const Color(0xFFB3261E)),
        _metric('Trein. pendentes', expiredTrainings + missingRequiredTrainingCount, Icons.school_outlined, AuditarBrand.info),
      ],
    );
  }

  Widget _metric(String label, int value, IconData icon, Color color) {
    return SizedBox(
      width: 205,
      child: Card(
        margin: EdgeInsets.zero,
        child: Padding(
          padding: const EdgeInsets.all(13),
          child: Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: color.withValues(alpha: .09),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: color),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '$value',
                      style: TextStyle(
                        color: color,
                        fontSize: 23,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    Text(
                      label,
                      style: const TextStyle(
                        fontSize: 10.8,
                        fontWeight: FontWeight.w700,
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
  }

  Widget _monthlyResults() {
    final stats = thisMonthStats;
    return _panel(
      title: 'O que foi realizado neste mês',
      subtitle: 'Atividades encontradas nos registros da empresa no período atual.',
      icon: Icons.auto_graph_rounded,
      child: Wrap(
        spacing: 10,
        runSpacing: 10,
        children: [
          _resultItem('Vistorias', stats.visits, Icons.fact_check_outlined),
          _resultItem('Rondas', stats.rounds, Icons.route_outlined),
          _resultItem('DDS', stats.dds, Icons.record_voice_over_outlined),
          _resultItem('Treinamentos', stats.trainings, Icons.school_outlined),
          _resultItem('Integrações', stats.integrations, Icons.groups_outlined),
          _resultItem('CIPA', stats.cipa, Icons.how_to_vote_outlined),
          _resultItem('Ações concluídas', completedActionsThisMonth, Icons.task_alt_rounded),
          _resultItem('NCs resolvidas', resolvedNcThisMonth, Icons.verified_outlined),
        ],
      ),
    );
  }

  Widget _resultItem(String label, int value, IconData icon) {
    return Container(
      width: 160,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AuditarBrand.navySoft,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AuditarBrand.line),
      ),
      child: Row(
        children: [
          Icon(icon, color: AuditarBrand.navy, size: 21),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '$value',
                  style: const TextStyle(
                    color: AuditarBrand.navy,
                    fontSize: 19,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                Text(
                  label,
                  style: const TextStyle(
                    color: AuditarBrand.neutral,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _evolutionCard() {
    final current = thisMonthStats.total;
    final previous = previousMonthStats.total;
    final maxActivities = [current, previous, 1].reduce((a, b) => a > b ? a : b);
    final maxResolved = [resolvedNcThisMonth, resolvedNcPreviousMonth, 1]
        .reduce((a, b) => a > b ? a : b);

    return _panel(
      title: 'Evolução mensal',
      subtitle: 'Comparação objetiva entre o mês atual e o mês anterior com base nos registros cadastrados.',
      icon: Icons.trending_up_rounded,
      child: Column(
        children: [
          _comparisonRow('Atividades registradas', previous, current, maxActivities),
          const SizedBox(height: 14),
          _comparisonRow('NCs resolvidas', resolvedNcPreviousMonth, resolvedNcThisMonth, maxResolved),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(child: _smallStat('Novas NCs no mês', newNcThisMonth)),
              const SizedBox(width: 10),
              Expanded(child: _smallStat('Recorrências identificadas', recurrenceGroups.length)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _comparisonRow(String label, int previous, int current, int maxValue) {
    const months = <String>[
      'JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN',
      'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ',
    ];
    final monthNow = months[_now.month - 1];
    final monthPrev = months[_previousMonth.month - 1];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: AuditarBrand.navy, fontWeight: FontWeight.w800)),
        const SizedBox(height: 7),
        _bar(monthPrev, previous, maxValue, AuditarBrand.neutral),
        const SizedBox(height: 5),
        _bar(monthNow, current, maxValue, AuditarBrand.greenDark),
      ],
    );
  }

  Widget _bar(String label, int value, int maxValue, Color color) {
    final fraction = maxValue <= 0 ? 0.0 : value / maxValue;
    return Row(
      children: [
        SizedBox(
          width: 42,
          child: Text(label, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w800)),
        ),
        Expanded(
          child: LayoutBuilder(
            builder: (context, constraints) {
              return Stack(
                children: [
                  Container(
                    height: 22,
                    decoration: BoxDecoration(
                      color: color.withValues(alpha: .08),
                      borderRadius: BorderRadius.circular(7),
                    ),
                  ),
                  Container(
                    height: 22,
                    width: constraints.maxWidth * fraction.clamp(0.0, 1.0).toDouble(),
                    decoration: BoxDecoration(
                      color: color.withValues(alpha: .35),
                      borderRadius: BorderRadius.circular(7),
                    ),
                  ),
                ],
              );
            },
          ),
        ),
        const SizedBox(width: 8),
        SizedBox(
          width: 30,
          child: Text(
            '$value',
            textAlign: TextAlign.right,
            style: TextStyle(color: color, fontWeight: FontWeight.w900),
          ),
        ),
      ],
    );
  }

  Widget _decisionCard() {
    return _panel(
      title: 'Resumo para decisão',
      subtitle: 'Leitura gerencial sem depender de IA.',
      icon: Icons.insights_outlined,
      child: Text(
        executiveSummary,
        style: const TextStyle(fontWeight: FontWeight.w700, height: 1.45),
      ),
    );
  }

  Widget _attentionCard() {
    return _panel(
      title: 'Prioridades da gestão',
      subtitle: 'O que merece atenção primeiro.',
      icon: Icons.flag_outlined,
      child: Column(
        children: [
          _attentionLine('NCs alta/crítica', highCriticalOpen, highCriticalOpen > 0),
          _attentionLine('Ações vencidas', overdueActions, overdueActions > 0),
          _attentionLine('Treinamentos vencidos', expiredTrainings, expiredTrainings > 0),
          _attentionLine('Obrigatórios sem registro', missingRequiredTrainingCount, missingRequiredTrainingCount > 0),
          _attentionLine('Reincidências', recurrenceGroups.length, recurrenceGroups.isNotEmpty),
        ],
      ),
    );
  }

  Widget _attentionLine(String label, int value, bool alert) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 9),
      child: Row(
        children: [
          Icon(
            alert ? Icons.error_outline_rounded : Icons.check_circle_outline,
            color: alert ? const Color(0xFFB3261E) : AuditarBrand.greenDark,
            size: 19,
          ),
          const SizedBox(width: 8),
          Expanded(child: Text(label)),
          Text(
            '$value',
            style: TextStyle(
              color: alert ? const Color(0xFFB3261E) : AuditarBrand.greenDark,
              fontWeight: FontWeight.w900,
            ),
          ),
        ],
      ),
    );
  }

  Widget _topRisksCard() {
    final risks = topRisks;
    return _panel(
      title: 'Top prioridades abertas',
      subtitle: 'Pendências abertas ordenadas por criticidade informada no registro.',
      icon: Icons.warning_amber_rounded,
      child: risks.isEmpty
          ? const Text(
              'Nenhuma não conformidade aberta localizada.',
              style: TextStyle(color: AuditarBrand.neutral),
            )
          : Column(
              children: [
                for (final risk in risks)
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    dense: true,
                    leading: CircleAvatar(
                      radius: 16,
                      backgroundColor: risk.rank >= 3
                          ? const Color(0xFFFFE8E6)
                          : AuditarBrand.navySoft,
                      child: Text(
                        '${risk.rank}',
                        style: TextStyle(
                          color: risk.rank >= 3
                              ? const Color(0xFFB3261E)
                              : AuditarBrand.navy,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                    ),
                    title: Text(
                      risk.title,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.w700),
                    ),
                    subtitle: Text([
                      risk.level,
                      if (risk.sector.isNotEmpty) risk.sector,
                    ].join(' • ')),
                  ),
              ],
            ),
    );
  }

  Widget _recurrenceCard() {
    final groups = recurrenceGroups.take(5).toList(growable: false);
    return _panel(
      title: 'Reincidências',
      subtitle: 'Problemas semelhantes identificados no mesmo setor, conforme detector local.',
      icon: Icons.repeat_rounded,
      child: groups.isEmpty
          ? const Text(
              'Nenhuma reincidência relevante localizada.',
              style: TextStyle(color: AuditarBrand.neutral),
            )
          : Column(
              children: [
                for (final group in groups)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 9),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          width: 34,
                          height: 34,
                          alignment: Alignment.center,
                          decoration: BoxDecoration(
                            color: AuditarBrand.navySoft,
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Text(
                            '${group.count}x',
                            style: const TextStyle(
                              color: AuditarBrand.navy,
                              fontWeight: FontWeight.w900,
                            ),
                          ),
                        ),
                        const SizedBox(width: 9),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                group.sector.isEmpty ? 'Setor não informado' : group.sector,
                                style: const TextStyle(fontWeight: FontWeight.w800),
                              ),
                              Text(
                                _value(group.records.first, 'description'),
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(
                                  color: AuditarBrand.neutral,
                                  fontSize: 11.5,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
    );
  }

  Widget _smallStat(String label, int value) {
    return Container(
      padding: const EdgeInsets.all(11),
      decoration: BoxDecoration(
        color: AuditarBrand.navySoft,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Expanded(child: Text(label, style: const TextStyle(fontSize: 11.5))),
          Text(
            '$value',
            style: const TextStyle(
              color: AuditarBrand.navy,
              fontWeight: FontWeight.w900,
            ),
          ),
        ],
      ),
    );
  }

  Widget _panel({
    required String title,
    required String subtitle,
    required IconData icon,
    required Widget child,
  }) {
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(17),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: AuditarBrand.navy),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    title,
                    style: const TextStyle(
                      color: AuditarBrand.navy,
                      fontSize: 17,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 3),
            Text(
              subtitle,
              style: const TextStyle(
                color: AuditarBrand.neutral,
                fontSize: 11.5,
              ),
            ),
            const SizedBox(height: 13),
            child,
          ],
        ),
      ),
    );
  }
}

class _ActivityStats {
  final int visits;
  final int dds;
  final int trainings;
  final int integrations;
  final int cipa;
  final int rounds;
  final int other;

  const _ActivityStats({
    required this.visits,
    required this.dds,
    required this.trainings,
    required this.integrations,
    required this.cipa,
    required this.rounds,
    required this.other,
  });

  int get total =>
      visits + dds + trainings + integrations + cipa + rounds + other;
}

class _RiskItem {
  final int rank;
  final String level;
  final String title;
  final String sector;

  const _RiskItem({
    required this.rank,
    required this.level,
    required this.title,
    required this.sector,
  });
}

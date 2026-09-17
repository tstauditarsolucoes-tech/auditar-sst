#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('app/Auditar_SST_v1_5_dashboard')
rondap = root / 'lib/screens/express_round_screen.dart'
pubp = root / 'pubspec.yaml'
ronda = rondap.read_text(encoding='utf-8')
pub = pubp.read_text(encoding='utf-8')


def once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Marcador ausente: {label}')
    return text.replace(old, new, 1)


pub = once(pub, 'version: 3.29.60+202', 'version: 3.29.61+203', 'versao 3.29.61')

ronda = once(
    ronda,
    "  String roundId = '';\n  String? sectorId;\n",
    "  String roundId = '';\n  String activeRoundId = '';\n  bool viewingHistoricalRound = false;\n  String? sectorId;\n",
    'estado de ronda historica',
)

ronda = once(
    ronda,
    "    setState(() {\n      roundId = activeRound;\n      sectors = loaded;\n",
    "    setState(() {\n      roundId = activeRound;\n      activeRoundId = activeRound;\n      viewingHistoricalRound = false;\n      sectors = loaded;\n",
    'roundId ativo persistente',
)

archive_methods = r'''  String _roundDateLabel(DateTime value) {
    final day = value.day.toString().padLeft(2, '0');
    final month = value.month.toString().padLeft(2, '0');
    final year = value.year.toString();
    final hour = value.hour.toString().padLeft(2, '0');
    final minute = value.minute.toString().padLeft(2, '0');
    return '$day/$month/$year $hour:$minute';
  }

  Future<void> _loadRoundById(
    String targetRoundId, {
    required bool historical,
  }) async {
    final id = targetRoundId.trim();
    if (id.isEmpty) return;
    final db = AppDatabase.instance;
    final all = await db.getSstRecords(
      type: 'OBSERVACAO_SEGURANCA',
      companyId: widget.company.id,
    );
    final selected = all
        .where((record) => '${record.payload['roundId'] ?? ''}' == id)
        .toList()
      ..sort((a, b) => a.date.compareTo(b.date));
    final conclusion =
        (await db.getSetting('express_round_conclusion_$id')).trim();
    if (!mounted) return;
    setState(() {
      roundId = id;
      roundRecords = selected;
      roundAiConclusion = conclusion;
      roundAiReview = const {};
      viewingHistoricalRound = historical;
    });
  }

  Future<void> _returnToActiveRound() async {
    if (activeRoundId.trim().isEmpty) {
      await _load();
      return;
    }
    await _loadRoundById(activeRoundId, historical: false);
  }

  Future<void> _showRoundsArchive() async {
    final all = await AppDatabase.instance.getSstRecords(
      type: 'OBSERVACAO_SEGURANCA',
      companyId: widget.company.id,
    );
    final grouped = <String, List<SstRecord>>{};
    for (final record in all) {
      final id = '${record.payload['roundId'] ?? ''}'.trim();
      final roundType = '${record.payload['roundType'] ?? ''}'.trim();
      if (id.isEmpty || (roundType.isNotEmpty && roundType != 'RONDA_EXPRESSA')) {
        continue;
      }
      grouped.putIfAbsent(id, () => <SstRecord>[]).add(record);
    }
    if (grouped.isEmpty) {
      _message('Ainda não há rondas salvas para esta empresa.');
      return;
    }
    final entries = grouped.entries.toList()
      ..sort((a, b) {
        final aDate = a.value.map((e) => e.date).reduce((x, y) => x.isAfter(y) ? x : y);
        final bDate = b.value.map((e) => e.date).reduce((x, y) => x.isAfter(y) ? x : y);
        return bDate.compareTo(aDate);
      });
    if (!mounted) return;
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) => SafeArea(
        child: FractionallySizedBox(
          heightFactor: .86,
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 14, 10, 8),
                child: Row(
                  children: [
                    const Expanded(
                      child: Text(
                        'Histórico de Rondas Expressas',
                        style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900),
                      ),
                    ),
                    IconButton(
                      onPressed: () => Navigator.pop(sheetContext),
                      icon: const Icon(Icons.close_rounded),
                    ),
                  ],
                ),
              ),
              const Padding(
                padding: EdgeInsets.fromLTRB(16, 0, 16, 10),
                child: Text(
                  'Abra uma ronda já encerrada para revisar registros, analisar fotos pendentes com IA e gerar novamente os relatórios.',
                  style: TextStyle(fontSize: 12.5, color: Colors.black54),
                ),
              ),
              Expanded(
                child: ListView.builder(
                  padding: const EdgeInsets.fromLTRB(12, 2, 12, 20),
                  itemCount: entries.length,
                  itemBuilder: (_, index) {
                    final entry = entries[index];
                    final records = entry.value..sort((a, b) => a.date.compareTo(b.date));
                    final first = records.first.date;
                    final last = records.last.date;
                    final pending = records.where(_recordNeedsPhotoAi).length;
                    final isCurrent = entry.key == activeRoundId;
                    final nonConformities = records.where((r) => !_recordIsConformity(r)).length;
                    return Card(
                      child: ListTile(
                        leading: CircleAvatar(
                          child: Icon(isCurrent ? Icons.directions_walk_rounded : Icons.history_rounded),
                        ),
                        title: Text(
                          isCurrent
                              ? 'Ronda atual · ${records.length} registro(s)'
                              : 'Ronda de ${_roundDateLabel(first)}',
                          style: const TextStyle(fontWeight: FontWeight.w800),
                        ),
                        subtitle: Text(
                          '${records.length} registro(s) • $nonConformities NC(s)'
                          '${pending > 0 ? ' • IA pendente: $pending' : ''}'
                          '${first == last ? '' : ' • até ${_roundDateLabel(last)}'}',
                        ),
                        trailing: Icon(
                          pending > 0 ? Icons.auto_awesome_rounded : Icons.chevron_right_rounded,
                          color: pending > 0 ? const Color(0xFF6A4BBC) : null,
                        ),
                        onTap: () async {
                          Navigator.pop(sheetContext);
                          await _loadRoundById(
                            entry.key,
                            historical: entry.key != activeRoundId,
                          );
                        },
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<Map<String, dynamic>?> _reviewDeferredAiSuggestion(
    SstRecord record,
    Map<String, dynamic> result,
  ) async {
    final conformity = _recordIsConformity(record);
    String text(String key) => '${result[key] ?? ''}'.trim();
    List<String> list(String key) => (result[key] as List? ?? const [])
        .map((value) => '$value'.trim())
        .where((value) => value.isNotEmpty)
        .toList();

    final descriptionCtl = TextEditingController(text: text('description'));
    final riskCtl = TextEditingController(text: conformity ? '' : text('risk'));
    final consequenceCtl = TextEditingController(
      text: conformity ? '' : text('possibleConsequence'),
    );
    final recommendationCtl = TextEditingController(
      text: <String>[
        text('recommendation'),
        text('correctiveAction'),
      ].where((value) => value.isNotEmpty).join('\n'),
    );
    final immediateCtl = TextEditingController(
      text: conformity ? '' : text('immediateAction'),
    );
    final responsibleCtl = TextEditingController(
      text: conformity ? '' : text('responsibleProfile'),
    );
    final suggestedPriority = text('priority');
    var selectedPriority = conformity
        ? 'Baixa'
        : const ['Baixa', 'Média', 'Alta', 'Crítica'].contains(suggestedPriority)
            ? suggestedPriority
            : record.priority;
    final references = list('likelyReferences');
    final checks = list('checksRequired');
    final confidence = text('confidence');

    final approved = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => StatefulBuilder(
        builder: (dialogContext, setDialogState) => AlertDialog(
          title: const Row(
            children: [
              Icon(Icons.fact_check_outlined),
              SizedBox(width: 8),
              Expanded(child: Text('Revisar sugestão da IA')),
            ],
          ),
          content: SizedBox(
            width: 700,
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'A IA não altera o registro automaticamente. Revise, edite e aprove somente o que você confirmar tecnicamente.',
                    style: TextStyle(fontSize: 12.5, color: Colors.black54),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: descriptionCtl,
                    minLines: 2,
                    maxLines: 5,
                    decoration: const InputDecoration(
                      labelText: 'Descrição sugerida',
                      alignLabelWithHint: true,
                    ),
                  ),
                  if (!conformity) ...[
                    const SizedBox(height: 10),
                    TextField(
                      controller: riskCtl,
                      minLines: 1,
                      maxLines: 3,
                      decoration: const InputDecoration(labelText: 'Risco'),
                    ),
                    const SizedBox(height: 10),
                    TextField(
                      controller: consequenceCtl,
                      minLines: 1,
                      maxLines: 3,
                      decoration: const InputDecoration(labelText: 'Possível consequência'),
                    ),
                  ],
                  const SizedBox(height: 10),
                  TextField(
                    controller: recommendationCtl,
                    minLines: 2,
                    maxLines: 5,
                    decoration: InputDecoration(
                      labelText: conformity
                          ? 'Como manter a boa prática'
                          : 'Recomendação / ação corretiva',
                      alignLabelWithHint: true,
                    ),
                  ),
                  if (!conformity) ...[
                    const SizedBox(height: 10),
                    TextField(
                      controller: immediateCtl,
                      minLines: 1,
                      maxLines: 3,
                      decoration: const InputDecoration(labelText: 'Ação imediata'),
                    ),
                    const SizedBox(height: 10),
                    TextField(
                      controller: responsibleCtl,
                      decoration: const InputDecoration(labelText: 'Perfil responsável'),
                    ),
                    const SizedBox(height: 10),
                    DropdownButtonFormField<String>(
                      value: selectedPriority,
                      decoration: const InputDecoration(labelText: 'Prioridade'),
                      items: const ['Baixa', 'Média', 'Alta', 'Crítica']
                          .map((value) => DropdownMenuItem(value: value, child: Text(value)))
                          .toList(),
                      onChanged: (value) {
                        if (value != null) setDialogState(() => selectedPriority = value);
                      },
                    ),
                  ],
                  if (references.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    Text(
                      'Referências prováveis: ${references.join(', ')}',
                      style: const TextStyle(fontSize: 12, color: Colors.black54),
                    ),
                  ],
                  if (checks.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Text(
                      'Conferir em campo: ${checks.join(' • ')}',
                      style: const TextStyle(fontSize: 12, color: Colors.black54),
                    ),
                  ],
                  if (confidence.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Text(
                      'Confiança informada pela IA: $confidence',
                      style: const TextStyle(fontSize: 11.5, color: Colors.black45),
                    ),
                  ],
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Manter pendente'),
            ),
            FilledButton.icon(
              onPressed: () => Navigator.pop(dialogContext, true),
              icon: const Icon(Icons.check_rounded),
              label: const Text('Aprovar e salvar'),
            ),
          ],
        ),
      ),
    );

    Map<String, dynamic>? accepted;
    if (approved == true) {
      accepted = <String, dynamic>{
        'description': descriptionCtl.text.trim(),
        'risk': conformity ? '' : riskCtl.text.trim(),
        'possibleConsequence': conformity ? '' : consequenceCtl.text.trim(),
        'recommendation': recommendationCtl.text.trim(),
        'immediateAction': conformity ? '' : immediateCtl.text.trim(),
        'responsibleProfile': conformity ? '' : responsibleCtl.text.trim(),
        'priority': selectedPriority,
        'likelyReferences': references,
        'checksRequired': checks,
        'confidence': confidence,
      };
    }
    descriptionCtl.dispose();
    riskCtl.dispose();
    consequenceCtl.dispose();
    recommendationCtl.dispose();
    immediateCtl.dispose();
    responsibleCtl.dispose();
    return accepted;
  }

  Widget _historicalRoundBody() => Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 760),
          child: ListView(
            padding: const EdgeInsets.fromLTRB(14, 14, 14, 30),
            children: [
              Container(
                padding: const EdgeInsets.all(15),
                decoration: BoxDecoration(
                  color: const Color(0xFFF4F0FF),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.history_rounded, color: Color(0xFF6A4BBC)),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Ronda encerrada. Os registros permanecem salvos e podem receber análise de IA, revisão técnica e novos relatórios sem reabrir a coleta de campo.',
                        style: TextStyle(fontWeight: FontWeight.w700),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                alignment: WrapAlignment.center,
                children: [
                  _summaryChip('Total', roundRecords.length, AuditarBrand.navy),
                  _summaryChip('Não conformidades', _nonConformities, const Color(0xFFD93025)),
                  _summaryChip('Conformidades', _conformities, AuditarBrand.greenDark),
                  _summaryChip('Alta/Crítica', _highCritical, const Color(0xFFE56B16)),
                  if (_pendingPhotoAiCount > 0)
                    _summaryChip('IA pendente', _pendingPhotoAiCount, const Color(0xFF6A4BBC)),
                ],
              ),
              const SizedBox(height: 14),
              if (_pendingPhotoAiCount > 0) ...[
                FilledButton.icon(
                  onPressed: analyzingRoundPhotos ? null : _analyzePendingRoundPhotos,
                  icon: analyzingRoundPhotos
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.auto_awesome_rounded),
                  label: Text(
                    analyzingRoundPhotos
                        ? 'Analisando...'
                        : 'Analisar e revisar $_pendingPhotoAiCount foto(s) com IA',
                  ),
                ),
                const SizedBox(height: 8),
              ],
              FilledButton.tonalIcon(
                onPressed: reviewingRoundWithAi ? null : _reviewRoundWithAi,
                icon: const Icon(Icons.fact_check_outlined),
                label: const Text('IA · Revisar a ronda e conclusão'),
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: generatingReport
                    ? null
                    : () => _shareRoundReport(ExpressRoundReportStyle.photographic),
                icon: const Icon(Icons.photo_library_outlined),
                label: const Text('Gerar relatório fotográfico'),
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: generatingReport
                    ? null
                    : () => _shareRoundReport(ExpressRoundReportStyle.technical),
                icon: const Icon(Icons.description_outlined),
                label: const Text('Gerar relatório técnico'),
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: roundRecords.isEmpty ? null : _showRoundHistory,
                icon: const Icon(Icons.edit_note_rounded),
                label: const Text('Revisar / editar registros'),
              ),
              if (roundRecords.isNotEmpty) ...[
                const SizedBox(height: 12),
                _recordsSummary(),
              ],
            ],
          ),
        ),
      );

  Widget _historicalBottomBar() => SafeArea(
        child: Material(
          elevation: 10,
          color: Theme.of(context).scaffoldBackgroundColor,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
            child: SizedBox(
              width: double.infinity,
              child: FilledButton.tonalIcon(
                onPressed: _returnToActiveRound,
                icon: const Icon(Icons.arrow_back_rounded),
                label: const Padding(
                  padding: EdgeInsets.symmetric(vertical: 14),
                  child: Text('Voltar à ronda atual'),
                ),
              ),
            ),
          ),
        ),
      );

'''

ronda = once(
    ronda,
    '  bool _recordIsConformity(SstRecord record) =>\n',
    archive_methods + '  bool _recordIsConformity(SstRecord record) =>\n',
    'metodos de historico e revisao',
)

new_batch = r'''  Future<void> _analyzePendingRoundPhotos() async {
    if (analyzingRoundPhotos) return;
    final pending = roundRecords.where(_recordNeedsPhotoAi).toList();
    if (pending.isEmpty) {
      _message('Não há fotos pendentes de análise nesta ronda.');
      return;
    }

    setState(() => analyzingRoundPhotos = true);
    var completed = 0;
    var skipped = 0;
    var failed = 0;
    var stoppedByNetwork = false;
    _message('A IA vai analisar uma foto por vez. Você revisará cada sugestão antes de salvar.');
    try {
      for (final record in pending) {
        final original = Map<String, dynamic>.from(record.payload);
        final path = '${original['photoPath'] ?? ''}'.trim();
        if (path.isEmpty || !File(path).existsSync()) {
          failed += 1;
          continue;
        }

        final conformity = _recordIsConformity(record);
        final reply = await AiAssistantService.analyzeSafetyObservationPhoto(
          company: widget.company,
          observationKind: conformity ? 'Conformidade' : 'Condição insegura',
          sectorName: '${original['sectorName'] ?? ''}',
          location: '${original['location'] ?? ''}',
          photoPath: path,
          technicianContext: _recordTechnicianContext(record),
        );
        final now = DateTime.now();

        if (!reply.success) {
          failed += 1;
          final failedPayload = Map<String, dynamic>.from(original)
            ..['aiStatus'] = 'ERRO'
            ..['aiLastError'] = reply.message
            ..['updatedAt'] = now.toIso8601String();
          await AppDatabase.instance.upsertSstRecord(
            SstRecord(
              id: record.id,
              companyId: record.companyId,
              sectorId: record.sectorId,
              type: record.type,
              title: record.title,
              date: record.date,
              status: record.status,
              priority: record.priority,
              payload: failedPayload,
            ),
          );
          if (_isNetworkLikeAiFailure(reply.message)) {
            stoppedByNetwork = true;
            break;
          }
          continue;
        }

        if (!mounted) break;
        final approved = await _reviewDeferredAiSuggestion(record, reply.result);
        if (!mounted) break;
        if (approved == null) {
          skipped += 1;
          continue;
        }

        final nextPriority = conformity
            ? 'Baixa'
            : '${approved['priority'] ?? record.priority}';
        final nextPayload = Map<String, dynamic>.from(original)
          ..['description'] = '${approved['description'] ?? ''}'.trim().isNotEmpty
              ? '${approved['description']}'.trim()
              : '${original['description'] ?? ''}'
          ..['risk'] = '${approved['risk'] ?? ''}'
          ..['possibleConsequence'] = '${approved['possibleConsequence'] ?? ''}'
          ..['recommendation'] = '${approved['recommendation'] ?? ''}'
          ..['immediateAction'] = '${approved['immediateAction'] ?? ''}'
          ..['responsible'] = '${approved['responsibleProfile'] ?? ''}'
          ..['likelyReferences'] = approved['likelyReferences'] ?? const <String>[]
          ..['checksRequired'] = approved['checksRequired'] ?? const <String>[]
          ..['aiConfidence'] = '${approved['confidence'] ?? ''}'
          ..['aiAssisted'] = true
          ..['aiStatus'] = 'CONCLUIDA'
          ..['aiLastError'] = ''
          ..['aiAnalyzedAt'] = now.toIso8601String()
          ..['aiReviewedByTechnician'] = true
          ..['aiReviewedAt'] = now.toIso8601String()
          ..['updatedAt'] = now.toIso8601String();

        await AppDatabase.instance.upsertSstRecord(
          SstRecord(
            id: record.id,
            companyId: record.companyId,
            sectorId: record.sectorId,
            type: record.type,
            title: record.title,
            date: record.date,
            status: record.status,
            priority: nextPriority,
            payload: nextPayload,
          ),
        );
        completed += 1;
      }
    } finally {
      await _reloadRoundRecords();
      if (mounted) setState(() => analyzingRoundPhotos = false);
    }

    if (!mounted) return;
    if (stoppedByNetwork) {
      _message(
        'IA interrompida por instabilidade de rede/Google. $completed análise(s) aprovadas ficaram salvas e o restante continua pendente.',
      );
    } else if (failed > 0 || skipped > 0) {
      _message(
        'IA: $completed aprovada(s), $skipped mantida(s) pendente(s) e $failed indisponível(is).',
      );
    } else {
      _message('IA concluída: $completed registro(s) revisados e aprovados pelo técnico.');
    }
  }

'''

pattern = re.compile(
    r"  Future<void> _analyzePendingRoundPhotos\(\) async \{.*?\n  Future<void> _showRoundHistory\(\) async \{",
    re.S,
)
ronda, count = pattern.subn(
    new_batch + '  Future<void> _showRoundHistory() async {',
    ronda,
    count=1,
)
if count != 1:
    raise RuntimeError('Marcador ausente: substituir análise em lote da Ronda')

ronda = once(
    ronda,
    "                        'Registros da ronda atual',\n",
    "                        viewingHistoricalRound\n                            ? 'Registros da ronda encerrada'\n                            : 'Registros da ronda atual',\n",
    'titulo do historico de registros',
)

ronda = once(
    ronda,
    "        title: const Text('Ronda Expressa'),\n        actions: [\n",
    "        title: Text(\n          viewingHistoricalRound ? 'Ronda Expressa · histórico' : 'Ronda Expressa',\n        ),\n        actions: [\n          IconButton(\n            tooltip: 'Histórico de rondas',\n            onPressed: _showRoundsArchive,\n            icon: const Icon(Icons.folder_open_outlined),\n          ),\n",
    'atalho de historico no appbar',
)

ronda = once(
    ronda,
    "      body: loading\n          ? const Center(child: CircularProgressIndicator())\n          : Center(\n",
    "      body: loading\n          ? const Center(child: CircularProgressIndicator())\n          : viewingHistoricalRound\n              ? _historicalRoundBody()\n              : Center(\n",
    'body em modo historico',
)

ronda = once(
    ronda,
    "      bottomNavigationBar: SafeArea(\n",
    "      bottomNavigationBar: viewingHistoricalRound\n          ? _historicalBottomBar()\n          : SafeArea(\n",
    'barra inferior historica',
)

rondap.write_text(ronda, encoding='utf-8', newline='\n')
pubp.write_text(pub, encoding='utf-8', newline='\n')

assert 'version: 3.29.61+203' in pub
assert 'viewingHistoricalRound' in ronda
assert '_showRoundsArchive' in ronda
assert '_historicalRoundBody' in ronda
assert '_reviewDeferredAiSuggestion' in ronda
assert "..['aiReviewedByTechnician'] = true" in ronda
assert 'Aprovar e salvar' in ronda
assert 'Manter pendente' in ronda
assert 'Voltar à ronda atual' in ronda
assert "setSetting(_openRoundSetting, '')" in ronda
print('Android v3.29.61+203: histórico pós-fechamento e revisão obrigatória da IA aplicados; sync preservado.')

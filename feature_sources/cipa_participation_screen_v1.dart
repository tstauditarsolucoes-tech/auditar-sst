part of 'cipa_management_screen.dart';

// Additive application records use the existing CIPA_DOCUMENTO envelope.
// No new table, endpoint, auth role or synchronization implementation.
extension _CipaParticipation on _CipaManagementScreenState {
  bool _cipaIsEvent(SstRecord r) =>
      r.payload['workspaceEvent'] == CipaParticipationRules.marker;

  CipaParticipationRules get _cipaRules => CipaParticipationRules(
    widget.companyId,
    documents.where(_cipaIsEvent).map((r) =>
        CipaParticipationEvent(r.id, r.companyId, r.date, r.payload)),
  );

  bool _cipaArchived(SstRecord r) => _cipaRules.hiddenByArchive(
      r.id, r.type, r.status, r.payload['signed'] == true);

  bool _cipaVisible(SstRecord r) => r.companyId == widget.companyId &&
      !_cipaIsEvent(r) && !_cipaArchived(r);

  List<SstRecord> get _cipaAllRecords =>
      [...mandates, ...members, ...meetings, ...minutes, ...actions, ...documents]
          .where((r) => r.companyId == widget.companyId && !_cipaIsEvent(r)).toList();

  String _cipaMandateName(String id) {
    for (final m in mandates) {
      if (m.id == id) return m.title;
    }
    return 'Mandato anterior';
  }

  Future<void> _cipaEvent(String kind, String targetId,
      Map<String, dynamic> details, {String? mandateId, String? eventId}) async {
    await CipaManagementService.saveRecord(
      id: eventId,
      companyId: widget.companyId,
      type: CipaManagementService.documentType,
      title: 'Registro de gestão CIPA • $kind',
      date: DateTime.now(),
      status: 'Registrado',
      payload: {
        ...details,
        'workspaceEvent': CipaParticipationRules.marker,
        'category': 'Registro de gestão CIPA',
        'requiredDocument': false,
        'mandateId': mandateId ?? activeMandate?.id ?? '',
        'kind': kind,
        'targetId': targetId,
      },
    );
  }

  Future<void> _cipaRun(Future<void> Function() task) async {
    if (!mounted || busy) return;
    setState(() => busy = true);
    try {
      await task();
      await _load(showLoading: false);
    } catch (_) {
      _message('Não foi possível concluir. Confira os registros antes de tentar novamente.');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<String?> _cipaReason(String title, String explanation) async {
    final text = TextEditingController();
    final result = await showDialog<String>(
      context: context,
      builder: (dialog) => StatefulBuilder(builder: (context, setLocal) => AlertDialog(
        title: Text(title),
        content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text(explanation),
          const SizedBox(height: 12),
          TextField(controller: text, maxLines: 3,
            onChanged: (_) => setLocal(() {}),
            decoration: const InputDecoration(labelText: 'Motivo / registro breve (obrigatório)')),
        ])),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialog), child: const Text('Cancelar')),
          FilledButton(onPressed: text.text.trim().isEmpty ? null :
            () => Navigator.pop(dialog, text.text.trim()), child: const Text('Confirmar')),
        ],
      )),
    );
    text.dispose();
    return result;
  }

  Future<void> _cipaArchive(SstRecord item, {bool restore = false}) async {
    if (item.companyId != widget.companyId || busy) return;
    if (!restore && !CipaParticipationRules.canArchive(
        item.type, item.status, item.payload['signed'] == true)) return;
    // Older clients attach signed files without setting payload['signed'].
    // Keep any minutes with attachments visible instead of guessing their content.
    if (!restore && item.type == CipaManagementService.minutesType) {
      try {
        final attachments = await CipaManagementService.attachments(
          entityType: 'cipa_minutes', entityId: item.id);
        if (!mounted) return;
        if (attachments.isNotEmpty) {
          _message('Ata com anexos preservada na lista. Use uma nova revisão para corrigir o conteúdo.');
          return;
        }
      } catch (_) {
        _message('Não foi possível conferir os anexos. O arquivamento foi bloqueado por segurança.');
        return;
      }
    }
    final reason = await _cipaReason(restore ? 'Restaurar registro' : 'Arquivar registro',
      '${item.title}\nO registro e seus anexos serão preservados. '
      'Pendências abertas e atas finalizadas não podem ser ocultadas por este botão.');
    if (reason == null || !mounted) return;
    await _cipaRun(() => _cipaEvent(restore ? 'restore' : 'archive', item.id,
      {'reason': reason, 'title': item.title}, mandateId: '${item.payload['mandateId'] ?? item.id}'));
  }

  Widget _cipaRecordCard(SstRecord item, Widget child) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [child,
      if (CipaParticipationRules.canArchive(item.type, item.status, item.payload['signed'] == true))
        Align(alignment: Alignment.centerRight, child: TextButton.icon(
          onPressed: busy ? null : () => _cipaArchive(item),
          icon: const Icon(Icons.archive_outlined, size: 18), label: const Text('Arquivar sem excluir'))),
    ],
  );

  Future<void> _cipaHandover() async {
    final target = activeMandate;
    if (target == null || busy) return;
    final candidates = actions.where((a) => _cipaVisible(a) && a.status != 'Resolvida' &&
      '${a.payload['mandateId'] ?? ''}' != target.id &&
      !_cipaRules.carriedTo(a.id, target.id)).toList();
    if (candidates.isEmpty) {
      _message('Não há pendências de outros mandatos para trazer.');
      return;
    }
    final selected = <String>{};
    final confirm = await showDialog<bool>(context: context, builder: (dialog) =>
      StatefulBuilder(builder: (context, setLocal) => AlertDialog(
        title: const Text('Passagem de mandato'),
        content: SizedBox(width: 550, child: SingleChildScrollView(child: Column(
          mainAxisSize: MainAxisSize.min, children: [
            Text('Selecione as pendências para ${target.title}. Os registros originais, '
              'prazos, responsáveis, NCs e evidências serão mantidos. Não serão criadas ações duplicadas.'),
            ...candidates.map((a) => CheckboxListTile(
              value: selected.contains(a.id), title: Text(a.title),
              subtitle: Text('${_cipaMandateName('${a.payload['mandateId'] ?? ''}')} • ${a.status}'),
              onChanged: (checked) => setLocal(() {
                checked == true ? selected.add(a.id) : selected.remove(a.id);
              }),
            )),
          ],
        ))),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialog, false), child: const Text('Cancelar')),
          FilledButton(onPressed: selected.isEmpty ? null : () => Navigator.pop(dialog, true),
            child: const Text('Trazer pendências')),
        ],
      )),
    );
    if (confirm != true || !mounted || activeMandate?.id != target.id) return;
    await _cipaRun(() => _cipaEvent('handover', target.id, {
      'actionIds': selected.toList(),
      'snapshots': candidates.where((a) => selected.contains(a.id)).map((a) => {
        'id': a.id, 'title': a.title, 'sourceMandateId': a.payload['mandateId'],
        'status': a.status, 'responsible': a.payload['responsible'],
        'dueDate': a.dueDate?.toIso8601String(),
      }).toList(),
    }, mandateId: target.id));
  }

  Future<void> _cipaSupport(SstRecord action) async {
    if (busy || action.status == 'Resolvida' || !_cipaVisible(action)) return;
    final notes = TextEditingController();
    var category = 'Manutenção';
    final save = await showDialog<bool>(context: context, builder: (dialog) =>
      StatefulBuilder(builder: (context, setLocal) => AlertDialog(
        title: const Text('Preciso de apoio'),
        content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text(action.title),
          DropdownButtonFormField<String>(value: category, isExpanded: true,
            items: ['Compra', 'Manutenção', 'Autorização', 'Orientação']
              .map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
            onChanged: (value) { if (value != null) setLocal(() => category = value); }),
          TextField(controller: notes, maxLines: 3, onChanged: (_) => setLocal(() {}),
            decoration: const InputDecoration(labelText: 'Qual apoio é necessário?')),
          const SizedBox(height: 10),
          const Text('O pedido ficará destacado na CIPA. Não envia mensagem ou e-mail automaticamente.'),
        ])),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialog, false), child: const Text('Cancelar')),
          FilledButton(onPressed: notes.text.trim().isEmpty ? null :
            () => Navigator.pop(dialog, true), child: const Text('Registrar pedido')),
        ],
      )),
    );
    final detail = notes.text.trim();
    notes.dispose();
    if (save != true || !mounted) return;
    await _cipaRun(() => _cipaEvent('support_requested', action.id,
      {'categoryName': category, 'detail': detail, 'title': action.title}));
  }

  Future<void> _cipaCompleteSupport(SstRecord action) async {
    final reason = await _cipaReason('Registrar apoio atendido',
      'Descreva o apoio prestado para ${action.title}. Isso não encerra a ação automaticamente.');
    if (reason == null || !mounted) return;
    await _cipaRun(() => _cipaEvent('support_completed', action.id,
      {'detail': reason, 'title': action.title}));
  }

  Future<void> _cipaSuggestAgenda(TextEditingController agenda) async {
    final pending = mandateActions.where((a) => a.status != 'Resolvida').toList();
    if (pending.isEmpty) { _message('Não há ações pendentes para sugerir.'); return; }
    final selected = <String>{};
    final ok = await showDialog<bool>(context: context, builder: (dialog) =>
      StatefulBuilder(builder: (context, setLocal) => AlertDialog(
        title: const Text('Pendências para a pauta'),
        content: SizedBox(width: 520, child: SingleChildScrollView(child: Column(
          mainAxisSize: MainAxisSize.min,
          children: pending.map((a) => CheckboxListTile(
            title: Text(a.title), subtitle: Text('Responsável: ${a.payload['responsible'] ?? '-'}'),
            value: selected.contains(a.id), onChanged: (v) => setLocal(() {
              v == true ? selected.add(a.id) : selected.remove(a.id);
            }),
          )).toList(),
        ))),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialog, false), child: const Text('Cancelar')),
          FilledButton(onPressed: selected.isEmpty ? null : () => Navigator.pop(dialog, true),
            child: const Text('Adicionar à pauta')),
        ],
      )),
    );
    if (ok != true || !mounted) return;
    agenda.text = CipaParticipationRules.appendAgenda(agenda.text,
      pending.where((a) => selected.contains(a.id)).map((a) =>
        '• Acompanhar: ${a.title} — ${a.payload['responsible'] ?? 'responsável a definir'}'));
  }

  Iterable<SstRecord> _cipaMinuteFamily(SstRecord ata) {
    final meetingId = '${ata.payload['meetingId'] ?? ''}';
    final root = '${ata.payload['revisionRootId'] ?? ata.id}';
    return minutes.where((a) => a.companyId == widget.companyId && (meetingId.isNotEmpty
      ? '${a.payload['meetingId'] ?? ''}' == meetingId
      : a.id == root || '${a.payload['revisionRootId'] ?? ''}' == root));
  }

  Future<void> _cipaReviseMinutes(SstRecord ata) async {
    final content = TextEditingController(text: '${ata.payload['content'] ?? ''}');
    final reason = TextEditingController();
    final save = await showDialog<bool>(context: context, builder: (dialog) =>
      StatefulBuilder(builder: (context, setLocal) => AlertDialog(
        title: const Text('Nova revisão da ata'),
        content: SizedBox(width: 650, child: SingleChildScrollView(child: Column(
          mainAxisSize: MainAxisSize.min, children: [
            const Text('A versão anterior e suas assinaturas ficam preservadas. '
              'Esta revisão será um novo rascunho, sem copiar assinaturas.'),
            TextField(controller: reason, onChanged: (_) => setLocal(() {}),
              decoration: const InputDecoration(labelText: 'Motivo da revisão')),
            TextField(controller: content, minLines: 6, maxLines: 18,
              onChanged: (_) => setLocal(() {}), decoration: const InputDecoration(labelText: 'Conteúdo')),
          ],
        ))),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialog, false), child: const Text('Cancelar')),
          FilledButton(onPressed: reason.text.trim().isEmpty || content.text.trim().isEmpty ? null :
            () => Navigator.pop(dialog, true), child: const Text('Criar revisão')),
        ],
      )),
    );
    final revised = content.text.trim();
    final note = reason.text.trim();
    content.dispose(); reason.dispose();
    if (save != true || !mounted) return;
    await _cipaRun(() => CipaManagementService.saveRecord(
      companyId: widget.companyId, type: CipaManagementService.minutesType,
      title: ata.title, date: ata.date, status: 'Rascunho',
      payload: {
        'mandateId': ata.payload['mandateId'], 'meetingId': ata.payload['meetingId'] ?? '',
        'content': revised, 'version': CipaParticipationRules.nextVersion(
          _cipaMinuteFamily(ata).map((a) => a.payload['version'])),
        'signed': false, 'importedByAi': false,
        'revisionRootId': ata.payload['revisionRootId'] ?? ata.id,
        'previousVersionId': ata.id, 'revisionReason': note,
        'revisedAt': DateTime.now().toIso8601String(),
      },
    ));
  }

  Future<void> _cipaFinalizeMinutes(SstRecord ata) async {
    if (ata.status != 'Rascunho' || '${ata.payload['content'] ?? ''}'.trim().isEmpty) return;
    final reason = await _cipaReason('Finalizar conteúdo da ata',
      'Após finalizar, correções exigirão nova revisão. Finalizar não equivale a assinar a ata.');
    if (reason == null || !mounted) return;
    await _cipaRun(() => CipaManagementService.saveRecord(
      id: ata.id, companyId: widget.companyId, type: ata.type, title: ata.title,
      date: ata.date, dueDate: ata.dueDate, priority: ata.priority, status: 'Finalizada',
      payload: {...ata.payload, 'finalizedAt': DateTime.now().toIso8601String(), 'finalizationNote': reason},
    ));
  }

  Widget _cipaMinutesTools(SstRecord ata) => Wrap(spacing: 6, children: [
    TextButton.icon(onPressed: busy ? null : () => _cipaReviseMinutes(ata),
      icon: const Icon(Icons.edit_note), label: const Text('Criar revisão')),
    if (ata.status == 'Rascunho' && ata.payload['signed'] != true)
      TextButton(onPressed: busy ? null : () => _cipaFinalizeMinutes(ata), child: const Text('Finalizar conteúdo')),
  ]);

  Future<void> _cipaMonthlyPdf() async {
    final month = _cipaReportMonth;
    // Resolved records still belong in the report after presentation archiving.
    final mandateId = activeMandate?.id ?? '';
    final rows = actions.where((a) => a.companyId == widget.companyId &&
      (mandateId.isEmpty || '${a.payload['mandateId'] ?? ''}' == mandateId ||
        _cipaRules.carriedTo(a.id, mandateId))).toList();
    final rules = _cipaRules;
    final performed = mandateMeetings.where((m) => m.status == 'Realizada' &&
        CipaParticipationRules.inMonth(m.date, month)).toList();
    final completed = rows.where((a) {
      final date = rules.knownCompletion(a.id, a.status,
        linkedNc: '${a.payload['ncId'] ?? ''}'.isNotEmpty);
      return date != null && CipaParticipationRules.inMonth(date, month);
    }).toList();
    final undated = rows.where((a) => a.status == 'Resolvida' &&
      rules.knownCompletion(a.id, a.status,
        linkedNc: '${a.payload['ncId'] ?? ''}'.isNotEmpty) == null).length;
    final pending = rows.where((a) => a.status != 'Resolvida').toList();
    final needsSupport = pending.where((a) => rules.support(a.id) != null).toList();
    final doc = pw.Document();
    doc.addPage(pw.MultiPage(pageFormat: PdfPageFormat.a4, margin: const pw.EdgeInsets.all(36),
      footer: (c) => pw.Text('${c.pageNumber}/${c.pagesCount}', textAlign: pw.TextAlign.right),
      build: (_) => [
        _pdfHeading('CIPA • Resumo para a gestão • ${DateFormat('MM/yyyy').format(month)}'),
        pw.Text('Empresa: ${company?.name ?? ''}'),
        pw.Text('Mandato: ${activeMandate?.title ?? 'Todos os mandatos'}'),
        pw.Text('Emitido em ${_dateTime.format(DateTime.now())}'),
        pw.SizedBox(height: 12),
        pw.Text('No mês selecionado: ${performed.length} reunião(ões) realizada(s); '
          '${completed.length} conclusão(ões) com data registrada neste módulo.'),
        pw.Text('Situação atual: ${pending.length} ação(ões) pendente(s); '
          '${pending.where(CipaManagementService.isOverdue).length} vencida(s); '
          '${needsSupport.length} pedido(s) de apoio em aberto.'),
        pw.Text('As pendências refletem a situação atual, não uma fotografia histórica do mês. '
          'Conclusões antigas ou automáticas sem data não entram na contagem mensal ($undated registro(s)).'),
        pw.SizedBox(height: 12), _pdfHeading('Resultados registrados no mês'),
        if (completed.isEmpty) pw.Text('Nenhuma conclusão datada para este mês.'),
        ...completed.map((a) => pw.Bullet(text: a.title)),
        pw.SizedBox(height: 12), _pdfHeading('Prioridades atuais (até 10)'),
        if (pending.isEmpty) pw.Text('Nenhuma ação aberta neste recorte.'),
        ...(_cipaSortedActions(pending).take(10)).map((a) => pw.Bullet(text:
          '${a.title} • ${a.priority} • ${a.payload['responsible'] ?? '-'} • '
          'Prazo: ${a.dueDate == null ? 'não informado' : _date.format(a.dueDate!)}')),
        if (pending.length > 10) pw.Text('Mais ${pending.length - 10} ação(ões) no plano de ação.'),
        pw.SizedBox(height: 12), _pdfHeading('Apoio necessário (até 10)'),
        if (needsSupport.isEmpty) pw.Text('Nenhum pedido de apoio em aberto.'),
        ...needsSupport.take(10).map((a) => pw.Bullet(text:
          '${a.title}: ${rules.support(a.id)!.data['categoryName']} — ${rules.support(a.id)!.data['detail']}')),
        if (needsSupport.length > 10) pw.Text('Mais ${needsSupport.length - 10} pedido(s) no app.'),
      ],
    ));
    await Printing.sharePdf(bytes: await doc.save(),
      filename: 'CIPA_Resumo_${DateFormat('yyyy-MM').format(month)}.pdf');
  }

  List<SstRecord> _cipaSortedActions(Iterable<SstRecord> source) {
    final list = source.toList();
    const priorities = {'Crítica': 0, 'Alta': 1, 'Média': 2, 'Baixa': 3};
    list.sort((a, b) {
      final priority = (priorities[a.priority] ?? 2).compareTo(priorities[b.priority] ?? 2);
      if (priority != 0) return priority;
      return (a.dueDate ?? DateTime(9999)).compareTo(b.dueDate ?? DateTime(9999));
    });
    return list;
  }

  Future<void> _cipaShowRecord(SstRecord record) => showDialog<void>(context: context,
    builder: (dialog) => AlertDialog(title: Text(record.title),
      content: SingleChildScrollView(child: SelectableText(
        '${record.status}\n${record.payload['description'] ?? record.payload['content'] ?? record.payload['notes'] ?? ''}')),
      actions: [TextButton(onPressed: () => Navigator.pop(dialog), child: const Text('Fechar'))]));


  Widget _cipaMonthlyGuide(CipaParticipationRules rules) {
    final mandate = activeMandate;
    if (mandate == null) return const Card(child: ListTile(
      title: Text('Roteiro mensal da CIPA'),
      subtitle: Text('Selecione um mandato para começar.')));
    final month = DateTime.now();
    final monthKey = CipaParticipationRules.monthKey(month);
    const items = <Map<String, String>>[
      {'key':'verificar_ambiente','title':'Observar as condições de segurança',
       'hint':'Observe sem se aproximar do perigo. Avise o técnico em caso de risco.'},
      {'key':'acompanhar_pendencias','title':'Acompanhar ações pendentes',
       'hint':'Confira os responsáveis, prazos e pedidos de apoio.'},
      {'key':'consultar_reuniao','title':'Conferir a próxima reunião',
       'hint':'Veja a data e os assuntos que precisam ser conversados.'},
      {'key':'registrar_melhoria','title':'Registrar oportunidade de melhoria',
       'hint':'Anote local e situação observada, sem precisar citar uma NR.'},
    ];
    final count = items.where((i) => rules.monthlyDone(mandate.id, month, i['key']!)).length;
    return Card(child: ExpansionTile(
      leading: const Icon(Icons.fact_check_outlined),
      title: Text('Roteiro mensal • ${month.month.toString().padLeft(2, '0')}/${month.year}'),
      subtitle: Text('$count de ${items.length} atividades acompanhadas'),
      initiallyExpanded: _cipaSimpleMode,
      children: [
        const Padding(padding: EdgeInsets.all(12), child: Text(
          'Roteiro compartilhado da conta atual. Não comprova participação individual, '
          'presença em reunião ou realização de inspeção técnica.')),
        ...items.map((i) => CheckboxListTile(
          title: Text(i['title']!), subtitle: Text(i['hint']!),
          value: rules.monthlyDone(mandate.id, month, i['key']!),
          isThreeLine: true, controlAffinity: ListTileControlAffinity.leading,
          onChanged: busy ? null : (value) {
            if (value == null) return;
            _cipaRun(() => _cipaEvent('monthly_check',
              '${mandate.id}|$monthKey|${i['key']}',
              {'monthKey': monthKey, 'taskKey': i['key'],
                'done': value, 'title': i['title']}, mandateId: mandate.id));
          },
        )),
      ],
    ));
  }

  Future<void> _cipaNewObservation() async {
    final mandate = activeMandate;
    if (mandate == null || busy) return;
    final place = TextEditingController();
    final detail = TextEditingController();
    var attachPhotoNow = false;
    final confirmed = await showDialog<bool>(context: context, builder: (dialog) =>
      StatefulBuilder(builder: (context, update) => AlertDialog(
        title: const Text('Registrar situação observada'),
        content: SizedBox(width: 520, child: SingleChildScrollView(child: Column(
          mainAxisSize: MainAxisSize.min, children: [
            const Text('Escreva com suas palavras. Não se exponha a riscos para registrar. '
              'O técnico avaliará a situação; ela não vira NC automaticamente.'),
            TextField(controller: place, maxLength: 120, onChanged: (_) => update(() {}),
              decoration: const InputDecoration(labelText: 'Local', hintText: 'Ex.: expedição')),
            TextField(controller: detail, maxLength: 1200, maxLines: 5,
              onChanged: (_) => update(() {}),
              decoration: const InputDecoration(labelText: 'O que foi observado?',
                hintText: 'Ex.: caixas obstruindo a passagem')),
            CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              value: attachPhotoNow,
              onChanged: (selected) => update(() => attachPhotoNow = selected == true),
              title: const Text('Adicionar foto depois de salvar'),
              subtitle: const Text('Opcional. Você também pode anexar mais tarde. Não se aproxime de riscos para fotografar.'),
              controlAffinity: ListTileControlAffinity.leading,
            ),
          ],
        ))),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialog, false), child: const Text('Cancelar')),
          FilledButton(onPressed: place.text.trim().isEmpty || detail.text.trim().isEmpty ?
            null : () => Navigator.pop(dialog, true), child: const Text('Salvar')),
        ],
      )),
    );
    final location = place.text.trim(), message = detail.text.trim();
    place.dispose(); detail.dispose();
    if (confirmed != true || !mounted || mandate.id != activeMandate?.id) return;
    final eventId = const Uuid().v4();
    await _cipaRun(() async {
      await _cipaEvent('observation', eventId,
        {'title': 'Situação observada • $location', 'location': location, 'detail': message},
        mandateId: mandate.id, eventId: eventId);
      if (attachPhotoNow && mounted) {
        await _attachTo(entityType: 'cipa_document', entityId: eventId);
      }
    });
  }

  Widget _cipaObservationList(CipaParticipationRules rules) {
    final mandate = activeMandate;
    if (mandate == null) return const SizedBox.shrink();
    final records = rules.observations(mandate.id).toList().reversed.toList();
    return Card(child: ExpansionTile(
      leading: const Icon(Icons.visibility_outlined),
      title: Text('Situações observadas (${records.length})'),
      subtitle: const Text('Registrar e acompanhar sem classificar automaticamente como NC'),
      children: [
        OutlinedButton.icon(onPressed: busy ? null : _cipaNewObservation,
          icon: const Icon(Icons.add_photo_alternate_outlined),
          label: const Text('Registrar situação')),
        if (records.isEmpty) const ListTile(title: Text('Nenhuma situação registrada.')),
        ...records.map((e) => ListTile(
          title: Text('${e.data['location'] ?? 'Local não informado'}'),
          subtitle: Text('${_dateTime.format(e.date)} • ${e.data['detail'] ?? ''}'),
          trailing: PopupMenuButton<String>(
            tooltip: 'Foto e anexos',
            onSelected: (value) {
              if (value == 'add') _attachTo(entityType: 'cipa_document', entityId: e.id);
              if (value == 'view') _showAttachments(entityType: 'cipa_document', entityId: e.id);
            },
            itemBuilder: (_) => const [
              PopupMenuItem(value: 'add', child: Text('Anexar foto')),
              PopupMenuItem(value: 'view', child: Text('Ver anexos')),
            ],
          ),
        )),
      ],
    ));
  }

  // Guided scheduling reuses the current CIPA service; attendance is never inferred.
  Future<void> _cipaGuidedMeeting() async {
    final mandate = activeMandate;
    if (mandate == null || mandate.status == 'Encerrado' || busy) return;
    final title = TextEditingController(text: 'Reunião ordinária da CIPA');
    final location = TextEditingController();
    final agenda = TextEditingController(text:
      '1. Acompanhar as ações pendentes.\n'
      '2. Conversar sobre situações observadas e sugestões.\n'
      '3. Definir responsáveis e prazos.\n'
      '4. Confirmar os próximos encaminhamentos.');
    var dateTime = DateTime.now().add(const Duration(days: 7));
    var kind = 'Ordinária';
    final choices = _cipaSortedActions(
      mandateActions.where((a) => a.status != 'Resolvida'),
    ).take(8).toList();
    final chosen = <String>{};
    final confirmation = await showDialog<bool>(
      context: context,
      builder: (dialog) => StatefulBuilder(
        builder: (context, update) => AlertDialog(
          title: const Text('Preparar reunião passo a passo'),
          content: SizedBox(width: 540, child: SingleChildScrollView(
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              const Text('Preencha os dados básicos. A reunião será agendada, '
                'sem confirmar presença nem gerar ata automaticamente.'),
              const SizedBox(height: 12),
              TextField(controller: title, maxLength: 180,
                onChanged: (_) => update(() {}),
                decoration: const InputDecoration(labelText: 'Nome da reunião')),
              DropdownButtonFormField<String>(
                value: kind, isExpanded: true,
                decoration: const InputDecoration(labelText: 'Tipo de reunião'),
                items: const [
                  DropdownMenuItem(value: 'Ordinária', child: Text('Ordinária')),
                  DropdownMenuItem(value: 'Extraordinária', child: Text('Extraordinária')),
                ],
                onChanged: (v) { if (v != null) update(() => kind = v); },
              ),
              ListTile(contentPadding: EdgeInsets.zero,
                title: const Text('Data e horário'),
                subtitle: Text(_dateTime.format(dateTime)),
                trailing: const Icon(Icons.calendar_month_outlined),
                onTap: () async {
                  final selected = await _pickDateTime(dateTime);
                  if (selected != null) update(() => dateTime = selected);
                }),
              TextField(controller: location, maxLength: 180,
                decoration: const InputDecoration(labelText: 'Local (opcional)',
                  hintText: 'Ex.: sala de reuniões')),
              TextField(controller: agenda, minLines: 4, maxLines: 7,
                maxLength: 1800, decoration: const InputDecoration(
                  labelText: 'Pauta sugerida (você pode editar)')),
              if (choices.isNotEmpty) ...[
                const Align(alignment: Alignment.centerLeft, child: Text(
                  'Adicionar pendências à pauta (opcional)',
                  style: TextStyle(fontWeight: FontWeight.bold))),
                ...choices.map((action) => CheckboxListTile(
                  contentPadding: EdgeInsets.zero, dense: true,
                  value: chosen.contains(action.id),
                  title: Text(action.title, maxLines: 2,
                    overflow: TextOverflow.ellipsis),
                  onChanged: (v) => update(() {
                    v == true ? chosen.add(action.id) : chosen.remove(action.id);
                  }),
                )),
              ],
              const Text('Depois da reunião, a equipe precisa registrar '
                'os assuntos, conferir os presentes e revisar a ata.'),
            ]),
          )),
          actions: [
            TextButton(onPressed: () => Navigator.pop(dialog, false),
              child: const Text('Cancelar')),
            FilledButton(
              onPressed: title.text.trim().isEmpty ? null :
                () => Navigator.pop(dialog, true),
              child: const Text('Agendar reunião')),
          ],
        ),
      ),
    );
    final meetingTitle = title.text.trim();
    final meetingPlace = location.text.trim();
    final meetingAgenda = CipaParticipationRules.appendAgenda(
      agenda.text.trim(),
      choices.where((a) => chosen.contains(a.id)).map((a) =>
        '• Acompanhar: ${a.title} — ${a.payload['responsible'] ?? 'a definir'}'),
    );
    title.dispose();
    location.dispose();
    agenda.dispose();
    if (confirmation != true || !mounted || mandate.id != activeMandate?.id ||
        mandate.status == 'Encerrado') return;
    final meetingId = const Uuid().v4();
    await _cipaRun(() async {
      await CipaManagementService.saveMeeting(
        id: meetingId,
        companyId: widget.companyId,
        mandateId: mandate.id,
        title: meetingTitle,
        dateTime: dateTime,
        meetingKind: kind,
        place: meetingPlace,
        agenda: meetingAgenda,
        subjects: '',
        decisions: '',
        memberIds: activeMembers.map((m) => m.id).toList(),
        presentIds: const [],
        status: 'Agendada',
      );
    });
  }

  Widget _cipaMeetingGuide() => Card(child: ExpansionTile(
    leading: const Icon(Icons.menu_book_outlined),
    title: const Text('Guia rápido para reunião'),
    subtitle: const Text('Como preparar, registrar e acompanhar uma reunião da CIPA'),
    children: [
      const ListTile(title: Text('1. Prepare a pauta'),
        subtitle: Text('Inclua pendências, riscos observados e sugestões de prevenção.')),
      const ListTile(title: Text('2. Registre as decisões'),
        subtitle: Text('Anote encaminhamentos, responsáveis e prazos.')),
      const ListTile(title: Text('3. Revise a ata'),
        subtitle: Text('Conferir presença, texto e assinaturas conforme o procedimento da empresa.')),
      const ListTile(title: Text('4. Acompanhe'),
        subtitle: Text('Verifique as ações na reunião seguinte. A minuta não substitui ata assinada.')),
      OutlinedButton.icon(
        onPressed: busy || activeMandate == null ||
            activeMandate?.status == 'Encerrado' ? null : _cipaGuidedMeeting,
        icon: const Icon(Icons.auto_stories_outlined),
        label: const Text('Preparar reunião guiada')),
      TextButton.icon(
        onPressed: busy || activeMandate == null ? null : () => _editMeeting(),
        icon: const Icon(Icons.edit_note_outlined),
        label: const Text('Abrir editor completo de reuniões')),
    ],
  ));

  Widget _cipaWorkspaceTab() {
    final rules = _cipaRules;
    final pending = _cipaSortedActions(mandateActions.where((a) => a.status != 'Resolvida'));
    final query = _cipaResponsibleFilter.trim().toLowerCase();
    final visible = pending.where((a) => query.isEmpty ||
        '${a.payload['responsible'] ?? ''}'.toLowerCase().contains(query));
    final resolved = mandateActions.where((a) => a.status == 'Resolvida').toList();
    final archived = _cipaAllRecords.where(_cipaArchived).toList();
    return ListView(padding: const EdgeInsets.fromLTRB(16, 16, 16, 90), children: [
      const Text('CIPA em ação', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
      Text(company?.name ?? ''),
      const SizedBox(height: 8),
      const Text('Visão de trabalho da conta já conectada. O filtro por responsável não altera '
        'permissões nem cria acesso individual de membro. Canal de denúncias fora deste módulo.'),
      const SizedBox(height: 12),
      Wrap(spacing: 8, runSpacing: 8, children: [
        FilledButton.icon(onPressed: busy || activeMandate == null ? null : () => _editAction(),
          icon: const Icon(Icons.add_task), label: const Text('Nova ação')),
        OutlinedButton.icon(onPressed: busy || activeMandate == null ||
             activeMandate?.status == 'Encerrado' ? null : _cipaGuidedMeeting,
           icon: const Icon(Icons.event_outlined),
           label: const Text('Preparar reunião guiada')),
        if (!_cipaSimpleMode)
          OutlinedButton.icon(onPressed: busy || activeMandate == null ? null : _cipaHandover,
            icon: const Icon(Icons.swap_horiz), label: const Text('Passagem de mandato')),
      ]),
      if (nextMeeting != null) Card(child: ListTile(
        leading: const Icon(Icons.event), title: Text(nextMeeting!.title),
        subtitle: Text('Próxima reunião: ${_dateTime.format(nextMeeting!.date)}'),
        onTap: () => _editMeeting(nextMeeting))),
      const SizedBox(height: 12),
      _cipaMonthlyGuide(rules),
      _cipaObservationList(rules),
      _cipaMeetingGuide(),
      TextField(onChanged: (value) => setState(() => _cipaResponsibleFilter = value),
        decoration: const InputDecoration(prefixIcon: Icon(Icons.search),
          labelText: 'Filtrar ações por nome do responsável', helperText: 'Somente filtro de visualização')),
      const SizedBox(height: 12),
      Text('Ações pendentes (${visible.length})', style: const TextStyle(fontWeight: FontWeight.w800)),
      if (visible.isEmpty) const Padding(padding: EdgeInsets.all(16), child: Text('Nenhuma ação neste filtro.')),
      ...visible.map((a) {
        final help = rules.support(a.id);
        final original = '${a.payload['mandateId'] ?? ''}';
        return Card(child: Padding(padding: const EdgeInsets.all(12), child: Column(
          crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(a.title, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
            Text('${a.payload['responsible'] ?? '-'} • ${a.priority} • ${a.status}'),
            Text('Prazo: ${a.dueDate == null ? '-' : _date.format(a.dueDate!)}'),
            if (CipaManagementService.isOverdue(a)) const Text('Prazo vencido', style: TextStyle(color: Colors.red)),
            if (activeMandate != null && original != activeMandate!.id)
              Text('Origem preservada: ${_cipaMandateName(original)}'),
            if (help != null) Padding(padding: const EdgeInsets.symmetric(vertical: 8),
              child: Text('APOIO NECESSÁRIO • ${help.data['categoryName']}\n${help.data['detail']}',
                style: const TextStyle(fontWeight: FontWeight.w700))),
            Wrap(spacing: 8, children: [
              TextButton(onPressed: busy ? null : () => _editAction(current: a), child: const Text('Atualizar ação')),
              TextButton(onPressed: busy ? null : () => _cipaSupport(a), child: const Text('Preciso de apoio')),
              if (help != null) TextButton(onPressed: busy ? null : () => _cipaCompleteSupport(a),
                child: const Text('Apoio atendido')),
              TextButton(onPressed: () => _showAttachments(entityType: 'cipa_action', entityId: a.id),
                child: const Text('Ver evidências')),
            ]),
          ],
        )));
      }),
      const SizedBox(height: 16),
      if (!_cipaSimpleMode) ...[
        const Text('Resumo mensal para a gestão', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
        Wrap(spacing: 8, children: [
          TextButton.icon(icon: const Icon(Icons.calendar_month),
            label: Text(DateFormat('MM/yyyy').format(_cipaReportMonth)),
            onPressed: () async {
              final date = await _pickDate(_cipaReportMonth);
              if (date != null && mounted) setState(() => _cipaReportMonth = DateTime(date.year, date.month));
            }),
          FilledButton.icon(onPressed: busy ? null : () => _cipaRun(_cipaMonthlyPdf),
            icon: const Icon(Icons.picture_as_pdf), label: const Text('Gerar resumo PDF')),
        ]),
      ],
      const SizedBox(height: 16),
      ExpansionTile(title: Text('Melhorias realizadas pela equipe (${resolved.length})'),
        subtitle: const Text('Resultados coletivos, sem ranking individual. Situação registrada no app.'),
        children: [
          if (resolved.isEmpty) const ListTile(title: Text('Nenhuma ação resolvida neste recorte.')),
          ...resolved.map((a) => ListTile(leading: const Icon(Icons.check_circle_outline),
            title: Text(a.title), subtitle: Text('${a.payload['description'] ?? ''}'),
            onTap: () => _showAttachments(entityType: 'cipa_action', entityId: a.id))),
        ]),
      if (!_cipaSimpleMode) ...[
        ExpansionTile(title: Text('Registros arquivados (${archived.length})'),
          subtitle: const Text('Não foram excluídos. Restaurar mantém os anexos e a origem.'),
          children: archived.map((r) => ListTile(title: Text(r.title), subtitle: Text(r.status),
            onTap: () => _cipaShowRecord(r), trailing: IconButton(tooltip: 'Restaurar',
              onPressed: busy ? null : () => _cipaArchive(r, restore: true),
              icon: const Icon(Icons.unarchive_outlined)))).toList()),
        ExpansionTile(title: const Text('Histórico da participação e passagem de mandato'),
          subtitle: const Text('Registro operacional de alterações; não substitui assinatura ou auditoria de acesso.'),
          children: rules.events.reversed.map((e) => ListTile(
            title: Text(_cipaEventLabel(e.kind)), subtitle: Text(
              '${_dateTime.format(e.date)} • ${e.data['title'] ?? _cipaMandateName(e.targetId)}\n'
              '${e.data['reason'] ?? e.data['detail'] ?? (e.kind == 'handover' ? '${(e.data['actionIds'] as List?)?.length ?? 0} ação(ões) mantidas com origem preservada' : e.data['status'] ?? '')}'),
            onTap: e.kind != 'handover' ? null : () => showDialog<void>(context: context,
              builder: (dialog) => AlertDialog(title: const Text('Pendências na passagem de mandato'),
                content: SizedBox(width: 520, child: SingleChildScrollView(child: Column(
                  mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Registro de ${_dateTime.format(e.date)}. Situação daquele momento:'),
                    for (final snapshot in (e.data['snapshots'] as List? ?? []).whereType<Map>())
                      ListTile(title: Text('${snapshot['title'] ?? ''}'), subtitle: Text(
                        '${_cipaMandateName('${snapshot['sourceMandateId'] ?? ''}')} • ${snapshot['status'] ?? ''}\n'
                        'Responsável: ${snapshot['responsible'] ?? '-'}')),
                  ],
                ))), actions: [TextButton(onPressed: () => Navigator.pop(dialog), child: const Text('Fechar'))],
              )),
          )).toList()),
      ],
    ]);
  }

  String _cipaEventLabel(String kind) => const {
    'handover': 'Passagem de mandato', 'archive': 'Arquivado', 'restore': 'Restaurado',
    'support_requested': 'Apoio solicitado', 'support_completed': 'Apoio atendido',
    'action_status': 'Situação da ação registrada',
    'monthly_check': 'Roteiro mensal da CIPA',
    'observation': 'Situação observada',
  }[kind] ?? 'Registro de gestão';

  Widget _cipaCalendar() {
    final mandate = activeMandate;
    if (mandate == null) return const Card(child: ListTile(
      title: Text('Planejamento anual da CIPA'), subtitle: Text('Ative um mandato para acompanhar as reuniões.')));
    final now = DateTime.now();
    final start = DateTime(mandate.date.year, mandate.date.month, mandate.date.day);
    final end = mandate.dueDate ?? DateTime(now.year, 12, 31);
    const names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
    final months = <int>[];
    for (var m = 1; m <= 12; m++) {
      if (!DateTime(now.year, m + 1).isBefore(start) && !DateTime(now.year, m).isAfter(end) &&
          DateTime(now.year, m + 1).isAfter(start)) months.add(m);
    }
    return Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(
      crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('Planejamento anual da CIPA • ${now.year}',
          style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
        const SizedBox(height: 8),
        Wrap(spacing: 8, runSpacing: 8, children: months.map((m) {
          final label = CipaParticipationRules.meetingMonthLabel(mandateMeetings.where((r) =>
            r.date.year == now.year && r.date.month == m).map((r) => r.status), m < now.month);
          return Chip(label: Text('${names[m - 1]} • $label'));
        }).toList()),
        const Text('Agendada não significa realizada. Reuniões canceladas não contam como realizadas. '
          'O calendário mostra os registros do app; não certifica conformidade legal.'),
      ],
    )));
  }
}

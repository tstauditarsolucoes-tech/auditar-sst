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

  bool _cipaVisible(SstRecord r) => r.companyId == widget.companyId &&
      !_cipaIsEvent(r) && !_cipaRules.archived(r.id);

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
      Map<String, dynamic> details, {String? mandateId}) async {
    await CipaManagementService.saveRecord(
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
    if (busy) return;
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

  Widget _cipaWorkspaceTab() {
    final rules = _cipaRules;
    final pending = _cipaSortedActions(mandateActions.where((a) => a.status != 'Resolvida'));
    final query = _cipaResponsibleFilter.trim().toLowerCase();
    final visible = pending.where((a) => query.isEmpty ||
        '${a.payload['responsible'] ?? ''}'.toLowerCase().contains(query));
    final resolved = mandateActions.where((a) => a.status == 'Resolvida').toList();
    final archived = _cipaAllRecords.where((r) => rules.archived(r.id)).toList();
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
        OutlinedButton.icon(onPressed: busy || activeMandate == null ? null : () => _editMeeting(),
          icon: const Icon(Icons.event_outlined), label: const Text('Reunião e pauta')),
        if (!_cipaSimpleMode)
          OutlinedButton.icon(onPressed: busy || activeMandate == null ? null : _cipaHandover,
            icon: const Icon(Icons.swap_horiz), label: const Text('Passagem de mandato')),
      ]),
      if (nextMeeting != null) Card(child: ListTile(
        leading: const Icon(Icons.event), title: Text(nextMeeting!.title),
        subtitle: Text('Próxima reunião: ${_dateTime.format(nextMeeting!.date)}'),
        onTap: () => _editMeeting(nextMeeting))),
      const SizedBox(height: 12),
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
          )).toList()),
      ],
    ]);
  }

  String _cipaEventLabel(String kind) => const {
    'handover': 'Passagem de mandato', 'archive': 'Arquivado', 'restore': 'Restaurado',
    'support_requested': 'Apoio solicitado', 'support_completed': 'Apoio atendido',
    'action_status': 'Situação da ação registrada',
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

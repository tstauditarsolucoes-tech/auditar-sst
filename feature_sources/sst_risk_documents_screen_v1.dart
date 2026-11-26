import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:printing/printing.dart';

import '../database.dart';
import '../models.dart';
import '../services/auth_service.dart';
import '../services/sst_risk_documents_models.dart';
import '../services/sst_risk_documents_pdf.dart';
import '../services/sst_activity_guide_models.dart';
import '../services/sst_document_signature_models.dart';
import 'sst_document_signature_panel.dart';
import 'sst_activity_guide_screen.dart';
import 'sst_pet_nr33_screen.dart';

/// APR, PT, AR e PET NR-33 na empresa atual, sem autorizar trabalho.
class SstRiskDocsHomeScreen extends StatelessWidget {
  const SstRiskDocsHomeScreen({super.key, required this.company});
  final Company company;

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('APR, PT, AR e PET')),
    body: SafeArea(child: ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(company.name, style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 12),
        const Text('Escolha o tipo de documento. Salve o rascunho '
            'por empresa e usuário e gere um PDF marcado como minuta. '
            'A PT não libera trabalho pelo simples preenchimento.'),
        Card(child: ListTile(
          leading: const Icon(Icons.auto_awesome_outlined),
          title: const Text('Assistente passo a passo',
              style: TextStyle(fontWeight: FontWeight.bold)),
          subtitle: const Text('Escolha uma atividade, consulte os perigos '
              'e reaproveite os dados em APR, AR, PT ou PET.'),
          trailing: const Icon(Icons.chevron_right),
          enabled: AuthService.canAccessCompany(company.id),
          onTap: () => Navigator.of(context).push(
            MaterialPageRoute<void>(builder: (_) =>
              SstActivityGuideScreen(company: company))),
        )),
        const SizedBox(height: 10),
        for (final kind in SstRiskDocKind.values)
          Card(child: ListTile(
            leading: Icon(kind == SstRiskDocKind.pt
                ? Icons.assignment_turned_in_outlined
                : Icons.fact_check_outlined),
            title: Text(kind.title),
            subtitle: Text(kind.subtitle),
            trailing: const Icon(Icons.chevron_right),
            enabled: AuthService.canAccessCompany(company.id),
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute<void>(builder: (_) =>
                SstRiskDocEditorScreen(company: company, kind: kind))),
          )),
        Card(child: ListTile(
          leading: const Icon(Icons.warning_amber_outlined),
          title: const Text('PET - Permissão de Entrada e Trabalho',
              style: TextStyle(fontWeight: FontWeight.bold)),
          subtitle: const Text('Espaço confinado NR-33: equipe, medições, '
              'vigia, controles e plano de resgate; somente minuta.'),
          trailing: const Icon(Icons.chevron_right),
          enabled: AuthService.canAccessCompany(company.id),
          onTap: () => Navigator.of(context).push(
            MaterialPageRoute<void>(builder: (_) =>
              SstPetNr33Screen(company: company))),
        )),
        const SizedBox(height: 10),
        const Text('APR e AR são registros de análise. PT é uma '
            'autorização de trabalho que exige procedimento, '
            'aprovação e condições vigentes. Para espaço confinado '
            'é necessária PET específica da NR-33, não substituída '
            'por esta minuta genérica.',
          style: TextStyle(fontSize: 12)),
      ],
    )),
  );
}

class SstRiskDocEditorScreen extends StatefulWidget {
  const SstRiskDocEditorScreen({
    super.key, required this.company, required this.kind,
    this.initialPlan,
  });
  final Company company;
  final SstRiskDocKind kind;
  final SstActivityPlan? initialPlan;
  @override
  State<SstRiskDocEditorScreen> createState() => _SstRiskDocEditorScreenState();
}

class _SstRiskDocEditorScreenState extends State<SstRiskDocEditorScreen> {
  final SstRiskDocStore store = SstRiskDocStore(
    read: AppDatabase.instance.getSetting,
    write: AppDatabase.instance.setSetting,
  );
  final SstHandwrittenSignatureStore signatureStore =
      SstHandwrittenSignatureStore(
    read: AppDatabase.instance.getSetting,
    write: AppDatabase.instance.setSetting,
  );
  final SstActivityPlanStore activityStore = SstActivityPlanStore(
    read: AppDatabase.instance.getSetting,
    write: AppDatabase.instance.setSetting,
  );
  SstRiskDocDraft? draft;
  String? userId;
  String? error;
  bool loading = true;
  bool saveError = false;
  int pendingCount = 0;
  bool exporting = false;
  bool archiving = false;
  Future<void> pending = Future<void>.value();
  List<String> versions = const [];

  bool get authorized => userId != null &&
      userId == AppDatabase.activeUserId.toString() &&
      AuthService.canAccessCompany(widget.company.id);
  bool get canEdit => authorized && !archiving && !exporting && !saveError;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    if (!AuthService.canAccessCompany(widget.company.id)) {
      setState(() { loading = false; error = 'Sem acesso à empresa'; });
      return;
    }
    final uid = AppDatabase.activeUserId.toString();
    try {
      final current = await store.load(uid, widget.company.id, widget.kind);
      final ids = await store.listArchives(uid, widget.company.id, widget.kind);
      if (!mounted || uid != AppDatabase.activeUserId.toString()) return;
      setState(() {
        userId = uid;
        draft = current;
        versions = ids;
        error = null;
        loading = false;
      });
      if (widget.initialPlan != null) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (mounted) _importPlan(incoming: widget.initialPlan);
        });
      }
    } catch (_) {
      if (mounted) setState(() {
        loading = false;
        error = 'Falha ao ler o rascunho ou histórico. '
            'Nenhum registro foi sobrescrito.';
      });
    }
  }

  void _update(SstRiskDocDraft next) {
    if (!canEdit || next.companyId != widget.company.id ||
        next.kind != widget.kind) return;
    final uid = userId!;
    setState(() {
      draft = next;
      pendingCount++;
      error = null;
    });
    pending = pending.then((_) async {
      if (uid != AppDatabase.activeUserId.toString() ||
          !AuthService.canAccessCompany(widget.company.id)) {
        throw StateError('Acesso ou empresa alterados');
      }
      await store.save(uid, widget.company.id, next);
    }).catchError((_) {
      if (mounted) setState(() {
        saveError = true;
        error = 'Não foi possível salvar. '
            'Não feche até conferir os dados.';
      });
    }).whenComplete(() {
      if (mounted) setState(() => pendingCount--);
    });
  }

  /// Reaproveitar identificação e sugestões não verificadas somente
  /// depois de confirmação humana. Nunca copiar PT aprovada ou controles.
  Future<void> _importPlan({SstActivityPlan? incoming}) async {
    if (!canEdit || pendingCount > 0 || draft == null) return;
    final uid = userId!;
    SstActivityPlan? plan = incoming;
    if (plan == null) {
      try {
        plan = await activityStore.load(uid, widget.company.id);
      } catch (_) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Atividade compartilhada não pôde '
              'ser carregada. Nenhum dado foi substituído.')));
        return;
      }
    }
    if (!mounted || !canEdit ||
        plan == null || !plan.valid ||
        plan.userId != uid || plan.companyId != widget.company.id) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Não há atividade salva '
            'para esta empresa e conta.')));
      return;
    }
    final selected = plan;
    final yes = await showDialog<bool>(
      context: context,
      builder: (dialog) => AlertDialog(
        title: const Text('Importar dados da atividade?'),
        content: Text(
          'Atividade: ' + selected.activity +
          '\nLocal: ' + selected.sector +
          '\n\nSomente campos vazios serão preenchidos. '
          'Se este documento ainda não tiver etapas, serão adicionadas '
          'sugestões educativas marcadas COMO NÃO CONFERIDAS. '
          'É necessário abrir cada etapa, verificar as informações '
          'e indicar o responsável antes de gerar uma minuta PDF. '
          'Nenhuma PT será autorizada.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialog, false),
            child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(dialog, true),
            child: const Text('Importar para revisar')),
        ],
      ),
    );
    if (yes != true || !mounted || !canEdit ||
        uid != AppDatabase.activeUserId.toString()) return;
    final current = draft!;
    final imported = <SstRiskDocItem>[];
    if (current.items.isEmpty) {
      for (final hint in selected.template.hints) {
        imported.add(SstRiskDocItem(
          id: SstRiskDocStore.newId(),
          step: hint.step, hazard: hint.hazard,
          consequence: hint.consequence,
          controls: hint.controlToVerify,
          owner: '',
          presetUnreviewed: true,
        ));
      }
    }
    if (current.activity.isNotEmpty && current.sector.isNotEmpty &&
        current.items.isNotEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Os campos já estão preenchidos. '
            'Nada foi sobrescrito.')));
      return;
    }
    _update(current.copyWith(
      activity: current.activity.isEmpty
          ? selected.activity : current.activity,
      sector: current.sector.isEmpty ? selected.sector : current.sector,
      items: current.items.isEmpty ? imported : current.items,
    ));
  }

  String _fieldValue(String field) {
    final d = draft!;
    switch (field) {
      case 'activity': return d.activity;
      case 'sector': return d.sector;
      case 'date': return d.date;
      case 'preparedBy': return d.preparedBy;
      case 'blockers': return d.blockers;
      case 'emergency': return d.emergency;
      case 'team': return d.team;
      case 'validUntil': return d.validUntil;
      case 'authorizer': return d.authorizer;
      case 'referenceAr': return d.referenceAr;
      default: return '';
    }
  }

  Future<void> _editField(String field, String label) async {
    if (!canEdit) return;
    final text = TextEditingController(text: _fieldValue(field));
    final value = await showDialog<String>(
      context: context,
      builder: (dialog) => StatefulBuilder(
        builder: (dialog, change) => AlertDialog(
          title: Text(label),
          content: SizedBox(width: 490, child: TextField(
            controller: text, maxLines: 4, maxLength: 2000,
            autofocus: true,
            onChanged: (_) => change(() {}),
            decoration: const InputDecoration(
              border: OutlineInputBorder(),
              helperText: 'Registre apenas informações conferidas',
            ),
          )),
          actions: [
            TextButton(onPressed: () => Navigator.pop(dialog),
                child: const Text('Cancelar')),
            FilledButton(
              onPressed: text.text.trim().isEmpty ? null :
                  () => Navigator.pop(dialog, text.text.trim()),
              child: const Text('Salvar'),
            ),
          ],
        ),
      ),
    );
    WidgetsBinding.instance.addPostFrameCallback((_) => text.dispose());
    if (value == null || !mounted || !canEdit) return;
    final current = draft!;
    switch (field) {
      case 'activity': _update(current.copyWith(activity: value)); break;
      case 'sector': _update(current.copyWith(sector: value)); break;
      case 'date': _update(current.copyWith(date: value)); break;
      case 'preparedBy': _update(current.copyWith(preparedBy: value)); break;
      case 'blockers': _update(current.copyWith(blockers: value)); break;
      case 'emergency': _update(current.copyWith(emergency: value)); break;
      case 'team': _update(current.copyWith(team: value)); break;
      case 'validUntil': _update(current.copyWith(validUntil: value)); break;
      case 'authorizer': _update(current.copyWith(authorizer: value)); break;
      case 'referenceAr': _update(current.copyWith(referenceAr: value)); break;
    }
  }

  Widget _field(String label, String key) => ListTile(
    contentPadding: EdgeInsets.zero,
    title: Text(label),
    subtitle: Text(_fieldValue(key).isEmpty
        ? 'Não informado (preenchimento necessário)'
        : _fieldValue(key)),
    trailing: const Icon(Icons.edit_note_outlined),
    enabled: canEdit,
    onTap: () => _editField(key, label),
  );

  Future<void> _editItem([SstRiskDocItem? before]) async {
    if (!canEdit) return;
    final item = before ?? SstRiskDocItem(id: SstRiskDocStore.newId());
    final step = TextEditingController(text: item.step);
    final hazard = TextEditingController(text: item.hazard);
    final consequence = TextEditingController(text: item.consequence);
    final controls = TextEditingController(text: item.controls);
    final owner = TextEditingController(text: item.owner);
    var prob = item.probability;
    var sev = item.severity;
    final result = await showDialog<SstRiskDocItem>(
      context: context,
      builder: (dialog) => StatefulBuilder(
        builder: (dialog, change) {
          final valid = [
            step, hazard, consequence, controls, owner,
          ].every((controller) => controller.text.trim().isNotEmpty);
          return AlertDialog(
            title: Text(before == null ? 'Adicionar etapa' : 'Editar etapa'),
            content: SizedBox(
              width: 560,
              child: SingleChildScrollView(child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  for (final field in <(String, TextEditingController)>[
                    ('Etapa ou cenário', step),
                    ('Perigo / condição perigosa', hazard),
                    ('Consequência possível', consequence),
                    ('Controles necessários', controls),
                    ('Responsável proposto', owner),
                  ])
                    Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: TextField(
                        controller: field.$2,
                        maxLines: field.$1 == 'Controles necessários' ? 4 : 2,
                        maxLength: 2200,
                        decoration: InputDecoration(
                          labelText: field.$1,
                          border: const OutlineInputBorder(),
                        ),
                        onChanged: (_) => change(() {}),
                      ),
                    ),
                  const Text('Escala ilustrativa. Não comprova aceitabilidade '
                      'do risco nem autorização da atividade.',
                      style: TextStyle(fontSize: 12)),
                  Row(children: [
                    Expanded(child: DropdownButtonFormField<int>(
                      value: prob,
                      decoration: const InputDecoration(
                        labelText: 'Probabilidade',
                      ),
                      items: List.generate(5, (i) => DropdownMenuItem(
                        value: i + 1, child: Text((i + 1).toString()),
                      )),
                      onChanged: (v) => change(() { prob = v ?? prob; }),
                    )),
                    const SizedBox(width: 12),
                    Expanded(child: DropdownButtonFormField<int>(
                      value: sev,
                      decoration: const InputDecoration(
                        labelText: 'Severidade',
                      ),
                      items: List.generate(5, (i) => DropdownMenuItem(
                        value: i + 1, child: Text((i + 1).toString()),
                      )),
                      onChanged: (v) => change(() { sev = v ?? sev; }),
                    )),
                  ]),
                ],
              )),
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(dialog),
                  child: const Text('Cancelar')),
              FilledButton(
                onPressed: !valid ? null : () => Navigator.pop(
                  dialog, item.copyWith(
                    step: step.text.trim(),
                    hazard: hazard.text.trim(),
                    consequence: consequence.text.trim(),
                    controls: controls.text.trim(),
                    owner: owner.text.trim(),
                    probability: prob, severity: sev,
                    presetUnreviewed: false,
                  ),
                ),
                child: const Text('Salvar etapa'),
              ),
            ],
          );
        },
      ),
    );
    WidgetsBinding.instance.addPostFrameCallback((_) {
      for (final c in [step, hazard, consequence, controls, owner]) {
        c.dispose();
      }
    });
    if (result == null || !mounted || !canEdit) return;
    final current = draft!;
    final updated = [...current.items];
    final index = updated.indexWhere((row) => row.id == result.id);
    if (index >= 0) {
      updated[index] = result;
    } else if (updated.length < 50) {
      updated.add(result);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Limite de 50 etapas por documento'),
      ));
      return;
    }
    _update(current.copyWith(items: updated));
  }

  Future<void> _removeItem(SstRiskDocItem item) async {
    if (!canEdit) return;
    final yes = await showDialog<bool>(context: context,
      builder: (dialog) => AlertDialog(
        title: const Text('Remover etapa deste rascunho?'),
        content: const Text('A etapa será retirada apenas do rascunho.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialog, false),
            child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(dialog, true),
            child: const Text('Remover')),
        ],
      ),
    );
    if (yes == true && mounted && canEdit) {
      final now = draft!;
      _update(now.copyWith(
        items: now.items.where((x) => x.id != item.id).toList()));
    }
  }

  Future<void> _export(SstRiskDocDraft value) async {
    if (!authorized || exporting || archiving || pendingCount > 0 ||
        saveError || !value.canExportDraft) return;
    setState(() => exporting = true);
    try {
      await pending;
      if (!authorized || saveError) throw StateError('Rascunho não salvo');
      final signatures = await signatureStore.validForDocument(
        user: userId!,
        company: widget.company.id,
        kind: 'risk_' + widget.kind.name,
        id: value.id,
        snapshot: sstDocumentFingerprint(value.toJson()),
      );
      if (!mounted || !authorized) return;
      final pdf = await SstRiskDocumentPdf.generate(
        companyName: widget.company.name,
        companyId: widget.company.id,
        draft: value,
        signatures: signatures,
      );
      if (!mounted || !authorized) return;
      await Printing.layoutPdf(
        onLayout: (_) => pdf,
        name: 'Auditar_' + widget.kind.name.toUpperCase() + '_MINUTA.pdf',
      );
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Não foi possível gerar a minuta PDF. '
            'Confira o preenchimento e o armazenamento.')));
    } finally {
      if (mounted) setState(() => exporting = false);
    }
  }

  Future<void> _archive() async {
    if (!canEdit || pendingCount > 0 || draft == null ||
        !draft!.canExportDraft) return;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialog) => AlertDialog(
        title: const Text('Arquivar e começar outro rascunho?'),
        content: const Text('A versão atual será preservada no histórico '
            'desta conta e empresa. O formulário será reiniciado. '
            'Nenhuma PT é aprovada por esta operação.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialog, false),
            child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(dialog, true),
            child: const Text('Arquivar minuta')),
        ],
      ),
    );
    if (confirmed != true || !mounted || !canEdit) return;
    setState(() => archiving = true);
    try {
      await pending;
      if (!authorized || saveError) throw StateError('Salvamento incompleto');
      final uid = userId!;
      final current = draft!;
      await store.archive(uid, widget.company.id, current);
      final fresh = store.fresh(widget.company.id, widget.kind);
      await store.save(uid, widget.company.id, fresh);
      final ids = await store.listArchives(
        uid, widget.company.id, widget.kind);
      if (mounted && authorized) setState(() {
        draft = fresh; versions = ids;
      });
    } catch (_) {
      if (mounted) setState(() {
        error = 'Falha ao arquivar. O rascunho foi mantido para conferência.';
      });
    } finally {
      if (mounted) setState(() => archiving = false);
    }
  }

  Future<void> _retrySave() async {
    if (!authorized || pendingCount > 0 || archiving || exporting ||
        draft == null) return;
    final snapshot = draft!;
    final uid = userId!;
    setState(() { error = null; pendingCount++; });
    try {
      await store.save(uid, widget.company.id, snapshot);
      if (!mounted || !authorized) return;
      setState(() { saveError = false; error = null; });
    } catch (_) {
      if (mounted) setState(() {
        saveError = true;
        error = 'Persistiu a falha no salvamento. '
            'Não saia antes de recuperar seu rascunho.';
      });
    } finally {
      if (mounted) setState(() { pendingCount--; });
    }
  }

  Future<void> _openArchive(String id) async {
    if (!authorized) return;
    try {
      final uid = userId!;
      final saved = await store.openArchive(
        uid, widget.company.id, widget.kind, id);
      if (!mounted || !authorized) return;
      await _export(saved);
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Versão arquivada indisponível')));
    }
  }

  @override
  Widget build(BuildContext context) {
    if (loading) return Scaffold(
      appBar: AppBar(title: Text(widget.kind.title)),
      body: const Center(child: CircularProgressIndicator()),
    );
    final value = draft;
    if (!authorized || value == null) return Scaffold(
      appBar: AppBar(title: Text(widget.kind.title)),
      body: Center(child: Text(error ?? 'Acesso não autorizado')),
    );
    return PopScope(
      canPop: pendingCount == 0 && !saveError && !exporting && !archiving,
      child: Scaffold(
        appBar: AppBar(title: Text(widget.kind.title)),
        body: SafeArea(child: Center(child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 780),
          child: ListView(padding: const EdgeInsets.all(14), children: [
            Text(widget.company.name,
              style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            Text(widget.kind.help),
            const SizedBox(height: 8),
            const Text('Documento em elaboração. Informações não '
                'verificadas devem permanecer como pendências. '
                'Nenhum PDF gerado aqui libera trabalho.',
                style: TextStyle(fontWeight: FontWeight.bold)),
            if (error != null) Padding(
              padding: const EdgeInsets.all(10), child: Text(error!,
                style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ),
            if (pendingCount > 0) const LinearProgressIndicator(),
            if (saveError)
              FilledButton.icon(
                onPressed: authorized && pendingCount == 0
                    ? _retrySave : null,
                icon: const Icon(Icons.save_outlined),
                label: const Text('Tentar salvar novamente'),
              ),
            Card(child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('1. Identificação',
                    style: Theme.of(context).textTheme.titleMedium),
                  OutlinedButton.icon(
                    onPressed: canEdit && pendingCount == 0
                        ? () => _importPlan() : null,
                    icon: const Icon(Icons.file_copy_outlined),
                    label: const Text('Reaproveitar atividade salva'),
                  ),
                  const Text('Só completa campos vazios. Sugestões '
                    'de perigos exigem revisão de cada etapa.',
                    style: TextStyle(fontSize: 12)),
                  _field('Atividade / tarefa', 'activity'),
                  _field('Local / setor', 'sector'),
                  _field('Data do registro', 'date'),
                  _field('Responsável pela elaboração', 'preparedBy'),
                  _field('Condições impeditivas e critérios de parada',
                      'blockers'),
                  _field('Emergência / resgate / comunicação', 'emergency'),
                  if (widget.kind == SstRiskDocKind.pt) ...[
                    const Divider(),
                    const Text('2. PT - verificação e autorização pendentes',
                        style: TextStyle(fontWeight: FontWeight.bold)),
                    _field('Equipe envolvida', 'team'),
                    _field('Validade proposta (data e hora)', 'validUntil'),
                    _field('Pessoa responsável por autorizar', 'authorizer'),
                    _field('Referência à AR/APR conferida', 'referenceAr'),
                    const Text('O nome informado não constitui assinatura '
                        'ou liberação. A PT deve ser emitida, aprovada, '
                        'revalidada e encerrada conforme procedimento '
                        'da empresa e NR aplicável.',
                        style: TextStyle(fontSize: 12)),
                  ],
                ],
              ),
            )),
            const SizedBox(height: 8),
            Card(child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(widget.kind == SstRiskDocKind.pt
                      ? '3. Conferência de perigos e controles'
                      : '2. Etapas, perigos e medidas preventivas',
                    style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  if (value.items.isEmpty)
                    const Text('Nenhuma etapa registrada ainda.'),
                  for (var i = 0; i < value.items.length; i++)
                    Card(child: ListTile(
                      title: Text((i + 1).toString() + '. ' +
                          value.items[i].step),
                      subtitle: Text(
                        (value.items[i].presetUnreviewed
                          ? 'SUGESTÃO NÃO CONFERIDA — abra e revise\n'
                          : '') +
                        'Perigo: ' + value.items[i].hazard +
                        '\nControle: ' + value.items[i].controls +
                        '\nResponsável: ' + value.items[i].owner +
                        '\nP x S ilustrativo: ' +
                        value.items[i].illustrativeScore.toString()),
                      isThreeLine: true,
                      trailing: PopupMenuButton<String>(
                        onSelected: (v) => v == 'edit'
                            ? _editItem(value.items[i])
                            : _removeItem(value.items[i]),
                        itemBuilder: (_) => const [
                          PopupMenuItem(value: 'edit', child: Text('Editar')),
                          PopupMenuItem(value: 'remove', child: Text('Remover')),
                        ],
                      ),
                      onTap: canEdit ? () => _editItem(value.items[i]) : null,
                    )),
                  FilledButton.icon(
                    onPressed: canEdit && value.items.length < 50
                        ? () => _editItem() : null,
                    icon: const Icon(Icons.add),
                    label: const Text('Adicionar etapa / perigo'),
                  ),
                  const SizedBox(height: 7),
                  const Text('Escala P x S de 1 a 5 é somente ilustrativa: '
                    'deve ser calibrada à metodologia aprovada pelo cliente.',
                    style: TextStyle(fontSize: 12)),
                ],
              ),
            )),
            const SizedBox(height: 10),
            SstDocumentSignaturePanel(
              key: ValueKey('risk-sign-' + value.id),
              companyId: widget.company.id,
              userId: userId!,
              documentKind: 'risk_' + widget.kind.name,
              documentId: value.id,
              snapshot: sstDocumentFingerprint(value.toJson()),
              roles: widget.kind == SstRiskDocKind.pt
                  ? const {
                      'author': 'Elaborador — ciência e revisão',
                      'reviewer': 'Responsável pela conferência — ciência',
                    }
                  : const {
                      'author': 'Elaborador — ciência e revisão',
                      'reviewer': 'Responsável pela revisão técnica — ciência',
                    },
              enabled: canEdit && pendingCount == 0 &&
                  value.canExportDraft,
            ),
            FilledButton.icon(
              onPressed: canEdit && pendingCount == 0 &&
                  value.canExportDraft ? () => _export(value) : null,
              icon: const Icon(Icons.picture_as_pdf_outlined),
              label: const Text('Gerar PDF - MINUTA para conferência'),
            ),
            if (!value.canExportDraft)
              const Text('Para gerar minuta: preencha identificação, '
                'condições impeditivas, emergência e ao menos uma etapa '
                'com perigo, consequência, controles e responsável. '
                'Na PT, preencha equipe, validade proposta, '
                'responsável pela autorização e referência à AR/APR.'),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: canEdit && pendingCount == 0 &&
                  value.canExportDraft ? _archive : null,
              icon: const Icon(Icons.inventory_2_outlined),
              label: const Text('Arquivar versão e iniciar novo rascunho'),
            ),
            if (versions.isNotEmpty) ...[
              const Divider(),
              Text('Versões arquivadas (minutas)',
                style: Theme.of(context).textTheme.titleMedium),
              for (final id in versions)
                ListTile(
                  title: Text('Documento ' + id),
                  subtitle: const Text('Arquivo local - não autorizado'),
                  trailing: const Icon(Icons.picture_as_pdf_outlined),
                  onTap: () => _openArchive(id),
                ),
            ],
          ]),
        ))),
      ),
    );
  }
}

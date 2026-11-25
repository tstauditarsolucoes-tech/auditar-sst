import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:printing/printing.dart';

import '../database.dart';
import '../models.dart';
import '../services/auth_service.dart';
import '../services/sst_pet_nr33_models.dart';
import '../services/sst_pet_nr33_pdf.dart';
import '../services/sst_activity_guide_models.dart';
import '../services/sst_document_signature_models.dart';
import 'sst_document_signature_panel.dart';

/// Assistente de PET NR-33: somente MINUTAS e conferências, sem permitir entrada.
class SstPetNr33Screen extends StatefulWidget {
  const SstPetNr33Screen({
    super.key, required this.company, this.initialPlan,
  });
  final Company company;
  final SstActivityPlan? initialPlan;

  @override
  State<SstPetNr33Screen> createState() => _SstPetNr33ScreenState();
}

class _SstPetNr33ScreenState extends State<SstPetNr33Screen> {
  final SstPetStore store = SstPetStore(
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
  SstPetDraft? draft;
  String? ownerUser;
  String? error;
  List<String> archives = const [];
  bool loading = true;
  bool saveFailed = false;
  bool exporting = false;
  bool archiving = false;
  int pendingCount = 0;
  Future<void> pending = Future<void>.value();

  bool get authorized => ownerUser != null &&
      ownerUser == AppDatabase.activeUserId.toString() &&
      AuthService.canAccessCompany(widget.company.id);
  bool get canEdit => authorized && !saveFailed &&
      !exporting && !archiving && pendingCount == 0;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    if (!AuthService.canAccessCompany(widget.company.id)) {
      setState(() { loading = false; error = 'Sem acesso à empresa.'; });
      return;
    }
    final uid = AppDatabase.activeUserId.toString();
    try {
      final value = await store.load(uid, widget.company.id);
      final history = await store.list(uid, widget.company.id);
      if (!mounted || uid != AppDatabase.activeUserId.toString()) return;
      setState(() {
        draft = value;
        ownerUser = uid;
        archives = history;
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
        error = 'Não foi possível abrir o rascunho ou o histórico. '
            'Nenhum documento antigo foi substituído.';
      });
    }
  }

  void _update(SstPetDraft next) {
    if (!canEdit || next.userId != ownerUser ||
        next.companyId != widget.company.id) return;
    final uid = ownerUser!;
    setState(() {
      draft = next;
      error = null;
      pendingCount++;
    });
    pending = pending.then((_) async {
      if (uid != AppDatabase.activeUserId.toString() ||
          !AuthService.canAccessCompany(widget.company.id)) {
        throw StateError('Conta ou empresa alterada');
      }
      await store.save(next);
    }).catchError((_) {
      if (mounted) setState(() {
        saveFailed = true;
        error = 'Falha ao salvar. Não feche a PET sem conferir '
            'o salvamento; tente novamente.';
      });
    }).whenComplete(() {
      if (mounted) setState(() => pendingCount--);
    });
  }

  Future<void> _retrySave() async {
    if (!authorized || draft == null || pendingCount > 0 ||
        exporting || archiving) return;
    final snapshot = draft!;
    setState(() { pendingCount++; error = null; });
    try {
      await store.save(snapshot);
      if (mounted && authorized) setState(() {
        saveFailed = false;
        error = null;
      });
    } catch (_) {
      if (mounted) setState(() {
        saveFailed = true;
        error = 'Não foi possível salvar o rascunho PET.';
      });
    } finally {
      if (mounted) setState(() => pendingCount--);
    }
  }

  /// Importa APENAS identificação, nunca dados críticos da PET:
  /// não copiar atmosfera, vigia, supervisor, resgate ou autorização.
  Future<void> _importPlan({SstActivityPlan? incoming}) async {
    if (!canEdit || draft == null) return;
    final uid = ownerUser!;
    SstActivityPlan? plan = incoming;
    if (plan == null) {
      try {
        plan = await activityStore.load(uid, widget.company.id);
      } catch (_) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Atividade não pôde ser carregada.')));
        return;
      }
    }
    if (!mounted || !canEdit || plan == null || !plan.valid ||
        plan.userId != uid || plan.companyId != widget.company.id) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Nenhuma atividade disponível '
            'para esta conta e empresa.')));
      return;
    }
    final selected = plan;
    final accepted = await showDialog<bool>(
      context: context,
      builder: (dialog) => AlertDialog(
        title: const Text('Reaproveitar local e atividade na PET?'),
        content: Text('Atividade: ' + selected.activity +
          '\nLocal: ' + selected.sector +
          '\n\nSomente esses dois campos vazios serão preenchidos. '
          'Vigia, supervisor, medição de gases, equipe, resgate, '
          'controles e horário de entrada continuarão pendentes. '
          'Isto NÃO emite ou autoriza a PET.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialog, false),
            child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(dialog, true),
            child: const Text('Importar identificação')),
        ],
      ),
    );
    if (accepted != true || !mounted || !canEdit ||
        uid != AppDatabase.activeUserId.toString()) return;
    final current = draft!;
    var next = current;
    if (current.value('activity').isEmpty) {
      next = next.withValue('activity', selected.activity);
    }
    if (current.value('location').isEmpty) {
      next = next.withValue('location', selected.sector);
    }
    if (identical(next, current)) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Atividade e local já preenchidos. '
            'Nenhum dado foi sobrescrito.')));
      return;
    }
    _update(next);
  }

  Future<String?> _textDialog({
    required String title, required String value,
    required String helper, int max = 2400, bool numeric = false,
  }) async {
    final controller = TextEditingController(text: value);
    final result = await showDialog<String>(
      context: context,
      builder: (dialog) => StatefulBuilder(
        builder: (dialog, refresh) => AlertDialog(
          title: Text(title),
          content: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 540),
            child: SingleChildScrollView(child: TextField(
              controller: controller,
              maxLines: numeric ? 1 : 5,
              maxLength: max,
              keyboardType: numeric
                  ? const TextInputType.numberWithOptions(decimal: true)
                  : TextInputType.multiline,
              autofocus: true,
              onChanged: (_) => refresh(() {}),
              decoration: InputDecoration(
                labelText: helper, border: const OutlineInputBorder(),
              ),
            )),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialog),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: controller.text.trim().isEmpty ? null : () =>
                  Navigator.pop(dialog, controller.text.trim()),
              child: const Text('Salvar informação'),
            ),
          ],
        ),
      ),
    );
    WidgetsBinding.instance.addPostFrameCallback((_) => controller.dispose());
    return result;
  }

  Future<void> _editField(PetField field) async {
    if (!canEdit) return;
    final before = draft!;
    final result = await _textDialog(
      title: field.label,
      value: before.value(field.key),
      helper: 'Registrar o que foi realmente verificado ou informado',
      numeric: field.key == 'oxygen' || field.key == 'lel',
      max: field.key == 'oxygen' || field.key == 'lel' ? 30 : 2400,
    );
    if (result == null || !mounted || !canEdit || !identical(draft, before)) {
      return;
    }
    if (field.key == 'oxygen' || field.key == 'lel') {
      final parsed = double.tryParse(result.replaceAll(',', '.'));
      if (parsed == null || !parsed.isFinite ||
          parsed < 0 || parsed > 100) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Informe leitura numérica entre 0 e 100. '
              'O aplicativo não valida a segurança atmosférica.'),
        ));
        return;
      }
    }
    _update(before.withValue(field.key, result));
  }

  /// Leituras são digitadas manualmente, com unidade e fonte explícitas.
  /// Nenhuma faixa numérica deve ser convertida em "entrada liberada".
  Future<void> _addAtmosphereReading() async {
    if (!canEdit || draft == null || draft!.readings.length >= 30) return;
    final before = draft!;
    final inputs = <String, TextEditingController>{
      'dateTime': TextEditingController(),
      'point': TextEditingController(),
      'oxygen': TextEditingController(),
      'lel': TextEditingController(),
      'toxic': TextEditingController(),
      'detector': TextEditingController(),
      'measuredBy': TextEditingController(),
    };
    final labels = <String, String>{
      'dateTime': 'Data e hora reais da leitura',
      'point': 'Ponto/local da medição',
      'oxygen': 'O₂ medido (% vol.)',
      'lel': 'Inflamáveis (% LIE) medido',
      'toxic': 'Agentes tóxicos medidos (valor e unidade)',
      'detector': 'Detector, identificação e testes realizados',
      'measuredBy': 'Nome e função de quem mediu',
    };
    SstPetAtmosphereReading? create() {
      final value = SstPetAtmosphereReading(
        id: SstPetStore.newId(),
        dateTime: inputs['dateTime']!.text.trim(),
        point: inputs['point']!.text.trim(),
        oxygen: inputs['oxygen']!.text.trim(),
        lel: inputs['lel']!.text.trim(),
        toxic: inputs['toxic']!.text.trim(),
        detector: inputs['detector']!.text.trim(),
        measuredBy: inputs['measuredBy']!.text.trim(),
      );
      return value.complete ? value : null;
    }
    final reading = await showDialog<SstPetAtmosphereReading>(
      context: context,
      builder: (dialog) => StatefulBuilder(
        builder: (dialog, refresh) => AlertDialog(
          title: const Text('Registrar leitura atmosférica'),
          content: SizedBox(width: 540,
            child: SingleChildScrollView(child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text('Transcreva valores realmente medidos, '
                    'com hora e responsável. O app NÃO interpreta '
                    'limites de segurança nem autoriza entrada.'),
                const SizedBox(height: 8),
                for (final key in labels.keys)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: TextField(
                      controller: inputs[key],
                      maxLines: 1,
                      maxLength: key == 'toxic' ? 500 : 250,
                      keyboardType: (key == 'oxygen' || key == 'lel')
                          ? const TextInputType.numberWithOptions(decimal: true)
                          : TextInputType.text,
                      decoration: InputDecoration(
                        labelText: labels[key],
                        border: const OutlineInputBorder(),
                      ),
                      onChanged: (_) => refresh(() {}),
                    ),
                  ),
              ],
            )),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(dialog),
              child: const Text('Cancelar')),
            FilledButton(
              onPressed: create() == null ? null :
                () => Navigator.pop(dialog, create()),
              child: const Text('Registrar leitura informada'),
            ),
          ],
        ),
      ),
    );
    WidgetsBinding.instance.addPostFrameCallback((_) {
      for (final controller in inputs.values) {
        controller.dispose();
      }
    });
    if (reading == null || !mounted || !canEdit ||
        !identical(draft, before)) return;
    _update(before.withReading(reading));
  }

  Future<void> _removeAtmosphereReading(String id) async {
    if (!canEdit) return;
    final accepted = await showDialog<bool>(
      context: context,
      builder: (dialog) => AlertDialog(
        title: const Text('Retirar esta leitura da minuta?'),
        content: const Text('O registro será retirado somente do '
            'rascunho ativo. Não altera versões já arquivadas.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialog, false),
            child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(dialog, true),
            child: const Text('Retirar leitura')),
        ],
      ),
    );
    if (accepted == true && mounted && canEdit) {
      _update(draft!.withoutReading(id));
    }
  }

  Future<void> _editCheckNote(PetCheck check) async {
    if (!canEdit) return;
    final before = draft!;
    final result = await _textDialog(
      title: 'Justificativa / observação: ' + check.label,
      value: before.note(check.key),
      helper: 'Fonte, justificativa ou pendência encontrada',
      max: 500,
    );
    if (result == null || !mounted || !canEdit ||
        !identical(draft, before)) return;
    _update(before.withCheck(
      check.key, before.status(check.key), note: result,
    ));
  }

  Future<void> _export(SstPetDraft source) async {
    if (!authorized || exporting || archiving || pendingCount > 0 ||
        saveFailed || !source.readyForReviewPdf) return;
    setState(() => exporting = true);
    try {
      await pending;
      if (!authorized || saveFailed) {
        throw StateError('Verifique o salvamento local');
      }
      final signatures = await signatureStore.validForDocument(
        user: ownerUser!,
        company: widget.company.id,
        kind: 'pet_nr33',
        id: source.id,
        snapshot: jsonEncode(source.toJson()),
      );
      if (!mounted || !authorized) return;
      final bytes = await SstPetNr33Pdf.generate(
        companyName: widget.company.name,
        companyId: widget.company.id,
        userId: ownerUser!,
        draft: source,
        signatures: signatures,
      );
      if (!mounted || !authorized) return;
      await Printing.layoutPdf(onLayout: (_) => bytes,
        name: 'Auditar_PET_NR33_MINUTA_NAO_AUTORIZADA.pdf');
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Não foi possível gerar o PDF '
            'da minuta PET. Confira os campos e os dados locais.')));
    } finally {
      if (mounted) setState(() => exporting = false);
    }
  }

  Future<void> _archive() async {
    if (!canEdit || draft == null || !draft!.readyForReviewPdf) return;
    final yes = await showDialog<bool>(
      context: context,
      builder: (dialog) => AlertDialog(
        title: const Text('Arquivar minuta e iniciar outra?'),
        content: const Text('A minuta atual será guardada no histórico '
            'local da conta e empresa. Arquivar não equivale a emitir PET. '
            'Uma nova PET real depende das verificações e autorizações '
            'previstas pela NR-33.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialog, false),
            child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(dialog, true),
            child: const Text('Arquivar minuta')),
        ],
      ),
    );
    if (yes != true || !mounted || !canEdit) return;
    setState(() => archiving = true);
    try {
      await pending;
      if (!authorized || saveFailed) throw StateError('Salvamento pendente');
      final snapshot = draft!;
      await store.archive(snapshot);
      final fresh = store.fresh(ownerUser!, widget.company.id);
      await store.save(fresh);
      final list = await store.list(ownerUser!, widget.company.id);
      if (mounted && authorized) setState(() {
        draft = fresh; archives = list; error = null;
      });
    } catch (_) {
      if (mounted) setState(() {
        error = 'Não foi possível arquivar. O rascunho foi preservado; '
            'confira o histórico antes de repetir a ação.';
      });
    } finally {
      if (mounted) setState(() => archiving = false);
    }
  }

  Future<void> _openArchive(String id) async {
    if (!authorized) return;
    try {
      final archived = await store.open(ownerUser!, widget.company.id, id);
      if (!mounted || !authorized) return;
      await _export(archived);
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Minuta arquivada não encontrada.')));
    }
  }

  Widget _field(PetField field) => ListTile(
    contentPadding: EdgeInsets.zero,
    title: Text(field.label),
    subtitle: Text(draft!.value(field.key).isEmpty
        ? 'Pendente de informação'
        : draft!.value(field.key),
      maxLines: 4,
      overflow: TextOverflow.ellipsis),
    trailing: const Icon(Icons.edit_outlined),
    enabled: canEdit,
    onTap: () => _editField(field),
  );

  Widget _check(PetCheck item) => Card(
    child: Padding(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(item.label, style: const TextStyle(
              fontWeight: FontWeight.w600)),
          DropdownButton<PetCheckStatus>(
            isExpanded: true,
            value: draft!.status(item.key),
            items: [
              for (final status in PetCheckStatus.values)
                DropdownMenuItem(value: status, child: Text(status.label)),
            ],
            onChanged: canEdit ? (status) {
              if (status != null) {
                _update(draft!.withCheck(item.key, status));
              }
            } : null,
          ),
          if (draft!.status(item.key) == PetCheckStatus.reportedNo)
            const Text('Pendência informada: não autoriza entrada.',
              style: TextStyle(color: Colors.red)),
          if (draft!.status(item.key) == PetCheckStatus.notApplicable &&
              draft!.note(item.key).isEmpty)
            const Text('Justificativa obrigatória para não aplicável.'),
          if (draft!.note(item.key).isNotEmpty)
            Text('Observação: ' + draft!.note(item.key)),
          TextButton.icon(
            onPressed: canEdit ? () => _editCheckNote(item) : null,
            icon: const Icon(Icons.edit_note_outlined),
            label: const Text('Registrar justificativa/observação'),
          ),
        ],
      ),
    ),
  );

  @override
  Widget build(BuildContext context) {
    if (loading) return Scaffold(
      appBar: AppBar(title: const Text('PET - Espaço Confinado')),
      body: const Center(child: CircularProgressIndicator()),
    );
    if (!authorized || draft == null) return Scaffold(
      appBar: AppBar(title: const Text('PET - Espaço Confinado')),
      body: Center(child: Padding(
        padding: const EdgeInsets.all(20),
        child: Text(error ?? 'Acesso não autorizado a esta empresa.'),
      )),
    );
    final d = draft!;
    final groups = PetTemplate.fields.map((field) => field.group).toSet();
    return PopScope(
      canPop: pendingCount == 0 && !saveFailed &&
          !exporting && !archiving,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Confira o salvamento da PET '
              'antes de sair desta tela.')));
      },
      child: Scaffold(
        appBar: AppBar(title: const Text('PET - Espaço Confinado')),
        body: SafeArea(child: Center(child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 820),
          child: ListView(padding: const EdgeInsets.all(14), children: [
            Text(widget.company.name,
              style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 6),
            const Text('Permissão de Entrada e Trabalho | NR-33',
              style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Card(child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('MINUTA - ENTRADA NÃO AUTORIZADA',
                    style: TextStyle(
                      color: Colors.red,
                      fontWeight: FontWeight.bold, fontSize: 16)),
                  const SizedBox(height: 6),
                  const Text('Este módulo é um roteiro para preparar a PET. '
                    'Não faz medição da atmosfera, emissão legal, '
                    'assinatura certificada, acesso permanente pelo vigia '
                    'nem encerramento da permissão. A entrada depende da '
                    'PET válida emitida por pessoas competentes.'),
                  const SizedBox(height: 8),
                  const Text('Não substitui o procedimento da empresa. '
                    'Não entre no espaço para medir: a avaliação inicial '
                    'é realizada com o supervisor fora do espaço, '
                    'imediatamente antes da entrada.'),
                ],
              ),
            )),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: canEdit ? () => _importPlan() : null,
              icon: const Icon(Icons.file_copy_outlined),
              label: const Text('Reaproveitar só local e atividade'),
            ),
            Text('Campos essenciais: ' +
                d.completedRequired.toString() + '/' +
                d.requiredTotal.toString()),
            LinearProgressIndicator(value:
                d.completedRequired / d.requiredTotal),
            if (pendingCount > 0) const LinearProgressIndicator(),
            if (error != null) Padding(
              padding: const EdgeInsets.all(8),
              child: Text(error!, style: TextStyle(
                color: Theme.of(context).colorScheme.error)),
            ),
            if (saveFailed)
              FilledButton.icon(
                onPressed: authorized && pendingCount == 0
                    ? _retrySave : null,
                icon: const Icon(Icons.save_outlined),
                label: const Text('Tentar salvar rascunho novamente'),
              ),
            for (final group in groups)
              Card(child: ExpansionTile(
                key: ValueKey('pet-' + group),
                title: Text(group),
                initiallyExpanded: group.startsWith('1.'),
                childrenPadding: const EdgeInsets.symmetric(
                  horizontal: 14, vertical: 6),
                children: [
                  for (final field in PetTemplate.fields)
                    if (field.group == group) _field(field),
                  if (group.startsWith('5.')) ...[
                    const Padding(
                      padding: EdgeInsets.all(10),
                      child: Text(
                      'Apenas transcreva leituras reais do detector '
                      'com data/hora, instrumento e responsável. '
                      'Não presuma O₂ seguro por estar em uma faixa: '
                      'a causa de redução/enriquecimento deve ser '
                      'conhecida e controlada. Registre gases '
                      'tóxicos efetivamente avaliados e mantenha '
                      'monitoramento contínuo durante a entrada.',
                      style: TextStyle(fontSize: 12)),
                    ),
                    const Divider(),
                    const Text('Leituras atmosféricas complementares',
                        style: TextStyle(fontWeight: FontWeight.bold)),
                    const Text('Histórico manual; NÃO é um monitor '
                        'eletrônico contínuo nem libera a entrada.'),
                    for (final reading in d.readings)
                      ListTile(
                        title: Text(reading.dateTime + ' · ' + reading.point),
                        subtitle: Text('O₂: ' + reading.oxygen +
                          '% | Inflamáveis: ' + reading.lel +
                          '% LIE\nTóxicos: ' + reading.toxic +
                          '\nDetector: ' + reading.detector +
                          ' · Mediu: ' + reading.measuredBy),
                        trailing: IconButton(
                          icon: const Icon(Icons.remove_circle_outline),
                          tooltip: 'Retirar leitura do rascunho',
                          onPressed: canEdit ?
                            () => _removeAtmosphereReading(reading.id) : null,
                        ),
                      ),
                    OutlinedButton.icon(
                      onPressed: canEdit && d.readings.length < 30
                          ? _addAtmosphereReading : null,
                      icon: const Icon(Icons.add_chart_outlined),
                      label: const Text('Registrar outra leitura'),
                    ),
                  ],
                ],
              )),
            const SizedBox(height: 12),
            Text('8. Conferências antes da entrada (informadas)',
              style: Theme.of(context).textTheme.titleMedium),
            const Text('Marcar Sim não constitui aprovação. '
              'O supervisor e o vigia precisam confirmar em campo.',
              style: TextStyle(fontSize: 12)),
            for (final item in PetTemplate.checks)
              _check(item),
            const SizedBox(height: 10),
            if (d.criticalAlerts.isNotEmpty)
              Card(child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(children: [
                      Icon(Icons.report_problem_outlined, color: Colors.red),
                      SizedBox(width: 8),
                      Expanded(child: Text(
                        'ATENÇÃO: CONDIÇÕES CRÍTICAS A CONFERIR',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      )),
                    ]),
                    const SizedBox(height: 6),
                    for (final alert in d.criticalAlerts.take(12))
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 3),
                        child: Text('• ' + alert),
                      ),
                    const Text('A geração de uma minuta não é '
                      'autorização de entrada no espaço confinado.'),
                  ],
                ),
              )),
            if (d.pending.isNotEmpty)
              Card(child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Pendências do rascunho (' +
                        d.pending.length.toString() + ')',
                      style: const TextStyle(fontWeight: FontWeight.bold)),
                    for (final item in d.pending.take(10))
                      Text('• ' + item),
                    if (d.pending.length > 10)
                      const Text('Há outras pendências. '
                        'Revise os campos antes de exportar.'),
                  ],
                ),
              )),
            SstDocumentSignaturePanel(
              key: ValueKey('pet-sign-' + d.id),
              companyId: widget.company.id,
              userId: ownerUser!,
              documentKind: 'pet_nr33',
              documentId: d.id,
              snapshot: jsonEncode(d.toJson()),
              roles: const {
                'supervisor_ack': 'Supervisor de entrada — ciência',
                'attendant_ack': 'Vigia — ciência',
              },
              enabled: canEdit && d.readyForReviewPdf,
            ),
            const Text('Estas rubricas desenhadas NÃO são certificadas '
              'nem representam a assinatura válida de uma PET emitida. '
              'O app não libera entrada no espaço confinado.',
              style: TextStyle(fontSize: 12)),
            FilledButton.icon(
              onPressed: canEdit && d.readyForReviewPdf
                  ? () => _export(d) : null,
              icon: const Icon(Icons.picture_as_pdf_outlined),
              label: const Text('Gerar PDF - MINUTA NÃO AUTORIZADA'),
            ),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: canEdit && d.readyForReviewPdf ? _archive : null,
              icon: const Icon(Icons.inventory_2_outlined),
              label: const Text('Arquivar minuta e iniciar outra'),
            ),
            if (archives.isNotEmpty) ...[
              const Divider(),
              Text('Histórico local de minutas',
                style: Theme.of(context).textTheme.titleMedium),
              for (final id in archives)
                ListTile(
                  title: Text('Minuta ' + id),
                  subtitle: const Text('Nunca emitida/autorizada pelo app'),
                  trailing: const Icon(Icons.picture_as_pdf_outlined),
                  onTap: authorized ? () => _openArchive(id) : null,
                ),
            ],
            const SizedBox(height: 18),
            const Text('A PET emitida deve seguir a NR-33, '
              'com rastreabilidade, assinatura dos supervisores e vigias, '
              'acesso permanente pelo vigia e arquivamento legal. '
              'O histórico local deste protótipo não satisfaz '
              'essas obrigações.',
              style: TextStyle(fontSize: 12)),
          ]),
        ))),
      ),
    );
  }
}

import 'package:flutter/material.dart';

import '../database.dart';
import '../models.dart';
import '../services/auth_service.dart';
import '../services/sst_activity_guide_models.dart';
import '../services/sst_risk_documents_models.dart';
import 'sst_pet_nr33_screen.dart';
import 'sst_risk_documents_screen.dart';

/// Coleta uma vez a identificação da tarefa; controles são apenas perguntas.
/// Compartilhar dados NÃO cria autorizações ou evidências de implantação.
class SstActivityGuideScreen extends StatefulWidget {
  const SstActivityGuideScreen({super.key, required this.company});
  final Company company;

  @override
  State<SstActivityGuideScreen> createState() =>
      _SstActivityGuideScreenState();
}

class _SstActivityGuideScreenState extends State<SstActivityGuideScreen> {
  final store = SstActivityPlanStore(
    read: AppDatabase.instance.getSetting,
    write: AppDatabase.instance.setSetting,
  );
  final activity = TextEditingController();
  final sector = TextEditingController();
  String templateCode = 'altura';
  String? owner;
  String? error;
  bool loading = true, saving = false;

  SstActivityTemplate get template =>
      SstActivityTemplates.find(templateCode)!;
  bool get authorized => owner != null &&
      owner == AppDatabase.activeUserId.toString() &&
      AuthService.canAccessCompany(widget.company.id);
  bool get valid => authorized && !saving &&
      activity.text.trim().isNotEmpty &&
      sector.text.trim().isNotEmpty &&
      activity.text.length <= 220 && sector.text.length <= 220;

  @override
  void initState() {
    super.initState();
    activity.text = template.defaultActivity;
    _load();
  }

  Future<void> _load() async {
    if (!AuthService.canAccessCompany(widget.company.id)) {
      if (mounted) setState(() {
        loading = false;
        error = 'Sem permissão para esta empresa';
      });
      return;
    }
    final uid = AppDatabase.activeUserId.toString();
    try {
      final saved = await store.load(uid, widget.company.id);
      if (!mounted || uid != AppDatabase.activeUserId.toString()) return;
      setState(() {
        owner = uid;
        if (saved != null) {
          templateCode = saved.templateCode;
          activity.text = saved.activity;
          sector.text = saved.sector;
        }
        loading = false;
      });
    } catch (_) {
      if (mounted) setState(() {
        loading = false;
        error = 'O plano anterior não pôde ser aberto. '
            'Nenhum registro existente foi modificado.';
      });
    }
  }

  @override
  void dispose() {
    activity.dispose();
    sector.dispose();
    super.dispose();
  }

  void _choose(String? code) {
    final next = code == null ? null : SstActivityTemplates.find(code);
    if (next == null || !authorized || saving) return;
    final previous = template.defaultActivity;
    setState(() {
      templateCode = next.code;
      if (activity.text.trim().isEmpty || activity.text == previous) {
        activity.text = next.defaultActivity;
      }
      error = null;
    });
  }

  Future<SstActivityPlan?> _save() async {
    if (!valid) return null;
    final uid = owner!;
    final plan = SstActivityPlan(
      userId: uid, companyId: widget.company.id,
      templateCode: templateCode,
      activity: activity.text.trim(), sector: sector.text.trim(),
      updatedAt: DateTime.now().toIso8601String(),
    );
    setState(() { saving = true; error = null; });
    try {
      if (!authorized || uid != AppDatabase.activeUserId.toString()) {
        throw StateError('Conta ou empresa alterada');
      }
      await store.save(plan);
      if (!mounted || !authorized) return null;
      return plan;
    } catch (_) {
      if (mounted) setState(() {
        error = 'Falha ao guardar os dados da atividade. '
            'A importação não foi iniciada.';
      });
      return null;
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  Future<void> _start(SstRiskDocKind? kind, {bool pet = false}) async {
    final plan = await _save();
    if (plan == null || !mounted || !authorized) return;
    await Navigator.of(context).push(MaterialPageRoute<void>(
      builder: (_) => pet
          ? SstPetNr33Screen(company: widget.company, initialPlan: plan)
          : SstRiskDocEditorScreen(
              company: widget.company, kind: kind!, initialPlan: plan),
    ));
  }

  @override
  Widget build(BuildContext context) {
    if (loading) return Scaffold(
      appBar: AppBar(title: const Text('Assistente de atividade')),
      body: const Center(child: CircularProgressIndicator()),
    );
    final t = template;
    return Scaffold(
      appBar: AppBar(title: const Text('Criar APR, PT, AR ou PET')),
      body: SafeArea(child: Center(child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 800),
        child: ListView(padding: const EdgeInsets.all(16), children: [
          Text(widget.company.name,
            style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 10),
          const Text('Uma atividade, vários documentos: informe os dados '
            'uma vez e escolha o formulário. Nenhum risco, medida '
            'implantada ou assinatura é confirmado automaticamente.'),
          const SizedBox(height: 14),
          Card(child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('1. Escolha a atividade',
                  style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  key: ValueKey('atividade-' + templateCode),
                  value: templateCode,
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                    labelText: 'Tipo de atividade',
                  ),
                  isExpanded: true,
                  items: [
                    for (final option in SstActivityTemplates.values)
                      DropdownMenuItem(
                        value: option.code, child: Text(option.title),
                      ),
                  ],
                  onChanged: authorized && !saving ? _choose : null,
                ),
              ],
            ),
          )),
          Card(child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('2. Identifique o serviço e o local',
                  style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 8),
                TextField(
                  controller: activity, maxLength: 220,
                  enabled: authorized && !saving,
                  onChanged: (_) => setState(() {}),
                  decoration: const InputDecoration(
                    labelText: 'Atividade real',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: sector, maxLength: 220,
                  enabled: authorized && !saving,
                  onChanged: (_) => setState(() {}),
                  decoration: const InputDecoration(
                    labelText: 'Setor / local',
                    border: OutlineInputBorder(),
                  ),
                ),
              ],
            ),
          )),
          Card(child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('3. Veja perigos e perguntas para confirmar',
                  style: Theme.of(context).textTheme.titleMedium),
                const Text('Ideias para investigação: não são fatos '
                  'observados nem controles comprovados.'),
                const SizedBox(height: 8),
                for (final risk in t.hints) ...[
                  ListTile(
                    leading: const Icon(Icons.warning_amber_outlined),
                    title: Text(risk.step + ': ' + risk.hazard),
                    subtitle: Text('Possível consequência: ' +
                      risk.consequence + '\nConferir: ' +
                      risk.controlToVerify),
                  ),
                ],
                const Divider(),
                for (final q in t.questions)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Row(crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(Icons.help_outline, size: 17),
                        const SizedBox(width: 7),
                        Expanded(child: Text(q)),
                      ],
                    ),
                  ),
              ],
            ),
          )),
          Card(child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text('4. Escolha qual documento elaborar',
                  style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 6),
                Text('Documentos a avaliar: ' + t.docs.join(', ')),
                const SizedBox(height: 9),
                FilledButton.icon(
                  onPressed: valid ? () => _start(SstRiskDocKind.apr) : null,
                  icon: const Icon(Icons.library_add_check_outlined),
                  label: const Text('Criar APR - rascunho guiado'),
                ),
                const SizedBox(height: 7),
                FilledButton.icon(
                  onPressed: valid ? () => _start(SstRiskDocKind.ar) : null,
                  icon: const Icon(Icons.fact_check_outlined),
                  label: const Text('Criar AR - rascunho guiado'),
                ),
                if (t.code != 'confinado')
                  Padding(
                    padding: const EdgeInsets.only(top: 7),
                    child: OutlinedButton.icon(
                      onPressed: valid ? () => _start(SstRiskDocKind.pt) : null,
                      icon: const Icon(Icons.description_outlined),
                      label: const Text('Preparar minuta de PT'),
                    ),
                  ),
                if (t.code == 'confinado' || t.code == 'forno')
                  Padding(
                    padding: const EdgeInsets.only(top: 7),
                    child: OutlinedButton.icon(
                      onPressed: valid ? () => _start(null, pet: true) : null,
                      icon: const Icon(Icons.warning_amber_outlined),
                      label: const Text('Preparar minuta de PET NR-33'),
                    ),
                  ),
                const SizedBox(height: 9),
                const Text('A PET aplica-se quando o local caracteriza '
                  'espaço confinado. Uma minuta não autoriza entrada. '
                  'PT requer procedimento e autorização válidos quando '
                  'exigida. Nenhum modelo substitui avaliação presencial.',
                  style: TextStyle(fontSize: 12)),
              ],
            ),
          )),
          if (error != null)
            Padding(
              padding: const EdgeInsets.all(10),
              child: Text(error!, style: TextStyle(
                color: Theme.of(context).colorScheme.error)),
            ),
          if (saving) const LinearProgressIndicator(),
        ]),
      ))),
    );
  }
}

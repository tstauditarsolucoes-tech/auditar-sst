#!/usr/bin/env python3
"""Auditar SST v3.26.0 — PGR como guia de trabalho e vistoria."""
from __future__ import annotations
import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"Marcador não encontrado: {label}")
    return text.replace(old, new, 1)


def patch_pgr_screen(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    marker = "  Widget _body() {"
    helpers = r'''  Set<String> get _sectorsFromPgr {
    final result = <String>{};
    for (final role in _roles) {
      final sectors = role['sectors'];
      if (sectors is! List) continue;
      for (final sector in sectors) {
        final value = '$sector'.trim();
        if (value.isNotEmpty) result.add(value);
      }
    }
    return result;
  }

  int get _riskCount {
    var count = 0;
    for (final role in _roles) {
      final risks = role['risks'];
      if (risks is List) count += risks.length;
    }
    return count;
  }

  int get _trainingSuggestionCount {
    var count = 0;
    for (final role in _roles) {
      count += _trainings(role).length;
    }
    return count;
  }

  List<String> get _rolesMissingInApp {
    final app = companyRoles
        .map((row) => AppDatabase.normalizeRoleKey('${row['name'] ?? ''}'))
        .where((value) => value.isNotEmpty)
        .toSet();
    return _roles
        .map((row) => '${row['role'] ?? ''}'.trim())
        .where((name) => name.isNotEmpty && !app.contains(AppDatabase.normalizeRoleKey(name)))
        .toList();
  }

  List<String> get _appRolesNotInPgr {
    final pgr = _roles
        .map((row) => AppDatabase.normalizeRoleKey('${row['role'] ?? ''}'))
        .where((value) => value.isNotEmpty)
        .toSet();
    return companyRoles
        .where((row) => (row['active'] as num?)?.toInt() != 0)
        .map((row) => '${row['name'] ?? ''}'.trim())
        .where((name) => name.isNotEmpty && !pgr.contains(AppDatabase.normalizeRoleKey(name)))
        .toList();
  }

  List<String> get _dataGaps {
    final rows = analysis?['dataGaps'];
    if (rows is! List) return const [];
    return rows.map((item) => '$item'.trim()).where((item) => item.isNotEmpty).toList();
  }

  Future<void> _runQuickTool(String title, String prompt) async {
    final doc = document;
    if (doc == null) return;
    setState(() => busy = true);
    try {
      final result = await PgrService.ask(widget.company, doc, prompt);
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: Row(children: [
            const Icon(Icons.auto_awesome_rounded),
            const SizedBox(width: 8),
            Expanded(child: Text(title)),
          ]),
          content: SizedBox(
            width: 680,
            child: SingleChildScrollView(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('${result['answer'] ?? ''}', style: const TextStyle(height: 1.4)),
                if (result['sourceHints'] is List && (result['sourceHints'] as List).isNotEmpty) ...[
                  const SizedBox(height: 14),
                  const Text('Onde conferir no PGR', style: TextStyle(fontWeight: FontWeight.w800)),
                  ...(result['sourceHints'] as List).take(8).map((item) => Padding(
                    padding: const EdgeInsets.only(top: 4), child: Text('• $item'))),
                ],
                if ('${result['limitations'] ?? ''}'.trim().isNotEmpty) ...[
                  const SizedBox(height: 10),
                  Text('Limitação: ${result['limitations']}', style: const TextStyle(fontSize: 12, color: Colors.black54)),
                ],
              ]),
            ),
          ),
          actions: [FilledButton(onPressed: () => Navigator.pop(context), child: const Text('Fechar'))],
        ),
      );
    } catch (e) {
      _message('$e', error: true);
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Widget _metric(String value, String label, IconData icon) {
    return Container(
      width: 150,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AuditarBrand.navySoft,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AuditarBrand.line),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Icon(icon, color: AuditarBrand.navy, size: 20),
        const SizedBox(height: 8),
        Text(value, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w900, color: AuditarBrand.navy)),
        Text(label, style: const TextStyle(fontSize: 11.5, color: Colors.black54)),
      ]),
    );
  }

'''
    text = replace_once(text, marker, helpers + marker, "helpers do PGR")

    old = """          const SizedBox(height: 12),
          Row(children: [
            const Expanded(child: Text('Cargos identificados', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: AuditarBrand.navy))),
"""
    new = """          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('O que o PGR está dizendo sobre esta empresa', style: TextStyle(fontWeight: FontWeight.w900, color: AuditarBrand.navy)),
                const SizedBox(height: 10),
                Wrap(spacing: 8, runSpacing: 8, children: [
                  _metric('${_sectorsFromPgr.length}', 'Setores', Icons.apartment_outlined),
                  _metric('${_roles.length}', 'Cargos / funções', Icons.badge_outlined),
                  _metric('$_riskCount', 'Riscos mapeados', Icons.warning_amber_rounded),
                  _metric('$_trainingSuggestionCount', 'Treinamentos sugeridos', Icons.school_outlined),
                ]),
                if (_dataGaps.isNotEmpty || '${analysis!['warning'] ?? ''}'.trim().isNotEmpty) ...[
                  const SizedBox(height: 12),
                  const Text('Pontos para conferir', style: TextStyle(fontWeight: FontWeight.w800)),
                  ..._dataGaps.take(6).map((item) => Padding(padding: const EdgeInsets.only(top: 4), child: Text('• $item'))),
                  if ('${analysis!['warning'] ?? ''}'.trim().isNotEmpty)
                    Padding(padding: const EdgeInsets.only(top: 6), child: Text('${analysis!['warning']}', style: const TextStyle(fontSize: 12, color: Colors.black54))),
                ],
              ]),
            ),
          ),
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('Ferramentas rápidas com o PGR', style: TextStyle(fontWeight: FontWeight.w900, color: AuditarBrand.navy)),
                const SizedBox(height: 5),
                const Text('A IA usa somente o PGR desta empresa como fonte para preparar o material.', style: TextStyle(fontSize: 12, color: Colors.black54)),
                const SizedBox(height: 10),
                Wrap(spacing: 8, runSpacing: 8, children: [
                  OutlinedButton.icon(
                    onPressed: busy ? null : () => _runQuickTool('Guia de vistoria', 'Crie um guia prático de vistoria SST baseado somente neste PGR. Liste setores e atividades prioritárias, riscos a observar em campo, medidas de proteção, EPC/EPI citados ou relacionados no documento, documentos ou registros a conferir e perguntas úteis aos trabalhadores. Não invente requisitos que não estejam sustentados pelo PGR.'),
                    icon: const Icon(Icons.fact_check_outlined), label: const Text('Guia de vistoria')),
                  OutlinedButton.icon(
                    onPressed: busy ? null : () => _runQuickTool('DDS baseado no PGR', 'Prepare um DDS curto e simples baseado somente nos principais riscos deste PGR. Use linguagem de trabalhador, destaque comportamentos seguros e não invente riscos que não estejam no documento.'),
                    icon: const Icon(Icons.record_voice_over_outlined), label: const Text('DDS')),
                  OutlinedButton.icon(
                    onPressed: busy ? null : () => _runQuickTool('Proteções e EPI', 'Resuma por cargo, função ou setor as medidas de proteção coletiva e os EPIs citados ou sustentados por este PGR. Quando o documento não indicar EPI específico, diga que não foi localizado em vez de inventar.'),
                    icon: const Icon(Icons.health_and_safety_outlined), label: const Text('EPI / proteções')),
                  OutlinedButton.icon(
                    onPressed: busy ? null : () => _runQuickTool('Rascunho de Ordem de Serviço', 'Prepare um rascunho técnico de pontos para uma Ordem de Serviço SST usando somente atividades, riscos e medidas preventivas encontradas neste PGR. Separe por cargo ou função quando possível e deixe claro o que precisa de conferência do Técnico.'),
                    icon: const Icon(Icons.description_outlined), label: const Text('Ordem de Serviço')),
                  OutlinedButton.icon(
                    onPressed: busy ? null : () => _runQuickTool('Resumo gerencial', 'Faça um resumo gerencial curto deste PGR: principais setores, atividades, riscos prioritários, medidas de controle relevantes e pontos que merecem acompanhamento pela gestão. Use somente informações do documento.'),
                    icon: const Icon(Icons.insights_outlined), label: const Text('Resumo gerencial')),
                ]),
              ]),
            ),
          ),
          const SizedBox(height: 12),
          if (_rolesMissingInApp.isNotEmpty || _appRolesNotInPgr.isNotEmpty)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Text('Conferência PGR × cadastro do app', style: TextStyle(fontWeight: FontWeight.w900, color: AuditarBrand.navy)),
                  const SizedBox(height: 6),
                  const Text('Diferenças não significam erro automaticamente. Servem para você conferir se RH, cargos e PGR estão alinhados.', style: TextStyle(fontSize: 12, color: Colors.black54)),
                  if (_rolesMissingInApp.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    Text('${_rolesMissingInApp.length} cargo(s) do PGR ainda não cadastrados no app', style: const TextStyle(fontWeight: FontWeight.w800)),
                    ..._rolesMissingInApp.take(8).map((name) => Padding(padding: const EdgeInsets.only(top: 3), child: Text('• $name'))),
                  ],
                  if (_appRolesNotInPgr.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    Text('${_appRolesNotInPgr.length} cargo(s) ativos do app não localizados na análise do PGR', style: const TextStyle(fontWeight: FontWeight.w800)),
                    ..._appRolesNotInPgr.take(8).map((name) => Padding(padding: const EdgeInsets.only(top: 3), child: Text('• $name'))),
                  ],
                ]),
              ),
            ),
          if (_rolesMissingInApp.isNotEmpty || _appRolesNotInPgr.isNotEmpty) const SizedBox(height: 12),
          Row(children: [
            const Expanded(child: Text('Cargos identificados', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: AuditarBrand.navy))),
"""
    text = replace_once(text, old, new, "painel inteligente do PGR")
    path.write_text(text, encoding="utf-8")


def patch_new_inspection(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "import 'dart:convert';" not in text:
        text = "import 'dart:convert';\n\n" + text
    if "import '../services/pgr_service.dart';" not in text:
        text = text.replace("import '../models.dart';\n", "import '../models.dart';\nimport '../services/pgr_service.dart';\n", 1)

    text = replace_once(
        text,
        "  String? selectedChecklistCategory;\n\n  final technicianName = TextEditingController();\n",
        "  String? selectedChecklistCategory;\n  Map<String, Object?>? pgrDocument;\n  Map<String, dynamic>? pgrAnalysis;\n  bool pgrGuideBusy = false;\n\n  final technicianName = TextEditingController();\n",
        "estado PGR da vistoria",
    )

    old = """      sites = [];
      sectors = [];
    });

    if (company == null) return;

    final results = await Future.wait([
      AppDatabase.instance.getWorkSites(company.id),
      AppDatabase.instance.getSectors(company.id),
    ]);

    if (!mounted) return;

    setState(() {
      sites = results[0] as List<WorkSite>;
      sectors = results[1] as List<Sector>;
    });
"""
    new = """      sites = [];
      sectors = [];
      pgrDocument = null;
      pgrAnalysis = null;
    });

    if (company == null) return;

    final results = await Future.wait([
      AppDatabase.instance.getWorkSites(company.id),
      AppDatabase.instance.getSectors(company.id),
      AppDatabase.instance.getPgrDocument(company.id),
    ]);

    Map<String, dynamic>? parsedPgr;
    final doc = results[2] as Map<String, Object?>?;
    final raw = '${doc?['analysis_json'] ?? ''}'.trim();
    if (raw.isNotEmpty) {
      try {
        final value = jsonDecode(raw);
        if (value is Map) parsedPgr = Map<String, dynamic>.from(value);
      } catch (_) {}
    }

    if (!mounted) return;

    setState(() {
      sites = results[0] as List<WorkSite>;
      sectors = results[1] as List<Sector>;
      pgrDocument = doc;
      pgrAnalysis = parsedPgr;
    });
"""
    text = replace_once(text, old, new, "carregamento PGR na nova vistoria")

    marker = "  List<String> get _suggestedChecklistCategories {\n"
    helpers = r'''  String get _pgrContextText {
    final rows = pgrAnalysis?['roles'];
    if (rows is! List) return '';
    final selectedName = (selectedSector?.name ?? '').trim().toLowerCase();
    final parts = <String>[];
    for (final raw in rows.whereType<Map>()) {
      final role = Map<String, dynamic>.from(raw);
      final sectorsRaw = role['sectors'];
      final roleSectors = sectorsRaw is List
          ? sectorsRaw.map((item) => '$item'.trim()).where((item) => item.isNotEmpty).toList()
          : <String>[];
      final matchesSector = selectedName.isEmpty ||
          roleSectors.isEmpty ||
          roleSectors.any((item) {
            final value = item.toLowerCase();
            return value.contains(selectedName) || selectedName.contains(value);
          });
      if (!matchesSector) continue;
      parts.add('${role['role'] ?? ''}');
      parts.add('${role['activities'] ?? ''}');
      final risks = role['risks'];
      if (risks is List) {
        for (final risk in risks.whereType<Map>()) {
          parts.add('${risk['description'] ?? risk['risk'] ?? ''}');
          parts.add('${risk['category'] ?? ''}');
        }
      }
      final trainings = role['suggestedTrainings'];
      if (trainings is List) {
        for (final training in trainings.whereType<Map>()) {
          parts.add('${training['code'] ?? ''} ${training['title'] ?? ''}');
        }
      }
    }
    return parts.join(' ');
  }

  Future<void> _openPgrGuide() async {
    final company = selectedCompany;
    final sector = selectedSector;
    final doc = pgrDocument;
    if (company == null || sector == null || doc == null) return;
    setState(() => pgrGuideBusy = true);
    try {
      final siteText = selectedSite == null ? '' : ' na unidade/obra ${selectedSite!.name}';
      final result = await PgrService.ask(
        company,
        doc,
        'Prepare um guia prático para a vistoria SST no setor ${sector.name}$siteText. '
        'Use somente o PGR desta empresa. Mostre: 1) atividades e riscos do setor; '
        '2) pontos que devo observar em campo; 3) EPC, EPI e medidas de controle citadas ou sustentadas pelo documento; '
        '4) documentos ou registros que vale conferir; 5) perguntas simples que posso fazer aos trabalhadores. '
        'Se o PGR não trouxer informação suficiente para algum item, diga isso claramente. Não invente requisitos.',
      );
      if (!mounted) return;
      await showModalBottomSheet<void>(
        context: context,
        isScrollControlled: true,
        showDragHandle: true,
        builder: (context) => SafeArea(
          child: Padding(
            padding: EdgeInsets.fromLTRB(18, 4, 18, 18 + MediaQuery.of(context).viewInsets.bottom),
            child: ConstrainedBox(
              constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * .78),
              child: SingleChildScrollView(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Row(children: [
                    const Icon(Icons.fact_check_outlined),
                    const SizedBox(width: 9),
                    Expanded(child: Text('Guia PGR • ${sector.name}', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900))),
                  ]),
                  const SizedBox(height: 10),
                  Text('${result['answer'] ?? ''}', style: const TextStyle(height: 1.4)),
                  if (result['sourceHints'] is List && (result['sourceHints'] as List).isNotEmpty) ...[
                    const SizedBox(height: 14),
                    const Text('Onde conferir no PGR', style: TextStyle(fontWeight: FontWeight.w800)),
                    ...(result['sourceHints'] as List).take(8).map((item) => Padding(
                      padding: const EdgeInsets.only(top: 4), child: Text('• $item'))),
                  ],
                  if ('${result['limitations'] ?? ''}'.trim().isNotEmpty) ...[
                    const SizedBox(height: 10),
                    Text('Limitação: ${result['limitations']}', style: const TextStyle(fontSize: 12, color: Colors.black54)),
                  ],
                  const SizedBox(height: 14),
                  const Text('Use este guia como apoio. A vistoria continua dependendo da verificação real das condições do local.', style: TextStyle(fontSize: 11.5, color: Colors.black54)),
                ]),
              ),
            ),
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    } finally {
      if (mounted) setState(() => pgrGuideBusy = false);
    }
  }

'''
    text = replace_once(text, marker, helpers + marker, "guia PGR da vistoria")
    text = replace_once(
        text,
        "      selectedSector?.description ?? '',\n    ].join(' ').toLowerCase();\n",
        "      selectedSector?.description ?? '',\n      _pgrContextText,\n    ].join(' ').toLowerCase();\n",
        "contexto PGR nas sugestões de checklist",
    )

    old_kw = """    if (contextText.contains('confin') ||
        contextText.contains('silo') ||
        contextText.contains('tanque')) {
      suggested.add('Espaço Confinado');
    }

    final available = _checklistCategories.toSet();
"""
    new_kw = """    if (contextText.contains('confin') ||
        contextText.contains('silo') ||
        contextText.contains('tanque') ||
        contextText.contains('nr-33') ||
        contextText.contains('nr 33')) {
      suggested.add('Espaço Confinado');
    }
    if (contextText.contains('nr-10') || contextText.contains('nr 10')) suggested.add('Elétrica');
    if (contextText.contains('nr-12') || contextText.contains('nr 12')) suggested.add('Máquinas e Equipamentos');
    if (contextText.contains('nr-17') || contextText.contains('nr 17')) suggested.add('Ergonomia');
    if (contextText.contains('altura') || contextText.contains('nr-35') || contextText.contains('nr 35')) {
      suggested.addAll({'Normas Regulamentadoras', 'Construção Civil'});
    }
    if (contextText.contains('ruído') || contextText.contains('ruido')) suggested.add('EPI');
    if (contextText.contains('nr-') || contextText.contains('nr ')) suggested.add('Normas Regulamentadoras');

    final available = _checklistCategories.toSet();
"""
    text = replace_once(text, old_kw, new_kw, "categorias de checklist pelo PGR")

    old_ui = """          const SizedBox(height: 14),
          if (selectedSector != null && _suggestedChecklistCategories.isNotEmpty)
            Card(
"""
    new_ui = """          const SizedBox(height: 14),
          if (selectedSector != null && pgrDocument != null) ...[
            Card(
              color: Theme.of(context).colorScheme.secondaryContainer.withValues(alpha: .36),
              child: Padding(
                padding: const EdgeInsets.all(13),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Row(children: [
                    Icon(Icons.auto_awesome_rounded, size: 20),
                    SizedBox(width: 7),
                    Expanded(child: Text('Usar PGR como guia da vistoria', style: TextStyle(fontWeight: FontWeight.w900))),
                  ]),
                  const SizedBox(height: 6),
                  Text(
                    pgrAnalysis == null
                        ? 'A IA consulta o PGR desta empresa e prepara os principais pontos para verificar no setor selecionado.'
                        : 'O PGR também está sendo considerado nas sugestões de checklist abaixo.',
                    style: const TextStyle(fontSize: 11.5),
                  ),
                  const SizedBox(height: 10),
                  OutlinedButton.icon(
                    onPressed: pgrGuideBusy ? null : _openPgrGuide,
                    icon: pgrGuideBusy
                        ? const SizedBox(width: 17, height: 17, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(Icons.fact_check_outlined),
                    label: Text(pgrGuideBusy ? 'Consultando PGR...' : 'Ver guia deste setor'),
                  ),
                ]),
              ),
            ),
            const SizedBox(height: 10),
          ],
          if (selectedSector != null && _suggestedChecklistCategories.isNotEmpty)
            Card(
"""
    text = replace_once(text, old_ui, new_ui, "botão guia PGR na nova vistoria")
    path.write_text(text, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: patch_pgr_tools_v3260.py <pasta-do-projeto>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    patch_pgr_screen(root / "lib/screens/pgr_screen.dart")
    patch_new_inspection(root / "lib/screens/new_inspection_screen.dart")
    pubspec = root / "pubspec.yaml"
    text = pubspec.read_text(encoding="utf-8")
    text = text.replace("version: 3.25.2+105", "version: 3.26.0+106", 1)
    pubspec.write_text(text, encoding="utf-8")
    (root / "MUDANCAS_V3_26_0_PGR_GUIA_VISTORIA.txt").write_text(
        "AUDITAR SST v3.26.0 — PGR COMO GUIA DE TRABALHO\n\n"
        "- Painel com setores, cargos, riscos e treinamentos sugeridos pelo PGR.\n"
        "- Ferramentas rápidas: guia de vistoria, DDS, EPI/proteções, Ordem de Serviço e resumo gerencial.\n"
        "- Conferência PGR x cadastro do app.\n"
        "- Nova Vistoria pode usar o PGR como guia por setor.\n"
        "- Sugestões de checklist passam a considerar riscos e atividades do PGR.\n"
        "- A Central Online v3.25.2 continua compatível; não exige novo Code.gs.\n",
        encoding="utf-8",
    )
    print("v3.26.0: PGR como guia de trabalho e vistoria aplicado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Adiciona o criador de checklist com IA (v3.25.2)."""
from __future__ import annotations
import re, sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Marcador não encontrado: {label}')
    return text.replace(old, new, 1)


def patch_screen(root: Path) -> None:
    p = root / 'lib/screens/checklist_templates_screen.dart'
    t = p.read_text(encoding='utf-8')
    t = replace_once(t, "import '../models.dart';\n", "import '../models.dart';\nimport '../services/ai_assistant_service.dart';\n", 'import IA')
    t = replace_once(t, '  bool loading = true;\n', '  bool loading = true;\n  bool generatingWithAi = false;\n', 'estado IA')

    marker = '  Future<void> _addTemplate() async {\n'
    method = r'''  Future<void> _createChecklistWithAi() async {
    final requestController = TextEditingController();

    final shouldGenerate = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.auto_awesome),
            SizedBox(width: 8),
            Expanded(child: Text('Criar checklist com IA')),
          ],
        ),
        content: SizedBox(
          width: 560,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Diga em linguagem simples qual checklist você precisa. A IA cria o modelo e as perguntas para você revisar antes de salvar.',
              ),
              const SizedBox(height: 12),
              TextField(
                controller: requestController,
                autofocus: true,
                minLines: 4,
                maxLines: 7,
                decoration: const InputDecoration(
                  labelText: 'Que checklist você quer?',
                  hintText: 'Ex.: Checklist para inspeção de betoneira em obra, focado em proteções, elétrica, organização e uso seguro.',
                  alignLabelWithHint: true,
                ),
              ),
              const SizedBox(height: 10),
              const Text(
                'A IA é apoio. Revise as perguntas e referências antes de usar em campo.',
                style: TextStyle(fontSize: 12),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton.icon(
            onPressed: () => Navigator.pop(context, true),
            icon: const Icon(Icons.auto_awesome),
            label: const Text('Criar com IA'),
          ),
        ],
      ),
    );

    final request = requestController.text.trim();
    requestController.dispose();
    if (shouldGenerate != true || request.isEmpty || !mounted) return;

    setState(() => generatingWithAi = true);
    final reply = await AiAssistantService.createChecklist(request: request);
    if (!mounted) return;
    setState(() => generatingWithAi = false);

    if (!reply.success) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(reply.message)),
      );
      return;
    }

    final result = reply.result;
    final rawItems = result['items'];
    final items = rawItems is List
        ? rawItems
            .whereType<Map>()
            .map((row) => Map<String, dynamic>.from(row))
            .toList()
        : <Map<String, dynamic>>[];
    if (items.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('A IA não retornou perguntas para o checklist.'),
        ),
      );
      return;
    }

    final name = '${result['name'] ?? 'Checklist criado com IA'}'.trim();
    final category = '${result['category'] ?? 'Personalizado'}'.trim();
    final reference = '${result['reference'] ?? ''}'.trim();

    final save = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Revisar checklist criado pela IA'),
        content: SizedBox(
          width: 680,
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  [category, reference]
                      .where((value) => value.isNotEmpty)
                      .join(' • '),
                ),
                const SizedBox(height: 12),
                Text(
                  '${items.length} perguntas sugeridas',
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 8),
                ...items.take(40).toList().asMap().entries.map((entry) {
                  final item = entry.value;
                  final question = '${item['question'] ?? ''}'.trim();
                  final itemReference = '${item['reference'] ?? ''}'.trim();
                  final priority = '${item['priority'] ?? 'Média'}'.trim();
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 9),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        SizedBox(
                          width: 30,
                          child: Text(
                            '${entry.key + 1}.',
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                        ),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(question),
                              if (itemReference.isNotEmpty)
                                Text(
                                  '$itemReference • Prioridade $priority',
                                  style: Theme.of(context).textTheme.bodySmall,
                                ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  );
                }),
                const SizedBox(height: 6),
                const Text(
                  'Ao salvar, o checklist entra na biblioteca e pode ser editado normalmente.',
                  style: TextStyle(fontSize: 12),
                ),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Descartar'),
          ),
          FilledButton.icon(
            onPressed: () => Navigator.pop(context, true),
            icon: const Icon(Icons.save_outlined),
            label: const Text('Salvar checklist'),
          ),
        ],
      ),
    );

    if (save != true || !mounted) return;

    final template = ChecklistTemplate(
      id: const Uuid().v4(),
      name: name.isEmpty ? 'Checklist criado com IA' : name,
      category: category.isEmpty ? 'Personalizado' : category,
      reference: reference,
    );
    await AppDatabase.instance.insertChecklistTemplate(template);

    var order = 1;
    for (final row in items.take(40)) {
      final question = '${row['question'] ?? ''}'.trim();
      if (question.isEmpty) continue;
      final priorityRaw = '${row['priority'] ?? 'Média'}'.trim();
      final priority = const ['Baixa', 'Média', 'Alta', 'Crítica']
              .contains(priorityRaw)
          ? priorityRaw
          : 'Média';
      await AppDatabase.instance.insertChecklistItem(
        ChecklistItem(
          id: const Uuid().v4(),
          templateId: template.id,
          sortOrder: order++,
          category: '${row['category'] ?? category}'.trim(),
          text: question,
          reference: '${row['reference'] ?? reference}'.trim(),
          priority: priority,
        ),
      );
    }

    await _load();
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Checklist criado e salvo na biblioteca.')),
    );
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ChecklistItemsScreen(template: template),
      ),
    );
    await _load();
  }

'''
    if '_createChecklistWithAi()' not in t:
        t = replace_once(t, marker, method + marker, 'método criador IA')

    old_button = '''                        FilledButton.icon(
                          onPressed: _addTemplate,
                          icon:
                              const Icon(Icons.add),
                          label: const Text(
                            'Novo checklist',
                          ),
                        ),'''
    new_button = '''                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: [
                            FilledButton.icon(
                              onPressed: _addTemplate,
                              icon: const Icon(Icons.add),
                              label: const Text('Novo checklist'),
                            ),
                            FilledButton.tonalIcon(
                              onPressed: generatingWithAi
                                  ? null
                                  : _createChecklistWithAi,
                              icon: generatingWithAi
                                  ? const SizedBox(
                                      width: 18,
                                      height: 18,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                      ),
                                    )
                                  : const Icon(Icons.auto_awesome),
                              label: Text(
                                generatingWithAi
                                    ? 'Criando com IA...'
                                    : 'Criar com IA',
                              ),
                            ),
                          ],
                        ),'''
    if "FilledButton.tonalIcon(" not in t:
        t = replace_once(t, old_button, new_button, 'botão Criar com IA')
    p.write_text(t, encoding='utf-8')


def patch_service(root: Path) -> None:
    p = root / 'lib/services/ai_assistant_service.dart'
    t = p.read_text(encoding='utf-8')
    marker = '  static Future<AiAssistantReply> suggestReportConclusion(\n'
    method = '''  static Future<AiAssistantReply> createChecklist({
    required String request,
  }) async {
    final objective = request.trim();
    if (objective.length < 8) {
      return const AiAssistantReply(
        success: false,
        message: 'Descreva um pouco melhor o checklist que você quer criar.',
      );
    }

    return _send({
      'mode': 'checklist_builder',
      'request': objective,
    });
  }

'''
    if 'createChecklist({' not in t:
        t = replace_once(t, marker, method + marker, 'serviço IA checklist')
    p.write_text(t, encoding='utf-8')


def patch_backend(root: Path) -> None:
    p = root / 'painel_web_google_apps_script/Code.gs'
    t = p.read_text(encoding='utf-8')
    t = replace_once(
        t,
        "'pgr_extract', 'pgr_question']",
        "'pgr_extract', 'pgr_question', 'checklist_builder']",
        'modo permitido',
    )
    t = replace_once(
        t,
        ": mode === 'training_management' ? 3200\n        : mode === 'report_conclusion' ? 1400 : 1700,",
        ": mode === 'training_management' ? 3200\n        : mode === 'checklist_builder' ? 6500\n        : mode === 'report_conclusion' ? 1400 : 1700,",
        'tokens checklist',
    )

    prompt_marker = "  if (mode === 'report_conclusion') {\n"
    prompt = """  if (mode === 'checklist_builder') {
    return [
      'Crie um checklist de Segurança e Saúde no Trabalho com base no pedido do técnico abaixo.',
      'Pedido: ' + String(payload.request || '') + '.',
      'Gere um nome curto e profissional, uma categoria, uma referência geral e entre 8 e 40 perguntas objetivas.',
      'Cada pergunta deve verificar apenas um ponto e ser adequada para uso em vistoria de campo.',
      'Organize por categorias quando fizer sentido.',
      'Use referências de NRs somente quando forem razoavelmente aplicáveis e trate-as como referência a conferir, nunca como garantia de conformidade legal.',
      'Não invente medições, limites ou requisitos específicos quando o pedido não fornecer contexto suficiente.',
      'Prioridade deve ser Baixa, Média, Alta ou Crítica conforme o potencial de risco do item.',
      'Evite perguntas repetidas, genéricas demais ou que dependam de documentos que não foram mencionados.'
    ].join('\\n');
  }
"""
    ai_prompt_start = t.index('function aiUserPrompt_')
    ai_schema_start = t.index('function aiOutputSchema_')
    if "mode === 'checklist_builder'" not in t[ai_prompt_start:ai_schema_start]:
        pos = t.index(prompt_marker, ai_prompt_start)
        t = t[:pos] + prompt + t[pos:]

    schema = """  if (mode === 'checklist_builder') {
    return {
      type: 'object',
      properties: {
        name: {type: 'string'},
        category: {type: 'string'},
        reference: {type: 'string'},
        items: {
          type: 'array',
          minItems: 8,
          maxItems: 40,
          items: {
            type: 'object',
            properties: {
              category: {type: 'string'},
              question: {type: 'string'},
              reference: {type: 'string'},
              priority: {type: 'string', enum: ['Baixa', 'Média', 'Alta', 'Crítica']}
            },
            required: ['category', 'question', 'reference', 'priority']
          }
        },
        warning: {type: 'string'}
      },
      required: ['name', 'category', 'reference', 'items', 'warning']
    };
  }
"""
    ai_schema_start = t.index('function aiOutputSchema_')
    if "mode === 'checklist_builder'" not in t[ai_schema_start:]:
        pos = t.index(prompt_marker, ai_schema_start)
        t = t[:pos] + schema + t[pos:]
    p.write_text(t, encoding='utf-8')


def patch_version(root: Path) -> None:
    p = root / 'pubspec.yaml'
    t = p.read_text(encoding='utf-8')
    t = re.sub(r'^version:\s*[^\n]+', 'version: 3.25.2+105', t, count=1, flags=re.M)
    p.write_text(t, encoding='utf-8')
    (root / 'MUDANCAS_V3_25_2_CHECKLIST_IA.txt').write_text(
        'Auditar SST v3.25.2 — Criador de Checklist com IA\n\n'
        '- Botão "Criar com IA" no menu Biblioteca de checklists.\n'
        '- O técnico descreve o checklist em linguagem simples.\n'
        '- A IA gera nome, categoria, referência e 8 a 40 perguntas.\n'
        '- O app mostra uma prévia para revisão antes de salvar.\n'
        '- Ao confirmar, o checklist fica salvo na biblioteca e pode ser editado normalmente.\n'
        '- As referências devem ser conferidas pelo TST antes do uso em campo.\n',
        encoding='utf-8',
    )


def main() -> int:
    if len(sys.argv) != 2:
        print('Uso: patch_checklist_ai_v3252.py <pasta-do-projeto>', file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    patch_screen(root)
    patch_service(root)
    patch_backend(root)
    patch_version(root)
    print('v3.25.2: criador de checklist com IA aplicado.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

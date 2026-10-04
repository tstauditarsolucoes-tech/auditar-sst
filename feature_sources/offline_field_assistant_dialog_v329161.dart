import 'package:flutter/material.dart';

import '../services/offline_field_rules_service.dart';

class OfflineFieldAssistantDialog {
  const OfflineFieldAssistantDialog._();

  static Future<OfflineFieldRuleResult?> show(
    BuildContext context, {
    required String text,
    bool markedRecurring = false,
    String? existingReference,
  }) {
    var probability = 3;
    var severity = 3;
    var recurring = markedRecurring;

    return showDialog<OfflineFieldRuleResult>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) {
          final combined = [
            text,
            if ((existingReference ?? '').trim().isNotEmpty)
              existingReference!.trim(),
          ].join(' ');
          final result = OfflineFieldRulesService.analyze(
            text: combined,
            probability: probability,
            severity: severity,
            recurring: recurring,
          );
          final nrs = result.nrs.isEmpty
              ? 'Nenhuma NR sugerida automaticamente'
              : result.nrs.join(', ');

          Widget selector(
            String label,
            int value,
            ValueChanged<int> onChanged,
          ) {
            return DropdownButtonFormField<int>(
              value: value,
              isExpanded: true,
              decoration: InputDecoration(
                labelText: label,
                border: const OutlineInputBorder(),
              ),
              items: List.generate(
                5,
                (index) {
                  final number = index + 1;
                  return DropdownMenuItem(
                    value: number,
                    child: Text(number.toString()),
                  );
                },
              ),
              onChanged: (next) {
                if (next != null) onChanged(next);
              },
            );
          }

          return AlertDialog(
            title: const Row(
              children: [
                Icon(Icons.offline_bolt_outlined),
                SizedBox(width: 8),
                Expanded(child: Text('Assistente sem IA')),
              ],
            ),
            content: SizedBox(
              width: 720,
              child: SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Cálculo e sugestões feitos no aparelho. Não usa internet nem IA. Confirme sempre a NR e a prioridade antes de salvar.',
                      style: TextStyle(fontSize: 12.5, color: Colors.black54),
                    ),
                    const SizedBox(height: 14),
                    LayoutBuilder(
                      builder: (context, constraints) {
                        if (constraints.maxWidth < 520) {
                          return Column(
                            children: [
                              selector(
                                'Probabilidade (1 a 5)',
                                probability,
                                (next) => setDialogState(
                                  () => probability = next,
                                ),
                              ),
                              const SizedBox(height: 10),
                              selector(
                                'Severidade (1 a 5)',
                                severity,
                                (next) => setDialogState(
                                  () => severity = next,
                                ),
                              ),
                            ],
                          );
                        }
                        return Row(
                          children: [
                            Expanded(
                              child: selector(
                                'Probabilidade (1 a 5)',
                                probability,
                                (next) => setDialogState(
                                  () => probability = next,
                                ),
                              ),
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: selector(
                                'Severidade (1 a 5)',
                                severity,
                                (next) => setDialogState(
                                  () => severity = next,
                                ),
                              ),
                            ),
                          ],
                        );
                      },
                    ),
                    CheckboxListTile(
                      contentPadding: EdgeInsets.zero,
                      value: recurring,
                      title: const Text('Situação recorrente'),
                      subtitle: const Text(
                        'A recorrência aumenta a prioridade calculada pela regra local.',
                      ),
                      onChanged: (value) => setDialogState(
                        () => recurring = value ?? false,
                      ),
                    ),
                    const Divider(),
                    Text(
                      'Prioridade sugerida: ' + result.priority,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    Text('Pontuação da matriz: ' + result.score.toString()),
                    const SizedBox(height: 10),
                    const Text(
                      'NRs sugeridas',
                      style: TextStyle(fontWeight: FontWeight.w800),
                    ),
                    SelectableText(nrs),
                    const SizedBox(height: 10),
                    const Text(
                      'Ação sugerida',
                      style: TextStyle(fontWeight: FontWeight.w800),
                    ),
                    SelectableText(result.actionPlan),
                    const SizedBox(height: 8),
                    Text(
                      'Responsável sugerido: ' + result.responsibleSuggestion,
                    ),
                    Text('Prazo sugerido: ' + result.deadlineSuggestion),
                  ],
                ),
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(dialogContext),
                child: const Text('Cancelar'),
              ),
              FilledButton.icon(
                onPressed: () => Navigator.pop(dialogContext, result),
                icon: const Icon(Icons.check),
                label: const Text('Aplicar sugestões'),
              ),
            ],
          );
        },
      ),
    );
  }
}

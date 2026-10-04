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
    final combined = [
      text,
      if ((existingReference ?? '').trim().isNotEmpty)
        existingReference!.trim(),
    ].join(' ');
    var probability =
        OfflineFieldRulesService.suggestedProbabilityForText(combined);
    var severity =
        OfflineFieldRulesService.suggestedSeverityForText(combined);
    var recurring = markedRecurring;

    return showDialog<OfflineFieldRuleResult>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) {
          final result = OfflineFieldRulesService.analyze(
            text: combined,
            probability: probability,
            severity: severity,
            recurring: recurring,
          );

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

          Widget section(
            String title,
            String value, {
            IconData? icon,
          }) {
            if (value.trim().isEmpty) return const SizedBox.shrink();
            return Padding(
              padding: const EdgeInsets.only(top: 10),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (icon != null) ...[
                        Icon(icon, size: 18),
                        const SizedBox(width: 6),
                      ],
                      Expanded(
                        child: Text(
                          title,
                          style: const TextStyle(
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  SelectableText(value),
                ],
              ),
            );
          }

          return AlertDialog(
            title: const Row(
              children: [
                Icon(Icons.offline_bolt_outlined),
                SizedBox(width: 8),
                Expanded(child: Text('Análise técnica sem IA')),
              ],
            ),
            content: SizedBox(
              width: 760,
              child: SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Leitura feita no próprio aparelho. Não usa internet nem IA. '
                      'O resultado é uma sugestão técnica para conferência do TST antes de salvar.',
                      style: TextStyle(
                        fontSize: 12.5,
                        color: Colors.black54,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.black.withValues(alpha: .035),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: Colors.black12),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            result.category,
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w900,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            result.technicalReason,
                            style: const TextStyle(
                              fontSize: 12.5,
                              color: Colors.black54,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),
                    const Text(
                      'Matriz de risco',
                      style: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Valores iniciais sugeridos pela regra local: '
                      'P${result.suggestedProbability} / S${result.suggestedSeverity}. '
                      'Ajuste conforme a situação real observada.',
                      style: const TextStyle(
                        fontSize: 12,
                        color: Colors.black54,
                      ),
                    ),
                    const SizedBox(height: 10),
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
                        'A recorrência acrescenta peso à matriz local.',
                      ),
                      onChanged: (value) => setDialogState(
                        () => recurring = value ?? false,
                      ),
                    ),
                    const Divider(),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        Chip(
                          avatar: const Icon(
                            Icons.priority_high_rounded,
                            size: 17,
                          ),
                          label: Text(
                            'Prioridade: ${result.priority}',
                            style: const TextStyle(
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ),
                        Chip(
                          avatar: const Icon(
                            Icons.calculate_outlined,
                            size: 17,
                          ),
                          label: Text(
                            'Matriz: ${result.score}/25',
                          ),
                        ),
                        if (result.possibleRecurrence)
                          const Chip(
                            avatar: Icon(Icons.repeat_rounded, size: 17),
                            label: Text('Possível recorrência'),
                          ),
                      ],
                    ),
                    section(
                      'Risco identificado',
                      result.riskSummary,
                      icon: Icons.warning_amber_rounded,
                    ),
                    section(
                      'Consequência possível',
                      result.consequenceSummary,
                      icon: Icons.personal_injury_outlined,
                    ),
                    const SizedBox(height: 12),
                    const Text(
                      'Base normativa sugerida',
                      style: TextStyle(fontWeight: FontWeight.w900),
                    ),
                    const SizedBox(height: 5),
                    if (result.nrDetails.isEmpty)
                      const Text(
                        'Nenhuma NR específica foi reconhecida automaticamente. '
                        'Confirme manualmente a base normativa.',
                      )
                    else
                      ...result.nrDetails.map(
                        (item) => Padding(
                          padding: const EdgeInsets.only(bottom: 4),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('• '),
                              Expanded(child: SelectableText(item)),
                            ],
                          ),
                        ),
                      ),
                    section(
                      'Ação corretiva sugerida',
                      result.actionPlan,
                      icon: Icons.build_circle_outlined,
                    ),
                    section(
                      'Evidência recomendada para encerramento',
                      result.evidenceSuggestion,
                      icon: Icons.photo_camera_back_outlined,
                    ),
                    const SizedBox(height: 10),
                    Text(
                      'Responsável sugerido: ${result.responsibleSuggestion}',
                    ),
                    Text('Prazo sugerido: ${result.deadlineSuggestion}'),
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

import 'package:flutter/material.dart';

import '../models.dart';

class SearchableWorkerField extends StatelessWidget {
  final List<Worker> workers;
  final String? value;
  final ValueChanged<String?> onChanged;
  final String label;
  final bool enabled;
  final String emptyText;

  const SearchableWorkerField({
    super.key,
    required this.workers,
    required this.value,
    required this.onChanged,
    this.label = 'Colaborador',
    this.enabled = true,
    this.emptyText = 'Pesquisar colaborador por nome',
  });

  Worker? get selectedWorker {
    final id = value?.trim() ?? '';
    if (id.isEmpty) return null;
    for (final worker in workers) {
      if (worker.id == id) return worker;
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final selected = selectedWorker;
    return InkWell(
      borderRadius: BorderRadius.circular(12),
      onTap: enabled
          ? () async {
              final result = await showWorkerSearchDialog(
                context,
                workers: workers,
                selectedId: value,
                title: label,
              );
              if (result != null) onChanged(result);
            }
          : null,
      child: InputDecorator(
        decoration: InputDecoration(
          labelText: label,
          prefixIcon: const Icon(Icons.person_search_outlined),
          suffixIcon: const Icon(Icons.search),
          enabled: enabled,
        ),
        child: Text(
          selected == null
              ? emptyText
              : [
                  selected.name,
                  if (selected.role.trim().isNotEmpty) selected.role.trim(),
                ].join(' • '),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: TextStyle(
            color: selected == null ? Colors.black54 : Colors.black87,
            fontWeight:
                selected == null ? FontWeight.w400 : FontWeight.w700,
          ),
        ),
      ),
    );
  }
}

Future<String?> showWorkerSearchDialog(
  BuildContext context, {
  required List<Worker> workers,
  String? selectedId,
  String title = 'Selecionar colaborador',
}) async {
  final controller = TextEditingController();
  var query = '';

  final result = await showDialog<String>(
    context: context,
    builder: (dialogContext) => StatefulBuilder(
      builder: (context, setLocalState) {
        final clean = query.trim().toLowerCase();
        final visible = workers.where((worker) {
          if (!worker.active) return false;
          if (clean.isEmpty) return true;
          return worker.name.toLowerCase().contains(clean) ||
              worker.role.toLowerCase().contains(clean) ||
              worker.cpf.toLowerCase().contains(clean);
        }).toList()
          ..sort(
            (a, b) =>
                a.name.toLowerCase().compareTo(b.name.toLowerCase()),
          );

        return AlertDialog(
          title: Text(title),
          content: SizedBox(
            width: 560,
            height: 540,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextField(
                  controller: controller,
                  autofocus: true,
                  onChanged: (value) =>
                      setLocalState(() => query = value),
                  decoration: InputDecoration(
                    labelText: 'Pesquisar por nome',
                    hintText: 'Digite o nome do colaborador',
                    prefixIcon: const Icon(Icons.search),
                    suffixIcon: query.isEmpty
                        ? null
                        : IconButton(
                            tooltip: 'Limpar pesquisa',
                            onPressed: () {
                              controller.clear();
                              setLocalState(() => query = '');
                            },
                            icon: const Icon(Icons.close),
                          ),
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  '${visible.length} colaborador(es) encontrado(s)',
                  style: const TextStyle(
                    fontSize: 12,
                    color: Colors.black54,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 6),
                Expanded(
                  child: visible.isEmpty
                      ? const Center(
                          child: Text(
                            'Nenhum colaborador encontrado.',
                            textAlign: TextAlign.center,
                          ),
                        )
                      : ListView.separated(
                          itemCount: visible.length,
                          separatorBuilder: (_, __) =>
                              const Divider(height: 1),
                          itemBuilder: (_, index) {
                            final worker = visible[index];
                            final details = [
                              if (worker.role.trim().isNotEmpty)
                                worker.role.trim(),
                              if (worker.cpf.trim().isNotEmpty)
                                'CPF ${worker.cpf.trim()}',
                            ].join(' • ');
                            final selected = worker.id == selectedId;
                            return ListTile(
                              leading: Icon(
                                selected
                                    ? Icons.check_circle
                                    : Icons.person_outline,
                                color: selected
                                    ? Theme.of(context).colorScheme.primary
                                    : null,
                              ),
                              title: Text(
                                worker.name,
                                style: TextStyle(
                                  fontWeight: selected
                                      ? FontWeight.w800
                                      : FontWeight.w600,
                                ),
                              ),
                              subtitle:
                                  details.isEmpty ? null : Text(details),
                              onTap: () =>
                                  Navigator.pop(dialogContext, worker.id),
                            );
                          },
                        ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('Cancelar'),
            ),
          ],
        );
      },
    ),
  );
  controller.dispose();
  return result;
}

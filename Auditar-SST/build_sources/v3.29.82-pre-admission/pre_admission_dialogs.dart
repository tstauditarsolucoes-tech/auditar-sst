import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../models.dart';
import '../services/pre_admission_participant_service.dart';

Future<SstRecord?> showCreatePreAdmissionDialog(
  BuildContext context, {
  required String companyId,
  required List<Sector> sectors,
  String title = 'Participante em pré-admissão',
}) async {
  final name = TextEditingController();
  final cpf = TextEditingController();
  final role = TextEditingController();
  String? sectorId;

  final result = await showDialog<SstRecord>(
    context: context,
    builder: (dialogContext) => StatefulBuilder(
      builder: (context, setLocalState) => AlertDialog(
        title: Text(title),
        content: SizedBox(
          width: 520,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  'Use para quem vai participar da integração ou DDS antes de o vínculo estar formalizado. Não entra como colaborador ativo.',
                  style: TextStyle(
                    fontSize: 12.5,
                    color: Colors.black54,
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: name,
                  autofocus: true,
                  decoration: const InputDecoration(
                    labelText: 'Nome *',
                    prefixIcon: Icon(Icons.person_outline),
                  ),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: role,
                  decoration: const InputDecoration(
                    labelText: 'Função prevista',
                    prefixIcon: Icon(Icons.badge_outlined),
                  ),
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String?>(
                  value: sectorId,
                  isExpanded: true,
                  decoration: const InputDecoration(
                    labelText: 'Setor previsto',
                    prefixIcon: Icon(Icons.account_tree_outlined),
                  ),
                  items: [
                    const DropdownMenuItem<String?>(
                      value: null,
                      child: Text('Ainda não definido'),
                    ),
                    ...sectors.map(
                      (sector) => DropdownMenuItem<String?>(
                        value: sector.id,
                        child: Text(
                          sector.name,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ),
                  ],
                  onChanged: (value) =>
                      setLocalState(() => sectorId = value),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: cpf,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'CPF (opcional)',
                    prefixIcon: Icon(Icons.credit_card_outlined),
                  ),
                ),
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
            onPressed: () async {
              final cleanName = name.text.trim();
              if (cleanName.isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Informe o nome do participante.'),
                  ),
                );
                return;
              }
              var sectorName = '';
              for (final sector in sectors) {
                if (sector.id == sectorId) {
                  sectorName = sector.name;
                  break;
                }
              }
              final created =
                  await PreAdmissionParticipantService.create(
                companyId: companyId,
                name: cleanName,
                cpf: cpf.text.trim(),
                role: role.text.trim(),
                sectorId: sectorId,
                sectorName: sectorName,
              );
              if (dialogContext.mounted) {
                Navigator.pop(dialogContext, created);
              }
            },
            icon: const Icon(Icons.person_add_alt_1_outlined),
            label: const Text('Adicionar'),
          ),
        ],
      ),
    ),
  );

  name.dispose();
  cpf.dispose();
  role.dispose();
  return result;
}

Future<Worker?> showConvertPreAdmissionDialog(
  BuildContext context, {
  required SstRecord participant,
  required List<Sector> sectors,
}) async {
  final name = TextEditingController(
    text: '${participant.payload['name'] ?? participant.title}',
  );
  final cpf = TextEditingController(
    text: '${participant.payload['cpf'] ?? ''}',
  );
  final role = TextEditingController(
    text: '${participant.payload['role'] ?? ''}',
  );
  String? sectorId =
      '${participant.payload['sectorId'] ?? ''}'.trim();
  if (sectorId.isEmpty) sectorId = null;
  var admissionDate = DateTime.now();

  final result = await showDialog<Worker>(
    context: context,
    builder: (dialogContext) => StatefulBuilder(
      builder: (context, setLocalState) => AlertDialog(
        title: const Text('Converter em colaborador'),
        content: SizedBox(
          width: 520,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  'Ao converter, o histórico da integração, DDS e assinaturas anteriores permanece vinculado à pessoa.',
                  style: TextStyle(
                    fontSize: 12.5,
                    color: Colors.black54,
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: name,
                  decoration: const InputDecoration(
                    labelText: 'Nome *',
                  ),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: role,
                  decoration: const InputDecoration(
                    labelText: 'Cargo / função',
                  ),
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String?>(
                  value: sectorId,
                  isExpanded: true,
                  decoration: const InputDecoration(
                    labelText: 'Setor',
                  ),
                  items: [
                    const DropdownMenuItem<String?>(
                      value: null,
                      child: Text('Sem setor definido'),
                    ),
                    ...sectors.map(
                      (sector) => DropdownMenuItem<String?>(
                        value: sector.id,
                        child: Text(
                          sector.name,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ),
                  ],
                  onChanged: (value) =>
                      setLocalState(() => sectorId = value),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: cpf,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'CPF'),
                ),
                const SizedBox(height: 6),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.event_available_outlined),
                  title: const Text('Data de admissão'),
                  subtitle: Text(
                    DateFormat('dd/MM/yyyy').format(admissionDate),
                  ),
                  onTap: () async {
                    final picked = await showDatePicker(
                      context: dialogContext,
                      initialDate: admissionDate,
                      firstDate: DateTime(1950),
                      lastDate:
                          DateTime.now().add(const Duration(days: 365)),
                    );
                    if (picked != null) {
                      setLocalState(() => admissionDate = picked);
                    }
                  },
                ),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () async {
              final cleanName = name.text.trim();
              if (cleanName.isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Informe o nome do colaborador.'),
                  ),
                );
                return;
              }
              final worker =
                  await PreAdmissionParticipantService.convertToWorker(
                participant: participant,
                name: cleanName,
                cpf: cpf.text.trim(),
                role: role.text.trim(),
                sectorId: sectorId,
                admissionDate: admissionDate,
              );
              if (dialogContext.mounted) {
                Navigator.pop(dialogContext, worker);
              }
            },
            child: const Text('Converter'),
          ),
        ],
      ),
    ),
  );

  name.dispose();
  cpf.dispose();
  role.dispose();
  return result;
}

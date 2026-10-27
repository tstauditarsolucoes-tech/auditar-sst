import 'dart:io';
import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';
import 'package:share_plus/share_plus.dart';

import '../brand.dart';
import '../database.dart';
import '../models.dart';
import '../services/cipa_management_service.dart';
import 'cipa_screen.dart';
import 'non_conformity_detail_screen.dart';
import 'trainings_screen.dart';

class CipaManagementScreen extends StatefulWidget {
  final String companyId;

  const CipaManagementScreen({
    super.key,
    required this.companyId,
  });

  @override
  State<CipaManagementScreen> createState() => _CipaManagementScreenState();
}

class _CipaManagementScreenState extends State<CipaManagementScreen> {
  final _date = DateFormat('dd/MM/yyyy');
  final _dateTime = DateFormat('dd/MM/yyyy HH:mm');

  Company? company;
  List<Worker> workers = [];
  List<TrainingControl> trainings = [];
  List<SstRecord> mandates = [];
  List<SstRecord> members = [];
  List<SstRecord> meetings = [];
  List<SstRecord> minutes = [];
  List<SstRecord> actions = [];
  List<SstRecord> documents = [];
  List<CipaElection> elections = [];
  bool loading = true;
  bool busy = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load({bool showLoading = true}) async {
    if (showLoading && mounted) setState(() => loading = true);
    try {
      await CipaManagementService.refreshLinkedNcStatuses(widget.companyId);
      final companies = await AppDatabase.instance.getCompanies();
      Company? selected;
      for (final item in companies) {
        if (item.id == widget.companyId) {
          selected = item;
          break;
        }
      }
      final results = await Future.wait<Object>([
        AppDatabase.instance.getWorkers(companyId: widget.companyId),
        AppDatabase.instance.getTrainingControls(companyId: widget.companyId),
        CipaManagementService.records(
          CipaManagementService.mandateType,
          widget.companyId,
        ),
        CipaManagementService.records(
          CipaManagementService.memberType,
          widget.companyId,
        ),
        CipaManagementService.records(
          CipaManagementService.meetingType,
          widget.companyId,
        ),
        CipaManagementService.records(
          CipaManagementService.minutesType,
          widget.companyId,
        ),
        CipaManagementService.records(
          CipaManagementService.actionType,
          widget.companyId,
        ),
        CipaManagementService.records(
          CipaManagementService.documentType,
          widget.companyId,
        ),
        AppDatabase.instance.getCipaElections(companyId: widget.companyId),
      ]);
      if (!mounted) return;
      setState(() {
        company = selected;
        workers = results[0] as List<Worker>;
        trainings = results[1] as List<TrainingControl>;
        mandates = results[2] as List<SstRecord>;
        members = results[3] as List<SstRecord>;
        meetings = results[4] as List<SstRecord>;
        minutes = results[5] as List<SstRecord>;
        actions = results[6] as List<SstRecord>;
        documents = results[7] as List<SstRecord>;
        elections = results[8] as List<CipaElection>;
        loading = false;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() => loading = false);
      _message('Não foi possível carregar a CIPA: $error');
    }
  }

  SstRecord? get activeMandate {
    for (final item in mandates) {
      if (item.status == 'Ativo') return item;
    }
    return null;
  }

  List<SstRecord> get activeMembers {
    final mandateId = activeMandate?.id ?? '';
    return members
        .where(
          (m) =>
              m.status == 'Ativo' &&
              (mandateId.isEmpty ||
                  '${m.payload['mandateId'] ?? ''}' == mandateId),
        )
        .toList();
  }

  List<SstRecord> get mandateMeetings {
    final mandateId = activeMandate?.id ?? '';
    return meetings
        .where(
          (m) =>
              mandateId.isEmpty ||
              '${m.payload['mandateId'] ?? ''}' == mandateId,
        )
        .toList();
  }

  List<SstRecord> get mandateActions {
    final mandateId = activeMandate?.id ?? '';
    return actions
        .where(
          (m) =>
              mandateId.isEmpty ||
              '${m.payload['mandateId'] ?? ''}' == mandateId,
        )
        .toList();
  }

  List<SstRecord> get mandateMinutes {
    final mandateId = activeMandate?.id ?? '';
    return minutes
        .where(
          (m) =>
              mandateId.isEmpty ||
              '${m.payload['mandateId'] ?? ''}' == mandateId,
        )
        .toList();
  }

  List<SstRecord> get mandateDocuments {
    final mandateId = activeMandate?.id ?? '';
    return documents
        .where(
          (m) =>
              mandateId.isEmpty ||
              '${m.payload['mandateId'] ?? ''}' == mandateId,
        )
        .toList();
  }

  SstRecord? get nextMeeting {
    final now = DateTime.now();
    final future = mandateMeetings
        .where((m) => m.status != 'Realizada' && !m.date.isBefore(now))
        .toList()
      ..sort((a, b) => a.date.compareTo(b.date));
    return future.isEmpty ? null : future.first;
  }

  int get pendingMinutesCount {
    var count = 0;
    for (final meeting in mandateMeetings.where((m) => m.status == 'Realizada')) {
      final hasMinutes = mandateMinutes.any(
        (a) => '${a.payload['meetingId'] ?? ''}' == meeting.id,
      );
      if (!hasMinutes) count++;
    }
    return count;
  }

  int get pendingTrainingCount {
    var count = 0;
    for (final member in activeMembers) {
      final workerId = '${member.payload['workerId'] ?? ''}'.trim();
      if (workerId.isEmpty) continue;
      final found = trainings.any(
        (training) =>
            training.workerId == workerId &&
            CipaManagementService.isCipaTraining(training),
      );
      if (!found) count++;
    }
    return count;
  }

  int get overdueActionsCount => mandateActions
      .where((a) => CipaManagementService.isOverdue(a))
      .length;

  List<String> get alerts {
    final result = <String>[];
    final mandate = activeMandate;
    final now = DateTime.now();
    if (mandate == null) {
      result.add('Nenhum mandato ativo cadastrado.');
    } else if (mandate.dueDate != null) {
      final days = mandate.dueDate!.difference(now).inDays;
      if (days <= 90) {
        result.add(
          days < 0
              ? 'O mandato está vencido.'
              : 'O mandato termina em $days dia(s). Prepare o próximo processo eleitoral.',
        );
      }
    }
    if (nextMeeting != null) {
      result.add('Próxima reunião: ${_dateTime.format(nextMeeting!.date)}.');
    } else {
      result.add('Não há próxima reunião agendada.');
    }
    if (pendingMinutesCount > 0) {
      result.add('$pendingMinutesCount reunião(ões) realizada(s) sem ata vinculada.');
    }
    if (overdueActionsCount > 0) {
      result.add('$overdueActionsCount ação(ões) da CIPA estão vencidas.');
    }
    if (pendingTrainingCount > 0) {
      result.add('$pendingTrainingCount membro(s) sem treinamento CIPA/NR-05 localizado.');
    }
    final requiredMissing = mandateDocuments
        .where(
          (d) =>
              d.payload['requiredDocument'] == true &&
              d.status != 'Arquivado' &&
              d.status != 'Concluído',
        )
        .length;
    if (requiredMissing > 0) {
      result.add('$requiredMissing documento(s) obrigatório(s) estão pendentes.');
    }
    return result;
  }

  void _message(String text) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));
  }

  Future<DateTime?> _pickDate(DateTime initial) => showDatePicker(
        context: context,
        firstDate: DateTime(2020),
        lastDate: DateTime(DateTime.now().year + 10),
        initialDate: initial,
      );

  Future<DateTime?> _pickDateTime(DateTime initial) async {
    final day = await _pickDate(initial);
    if (day == null || !mounted) return null;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(initial),
    );
    if (time == null) return DateTime(day.year, day.month, day.day);
    return DateTime(day.year, day.month, day.day, time.hour, time.minute);
  }

  Worker? _workerById(String id) {
    for (final worker in workers) {
      if (worker.id == id) return worker;
    }
    return null;
  }

  String _memberLabel(String memberId) {
    for (final member in members) {
      if (member.id == memberId) {
        final role = '${member.payload['cipaRole'] ?? ''}'.trim();
        return role.isEmpty ? member.title : '${member.title} • $role';
      }
    }
    return 'Membro';
  }

  Future<void> _editMandate([SstRecord? current]) async {
    final title = TextEditingController(text: current?.title ?? '');
    final notes = TextEditingController(
      text: '${current?.payload['notes'] ?? ''}',
    );
    var start = current?.date ?? DateTime.now();
    var end = current?.dueDate ?? DateTime.now().add(const Duration(days: 365));
    var status = current?.status ?? (activeMandate == null ? 'Ativo' : 'Planejado');

    final save = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
          title: Text(current == null ? 'Novo mandato' : 'Editar mandato'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: title,
                  decoration: const InputDecoration(
                    labelText: 'Identificação do mandato',
                    hintText: 'Ex.: CIPA 2026/2027',
                  ),
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  value: status,
                  decoration: const InputDecoration(labelText: 'Situação'),
                  items: const [
                    DropdownMenuItem(value: 'Planejado', child: Text('Planejado')),
                    DropdownMenuItem(value: 'Ativo', child: Text('Ativo')),
                    DropdownMenuItem(value: 'Encerrado', child: Text('Encerrado')),
                  ],
                  onChanged: (value) {
                    if (value != null) setLocal(() => status = value);
                  },
                ),
                const SizedBox(height: 10),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Início'),
                  subtitle: Text(_date.format(start)),
                  trailing: const Icon(Icons.calendar_month_outlined),
                  onTap: () async {
                    final picked = await _pickDate(start);
                    if (picked != null) setLocal(() => start = picked);
                  },
                ),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Término'),
                  subtitle: Text(_date.format(end)),
                  trailing: const Icon(Icons.event_outlined),
                  onTap: () async {
                    final picked = await _pickDate(end);
                    if (picked != null) setLocal(() => end = picked);
                  },
                ),
                TextField(
                  controller: notes,
                  maxLines: 3,
                  decoration: const InputDecoration(labelText: 'Observações'),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('Salvar'),
            ),
          ],
        ),
      ),
    );
    if (save != true) return;
    if (title.text.trim().isEmpty) {
      _message('Informe o nome do mandato.');
      return;
    }
    if (!end.isAfter(start)) {
      _message('A data final deve ser posterior à data inicial.');
      return;
    }
    if (status == 'Ativo') {
      for (final mandate in mandates) {
        if (mandate.id != current?.id && mandate.status == 'Ativo') {
          await CipaManagementService.saveMandate(
            id: mandate.id,
            companyId: widget.companyId,
            title: mandate.title,
            start: mandate.date,
            end: mandate.dueDate ?? mandate.date,
            status: 'Encerrado',
            notes: '${mandate.payload['notes'] ?? ''}',
            electionId: '${mandate.payload['electionId'] ?? ''}',
          );
        }
      }
    }
    await CipaManagementService.saveMandate(
      id: current?.id,
      companyId: widget.companyId,
      title: title.text.trim(),
      start: start,
      end: end,
      status: status,
      notes: notes.text,
      electionId: '${current?.payload['electionId'] ?? ''}',
    );
    await _load(showLoading: false);
  }

  Future<void> _editMember([SstRecord? current]) async {
    final mandate = activeMandate;
    if (mandate == null) {
      _message('Cadastre ou ative um mandato antes de incluir membros.');
      return;
    }
    var workerId = '${current?.payload['workerId'] ?? ''}';
    if (workerId.isEmpty && workers.isNotEmpty) workerId = workers.first.id;
    var cipaRole = '${current?.payload['cipaRole'] ?? 'Titular'}';
    var representation =
        '${current?.payload['representation'] ?? 'Empregados'}';
    var status = current?.status ?? 'Ativo';
    var entryDate = current?.date ?? mandate.date;
    DateTime? exitDate = current?.dueDate;
    final absences = TextEditingController(
      text: '${current?.payload['absences'] ?? 0}',
    );
    final notes = TextEditingController(
      text: '${current?.payload['notes'] ?? ''}',
    );

    final save = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
          title: Text(current == null ? 'Adicionar membro' : 'Editar membro'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                DropdownButtonFormField<String>(
                  value: workers.any((w) => w.id == workerId) ? workerId : null,
                  isExpanded: true,
                  decoration: const InputDecoration(labelText: 'Colaborador'),
                  items: workers
                      .where((w) => w.active)
                      .map(
                        (w) => DropdownMenuItem(
                          value: w.id,
                          child: Text(w.name),
                        ),
                      )
                      .toList(),
                  onChanged: (value) {
                    if (value != null) setLocal(() => workerId = value);
                  },
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  value: cipaRole,
                  decoration: const InputDecoration(labelText: 'Função na CIPA'),
                  items: const [
                    DropdownMenuItem(value: 'Presidente', child: Text('Presidente')),
                    DropdownMenuItem(value: 'Vice-presidente', child: Text('Vice-presidente')),
                    DropdownMenuItem(value: 'Titular', child: Text('Titular')),
                    DropdownMenuItem(value: 'Suplente', child: Text('Suplente')),
                    DropdownMenuItem(value: 'Secretário', child: Text('Secretário')),
                    DropdownMenuItem(value: 'Membro designado', child: Text('Membro designado')),
                  ],
                  onChanged: (value) {
                    if (value != null) setLocal(() => cipaRole = value);
                  },
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  value: representation,
                  decoration: const InputDecoration(labelText: 'Representação'),
                  items: const [
                    DropdownMenuItem(value: 'Empregador', child: Text('Empregador')),
                    DropdownMenuItem(value: 'Empregados', child: Text('Empregados')),
                    DropdownMenuItem(value: 'Designado', child: Text('Designado')),
                  ],
                  onChanged: (value) {
                    if (value != null) setLocal(() => representation = value);
                  },
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  value: status,
                  decoration: const InputDecoration(labelText: 'Situação'),
                  items: const [
                    DropdownMenuItem(value: 'Ativo', child: Text('Ativo')),
                    DropdownMenuItem(value: 'Afastado', child: Text('Afastado')),
                    DropdownMenuItem(value: 'Substituído', child: Text('Substituído')),
                    DropdownMenuItem(value: 'Encerrado', child: Text('Encerrado')),
                  ],
                  onChanged: (value) {
                    if (value != null) setLocal(() => status = value);
                  },
                ),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Entrada'),
                  subtitle: Text(_date.format(entryDate)),
                  onTap: () async {
                    final picked = await _pickDate(entryDate);
                    if (picked != null) setLocal(() => entryDate = picked);
                  },
                ),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Saída'),
                  subtitle: Text(
                    exitDate == null ? 'Não informada' : _date.format(exitDate!),
                  ),
                  trailing: exitDate == null
                      ? const Icon(Icons.add_outlined)
                      : IconButton(
                          onPressed: () => setLocal(() => exitDate = null),
                          icon: const Icon(Icons.clear),
                        ),
                  onTap: () async {
                    final picked =
                        await _pickDate(exitDate ?? DateTime.now());
                    if (picked != null) setLocal(() => exitDate = picked);
                  },
                ),
                TextField(
                  controller: absences,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'Faltas registradas'),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: notes,
                  maxLines: 3,
                  decoration: const InputDecoration(
                    labelText: 'Substituições / observações',
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('Salvar'),
            ),
          ],
        ),
      ),
    );
    if (save != true) return;
    final worker = _workerById(workerId);
    if (worker == null) {
      _message('Selecione um colaborador.');
      return;
    }
    await CipaManagementService.saveMember(
      id: current?.id,
      companyId: widget.companyId,
      mandateId: mandate.id,
      workerId: worker.id,
      name: worker.name,
      cipaRole: cipaRole,
      representation: representation,
      entryDate: entryDate,
      exitDate: exitDate,
      status: status,
      absences: int.tryParse(absences.text.trim()) ?? 0,
      notes: notes.text,
    );
    await _load(showLoading: false);
  }

  Future<void> _editMeeting([SstRecord? current]) async {
    final mandate = activeMandate;
    if (mandate == null) {
      _message('Cadastre ou ative um mandato antes de criar reuniões.');
      return;
    }
    final title = TextEditingController(
      text: current?.title ?? 'Reunião ordinária da CIPA',
    );
    final place = TextEditingController(
      text: '${current?.payload['place'] ?? ''}',
    );
    final agenda = TextEditingController(
      text: '${current?.payload['agenda'] ?? ''}',
    );
    final subjects = TextEditingController(
      text: '${current?.payload['subjects'] ?? ''}',
    );
    final decisions = TextEditingController(
      text: '${current?.payload['decisions'] ?? ''}',
    );
    var kind = '${current?.payload['meetingKind'] ?? 'Ordinária'}';
    var status = current?.status ?? 'Agendada';
    var when = current?.date ?? DateTime.now().add(const Duration(days: 7));
    final memberIds = (current?.payload['memberIds'] as List?)
            ?.map((e) => '$e')
            .toSet() ??
        activeMembers.map((e) => e.id).toSet();
    final presentIds = (current?.payload['presentIds'] as List?)
            ?.map((e) => '$e')
            .toSet() ??
        <String>{};

    final save = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
          title: Text(current == null ? 'Nova reunião' : 'Editar reunião'),
          content: SingleChildScrollView(
            child: SizedBox(
              width: 520,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(
                    controller: title,
                    decoration: const InputDecoration(labelText: 'Título'),
                  ),
                  const SizedBox(height: 10),
                  DropdownButtonFormField<String>(
                    value: kind,
                    decoration: const InputDecoration(labelText: 'Tipo'),
                    items: const [
                      DropdownMenuItem(value: 'Ordinária', child: Text('Ordinária')),
                      DropdownMenuItem(value: 'Extraordinária', child: Text('Extraordinária')),
                    ],
                    onChanged: (value) {
                      if (value != null) setLocal(() => kind = value);
                    },
                  ),
                  const SizedBox(height: 10),
                  DropdownButtonFormField<String>(
                    value: status,
                    decoration: const InputDecoration(labelText: 'Situação'),
                    items: const [
                      DropdownMenuItem(value: 'Agendada', child: Text('Agendada')),
                      DropdownMenuItem(value: 'Realizada', child: Text('Realizada')),
                      DropdownMenuItem(value: 'Cancelada', child: Text('Cancelada')),
                    ],
                    onChanged: (value) {
                      if (value != null) setLocal(() => status = value);
                    },
                  ),
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Data e horário'),
                    subtitle: Text(_dateTime.format(when)),
                    trailing: const Icon(Icons.schedule_outlined),
                    onTap: () async {
                      final picked = await _pickDateTime(when);
                      if (picked != null) setLocal(() => when = picked);
                    },
                  ),
                  TextField(
                    controller: place,
                    decoration: const InputDecoration(labelText: 'Local'),
                  ),
                  const SizedBox(height: 10),
                  TextField(
                    controller: agenda,
                    maxLines: 3,
                    decoration: const InputDecoration(labelText: 'Pauta'),
                  ),
                  const SizedBox(height: 10),
                  TextField(
                    controller: subjects,
                    maxLines: 3,
                    decoration: const InputDecoration(
                      labelText: 'Assuntos discutidos',
                    ),
                  ),
                  const SizedBox(height: 10),
                  TextField(
                    controller: decisions,
                    maxLines: 4,
                    decoration: const InputDecoration(
                      labelText: 'Decisões tomadas',
                    ),
                  ),
                  const SizedBox(height: 12),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      'Participantes e presença',
                      style: Theme.of(context).textTheme.titleSmall,
                    ),
                  ),
                  ...activeMembers.map(
                    (member) => CheckboxListTile(
                      contentPadding: EdgeInsets.zero,
                      value: memberIds.contains(member.id),
                      title: Text(_memberLabel(member.id)),
                      subtitle: memberIds.contains(member.id)
                          ? Text(
                              presentIds.contains(member.id)
                                  ? 'Presente'
                                  : 'Ausente / não confirmado',
                            )
                          : null,
                      secondary: memberIds.contains(member.id)
                          ? IconButton(
                              tooltip: presentIds.contains(member.id)
                                  ? 'Marcar ausente'
                                  : 'Marcar presente',
                              onPressed: () {
                                setLocal(() {
                                  if (presentIds.contains(member.id)) {
                                    presentIds.remove(member.id);
                                  } else {
                                    presentIds.add(member.id);
                                  }
                                });
                              },
                              icon: Icon(
                                presentIds.contains(member.id)
                                    ? Icons.check_circle
                                    : Icons.radio_button_unchecked,
                                color: presentIds.contains(member.id)
                                    ? AuditarBrand.greenDark
                                    : null,
                              ),
                            )
                          : null,
                      onChanged: (checked) {
                        setLocal(() {
                          if (checked == true) {
                            memberIds.add(member.id);
                          } else {
                            memberIds.remove(member.id);
                            presentIds.remove(member.id);
                          }
                        });
                      },
                    ),
                  ),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('Salvar'),
            ),
          ],
        ),
      ),
    );
    if (save != true) return;
    if (title.text.trim().isEmpty) {
      _message('Informe o título da reunião.');
      return;
    }
    await CipaManagementService.saveMeeting(
      id: current?.id,
      companyId: widget.companyId,
      mandateId: mandate.id,
      title: title.text,
      dateTime: when,
      meetingKind: kind,
      place: place.text,
      agenda: agenda.text,
      subjects: subjects.text,
      decisions: decisions.text,
      memberIds: memberIds.toList(),
      presentIds: presentIds.toList(),
      status: status,
    );
    await _load(showLoading: false);
  }

  Future<void> _generateMinutes(SstRecord meeting) async {
    final mandate = activeMandate;
    if (mandate == null) return;
    final invited = (meeting.payload['memberIds'] as List?)
            ?.map((e) => '$e')
            .toList() ??
        const <String>[];
    final present = (meeting.payload['presentIds'] as List?)
            ?.map((e) => '$e')
            .toSet() ??
        <String>{};
    final presentNames =
        invited.where(present.contains).map(_memberLabel).toList();
    final absentNames =
        invited.where((id) => !present.contains(id)).map(_memberLabel).toList();
    final content = [
      'ATA DA ${meeting.payload['meetingKind'] ?? 'REUNIÃO'} DA CIPA',
      '',
      'Empresa: ${company?.name ?? ''}',
      'Mandato: ${mandate.title}',
      'Data: ${_dateTime.format(meeting.date)}',
      'Local: ${meeting.payload['place'] ?? ''}',
      '',
      'Presentes: ${presentNames.isEmpty ? 'Não informado' : presentNames.join(', ')}',
      'Ausentes: ${absentNames.isEmpty ? 'Nenhum registrado' : absentNames.join(', ')}',
      '',
      'Pauta:',
      '${meeting.payload['agenda'] ?? ''}',
      '',
      'Assuntos discutidos:',
      '${meeting.payload['subjects'] ?? ''}',
      '',
      'Decisões tomadas:',
      '${meeting.payload['decisions'] ?? ''}',
    ].join('\n');

    final existing = mandateMinutes
        .where((a) => '${a.payload['meetingId'] ?? ''}' == meeting.id)
        .toList();
    await CipaManagementService.saveMinutes(
      id: null,
      companyId: widget.companyId,
      mandateId: mandate.id,
      meetingId: meeting.id,
      title: 'Ata • ${meeting.title}',
      date: meeting.date,
      content: content,
      status: 'Rascunho',
      version: existing.isEmpty
          ? 1
          : ((existing.first.payload['version'] as num?)?.toInt() ?? 1) + 1,
    );
    await _load(showLoading: false);
    _message('Ata gerada e vinculada à reunião.');
  }

  Future<void> _editAction({
    SstRecord? current,
    String meetingId = '',
  }) async {
    final mandate = activeMandate;
    if (mandate == null) {
      _message('Cadastre ou ative um mandato antes de criar ações.');
      return;
    }
    final title = TextEditingController(text: current?.title ?? '');
    final description = TextEditingController(
      text: '${current?.payload['description'] ?? ''}',
    );
    final responsible = TextEditingController(
      text: '${current?.payload['responsible'] ?? ''}',
    );
    final notes = TextEditingController(
      text: '${current?.payload['notes'] ?? ''}',
    );
    var due = current?.dueDate ?? DateTime.now().add(const Duration(days: 7));
    var priority = current?.priority ?? 'Média';
    var status = current?.status ?? 'Aberta';

    final save = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
          title: Text(current == null ? 'Nova ação da CIPA' : 'Editar ação'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: title,
                  decoration: const InputDecoration(labelText: 'Ação / título'),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: description,
                  maxLines: 3,
                  decoration: const InputDecoration(labelText: 'Descrição'),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: responsible,
                  decoration: const InputDecoration(labelText: 'Responsável'),
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  value: priority,
                  decoration: const InputDecoration(labelText: 'Prioridade'),
                  items: const [
                    DropdownMenuItem(value: 'Baixa', child: Text('Baixa')),
                    DropdownMenuItem(value: 'Média', child: Text('Média')),
                    DropdownMenuItem(value: 'Alta', child: Text('Alta')),
                    DropdownMenuItem(value: 'Crítica', child: Text('Crítica')),
                  ],
                  onChanged: (value) {
                    if (value != null) setLocal(() => priority = value);
                  },
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  value: status,
                  decoration: const InputDecoration(labelText: 'Status'),
                  items: const [
                    DropdownMenuItem(value: 'Aberta', child: Text('Aberta')),
                    DropdownMenuItem(value: 'Em andamento', child: Text('Em andamento')),
                    DropdownMenuItem(value: 'Resolvida', child: Text('Resolvida')),
                    DropdownMenuItem(value: 'Vencida', child: Text('Vencida')),
                  ],
                  onChanged: (value) {
                    if (value != null) setLocal(() => status = value);
                  },
                ),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Prazo'),
                  subtitle: Text(_date.format(due)),
                  onTap: () async {
                    final picked = await _pickDate(due);
                    if (picked != null) setLocal(() => due = picked);
                  },
                ),
                TextField(
                  controller: notes,
                  maxLines: 3,
                  decoration: const InputDecoration(
                    labelText: 'Orientação / observações',
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('Salvar'),
            ),
          ],
        ),
      ),
    );
    if (save != true) return;
    if (title.text.trim().isEmpty) {
      _message('Informe a ação.');
      return;
    }
    await CipaManagementService.saveAction(
      id: current?.id,
      companyId: widget.companyId,
      mandateId: mandate.id,
      meetingId: meetingId.isNotEmpty
          ? meetingId
          : '${current?.payload['meetingId'] ?? ''}',
      title: title.text,
      description: description.text,
      responsible: responsible.text,
      createdAt: current?.date ?? DateTime.now(),
      dueDate: due,
      priority: priority,
      status: status,
      ncId: '${current?.payload['ncId'] ?? ''}',
      notes: notes.text,
    );
    await _load(showLoading: false);
  }

  Future<void> _createNc(SstRecord action) async {
    final currentCompany = company;
    if (currentCompany == null) return;
    final existing = '${action.payload['ncId'] ?? ''}'.trim();
    if (existing.isNotEmpty) {
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => NonConformityDetailScreen(ncId: existing),
        ),
      );
      await _load(showLoading: false);
      return;
    }
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Criar não conformidade'),
        content: const Text(
          'Será criada uma NC real no módulo de Não Conformidades, vinculada a esta ação da CIPA.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Criar NC'),
          ),
        ],
      ),
    );
    if (confirm != true) return;
    final id = await CipaManagementService.createNcFromAction(
      companyId: widget.companyId,
      companyName: currentCompany.name,
      action: action,
    );
    await _load(showLoading: false);
    if (!mounted) return;
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => NonConformityDetailScreen(ncId: id),
      ),
    );
    await _load(showLoading: false);
  }

  Future<void> _editCommitteeMember([SstRecord? current]) async {
    var workerId = '${current?.payload['workerId'] ?? ''}';
    if (workerId.isEmpty && workers.isNotEmpty) workerId = workers.first.id;
    var function = '${current?.payload['function'] ?? 'Membro'}';
    final notes = TextEditingController(
      text: '${current?.payload['notes'] ?? ''}',
    );
    final electionId = '${current?.payload['electionId'] ?? ''}'.isNotEmpty
        ? '${current?.payload['electionId'] ?? ''}'
        : (elections.isEmpty ? '' : elections.first.id);

    final save = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
          title: Text(
            current == null ? 'Adicionar à comissão eleitoral' : 'Editar comissão eleitoral',
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                DropdownButtonFormField<String>(
                  value: workers.any((w) => w.id == workerId) ? workerId : null,
                  isExpanded: true,
                  decoration: const InputDecoration(labelText: 'Colaborador'),
                  items: workers
                      .where((w) => w.active)
                      .map(
                        (w) => DropdownMenuItem(
                          value: w.id,
                          child: Text(w.name),
                        ),
                      )
                      .toList(),
                  onChanged: (value) {
                    if (value != null) setLocal(() => workerId = value);
                  },
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  value: function,
                  decoration: const InputDecoration(
                    labelText: 'Função na comissão',
                  ),
                  items: const [
                    DropdownMenuItem(value: 'Presidente', child: Text('Presidente')),
                    DropdownMenuItem(value: 'Secretário', child: Text('Secretário')),
                    DropdownMenuItem(value: 'Membro', child: Text('Membro')),
                  ],
                  onChanged: (value) {
                    if (value != null) setLocal(() => function = value);
                  },
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: notes,
                  maxLines: 3,
                  decoration: const InputDecoration(labelText: 'Observações'),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('Salvar'),
            ),
          ],
        ),
      ),
    );
    if (save != true) return;
    final worker = _workerById(workerId);
    if (worker == null) {
      _message('Selecione um colaborador.');
      return;
    }
    await CipaManagementService.saveCommitteeMember(
      id: current?.id,
      companyId: widget.companyId,
      workerId: worker.id,
      name: worker.name,
      function: function,
      electionId: electionId,
      notes: notes.text,
    );
    if (mounted) setState(() {});
  }

  Future<void> _addDocument() async {
    final mandate = activeMandate;
    if (mandate == null) {
      _message('Cadastre ou ative um mandato antes de adicionar documentos.');
      return;
    }
    final title = TextEditingController();
    final notes = TextEditingController();
    var category = 'Outros';
    var requiredDocument = false;

    final save = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
          title: const Text('Novo documento da CIPA'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: title,
                  decoration: const InputDecoration(labelText: 'Título'),
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  value: category,
                  decoration: const InputDecoration(labelText: 'Categoria'),
                  items: const [
                    DropdownMenuItem(value: 'Edital', child: Text('Edital')),
                    DropdownMenuItem(value: 'Ata', child: Text('Ata')),
                    DropdownMenuItem(value: 'Lista de presença', child: Text('Lista de presença')),
                    DropdownMenuItem(value: 'Certificado', child: Text('Certificado')),
                    DropdownMenuItem(value: 'Documento eleitoral', child: Text('Documento eleitoral')),
                    DropdownMenuItem(value: 'Ata de eleição', child: Text('Ata de eleição')),
                    DropdownMenuItem(value: 'Ata de posse', child: Text('Ata de posse')),
                    DropdownMenuItem(value: 'Outros', child: Text('Outros')),
                  ],
                  onChanged: (value) {
                    if (value != null) setLocal(() => category = value);
                  },
                ),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Documento obrigatório'),
                  value: requiredDocument,
                  onChanged: (value) =>
                      setLocal(() => requiredDocument = value),
                ),
                TextField(
                  controller: notes,
                  maxLines: 3,
                  decoration: const InputDecoration(labelText: 'Observações'),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('Continuar'),
            ),
          ],
        ),
      ),
    );
    if (save != true || title.text.trim().isEmpty) return;

    final docId = 'cipa-doc-${DateTime.now().microsecondsSinceEpoch}';
    await CipaManagementService.saveDocument(
      id: docId,
      companyId: widget.companyId,
      mandateId: mandate.id,
      title: title.text,
      category: category,
      date: DateTime.now(),
      requiredDocument: requiredDocument,
      status: 'Pendente de anexo',
      notes: notes.text,
    );
    final picked = await FilePicker.platform.pickFiles(
      withData: true,
      allowedExtensions: const ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'],
      type: FileType.custom,
    );
    if (picked != null && picked.files.isNotEmpty) {
      await CipaManagementService.registerAttachment(
        companyId: widget.companyId,
        entityType: 'cipa_document',
        entityId: docId,
        picked: picked.files.first,
      );
      await CipaManagementService.saveDocument(
        id: docId,
        companyId: widget.companyId,
        mandateId: mandate.id,
        title: title.text,
        category: category,
        date: DateTime.now(),
        requiredDocument: requiredDocument,
        status: 'Arquivado',
        notes: notes.text,
      );
    }
    await _load(showLoading: false);
  }

  Future<void> _attachTo({
    required String entityType,
    required String entityId,
  }) async {
    final picked = await FilePicker.platform.pickFiles(
      withData: true,
      allowedExtensions: const ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'],
      type: FileType.custom,
    );
    if (picked == null || picked.files.isEmpty) return;
    await CipaManagementService.registerAttachment(
      companyId: widget.companyId,
      entityType: entityType,
      entityId: entityId,
      picked: picked.files.first,
    );
    _message('Arquivo anexado. O envio seguirá o fluxo de mídias já existente.');
    await _load(showLoading: false);
  }

  Future<void> _showAttachments({
    required String entityType,
    required String entityId,
  }) async {
    final rows = await CipaManagementService.attachments(
      entityType: entityType,
      entityId: entityId,
    );
    if (!mounted) return;
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (sheet) => SafeArea(
        child: SizedBox(
          height: MediaQuery.of(sheet).size.height * .65,
          child: rows.isEmpty
              ? const Center(child: Text('Nenhum anexo.'))
              : ListView.separated(
                  padding: const EdgeInsets.all(12),
                  itemCount: rows.length,
                  separatorBuilder: (_, __) => const Divider(height: 1),
                  itemBuilder: (context, index) {
                    final row = rows[index];
                    final path = '${row['local_path'] ?? ''}'.trim();
                    final name = '${row['file_name'] ?? 'Arquivo'}';
                    return ListTile(
                      leading: const Icon(Icons.attach_file_outlined),
                      title: Text(name),
                      subtitle: Text(
                        '${row['drive_file_id'] ?? ''}'.trim().isEmpty
                            ? 'Aguardando proteção online'
                            : 'Protegido no Drive',
                      ),
                      onTap: path.isEmpty
                          ? null
                          : () async {
                              final file = File(path);
                              if (await file.exists()) {
                                await Share.shareXFiles(
                                  [XFile(path)],
                                  text: name,
                                );
                              }
                            },
                    );
                  },
                ),
        ),
      ),
    );
  }

  Future<void> _importMinutesWithAi() async {
    final mandate = activeMandate;
    if (mandate == null) {
      _message('Cadastre ou ative um mandato antes de importar uma ata.');
      return;
    }
    final picked = await FilePicker.platform.pickFiles(
      withData: true,
      allowedExtensions: const ['pdf', 'jpg', 'jpeg', 'png'],
      type: FileType.custom,
    );
    if (picked == null || picked.files.isEmpty) return;
    final file = picked.files.first;
    final bytes = file.bytes ??
        (file.path == null ? null : await File(file.path!).readAsBytes());
    if (bytes == null) return;
    setState(() => busy = true);
    try {
      final result = await CipaManagementService.readMinutesWithAi(
        bytes: Uint8List.fromList(bytes),
        fileName: file.name,
        companyName: company?.name ?? '',
      );
      if (!mounted) return;
      final reviewed = await _reviewAiMinutes(result);
      if (reviewed == null) return;
      await CipaManagementService.saveMinutes(
        companyId: widget.companyId,
        mandateId: mandate.id,
        meetingId: '${reviewed['meetingId'] ?? ''}',
        title: '${reviewed['title'] ?? 'Ata importada por IA'}',
        date: reviewed['date'] as DateTime? ?? DateTime.now(),
        content: '${reviewed['content'] ?? ''}',
        status: 'Rascunho',
        version: 1,
        importedByAi: true,
      );
      await _load(showLoading: false);
      _message('Ata importada. Os dados foram salvos após sua conferência.');
    } catch (error) {
      _message('Não foi possível ler a ata com IA: $error');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<Map<String, dynamic>?> _reviewAiMinutes(
    Map<String, dynamic> raw,
  ) async {
    final dateText = '${raw['date'] ?? ''}'.trim();
    var parsedDate = DateTime.tryParse(dateText) ?? DateTime.now();
    final title = TextEditingController(
      text: '${raw['title'] ?? 'Ata da CIPA'}',
    );
    final content = TextEditingController(
      text: [
        if ('${raw['participants'] ?? ''}'.trim().isNotEmpty)
          'Participantes: ${_listText(raw['participants'])}',
        if ('${raw['subjects'] ?? ''}'.trim().isNotEmpty)
          'Assuntos: ${_listText(raw['subjects'])}',
        if ('${raw['decisions'] ?? ''}'.trim().isNotEmpty)
          'Decisões: ${_listText(raw['decisions'])}',
        if ('${raw['responsibles'] ?? ''}'.trim().isNotEmpty)
          'Responsáveis: ${_listText(raw['responsibles'])}',
        if ('${raw['deadlines'] ?? ''}'.trim().isNotEmpty)
          'Prazos: ${_listText(raw['deadlines'])}',
      ].join('\n\n'),
    );
    var meetingId = '';
    final selected = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
          title: const Text('Conferir leitura da IA'),
          content: SingleChildScrollView(
            child: SizedBox(
              width: 560,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(
                    controller: title,
                    decoration: const InputDecoration(labelText: 'Título'),
                  ),
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Data identificada'),
                    subtitle: Text(_date.format(parsedDate)),
                    onTap: () async {
                      final picked = await _pickDate(parsedDate);
                      if (picked != null) setLocal(() => parsedDate = picked);
                    },
                  ),
                  DropdownButtonFormField<String>(
                    value: meetingId.isEmpty ? null : meetingId,
                    isExpanded: true,
                    decoration: const InputDecoration(
                      labelText: 'Vincular à reunião',
                    ),
                    items: mandateMeetings
                        .map(
                          (m) => DropdownMenuItem(
                            value: m.id,
                            child: Text(
                              '${_date.format(m.date)} • ${m.title}',
                            ),
                          ),
                        )
                        .toList(),
                    onChanged: (value) =>
                        setLocal(() => meetingId = value ?? ''),
                  ),
                  const SizedBox(height: 10),
                  TextField(
                    controller: content,
                    maxLines: 12,
                    decoration: const InputDecoration(
                      labelText: 'Dados extraídos',
                      alignLabelWithHint: true,
                    ),
                  ),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('Confirmar e salvar'),
            ),
          ],
        ),
      ),
    );
    if (selected != true) return null;
    return {
      'title': title.text.trim(),
      'date': parsedDate,
      'meetingId': meetingId,
      'content': content.text.trim(),
    };
  }

  String _listText(dynamic value) {
    if (value is List) return value.map((e) => '$e').join('; ');
    return '$value';
  }

  Future<void> _shareMinutesPdf(SstRecord ata) async {
    final doc = pw.Document();
    doc.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(42),
        build: (_) => [
          pw.Text(
            ata.title,
            style: pw.TextStyle(
              fontSize: 18,
              fontWeight: pw.FontWeight.bold,
            ),
          ),
          pw.SizedBox(height: 6),
          pw.Text('Empresa: ${company?.name ?? ''}'),
          pw.Text('Data: ${_date.format(ata.date)}'),
          pw.SizedBox(height: 16),
          pw.Text('${ata.payload['content'] ?? ''}'),
        ],
      ),
    );
    await Printing.sharePdf(
      bytes: await doc.save(),
      filename: 'Ata_CIPA_${_date.format(ata.date).replaceAll('/', '-')}.pdf',
    );
  }

  Future<void> _shareDossier() async {
    final currentCompany = company;
    if (currentCompany == null) return;
    final mandate = activeMandate;
    final doc = pw.Document();
    final alertsNow = alerts;
    final trainingByWorker = <String, List<TrainingControl>>{};
    for (final training in trainings) {
      (trainingByWorker[training.workerId] ??= []).add(training);
    }

    doc.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(36),
        build: (_) => [
          pw.Text(
            'Dossiê CIPA',
            style: pw.TextStyle(
              fontSize: 22,
              fontWeight: pw.FontWeight.bold,
            ),
          ),
          pw.SizedBox(height: 4),
          pw.Text('Empresa: ${currentCompany.name}'),
          pw.Text('Mandato: ${mandate?.title ?? 'Não informado'}'),
          if (mandate != null)
            pw.Text(
              'Período: ${_date.format(mandate.date)} a ${mandate.dueDate == null ? '-' : _date.format(mandate.dueDate!)}',
            ),
          pw.SizedBox(height: 18),
          _pdfHeading('Situação atual'),
          if (alertsNow.isEmpty)
            pw.Text('Sem alertas relevantes.')
          else
            ...alertsNow.map((a) => pw.Bullet(text: a)),
          pw.SizedBox(height: 14),
          _pdfHeading('Membros'),
          ...activeMembers.map(
            (m) => pw.Text(
              '• ${m.title} — ${m.payload['cipaRole'] ?? ''} — ${m.payload['representation'] ?? ''}',
            ),
          ),
          pw.SizedBox(height: 14),
          _pdfHeading('Reuniões'),
          ...mandateMeetings.map(
            (m) => pw.Text(
              '• ${_dateTime.format(m.date)} — ${m.title} — ${m.status}',
            ),
          ),
          pw.SizedBox(height: 14),
          _pdfHeading('Atas'),
          ...mandateMinutes.map(
            (a) => pw.Text(
              '• ${_date.format(a.date)} — ${a.title} — ${a.status}',
            ),
          ),
          pw.SizedBox(height: 14),
          _pdfHeading('Treinamentos dos membros'),
          ...activeMembers.map((m) {
            final workerId = '${m.payload['workerId'] ?? ''}';
            final rows = (trainingByWorker[workerId] ?? [])
                .where(CipaManagementService.isCipaTraining)
                .toList();
            return pw.Text(
              '• ${m.title}: ${rows.isEmpty ? 'Pendente' : rows.map((t) => '${t.code} ${t.title}').join(', ')}',
            );
          }),
          pw.SizedBox(height: 14),
          _pdfHeading('Ações e não conformidades'),
          ...mandateActions.map(
            (a) => pw.Text(
              '• ${a.title} — ${a.status} — Resp.: ${a.payload['responsible'] ?? '-'} — NC: ${'${a.payload['ncId'] ?? ''}'.trim().isEmpty ? 'não vinculada' : a.payload['ncId']}',
            ),
          ),
          pw.SizedBox(height: 14),
          _pdfHeading('Documentos'),
          ...mandateDocuments.map(
            (d) => pw.Text(
              '• ${d.payload['category'] ?? 'Documento'} — ${d.title} — ${d.status}',
            ),
          ),
        ],
      ),
    );
    await Printing.sharePdf(
      bytes: await doc.save(),
      filename: 'Dossie_CIPA_${currentCompany.name.replaceAll(' ', '_')}.pdf',
    );
  }

  pw.Widget _pdfHeading(String text) => pw.Text(
        text,
        style: pw.TextStyle(
          fontSize: 14,
          fontWeight: pw.FontWeight.bold,
        ),
      );

  Widget _metric(String label, String value, IconData icon, {Color? color}) {
    final tone = color ?? AuditarBrand.navy;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(13),
        child: Row(
          children: [
            CircleAvatar(
              backgroundColor: tone.withValues(alpha: .12),
              foregroundColor: tone,
              child: Icon(icon),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    value,
                    style: const TextStyle(
                      fontSize: 21,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  Text(label, style: const TextStyle(fontSize: 12)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _panelTab() {
    final realized = mandateMeetings.where((m) => m.status == 'Realizada').length;
    final pending = mandateMeetings.length - realized;
    final openActions = mandateActions
        .where((a) => a.status != 'Resolvida')
        .length;

    return RefreshIndicator(
      onRefresh: () => _load(showLoading: false),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(12, 12, 12, 90),
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [AuditarBrand.navy, AuditarBrand.navyDark],
              ),
              borderRadius: BorderRadius.circular(18),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Gestão da CIPA',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 20,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  company?.name ?? '',
                  style: const TextStyle(color: Colors.white70),
                ),
                const SizedBox(height: 12),
                Text(
                  activeMandate == null
                      ? 'Nenhum mandato ativo'
                      : '${activeMandate!.title} • ${_date.format(activeMandate!.date)} a ${activeMandate!.dueDate == null ? '-' : _date.format(activeMandate!.dueDate!)}',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                if (nextMeeting != null) ...[
                  const SizedBox(height: 5),
                  Text(
                    'Próxima reunião: ${_dateTime.format(nextMeeting!.date)}',
                    style: const TextStyle(color: Colors.white70),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 10),
          GridView.count(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisCount: MediaQuery.of(context).size.width > 760 ? 4 : 2,
            childAspectRatio: 1.65,
            crossAxisSpacing: 8,
            mainAxisSpacing: 8,
            children: [
              _metric('Membros ativos', '${activeMembers.length}', Icons.groups_outlined),
              _metric('Reuniões realizadas', '$realized', Icons.event_available_outlined),
              _metric('Reuniões pendentes', '$pending', Icons.event_busy_outlined),
              _metric('Atas pendentes', '$pendingMinutesCount', Icons.description_outlined),
              _metric('Treinamentos pendentes', '$pendingTrainingCount', Icons.school_outlined),
              _metric('Ações abertas', '$openActions', Icons.task_alt_outlined),
              _metric(
                'Ações vencidas',
                '$overdueActionsCount',
                Icons.warning_amber_rounded,
                color: overdueActionsCount > 0 ? Colors.red : AuditarBrand.greenDark,
              ),
              _metric('Eleições registradas', '${elections.length}', Icons.how_to_vote_outlined),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              const Expanded(
                child: Text(
                  'Alertas importantes',
                  style: TextStyle(
                    fontWeight: FontWeight.w900,
                    fontSize: 16,
                  ),
                ),
              ),
              TextButton.icon(
                onPressed: _shareDossier,
                icon: const Icon(Icons.picture_as_pdf_outlined),
                label: const Text('Dossiê CIPA'),
              ),
            ],
          ),
          if (alerts.isEmpty)
            const Card(
              child: ListTile(
                leading: Icon(Icons.check_circle_outline, color: Colors.green),
                title: Text('Nenhum alerta crítico no momento.'),
              ),
            )
          else
            ...alerts.map(
              (alert) => Card(
                child: ListTile(
                  leading: const Icon(
                    Icons.notifications_active_outlined,
                    color: Color(0xFFF29D18),
                  ),
                  title: Text(alert),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _mandateTab() => _standardList(
        title: 'Mandato atual',
        addLabel: 'Novo mandato',
        onAdd: () => _editMandate(),
        items: mandates,
        itemBuilder: (item) => ListTile(
          leading: Icon(
            item.status == 'Ativo'
                ? Icons.verified_outlined
                : Icons.history_outlined,
          ),
          title: Text(
            item.title,
            style: const TextStyle(fontWeight: FontWeight.w800),
          ),
          subtitle: Text(
            '${_date.format(item.date)} a ${item.dueDate == null ? '-' : _date.format(item.dueDate!)} • ${item.status}',
          ),
          onTap: () => _editMandate(item),
        ),
      );

  Widget _membersTab() => _standardList(
        title: 'Membros da CIPA',
        addLabel: 'Adicionar membro',
        onAdd: () => _editMember(),
        items: activeMembers,
        itemBuilder: (item) => ListTile(
          leading: const CircleAvatar(child: Icon(Icons.person_outline)),
          title: Text(
            item.title,
            style: const TextStyle(fontWeight: FontWeight.w800),
          ),
          subtitle: Text(
            '${item.payload['cipaRole'] ?? ''} • ${item.payload['representation'] ?? ''}\n'
            'Faltas: ${item.payload['absences'] ?? 0} • ${item.status}',
          ),
          isThreeLine: true,
          onTap: () => _editMember(item),
        ),
      );

  Widget _meetingsTab() => _standardList(
        title: 'Calendário e reuniões',
        addLabel: 'Nova reunião',
        onAdd: () => _editMeeting(),
        items: mandateMeetings,
        itemBuilder: (item) {
          final late = item.status == 'Agendada' && item.date.isBefore(DateTime.now());
          return Card(
            margin: const EdgeInsets.only(bottom: 8),
            child: Column(
              children: [
                ListTile(
                  leading: CircleAvatar(
                    child: Icon(
                      item.status == 'Realizada'
                          ? Icons.event_available_outlined
                          : Icons.event_outlined,
                    ),
                  ),
                  title: Text(
                    item.title,
                    style: const TextStyle(fontWeight: FontWeight.w800),
                  ),
                  subtitle: Text(
                    '${_dateTime.format(item.date)} • ${item.payload['meetingKind'] ?? ''} • ${late ? 'Atrasada' : item.status}\n'
                    '${item.payload['place'] ?? ''}',
                  ),
                  isThreeLine: true,
                  onTap: () => _editMeeting(item),
                ),
                ButtonBar(
                  children: [
                    TextButton.icon(
                      onPressed: () => _generateMinutes(item),
                      icon: const Icon(Icons.description_outlined),
                      label: const Text('Gerar ata'),
                    ),
                    TextButton.icon(
                      onPressed: () => _editAction(meetingId: item.id),
                      icon: const Icon(Icons.add_task_outlined),
                      label: const Text('Criar ação'),
                    ),
                  ],
                ),
              ],
            ),
          );
        },
      );

  Widget _minutesTab() => _standardList(
        title: 'Atas',
        addLabel: 'Ler ata com IA',
        onAdd: busy ? null : _importMinutesWithAi,
        items: mandateMinutes,
        itemBuilder: (item) => Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: Column(
            children: [
              ListTile(
                leading: const Icon(Icons.description_outlined),
                title: Text(
                  item.title,
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
                subtitle: Text(
                  '${_date.format(item.date)} • v${item.payload['version'] ?? 1} • ${item.status}',
                ),
              ),
              ButtonBar(
                children: [
                  TextButton(
                    onPressed: () => _shareMinutesPdf(item),
                    child: const Text('PDF'),
                  ),
                  TextButton(
                    onPressed: () => _attachTo(
                      entityType: 'cipa_minutes',
                      entityId: item.id,
                    ),
                    child: const Text('Anexar assinada'),
                  ),
                  TextButton(
                    onPressed: () => _showAttachments(
                      entityType: 'cipa_minutes',
                      entityId: item.id,
                    ),
                    child: const Text('Anexos'),
                  ),
                ],
              ),
            ],
          ),
        ),
      );

  Widget _actionsTab() => _standardList(
        title: 'Plano de ação da CIPA',
        addLabel: 'Nova ação',
        onAdd: () => _editAction(),
        items: mandateActions,
        itemBuilder: (item) {
          final overdue = CipaManagementService.isOverdue(item);
          final ncId = '${item.payload['ncId'] ?? ''}'.trim();
          return Card(
            margin: const EdgeInsets.only(bottom: 8),
            child: Column(
              children: [
                ListTile(
                  leading: CircleAvatar(
                    backgroundColor:
                        (overdue ? Colors.red : AuditarBrand.navy)
                            .withValues(alpha: .12),
                    child: Icon(
                      overdue ? Icons.warning_amber : Icons.task_alt_outlined,
                      color: overdue ? Colors.red : AuditarBrand.navy,
                    ),
                  ),
                  title: Text(
                    item.title,
                    style: const TextStyle(fontWeight: FontWeight.w800),
                  ),
                  subtitle: Text(
                    'Responsável: ${item.payload['responsible'] ?? '-'}\n'
                    'Prazo: ${item.dueDate == null ? '-' : _date.format(item.dueDate!)} • ${overdue ? 'Vencida' : item.status} • ${item.priority}',
                  ),
                  isThreeLine: true,
                  onTap: () => _editAction(current: item),
                ),
                ButtonBar(
                  children: [
                    TextButton.icon(
                      onPressed: () => _attachTo(
                        entityType: 'cipa_action',
                        entityId: item.id,
                      ),
                      icon: const Icon(Icons.photo_camera_outlined),
                      label: const Text('Evidência'),
                    ),
                    TextButton.icon(
                      onPressed: () => _createNc(item),
                      icon: const Icon(Icons.report_problem_outlined),
                      label: Text(ncId.isEmpty ? 'Criar NC' : 'Abrir NC'),
                    ),
                  ],
                ),
              ],
            ),
          );
        },
      );

  Widget _electionTab() => ListView(
        padding: const EdgeInsets.fromLTRB(12, 12, 12, 90),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                children: [
                  const Icon(
                    Icons.how_to_vote_outlined,
                    size: 48,
                    color: AuditarBrand.navy,
                  ),
                  const SizedBox(height: 10),
                  const Text(
                    'Processo eleitoral da CIPA',
                    style: TextStyle(fontWeight: FontWeight.w900, fontSize: 17),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Controle candidatos, comissão eleitoral, votação, resultado e documentos. O processo eleitoral que já existia no Auditar foi preservado.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.grey.shade700),
                  ),
                  const SizedBox(height: 14),
                  FilledButton.icon(
                    onPressed: () async {
                      await Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => CipaScreen(
                            companyId: widget.companyId,
                          ),
                        ),
                      );
                      await _load(showLoading: false);
                    },
                    icon: const Icon(Icons.how_to_vote),
                    label: const Text('Abrir gestão eleitoral'),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 10),
          FutureBuilder<List<SstRecord>>(
            future: CipaManagementService.records(
              CipaManagementService.committeeType,
              widget.companyId,
            ),
            builder: (context, snapshot) {
              final rows = snapshot.data ?? const <SstRecord>[];
              return Card(
                child: Column(
                  children: [
                    ListTile(
                      leading: const Icon(Icons.groups_2_outlined),
                      title: const Text(
                        'Comissão eleitoral',
                        style: TextStyle(fontWeight: FontWeight.w800),
                      ),
                      subtitle: Text(
                        rows.isEmpty
                            ? 'Nenhum integrante cadastrado'
                            : '${rows.length} integrante(s) cadastrado(s)',
                      ),
                      trailing: IconButton(
                        tooltip: 'Adicionar integrante',
                        onPressed: () => _editCommitteeMember(),
                        icon: const Icon(Icons.person_add_alt_1_outlined),
                      ),
                    ),
                    if (rows.isNotEmpty)
                      ...rows.map(
                        (row) => ListTile(
                          dense: true,
                          leading: const Icon(Icons.person_outline),
                          title: Text(row.title),
                          subtitle: Text(
                            '${row.payload['function'] ?? 'Membro'}',
                          ),
                          onTap: () => _editCommitteeMember(row),
                        ),
                      ),
                  ],
                ),
              );
            },
          ),
          const SizedBox(height: 10),
          ...elections.map(
            (e) => Card(
              child: ListTile(
                leading: const Icon(Icons.ballot_outlined),
                title: Text(e.title),
                subtitle: Text(
                  '${e.managementPeriod} • ${e.status}',
                ),
              ),
            ),
          ),
        ],
      );

  Widget _trainingTab() {
    final byWorker = <String, List<TrainingControl>>{};
    for (final training in trainings) {
      (byWorker[training.workerId] ??= []).add(training);
    }
    return ListView(
      padding: const EdgeInsets.fromLTRB(12, 12, 12, 90),
      children: [
        Card(
          child: ListTile(
            leading: const Icon(Icons.school_outlined),
            title: const Text('Treinamentos da CIPA'),
            subtitle: const Text(
              'O módulo usa os treinamentos já cadastrados no Auditar. São considerados registros contendo CIPA, NR 5 ou NR 05.',
            ),
            trailing: FilledButton(
              onPressed: () async {
                await Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) =>
                        TrainingsScreen(companyId: widget.companyId),
                  ),
                );
                await _load(showLoading: false);
              },
              child: const Text('Gerenciar'),
            ),
          ),
        ),
        const SizedBox(height: 8),
        ...activeMembers.map((member) {
          final workerId = '${member.payload['workerId'] ?? ''}';
          final rows = (byWorker[workerId] ?? [])
              .where(CipaManagementService.isCipaTraining)
              .toList();
          rows.sort(
            (a, b) => (b.trainingDate ?? DateTime(2000))
                .compareTo(a.trainingDate ?? DateTime(2000)),
          );
          final latest = rows.isEmpty ? null : rows.first;
          return Card(
            child: ListTile(
              leading: Icon(
                latest == null ? Icons.error_outline : Icons.verified_outlined,
                color: latest == null ? Colors.red : AuditarBrand.greenDark,
              ),
              title: Text(
                member.title,
                style: const TextStyle(fontWeight: FontWeight.w800),
              ),
              subtitle: latest == null
                  ? const Text('Treinamento CIPA/NR-05 pendente')
                  : Text(
                      '${latest.code} ${latest.title}\n'
                      'Realizado: ${latest.trainingDate == null ? '-' : _date.format(latest.trainingDate!)}'
                      '${latest.expiryDate == null ? '' : ' • Validade: ${_date.format(latest.expiryDate!)}'}',
                    ),
              isThreeLine: latest != null,
            ),
          );
        }),
      ],
    );
  }

  Widget _documentsTab() => _standardList(
        title: 'Documentos da CIPA',
        addLabel: 'Adicionar documento',
        onAdd: _addDocument,
        items: mandateDocuments,
        itemBuilder: (item) => Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: Column(
            children: [
              ListTile(
                leading: const Icon(Icons.folder_copy_outlined),
                title: Text(
                  item.title,
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
                subtitle: Text(
                  '${item.payload['category'] ?? 'Documento'} • ${item.status}',
                ),
              ),
              ButtonBar(
                children: [
                  TextButton(
                    onPressed: () => _attachTo(
                      entityType: 'cipa_document',
                      entityId: item.id,
                    ),
                    child: const Text('Anexar'),
                  ),
                  TextButton(
                    onPressed: () => _showAttachments(
                      entityType: 'cipa_document',
                      entityId: item.id,
                    ),
                    child: const Text('Arquivos'),
                  ),
                ],
              ),
            ],
          ),
        ),
      );

  Widget _historyTab() {
    final old = mandates.where((m) => m.status != 'Ativo').toList();
    return ListView(
      padding: const EdgeInsets.fromLTRB(12, 12, 12, 90),
      children: [
        const Card(
          child: ListTile(
            leading: Icon(Icons.history_outlined),
            title: Text('Histórico de mandatos'),
            subtitle: Text(
              'Os mandatos antigos permanecem arquivados e podem ser consultados sem apagar dados.',
            ),
          ),
        ),
        const SizedBox(height: 8),
        if (old.isEmpty)
          const Card(
            child: Padding(
              padding: EdgeInsets.all(18),
              child: Text('Nenhum mandato anterior registrado.'),
            ),
          )
        else
          ...old.map((mandate) {
            final mMembers = members
                .where(
                  (m) => '${m.payload['mandateId'] ?? ''}' == mandate.id,
                )
                .length;
            final mMeetings = meetings
                .where(
                  (m) => '${m.payload['mandateId'] ?? ''}' == mandate.id,
                )
                .length;
            final mMinutes = minutes
                .where(
                  (m) => '${m.payload['mandateId'] ?? ''}' == mandate.id,
                )
                .length;
            return Card(
              child: ListTile(
                leading: const Icon(Icons.archive_outlined),
                title: Text(
                  mandate.title,
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
                subtitle: Text(
                  '${_date.format(mandate.date)} a ${mandate.dueDate == null ? '-' : _date.format(mandate.dueDate!)}\n'
                  '$mMembers membro(s) • $mMeetings reunião(ões) • $mMinutes ata(s)',
                ),
                isThreeLine: true,
                onTap: () => _editMandate(mandate),
              ),
            );
          }),
      ],
    );
  }

  Widget _standardList({
    required String title,
    required String addLabel,
    required VoidCallback? onAdd,
    required List<SstRecord> items,
    required Widget Function(SstRecord) itemBuilder,
  }) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(12, 12, 12, 90),
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                title,
                style: const TextStyle(
                  fontWeight: FontWeight.w900,
                  fontSize: 17,
                ),
              ),
            ),
            FilledButton.icon(
              onPressed: onAdd,
              icon: const Icon(Icons.add),
              label: Text(addLabel),
            ),
          ],
        ),
        const SizedBox(height: 10),
        if (items.isEmpty)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Text('Nenhum registro em $title.'),
            ),
          )
        else
          ...items.map(itemBuilder),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    if (loading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }
    return DefaultTabController(
      length: 10,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('CIPA'),
          actions: [
            IconButton(
              tooltip: 'Atualizar',
              onPressed: () => _load(showLoading: false),
              icon: const Icon(Icons.refresh),
            ),
          ],
          bottom: const TabBar(
            isScrollable: true,
            tabs: [
              Tab(text: 'Painel'),
              Tab(text: 'Mandato'),
              Tab(text: 'Membros'),
              Tab(text: 'Reuniões'),
              Tab(text: 'Atas'),
              Tab(text: 'Ações'),
              Tab(text: 'Eleição'),
              Tab(text: 'Treinamentos'),
              Tab(text: 'Documentos'),
              Tab(text: 'Histórico'),
            ],
          ),
        ),
        body: Stack(
          children: [
            TabBarView(
              children: [
                _panelTab(),
                _mandateTab(),
                _membersTab(),
                _meetingsTab(),
                _minutesTab(),
                _actionsTab(),
                _electionTab(),
                _trainingTab(),
                _documentsTab(),
                _historyTab(),
              ],
            ),
            if (busy)
              const Positioned.fill(
                child: ColoredBox(
                  color: Color(0x55000000),
                  child: Center(child: CircularProgressIndicator()),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

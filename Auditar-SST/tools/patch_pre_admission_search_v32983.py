#!/usr/bin/env python3
from pathlib import Path
import re, shutil, sys

root=Path(sys.argv[1])
platform=(sys.argv[2] if len(sys.argv)>2 else 'android').lower()
repo=Path.cwd()

def read(rel):
    return (root/rel).read_text(encoding='utf-8')

def write(rel,text):
    (root/rel).write_text(text,encoding='utf-8',newline='\n')

def once(text,old,new,label):
    if new in text:
        return text
    if old not in text:
        raise RuntimeError('Marcador não localizado: '+label)
    return text.replace(old,new,1)

def copy_source(src_rel,dst_rel):
    src=repo/src_rel
    if not src.exists():
        raise RuntimeError('Fonte não encontrada: '+src_rel)
    dst=root/dst_rel
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(src,dst)

version='3.30.11+198' if platform=='windows' else '3.29.83+225'
pub=read('pubspec.yaml')
pub,n=re.subn(r'^version:\s*[^\n]+',f'version: {version}',pub,count=1,flags=re.M)
if n!=1:
    raise RuntimeError('Versão não localizada')
write('pubspec.yaml',pub)

copy_source(
    'build_sources/v3.29.82-pre-admission/pre_admission_participant_service.dart',
    'lib/services/pre_admission_participant_service.dart',
)
copy_source(
    'build_sources/v3.29.82-pre-admission/pre_admission_dialogs.dart',
    'lib/screens/pre_admission_dialogs.dart',
)
copy_source(
    'build_sources/v3.29.82-pre-admission/searchable_worker_field.dart',
    'lib/widgets/searchable_worker_field.dart',
)

# ------------------------------------------------------------------
# Treinamentos realizados / Integração
# ------------------------------------------------------------------
rel='lib/screens/training_records_screen.dart'
c=read(rel)
if "import '../services/pre_admission_participant_service.dart';" not in c:
    c=once(
        c,
        "import '../services/media_sync_service.dart';\n",
        "import '../services/media_sync_service.dart';\n"
        "import '../services/pre_admission_participant_service.dart';\n",
        'import preadmission training',
    )
if "import 'pre_admission_dialogs.dart';" not in c:
    c=once(
        c,
        "import 'facial_confirmation_screen.dart';\n",
        "import 'facial_confirmation_screen.dart';\n"
        "import 'pre_admission_dialogs.dart';\n",
        'import dialogs training',
    )

c=once(
    c,
    "  List<Sector> sectors = <Sector>[];\n",
    "  List<Sector> sectors = <Sector>[];\n"
    "  List<SstRecord> preAdmissions = <SstRecord>[];\n",
    'state preadmissions training',
)

c=once(
    c,
    """      db.getWorkers(companyId: widget.companyId),
      db.getSectors(widget.companyId),
    ]);""",
    """      db.getWorkers(companyId: widget.companyId),
      db.getSectors(widget.companyId),
      PreAdmissionParticipantService.getAll(
        widget.companyId,
        includeConverted: false,
      ),
    ]);""",
    'load preadmissions training',
)
c=once(
    c,
    """      sectors = (result[2] as List).cast<Sector>();
      loading = false;""",
    """      sectors = (result[2] as List).cast<Sector>();
      preAdmissions = (result[3] as List).cast<SstRecord>();
      loading = false;""",
    'assign preadmissions training',
)

# Replace _newRecord block to permit no active workers and pass preadmissions.
old="""  Future<void> _newRecord() async {
    final current = company;
    if (current == null) return;
    if (workers.where((worker) => worker.active).isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Cadastre colaboradores antes de registrar o treinamento.')),
      );
      return;
    }
    final id = await Navigator.of(context).push<String>(
      MaterialPageRoute(
        builder: (_) => TrainingRecordFormScreen(
          company: current,
          workers: workers,
          sectors: sectors,
        ),
      ),
    );
"""
new="""  Future<void> _newRecord() async {
    final current = company;
    if (current == null) return;
    final id = await Navigator.of(context).push<String>(
      MaterialPageRoute(
        builder: (_) => TrainingRecordFormScreen(
          company: current,
          workers: workers,
          sectors: sectors,
          preAdmissions: preAdmissions,
        ),
      ),
    );
"""
c=once(c,old,new,'new training allows preadmission')

manage_method="""  Future<void> _managePreAdmissions() async {
    var rows = await PreAdmissionParticipantService.getAll(widget.companyId);
    final search = TextEditingController();
    var query = '';

    await showDialog<void>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setLocalState) {
          final clean = query.trim().toLowerCase();
          final visible = rows.where((row) {
            if (clean.isEmpty) return true;
            final payload = row.payload;
            return row.title.toLowerCase().contains(clean) ||
                '${payload['role'] ?? ''}'.toLowerCase().contains(clean) ||
                '${payload['cpf'] ?? ''}'.toLowerCase().contains(clean);
          }).toList()
            ..sort(
              (a, b) => a.title.toLowerCase().compareTo(b.title.toLowerCase()),
            );

          return AlertDialog(
            title: const Text('Pré-admissão / integração'),
            content: SizedBox(
              width: 620,
              height: 540,
              child: Column(
                children: [
                  TextField(
                    controller: search,
                    autofocus: true,
                    onChanged: (value) =>
                        setLocalState(() => query = value),
                    decoration: InputDecoration(
                      labelText: 'Pesquisar por nome',
                      prefixIcon: const Icon(Icons.search),
                      suffixIcon: query.isEmpty
                          ? null
                          : IconButton(
                              onPressed: () {
                                search.clear();
                                setLocalState(() => query = '');
                              },
                              icon: const Icon(Icons.close),
                            ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          '${visible.length} participante(s)',
                          style: const TextStyle(
                            fontSize: 12,
                            color: Colors.black54,
                          ),
                        ),
                      ),
                      FilledButton.tonalIcon(
                        onPressed: () async {
                          final created = await showCreatePreAdmissionDialog(
                            dialogContext,
                            companyId: widget.companyId,
                            sectors: sectors,
                          );
                          if (created != null) {
                            rows = await PreAdmissionParticipantService.getAll(
                              widget.companyId,
                            );
                            setLocalState(() {});
                          }
                        },
                        icon: const Icon(Icons.person_add_alt_1_outlined),
                        label: const Text('Adicionar'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Expanded(
                    child: visible.isEmpty
                        ? const Center(
                            child: Text('Nenhum participante encontrado.'),
                          )
                        : ListView.separated(
                            itemCount: visible.length,
                            separatorBuilder: (_, __) =>
                                const Divider(height: 1),
                            itemBuilder: (_, index) {
                              final row = visible[index];
                              final payload = row.payload;
                              final role = '${payload['role'] ?? ''}'.trim();
                              final converted =
                                  row.status.toUpperCase() == 'CONVERTIDO';
                              return ListTile(
                                leading: Icon(
                                  converted
                                      ? Icons.verified_user_outlined
                                      : Icons.person_outline,
                                ),
                                title: Text(
                                  row.title,
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w800,
                                  ),
                                ),
                                subtitle: Text(
                                  [
                                    if (role.isNotEmpty) role,
                                    converted
                                        ? 'Convertido em colaborador'
                                        : 'Vínculo ainda não formalizado',
                                  ].join(' • '),
                                ),
                                trailing: converted
                                    ? const Icon(
                                        Icons.check_circle,
                                        color: Colors.green,
                                      )
                                    : FilledButton.tonal(
                                        onPressed: () async {
                                          final worker =
                                              await showConvertPreAdmissionDialog(
                                            dialogContext,
                                            participant: row,
                                            sectors: sectors,
                                          );
                                          if (worker != null) {
                                            rows =
                                                await PreAdmissionParticipantService
                                                    .getAll(widget.companyId);
                                            setLocalState(() {});
                                          }
                                        },
                                        child: const Text('Converter'),
                                      ),
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
                child: const Text('Fechar'),
              ),
            ],
          );
        },
      ),
    );
    search.dispose();
    if (mounted) await _load();
  }

"""
marker="  Future<void> _newRecord() async {\n"
if manage_method not in c:
    if marker not in c:
        raise RuntimeError('Marcador manage preadmission não localizado')
    c=c.replace(marker,manage_method+marker,1)

c=once(
    c,
    "      appBar: AppBar(title: const Text('Treinamentos realizados')),\n",
    """      appBar: AppBar(
        title: const Text('Treinamentos realizados'),
        actions: [
          IconButton(
            tooltip: 'Pré-admissão / integração',
            onPressed: _managePreAdmissions,
            icon: const Icon(Icons.person_add_alt_1_outlined),
          ),
        ],
      ),
""",
    'appbar preadmission training',
)

# Form screen data.
c=once(
    c,
    """  final List<Sector> sectors;

  const TrainingRecordFormScreen({""",
    """  final List<Sector> sectors;
  final List<SstRecord> preAdmissions;

  const TrainingRecordFormScreen({""",
    'form preadmissions field',
)
c=once(
    c,
    """    required this.sectors,
  });""",
    """    required this.sectors,
    this.preAdmissions = const <SstRecord>[],
  });""",
    'form preadmissions ctor',
)
c=once(
    c,
    "  final Set<String> selected = <String>{};\n",
    "  final Set<String> selected = <String>{};\n"
    "  final Set<String> selectedPreAdmissions = <String>{};\n"
    "  late List<SstRecord> localPreAdmissions;\n",
    'form preadmission state',
)
c=once(
    c,
    """  void initState() {
    super.initState();
    _applyTemplate(templateIndex);
  }""",
    """  void initState() {
    super.initState();
    localPreAdmissions = List<SstRecord>.from(widget.preAdmissions)
      ..removeWhere((row) => row.status.toUpperCase() != 'ATIVO');
    _applyTemplate(templateIndex);
  }""",
    'init preadmissions form',
)

visible_marker="""  List<Worker> get visibleWorkers {
    final q = query.trim().toLowerCase();
    final rows = widget.workers.where((worker) => worker.active).where((worker) {
      if (q.isEmpty) return true;
      return worker.name.toLowerCase().contains(q) ||
          worker.role.toLowerCase().contains(q) ||
          worker.cpf.toLowerCase().contains(q);
    }).toList();
    rows.sort((a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()));
    return rows;
  }
"""
visible_new=visible_marker+"""
  List<SstRecord> get visiblePreAdmissions {
    final q = query.trim().toLowerCase();
    final rows = localPreAdmissions.where((row) {
      if (row.status.toUpperCase() != 'ATIVO') return false;
      if (q.isEmpty) return true;
      return row.title.toLowerCase().contains(q) ||
          '${row.payload['role'] ?? ''}'.toLowerCase().contains(q) ||
          '${row.payload['cpf'] ?? ''}'.toLowerCase().contains(q);
    }).toList();
    rows.sort(
      (a, b) => a.title.toLowerCase().compareTo(b.title.toLowerCase()),
    );
    return rows;
  }

  Future<void> _addPreAdmission() async {
    final created = await showCreatePreAdmissionDialog(
      context,
      companyId: widget.company.id,
      sectors: widget.sectors,
    );
    if (created == null || !mounted) return;
    setState(() {
      localPreAdmissions.add(created);
      selectedPreAdmissions.add(created.id);
    });
  }
"""
c=once(c,visible_marker,visible_new,'visible preadmissions form')

c=once(
    c,
    """    if (selected.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Selecione pelo menos um participante.')),
      );
      return;
    }""",
    """    if (selected.isEmpty && selectedPreAdmissions.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Selecione pelo menos um participante.')),
      );
      return;
    }""",
    'save preadmission selection requirement',
)

worker_participants="""    for (final worker in widget.workers.where((item) => selected.contains(item.id))) {
      participants.add({
        'id': const Uuid().v4(),
        'workerId': worker.id,
        'name': worker.name,
        'cpf': worker.cpf,
        'role': worker.role,
        'sector': _sector(worker.sectorId)?.name ?? '',
        'status': 'PENDENTE',
        'signatureId': '',
        'signedAt': '',
      });
    }
"""
worker_participants_new=worker_participants+"""
    for (final participant in localPreAdmissions.where(
      (item) => selectedPreAdmissions.contains(item.id),
    )) {
      final payload = participant.payload;
      participants.add({
        'id': const Uuid().v4(),
        'workerId': '',
        'preAdmissionId': participant.id,
        'participantType': 'PRE_ADMISSION',
        'employmentStatus': 'VINCULO_NAO_FORMALIZADO',
        'name': participant.title,
        'cpf': '${payload['cpf'] ?? ''}',
        'role': '${payload['role'] ?? ''}',
        'sector': '${payload['sector'] ?? ''}',
        'sectorId': '${payload['sectorId'] ?? ''}',
        'status': 'PENDENTE',
        'signatureId': '',
        'signedAt': '',
      });
    }
"""
c=once(c,worker_participants,worker_participants_new,'add preadmission participants')

c=once(
    c,
    """    final visible = visibleWorkers;
    final allVisible = visible.isNotEmpty &&
        visible.every((worker) => selected.contains(worker.id));""",
    """    final visible = visibleWorkers;
    final visiblePreAdmissionRows = visiblePreAdmissions;
    final selectedTotal = selected.length + selectedPreAdmissions.length;
    final allVisible = visible.isNotEmpty &&
        visible.every((worker) => selected.contains(worker.id));""",
    'build preadmission counts',
)
c=once(
    c,
    "              Text('${selected.length} selecionado(s)'),\n",
    "              Text('$selectedTotal selecionado(s)'),\n",
    'selected total label',
)
c=once(
    c,
    """            decoration: const InputDecoration(
              hintText: 'Buscar trabalhador ou cargo',
              prefixIcon: Icon(Icons.search),
            ),""",
    """            decoration: InputDecoration(
              hintText: 'Pesquisar por nome ou cargo',
              prefixIcon: const Icon(Icons.search),
              suffixIcon: query.isEmpty
                  ? null
                  : IconButton(
                      tooltip: 'Limpar pesquisa',
                      onPressed: () {
                        search.clear();
                        setState(() => query = '');
                      },
                      icon: const Icon(Icons.close),
                    ),
            ),""",
    'search standardized training form',
)

worker_list_end="""          ...visible.map(
            (worker) => CheckboxListTile(
              value: selected.contains(worker.id),
              title: Text(
                worker.name,
                style: const TextStyle(fontWeight: FontWeight.w700),
              ),
              subtitle: Text(
                [
                  worker.role,
                  if ((_sector(worker.sectorId)?.name ?? '').isNotEmpty)
                    _sector(worker.sectorId)!.name,
                ].where((item) => item.isNotEmpty).join(' • '),
              ),
              onChanged: (value) {
                setState(() {
                  if (value == true) {
                    selected.add(worker.id);
                  } else {
                    selected.remove(worker.id);
                  }
                });
              },
            ),
          ),
"""
worker_list_new=worker_list_end+"""
          const Divider(height: 24),
          Row(
            children: [
              const Expanded(
                child: Text(
                  'Pré-admissão / integração',
                  style: TextStyle(
                    fontWeight: FontWeight.w900,
                    color: AuditarBrand.navy,
                  ),
                ),
              ),
              FilledButton.tonalIcon(
                onPressed: _addPreAdmission,
                icon: const Icon(Icons.person_add_alt_1_outlined),
                label: const Text('Adicionar'),
              ),
            ],
          ),
          const SizedBox(height: 4),
          const Text(
            'Participantes ainda sem vínculo formal. Eles não entram na lista de colaboradores ativos.',
            style: TextStyle(fontSize: 11.5, color: Colors.black54),
          ),
          if (visiblePreAdmissionRows.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 10),
              child: Text(
                'Nenhum participante em pré-admissão encontrado.',
                style: TextStyle(color: Colors.black54),
              ),
            ),
          ...visiblePreAdmissionRows.map(
            (participant) => CheckboxListTile(
              value: selectedPreAdmissions.contains(participant.id),
              title: Text(
                participant.title,
                style: const TextStyle(fontWeight: FontWeight.w800),
              ),
              subtitle: Text(
                [
                  '${participant.payload['role'] ?? ''}',
                  '${participant.payload['sector'] ?? ''}',
                  'Vínculo ainda não formalizado',
                ].where((item) => item.trim().isNotEmpty).join(' • '),
              ),
              secondary: const Icon(Icons.person_outline),
              onChanged: (value) {
                setState(() {
                  if (value == true) {
                    selectedPreAdmissions.add(participant.id);
                  } else {
                    selectedPreAdmissions.remove(participant.id);
                  }
                });
              },
            ),
          ),
"""
c=once(c,worker_list_end,worker_list_new,'preadmission list training form')

c=c.replace(
    "'Criar registro com ${selected.length} participante(s)'",
    "'Criar registro com $selectedTotal participante(s)'",
    1,
)
write(rel,c)

# ------------------------------------------------------------------
# DDS com pré-admissão no seletor e assinatura
# ------------------------------------------------------------------
rel='lib/screens/sst_record_form_screen.dart'
c=read(rel)
if "import '../services/pre_admission_participant_service.dart';" not in c:
    c=once(
        c,
        "import '../services/media_sync_service.dart';\n",
        "import '../services/media_sync_service.dart';\n"
        "import '../services/pre_admission_participant_service.dart';\n",
        'import preadmission dds',
    )
if "import 'pre_admission_dialogs.dart';" not in c:
    c=once(
        c,
        "import 'facial_confirmation_screen.dart';\n",
        "import 'facial_confirmation_screen.dart';\n"
        "import 'pre_admission_dialogs.dart';\n",
        'import dialogs dds',
    )

c=once(
    c,
    """  List<Worker> ddsWorkers = [];
  final Set<String> selectedDdsWorkerIds = <String>{};""",
    """  List<Worker> ddsWorkers = [];
  List<SstRecord> ddsPreAdmissions = [];
  final Set<String> selectedDdsWorkerIds = <String>{};
  final Set<String> selectedDdsPreAdmissionIds = <String>{};""",
    'dds preadmission state',
)

c=once(
    c,
    """            final workerId = '${raw['workerId'] ?? raw['worker_id'] ?? ''}'.trim();
            if (workerId.isNotEmpty) selectedDdsWorkerIds.add(workerId);""",
    """            final workerId = '${raw['workerId'] ?? raw['worker_id'] ?? ''}'.trim();
            final preAdmissionId =
                '${raw['preAdmissionId'] ?? raw['pre_admission_id'] ?? ''}'.trim();
            if (workerId.isNotEmpty) selectedDdsWorkerIds.add(workerId);
            if (preAdmissionId.isNotEmpty) {
              selectedDdsPreAdmissionIds.add(preAdmissionId);
            }""",
    'restore dds preadmission selection',
)

old_load="""  Future<void> _loadDdsWorkers(String? companyId, {bool notify = true}) async {
    final loaded = companyId == null || companyId.isEmpty
        ? <Worker>[]
        : await AppDatabase.instance.getWorkers(companyId: companyId);
    selectedDdsWorkerIds.removeWhere(
      (id) => !loaded.any((worker) => worker.id == id),
    );
    if (!mounted) return;
    if (notify) {
      setState(() => ddsWorkers = loaded);
    } else {
      ddsWorkers = loaded;
    }
  }
"""
new_load="""  Future<void> _loadDdsWorkers(String? companyId, {bool notify = true}) async {
    final loaded = companyId == null || companyId.isEmpty
        ? <Worker>[]
        : await AppDatabase.instance.getWorkers(companyId: companyId);
    final preAdmissions = companyId == null || companyId.isEmpty
        ? <SstRecord>[]
        : await PreAdmissionParticipantService.getAll(
            companyId,
            includeConverted: false,
          );
    selectedDdsWorkerIds.removeWhere(
      (id) => !loaded.any((worker) => worker.id == id),
    );
    selectedDdsPreAdmissionIds.removeWhere(
      (id) => !preAdmissions.any((row) => row.id == id),
    );
    if (!mounted) return;
    if (notify) {
      setState(() {
        ddsWorkers = loaded;
        ddsPreAdmissions = preAdmissions;
      });
    } else {
      ddsWorkers = loaded;
      ddsPreAdmissions = preAdmissions;
    }
  }
"""
c=once(c,old_load,new_load,'load dds preadmissions')

start=c.find('  List<String> _ddsParticipantNames() {')
end=c.find('  Future<void> _restoreDdsSignaturePaths()',start)
if start<0 or end<0:
    raise RuntimeError('Bloco participantes DDS não localizado')
dds_block="""  List<String> _ddsParticipantNames() {
    final seen = <String>{};
    final result = <String>[];
    for (final worker in ddsWorkers) {
      if (!selectedDdsWorkerIds.contains(worker.id)) continue;
      final name = worker.name.trim();
      if (name.isEmpty) continue;
      if (seen.add(name.toLowerCase())) result.add(name);
    }
    for (final participant in ddsPreAdmissions) {
      if (!selectedDdsPreAdmissionIds.contains(participant.id)) continue;
      final name = participant.title.trim();
      if (name.isEmpty) continue;
      if (seen.add(name.toLowerCase())) result.add(name);
    }
    for (final raw in participantsController.text.split(RegExp(r'[\\r\\n]+'))) {
      final name = raw.trim();
      if (name.isEmpty) continue;
      final key = name.toLowerCase();
      if (seen.add(key)) result.add(name);
    }
    return result;
  }

  List<Map<String, dynamic>> _ddsStructuredParticipants() {
    final sectorById = {for (final sector in sectors) sector.id: sector.name};
    final result = <Map<String, dynamic>>[];
    for (final worker in ddsWorkers) {
      if (!selectedDdsWorkerIds.contains(worker.id)) continue;
      result.add({
        'workerId': worker.id,
        'participantType': 'WORKER',
        'name': worker.name,
        'cpf': worker.cpf,
        'role': worker.role,
        'sectorId': worker.sectorId ?? '',
        'sector': worker.sectorId == null
            ? ''
            : (sectorById[worker.sectorId] ?? ''),
      });
    }
    for (final participant in ddsPreAdmissions) {
      if (!selectedDdsPreAdmissionIds.contains(participant.id)) continue;
      final payload = participant.payload;
      result.add({
        'workerId': '',
        'preAdmissionId': participant.id,
        'participantType': 'PRE_ADMISSION',
        'employmentStatus': 'VINCULO_NAO_FORMALIZADO',
        'name': participant.title,
        'cpf': '${payload['cpf'] ?? ''}',
        'role': '${payload['role'] ?? ''}',
        'sectorId': '${payload['sectorId'] ?? ''}',
        'sector': '${payload['sector'] ?? ''}',
      });
    }
    return result;
  }

  Map<String, dynamic> _ddsParticipantMetadata(
    String name, [
    Map<String, dynamic>? current,
  ]) {
    final normalized = name.trim().toLowerCase();
    final currentPreId = '${current?['preAdmissionId'] ?? ''}'.trim();
    SstRecord? preAdmission;
    for (final row in ddsPreAdmissions) {
      if ((currentPreId.isNotEmpty && row.id == currentPreId) ||
          row.title.trim().toLowerCase() == normalized) {
        preAdmission = row;
        break;
      }
    }
    if (preAdmission != null) {
      final payload = preAdmission.payload;
      return <String, dynamic>{
        'preAdmissionId': preAdmission.id,
        'participantType': 'PRE_ADMISSION',
        'employmentStatus': 'VINCULO_NAO_FORMALIZADO',
        'cpf': '${payload['cpf'] ?? ''}',
        'role': '${payload['role'] ?? ''}',
        'sectorId': '${payload['sectorId'] ?? ''}',
        'sector': '${payload['sector'] ?? ''}',
      };
    }

    final currentWorkerId = '${current?['workerId'] ?? ''}'.trim();
    Worker? worker;
    for (final item in ddsWorkers) {
      if ((currentWorkerId.isNotEmpty && item.id == currentWorkerId) ||
          item.name.trim().toLowerCase() == normalized) {
        worker = item;
        break;
      }
    }
    if (worker == null) return const <String, dynamic>{};
    final sectorById = {for (final sector in sectors) sector.id: sector.name};
    return <String, dynamic>{
      'workerId': worker.id,
      'participantType': 'WORKER',
      'cpf': worker.cpf,
      'role': worker.role,
      'sectorId': worker.sectorId ?? '',
      'sector': worker.sectorId == null
          ? ''
          : (sectorById[worker.sectorId] ?? ''),
    };
  }

  Future<void> _selectDdsWorkers() async {
    if (selectedCompanyId == null || selectedCompanyId!.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Selecione a empresa antes de escolher os participantes.',
          ),
        ),
      );
      return;
    }
    if (ddsWorkers.isEmpty && ddsPreAdmissions.isEmpty) {
      await _loadDdsWorkers(selectedCompanyId);
    }
    if (!mounted) return;

    final chosenWorkers = <String>{...selectedDdsWorkerIds};
    final chosenPreAdmissions = <String>{...selectedDdsPreAdmissionIds};
    final search = TextEditingController();
    var query = '';

    final result = await showDialog<Map<String, Set<String>>>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) {
          final clean = query.trim().toLowerCase();
          final visibleWorkers = ddsWorkers.where((worker) {
            if (clean.isEmpty) return true;
            return worker.name.toLowerCase().contains(clean) ||
                worker.role.toLowerCase().contains(clean) ||
                worker.cpf.toLowerCase().contains(clean);
          }).toList()
            ..sort(
              (a, b) =>
                  a.name.toLowerCase().compareTo(b.name.toLowerCase()),
            );
          final visiblePreAdmissions = ddsPreAdmissions.where((row) {
            if (clean.isEmpty) return true;
            return row.title.toLowerCase().contains(clean) ||
                '${row.payload['role'] ?? ''}'.toLowerCase().contains(clean) ||
                '${row.payload['cpf'] ?? ''}'.toLowerCase().contains(clean);
          }).toList()
            ..sort(
              (a, b) =>
                  a.title.toLowerCase().compareTo(b.title.toLowerCase()),
            );
          final sectorName = {
            for (final sector in sectors) sector.id: sector.name,
          };
          final totalVisible =
              visibleWorkers.length + visiblePreAdmissions.length;

          return AlertDialog(
            title: const Text('Participantes do DDS'),
            content: SizedBox(
              width: 620,
              height: 580,
              child: Column(
                children: [
                  TextField(
                    controller: search,
                    autofocus: true,
                    onChanged: (value) =>
                        setDialogState(() => query = value),
                    decoration: InputDecoration(
                      prefixIcon: const Icon(Icons.search),
                      labelText: 'Pesquisar por nome',
                      suffixIcon: query.isEmpty
                          ? null
                          : IconButton(
                              tooltip: 'Limpar pesquisa',
                              onPressed: () {
                                search.clear();
                                setDialogState(() => query = '');
                              },
                              icon: const Icon(Icons.close),
                            ),
                    ),
                  ),
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          '$totalVisible participante(s) encontrado(s)',
                          style: const TextStyle(
                            fontSize: 12,
                            color: Colors.black54,
                          ),
                        ),
                      ),
                      TextButton(
                        onPressed: () => setDialogState(() {
                          chosenWorkers.addAll(
                            visibleWorkers.map((worker) => worker.id),
                          );
                          chosenPreAdmissions.addAll(
                            visiblePreAdmissions.map((row) => row.id),
                          );
                        }),
                        child: const Text('Selecionar exibidos'),
                      ),
                      TextButton(
                        onPressed: () => setDialogState(() {
                          chosenWorkers.clear();
                          chosenPreAdmissions.clear();
                        }),
                        child: const Text('Limpar'),
                      ),
                    ],
                  ),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton.tonalIcon(
                      onPressed: () async {
                        final created = await showCreatePreAdmissionDialog(
                          dialogContext,
                          companyId: selectedCompanyId!,
                          sectors: sectors,
                        );
                        if (created == null) return;
                        ddsPreAdmissions.add(created);
                        chosenPreAdmissions.add(created.id);
                        setDialogState(() {});
                      },
                      icon: const Icon(Icons.person_add_alt_1_outlined),
                      label: const Text(
                        'Adicionar participante em pré-admissão',
                      ),
                    ),
                  ),
                  const SizedBox(height: 6),
                  Expanded(
                    child: totalVisible == 0
                        ? const Center(
                            child: Text('Nenhum participante encontrado.'),
                          )
                        : ListView(
                            children: [
                              ...visibleWorkers.map((worker) {
                                final sector = worker.sectorId == null
                                    ? ''
                                    : (sectorName[worker.sectorId] ?? '');
                                final details = <String>[
                                  if (worker.role.trim().isNotEmpty)
                                    worker.role.trim(),
                                  if (sector.trim().isNotEmpty) sector.trim(),
                                  if (worker.cpf.trim().isNotEmpty)
                                    'CPF ${worker.cpf.trim()}',
                                ].join(' • ');
                                return CheckboxListTile(
                                  dense: true,
                                  value: chosenWorkers.contains(worker.id),
                                  title: Text(worker.name),
                                  subtitle:
                                      details.isEmpty ? null : Text(details),
                                  onChanged: (value) => setDialogState(() {
                                    if (value == true) {
                                      chosenWorkers.add(worker.id);
                                    } else {
                                      chosenWorkers.remove(worker.id);
                                    }
                                  }),
                                );
                              }),
                              if (visiblePreAdmissions.isNotEmpty)
                                const Padding(
                                  padding: EdgeInsets.fromLTRB(12, 10, 12, 2),
                                  child: Text(
                                    'PRÉ-ADMISSÃO / INTEGRAÇÃO',
                                    style: TextStyle(
                                      fontSize: 11,
                                      fontWeight: FontWeight.w900,
                                      color: AuditarBrand.greenDark,
                                    ),
                                  ),
                                ),
                              ...visiblePreAdmissions.map((row) {
                                final role =
                                    '${row.payload['role'] ?? ''}'.trim();
                                final sector =
                                    '${row.payload['sector'] ?? ''}'.trim();
                                return CheckboxListTile(
                                  dense: true,
                                  value:
                                      chosenPreAdmissions.contains(row.id),
                                  secondary:
                                      const Icon(Icons.person_outline),
                                  title: Text(
                                    row.title,
                                    style: const TextStyle(
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                  subtitle: Text(
                                    [
                                      if (role.isNotEmpty) role,
                                      if (sector.isNotEmpty) sector,
                                      'Vínculo ainda não formalizado',
                                    ].join(' • '),
                                  ),
                                  onChanged: (value) => setDialogState(() {
                                    if (value == true) {
                                      chosenPreAdmissions.add(row.id);
                                    } else {
                                      chosenPreAdmissions.remove(row.id);
                                    }
                                  }),
                                );
                              }),
                            ],
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
              FilledButton(
                onPressed: () => Navigator.pop(
                  dialogContext,
                  <String, Set<String>>{
                    'workers': chosenWorkers,
                    'preAdmissions': chosenPreAdmissions,
                  },
                ),
                child: Text(
                  'Confirmar (${chosenWorkers.length + chosenPreAdmissions.length})',
                ),
              ),
            ],
          );
        },
      ),
    );
    search.dispose();
    if (result == null || !mounted) return;
    setState(() {
      selectedDdsWorkerIds
        ..clear()
        ..addAll(result['workers'] ?? const <String>{});
      selectedDdsPreAdmissionIds
        ..clear()
        ..addAll(result['preAdmissions'] ?? const <String>{});
    });
  }

  Widget _ddsParticipantsCard() {
    final selectedWorkers = ddsWorkers
        .where((worker) => selectedDdsWorkerIds.contains(worker.id))
        .toList();
    final selectedPreAdmissions = ddsPreAdmissions
        .where(
          (participant) =>
              selectedDdsPreAdmissionIds.contains(participant.id),
        )
        .toList();
    final total =
        selectedWorkers.length + selectedPreAdmissions.length;

    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(
                  Icons.groups_2_outlined,
                  color: AuditarBrand.greenDark,
                ),
                const SizedBox(width: 8),
                const Expanded(
                  child: Text(
                    'Participantes do DDS',
                    style: TextStyle(
                      fontWeight: FontWeight.w800,
                      color: AuditarBrand.navy,
                    ),
                  ),
                ),
                Text(
                  '$total',
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
              ],
            ),
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: FilledButton.tonalIcon(
                onPressed: _selectDdsWorkers,
                icon: const Icon(Icons.person_search_outlined),
                label: const Text('Selecionar / pesquisar participantes'),
              ),
            ),
            if (total > 0) ...[
              const SizedBox(height: 8),
              ...selectedWorkers.take(5).map(
                    (worker) => Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Row(
                        children: [
                          const Icon(
                            Icons.check_circle,
                            size: 16,
                            color: AuditarBrand.greenDark,
                          ),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              worker.role.trim().isEmpty
                                  ? worker.name
                                  : '${worker.name} • ${worker.role}',
                              style: const TextStyle(fontSize: 12.5),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
              ...selectedPreAdmissions.take(5).map(
                    (participant) => Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Row(
                        children: [
                          const Icon(
                            Icons.person_outline,
                            size: 16,
                            color: AuditarBrand.greenDark,
                          ),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              '${participant.title} • Pré-admissão',
                              style: const TextStyle(fontSize: 12.5),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
              if (total > 10)
                Text(
                  '+ ${total - 10} participante(s)',
                  style: const TextStyle(
                    color: Colors.black54,
                    fontSize: 12,
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }

"""
c=c[:start]+dds_block+c[end:]

# Replace participant metadata blocks in both drawn and face signatures.
pattern_draw=re.compile(
r"""    final matchedWorker = ddsWorkers\.cast<Worker\?>\(\)\.firstWhere\(.*?    final updated = <String, dynamic>\{\n      'id': signatureId,\n      'name': result\.name,\n      'signedAt': result\.signedAt\.toUtc\(\)\.toIso8601String\(\),\n      'method': 'signature',\n.*?    \};""",
re.S)
m=pattern_draw.search(c)
if not m:
    raise RuntimeError('Metadados assinatura DDS não localizados')
draw_new="""    final participantMeta = _ddsParticipantMetadata(
      result.name,
      existing,
    );
    final updated = <String, dynamic>{
      'id': signatureId,
      'name': result.name,
      'signedAt': result.signedAt.toUtc().toIso8601String(),
      'method': 'signature',
      ...participantMeta,
    };"""
c=c[:m.start()]+draw_new+c[m.end():]

pattern_face=re.compile(
r"""    final matchedWorker = ddsWorkers\.cast<Worker\?>\(\)\.firstWhere\(.*?    final updated = <String, dynamic>\{\n      'id': result\.confirmationId,\n      'name': participantName,\n      'signedAt': result\.confirmedAt\.toUtc\(\)\.toIso8601String\(\),\n      'method': 'face',\n      'proofCode': result\.proofCode,\n      'photoSha256': result\.photoSha256,\n      'consentVersion': 'facial-photo-v2',\n.*?    \};""",
re.S)
m=pattern_face.search(c)
if not m:
    raise RuntimeError('Metadados facial DDS não localizados')
face_new="""    final participantMeta = _ddsParticipantMetadata(
      participantName,
      current,
    );
    final updated = <String, dynamic>{
      'id': result.confirmationId,
      'name': participantName,
      'signedAt': result.confirmedAt.toUtc().toIso8601String(),
      'method': 'face',
      'proofCode': result.proofCode,
      'photoSha256': result.photoSha256,
      'consentVersion': 'facial-photo-v2',
      ...participantMeta,
    };"""
c=c[:m.start()]+face_new+c[m.end():]
write(rel,c)

# ------------------------------------------------------------------
# PDFs: identificar pré-admissão sem sugerir vínculo formal
# ------------------------------------------------------------------
rel='lib/services/training_record_pdf_service.dart'
c=read(rel)
training_role_pattern = re.compile(
    r"\[\s*'\$\{person\['role'\]\s*\?\?\s*''\}',\s*"
    r"'\$\{person\['sector'\]\s*\?\?\s*''\}',\s*"
    r"\]\.where\(\(item\)\s*=>\s*item\.trim\(\)\.isNotEmpty\)\.join\('\\n'\)",
    re.S,
)
training_role_replacement = """[
                '${person['role'] ?? ''}',
                '${person['sector'] ?? ''}',
                if ('${person['preAdmissionId'] ?? ''}'.trim().isNotEmpty)
                  'PRÉ-ADMISSÃO • vínculo ainda não formalizado',
              ].where((item) => item.trim().isNotEmpty).join('\\n')"""
c,n=training_role_pattern.subn(lambda _: training_role_replacement,c,count=1)
if n!=1:
    raise RuntimeError('Marcador não localizado: training pdf preadmission')
write(rel,c)

rel='lib/services/dds_pdf_service.dart'
c=read(rel)
c=once(
    c,
    """          'sector': worker?.sectorId == null
              ? '${map['sector'] ?? ''}'
              : (sectorById[worker!.sectorId] ?? '${map['sector'] ?? ''}'),
        });""",
    """          'sector': worker?.sectorId == null
              ? '${map['sector'] ?? ''}'
              : (sectorById[worker!.sectorId] ?? '${map['sector'] ?? ''}'),
          'preAdmissionId':
              '${map['preAdmissionId'] ?? map['pre_admission_id'] ?? ''}',
          'participantType': '${map['participantType'] ?? ''}',
        });""",
    'dds pdf preserve preadmission',
)
c=once(
    c,
    """            _cell('${row['role'] ?? ''}'.trim().isEmpty ? '-' : '${row['role']}', fontSize: 6.2),""",
    r"""            _cell(
              [
                if ('${row['role'] ?? ''}'.trim().isNotEmpty)
                  '${row['role']}',
                if ('${row['preAdmissionId'] ?? ''}'.trim().isNotEmpty)
                  'PRÉ-ADMISSÃO',
              ].isEmpty
                  ? '-'
                  : [
                      if ('${row['role'] ?? ''}'.trim().isNotEmpty)
                        '${row['role']}',
                      if ('${row['preAdmissionId'] ?? ''}'.trim().isNotEmpty)
                        'PRÉ-ADMISSÃO',
                    ].join('\n'),
              fontSize: 6.2,
            ),""",
    'dds pdf preadmission label',
)
write(rel,c)

# ------------------------------------------------------------------
# Seletor reutilizável: CIPA / eleições / treinamentos
# ------------------------------------------------------------------
rel='lib/screens/cipa_election_detail_screen.dart'
c=read(rel)
if "import '../widgets/searchable_worker_field.dart';" not in c:
    # imports use ../models etc; insert after models
    if "import '../models.dart';\n" in c:
        c=c.replace(
            "import '../models.dart';\n",
            "import '../models.dart';\nimport '../widgets/searchable_worker_field.dart';\n",
            1,
        )
    else:
        raise RuntimeError('Import models CIPA election não localizado')
old_dialog="""    String? selectedWorkerId;
    final workerId = await showDialog<String>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setLocalState) => AlertDialog(
          title: const Text('Adicionar candidato'),
          content: DropdownButtonFormField<String>(
            value: selectedWorkerId,
            isExpanded: true,
            decoration: const InputDecoration(
              labelText: 'Trabalhador',
              prefixIcon: Icon(Icons.person_outline),
            ),
            items: workers
                .where((worker) => !candidates.any((c) => c.workerId == worker.id))
                .map((worker) => DropdownMenuItem(value: worker.id, child: Text(worker.name)))
                .toList(),
            onChanged: (value) =>
                setLocalState(() => selectedWorkerId = value),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: selectedWorkerId == null
                  ? null
                  : () => Navigator.pop(dialogContext, selectedWorkerId),
              child: const Text('Adicionar'),
            ),
          ],
        ),
      ),
    );"""
new_dialog="""    final eligibleWorkers = workers
        .where(
          (worker) =>
              worker.active &&
              !candidates.any((candidate) => candidate.workerId == worker.id),
        )
        .toList();
    final workerId = await showWorkerSearchDialog(
      context,
      workers: eligibleWorkers,
      title: 'Adicionar candidato',
    );"""
c=once(c,old_dialog,new_dialog,'search candidate CIPA')
write(rel,c)

rel='lib/screens/cipa_management_screen.dart'
c=read(rel)
if "import '../widgets/searchable_worker_field.dart';" not in c:
    if "import '../models.dart';\n" in c:
        c=c.replace(
            "import '../models.dart';\n",
            "import '../models.dart';\nimport '../widgets/searchable_worker_field.dart';\n",
            1,
        )
    else:
        raise RuntimeError('Import models CIPA management não localizado')
worker_dropdown="""                DropdownButtonFormField<String>(
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
                ),"""
worker_search="""                SearchableWorkerField(
                  workers: workers,
                  value: workers.any((w) => w.id == workerId)
                      ? workerId
                      : null,
                  label: 'Colaborador',
                  onChanged: (value) {
                    if (value != null) setLocal(() => workerId = value);
                  },
                ),"""
count=c.count(worker_dropdown)
if count<2 and worker_search not in c:
    raise RuntimeError(f'Dropdowns de trabalhador CIPA insuficientes: {count}')
c=c.replace(worker_dropdown,worker_search)
write(rel,c)

rel='lib/screens/trainings_screen.dart'
c=read(rel)
if "import '../widgets/searchable_worker_field.dart';" not in c:
    if "import '../models.dart';\n" in c:
        c=c.replace(
            "import '../models.dart';\n",
            "import '../models.dart';\nimport '../widgets/searchable_worker_field.dart';\n",
            1,
        )
    else:
        raise RuntimeError('Import models trainings não localizado')

single_dropdown="""                      DropdownButtonFormField<String>(
                        isExpanded: true,
                        value: selectedWorkerId,
                        decoration: const InputDecoration(
                          labelText: 'Trabalhador *',
                          prefixIcon: Icon(Icons.person_outline),
                        ),
                        items: workers
                            .map(
                              (worker) => DropdownMenuItem(
                                value: worker.id,
                                child: Text(worker.name, overflow: TextOverflow.ellipsis),
                              ),
                            )
                            .toList(),
                        onChanged: (value) {
                          if (value != null) setLocalState(() => selectedWorkerId = value);
                        },
                      ),"""
single_search="""                      SearchableWorkerField(
                        workers: workers,
                        value: selectedWorkerId,
                        label: 'Trabalhador *',
                        onChanged: (value) {
                          if (value != null) {
                            setLocalState(() => selectedWorkerId = value);
                          }
                        },
                      ),"""
c=once(c,single_dropdown,single_search,'single training searchable worker')

c=once(
    c,
    """    final notesController = TextEditingController();
    final selectedWorkers = <String>{...?initialWorkerIds};""",
    """    final notesController = TextEditingController();
    final workerSearchController = TextEditingController();
    final selectedWorkers = <String>{...?initialWorkerIds};""",
    'bulk search controller',
)
c=once(
    c,
    """    String roleFilter = 'TODOS';
    String? selectedTemplateKey;""",
    """    String roleFilter = 'TODOS';
    String workerQuery = '';
    String? selectedTemplateKey;""",
    'bulk search query',
)
c=once(
    c,
    """          final visibleWorkers = companyWorkers.where((worker) {
            return roleFilter == 'TODOS' || worker.role == roleFilter;
          }).toList();""",
    """          final cleanWorkerQuery = workerQuery.trim().toLowerCase();
          final visibleWorkers = companyWorkers.where((worker) {
            final roleMatches =
                roleFilter == 'TODOS' || worker.role == roleFilter;
            final queryMatches = cleanWorkerQuery.isEmpty ||
                worker.name.toLowerCase().contains(cleanWorkerQuery) ||
                worker.role.toLowerCase().contains(cleanWorkerQuery) ||
                worker.cpf.toLowerCase().contains(cleanWorkerQuery);
            return roleMatches && queryMatches;
          }).toList()
            ..sort(
              (a, b) =>
                  a.name.toLowerCase().compareTo(b.name.toLowerCase()),
            );""",
    'bulk visible searchable',
)
role_filter_marker="""                    DropdownButtonFormField<String>(
                      isExpanded: true,
                      value: roleFilter,
                      decoration: const InputDecoration(
                        labelText: 'Filtrar participantes por cargo',
                      ),"""
search_before="""                    TextField(
                      controller: workerSearchController,
                      onChanged: (value) =>
                          setLocalState(() => workerQuery = value),
                      decoration: InputDecoration(
                        labelText: 'Pesquisar por nome',
                        hintText: 'Digite o nome do colaborador',
                        prefixIcon: const Icon(Icons.search),
                        suffixIcon: workerQuery.isEmpty
                            ? null
                            : IconButton(
                                tooltip: 'Limpar pesquisa',
                                onPressed: () {
                                  workerSearchController.clear();
                                  setLocalState(() => workerQuery = '');
                                },
                                icon: const Icon(Icons.close),
                              ),
                      ),
                    ),
                    const SizedBox(height: 8),
"""+role_filter_marker
c=once(c,role_filter_marker,search_before,'bulk worker search field')

# Ensure controller disposed where other dialog controllers are disposed.
dispose_marker="""    codeController.dispose();
    titleController.dispose();
    notesController.dispose();"""
dispose_new="""    codeController.dispose();
    titleController.dispose();
    notesController.dispose();
    workerSearchController.dispose();"""
c=once(c,dispose_marker,dispose_new,'dispose bulk worker search')
write(rel,c)

# ------------------------------------------------------------------
# Garantias
# ------------------------------------------------------------------
checks={
    'lib/screens/training_records_screen.dart':[
        'Pré-admissão / integração',
        'selectedPreAdmissions',
        'preAdmissionId',
        'Pesquisar por nome ou cargo',
    ],
    'lib/screens/sst_record_form_screen.dart':[
        'selectedDdsPreAdmissionIds',
        'Adicionar participante em pré-admissão',
        'Pesquisar por nome',
        'preAdmissionId',
    ],
    'lib/services/training_record_pdf_service.dart':[
        'PRÉ-ADMISSÃO • vínculo ainda não formalizado',
    ],
    'lib/screens/cipa_election_detail_screen.dart':[
        'showWorkerSearchDialog',
    ],
    'lib/screens/cipa_management_screen.dart':[
        'SearchableWorkerField',
    ],
    'lib/screens/trainings_screen.dart':[
        'Pesquisar por nome',
        'SearchableWorkerField',
    ],
}
for rel,markers in checks.items():
    text=read(rel)
    for marker in markers:
        assert marker in text, f'{rel}: ausente {marker}'
assert f'version: {version}' in read('pubspec.yaml')
print('PRE_ADMISSION_SEARCH_OK',platform,version)

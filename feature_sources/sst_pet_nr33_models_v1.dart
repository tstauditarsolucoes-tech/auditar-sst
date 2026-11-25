import 'dart:convert';
import 'dart:math';

/// PET da NR-33: apenas rascunho auxiliar. NUNCA autoriza entrada.
enum PetCheckStatus { notChecked, reportedYes, reportedNo, notApplicable }

extension PetCheckStatusLabel on PetCheckStatus {
  String get label {
    switch (this) {
      case PetCheckStatus.notChecked: return 'Não verificado';
      case PetCheckStatus.reportedYes: return 'Sim (informado pelo técnico)';
      case PetCheckStatus.reportedNo: return 'Não / pendência';
      case PetCheckStatus.notApplicable: return 'Não se aplica (justificar)';
    }
  }
}

class PetField {
  const PetField(this.key, this.label, this.group, {this.requiredForReview = false});
  final String key, label, group;
  final bool requiredForReview;
}

class PetCheck {
  const PetCheck(this.key, this.label);
  final String key, label;
}

class PetTemplate {
  const PetTemplate._();

  /// Adaptar este roteiro ao cadastro do espaço e aos procedimentos da empresa
  /// antes de implementar emissão legal. NR-33, 33.5.6 e Anexo II.
  static const fields = <PetField>[
    PetField('spaceId', 'Identificação / código do espaço confinado',
        '1. Identificação', requiredForReview: true),
    PetField('location', 'Local e acesso do espaço confinado',
        '1. Identificação', requiredForReview: true),
    PetField('activity', 'Objetivo da entrada e serviço previsto',
        '1. Identificação', requiredForReview: true),
    PetField('riskReference', 'Referência à avaliação de riscos/PGR',
        '1. Identificação', requiredForReview: true),
    PetField('hazards', 'Perigos identificados e controles planejados',
        '2. Perigos e controles', requiredForReview: true),
    PetField('entryHazards', 'Perigos e medidas constatados no momento da entrada',
        '2. Perigos e controles', requiredForReview: true),
    PetField('energyIsolation', 'Bloqueio / isolamento de energias perigosas',
        '2. Perigos e controles', requiredForReview: true),
    PetField('ventilation', 'Ventilação, purga, lavagem ou inertização',
        '2. Perigos e controles', requiredForReview: true),
    PetField('supervisor', 'Supervisor(es) de entrada (nome completo e função)',
        '3. Equipe e funções', requiredForReview: true),
    PetField('attendant', 'Vigia(s) (nome completo e função)',
        '3. Equipe e funções', requiredForReview: true),
    PetField('entrants', 'Trabalhadores autorizados (nomes completos e funções)',
        '3. Equipe e funções', requiredForReview: true),
    PetField('rescueTeam', 'Equipe de emergência e salvamento',
        '3. Equipe e funções', requiredForReview: true),
    PetField('plannedIssue', 'Emissão proposta (data e hora)',
        '4. Validade prevista', requiredForReview: true),
    PetField('plannedEnd', 'Término previsto (data e hora)',
        '4. Validade prevista', requiredForReview: true),
    PetField('measurementTime', 'Data/hora da avaliação inicial imediatamente anterior à entrada',
        '5. Avaliação atmosférica', requiredForReview: true),
    PetField('measurementBy', 'Responsável pela medição (nome e função)',
        '5. Avaliação atmosférica', requiredForReview: true),
    PetField('detector', 'Detector: equipamento, identificação e situação de testes/calibração',
        '5. Avaliação atmosférica', requiredForReview: true),
    PetField('oxygen', 'Oxigênio O₂ (% em volume) medido',
        '5. Avaliação atmosférica', requiredForReview: true),
    PetField('lel', 'Inflamáveis (% LIE) medido',
        '5. Avaliação atmosférica', requiredForReview: true),
    PetField('toxic', 'Gases/vapores tóxicos (substância, leitura e unidade)',
        '5. Avaliação atmosférica', requiredForReview: true),
    PetField('otherAgents', 'Outros agentes avaliados (poeira, fumos, névoas)',
        '5. Avaliação atmosférica'),
    PetField('monitoring', 'Monitoramento atmosférico contínuo durante a permanência',
        '5. Avaliação atmosférica', requiredForReview: true),
    PetField('rescuePlan', 'Plano de resgate, recursos e tempo de resposta previstos',
        '6. Segurança e emergência', requiredForReview: true),
    PetField('communication', 'Comunicação com vigia e contatos de emergência',
        '6. Segurança e emergência', requiredForReview: true),
    PetField('ppe', 'EPIs, EPCs e proteção respiratória aplicáveis',
        '6. Segurança e emergência', requiredForReview: true),
    PetField('training', 'Evidências de capacitação e aptidão dos envolvidos',
        '6. Segurança e emergência', requiredForReview: true),
    PetField('hotWork', 'Trabalho a quente e permissões complementares, se aplicáveis',
        '6. Segurança e emergência'),
    PetField('closingNotes', 'Plano de encerramento, retirada de equipe e revalidação',
        '7. Encerramento', requiredForReview: true),
    PetField('reviewNotes', 'Pendências, relatos ou dúvidas para supervisor/vigia',
        '7. Encerramento'),
  ];

  static const checks = <PetCheck>[
    PetCheck('isolation', 'Isolamento de área, sinalização e controle de acesso'),
    PetCheck('lockout', 'Bloqueios de energias e etiquetagem'),
    PetCheck('atmosphere', 'Avaliação quantitativa inicial realizada fora do espaço'),
    PetCheck('calibration', 'Verificação de detector, calibração e teste de resposta'),
    PetCheck('ventilation', 'Ventilação e controle atmosférico previstos'),
    PetCheck('continuous', 'Monitoramento atmosférico contínuo disponível'),
    PetCheck('attendant', 'Vigia presente, com comunicação e sem outras tarefas'),
    PetCheck('training', 'Capacitação e aptidão pertinentes conferidas'),
    PetCheck('rescue', 'Plano e equipe de resgate disponíveis'),
    PetCheck('equipment', 'Equipamentos e proteção adequados à atividade'),
    PetCheck('entrance', 'Medidas específicas do espaço antes da entrada'),
  ];

  static PetField? field(String key) {
    for (final item in fields) {
      if (item.key == key) return item;
    }
    return null;
  }
}

/// Leitura informada pelo técnico; não atesta condições seguras.
class SstPetAtmosphereReading {
  const SstPetAtmosphereReading({
    required this.id, required this.dateTime, required this.point,
    required this.oxygen, required this.lel, required this.toxic,
    required this.detector, required this.measuredBy,
  });
  final String id, dateTime, point, oxygen, lel, toxic, detector, measuredBy;

  static bool _percent(String raw) {
    final n = double.tryParse(raw.trim().replaceAll(',', '.'));
    return n != null && n.isFinite && n >= 0 && n <= 100;
  }

  bool get complete => id.isNotEmpty && dateTime.trim().isNotEmpty &&
      point.trim().isNotEmpty && detector.trim().isNotEmpty &&
      measuredBy.trim().isNotEmpty && toxic.trim().isNotEmpty &&
      _percent(oxygen) && _percent(lel);

  Map<String, dynamic> toJson() => {
    'id': id, 'dateTime': dateTime, 'point': point,
    'oxygen': oxygen, 'lel': lel, 'toxic': toxic,
    'detector': detector, 'measuredBy': measuredBy,
  };

  factory SstPetAtmosphereReading.fromJson(Map<String, dynamic> json) {
    String field(String key, {int max = 250}) {
      final raw = (json[key] ?? '').toString().trim();
      return raw.length > max ? raw.substring(0, max) : raw;
    }
    final value = SstPetAtmosphereReading(
      id: field('id', max: 80),
      dateTime: field('dateTime'),
      point: field('point'),
      oxygen: field('oxygen', max: 25),
      lel: field('lel', max: 25),
      toxic: field('toxic', max: 500),
      detector: field('detector'),
      measuredBy: field('measuredBy'),
    );
    if (!RegExp(r'^[a-z0-9-]{8,80}$').hasMatch(value.id) ||
        !value.complete) {
      throw const FormatException('Leitura atmosférica inválida');
    }
    return value;
  }
}

class SstPetDraft {
  const SstPetDraft({
    required this.id,
    required this.companyId,
    required this.userId,
    this.values = const <String, String>{},
    this.checks = const <String, PetCheckStatus>{},
    this.checkNotes = const <String, String>{},
    this.readings = const <SstPetAtmosphereReading>[],
  });
  final String id, companyId, userId;
  final Map<String, String> values;
  final Map<String, PetCheckStatus> checks;
  final Map<String, String> checkNotes;
  final List<SstPetAtmosphereReading> readings;

  SstPetDraft withReading(SstPetAtmosphereReading reading) {
    if (!reading.complete || readings.length >= 30 ||
        readings.any((r) => r.id == reading.id)) {
      throw StateError('Leitura inválida, repetida ou limite excedido');
    }
    return SstPetDraft(
      id: id, companyId: companyId, userId: userId,
      values: values, checks: checks, checkNotes: checkNotes,
      readings: List.unmodifiable([...readings, reading]),
    );
  }

  SstPetDraft withoutReading(String targetId) => SstPetDraft(
    id: id, companyId: companyId, userId: userId,
    values: values, checks: checks, checkNotes: checkNotes,
    readings: List.unmodifiable(
      readings.where((item) => item.id != targetId)),
  );

  String value(String key) => values[key] ?? '';
  PetCheckStatus status(String key) =>
      checks[key] ?? PetCheckStatus.notChecked;
  String note(String key) => checkNotes[key] ?? '';

  SstPetDraft withValue(String key, String data) {
    if (PetTemplate.field(key) == null) {
      throw ArgumentError('Campo não reconhecido');
    }
    return SstPetDraft(
      id: id, companyId: companyId, userId: userId,
      values: {...values, key: data.trim()},
      checks: checks, checkNotes: checkNotes, readings: readings,
    );
  }

  SstPetDraft withCheck(String key, PetCheckStatus result,
      {String? note}) {
    if (!PetTemplate.checks.any((item) => item.key == key)) {
      throw ArgumentError('Conferência não reconhecida');
    }
    return SstPetDraft(
      id: id, companyId: companyId, userId: userId,
      values: values, checks: {...checks, key: result},
      checkNotes: {...checkNotes, if (note != null) key: note.trim()},
      readings: readings,
    );
  }

  int get completedRequired => PetTemplate.fields
      .where((field) => field.requiredForReview &&
          value(field.key).isNotEmpty).length;
  int get requiredTotal => PetTemplate.fields
      .where((field) => field.requiredForReview).length;

  List<String> get pending => [
    for (final field in PetTemplate.fields)
      if (field.requiredForReview && value(field.key).isEmpty) field.label,
    for (final check in PetTemplate.checks)
      if (status(check.key) == PetCheckStatus.notChecked) check.label,
    for (final check in PetTemplate.checks)
      if (status(check.key) == PetCheckStatus.notApplicable &&
          note(check.key).trim().isEmpty)
        'Justificar: ' + check.label,
    if (!_measurementValid(value('oxygen'))) 'Leitura de O₂ inválida/ausente',
    if (!_measurementValid(value('lel'))) 'Leitura de %LIE inválida/ausente',
    for (final reading in readings)
      if (!reading.complete) 'Leitura complementar inválida',
  ];

  /// Destaca falhas e ausências prioritárias, sem declarar aprovação.
  List<String> get criticalAlerts => [
    for (final check in PetTemplate.checks)
      if (status(check.key) == PetCheckStatus.reportedNo)
        'Controle não atendido: ' + check.label,
    for (final key in const ['supervisor', 'attendant', 'entrants',
        'rescuePlan', 'monitoring'])
      if (value(key).trim().isEmpty)
        'Campo essencial pendente: ' + (PetTemplate.field(key)?.label ?? key),
    if (!_measurementValid(value('oxygen')) ||
        !_measurementValid(value('lel')))
      'Leituras atmosféricas iniciais não conferidas',
  ];

  /// É só a conclusão do rascunho para PDF. Não é liberação para entrada.
  bool get readyForReviewPdf => pending.isEmpty;

  static bool _measurementValid(String raw) {
    final value = double.tryParse(raw.trim().replaceAll(',', '.'));
    return value != null && value.isFinite && value >= 0 && value <= 100;
  }

  Map<String, dynamic> toJson() => {
    'version': 1, 'id': id, 'companyId': companyId, 'userId': userId,
    'values': values,
    'checks': checks.map((key, value) => MapEntry(key, value.name)),
    'checkNotes': checkNotes,
    'readings': readings.map((r) => r.toJson()).toList(),
  };

  factory SstPetDraft.fromJson(Map<String, dynamic> json, {
    required String expectedCompany, required String expectedUser,
  }) {
    if (json['version'] != 1 ||
        json['companyId'] != expectedCompany ||
        json['userId'] != expectedUser ||
        json['values'] is! Map || json['checks'] is! Map ||
        json['checkNotes'] is! Map) {
      throw const FormatException('Rascunho fora da empresa/conta');
    }
    final id = (json['id'] ?? '').toString();
    if (!RegExp(r'^[a-z0-9-]{8,80}$').hasMatch(id)) {
      throw const FormatException('Identificador PET inválido');
    }
    final inputValues = Map<String, dynamic>.from(json['values'] as Map);
    final inputChecks = Map<String, dynamic>.from(json['checks'] as Map);
    final inputNotes = Map<String, dynamic>.from(json['checkNotes'] as Map);
    final values = <String, String>{};
    final statuses = <String, PetCheckStatus>{};
    final notes = <String, String>{};
    final readings = <SstPetAtmosphereReading>[];
    final rawReadings = json['readings'] ?? const <dynamic>[];
    if (rawReadings is! List || rawReadings.length > 30) {
      throw const FormatException('Histórico de leituras inválido');
    }
    final seenIds = <String>{};
    for (final raw in rawReadings) {
      if (raw is! Map) throw const FormatException('Leitura inválida');
      final reading = SstPetAtmosphereReading.fromJson(
        Map<String, dynamic>.from(raw));
      if (!seenIds.add(reading.id)) {
        throw const FormatException('Leitura duplicada');
      }
      readings.add(reading);
    }
    for (final field in PetTemplate.fields) {
      final v = (inputValues[field.key] ?? '').toString();
      values[field.key] = v.length > 2600 ? v.substring(0, 2600) : v;
    }
    for (final check in PetTemplate.checks) {
      final raw = (inputChecks[check.key] ?? '').toString();
      statuses[check.key] = PetCheckStatus.values.firstWhere(
        (status) => status.name == raw,
        orElse: () => PetCheckStatus.notChecked,
      );
      final note = (inputNotes[check.key] ?? '').toString();
      notes[check.key] = note.length > 500 ? note.substring(0, 500) : note;
    }
    return SstPetDraft(
      id: id, companyId: expectedCompany, userId: expectedUser,
      values: Map.unmodifiable(values), checks: Map.unmodifiable(statuses),
      checkNotes: Map.unmodifiable(notes),
      readings: List.unmodifiable(readings),
    );
  }
}

/// Chaves dedicadas, sem modificação do banco/GS do aplicativo.
class SstPetStore {
  const SstPetStore({required this.read, required this.write});
  final Future<String> Function(String) read;
  final Future<void> Function(String, String) write;

  static String _prefix(String user, String company) =>
      'pet_nr33_draft_v1_' + Uri.encodeComponent(user) + '_' +
      Uri.encodeComponent(company);

  static String draftKey(String user, String company) =>
      _prefix(user, company) + '_active';
  static String indexKey(String user, String company) =>
      _prefix(user, company) + '_index';
  static String itemKey(String user, String company, String id) =>
      _prefix(user, company) + '_item_' + id;

  static String newId() =>
      DateTime.now().microsecondsSinceEpoch.toRadixString(36) + '-' +
      Random.secure().nextInt(0x7fffffff).toRadixString(36);

  SstPetDraft fresh(String user, String company) => SstPetDraft(
    id: newId(), companyId: company, userId: user,
  );

  Future<SstPetDraft> load(String user, String company) async {
    final data = await read(draftKey(user, company));
    if (data.trim().isEmpty) return fresh(user, company);
    final json = jsonDecode(data);
    if (json is! Map) throw const FormatException('Rascunho PET inválido');
    return SstPetDraft.fromJson(Map<String, dynamic>.from(json),
      expectedCompany: company, expectedUser: user);
  }

  Future<void> save(SstPetDraft draft) async {
    await write(draftKey(draft.userId, draft.companyId),
        jsonEncode(draft.toJson()));
  }

  Future<List<String>> list(String user, String company) async {
    final data = await read(indexKey(user, company));
    if (data.trim().isEmpty) return const [];
    final json = jsonDecode(data);
    if (json is! Map || json['version'] != 1 ||
        json['userId'] != user || json['companyId'] != company ||
        json['ids'] is! List) {
      throw const FormatException('Histórico PET inválido');
    }
    final ids = (json['ids'] as List).whereType<String>().toList();
    if (ids.length > 50 || ids.length != (json['ids'] as List).length ||
        ids.toSet().length != ids.length ||
        ids.any((id) => !RegExp(r'^[a-z0-9-]{8,80}$').hasMatch(id))) {
      throw const FormatException('Índice PET inconsistente');
    }
    return List.unmodifiable(ids);
  }

  Future<void> archive(SstPetDraft draft) async {
    if (!draft.readyForReviewPdf) throw StateError('Minuta incompleta');
    final ids = await list(draft.userId, draft.companyId);
    if (ids.contains(draft.id)) throw StateError('Já arquivada');
    if (ids.length >= 50) throw StateError('Limite de minutas atingido');
    await write(itemKey(draft.userId, draft.companyId, draft.id),
        jsonEncode(draft.toJson()));
    await write(indexKey(draft.userId, draft.companyId), jsonEncode({
      'version': 1, 'userId': draft.userId,
      'companyId': draft.companyId, 'ids': [draft.id, ...ids],
    }));
  }

  Future<SstPetDraft> open(String user, String company, String id) async {
    if (!(await list(user, company)).contains(id)) {
      throw StateError('Minuta PET não encontrada neste acesso');
    }
    final json = jsonDecode(await read(itemKey(user, company, id)));
    if (json is! Map) throw const FormatException('Arquivo PET inválido');
    final draft = SstPetDraft.fromJson(Map<String, dynamic>.from(json),
      expectedCompany: company, expectedUser: user);
    if (draft.id != id) throw const FormatException('ID PET divergente');
    return draft;
  }
}

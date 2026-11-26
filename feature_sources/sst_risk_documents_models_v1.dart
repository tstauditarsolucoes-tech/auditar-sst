import 'dart:convert';
import 'dart:math';
import 'sst_scope_key.dart';

/// APR e AR avaliam perigos; PT e uma permissao sujeita a autorizacao real.
enum SstRiskDocKind { apr, pt, ar }

extension SstRiskDocKindLabel on SstRiskDocKind {
  String get title {
    switch (this) {
      case SstRiskDocKind.apr: return 'APR - Análise Preliminar de Riscos';
      case SstRiskDocKind.pt: return 'PT - Permissão de Trabalho';
      case SstRiskDocKind.ar: return 'AR - Análise de Risco';
    }
  }
  String get subtitle {
    switch (this) {
      case SstRiskDocKind.apr:
        return 'Etapas, perigos, consequências e medidas preventivas';
      case SstRiskDocKind.pt:
        return 'Conferência de condições, validade e autorização pendente';
      case SstRiskDocKind.ar:
        return 'Riscos, controles e condições impeditivas da atividade';
    }
  }
  String get help {
    switch (this) {
      case SstRiskDocKind.apr:
        return 'Divida a tarefa em etapas. Para cada etapa registre '
            'perigo, consequência, controles e responsável.';
      case SstRiskDocKind.pt:
        return 'Prepare uma minuta de PT. A execução depende de aprovação '
            'real pelo responsável competente, validação das condições '
            'e cumprimento da NR específica da atividade.';
      case SstRiskDocKind.ar:
        return 'Registre perigos, riscos, controles e condições impeditivas. '
            'Em altura, observe os requisitos específicos da NR-35.';
    }
  }
}

String _limit(dynamic raw, [int n = 2400]) {
  final s = (raw ?? '').toString().trim();
  return s.length > n ? s.substring(0, n) : s;
}
int _rating(dynamic raw) {
  if (raw is! int || raw < 1 || raw > 5) {
    throw const FormatException('Escala fora do intervalo 1 a 5');
  }
  return raw;
}

class SstRiskDocItem {
  const SstRiskDocItem({
    required this.id, this.step = '', this.hazard = '', this.consequence = '',
    this.controls = '', this.owner = '', this.probability = 3,
    this.severity = 3, this.presetUnreviewed = false,
  });
  final String id, step, hazard, consequence, controls, owner;
  final int probability, severity;
  /// Sugestões importadas não podem desbloquear PDF sem revisão.
  final bool presetUnreviewed;
  int get illustrativeScore => probability * severity;
  bool get complete =>
      !presetUnreviewed &&
      step.isNotEmpty && hazard.isNotEmpty && consequence.isNotEmpty &&
      controls.isNotEmpty && owner.isNotEmpty;

  SstRiskDocItem copyWith({
    String? step, String? hazard, String? consequence, String? controls,
    String? owner, int? probability, int? severity,
    bool? presetUnreviewed,
  }) => SstRiskDocItem(
    id: id,
    step: step ?? this.step, hazard: hazard ?? this.hazard,
    consequence: consequence ?? this.consequence,
    controls: controls ?? this.controls, owner: owner ?? this.owner,
    probability: probability ?? this.probability,
    severity: severity ?? this.severity,
    presetUnreviewed: presetUnreviewed ?? this.presetUnreviewed,
  );

  Map<String, dynamic> toJson() => {
    'id': id, 'step': step, 'hazard': hazard,
    'consequence': consequence, 'controls': controls, 'owner': owner,
    'probability': probability, 'severity': severity,
    'presetUnreviewed': presetUnreviewed,
  };

  factory SstRiskDocItem.fromJson(Map<String, dynamic> json) {
    final id = _limit(json['id'], 80);
    if (!RegExp(r'^[a-zA-Z0-9_-]{5,80}$').hasMatch(id)) {
      throw const FormatException('Identificador de etapa inválido');
    }
    return SstRiskDocItem(
      id: id,
      step: _limit(json['step']), hazard: _limit(json['hazard']),
      consequence: _limit(json['consequence']),
      controls: _limit(json['controls']), owner: _limit(json['owner'], 180),
      probability: _rating(json['probability']),
      severity: _rating(json['severity']),
      presetUnreviewed: json['presetUnreviewed'] == true,
    );
  }
}

class SstRiskDocDraft {
  const SstRiskDocDraft({
    required this.id, required this.kind, required this.companyId,
    this.activity = '', this.sector = '', this.date = '',
    this.preparedBy = '', this.blockers = '', this.emergency = '',
    this.team = '', this.validUntil = '', this.authorizer = '',
    this.referenceAr = '', this.items = const <SstRiskDocItem>[],
  });

  final String id, companyId;
  final SstRiskDocKind kind;
  final String activity, sector, date, preparedBy, blockers, emergency;
  final String team, validUntil, authorizer, referenceAr;
  final List<SstRiskDocItem> items;

  bool get canExportDraft =>
      activity.trim().isNotEmpty && sector.trim().isNotEmpty &&
      date.trim().isNotEmpty && preparedBy.trim().isNotEmpty &&
      blockers.trim().isNotEmpty && emergency.trim().isNotEmpty &&
      items.isNotEmpty && items.every((item) => item.complete) &&
      (kind != SstRiskDocKind.pt || (
        team.trim().isNotEmpty && validUntil.trim().isNotEmpty &&
        authorizer.trim().isNotEmpty && referenceAr.trim().isNotEmpty
      ));

  SstRiskDocDraft copyWith({
    String? activity, String? sector, String? date, String? preparedBy,
    String? blockers, String? emergency, String? team, String? validUntil,
    String? authorizer, String? referenceAr, List<SstRiskDocItem>? items,
  }) => SstRiskDocDraft(
    id: id, kind: kind, companyId: companyId,
    activity: activity ?? this.activity,
    sector: sector ?? this.sector,
    date: date ?? this.date,
    preparedBy: preparedBy ?? this.preparedBy,
    blockers: blockers ?? this.blockers,
    emergency: emergency ?? this.emergency,
    team: team ?? this.team,
    validUntil: validUntil ?? this.validUntil,
    authorizer: authorizer ?? this.authorizer,
    referenceAr: referenceAr ?? this.referenceAr,
    items: items ?? this.items,
  );

  Map<String, dynamic> toJson() => {
    'version': 1, 'id': id, 'kind': kind.name, 'companyId': companyId,
    'activity': activity, 'sector': sector, 'date': date,
    'preparedBy': preparedBy, 'blockers': blockers,
    'emergency': emergency, 'team': team, 'validUntil': validUntil,
    'authorizer': authorizer, 'referenceAr': referenceAr,
    'items': items.map((x) => x.toJson()).toList(),
  };

  factory SstRiskDocDraft.fromJson(Map<String, dynamic> json, {
    required String companyId, required SstRiskDocKind kind,
  }) {
    if (json['version'] != 1 || json['kind'] != kind.name ||
        json['companyId'] != companyId || json['items'] is! List) {
      throw const FormatException('Rascunho de outra empresa ou inválido');
    }
    final id = _limit(json['id'], 80);
    if (!RegExp(r'^[a-zA-Z0-9_-]{5,80}$').hasMatch(id)) {
      throw const FormatException('Identificador do documento inválido');
    }
    final rows = json['items'] as List;
    if (rows.length > 50) throw const FormatException('Etapas excedidas');
    final seen = <String>{};
    final items = <SstRiskDocItem>[];
    for (final row in rows) {
      if (row is! Map) throw const FormatException('Etapa inválida');
      final item = SstRiskDocItem.fromJson(Map<String, dynamic>.from(row));
      if (!seen.add(item.id)) throw const FormatException('Etapa duplicada');
      items.add(item);
    }
    return SstRiskDocDraft(
      id: id, kind: kind, companyId: companyId,
      activity: _limit(json['activity']), sector: _limit(json['sector']),
      date: _limit(json['date'], 64),
      preparedBy: _limit(json['preparedBy'], 180),
      blockers: _limit(json['blockers']),
      emergency: _limit(json['emergency']),
      team: _limit(json['team']),
      validUntil: _limit(json['validUntil'], 64),
      authorizer: _limit(json['authorizer'], 180),
      referenceAr: _limit(json['referenceAr'], 180),
      items: List.unmodifiable(items),
    );
  }
}

/// Usa settings local ja disponivel; nao altera esquema nem sincronizacao.
class SstRiskDocStore {
  const SstRiskDocStore({required this.read, required this.write});
  final Future<String> Function(String) read;
  final Future<void> Function(String, String) write;

  static String _prefix(String user, String company, SstRiskDocKind kind) =>
      sstScopedKey('risk_doc_v2', [user, company, kind.name]);

  static String draftKey(String user, String company, SstRiskDocKind kind) =>
      _prefix(user, company, kind) + '_draft';
  static String archiveKey(String user, String company,
      SstRiskDocKind kind, String id) =>
      _prefix(user, company, kind) + '_archive_' + id;
  static String indexKey(String user, String company, SstRiskDocKind kind) =>
      _prefix(user, company, kind) + '_index';

  static String newId() =>
      DateTime.now().microsecondsSinceEpoch.toRadixString(36) + '-' +
      Random.secure().nextInt(0x7fffffff).toRadixString(36);

  SstRiskDocDraft fresh(String company, SstRiskDocKind kind) =>
      SstRiskDocDraft(
        id: newId(), kind: kind, companyId: company,
        date: DateTime.now().toIso8601String().substring(0, 10),
      );

  Future<SstRiskDocDraft> load(String user, String company,
      SstRiskDocKind kind) async {
    final raw = await read(draftKey(user, company, kind));
    if (raw.isEmpty) return fresh(company, kind);
    final value = jsonDecode(raw);
    if (value is! Map) throw const FormatException('Rascunho inválido');
    return SstRiskDocDraft.fromJson(
      Map<String, dynamic>.from(value), companyId: company, kind: kind);
  }

  Future<void> save(String user, String company, SstRiskDocDraft draft) {
    if (company != draft.companyId) {
      throw StateError('Empresa divergente');
    }
    return write(draftKey(user, company, draft.kind),
        jsonEncode(draft.toJson()));
  }

  Future<List<String>> listArchives(String user, String company,
      SstRiskDocKind kind) async {
    final raw = await read(indexKey(user, company, kind));
    if (raw.isEmpty) return const [];
    final value = jsonDecode(raw);
    if (value is! Map || value['version'] != 1 ||
        value['user'] != user || value['companyId'] != company ||
        value['kind'] != kind.name || value['ids'] is! List) {
      throw const FormatException('Índice do histórico inválido');
    }
    final items = (value['ids'] as List).whereType<String>().toList();
    if (items.length > 30 || items.toSet().length != items.length ||
        items.any((id) => !RegExp(r'^[a-zA-Z0-9_-]{5,80}$').hasMatch(id))) {
      throw const FormatException('Histórico inválido');
    }
    return List.unmodifiable(items);
  }

  Future<void> archive(String user, String company, SstRiskDocDraft draft) async {
    if (draft.companyId != company || !draft.canExportDraft) {
      throw StateError('Rascunho incompleto ou empresa divergente');
    }
    final ids = await listArchives(user, company, draft.kind);
    if (ids.contains(draft.id)) {
      throw StateError('Documento já arquivado; não sobrescrever');
    }
    if (ids.length >= 30) throw StateError('Limite local de versões atingido');
    await write(archiveKey(user, company, draft.kind, draft.id),
        jsonEncode(draft.toJson()));
    await write(indexKey(user, company, draft.kind), jsonEncode({
      'version': 1, 'user': user, 'companyId': company,
      'kind': draft.kind.name, 'ids': [draft.id, ...ids],
    }));
  }

  Future<SstRiskDocDraft> openArchive(String user, String company,
      SstRiskDocKind kind, String id) async {
    final ids = await listArchives(user, company, kind);
    if (!ids.contains(id)) throw StateError('Documento não encontrado');
    final raw = await read(archiveKey(user, company, kind, id));
    final value = jsonDecode(raw);
    if (value is! Map) throw const FormatException('Arquivo inválido');
    final result = SstRiskDocDraft.fromJson(
      Map<String, dynamic>.from(value), companyId: company, kind: kind);
    if (result.id != id) throw const FormatException('ID divergente');
    return result;
  }
}

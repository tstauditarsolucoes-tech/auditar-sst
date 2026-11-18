import 'dart:convert';
import 'dart:math';

/// Eventos locais vinculados a uma NC já existente. Não cria NC, não muda
/// seu status oficial e não envia dados à Central.
enum NcFollowupKind { persists, photo, correctionReported }

class NcFollowupEvent {
  const NcFollowupEvent({
    required this.id,
    required this.companyId,
    required this.ncId,
    required this.authorId,
    required this.at,
    required this.kind,
    required this.note,
    this.photoPath,
  });
  final String id, companyId, ncId, authorId, at, note;
  final NcFollowupKind kind;
  final String? photoPath;

  Map<String, Object?> toJson() => {
    'id': id, 'companyId': companyId, 'ncId': ncId, 'authorId': authorId,
    'at': at, 'kind': kind.name, 'note': note,
    if (photoPath != null) 'photoPath': photoPath,
  };

  factory NcFollowupEvent.fromJson(Map<String, dynamic> row,
      {required String companyId, required String ncId}) {
    if (row['companyId'] != companyId || row['ncId'] != ncId) {
      throw const FormatException('Empresa ou NC divergente.');
    }
    final kindName = (row['kind'] ?? '').toString();
    final candidates = NcFollowupKind.values.where((v) => v.name == kindName);
    final id = (row['id'] ?? '').toString();
    final author = (row['authorId'] ?? '').toString();
    final date = (row['at'] ?? '').toString();
    final note = (row['note'] ?? '').toString();
    if (candidates.length != 1 || id.isEmpty || author.isEmpty ||
        DateTime.tryParse(date) == null || note.trim().length < 8 ||
        note.length > 1000) {
      throw const FormatException('Evento de acompanhamento inválido.');
    }
    return NcFollowupEvent(
      id: id, companyId: companyId, ncId: ncId, authorId: author,
      at: date, kind: candidates.single, note: note,
      photoPath: row['photoPath'] is String ? row['photoPath'] as String : null,
    );
  }
}

class NcFollowupLedger {
  const NcFollowupLedger({required this.read, required this.write});
  final Future<String> Function(String key) read;
  final Future<void> Function(String key, String value) write;

  static String key(String companyId, String ncId, String userId) {
    if (companyId.trim().isEmpty || ncId.trim().isEmpty || userId.trim().isEmpty) {
      throw ArgumentError('Empresa e NC obrigatórias.');
    }
    return 'auditar_nc_followup_v1_' + Uri.encodeComponent(userId) + '_' +
        Uri.encodeComponent(companyId) + '_' + Uri.encodeComponent(ncId);
  }

  static String newId() =>
      DateTime.now().microsecondsSinceEpoch.toRadixString(36) + '-' +
      Random.secure().nextInt(0x7fffffff).toRadixString(36);

  Future<List<NcFollowupEvent>> list(String companyId, String ncId, String userId) async {
    final raw = await read(key(companyId, ncId, userId));
    if (raw.trim().isEmpty) return const [];
    final json = jsonDecode(raw);
    if (json is! Map || json['version'] != 1 ||
        json['companyId'] != companyId || json['ncId'] != ncId ||
        json['userId'] != userId ||
        json['events'] is! List) {
      throw const FormatException('Histórico local inválido.');
    }
    final result = <NcFollowupEvent>[];
    final seen = <String>{};
    for (final item in json['events'] as List) {
      if (item is! Map) throw const FormatException('Evento inválido.');
      final event = NcFollowupEvent.fromJson(Map<String,dynamic>.from(item),
          companyId: companyId, ncId: ncId);
      if (event.authorId != userId || !seen.add(event.id)) {
        throw const FormatException('Evento de outro usuário ou duplicado.');
      }
      result.add(event);
    }
    return List.unmodifiable(result);
  }

  /// Reenvios idênticos não duplicam; colisões divergentes são rejeitadas.
  Future<List<NcFollowupEvent>> append(NcFollowupEvent event) async {
    if (event.companyId.isEmpty || event.ncId.isEmpty ||
        event.authorId.isEmpty || event.id.isEmpty ||
        DateTime.tryParse(event.at) == null ||
        event.note.trim().length < 8 || event.note.length > 1000) {
      throw ArgumentError('Revise os dados do acompanhamento.');
    }
    final rows = await list(event.companyId, event.ncId, event.authorId);
    for (final old in rows) {
      if (old.id == event.id) {
        if (jsonEncode(old.toJson()) != jsonEncode(event.toJson())) {
          throw StateError('Identificador já existe com outro conteúdo.');
        }
        return rows;
      }
    }
    if (rows.length >= 250) {
      throw StateError('Limite de registros locais atingido.');
    }
    final updated = [...rows, event];
    await write(key(event.companyId, event.ncId, event.authorId), jsonEncode({
      'version': 1, 'companyId': event.companyId, 'ncId': event.ncId,
      'userId': event.authorId,
      'events': updated.map((e) => e.toJson()).toList(),
    }));
    return List.unmodifiable(updated);
  }
}

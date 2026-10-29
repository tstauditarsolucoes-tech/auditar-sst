// AUDITAR SST - modelo de fila NOVA para testes Dart.
// Nao conecta Flutter instalado, Apps Script, SQLite legado nem dados reais.
import 'dart:async';
import 'dart:convert';

enum DraftState { pending, conflict, acknowledged }

class NativeDraft {
  final String requestId;
  final String kind;
  final Map<String, Object?> payload;
  final DraftState state;
  final String? remoteId;
  final int attempts;
  const NativeDraft({
    required this.requestId,
    required this.kind,
    required this.payload,
    this.state = DraftState.pending,
    this.remoteId,
    this.attempts = 0,
  });
  NativeDraft copy({
    DraftState? state,
    String? remoteId,
    int? attempts,
  }) => NativeDraft(
    requestId: requestId,
    kind: kind,
    payload: Map<String, Object?>.unmodifiable(payload),
    state: state ?? this.state,
    remoteId: remoteId ?? this.remoteId,
    attempts: attempts ?? this.attempts,
  );
}

// A camada de armazenamento DEVE gravar atomicamente e sobreviver ao reboot.
// Nao existe adaptador de SQLite/secure-storage nesta etapa de teste.
abstract class NativeDraftJournalStore {
  Future<List<NativeDraft>> read();
  Future<void> replaceAtomically(List<NativeDraft> all);
}

class DraftResponse {
  final int statusCode;
  final Map<String, dynamic>? json;
  const DraftResponse(this.statusCode, this.json);
}
typedef DraftSender = Future<DraftResponse> Function(NativeDraft item);
class DrainResult {
  final int committed;
  final int conflicts;
  final int stillPending;
  const DrainResult(this.committed, this.conflicts, this.stillPending);
}

class NativeDraftOutbox {
  static final _uuid = RegExp(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    caseSensitive: false,
  );
  final NativeDraftJournalStore store;
  bool _busy = false;
  NativeDraftOutbox(this.store);

  Future<void> enqueue(NativeDraft item) async {
    if (_busy) throw StateError('Operacao simultanea da fila');
    if (!_uuid.hasMatch(item.requestId) ||
        (item.kind != 'inspection' && item.kind != 'finding') ||
        item.payload['clientRequestId'] != item.requestId ||
        item.state != DraftState.pending ||
        item.remoteId != null || item.attempts != 0) {
      throw ArgumentError('Rascunho novo invalido');
    }
    _busy = true;
    try {
      final items = await store.read();
      final previous = items.where((e) => e.requestId == item.requestId).toList();
      if (previous.isNotEmpty) {
        if (previous.length != 1 ||
            previous.single.kind != item.kind ||
            jsonEncode(previous.single.payload) != jsonEncode(item.payload)) {
          throw StateError('UUID ja existe com dados diferentes');
        }
        return; // Nunca gera nova chave ao repetir salvamento local.
      }
      if (items.length >= 100) throw StateError('Fila ficticia cheia');
      await store.replaceAtomically([...items, item]);
    } finally {
      _busy = false;
    }
  }

  Future<DrainResult> drain(DraftSender sender) async {
    if (_busy) throw StateError('Operacao simultanea da fila');
    _busy = true;
    var committed = 0, conflicts = 0;
    try {
      final items = await store.read();
      for (var i = 0; i < items.length; i++) {
        final item = items[i];
        if (item.state != DraftState.pending) continue;
        DraftResponse? result;
        try {
          result = await sender(item);
        } catch (_) {
          // Transporte offline: sem ACK. Recupera e repete mesmo UUID.
        }
        if (result == null) continue;
        var next = item.copy(attempts: item.attempts + 1);
        final remote = result.json?['item'];
        final remoteId = remote is Map ? remote['id'] : null;
        if (result.statusCode == 201 &&
            result.json?['syncEnabled'] == false &&
            result.json?['legacyQueueAcknowledged'] == false &&
            remoteId is String && _uuid.hasMatch(remoteId)) {
          next = next.copy(
            state: DraftState.acknowledged,
            remoteId: remoteId,
          );
          committed++;
        } else if (result.statusCode == 409) {
          next = next.copy(state: DraftState.conflict);
          conflicts++;
        } else if (result.statusCode == 401 || result.statusCode == 403) {
          items[i] = next;
          await store.replaceAtomically(items);
          break; // Nao insistir com sessao invalida ou usuario sem acesso.
        }
        items[i] = next;
        // Persistir apos cada envio antes de prosseguir. Crash antes do ACK
        // gera retry com mesma chave idempotente no PostgreSQL novo.
        await store.replaceAtomically(items);
      }
      return DrainResult(committed, conflicts,
        items.where((i) => i.state == DraftState.pending).length);
    } finally {
      _busy = false;
    }
  }
}

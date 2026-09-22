/// Regras determinísticas para a fila de evidências. O envio ocorre fora
/// da sincronização de cadastros, sem bloquear a abertura do aplicativo.
class MediaSyncPolicy {
  const MediaSyncPolicy._();

  static const automaticBatchLimit = 2;
  static const manualBatchLimit = 5;

  static bool shouldKick({
    required DateTime now,
    required DateTime? lastKick,
    required bool active,
    required bool lastFailed,
    required int? pendingAfterLastAttempt,
  }) {
    if (active) return false;
    if (lastKick == null) return true;
    final gap = lastFailed
        ? const Duration(minutes: 1)
        : pendingAfterLastAttempt == 0
            ? const Duration(seconds: 30)
            : const Duration(seconds: 15);
    return now.difference(lastKick) >= gap;
  }
}

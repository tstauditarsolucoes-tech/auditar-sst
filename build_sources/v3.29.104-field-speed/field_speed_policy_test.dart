import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/media_sync_policy.dart';
import 'package:auditar_sst/services/checklist_field_capture_policy.dart';

void main() {
  test('media does not wait for structured queue to be empty', () {
    final now = DateTime.utc(2026, 9, 22, 20);
    expect(MediaSyncPolicy.shouldKick(
      now: now, lastKick: null, active: false, lastFailed: false,
      pendingAfterLastAttempt: 44,
    ), isTrue);
    expect(MediaSyncPolicy.shouldKick(
      now: now, lastKick: now.subtract(const Duration(seconds: 14)),
      active: false, lastFailed: false, pendingAfterLastAttempt: 44,
    ), isFalse);
    expect(MediaSyncPolicy.shouldKick(
      now: now, lastKick: now.subtract(const Duration(seconds: 15)),
      active: false, lastFailed: false, pendingAfterLastAttempt: 44,
    ), isTrue);
    expect(MediaSyncPolicy.shouldKick(
      now: now, lastKick: now.subtract(const Duration(seconds: 45)),
      active: true, lastFailed: false, pendingAfterLastAttempt: 44,
    ), isFalse);
  });

  test('failed uploads back off; empty queues are not polled constantly', () {
    final now = DateTime.utc(2026, 9, 22, 20);
    expect(MediaSyncPolicy.shouldKick(
      now: now, lastKick: now.subtract(const Duration(seconds: 30)),
      active: false, lastFailed: true, pendingAfterLastAttempt: 8,
    ), isFalse);
    expect(MediaSyncPolicy.shouldKick(
      now: now, lastKick: now.subtract(const Duration(minutes: 1)),
      active: false, lastFailed: true, pendingAfterLastAttempt: 8,
    ), isTrue);
    expect(MediaSyncPolicy.shouldKick(
      now: now, lastKick: now.subtract(const Duration(seconds: 20)),
      active: false, lastFailed: false, pendingAfterLastAttempt: 0,
    ), isFalse);
    expect(MediaSyncPolicy.shouldKick(
      now: now, lastKick: now.subtract(const Duration(seconds: 30)),
      active: false, lastFailed: false, pendingAfterLastAttempt: 0,
    ), isTrue);
    expect(MediaSyncPolicy.automaticBatchLimit, 2);
    expect(MediaSyncPolicy.manualBatchLimit, 5);
  });

  test('fast capture never fabricates a compliant response', () {
    expect(ChecklistFieldCapturePolicy.canAddOccurrence(null), isTrue);
    expect(ChecklistFieldCapturePolicy.canAddOccurrence('Não Conforme'), isTrue);
    expect(ChecklistFieldCapturePolicy.canAddOccurrence('Conforme'), isFalse);
    expect(ChecklistFieldCapturePolicy.canAddOccurrence('Parcial'), isFalse);
    expect(ChecklistFieldCapturePolicy.isAdditionalOccurrence(
      'Não Conforme', 'Registro anterior'), isTrue);
    expect(ChecklistFieldCapturePolicy.isAdditionalOccurrence(
      null, ''), isFalse);
    expect(ChecklistFieldCapturePolicy.acceptsEvidence(7, 3), isTrue);
    expect(ChecklistFieldCapturePolicy.acceptsEvidence(9, 2), isFalse);
    expect(ChecklistFieldCapturePolicy.acceptsEvidence(0, 0), isFalse);
  });
}

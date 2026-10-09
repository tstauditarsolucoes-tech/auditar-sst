import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/field_operational_priority_service.dart';

void main() {
  group('FieldOperationalPriorityService', () {
    test('prioriza NC critica antes das demais pendencias', () {
      final items = FieldOperationalPriorityService.build(
        highCriticalOpen: 2,
        overdueActions: 3,
        recurrenceGroups: 1,
        expiredTrainings: 4,
        awaitingEvidence: 2,
        openNonConformities: 5,
        pendingSync: 6,
        daysSinceLastInspection: 40,
      );
      expect(items.first.code, 'critical_nc');
      expect(items.map((e) => e.code), contains('overdue_actions'));
      expect(items.map((e) => e.code), contains('recurrence'));
      expect(items.map((e) => e.code), contains('evidence'));
    });

    test('sem pendencias retorna estado ok', () {
      final items = FieldOperationalPriorityService.build(
        highCriticalOpen: 0,
        overdueActions: 0,
        recurrenceGroups: 0,
        expiredTrainings: 0,
        awaitingEvidence: 0,
        openNonConformities: 0,
        pendingSync: 0,
        daysSinceLastInspection: 5,
      );
      expect(items.length, 1);
      expect(items.single.code, 'ok');
    });

    test('vistoria antiga entra no roteiro', () {
      final items = FieldOperationalPriorityService.build(
        highCriticalOpen: 0,
        overdueActions: 0,
        recurrenceGroups: 0,
        expiredTrainings: 0,
        awaitingEvidence: 0,
        openNonConformities: 0,
        pendingSync: 0,
        daysSinceLastInspection: 31,
      );
      expect(items.map((e) => e.code), contains('inspection_due'));
    });
  });
}

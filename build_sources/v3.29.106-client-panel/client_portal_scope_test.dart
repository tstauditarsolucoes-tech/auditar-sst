import 'package:auditar_sst/services/management_panel_service.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('client portal defaults are per-company and non-sensitive', () {
    final scope = ManagementPanelService.defaultClientPortalModules;
    expect(scope['overview'], isTrue);
    expect(scope['actions'], isTrue);
    expect(scope['inspections'], isTrue);
    expect(scope['training'], isFalse);
    expect(scope['safety'], isFalse);
    expect(scope['improvements'], isFalse);
    expect(scope['agenda'], isFalse);
    expect(scope['extinguishers'], isFalse);
    expect(scope.containsKey('medicalExams'), isFalse);
    expect(scope.containsKey('admin'), isFalse);
  });
}

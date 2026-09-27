import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/screens/manager_reports_screen.dart';
import 'package:auditar_sst/models.dart';

void main() {
  final now = DateTime(2026, 9, 26);
  final period = ManagerReportPeriod(DateTime(2026, 9, 1), now);
  Map<String, Object?> item(String id, String status,
      {String? verifiedAt, String? dueAt}) => {
    'id': id, 'status': status,
    'verified_at': verifiedAt, 'completion_date': verifiedAt,
    'next_due_date': dueAt, 'due_date': dueAt,
  };
  test('open backlog includes NC from previous visit; closed does not', () {
    final rows = [
      item('old-open', 'Pendente', dueAt: '2026-08-01'),
      item('closed', 'Concluída', verifiedAt: '2026-09-20'),
    ];
    final selected = ManagerReportService.selectNcs(
        rows, ManagerReportKind.pending, period, 'Todas', now);
    expect(selected.map((r) => r['id']).toList(), ['old-open']);
    expect(ManagerReportService.overdue(rows.first, now), isTrue);
    expect(ManagerReportService.overdue(rows.last, now), isFalse);
  });
  test('resolved requires actual verified date within reporting period', () {
    final rows = [
      item('verified', 'Concluída', verifiedAt: '2026-09-22'),
      item('unverified', 'Concluída'),
      item('earlier', 'Concluída', verifiedAt: '2026-08-31'),
      item('reported', 'Aguardando verificação'),
    ];
    final selected = ManagerReportService.selectNcs(
        rows, ManagerReportKind.resolved, period, 'Todas', now);
    expect(selected.map((r) => r['id']).toList(), ['verified']);
  });
  test('closed action requires recorded completion date', () {
    final rows = [
      item('executed', 'Concluído', verifiedAt: '2026-09-21'),
      item('old', 'Concluído', verifiedAt: '2026-08-12'),
      item('awaiting', 'Pendente'),
    ];
    final selected = ManagerReportService.selectActions(
        rows, ManagerReportKind.resolved, period, 'Todas', now);
    expect(selected.map((r) => r['id']).toList(), ['executed']);
  });
  test('activities report does not include NC or action records as accomplishments', () {
    final rows = [item('nc', 'Pendente')];
    expect(ManagerReportService.selectNcs(rows, ManagerReportKind.activities,
        period, 'Todas', now), isEmpty);
    expect(ManagerReportService.selectActions(rows, ManagerReportKind.activities,
        period, 'Todas', now), isEmpty);
  });
  test('specific management search covers NC code, sector and responsible', () {
    final row = <String, Object?>{
      'code': 'NC-004', 'sector_name': 'Forno', 'responsible': 'Manutenção',
      'description': 'Proteção danificada',
    };
    expect(ManagerReportService.matches(row, 'nc-004'), isTrue);
    expect(ManagerReportService.matches(row, 'FORNO'), isTrue);
    expect(ManagerReportService.matches(row, 'manuten'), isTrue);
    expect(ManagerReportService.matches(row, 'Escritório'), isFalse);
  });
  test('all four report kinds generate a valid, nonempty PDF', () async {
    TestWidgetsFlutterBinding.ensureInitialized();
    final company = Company(id: 'company-test', name: 'Empresa de teste');
    const dataset = ManagerReportDataset([], [], [], []);
    for (final kind in ManagerReportKind.values) {
      final bytes = await ManagerReportService.generate(
        company: company, dataset: dataset, kind: kind,
        period: period, status: 'Todas', includePhotos: false,
      );
      expect(bytes.length, greaterThan(1024), reason: kind.label);
      expect(String.fromCharCodes(bytes.take(4)), '%PDF');
    }
  });
  test('period respects date-only boundaries', () {
    expect(period.contains(DateTime(2026, 9, 1, 0, 0)), isTrue);
    expect(period.contains(DateTime(2026, 9, 26, 23, 59)), isTrue);
    expect(period.contains(DateTime(2026, 8, 31, 23, 59)), isFalse);
    expect(period.contains(DateTime(2026, 9, 27)), isFalse);
  });
}

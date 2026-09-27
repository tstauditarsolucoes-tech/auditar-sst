import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/auth_service.dart';
import 'package:auditar_sst/services/admin_access_policy.dart';

AuditarUser account(
  String role, {
  bool active = true,
  bool allCompanies = false,
  List<String> companies = const [],
}) => AuditarUser(
      id: role,
      name: role,
      email: role + '@example.com',
      role: role,
      active: active,
      allCompanies: allCompanies,
      companyIds: companies,
      clientPermissions: const <String, bool>{},
    );

void main() {
  test('all administrative capabilities belong only to active admin', () {
    final admin = account('admin');
    final technician = account('tecnico', companies: ['company-a']);
    final client = account('cliente', companies: ['company-a']);
    for (final capability in AuditarAdminCapability.values) {
      expect(AuditarAdminAccess.can(admin, capability), isTrue);
      expect(AuditarAdminAccess.can(technician, capability), isFalse);
      expect(AuditarAdminAccess.can(client, capability), isFalse);
      expect(AuditarAdminAccess.can(account('admin', active: false), capability),
          isFalse);
    }
  });

  test('admin can see all companies; technician remains scoped', () {
    expect(AuditarAdminAccess.canAccessCompany(account('admin'), 'company-b'),
        isTrue);
    expect(AuditarAdminAccess.canAccessCompany(
        account('tecnico', companies: ['company-a']), 'company-b'), isFalse);
    expect(AuditarAdminAccess.canAccessCompany(
        account('tecnico', companies: ['company-a']), 'company-a'), isTrue);
    expect(AuditarAdminAccess.canAccessCompany(
        account('cliente', companies: ['company-a']), 'company-a'), isFalse);
  });

  test('client and inactive accounts cannot operate the app', () {
    expect(AuditarAdminAccess.canOperate(account('admin')), isTrue);
    expect(AuditarAdminAccess.canOperate(account('tecnico')), isTrue);
    expect(AuditarAdminAccess.canOperate(account('cliente')), isFalse);
    expect(AuditarAdminAccess.canOperate(account('admin', active: false)),
        isFalse);
  });
}

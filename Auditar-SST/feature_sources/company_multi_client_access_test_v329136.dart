import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/auth_service.dart';
import 'package:auditar_sst/widgets/company_client_access_section.dart';

void main() {
  AuditarUser user(String id, String email, List<String> companies,
      {bool active = true, bool allCompanies = false}) => AuditarUser(
        id: id,
        name: id,
        email: email,
        role: 'cliente',
        active: active,
        allCompanies: allCompanies,
        companyIds: companies,
        clientPermissions: const {'indicadores': true},
      );

  test('manager and director belong to one shared company panel', () {
    final people = [
      user('gerente', 'gerente@exemplo.test', ['empresa-a']),
      user('diretoria', 'diretoria@exemplo.test', ['empresa-a']),
      user('outra', 'outra@exemplo.test', ['empresa-b']),
    ];
    final selected = people
        .where((u) => ClientCompanyAccessRules.belongsTo(u, 'empresa-a'))
        .toList();
    expect(selected.map((u) => u.id), ['gerente', 'diretoria']);
    expect(selected.every((u) => u.companyIds.single == 'empresa-a'), isTrue);
  });

  test('one person may be deactivated without removing other accounts', () {
    final people = [
      user('gerente', 'gerente@exemplo.test', ['empresa-a'], active: false),
      user('diretoria', 'diretoria@exemplo.test', ['empresa-a']),
    ];
    final selected = people
        .where((u) => ClientCompanyAccessRules.belongsTo(u, 'empresa-a'))
        .toList();
    expect(selected.length, 2);
    expect(selected.where((u) => u.active).single.id, 'diretoria');
  });

  test('duplicate e-mail is case-insensitive but edit keeps own address', () {
    final people = [
      user('gerente', 'Gerente@Exemplo.test', ['empresa-a']),
      user('diretoria', 'diretoria@exemplo.test', ['empresa-a']),
    ];
    expect(ClientCompanyAccessRules.duplicates(
        people, ' GERENTE@exemplo.test ', null), isTrue);
    expect(ClientCompanyAccessRules.duplicates(
        people, 'gerente@exemplo.test', 'gerente'), isFalse);
    expect(ClientCompanyAccessRules.duplicates(
        people, 'rh@exemplo.test', null), isFalse);
  });

  test('client scope rejects zero, multiple, and unrestricted companies', () {
    expect(ClientCompanyAccessRules.belongsTo(
      user('sem', 'sem@exemplo.test', []), 'empresa-a'), isFalse);
    expect(ClientCompanyAccessRules.belongsTo(
      user('ambas', 'ambas@exemplo.test', ['empresa-a', 'empresa-b']),
      'empresa-a'), isFalse);
    expect(ClientCompanyAccessRules.belongsTo(
      user('amplo', 'amplo@exemplo.test', ['empresa-a'], allCompanies: true),
      'empresa-a'), isFalse);
  });
}

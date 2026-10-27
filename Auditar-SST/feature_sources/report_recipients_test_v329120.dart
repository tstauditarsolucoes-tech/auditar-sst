import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/report_recipients.dart';

void main() {
  test('company supports one main plus multiple additional emails', () {
    expect(ReportRecipients.parse(
      'SST@Empresa.com', 'gerencia@empresa.com\nfinanceiro@empresa.com;rh@empresa.com'),
      ['sst@empresa.com', 'gerencia@empresa.com',
       'financeiro@empresa.com', 'rh@empresa.com']);
  });
  test('duplicate addresses are removed and legacy secondary stays valid', () {
    expect(ReportRecipients.parse(
      'sst@empresa.com', 'SST@EMPRESA.COM, RH@empresa.com; rh@empresa.com'),
      ['sst@empresa.com','rh@empresa.com']);
    expect(ReportRecipients.normalizedAdditional(
      'sst@empresa.com','SST@empresa.com, Rh@empresa.com'),
      'rh@empresa.com');
  });
  test('invalid address or more than ten recipients is blocked', () {
    expect(ReportRecipients.validationError(
      'sst@empresa.com','rh@empresa.com,not-an-email'),isNotNull);
    expect(ReportRecipients.validationError(
      'sst@empresa.com',
      List.generate(10,(i)=>'email$i@empresa.com').join(',')),isNotNull);
    expect(ReportRecipients.validationError(
      'sst@empresa.com',
      List.generate(9,(i)=>'email$i@empresa.com').join(',')),isNull);
  });
}

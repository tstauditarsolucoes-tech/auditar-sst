import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:auditar_sst/database.dart';
import 'package:auditar_sst/widgets/company_organization.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late Directory temp;
  setUpAll(() async {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
    temp = await Directory.systemTemp.createTemp('auditar_groups_');
    await databaseFactory.setDatabasesPath(temp.path);
    await AppDatabase.activateUser('group_test');
  });
  tearDownAll(() async { await AppDatabase.deactivateUser(); await temp.delete(recursive: true); });
  test('Persistência, duplicação normalizada e movimentação sem alterar schema', () async {
    final db = await AppDatabase.instance.database;
    final schema = await db.rawQuery('SELECT name, sql FROM sqlite_master ORDER BY name');
    final organization = CompanyOrganization();
    await organization.assign(['one', 'two'], 'Construtora Quality', type: 'Obra');
    await organization.assign(['one'], ' construtora   QUALITY ', favorite: true);
    var loaded = await CompanyOrganization.load();
    expect(loaded.groups, ['Construtora Quality']);
    expect(loaded.type('one'), 'Obra');
    expect(loaded.favorite('one'), true);
    await loaded.assign(['one'], '');
    loaded = await CompanyOrganization.load();
    expect(loaded.group('one'), '');
    expect(loaded.group('two'), 'Construtora Quality');
    expect(loaded.type('one'), 'Obra');
    expect(await db.rawQuery('SELECT name, sql FROM sqlite_master ORDER BY name'), schema);
    await AppDatabase.activateUser('other_user');
    expect((await CompanyOrganization.load()).groups, isEmpty);
    await AppDatabase.activateUser('group_test');
  });
  for (final width in [360.0, 412.0, 1100.0]) {
    testWidgets('Formulário sem overflow em $width px', (tester) async {
      tester.view.physicalSize = Size(width, 900);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      await tester.pumpWidget(MaterialApp(home: Scaffold(body: Padding(padding: const EdgeInsets.all(20), child: CompanyOrganizationEditor(
        organization: CompanyOrganization(groups: ['Construtora Quality — nome longo para conferir layout']), initialGroup: '', initialType: '', onChanged: (_, __) {},
      )))));
      expect(find.text('Sem grupo — independente'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  }
}

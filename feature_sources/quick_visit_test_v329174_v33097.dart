import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/models.dart';
import 'package:auditar_sst/widgets/company_organization.dart';
import 'package:auditar_sst/screens/quick_visit_screen.dart';

void main() {
  test(
    'Seleção respeita acesso, atividade, grupos e pesquisa por nome curto',
    () {
      final companies = [
        Company(id: 'a', name: 'Obra A'),
        Company(id: 'b', name: 'Obra B'),
        Company(id: 'c', name: 'Inativa', active: false),
        Company(id: 'd', name: 'Outra empresa'),
      ];
      final organization = CompanyOrganization(
        entries: {
          'a': {
            'group': 'Construtora Quality',
            'alias': 'Centro',
            'favorite': true,
          },
          'b': {'group': 'Construtora Quality', '_lastVisit': '2026-10-08'},
        },
      );
      List<Company> select({
        String query = '',
        String? group,
        bool favorites = false,
      }) => quickVisitCompanies(
        companies,
        organization,
        query: query,
        group: group,
        favorites: favorites,
        canAccess: (id) => id != 'd',
      );
      expect(select().map((c) => c.id), ['a', 'b']);
      expect(select(query: 'centro').single.id, 'a');
      expect(select(group: '').length, 0);
      expect(select(favorites: true).single.id, 'a');
      expect(
        quickVisitCompanies(
          companies,
          organization,
          recent: true,
          canAccess: (id) => id != 'd',
        ).single.id,
        'b',
      );
      expect(
        quickVisitCompanies(companies, organization, canAccess: (_) => false),
        isEmpty,
      );
    },
  );
  for (final width in [360.0, 412.0, 1280.0]) {
    testWidgets('Atalhos acessíveis em largura $width com texto ampliado', (
      tester,
    ) async {
      tester.view.resetPhysicalSize();
      tester.view.physicalSize = Size(width, 1000);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      VisitIntent? selected;
      var more = false;
      var changed = false;
      await tester.pumpWidget(
        MaterialApp(
          home: MediaQuery(
            data: MediaQueryData(
              size: Size(width, 1000),
              textScaler: const TextScaler.linear(1.3),
            ),
            child: Scaffold(
              body: SingleChildScrollView(
                child: VisitStartPanel(
                  companyName: 'Construtora Quality — Obra Residencial Centro',
                  onOpen: (intent) => selected = intent,
                  onMore: () => more = true,
                  onChange: () => changed = true,
                ),
              ),
            ),
          ),
        ),
      );
      for (final entry in {
        'Iniciar visita': VisitIntent.visit,
        'Continuar rascunho': VisitIntent.drafts,
        'Pendências': VisitIntent.pending,
        'Relatórios': VisitIntent.reports,
      }.entries) {
        await tester.ensureVisible(find.text(entry.key));
        await tester.tap(find.text(entry.key));
        expect(selected, entry.value);
      }
      await tester.ensureVisible(find.text('Mais opções'));
      await tester.tap(find.text('Mais opções'));
      expect(more, isTrue);
      await tester.ensureVisible(find.text('Trocar'));
      await tester.tap(find.text('Trocar'));
      expect(changed, isTrue);
      expect(tester.takeException(), isNull);
    });
  }
}

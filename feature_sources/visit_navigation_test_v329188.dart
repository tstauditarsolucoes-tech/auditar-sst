import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/screens/quick_visit_screen.dart';

void main() {
  test('all existing visit intents appear in switcher', () {
    expect(VisitIntentTabs.labels.keys.toSet(), VisitIntent.values.toSet());
  });
  for (final width in [360.0, 412.0, 1280.0]) {
    testWidgets('task switch fits width $width', (tester) async {
      tester.view.physicalSize = Size(width, 900);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      var selected = VisitIntent.visit;
      await tester.pumpWidget(MaterialApp(home: Scaffold(body:
        StatefulBuilder(builder: (context, redraw) => VisitIntentTabs(
          selected: selected, onSelected: (value) => redraw(() => selected = value),
        )),
      )));
      expect(find.byType(ChoiceChip), findsNWidgets(4));
      await tester.ensureVisible(find.text('Pendências'));
      await tester.tap(find.text('Pendências'));
      await tester.pumpAndSettle();
      expect(selected, VisitIntent.pending);
      await tester.ensureVisible(find.text('Relatórios'));
      await tester.tap(find.text('Relatórios'));
      await tester.pumpAndSettle();
      expect(selected, VisitIntent.reports);
      expect(tester.takeException(), isNull);
    });
  }
  testWidgets('cannot switch while another page is opening', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: Scaffold(
      body: VisitIntentTabs(selected: VisitIntent.visit, onSelected: null),
    )));
    for (final chip in tester.widgetList<ChoiceChip>(find.byType(ChoiceChip))) {
      expect(chip.onSelected, isNull);
    }
  });
}

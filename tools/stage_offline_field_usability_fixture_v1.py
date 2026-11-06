#!/usr/bin/env python3
"""Fixture Flutter isolada: testa o widget existente + pequenas melhorias.

A biblioteca por NR real permanece no aplicativo principal. Aqui só existe
uma navegação simulada de biblioteca para testar os atalhos de consulta sem
montar as 1600 etapas de build operacional. Usa a implementação real do
serviço de sugestões e das regras de triagem.
"""
from pathlib import Path
import re
import shutil
import sys

if len(sys.argv)!=2:
    raise SystemExit("Uso: stage_offline_field_usability_fixture_v1.py <FlutterAPP>")
repo=Path(__file__).resolve().parents[1]
app=Path(sys.argv[1])
pubspec=app/"pubspec.yaml"
assert pubspec.is_file() and "name: offline_campo_fixture" in pubspec.read_text()
src=repo/"feature_sources/offline_report_inline_suggestions_v329175.dart"
widget=app/"lib/widgets/offline_report_inline_suggestions.dart"
reasoning=app/"lib/services/offline_reasoning.dart"
widget.parent.mkdir(parents=True,exist_ok=True)
reasoning.parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(src,widget)
shutil.copyfile(repo/"feature_sources/offline_reasoning_v329175.dart",reasoning)
s=widget.read_text(encoding="utf-8")
start=s.index("class OfflineReportInlineSuggestions extends StatelessWidget")
build=s.index("  @override\n  Widget build(BuildContext context) {",start)
injection="""  Future<void> _browseCatalog(BuildContext context) async {
    final search = TextEditingController();
    var selected = 'Todas';
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (modalContext) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Filtro por NR: $selected'),
            TextField(
              controller: search,
              decoration: const InputDecoration(
                labelText: 'Pesquisar situação ou recomendação',
              ),
            ),
            TextButton(
              onPressed: () => Navigator.pop(modalContext),
              child: const Text('Fechar biblioteca'),
            ),
          ],
        ),
      ),
    );
    search.dispose();
  }

  Widget _browseButton(BuildContext context) => OutlinedButton.icon(
    onPressed: () => _browseCatalog(context),
    icon: const Icon(Icons.menu_book_outlined),
    label: const Text('Consultar biblioteca por NR'),
  );

"""
s=s[:build]+injection+s[build:]
old="if (query.trim().length < 3) return const SizedBox.shrink();"
assert s.count(old)==1
s=s.replace(old,"if (query.trim().length < 3) return _browseButton(context);",1)
widget.write_text(s,encoding="utf-8",newline="\n")
pub=pubspec.read_text(encoding="utf-8")
assert pub.count("\ndependencies:\n")==1
pub=pub.replace("\ndependencies:\n","\ndependencies:\n  path_provider: ^2.1.5\n",1)
pubspec.write_text(pub,encoding="utf-8")
test=app/"test/offline_usability_test.dart"
test.parent.mkdir(parents=True,exist_ok=True)
test.write_text(r"""import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:offline_campo_fixture/widgets/offline_report_inline_suggestions.dart';

void main() {
  testWidgets('Atalhos rápidos só no campo vazio e consulta offline',
      (tester) async {
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:
      SingleChildScrollView(child:OfflineReportInlineSuggestions(
        query:'',onSelected:(_){},
      )),
    )));
    expect(find.text('Consultar biblioteca por NR'),findsOneWidget);
    expect(find.byKey(const ValueKey('offline-shortcut-extintor')),findsOneWidget);
    expect(find.byKey(const ValueKey('offline-shortcut-maquinas')),findsOneWidget);
    expect(find.byKey(const ValueKey('offline-shortcut-altura')),findsOneWidget);
    expect(find.byKey(const ValueKey('offline-shortcut-epi')),findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('offline-shortcut-extintor')));
    await tester.pumpAndSettle();
    final field=tester.widget<TextField>(find.byType(TextField).last);
    expect(field.controller?.text,'extintor');
    expect(find.text('Filtro por NR: Todas'),findsOneWidget);
    await tester.tap(find.text('Fechar biblioteca'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('offline-shortcut-altura')));
    await tester.pumpAndSettle();
    expect(find.text('Filtro por NR: NR-35'),findsOneWidget);
  });

  testWidgets('Ignorar sugestão com um toque não apaga texto nem aplica',
      (tester) async {
    const query='Botoeira de emergência não funcionou';
    final results=(await tester.runAsync(() =>
      OfflineReportInlineSuggestionService.search(query:query)))
      ?? const <OfflineInlineSuggestion>[];
    expect(results,isNotEmpty);
    var selected=0;
    Widget screen(String text)=>MaterialApp(home:Scaffold(body:
      SingleChildScrollView(child:OfflineReportInlineSuggestions(
        query:text,onSelected:(_)=>selected++,
      )),
    ));
    await tester.pumpWidget(screen(query));
    await tester.pumpAndSettle();
    expect(find.text(results.first.title),findsOneWidget);
    expect(find.text('Ajustar'),findsOneWidget);
    expect(find.byKey(const ValueKey('offline-suggestion-ignore')),findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('offline-suggestion-ignore')));
    await tester.pumpAndSettle();
    expect(selected,0);
    expect(find.text(results.first.title),findsNothing);
    await tester.pumpWidget(screen('Outro texto'));
    await tester.pumpAndSettle();
    await tester.pumpWidget(screen(query));
    await tester.pumpAndSettle();
    expect(find.text(results.first.title),findsOneWidget);
    expect(selected,0);
  });

  testWidgets('Ignorar no diálogo não altera o relatório',
      (tester) async {
    const query='Botoeira de emergência não funcionou';
    final results=(await tester.runAsync(() =>
      OfflineReportInlineSuggestionService.search(query:query)))
      ?? const <OfflineInlineSuggestion>[];
    expect(results,isNotEmpty);
    var selected=0;
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:
      SingleChildScrollView(child:OfflineReportInlineSuggestions(
        query:query,onSelected:(_)=>selected++,
      )),
    )));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Ajustar'));
    await tester.pumpAndSettle();
    expect(find.text('Revisar sugestão sem IA'),findsOneWidget);
    await tester.tap(find.text('Não corresponde'));
    await tester.pumpAndSettle();
    expect(selected,0);
    expect(find.text(results.first.title),findsNothing);
  });
}
""",encoding="utf-8",newline="\n")
oldtest=app/"test/widget_test.dart"
if oldtest.exists():oldtest.unlink()
print("OFFLINE_FIELD_FLUTTER_FIXTURE_READY")

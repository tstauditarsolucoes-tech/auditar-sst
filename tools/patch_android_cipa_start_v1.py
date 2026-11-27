#!/usr/bin/env python3
"""Late Android-only CIPA entry point. All non-CIPA files are immutable."""
from pathlib import Path
import hashlib
import re
import sys

WIDGET = r"""
import 'package:flutter/material.dart';

class CipaStartPanel extends StatelessWidget {
  const CipaStartPanel({
    super.key,
    required this.companyName,
    required this.mandateLabel,
    required this.active,
    required this.pending,
    required this.overdue,
    required this.nextMeeting,
    required this.onMandate,
    required this.onGuide,
    required this.onObservation,
    required this.onMeeting,
    required this.onMinutes,
    required this.onActions,
    required this.onMembers,
    required this.onLearn,
    required this.onIndicators,
  });

  final String companyName, mandateLabel, nextMeeting;
  final bool active;
  final int pending, overdue;
  final VoidCallback onMandate, onGuide, onMinutes, onActions, onMembers,
      onLearn, onIndicators;
  final VoidCallback? onObservation, onMeeting;

  Widget _tile(String label, String description, IconData icon,
      VoidCallback? action) {
    return OutlinedButton(
      key: ValueKey('cipa-start-$label'),
      onPressed: action,
      style: OutlinedButton.styleFrom(
        minimumSize: const Size(0, 106),
        padding: const EdgeInsets.all(12),
        alignment: Alignment.centerLeft,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 28),
          const SizedBox(height: 8),
          Text(label, style: const TextStyle(fontSize: 16,
            fontWeight: FontWeight.w700)),
          const SizedBox(height: 4),
          Text(description, style: const TextStyle(fontSize: 12)),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return ListView(
      key: const ValueKey('cipa-start-scroll'),
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
      children: [
        Text('Central da CIPA', style: Theme.of(context).textTheme.headlineSmall
            ?.copyWith(fontWeight: FontWeight.w800)),
        Text(companyName),
        const SizedBox(height: 10),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(mandateLabel, style: const TextStyle(fontWeight: FontWeight.w700)),
                const SizedBox(height: 6),
                Text('Próxima reunião: $nextMeeting'),
                Text('$pending ações abertas • $overdue vencidas'),
                if (!active) ...[
                  const SizedBox(height: 8),
                  const Text('Ative um mandato antes de registrar situações ou preparar reuniões.'),
                  TextButton(onPressed: onMandate, child: const Text('Gerenciar mandato')),
                ],
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        Text('O que você deseja fazer hoje?',
          style: Theme.of(context).textTheme.titleMedium
              ?.copyWith(fontWeight: FontWeight.w800, color: colors.primary)),
        const SizedBox(height: 12),
        LayoutBuilder(builder: (context, constraints) {
          final scale = MediaQuery.textScalerOf(context).scale(16) / 16;
          final columns = constraints.maxWidth >= 300 && scale <= 1.3 ? 2 : 1;
          final width = (constraints.maxWidth - (columns - 1) * 10) / columns;
          final tiles = <Widget>[
            _tile('Roteiro mensal', 'Verificar ambiente e atividades',
              Icons.fact_check_outlined, onGuide),
            _tile('Registrar situação', 'Informar local e anexar foto',
              Icons.add_a_photo_outlined, active ? onObservation : null),
            _tile('Preparar reunião', 'Agendar passo a passo',
              Icons.calendar_month_outlined, active ? onMeeting : null),
            _tile('Atas', 'Elaborar e revisar registros',
              Icons.description_outlined, onMinutes),
            _tile('Pendências', '$pending ações em aberto',
              Icons.task_alt_outlined, onActions),
            _tile('Membros da CIPA', 'Consultar e gerenciar integrantes',
              Icons.groups_outlined, onMembers),
            _tile('Aprender sobre a CIPA', 'Orientações para começar',
              Icons.school_outlined, onLearn),
            _tile('Indicadores', 'Consultar painel da gestão',
              Icons.bar_chart, onIndicators),
          ];
          return Wrap(spacing: 10, runSpacing: 10, children: [
            for (final tile in tiles) SizedBox(width: width, child: tile),
          ]);
        }),
        const SizedBox(height: 18),
        const Text('Use as abas para acessar a gestão completa. '
          'Os atalhos mantêm as permissões da conta atual.'),
      ],
    );
  }
}
"""

TEST = r"""
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import '../lib/screens/cipa_start_panel.dart';

void main() {
  for (final width in [320.0, 360.0, 412.0]) {
    for (final scale in [1.0, 1.3, 2.0]) {
      testWidgets('CIPA início $width / $scale', (tester) async {
        tester.view.physicalSize = Size(width, 800);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
        final calls = <String>[];
        await tester.pumpWidget(MaterialApp(
          builder: (context, child) => MediaQuery(
            data: MediaQuery.of(context).copyWith(textScaler: TextScaler.linear(scale)),
            child: child!,
          ),
          home: Scaffold(body: CipaStartPanel(
            companyName: 'Empresa de teste', mandateLabel: 'Mandato de teste',
            active: true, pending: 2, overdue: 1, nextMeeting: 'Não agendada',
            onMandate: () => calls.add('mandate'),
            onGuide: () => calls.add('guide'),
            onObservation: () => calls.add('observation'),
            onMeeting: () => calls.add('meeting'),
            onMinutes: () => calls.add('minutes'),
            onActions: () => calls.add('actions'),
            onMembers: () => calls.add('members'),
            onLearn: () => calls.add('learn'),
            onIndicators: () => calls.add('indicators'),
          )),
        ));
        expect(find.text('Central da CIPA'), findsOneWidget);
        final targets = <String, String>{
          'Roteiro mensal': 'guide',
          'Registrar situação': 'observation',
          'Preparar reunião': 'meeting',
          'Atas': 'minutes',
          'Pendências': 'actions',
          'Membros da CIPA': 'members',
          'Aprender sobre a CIPA': 'learn',
          'Indicadores': 'indicators',
        };
        for (final e in targets.entries) {
          final target = find.byKey(ValueKey('cipa-start-${e.key}'));
          final scroll = find.byKey(const ValueKey('cipa-start-scroll'));
          final scrollable = find.descendant(of: scroll, matching: find.byType(Scrollable));
          await tester.scrollUntilVisible(target, 150, scrollable: scrollable);
          await tester.ensureVisible(target);
          await tester.pumpAndSettle();
          await tester.tap(target);
          expect(calls.last, e.value);
          expect(tester.takeException(), isNull);
        }
      });
    }
  }

  testWidgets('sem mandato não cria registro nem reunião', (tester) async {
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: CipaStartPanel(
      companyName: 'Teste', mandateLabel: 'Nenhum mandato ativo',
      active: false, pending: 0, overdue: 0, nextMeeting: 'Não agendada',
      onMandate: () {}, onGuide: () {}, onObservation: () {}, onMeeting: () {},
      onMinutes: () {}, onActions: () {}, onMembers: () {}, onLearn: () {},
      onIndicators: () {},
    ))));
    expect(find.text('Gerenciar mandato'), findsOneWidget);
    for (final label in ['Registrar situação', 'Preparar reunião']) {
      final button = tester.widget<OutlinedButton>(find.byKey(ValueKey('cipa-start-$label')));
      expect(button.onPressed, isNull);
    }
  });
}
"""

ALLOWED = {
    'lib/screens/cipa_management_screen.dart',
    'lib/screens/cipa_participation_screen.dart',
    'lib/screens/cipa_start_panel.dart',
    'test/cipa_start_panel_test.dart',
}

def snapshot(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for base in ('lib', 'painel_web_google_apps_script', 'android', 'test')
            for p in (root / base).rglob('*') if p.is_file()
            and p.relative_to(root).as_posix() not in ALLOWED}

def replace_one(source, pattern, replacement):
    result, n = re.subn(pattern, lambda m: replacement(m), source)
    if n != 1:
        raise RuntimeError(f'CIPA inicio: anchor {pattern} matched {n}')
    return result

def transform(source):
    if 'CIPA_START_PANEL_V1' in source:
        raise RuntimeError('Painel já aplicado')
    if 'CIPA_PARTICIPATION_V1' not in source:
        raise RuntimeError('Módulo participação ausente')
    source = replace_one(source, r"(import '../services/cipa_participation_rules.dart';)",
        lambda m: m[1] + "\nimport 'cipa_start_panel.dart';")
    start = source.index('  Widget build(BuildContext context) {')
    head, tail = source[:start], source[start:]
    tail = replace_one(tail, r'(DefaultTabController\(\s*length:\s*)11\b',
        lambda m: m[1] + '12, initialIndex: 0'.replace(',', ',') )
    # The original comma after length is retained; the added initialIndex has its own comma.
    tail = replace_one(tail, r"(Tab\(text: 'Painel'\),)",
        lambda m: "Tab(text: 'Início'),\n" + m[1])
    tail = replace_one(tail, r'(_panelTab\(\),)', lambda m: '_cipaStartTab(),\n' + m[1])
    labels = re.findall(r"Tab\(text:\s*'([^']+)'\)", tail)
    expected = ['Início', 'Painel', 'Mandato', 'Membros', 'Reuniões', 'Atas',
                'Ações', 'Eleição', 'Treinamentos', 'Documentos', 'Histórico', 'Participação']
    if labels != expected:
        raise RuntimeError('Ordem das abas divergente: ' + repr(labels))
    view = tail[tail.index('TabBarView('):]
    destinations = re.findall(r'(_\w+Tab\(\))\s*,', view)
    expected_routes = ['_cipaStartTab()', '_panelTab()', '_mandateTab()', '_membersTab()',
        '_meetingsTab()', '_minutesTab()', '_actionsTab()', '_electionTab()',
        '_trainingTab()', '_documentsTab()', '_historyTab()', '_cipaWorkspaceTab()']
    if destinations != expected_routes:
        raise RuntimeError('Ordem das rotas divergente: ' + repr(destinations))
    return head + tail

START_METHOD = r"""
  // CIPA_START_PANEL_V1: same authorized account and existing handlers.
  Widget _cipaStartTab() => Builder(builder: (tabsContext) {
    final tabs = DefaultTabController.of(tabsContext);
    final mandate = activeMandate;
    final active = mandate != null && mandate.status != 'Encerrado';
    return CipaStartPanel(
      companyName: company?.name ?? '',
      mandateLabel: mandate?.title ?? 'Nenhum mandato ativo',
      active: active,
      pending: mandateActions.where((a) => a.status != 'Resolvida').length,
      overdue: overdueActionsCount,
      nextMeeting: nextMeeting == null
          ? 'Não agendada' : _dateTime.format(nextMeeting!.date),
      onMandate: () => tabs.animateTo(2),
      onGuide: () => tabs.animateTo(11),
      onObservation: busy || !active ? null : _cipaNewObservation,
      onMeeting: busy || !active ? null : _cipaGuidedMeeting,
      onMinutes: () => tabs.animateTo(5),
      onActions: () => tabs.animateTo(6),
      onMembers: () => tabs.animateTo(3),
      onLearn: _cipaBeginnerHelp,
      onIndicators: () => tabs.animateTo(1),
    );
  });

"""

def main(root):
    before = snapshot(root)
    screen = root / 'lib/screens/cipa_management_screen.dart'
    part = root / 'lib/screens/cipa_participation_screen.dart'
    s = transform(screen.read_text(encoding='utf-8'))
    p = part.read_text(encoding='utf-8')
    p = replace_one(p, r'  Widget _cipaWorkspaceTab\(\)\s*\{',
                    lambda m: START_METHOD + m[0])
    # Open the monthly guide when entering participation instead of hiding its checklist.
    p = replace_one(p, r'initiallyExpanded:\s*_cipaSimpleMode\s*,', lambda m: 'initiallyExpanded: true,')
    for name in ('lib/screens/cipa_start_panel.dart', 'test/cipa_start_panel_test.dart'):
        if (root / name).exists():
            raise RuntimeError('Arquivo existente: ' + name)
    screen.write_text(s, encoding='utf-8')
    part.write_text(p, encoding='utf-8')
    (root / 'lib/screens/cipa_start_panel.dart').write_text(WIDGET, encoding='utf-8')
    (root / 'test/cipa_start_panel_test.dart').write_text(TEST, encoding='utf-8')
    if snapshot(root) != before:
        raise RuntimeError('Arquivos fora da CIPA alterados')
    print('CIPA_START_PANEL_V1_OK; rotas existentes e núcleo de sincronização preservados')

if __name__ == '__main__':
    main(Path(sys.argv[1]))

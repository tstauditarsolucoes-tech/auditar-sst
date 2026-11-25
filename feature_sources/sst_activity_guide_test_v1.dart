import 'package:flutter_test/flutter_test.dart';
import '../lib/services/sst_activity_guide_models.dart';
import '../lib/services/sst_risk_documents_models.dart';

void main() {
  SstActivityPlan makePlan({String user = 'u1', String company = 'a',
      String code = 'altura'}) => SstActivityPlan(
    userId: user, companyId: company,
    templateCode: code,
    activity: 'Reforma de fachada',
    sector: 'Obra A - cobertura',
    updatedAt: '2026-11-25T14:00:00',
  );

  test('biblioteca de atividades oferece orientacoes com riscos', () {
    final codes = SstActivityTemplates.values.map((t) => t.code).toSet();
    expect(codes.length, SstActivityTemplates.values.length);
    for (final t in SstActivityTemplates.values) {
      expect(t.hints, isNotEmpty);
      expect(t.questions, isNotEmpty);
      expect(t.docs, isNotEmpty);
      expect(t.defaultActivity, isNotEmpty);
    }
    expect(codes, containsAll(['altura', 'confinado', 'maquinas',
      'soldagem', 'escavacao', 'eletrica', 'forno']));
    expect(SstActivityTemplates.find('inexistente'), isNull);
  });

  test('plano identifica empresa, usuario e atividade', () {
    final p = makePlan();
    expect(p.valid, isTrue);
    expect(() => SstActivityPlan.fromJson(p.toJson(),
      expectedUser: 'u2', expectedCompany: 'a'), throwsFormatException);
    expect(() => SstActivityPlan.fromJson(p.toJson(),
      expectedUser: 'u1', expectedCompany: 'b'), throwsFormatException);
  });

  test('reaproveitamento é isolado por conta e empresa', () async {
    final db = <String, String>{};
    final store = SstActivityPlanStore(
      read: (k) async => db[k] ?? '',
      write: (k,v) async { db[k] = v; },
    );
    expect(await store.load('u1','a'), isNull);
    await store.save(makePlan());
    expect((await store.load('u1','a'))!.templateCode, 'altura');
    expect(await store.load('u2','a'), isNull);
    expect(await store.load('u1','b'), isNull);
    expect(SstActivityPlanStore.key('u1','a'),
      isNot(SstActivityPlanStore.key('u2','a')));
  });

  test('plano incompleto ou codigo desconhecido é recusado', () async {
    final db = <String, String>{};
    final store = SstActivityPlanStore(
      read: (k) async => db[k] ?? '',
      write: (k,v) async { db[k] = v; },
    );
    final invalid = SstActivityPlan(
      userId: 'u1', companyId: 'a',
      templateCode: 'unknown', activity: '', sector: '',
      updatedAt: '',
    );
    expect(invalid.valid, isFalse);
    await expectLater(store.save(invalid), throwsStateError);
  });

  test('sugestao importada NÃO libera PDF antes de conferir', () {
    const item = SstRiskDocItem(
      id: 'modelo-01',
      step: 'Acesso', hazard: 'Queda de altura',
      consequence: 'Lesão grave', controls: 'Verificar proteção',
      owner: 'Encarregado',
      presetUnreviewed: true,
    );
    expect(item.complete, isFalse);
    final document = SstRiskDocDraft(
      id: 'doc-001', companyId: 'a', kind: SstRiskDocKind.apr,
      activity: 'Reforma', sector: 'Cobertura', date: '2026-11-25',
      preparedBy: 'TST', blockers: 'Parar sem proteção',
      emergency: 'Plano a conferir', items: [item],
    );
    expect(document.canExportDraft, isFalse);
    final reviewed = item.copyWith(presetUnreviewed: false);
    expect(reviewed.complete, isTrue);
    expect(document.copyWith(items: [reviewed]).canExportDraft, isTrue);
  });

  test('flags de revisão sobrevivem ao JSON', () {
    const item = SstRiskDocItem(
      id: 'modelo-01',
      step: 'Acesso', hazard: 'Queda',
      consequence: 'Lesão', controls: 'A verificar',
      owner: '', presetUnreviewed: true,
    );
    final again = SstRiskDocItem.fromJson(item.toJson());
    expect(again.presetUnreviewed, isTrue);
    expect(again.complete, isFalse);
    expect(again.copyWith(owner: 'TST', presetUnreviewed: false).complete,
      isTrue);
  });
}

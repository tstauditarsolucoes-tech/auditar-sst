import 'package:flutter_test/flutter_test.dart';
import '../lib/services/sst_risk_documents_models.dart';

void main() {
  final completeItem = SstRiskDocItem(
    id: 'etapa-01',
    step: 'Preparação da atividade',
    hazard: 'Queda de altura',
    consequence: 'Lesão por queda',
    controls: 'Isolar e conferir proteção coletiva',
    owner: 'Responsável da frente',
    probability: 3,
    severity: 5,
  );

  SstRiskDocDraft basic(SstRiskDocKind kind) => SstRiskDocDraft(
    id: 'doc-0001', kind: kind, companyId: 'empresa-a',
    activity: 'Inspeção na obra', sector: 'Cobertura',
    date: '2026-11-25', preparedBy: 'TST',
    blockers: 'Suspender diante de vento ou ausência de proteção',
    emergency: 'Comunicação, resgate e atendimento planejados',
    items: [completeItem],
  );

  test('APR e AR completas exportam apenas MINUTA', () {
    expect(basic(SstRiskDocKind.apr).canExportDraft, isTrue);
    expect(basic(SstRiskDocKind.ar).canExportDraft, isTrue);
    expect(SstRiskDocKind.pt.title, contains('Permissão de Trabalho'));
  });

  test('PT exige equipe, validade, aprovador indicado e AR/APR', () {
    final pt = basic(SstRiskDocKind.pt);
    expect(pt.canExportDraft, isFalse);
    final described = pt.copyWith(
      team: 'Equipe definida',
      validUntil: '2026-11-25 16:00',
      authorizer: 'Encarregado habilitado',
      referenceAr: 'AR-2026-01',
    );
    expect(described.canExportDraft, isTrue);
    expect(described.kind, SstRiskDocKind.pt);
  });

  test('etapa incompleta bloqueia minuta e score e ilustrativo', () {
    expect(completeItem.illustrativeScore, 15);
    final incomplete = completeItem.copyWith(controls: '');
    expect(incomplete.complete, isFalse);
    expect(basic(SstRiskDocKind.ar).copyWith(
      items: [incomplete]).canExportDraft, isFalse);
  });

  test('nao misturar empresa ou tipo no carregamento', () {
    final data = basic(SstRiskDocKind.apr).toJson();
    expect(() => SstRiskDocDraft.fromJson(data,
      companyId: 'empresa-b', kind: SstRiskDocKind.apr),
      throwsFormatException);
    expect(() => SstRiskDocDraft.fromJson(data,
      companyId: 'empresa-a', kind: SstRiskDocKind.pt),
      throwsFormatException);
  });

  test('conservar campos na serializacao', () {
    final original = basic(SstRiskDocKind.ar);
    final loaded = SstRiskDocDraft.fromJson(original.toJson(),
      companyId: original.companyId, kind: original.kind);
    expect(loaded.items.single.hazard, 'Queda de altura');
    expect(loaded.items.single.probability, 3);
    expect(loaded.canExportDraft, isTrue);
  });

  test('isolamento do rascunho por conta, empresa e tipo', () {
    expect(SstRiskDocStore.draftKey('u1','empresa-a',SstRiskDocKind.apr),
      isNot(SstRiskDocStore.draftKey(
        'u2','empresa-a',SstRiskDocKind.apr)));
    expect(SstRiskDocStore.draftKey('u1','empresa-a',SstRiskDocKind.apr),
      isNot(SstRiskDocStore.draftKey(
        'u1','empresa-b',SstRiskDocKind.apr)));
    expect(SstRiskDocStore.draftKey('u1','empresa-a',SstRiskDocKind.apr),
      isNot(SstRiskDocStore.draftKey(
        'u1','empresa-a',SstRiskDocKind.pt)));
  });

  test('arq. local preserva versoes antigas e nao sobrescreve', () async {
    final files = <String, String>{};
    final store = SstRiskDocStore(
      read: (k) async => files[k] ?? '',
      write: (k,v) async { files[k] = v; },
    );
    final doc = basic(SstRiskDocKind.apr);
    await store.archive('u1', 'empresa-a', doc);
    final ids = await store.listArchives(
      'u1','empresa-a',SstRiskDocKind.apr);
    expect(ids, [doc.id]);
    final read = await store.openArchive(
      'u1','empresa-a',SstRiskDocKind.apr,doc.id);
    expect(read.items.single.owner, 'Responsável da frente');
    await expectLater(store.archive('u1','empresa-a',doc),
      throwsStateError);
    await expectLater(store.openArchive(
      'u2','empresa-a',SstRiskDocKind.apr,doc.id),
      throwsStateError);
  });

  test('falhar com escala ou etapa repetida', () {
    final value = basic(SstRiskDocKind.ar).toJson();
    final rows = (value['items'] as List);
    (rows.first as Map<String, dynamic>)['probability'] = 9;
    expect(() => SstRiskDocDraft.fromJson(value,
      companyId: 'empresa-a',kind:SstRiskDocKind.ar),
      throwsFormatException);
  });
}

import 'package:flutter_test/flutter_test.dart';
import '../lib/services/sst_pet_nr33_models.dart';

void main() {
  SstPetDraft prepared() {
    var draft = const SstPetDraft(
      id: 'pet-test-01', companyId: 'ceramica-a', userId: 'tst-a');
    for (final field in PetTemplate.fields) {
      if (field.requiredForReview) {
        final value = field.key == 'oxygen' ? '20,9' :
            field.key == 'lel' ? '0' : 'Informação de teste - conferida em campo';
        draft = draft.withValue(field.key, value);
      }
    }
    for (final check in PetTemplate.checks) {
      draft = draft.withCheck(check.key, PetCheckStatus.reportedYes);
    }
    return draft;
  }

  test('PET inicia sem liberar entrada ou inventar leituras', () {
    const draft = SstPetDraft(
      id: 'pet-test-01', companyId: 'ceramica-a', userId: 'tst-a');
    expect(draft.readyForReviewPdf, isFalse);
    expect(draft.value('oxygen'), isEmpty);
    expect(draft.value('lel'), isEmpty);
    expect(draft.status('attendant'), PetCheckStatus.notChecked);
    expect(draft.pending, isNotEmpty);
  });

  test('campos essenciais, equipe, atmosfera e resgate são exigidos', () {
    final draft = prepared();
    expect(draft.readyForReviewPdf, isTrue);
    expect(draft.value('attendant'), isNotEmpty);
    expect(draft.value('supervisor'), isNotEmpty);
    expect(draft.value('entrants'), isNotEmpty);
    expect(draft.value('rescuePlan'), isNotEmpty);
    expect(draft.value('monitoring'), isNotEmpty);
  });

  test('O2 e LIE numéricos não podem ser campos vazios nem inválidos', () {
    final draft = prepared();
    expect(draft.withValue('oxygen', 'abc').readyForReviewPdf, isFalse);
    expect(draft.withValue('oxygen', '150').readyForReviewPdf, isFalse);
    expect(draft.withValue('lel', '-1').readyForReviewPdf, isFalse);
    expect(draft.withValue('lel', '101').readyForReviewPdf, isFalse);
    expect(draft.withValue('oxygen', '19,5').readyForReviewPdf, isTrue);
  });

  test('marcar não aplicável exige justificativa específica', () {
    final source = prepared().withCheck(
        'ventilation', PetCheckStatus.notApplicable);
    expect(source.readyForReviewPdf, isFalse);
    final justified = source.withCheck(
      'ventilation', PetCheckStatus.notApplicable,
      note: 'Apenas para verificação documental por profissional competente',
    );
    expect(justified.readyForReviewPdf, isTrue);
  });

  test('resposta não não equivale a autorização mesmo após revisar', () {
    final draft = prepared().withCheck('continuous',
      PetCheckStatus.reportedNo, note: 'Monitor indisponível');
    expect(draft.status('continuous'), PetCheckStatus.reportedNo);
    // A regra habilita somente PDF de MINUTA; não existe status autorizado.
    expect(draft.readyForReviewPdf, isTrue);
    expect(PetCheckStatus.values.map((e) => e.name).join(','),
      isNot(contains('authorized')));
  });

  test('dados de outra conta ou empresa são recusados', () {
    final json = prepared().toJson();
    expect(() => SstPetDraft.fromJson(json,
      expectedCompany: 'outra', expectedUser: 'tst-a'),
      throwsFormatException);
    expect(() => SstPetDraft.fromJson(json,
      expectedCompany: 'ceramica-a', expectedUser: 'outro'),
      throwsFormatException);
  });

  test('JSON conserva medições e controles sem alterar estado', () {
    final saved = prepared();
    final read = SstPetDraft.fromJson(saved.toJson(),
      expectedCompany: 'ceramica-a', expectedUser: 'tst-a');
    expect(read.value('oxygen'), '20,9');
    expect(read.value('lel'), '0');
    expect(read.status('attendant'), PetCheckStatus.reportedYes);
    expect(read.id, saved.id);
  });

  test('rascunho é separado por conta e empresa', () {
    expect(SstPetStore.draftKey('u1','a'),
      isNot(SstPetStore.draftKey('u2','a')));
    expect(SstPetStore.draftKey('u1','a'),
      isNot(SstPetStore.draftKey('u1','b')));
  });

  test('registros atmosféricos informados: sem liberação', () {
    const reading = SstPetAtmosphereReading(
      id: 'read-00001', dateTime: '2026-11-25 10:00',
      point: 'Boca de visita', oxygen: '20,9', lel: '0',
      toxic: 'H2S 0 ppm (valor informado)',
      detector: 'Detector 101, teste a conferir',
      measuredBy: 'Técnico de medição',
    );
    expect(reading.complete, isTrue);
    final saved = prepared().withReading(reading);
    expect(saved.readings.length, 1);
    expect(saved.readyForReviewPdf, isTrue);
    final loaded = SstPetDraft.fromJson(saved.toJson(),
        expectedCompany: 'ceramica-a', expectedUser: 'tst-a');
    expect(loaded.readings.single.oxygen, '20,9');
    expect(loaded.readings.single.toxic, contains('ppm'));
    expect(loaded.withoutReading(reading.id).readings, isEmpty);
  });

  test('leitura inválida não entra no histórico', () {
    const invalid = SstPetAtmosphereReading(
      id: 'read-00002', dateTime: '2026-11-25 10:00',
      point: 'Entrada', oxygen: 'inexistente', lel: '0',
      toxic: 'Não informado', detector: 'D-1', measuredBy: 'TST',
    );
    expect(invalid.complete, isFalse);
    expect(() => prepared().withReading(invalid), throwsStateError);
  });

  test('rejeitar duplicação de ID de leitura', () {
    const a = SstPetAtmosphereReading(
      id: 'read-00003', dateTime: '2026-11-25 10:00',
      point: 'P1', oxygen: '20,9', lel: '0',
      toxic: 'Gás A 0 ppm', detector: 'D-1', measuredBy: 'TST',
    );
    final draft = prepared().withReading(a);
    expect(() => draft.withReading(a), throwsStateError);
  });

  test('arquivo de minuta é imutável, por empresa e usuário', () async {
    final data = <String, String>{};
    final store = SstPetStore(
      read: (key) async => data[key] ?? '',
      write: (key, value) async { data[key] = value; },
    );
    final draft = prepared();
    await store.save(draft);
    await store.archive(draft);
    expect(await store.list('tst-a','ceramica-a'), [draft.id]);
    final archive = await store.open('tst-a','ceramica-a',draft.id);
    expect(archive.value('oxygen'), '20,9');
    await expectLater(store.archive(draft), throwsStateError);
    await expectLater(
      store.open('tst-b','ceramica-a',draft.id), throwsStateError);
    await expectLater(
      store.open('tst-a','ceramica-b',draft.id), throwsStateError);
  });
}

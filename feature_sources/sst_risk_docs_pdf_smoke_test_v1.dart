import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import '../lib/services/sst_document_signature_models.dart';
import '../lib/services/sst_risk_documents_models.dart';
import '../lib/services/sst_risk_documents_pdf.dart';
import '../lib/services/sst_pet_nr33_models.dart';
import '../lib/services/sst_pet_nr33_pdf.dart';

// Imagem pequena gerada para testes; NÃO pertence a trabalhador real.
const testSignaturePng = 'iVBORw0KGgoAAAANSUhEUgAAAGQAAAAtCAIAAADX11mnAAABmklEQVR4nO2awRKCMAxErf//z3hwZJxCt9kkW8TJO3hwsAnPDVORtm3bo7DxvLqBO1GyCEoWQckiKFkEJYugZBHcXlZrbX9VkyNr73VN013dZb5afAd/7HLBr4KRGmlpyRiqv2SwvrR0VNaoOVHTrbXpyjpfIVm4rfSmTxfcPkhLv8kcQ13To0B9l1vgyy+r62bvNb1pEKjjm7mlO5yycB9ZTVsCJSp9Ss4YTr9kB/ZA4dKJvjyyRgPY8f0+1bEjUPjILF+0LKqww5c7UKC0vTomOobUOUy3GsFAZX1wBCfLOIDgGGoT6wgUqB4PFyHLYer0yG6d9ECBdYK+rLKCZUa+RIECRE7Eec1ynMzRlzRQuLRvHZMs9wB24A9KA5Xiay4rdxNs2ZSJiPuixzB+Vt0K0kDh0qyviaysAezYBa1/0iLiC8lS3/C86pkUty9iDP/peRufr6Es0QD+Dg5fQ1krr7tXwfqajOFVl+FlgBvTR+bXrD829cYeiNv/fZ+CMRAli6BkEZQsgpJFULIIShZBySIoWQQli+AFeGQCTZnCS3cAAAAASUVORK5CYII=';

SstHandwrittenMark signature(String snapshot, String role) =>
    SstHandwrittenMark(
      roleCode: role,
      roleLabel: 'Ciência para conferência',
      declaredName: 'Pessoa de teste fictícia',
      declaredFunction: 'TST (simulado)',
      signedAt: '2026-11-26T10:00:00Z',
      documentSnapshot: snapshot,
      pngBase64: testSignaturePng,
    );

SstRiskDocDraft riskDraft(SstRiskDocKind kind) => SstRiskDocDraft(
  id: 'doc-test-01',
  kind: kind,
  companyId: 'empresa-teste',
  activity: 'Verificação fictícia de segurança',
  sector: 'Área de teste',
  date: '2026-11-26',
  preparedBy: 'Técnico fictício',
  blockers: 'Suspender diante de ausência de proteção',
  emergency: 'Plano de resgate deverá ser validado',
  team: 'Equipe fictícia',
  validUntil: '2026-11-26 17:00',
  authorizer: 'Responsável a consultar',
  referenceAr: 'AR TESTE-01',
  items: [
    const SstRiskDocItem(
      id: 'step-test-01',
      step: 'Preparação',
      hazard: 'Queda de altura',
      consequence: 'Lesões graves',
      controls: 'Conferir as proteções coletivas',
      owner: 'Responsável fictício',
      probability: 3,
      severity: 5,
    ),
  ],
);

SstPetDraft petDraft() {
  var draft = const SstPetDraft(
    id: 'pet-test-0001',
    userId: 'tecnico-teste',
    companyId: 'empresa-teste',
  );
  for (final field in PetTemplate.fields) {
    if (field.requiredForReview) {
      draft = draft.withValue(
        field.key,
        field.key == 'oxygen' ? '20,9'
            : field.key == 'lel' ? '0'
            : 'Dado fictício para teste de renderização',
      );
    }
  }
  for (final item in PetTemplate.checks) {
    draft = draft.withCheck(item.key, PetCheckStatus.reportedYes);
  }
  return draft;
}

void validatePdf(Uint8List bytes) {
  expect(bytes.length, greaterThan(1500));
  expect(String.fromCharCodes(bytes.take(4)), '%PDF');
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('APR, AR e PT geram PDF com rubrica manuscrita de ciência', () async {
    for (final kind in SstRiskDocKind.values) {
      final draft = riskDraft(kind);
      expect(draft.canExportDraft, isTrue);
      final snapshot = jsonEncode(draft.toJson());
      final bytes = await SstRiskDocumentPdf.generate(
        companyName: 'Empresa fictícia',
        companyId: 'empresa-teste',
        draft: draft,
        signatures: [signature(snapshot, 'author')],
      );
      validatePdf(bytes);
    }
  });

  test('PET longa e rubrica de vigia geram PDF identificado como minuta', () async {
    final draft = petDraft().withReading(
      const SstPetAtmosphereReading(
        id: 'read-test-01',
        dateTime: '2026-11-26 08:00',
        point: 'Ponto fictício de teste',
        oxygen: '20,9',
        lel: '0',
        toxic: 'Agente simulado 0 ppm',
        detector: 'Equipamento fictício',
        measuredBy: 'Técnico fictício',
      ),
    );
    expect(draft.readyForReviewPdf, isTrue);
    final bytes = await SstPetNr33Pdf.generate(
      companyName: 'Empresa fictícia',
      companyId: 'empresa-teste',
      userId: 'tecnico-teste',
      draft: draft,
      signatures: [signature(sstDocumentFingerprint(draft.toJson()), 'attendant_ack')],
    );
    validatePdf(bytes);
  });

  test('PDF recusa rubrica de versão diferente do conteúdo', () async {
    final risk = riskDraft(SstRiskDocKind.pt);
    await expectLater(
      SstRiskDocumentPdf.generate(
        companyName: 'Empresa fictícia',
        companyId: risk.companyId,
        draft: risk,
        signatures: [signature('revisão anterior', 'author')],
      ),
      throwsStateError,
    );
    final pet = petDraft();
    await expectLater(
      SstPetNr33Pdf.generate(
        companyName: 'Empresa fictícia',
        companyId: pet.companyId,
        userId: pet.userId,
        draft: pet,
        signatures: [signature('revisão anterior', 'supervisor_ack')],
      ),
      throwsStateError,
    );
  });

  test('PDF recusa empresa, usuário e formulário incompleto', () async {
    final risk = riskDraft(SstRiskDocKind.apr);
    await expectLater(
      SstRiskDocumentPdf.generate(
        companyName: 'Empresa de teste',
        companyId: 'outra-empresa',
        draft: risk,
      ),
      throwsStateError,
    );
    final pet = petDraft();
    await expectLater(
      SstPetNr33Pdf.generate(
        companyName: 'Empresa de teste',
        companyId: pet.companyId,
        userId: 'outro-tecnico',
        draft: pet,
      ),
      throwsStateError,
    );
  });
}

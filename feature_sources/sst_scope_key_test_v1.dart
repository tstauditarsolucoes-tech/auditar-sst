import 'package:flutter_test/flutter_test.dart';

import '../lib/services/sst_scope_key.dart';
import '../lib/services/sst_risk_documents_models.dart';
import '../lib/services/sst_pet_nr33_models.dart';
import '../lib/services/sst_activity_guide_models.dart';
import '../lib/services/sst_document_signature_models.dart';

void main() {
  test('chaves separadas não colidem com _ nos identificadores', () {
    final a = sstScopedKey('test_scope', ['a_b', 'c']);
    final b = sstScopedKey('test_scope', ['a', 'b_c']);
    expect(a, isNot(b));
  });

  test('separadores, percentuais e unicode não causam colisão', () {
    expect(sstScopedKey('test_scope', ['a|b', 'c']),
        isNot(sstScopedKey('test_scope', ['a', 'b|c'])));
    expect(sstScopedKey('test_scope', ['a:b', 'c']),
        isNot(sstScopedKey('test_scope', ['a', 'b:c'])));
    expect(sstScopedKey('test_scope', ['é', 'x']),
        isNot(sstScopedKey('test_scope', ['e', 'x'])));
    expect(sstScopedKey('test_scope', ['a%b', 'c']),
        isNot(sstScopedKey('test_scope', ['a', 'b%c'])));
  });

  test('não aceita scope vazio ou excesso de tamanho', () {
    expect(() => sstScopedKey('test_scope', ['', 'empresa']),
        throwsArgumentError);
    expect(() => sstScopedKey('test_scope', ['u', '']),
        throwsArgumentError);
    expect(() => sstScopedKey('test_scope', ['u' * 600]),
        throwsArgumentError);
  });

  test('APR AR PT não misturam usuário e empresa por _', () {
    expect(SstRiskDocStore.draftKey('a_b', 'c', SstRiskDocKind.apr),
        isNot(SstRiskDocStore.draftKey('a', 'b_c', SstRiskDocKind.apr)));
    expect(SstRiskDocStore.draftKey('u','empresa',SstRiskDocKind.apr),
        isNot(SstRiskDocStore.draftKey('u','empresa',SstRiskDocKind.pt)));
  });

  test('PET não mistura usuário com empresa parecidos', () {
    expect(SstPetStore.draftKey('a_b', 'c'),
        isNot(SstPetStore.draftKey('a', 'b_c')));
  });

  test('plano guiado não mistura usuário e empresa', () {
    expect(SstActivityPlanStore.key('a_b', 'c'),
        isNot(SstActivityPlanStore.key('a', 'b_c')));
  });

  test('assinatura de documento não colide em papel nem id', () {
    expect(SstHandwrittenSignatureStore.key('a_b', 'c', 'pet', '1'),
        isNot(SstHandwrittenSignatureStore.key('a', 'b_c', 'pet', '1')));
    expect(SstHandwrittenSignatureStore.key('u','c','risk_ar','a_b'),
        isNot(SstHandwrittenSignatureStore.key('u','c','risk_ar_a','b')));
  });
}

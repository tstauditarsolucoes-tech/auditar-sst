import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_cipa_membro/services/cipa_member_draft_store.dart';

void main() {
  test('AES-GCM protege respostas e até duas fotos com integridade',() async {
    final photo=Uint8List.fromList([255,216,255,224,1,2,3,255,217]);
    final model=CipaInspectionDraft(
      requestId:'mobile-test-request-0123456789',
      category:'Cerâmica',place:'Área de produção',
      answers:['Sim','Não',null],
      observation:'Relato visual para conferência',
      photos:[photo,photo],savedAt:DateTime.now().toUtc());
    final key=List<int>.generate(32,(i)=>i+1);
    final sealed=await CipaDraftCipher.seal(model.toJson(),key);
    expect(sealed.contains('Área de produção'),false,
      reason:'O arquivo não pode expor o texto em claro');
    expect(sealed.contains(base64Encode(photo)),false);
    final decoded=await CipaDraftCipher.open(sealed,key);
    final restored=CipaInspectionDraft.fromJson(decoded)!;
    expect(restored.requestId,model.requestId);
    expect(restored.place,'Área de produção');
    expect(restored.answers,['Sim','Não',null]);
    expect(restored.photos.length,2);
    expect(restored.photos.first,photo);
  });

  test('Chave de outro membro não lê o rascunho',() async {
    final keyA=List<int>.filled(32,1),keyB=List<int>.filled(32,2);
    final sealed=await CipaDraftCipher.seal(
      {'version':1,'secret':'somente membro A'},keyA);
    await expectLater(CipaDraftCipher.open(sealed,keyB),throwsException);
  });

  test('Adulteração do arquivo criptografado é rejeitada',() async {
    final key=List<int>.filled(32,9);
    final original=await CipaDraftCipher.seal(
      {'version':1,'note':'vistoria'},key);
    final wrapper=jsonDecode(original) as Map<String,dynamic>;
    final cipher=base64Decode(wrapper['ciphertext'] as String);
    cipher[0]^=1;
    wrapper['ciphertext']=base64Encode(cipher);
    await expectLater(CipaDraftCipher.open(jsonEncode(wrapper),key),
      throwsException);
  });

  test('Descarta rascunho com versão inválida ou mais de duas fotos',(){
    final saved=DateTime.now().toUtc().toIso8601String();
    final model={
      'version':1,'requestId':'mobile-test-request-12345678',
      'category':'Cerâmica','place':'Produção',
      'answers':['Sim','Não','Não sei/não verifiquei'],
      'observation':'','photos':[],'savedAt':saved,
    };
    expect(CipaInspectionDraft.fromJson(
      Map<String,dynamic>.from(model)),isNotNull);
    expect(CipaInspectionDraft.fromJson({
      ...model,'photos':['AA==','AA==','AA==']}),isNull);
    expect(CipaInspectionDraft.fromJson({
      ...model,'version':2}),isNull);
    expect(CipaInspectionDraft.fromJson({
      ...model,'requestId':'curto'}),isNull);
  });
}

import 'dart:io';
import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_cipa_membro/services/cipa_member_mural_draft_store.dart';

void main(){
  test('Mural offline criptografa rascunho com foto por conta/mandato',()async{
    final dir=await Directory.systemTemp.createTemp('cipa_mural_private_test_');
    addTearDown(()=>dir.delete(recursive:true));
    final key=List<int>.filled(32,71);
    CipaMuralDraftStore store(String who,String mandate,{DateTime? now})=>
      CipaMuralDraftStore(accountId:who,companyId:'company-A',
        mandateId:mandate,memberId:who,
        directory:()async=>dir,keyProvider:(_)async=>key,
        clock:()=>now??DateTime(2026,11,13,9));
    final a=store('member-A','mandate-A'),b=store('member-B','mandate-A');
    final bytes=Uint8List.fromList([255,216,255,224,1,2,3,255,217]);
    const id='mural-draft-test-1234567890123456';
    await a.save(CipaMuralDraft(id:id,place:'Pátio industrial',
      detail:'Foi observado material sobre passagem de pessoas',
      savedAt:DateTime(2026,11,13,8),photo:bytes));
    expect(await a.count(),1);
    expect(await b.count(),0);
    final recovered=(await a.list()).single;
    expect(recovered.detail,contains('passagem'));
    expect(recovered.photo,orderedEquals(bytes));
    final files=await dir.list().where((x)=>x is File).toList();
    expect(files.length,1);
    expect(await (files.single as File).readAsString(),
      isNot(contains('Pátio industrial')));
    expect(await store('member-A','mandate-B').count(),0);
    await expectLater(store('member-A','mandate-A',
      now:DateTime(2026,11,22)).list(),throwsStateError);
    final staged=(files.single as File);
    await staged.rename(staged.path+'.next');
    expect(await a.count(),1,'Recupera arquivo cifrado interrompido');
    expect((await a.list()).single.id,id);
    await a.delete(id);
    expect(await a.count(),0);
    await a.clearAll();
    expect(await a.list(),isEmpty);
  });
  test('Rascunho rejeita ID e foto inválidos',(){
    expect(()=>CipaMuralDraft.fromJson({
      'version':1,'id':'short','place':'Sala',
      'detail':'Situação observada com cuidado no setor',
      'savedAt':'2026-11-13T08:00:00Z',
    },now:DateTime(2026,11,13)),throwsStateError);
    expect(()=>CipaMuralDraft.fromJson({
      'version':1,'id':'mural-draft-test-1234567890123456',
      'place':'Sala','detail':'Situação observada com cuidado no setor',
      'savedAt':'2026-11-13T08:00:00Z','photo':'bm90IGpwZWc=',
    },now:DateTime(2026,11,13)),throwsStateError);
  });
}

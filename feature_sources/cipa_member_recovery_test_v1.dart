import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_cipa_membro/services/cipa_member_draft_store.dart';

void main(){
  CipaInspectionDraft draft(String id,{DateTime? at})=>CipaInspectionDraft(
    requestId:id,category:'Cerâmica',place:'Área de produção',
    answers:['Sim','Não',null],observation:'Proteção observada',
    photos:[],savedAt:at??DateTime.now().toUtc());
  CipaMemberDraftStore makeStore(Directory dir,String id)=>
    CipaMemberDraftStore(accountId:'account-1',companyId:'company-1',
      mandateId:'mandate-1',memberId:'member-1',draftId:id,
      directory:()async=>dir,
      keyProvider:(_)async=>List<int>.filled(32,17));

  test('Recupera arquivo cifrado após interrupção antes da renomeação',()async{
    final dir=await Directory.systemTemp.createTemp('cipa-recovery-');
    try {
      const id='mobile-resume-123456789012345';
      final store=makeStore(dir,id);
      await store.save(draft(id));
      final finalFile=(await dir.list().where((e)=>e is File).toList())
        .single as File;
      await finalFile.rename('${finalFile.path}.next');
      expect(await store.load(),isNotNull);
      final files=await dir.list().where((e)=>e is File).toList();
      expect(files.length,1);
      expect(files.single.path.endsWith('.enc'),true);
      expect((await store.load())?.requestId,id);
    }finally{await dir.delete(recursive:true);}
  });

  test('Inventário recupera novo registro parcial sem perder outro',()async{
    final dir=await Directory.systemTemp.createTemp('cipa-recovery-list-');
    try {
      const a='mobile-recover-aaaaaaaaaaaaaaaa';
      const b='mobile-recover-bbbbbbbbbbbbbbbb';
      final storeA=makeStore(dir,a),storeB=makeStore(dir,b);
      await storeA.save(draft(a));
      await storeB.save(draft(b));
      final records=await dir.list().where((e)=>e is File).toList();
      for(final e in records){
        final source=e as File;
        final decoded=await source.readAsString();
        if(!decoded.contains('ciphertext'))throw StateError('Not encrypted');
      }
      // Simula interrupção no salvamento de B sem tocar no registro A.
      final all=await storeA.listForMember();
      expect(all.length,2);
      final bRecord=all.singleWhere((e)=>e.draftId==b);
      expect(bRecord.canResume,true);
      await storeB.clear();
      final entries=await dir.list().where((e)=>e is File).toList();
      expect(entries.length,1);
      final current=entries.single as File;
      await current.rename('${current.path}.next');
      final recovered=await storeA.listForMember();
      expect(recovered.length,1);
      expect(recovered.single.draftId,a);
      expect(await storeA.load(),isNotNull);
    }finally{await dir.delete(recursive:true);}
  });

  test('Recusa rascunhos de mais de 7 dias e datas futuras anormais',(){
    const id='mobile-expiry-123456789012345';
    final now=DateTime.now().toUtc();
    expect(CipaInspectionDraft.fromJson(draft(id,
      at:now.subtract(const Duration(days:7,minutes:1))).toJson()),isNull);
    expect(CipaInspectionDraft.fromJson(draft(id,
      at:now.add(const Duration(hours:2))).toJson()),isNull);
    expect(CipaInspectionDraft.fromJson(draft(id).toJson()),isNotNull);
  });
}

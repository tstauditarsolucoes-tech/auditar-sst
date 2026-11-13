import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_cipa_membro/services/cipa_member_draft_store.dart';

void main(){
  test('Duas vistorias livres persistem sem sobrescrever ou expor texto',()async{
    final dir=await Directory.systemTemp.createTemp('cipa-multidraft-');
    try {
      CipaMemberDraftStore store({String? draftId,String? scheduled,
        String company='company-A'})=>CipaMemberDraftStore(
        accountId:'user-A',companyId:company,mandateId:'mandate-A',
        memberId:'member-A',scheduleId:scheduled,draftId:draftId,
        directory:()async=>dir,
        keyProvider:(_)async=>List<int>.filled(32,9));
      final now=DateTime.now().toUtc();
      CipaInspectionDraft draft(String requestId,String place)=>
        CipaInspectionDraft(
          requestId:requestId,category:'Cerâmica',place:place,
          answers:['Sim','Não',null],observation:'Observação no campo',
          photos:[],savedAt:now);
      const firstId='mobile-test-first-0000000000000000';
      const secondId='mobile-test-second-000000000000000';
      const scheduledId='cipa-inspection-fixture';
      await store(draftId:firstId).save(draft(firstId,'Pátio norte'));
      await store(draftId:secondId).save(draft(secondId,'Forno túnel'));
      await store(scheduled:scheduledId).save(
        draft('mobile-test-scheduled-000000000000','Produção'));
      await store(company:'company-B',draftId:'mobile-other-1111111111111111')
        .save(draft('mobile-other-1111111111111111','Área secreta'));
      final all=await store().listForMember(
        scheduledIds:{scheduledId});
      expect(all.length,3);
      expect(all.where((x)=>x.draftId!=null).length,2);
      expect(all.where((x)=>x.scheduleId==scheduledId).length,1);
      expect(all.map((x)=>x.displayPlace).toSet(),
        {'Pátio norte','Forno túnel','Produção'});
      for(final entry in await dir.list().where((f)=>f is File).toList()){
        final contents=await (entry as File).readAsString();
        expect(contents.contains('Forno túnel'),false);
        expect(contents.contains('Área secreta'),false);
      }
      await store(draftId:firstId).clear();
      final after=await store().listForMember(scheduledIds:{scheduledId});
      expect(after.length,2);
      expect(after.map((x)=>x.displayPlace).toSet(),
        {'Forno túnel','Produção'});
    }finally{await dir.delete(recursive:true);}
  });

  test('Rascunho legado é recuperado e agenda revogada não é enviada',()async{
    final dir=await Directory.systemTemp.createTemp('cipa-legacy-');
    try {
      CipaMemberDraftStore storage({String? scheduled})=>
        CipaMemberDraftStore(accountId:'user-A',companyId:'company-A',
          mandateId:'mandate-A',memberId:'member-A',
          scheduleId:scheduled,directory:()async=>dir,
          keyProvider:(_)async=>List<int>.filled(32,7));
      CipaInspectionDraft model(String id)=>CipaInspectionDraft(
        requestId:id,category:'Cerâmica',place:'Área de britagem',
        answers:['Não',null,null],observation:'',
        photos:[],savedAt:DateTime.now().toUtc());
      await storage().save(model('mobile-old-00000000000000000000'));
      await storage(scheduled:'cipa-inspection-removed').save(
        model('mobile-old-scheduled-0000000000'));
      final entries=await storage().listForMember(
        scheduledIds:{'cipa-inspection-active'});
      expect(entries.length,2);
      expect(entries.any((x)=>x.isLegacyFree&&x.canResume),true);
      expect(entries.any((x)=>x.warning.contains('Agendamento')&&
        !x.canResume),true);
    }finally{await dir.delete(recursive:true);}
  });

  test('Rascunho com ID incorreto não sobrescreve outro arquivo',()async{
    final dir=await Directory.systemTemp.createTemp('cipa-mismatch-');
    try {
      final store=CipaMemberDraftStore(accountId:'user-A',
        companyId:'company-A',mandateId:'mandate-A',memberId:'member-A',
        draftId:'mobile-expected-000000000000000',
        directory:()async=>dir,
        keyProvider:(_)async=>List<int>.filled(32,10));
      await expectLater(store.save(CipaInspectionDraft(
        requestId:'mobile-different-00000000000000',category:'Cerâmica',
        place:'Produção',answers:['Sim',null,null],observation:'',
        photos:[],savedAt:DateTime.now().toUtc())),throwsStateError);
      expect(await dir.list().toList(),isEmpty);
    }finally{await dir.delete(recursive:true);}
  });
}

import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_cipa_membro/services/cipa_member_identity.dart';
import 'package:auditar_cipa_membro/services/cipa_member_offline_cache.dart';
import 'package:auditar_cipa_membro/services/cipa_member_portal_policy.dart';

class MemoryVault implements CipaOfflineSecretVault {
  final values=<String,String>{};
  @override Future<String?> read(String key)async=>values[key];
  @override Future<void> write(String key,String value)async{values[key]=value;}
  @override Future<void> delete(String key)async{values.remove(key);}
}

CipaMemberView testView({String company='company-A'}) {
  final p=CipaMemberProfileContract.fromVerifiedMembership(
    authenticatedUserId:'account-A',grantedCompanyId:company,
    grantedMandateId:'mandate-A',grantedMemberId:'member-A',
    membershipUserId:'account-A',membershipCompanyId:company,
    membershipMandateId:'mandate-A',membershipMemberId:'member-A',
    membershipWorkerId:'worker-A',fullName:'Joana',
    cipaRole:'Titular',representation:'Empregados',
    userActive:true,mandateActive:true,memberActive:true)!;
  return CipaMemberPortalRules.build(
    verifiedProfile:p,records:[
      CipaMemberItem(
        id:'action-A',companyId:company,mandateId:'mandate-A',
        type:CipaMemberItemType.action,assignedMemberId:'member-A',
        title:'Conferir extintor',status:'Em andamento',
      ),
    ]);
}

void main(){
  test('Arquivo cifrado e PIN individual permitem consulta offline',()async{
    final dir=await Directory.systemTemp.createTemp('cipa-cache-');
    try {
      final cache=CipaMemberOfflineCache(
        vault:MemoryVault(),directory:()async=>dir);
      await cache.enroll('joana@example.test','314159',testView());
      expect(await cache.isEnabled('joana@example.test'),true);
      final files=await dir.list().where((e)=>e is File).toList();
      final cipher=await (files.single as File).readAsString();
      expect(cipher.contains('Conferir extintor'),false);
      final snapshot=await cache.unlock('joana@example.test','314159');
      expect(snapshot.view.myActions.single.title,'Conferir extintor');
      await cache.clear('joana@example.test');
      expect(await cache.isEnabled('joana@example.test'),false);
    }finally{await dir.delete(recursive:true);}
  });

  test('Troca de empresa invalida cache pessoal',()async{
    final dir=await Directory.systemTemp.createTemp('cipa-scope-');
    try {
      final cache=CipaMemberOfflineCache(
        vault:MemoryVault(),directory:()async=>dir);
      await cache.enroll('joana@example.test','314159',testView());
      await cache.updateFromServer('joana@example.test',
        testView(company:'company-B'));
      expect(await cache.isEnabled('joana@example.test'),false);
    }finally{await dir.delete(recursive:true);}
  });
  test('Cache com mais de 24 horas não abre sem atualizar online',()async{
    final dir=await Directory.systemTemp.createTemp('cipa-expiry-');
    var now=DateTime.utc(2026,11,13,12);
    try {
      final cache=CipaMemberOfflineCache(
        vault:MemoryVault(),directory:()async=>dir,clock:()=>now);
      await cache.enroll('joana@example.test','314159',testView());
      now=now.add(const Duration(hours:24,minutes:1));
      await expectLater(cache.unlock('joana@example.test','314159'),
        throwsStateError);
      await cache.updateFromServer('joana@example.test',testView());
      expect((await cache.unlock('joana@example.test','314159'))
        .view.myActions.length,1);
    }finally{await dir.delete(recursive:true);}
  });

  test('Retrocesso abrupto do relógio exige autenticação online',()async{
    final dir=await Directory.systemTemp.createTemp('cipa-clock-');
    var clock=DateTime.utc(2026,11,13,12);
    try {
      final cache=CipaMemberOfflineCache(
        vault:MemoryVault(),directory:()async=>dir,clock:()=>clock);
      await cache.enroll('joana@example.test','314159',testView());
      clock=clock.add(const Duration(hours:2));
      expect((await cache.unlock('joana@example.test','314159'))
        .view.myActions.length,1);
      clock=clock.subtract(const Duration(hours:1));
      await expectLater(cache.unlock('joana@example.test','314159'),
        throwsStateError);
      await cache.updateFromServer('joana@example.test',testView());
      expect((await cache.unlock('joana@example.test','314159'))
        .view.myActions.length,1);
    }finally{await dir.delete(recursive:true);}
  });
  test('PIN incorreto bloqueia consulta offline após cinco tentativas',()async{
    final dir=await Directory.systemTemp.createTemp('cipa-pin-');
    try {
      final cache=CipaMemberOfflineCache(
        vault:MemoryVault(),directory:()async=>dir);
      await cache.enroll('joana@example.test','314159',testView());
      for(var attempt=0;attempt<5;attempt++){
        await expectLater(cache.unlock('joana@example.test','000000'),
          throwsStateError);
      }
      await expectLater(cache.unlock('joana@example.test','314159'),
        throwsStateError);
    }finally{await dir.delete(recursive:true);}
  });

  test('Conteúdo de outra empresa é recusado antes da consulta',(){
    final data=CipaOfflineSnapshotCodec.encode(CipaOfflineSnapshot(
      view:testView(),syncedAt:DateTime.now().toUtc()));
    final items=data['items'] as List;
    (items.first as Map<String,dynamic>)['companyId']='outra-empresa';
    expect(()=>CipaOfflineSnapshotCodec.decode(data),throwsStateError);
  });

}

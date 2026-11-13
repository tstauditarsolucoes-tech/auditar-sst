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
}

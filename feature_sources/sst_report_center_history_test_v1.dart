import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/sst_report_center_models.dart';
import 'package:auditar_sst/services/sst_report_center_history.dart';

SstFieldDraft visit(String company,String sector,{String tech='Técnico'}) {
  return SstFieldDraft(
    kind:SstFieldReportKind.nr12,
    companyId:company,
    technician:tech,date:'2026-11-06',
    location:sector,
    answers:{
      'nr12-02':const SstFieldAnswer(
        status:SstFieldStatus.nonConforming,
        observation:'Transmissão com proteção removida.',
        recommendation:'Recompor e verificar a proteção.'),
    },
  );
}
void main(){
  late Map<String,String> storage;
  late SstFieldReportHistory history;
  setUp((){
    storage=<String,String>{};
    history=SstFieldReportHistory(
      read:(key)async=>storage[key]??'',
      write:(key,value)async{storage[key]=value;},
    );
  });
  test('histórico armazena duas visitas distintas sem sobrescrever a primeira',() async {
    final first=visit('company-A','Moinho');
    final second=visit('company-A','Produção');
    final id1=SstFieldReportHistory.newId();
    final id2=SstFieldReportHistory.newId();
    expect(id1,isNot(id2));
    await history.archive(draft:first,userId:'user-A',id:id1);
    await history.archive(draft:second,userId:'user-A',id:id2);
    final all=await history.list(
      companyId:'company-A',userId:'user-A',
      kind:SstFieldReportKind.nr12);
    expect(all.length,2);
    expect(all.map((a)=>a.location),['Produção','Moinho']);
    final retrieved=await history.open(companyId:'company-A',
      userId:'user-A',kind:SstFieldReportKind.nr12,id:id1);
    expect(retrieved.draft.location,'Moinho');
    expect(retrieved.draft.answer('nr12-02').observation,
      'Transmissão com proteção removida.');
    final old=await history.open(companyId:'company-A',
      userId:'user-A',kind:SstFieldReportKind.nr12,id:id2);
    expect(old.draft.location,'Produção');
    // Arquivamento não altera rascunho ativo existente.
    expect(storage.keys.any((k)=>k.startsWith('field_report_v1_')),isFalse);
  });
  test('segunda tentativa com mesmo ID é idempotente e não duplica',()async{
    final draft=visit('company-A','Produção'),id=SstFieldReportHistory.newId();
    await history.archive(draft:draft,userId:'user-A',id:id);
    await history.archive(draft:draft,userId:'user-A',id:id);
    expect((await history.list(companyId:'company-A',userId:'user-A',
      kind:SstFieldReportKind.nr12)).length,1);
    await expectLater(history.archive(
      draft:visit('company-A','Outra visita'),userId:'user-A',id:id),
      throwsStateError);
  });
  test('não acessa visitas de outra empresa, técnico ou tipo',() async {
    final id=SstFieldReportHistory.newId();
    await history.archive(draft:visit('company-A','Moinho'),
      userId:'user-A',id:id);
    for(final (company,user,kind) in [
      ('company-B','user-A',SstFieldReportKind.nr12),
      ('company-A','user-B',SstFieldReportKind.nr12),
      ('company-A','user-A',SstFieldReportKind.nr18),
    ]){
      expect((await history.list(companyId:company,userId:user,
        kind:kind)).isEmpty,isTrue);
      await expectLater(history.open(companyId:company,userId:user,
        kind:kind,id:id),throwsStateError);
    }
  });
  test('falha na gravação do índice não destrói a visita ativa',()async {
    final data=<String,String>{'field_report_v1_user-A_company-A_nr12':
      jsonEncode(visit('company-A','Moinho').toJson())};
    var fail=true;
    final broken=SstFieldReportHistory(
      read:(key)async=>data[key]??'',
      write:(key,value)async{
        if(key.endsWith('_index')&&fail)throw StateError('Disco cheio');
        data[key]=value;
      },
    );
    final id=SstFieldReportHistory.newId();
    await expectLater(broken.archive(draft:visit('company-A','Moinho'),
      userId:'user-A',id:id),throwsStateError);
    expect(data['field_report_v1_user-A_company-A_nr12'],isNotNull);
    expect(jsonDecode(data['field_report_v1_user-A_company-A_nr12']!)['location'],
      'Moinho');
    fail=false;
    await broken.archive(draft:visit('company-A','Moinho'),
      userId:'user-A',id:id);
    expect((await broken.list(companyId:'company-A',userId:'user-A',
      kind:SstFieldReportKind.nr12)).length,1);
  });
  test('histórico não inventa visita vazia nem aceita índice adulterado',() async {
    await expectLater(history.archive(
      draft:SstFieldDraft(kind:SstFieldReportKind.nr12,companyId:'A'),
      userId:'u',id:SstFieldReportHistory.newId()),throwsStateError);
    final index=SstFieldReportHistory.indexKey('A','u',SstFieldReportKind.nr12);
    storage[index]=jsonEncode({'version':1,
      'companyId':'B','userId':'u','kind':'nr12','items':[]});
    await expectLater(history.list(companyId:'A',userId:'u',
      kind:SstFieldReportKind.nr12),throwsFormatException);
  });
}

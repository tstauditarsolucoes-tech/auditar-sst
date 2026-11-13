import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_cipa_membro/services/cipa_member_draft_store.dart';
import 'package:auditar_cipa_membro/services/cipa_member_identity.dart';
import 'package:auditar_cipa_membro/services/cipa_member_pending_sync.dart';
import 'package:auditar_cipa_membro/services/cipa_member_portal_policy.dart';

class MemoryDraft extends CipaMemberDraftStore {
  MemoryDraft({String? schedule,String? id}):super(
    accountId:'user-A',companyId:'company-A',
    mandateId:'mandate-A',memberId:'member-A',
    scheduleId:schedule,draftId:id);
  CipaInspectionDraft? data;
  List<CipaStoredDraft> entries=[];
  @override Future<CipaInspectionDraft?> load()async=>data;
  @override Future<void> clear()async{data=null;}
  @override Future<List<CipaStoredDraft>> listForMember({
    Set<String> scheduledIds=const <String>{},
  })async=>entries;
}

CipaMemberView testMember() {
  final p=CipaMemberProfileContract.fromVerifiedMembership(
    authenticatedUserId:'user-A',grantedCompanyId:'company-A',
    grantedMandateId:'mandate-A',grantedMemberId:'member-A',
    membershipUserId:'user-A',membershipCompanyId:'company-A',
    membershipMandateId:'mandate-A',membershipMemberId:'member-A',
    membershipWorkerId:'worker-A',fullName:'Joana',
    cipaRole:'Titular',representation:'Empregados',
    userActive:true,mandateActive:true,memberActive:true)!;
  return CipaMemberPortalRules.build(verifiedProfile:p,records:[
    const CipaMemberItem(id:'cipa-inspection-fixture',
      companyId:'company-A',mandateId:'mandate-A',
      assignedMemberId:'member-A',
      type:CipaMemberItemType.scheduledInspection,
      title:'Vistoria: Cerâmica',status:'Programada'),
  ]);
}

CipaInspectionDraft sampleDraft(String id,{bool complete=true})=>
  CipaInspectionDraft(requestId:id,category:'Cerâmica',
    place:'Moinho de cavaco',
    answers:complete?['Sim','Não','Não sei/não verifiquei']:
      ['Sim',null,null],
    observation:'Verificar proteção de equipamentos',
    photos:[Uint8List.fromList([255,216,255,217])],
    savedAt:DateTime.now().toUtc());

void main(){
  test('Prévia separa prontos, incompletos, bloqueados e fotos',(){
    final first=sampleDraft('mobile-prepare-aaaaaaaaaaaaaaaa');
    final second=sampleDraft('mobile-prepare-bbbbbbbbbbbbbbbb',
      complete:false);
    final plan=CipaPendingSyncPlan.fromEntries([
      CipaStoredDraft(draft:first,draftId:first.requestId),
      CipaStoredDraft(draft:second,draftId:second.requestId),
      const CipaStoredDraft(warning:'Agendamento cancelado'),
    ]);
    expect(plan.total,3);
    expect(plan.ready,1);
    expect(plan.incomplete,1);
    expect(plan.blocked,1);
    expect(plan.photoCount,1);
    expect(plan.canSend,true);
  });

  test('Prévia somente com pendências não habilita envio',(){
    final plan=CipaPendingSyncPlan.fromEntries([
      const CipaStoredDraft(warning:'Arquivo ilegível'),
    ]);
    expect(plan.canSend,false);
  });

  test('Várias vistorias avulsas e uma programada enviam IDs distintos',()async{
    final root=MemoryDraft();
    final a='mobile-free-aaaaaaaaaaaaaaaa';
    final b='mobile-free-bbbbbbbbbbbbbbbb';
    final c='mobile-scheduled-cccccccccccccccc';
    final one=MemoryDraft(id:a)..data=sampleDraft(a);
    final two=MemoryDraft(id:b)..data=sampleDraft(b);
    final scheduled=MemoryDraft(schedule:'cipa-inspection-fixture')
      ..data=sampleDraft(c);
    root.entries=[
      CipaStoredDraft(draft:one.data,draftId:a),
      CipaStoredDraft(draft:two.data,draftId:b),
      CipaStoredDraft(draft:scheduled.data,scheduleId:'cipa-inspection-fixture'),
    ];
    final sync=CipaMemberPendingSync(storage:(view,schedule,id)=>
      id==a?one:id==b?two:schedule!=null?scheduled:root);
    final observed=<String>[];
    final report=await sync.sync(testMember(),({
      scheduleId,required place,required note,required photos,
      required requestId,
    })async{
      observed.add(requestId);
      expect(note,contains('conferência técnica'));
      expect(photos.length,1);
    });
    expect(report.sent,3);
    expect(report.remaining,0);
    expect(observed.toSet(),{a,b,c});
    expect(one.data,isNull);
    expect(two.data,isNull);
    expect(scheduled.data,isNull);
  });

  test('Falha de internet não apaga rascunho ou altera requestId',()async{
    final id='mobile-free-dddddddddddddddd';
    final root=MemoryDraft();
    final saved=MemoryDraft(id:id)..data=sampleDraft(id);
    root.entries=[CipaStoredDraft(draft:saved.data,draftId:id)];
    final sync=CipaMemberPendingSync(storage:(view,schedule,draft)=>
      draft==id?saved:root);
    final failures=await sync.sync(testMember(),({
      scheduleId,required place,required note,required photos,
      required requestId,
    })async{throw StateError('Sem conexão');});
    expect(failures.sent,0);
    expect(failures.remaining,1);
    expect(saved.data?.requestId,id);
  });

  test('Incompleta, ilegível ou agenda não autorizada não é enviada',()async{
    final id='mobile-free-eeeeeeeeeeeeeeee';
    final root=MemoryDraft();
    root.entries=[
      CipaStoredDraft(draft:sampleDraft(id,complete:false),draftId:id),
      const CipaStoredDraft(warning:'Rascunho ilegível'),
      CipaStoredDraft(draft:sampleDraft('mobile-orphan-ffffffffffffffff'),
        warning:'Agendamento indisponível'),
    ];
    var calls=0;
    final sync=CipaMemberPendingSync(storage:(v,s,d)=>root);
    final result=await sync.sync(testMember(),({
      scheduleId,required place,required note,required photos,
      required requestId,
    })async{calls++;});
    expect(calls,0);
    expect(result.remaining,3);
    expect(result.incomplete,1);
    expect(result.failed,2);
  });
}

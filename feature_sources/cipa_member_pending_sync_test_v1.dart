import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_cipa_membro/services/cipa_member_draft_store.dart';
import 'package:auditar_cipa_membro/services/cipa_member_identity.dart';
import 'package:auditar_cipa_membro/services/cipa_member_pending_sync.dart';
import 'package:auditar_cipa_membro/services/cipa_member_portal_policy.dart';

class MemoryDraft extends CipaMemberDraftStore {
  MemoryDraft({String? schedule}):super(
    accountId:'user-A',companyId:'company-A',
    mandateId:'mandate-A',memberId:'member-A',scheduleId:schedule);
  CipaInspectionDraft? data;
  @override Future<CipaInspectionDraft?> load()async=>data;
  @override Future<void> clear()async{data=null;}
}

void main(){
  test('Envia rascunho vinculado com mesmo ID e remove apenas após confirmação',
      ()async{
    final p=CipaMemberProfileContract.fromVerifiedMembership(
      authenticatedUserId:'user-A',grantedCompanyId:'company-A',
      grantedMandateId:'mandate-A',grantedMemberId:'member-A',
      membershipUserId:'user-A',membershipCompanyId:'company-A',
      membershipMandateId:'mandate-A',membershipMemberId:'member-A',
      membershipWorkerId:'worker-A',fullName:'Joana',
      cipaRole:'Titular',representation:'Empregados',
      userActive:true,mandateActive:true,memberActive:true)!;
    final view=CipaMemberPortalRules.build(
      verifiedProfile:p,records:[
        const CipaMemberItem(id:'cipa-inspection-fixture',
          companyId:'company-A',mandateId:'mandate-A',
          assignedMemberId:'member-A',
          type:CipaMemberItemType.scheduledInspection,
          title:'Vistoria: Cerâmica',status:'Programada'),
      ]);
    final drafts=<String?,MemoryDraft>{
      null:MemoryDraft(),
      'cipa-inspection-fixture':
        MemoryDraft(schedule:'cipa-inspection-fixture'),
    };
    drafts['cipa-inspection-fixture']!.data=CipaInspectionDraft(
      requestId:'mobile-fixture-request-0123456',
      category:'Cerâmica',place:'Moinho de cavaco',
      answers:['Sim','Não','Não sei/não verifiquei'],
      observation:'Foto obtida sem aproximação',
      photos:[Uint8List.fromList([255,216,255,217])],
      savedAt:DateTime.now().toUtc());
    final sync=CipaMemberPendingSync(storage:(view,id)=>drafts[id]!);
    expect(await sync.count(view),1);
    String? received,request;
    Future<void> dispatch({
      String? scheduleId,required String place,required String note,
      required List<Uint8List> photos,required String requestId,
    })async{
      received=scheduleId;request=requestId;
      expect(note,contains('conferência técnica'));
      expect(photos.length,1);
    }
    final status=await sync.sync(view,dispatch);
    expect(status.sent,1);
    expect(status.failed,0);
    expect(received,'cipa-inspection-fixture');
    expect(request,'mobile-fixture-request-0123456');
    expect(await sync.count(view),0);
  });
}

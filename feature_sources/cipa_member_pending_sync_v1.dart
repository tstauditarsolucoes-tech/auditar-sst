import 'dart:typed_data';

import 'cipa_member_draft_store.dart';
import 'cipa_member_portal_policy.dart';
import '../widgets/cipa_member_guided_inspection.dart';

typedef CipaDraftDispatcher=Future<void> Function({
  String? scheduleId,required String place,
  required String note,required List<Uint8List> photos,
  required String requestId,
});

class CipaPendingSyncStatus {
  const CipaPendingSyncStatus({
    required this.sent,required this.remaining,required this.incomplete,
    required this.failed,
  });
  final int sent,remaining,incomplete,failed;
}

/// Sincronização MANUAL após login online: rascunhos da pessoa/mandato.
/// Cada reenvio conserva o ID original e nunca declara sucesso por timeout.
class CipaMemberPendingSync {
  CipaMemberPendingSync({
    CipaMemberDraftStore Function(CipaMemberView,String?)? storage,
  }):_storage=storage??((view,id){
    final p=view.profile;
    return CipaMemberDraftStore(accountId:p.userId,
      companyId:p.companyId,mandateId:p.mandateId,
      memberId:p.memberId,scheduleId:id);
  });
  final CipaMemberDraftStore Function(CipaMemberView,String?) _storage;

  List<String?> _scheduledIds(CipaMemberView view){
    final profile=view.profile;
    final result=<String?>[null];
    for(final item in view.scheduledInspections){
      if(item.companyId!=profile.companyId||
         item.mandateId!=profile.mandateId||
         item.assignedMemberId!=profile.memberId||
         !['Programada','Registro enviado'].contains(item.status))continue;
      if(item.id.startsWith('cipa-inspection-'))result.add(item.id);
    }
    return result;
  }

  Future<int> count(CipaMemberView view) async {
    var total=0;
    for(final id in _scheduledIds(view)){
      final data=await _storage(view,id).load();
      if(data!=null)total++;
    }
    return total;
  }

  Future<CipaPendingSyncStatus> sync(CipaMemberView view,
      CipaDraftDispatcher dispatch) async {
    var sent=0,remaining=0,incomplete=0,failed=0;
    for(final id in _scheduledIds(view)){
      final store=_storage(view,id);
      CipaInspectionDraft? data;
      try {data=await store.load();}catch(_){failed++;continue;}
      if(data==null)continue;
      if(data.answers.length!=3||data.answers.any((v)=>v==null)||
         data.place.trim().length<2){
        remaining++;incomplete++;
        continue;
      }
      try {
        final note=CipaGuidedInspection.summary(
          place:data.place,category:data.category,
          answers:data.answers.cast<String>(),
          observation:data.observation);
        await dispatch(scheduleId:id,place:data.place.trim(),note:note,
          photos:data.photos,requestId:data.requestId);
        await store.clear();
        sent++;
      }catch(_){
        remaining++;failed++;
      }
    }
    return CipaPendingSyncStatus(
      sent:sent,remaining:remaining,incomplete:incomplete,failed:failed);
  }
}

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

/// Sincronização MANUAL após login online e revalidação do mandato.
/// Múltiplos rascunhos avulsos têm IDs próprios, sem sobrescrita.
class CipaMemberPendingSync {
  CipaMemberPendingSync({
    CipaMemberDraftStore Function(CipaMemberView,String?,String?)? storage,
  }):_storage=storage??((view,schedule,draftId){
    final p=view.profile;
    return CipaMemberDraftStore(accountId:p.userId,
      companyId:p.companyId,mandateId:p.mandateId,
      memberId:p.memberId,scheduleId:schedule,draftId:draftId);
  });
  final CipaMemberDraftStore Function(CipaMemberView,String?,String?) _storage;

  Set<String> _allowedSchedules(CipaMemberView view){
    final p=view.profile;
    return view.scheduledInspections.where((item)=>
      item.companyId==p.companyId &&
      item.mandateId==p.mandateId &&
      item.assignedMemberId==p.memberId &&
      ['Programada','Registro enviado'].contains(item.status) &&
      item.id.startsWith('cipa-inspection-'))
      .map((item)=>item.id).toSet();
  }

  Future<List<CipaStoredDraft>> list(CipaMemberView view) =>
    _storage(view,null,null).listForMember(
      scheduledIds:_allowedSchedules(view));

  Future<int> count(CipaMemberView view) async =>
    (await list(view)).length;

  Future<CipaPendingSyncStatus> sync(CipaMemberView view,
      CipaDraftDispatcher dispatch) async {
    final allowedSchedules=_allowedSchedules(view);
    final saved=await list(view);
    var sent=0,remaining=0,incomplete=0,failed=0;
    for(final entry in saved){
      final data=entry.draft;
      if(!entry.canResume||data==null||
         (entry.scheduleId!=null&&
          !allowedSchedules.contains(entry.scheduleId))){
        remaining++;failed++;continue;
      }
      if(!entry.complete){
        remaining++;incomplete++;continue;
      }
      try {
        final store=_storage(view,entry.scheduleId,entry.draftId);
        // Salva o mesmo ID persistido. Não assumir sucesso em timeout.
        final note=CipaGuidedInspection.summary(
          place:data.place,category:data.category,
          answers:data.answers.cast<String>(),
          observation:data.observation);
        await dispatch(scheduleId:entry.scheduleId,
          place:data.place.trim(),note:note,
          photos:data.photos,requestId:data.requestId);
        await store.clear();
        sent++;
      }catch(_){
        remaining++;failed++;
      }
    }
    return CipaPendingSyncStatus(sent:sent,remaining:remaining,
      incomplete:incomplete,failed:failed);
  }
}

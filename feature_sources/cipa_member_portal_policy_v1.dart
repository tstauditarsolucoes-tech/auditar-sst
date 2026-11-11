import 'cipa_member_identity.dart';

/// DTOs do portal do membro. Dados somente de uma resposta do servidor
/// autorizada; não consumir as tabelas sincronizadas do app de técnico.
enum CipaMemberItemType {
  meeting,
  action,
  notice,
  training,
  document,
  observation,
  reminder,
  scheduledInspection,
}

class CipaMemberItem {
  const CipaMemberItem({
    required this.id,
    required this.companyId,
    required this.mandateId,
    required this.type,
    required this.title,
    this.description = '',
    this.feedback = '',
    this.status = '',
    this.assignedMemberId = '',
    this.visibleToAllMembers = false,
    this.date,
    this.dueDate,
  });
  final String id,companyId,mandateId,title,description,feedback,status,assignedMemberId;
  final CipaMemberItemType type;
  final bool visibleToAllMembers;
  final DateTime? date,dueDate;
}

class CipaMemberView {
  const CipaMemberView({
    required this.profile,
    this.companyLabel='Empresa vinculada à CIPA',
    this.mandateLabel='Mandato atual',
    required this.meetings,
    required this.myActions,
    required this.notices,
    required this.trainings,
    required this.documents,
    required this.observations,
    required this.reminders,
    this.scheduledInspections=const [],
  });
  final CipaMemberAccessProfile profile;
  final String companyLabel,mandateLabel;
  final List<CipaMemberItem> meetings,myActions,notices,trainings,documents,
      observations,reminders,scheduledInspections;
  int get pendingActions => myActions.where(
    (item)=>item.status!='Resolvida' && item.status!='Concluída').length;
  int get pendingReminders => reminders.length;
}

enum CipaMemberCapability {
  viewMeeting,
  acknowledgeConvocation,
  viewOwnAction,
  reportOwnActionProgress,
  requestOwnActionSupport,
  submitObservation,
  viewPublishedDocument,
  viewTrainingInfo,
  viewNotices,
  manageUsers,
  signMinutes,
  finalizeMinutes,
  certifyAttendance,
  closeNonConformity,
  manageElection,
  syncFullDatabase,
}

/// Camada de defesa adicional no dispositivo. A autorização obrigatória
/// precisa acontecer também NO SERVIDOR em toda operação.
class CipaMemberPortalRules {
  const CipaMemberPortalRules._();

  static bool may(CipaMemberCapability capability) {
    switch(capability) {
      case CipaMemberCapability.viewMeeting:
      case CipaMemberCapability.acknowledgeConvocation:
      case CipaMemberCapability.viewOwnAction:
      case CipaMemberCapability.reportOwnActionProgress:
      case CipaMemberCapability.requestOwnActionSupport:
      case CipaMemberCapability.submitObservation:
      case CipaMemberCapability.viewPublishedDocument:
      case CipaMemberCapability.viewTrainingInfo:
      case CipaMemberCapability.viewNotices:
        return true;
      default:
        return false;
    }
  }

  static CipaMemberView build({
    required CipaMemberAccessProfile verifiedProfile,
    required Iterable<CipaMemberItem> records,
    String companyLabel='Empresa vinculada à CIPA',
    String mandateLabel='Mandato atual',
  }) {
    final memberId=verifiedProfile.memberId;
    final visible=records.where((r)=>
        r.id.trim().isNotEmpty &&
        r.companyId==verifiedProfile.companyId &&
        r.mandateId==verifiedProfile.mandateId).toList(growable:false);
    List<CipaMemberItem> select(CipaMemberItemType type,{bool onlyMine=false}){
      return visible.where((r)=>r.type==type && (
        onlyMine?r.assignedMemberId==memberId:
        r.visibleToAllMembers || r.assignedMemberId==memberId))
        .toList(growable:false)
        ..sort((a,b)=>(
          a.dueDate??a.date??DateTime(9999)).compareTo(
          b.dueDate??b.date??DateTime(9999)));
    }
    return CipaMemberView(
      profile:verifiedProfile,
      companyLabel:companyLabel,
      mandateLabel:mandateLabel,
      meetings:select(CipaMemberItemType.meeting),
      myActions:select(CipaMemberItemType.action,onlyMine:true),
      notices:select(CipaMemberItemType.notice),
      trainings:select(CipaMemberItemType.training,onlyMine:true),
      documents:select(CipaMemberItemType.document),
      observations:select(CipaMemberItemType.observation,onlyMine:true),
      reminders:select(CipaMemberItemType.reminder),
      scheduledInspections:select(CipaMemberItemType.scheduledInspection,
        onlyMine:true),
    );
  }

  static bool canReportAction(
    CipaMemberAccessProfile profile,
    CipaMemberItem action,
  ) =>
      may(CipaMemberCapability.reportOwnActionProgress) &&
      action.type==CipaMemberItemType.action &&
      action.companyId==profile.companyId &&
      action.mandateId==profile.mandateId &&
      action.assignedMemberId==profile.memberId &&
      action.status!='Resolvida' && action.status!='Concluída';

  static bool canAcknowledge(
    CipaMemberAccessProfile profile,
    CipaMemberItem meeting,
  ) =>
      may(CipaMemberCapability.acknowledgeConvocation) &&
      meeting.type==CipaMemberItemType.meeting &&
      meeting.companyId==profile.companyId &&
      meeting.mandateId==profile.mandateId &&
      meeting.status=='Agendada' &&
      (meeting.visibleToAllMembers ||
       meeting.assignedMemberId==profile.memberId);
}

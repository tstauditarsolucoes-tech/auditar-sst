import 'cipa_member_identity_v1.dart';
import 'cipa_member_portal_policy_v1.dart';

void check(bool ok,String label) {
  if(!ok) throw StateError(label);
}
void main() {
  final profile=CipaMemberProfileContract.fromVerifiedMembership(
    authenticatedUserId:'user-A',
    grantedCompanyId:'empresa-A',
    grantedMandateId:'mandato-A',
    grantedMemberId:'member-A',
    membershipUserId:'user-A',
    membershipCompanyId:'empresa-A',
    membershipMandateId:'mandato-A',
    membershipMemberId:'member-A',
    membershipWorkerId:'worker-A',
    fullName:'João Alves',cipaRole:'Titular',
    representation:'Empregados',
    jobTitle:'Operador',userActive:true,
    mandateActive:true,memberActive:true)!;
  CipaMemberItem item(String id,CipaMemberItemType type,{
    String company='empresa-A',
    String mandate='mandato-A',
    String owner='',
    String status='Pendente',bool shared=false}) =>
      CipaMemberItem(id:id,type:type,
        companyId:company,mandateId:mandate,
        title:id,assignedMemberId:owner,
        visibleToAllMembers:shared,status:status);
  final data=[
    item('my-action',CipaMemberItemType.action,owner:'member-A'),
    item('other-action',CipaMemberItemType.action,owner:'member-B'),
    item('shared-action',CipaMemberItemType.action,shared:true),
    item('my-action-other-company',CipaMemberItemType.action,
      owner:'member-A',company:'empresa-B'),
    item('my-action-other-mandate',CipaMemberItemType.action,
      owner:'member-A',mandate:'mandato-B'),
    item('meeting-public',CipaMemberItemType.meeting,
      shared:true,status:'Agendada'),
    item('meeting-secret',CipaMemberItemType.meeting),
    item('meeting-personal',CipaMemberItemType.meeting,
      owner:'member-A',status:'Agendada'),
    item('notice',CipaMemberItemType.notice,shared:true),
    item('training-own',CipaMemberItemType.training,owner:'member-A'),
    item('training-other',CipaMemberItemType.training,owner:'member-B'),
    item('doc-allowed',CipaMemberItemType.document,shared:true),
    item('doc-other',CipaMemberItemType.document,owner:'member-B'),
    item('observation-own',CipaMemberItemType.observation,owner:'member-A'),
    item('reminder',CipaMemberItemType.reminder,shared:true),
  ];
  final view=CipaMemberPortalRules.build(
    verifiedProfile:profile,records:data);
  check(view.myActions.map((e)=>e.id).join(',')=='my-action',
    'Ações de outra pessoa ou compartilhadas não são próprias.');
  check(view.meetings.map((e)=>e.id).toSet()
      .containsAll(['meeting-public','meeting-personal']),
      'Mostrar convocações coletivas ou individuais.');
  check(view.meetings.length==2,'Não expor reuniões privadas.');
  check(view.trainings.map((e)=>e.id).join()==
      'training-own','Treinamento próprio.');
  check(view.documents.length==1,'Documento publicado e seguro.');
  check(view.observations.length==1,'Observações próprias.');
  check(view.notices.length==1 && view.reminders.length==1,
      'Avisos e lembretes autorizados.');
  check(view.pendingActions==1,'Ação pendente não concluída.');
  final labelled=CipaMemberPortalRules.build(
    verifiedProfile:profile,records:data,
    companyLabel:'Cerâmica de Exemplo',mandateLabel:'CIPA 2026');
  check(labelled.companyLabel=='Cerâmica de Exemplo' &&
    labelled.mandateLabel=='CIPA 2026',
    'Exibir nomes legíveis em lugar de IDs de banco.');
  check(CipaMemberPortalRules.canReportAction(profile,data[0]),
      'Informar andamento da sua ação.');
  for(final record in data.skip(1).take(4)){
    check(!CipaMemberPortalRules.canReportAction(profile,record),
      'Não alterar ação alheia ou de outra empresa/mandato.');
  }
  check(CipaMemberPortalRules.canAcknowledge(profile,data[5]),
      'Ciência de convocação autorizada.');
  check(!CipaMemberPortalRules.canAcknowledge(profile,data[6]),
      'Convocação de outro membro negada.');
  for(final cap in [
    CipaMemberCapability.manageUsers,
    CipaMemberCapability.signMinutes,
    CipaMemberCapability.finalizeMinutes,
    CipaMemberCapability.certifyAttendance,
    CipaMemberCapability.closeNonConformity,
    CipaMemberCapability.manageElection,
    CipaMemberCapability.syncFullDatabase,
  ]){
    check(!CipaMemberPortalRules.may(cap),'Privilégio operacional negado: $cap');
  }
  print('CIPA_MEMBER_PORTAL_POLICY_OK');
}

import 'cipa_guide_rules_v1.dart';
void check(bool result,String message){if(!result)throw StateError(message);}
CipaGuideSnapshot sample({bool mandate=false,int members=0,int election=0,
 bool meeting=false,int realized=0,int noAta=0,int noTraining=0,
 int open=0,int overdue=0,int docs=0,int observations=0})=>
 CipaGuideSnapshot(hasActiveMandate:mandate,activeMemberCount:members,
 registeredElectionCount:election,hasUpcomingMeeting:meeting,
 performedMeetingCount:realized,minutesWithoutMeetingCount:noAta,
 trainingNotFoundCount:noTraining,openActionCount:open,
 overdueActionCount:overdue,requiredDocumentPendingCount:docs,
 observationsAwaitingReviewCount:observations);
void main(){
 final empty=sample();
 final all=CipaGuideRules.steps(empty);
 check(all.length==8,'São oito passos.');
 check(all.map((x)=>x.id).toSet().length==8,'Não repetir etapas.');
 check(all.map((x)=>x.tab).join(',')=='1,6,2,7,3,4,5,8',
   'Usar abas existentes, sem criar novos fluxos.');
 check(CipaGuideRules.recommended(empty).id=='mandate','Mandato vem primeiro.');
 check(CipaGuideRules.recommended(sample(mandate:true)).id=='members','Priorizar integrantes.');
 check(CipaGuideRules.recommended(sample(mandate:true,members:2,overdue:1,noAta:1)).id=='actions','Priorizar ação vencida.');
 check(CipaGuideRules.recommended(sample(mandate:true,members:2,noAta:1)).id=='minutes','Alertar sobre ata.');
 check(CipaGuideRules.recommended(sample(mandate:true,members:2,observations:2)).id=='participation','Relatos a revisar.');
 check(CipaGuideRules.recommended(sample(mandate:true,members:2,noTraining:2)).id=='training','Conferir treinamentos.');
 check(CipaGuideRules.recommended(sample(mandate:true,members:2)).id=='meeting','Sem reunião próxima, orientar agenda.');
 check(CipaGuideRules.recommended(CipaGuideSnapshot(hasActiveMandate:true,activeMemberCount:2,registeredElectionCount:0,hasUpcomingMeeting:true,pastScheduledMeetingCount:1,performedMeetingCount:1,minutesWithoutMeetingCount:0,trainingNotFoundCount:0,openActionCount:0,overdueActionCount:0,requiredDocumentPendingCount:0,observationsAwaitingReviewCount:0)).id=='meeting','Reunião antiga ainda agendada deve ser conferida.');
 check(CipaGuideRules.recommended(sample(mandate:true,members:2,meeting:true,docs:1)).id=='documents','Conferir documentos.');
 check(CipaGuideRules.recommended(sample(mandate:true,members:2,meeting:true)).id=='routine','Acompanhamento, não conformidade final.');
 check(!CipaGuideRules.steps(sample(mandate:true,members:2))[1].attention,'Ausência de eleição não comprova descumprimento.');
 check(CipaGuideRules.registeredCount(empty)==0,'Sem cadastro não declarar etapas concluídas.');
 check(CipaGuideRules.attentionCount(sample(mandate:true,members:2,overdue:1,noAta:1))>=2,'Sinalizar pendências.');
 print('CIPA_GUIA_8_ETAPAS_OK');
}

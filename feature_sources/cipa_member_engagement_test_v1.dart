import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/cipa_member_identity.dart';
import 'package:auditar_sst/services/cipa_member_engagement.dart';
import 'package:auditar_sst/services/cipa_member_portal_policy.dart';

CipaMemberView memberView(){
  final p=CipaMemberProfileContract.fromVerifiedMembership(
    authenticatedUserId:'user-A',grantedCompanyId:'company-A',
    grantedMandateId:'mandate-A',grantedMemberId:'member-A',
    membershipUserId:'user-A',membershipCompanyId:'company-A',
    membershipMandateId:'mandate-A',membershipMemberId:'member-A',
    membershipWorkerId:'worker-A',fullName:'Joana Souza',
    cipaRole:'Titular',representation:'Empregados',
    userActive:true,mandateActive:true,memberActive:true)!;
  return CipaMemberPortalRules.build(verifiedProfile:p,records:[
    CipaMemberItem(id:'own-inspection',companyId:'company-A',
      mandateId:'mandate-A',assignedMemberId:'member-A',
      type:CipaMemberItemType.observation,
      title:'Vistoria orientada',
      description:'VISTORIA ORIENTADA DA CIPA — OBSERVAÇÃO VISUAL\n'
        'Tema: Ambiente e proteção',
      status:'Orientação enviada',feedback:'Equipe avaliará a situação.',
      date:DateTime(2026,11,9)),
    const CipaMemberItem(id:'own-action',companyId:'company-A',
      mandateId:'mandate-A',assignedMemberId:'member-A',
      type:CipaMemberItemType.action,title:'Conferir sinalização',
      status:'Concluída'),
    const CipaMemberItem(id:'foreign',companyId:'company-B',
      mandateId:'mandate-A',assignedMemberId:'member-A',
      type:CipaMemberItemType.observation,
      title:'Registro de outra empresa',
      description:'VISTORIA ORIENTADA DA CIPA',
      status:'Orientação enviada',feedback:'Outro cliente'),
    const CipaMemberItem(id:'other-member',companyId:'company-A',
      mandateId:'mandate-A',assignedMemberId:'member-B',
      type:CipaMemberItemType.observation,title:'Registro de colega',
      status:'Orientação enviada',feedback:'Privado'),
  ]);
}

void main(){
  test('Missões mudam por mês, respeitando roteiro existente',(){
    expect(CipaMemberEngagement.missionFor(DateTime(2026,11,1)).category,
      'Máquinas e equipamentos');
    expect(CipaMemberEngagement.missionFor(DateTime(2026,12,1)).category,
      'Ambiente e proteção');
    expect(CipaMemberEngagement.missionFor(DateTime(2027,1,1)).category,
      'Organização e circulação');
  });

  test('Escola educativa tem perguntas sem certificados automáticos',(){
    expect(CipaMemberEngagement.lessons.length,4);
    for(final lesson in CipaMemberEngagement.lessons){
      expect(lesson.choices.length,3);
      expect(lesson.correctIndex,inInclusiveRange(0,2));
      expect(lesson.explanation.trim(),isNotEmpty);
    }
  });

  test('Pergunta ao TST tem assunto controlado e não é laudo',(){
    final text=CipaMemberEngagement.questionText('EPI e proteção',
      'Qual é o procedimento correto para pedir luvas?');
    expect(text,contains(CipaMemberEngagement.questionMarker));
    expect(text,contains('Assunto: EPI e proteção'));
    expect(text,contains('não vistoria técnica'));
    expect(()=>CipaMemberEngagement.questionText('Assunto estranho',
      'Por favor, preciso saber mais.'),throwsArgumentError);
    expect(()=>CipaMemberEngagement.questionText('EPI e proteção','curto'),
      throwsArgumentError);
    final item=CipaMemberItem(id:'question',
      companyId:'company-A',mandateId:'mandate-A',
      assignedMemberId:'member-A',type:CipaMemberItemType.observation,
      title:'Situação observada • Orientação CIPA',
      description:text);
    expect(CipaMemberEngagement.isQuestion(item),true);
  });

  test('Meu impacto usa apenas registros filtrados do próprio mandato',(){
    final view=memberView();
    final impact=CipaMemberEngagement.impact(view,
      now:DateTime(2026,11,13));
    expect(impact.reports,1);
    expect(impact.technicalReplies,1);
    expect(impact.completedActions,1);
    expect(impact.missionReported,false);
    // Novembro não confunde uma vistoria de outro tema com missão.
    final sameTheme=CipaMemberEngagement.impact(view,
      now:DateTime(2026,12,13));
    expect(sameTheme.missionReported,false);
    expect(view.observations.any((x)=>x.title=='Registro de colega'),false);
  });

  test('Relato de missão só aparece após registro de mesmo tema e mês',(){
    final p=memberView().profile;
    final view=CipaMemberPortalRules.build(verifiedProfile:p,records:[
      CipaMemberItem(id:'report-1',companyId:'company-A',
        mandateId:'mandate-A',assignedMemberId:'member-A',
        type:CipaMemberItemType.observation,
        title:'Vistoria orientada',
        description:'VISTORIA ORIENTADA DA CIPA\n'
          'Tema: Máquinas e equipamentos',
        date:DateTime(2026,11,2)),
    ]);
    final impact=CipaMemberEngagement.impact(view,
      now:DateTime(2026,11,13));
    expect(impact.missionReported,true);
  });
}

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/cipa_member_identity.dart';
import 'package:auditar_sst/services/cipa_member_portal_policy.dart';
import 'package:auditar_sst/widgets/cipa_member_engagement_panel.dart';

CipaMemberView makeView(){
  final p=CipaMemberProfileContract.fromVerifiedMembership(
    authenticatedUserId:'user-A',grantedCompanyId:'company-A',
    grantedMandateId:'mandate-A',grantedMemberId:'member-A',
    membershipUserId:'user-A',membershipCompanyId:'company-A',
    membershipMandateId:'mandate-A',membershipMemberId:'member-A',
    membershipWorkerId:'worker-A',fullName:'Joana',
    cipaRole:'Titular',representation:'Empregados',
    userActive:true,mandateActive:true,memberActive:true)!;
  return CipaMemberPortalRules.build(verifiedProfile:p,records:[
    const CipaMemberItem(id:'my-report',companyId:'company-A',
      mandateId:'mandate-A',assignedMemberId:'member-A',
      type:CipaMemberItemType.observation,
      title:'Relato de organização',status:'Em análise'),
  ]);
}

Widget screen(CipaMemberView v,{bool offline=false,
    Future<void> Function(String)? start,
    Future<void> Function(String,String)? ask})=>
  MaterialApp(home:Scaffold(body:SingleChildScrollView(
    child:CipaMemberEngagementPanel(view:v,offlineMode:offline,
      now:DateTime(2026,11,13),onStartMission:start,onAskTst:ask))));

void main(){
  testWidgets('Missão leva para o roteiro escolhido, sem declarar concluída',
    (tester)async{
      String? chosen;
      await tester.pumpWidget(screen(makeView(),
        start:(category)async{chosen=category;}));
      expect(find.text('Missão do mês • 11/2026'),findsOneWidget);
      await tester.ensureVisible(find.text('Começar missão'));
      await tester.tap(find.text('Começar missão'));
      await tester.pumpAndSettle();
      expect(chosen,'Máquinas e equipamentos');
      expect(find.textContaining('não conformidade validada'),findsNothing);
    });

  testWidgets('Escola exibe miniaula, pergunta e orientação após resposta',
    (tester)async{
      await tester.pumpWidget(screen(makeView()));
      await tester.ensureVisible(find.text('Escola do Cipeiro'));
      await tester.tap(find.text('Escola do Cipeiro'));
      await tester.pumpAndSettle();
      expect(find.textContaining('Não substituem o treinamento'),
        findsOneWidget);
      await tester.tap(find.text('Qual é meu papel na CIPA?'));
      await tester.pumpAndSettle();
      expect(find.text('Ao perceber um perigo, o que fazer?'),
        findsOneWidget);
      await tester.tap(find.text('Registrar de um local seguro e comunicar a equipe'));
      await tester.pumpAndSettle();
      expect(find.text('Você acertou!'),findsOneWidget);
      expect(find.textContaining('sem nota ou certificado'),findsOneWidget);
    });

  testWidgets('Pergunta online envia apenas após confirmação do integrante',
    (tester)async{
      String? category,detail;
      await tester.pumpWidget(screen(makeView(),ask:(a,b)async{
        category=a;detail=b;
      }));
      await tester.ensureVisible(find.text('Pergunte ao TST'));
      await tester.tap(find.text('Pergunte ao TST'));
      await tester.pumpAndSettle();
      expect(find.textContaining('não é chat em tempo real'),findsOneWidget);
      expect(category,isNull);
      final send=find.widgetWithText(FilledButton,'Enviar dúvida');
      expect(tester.widget<FilledButton>(send).onPressed,isNull);
      await tester.enterText(find.byType(TextField).last,
        'Como registrar corretamente uma situação observada?');
      await tester.pumpAndSettle();
      expect(tester.widget<FilledButton>(send).onPressed,isNotNull);
      await tester.tap(send);
      await tester.pumpAndSettle();
      expect(category,'EPI e proteção');
      expect(detail,contains('Como registrar corretamente'));
    });

  testWidgets('Modo offline não permite enviar pergunta sem internet',
    (tester)async{
      var sent=0;
      await tester.pumpWidget(screen(makeView(),offline:true,ask:(a,b)async{
        sent++;
      }));
      await tester.ensureVisible(find.text('Pergunte ao TST'));
      await tester.tap(find.text('Pergunte ao TST'));
      await tester.pumpAndSettle();
      expect(find.textContaining('não há envio de perguntas offline'),
        findsOneWidget);
      expect(find.text('Enviar dúvida'),findsNothing);
      expect(sent,0);
    });

  testWidgets('Meu Impacto distingue contagens de comprovação de resultado',
    (tester)async{
      await tester.pumpWidget(screen(makeView(),offline:true));
      await tester.ensureVisible(find.text('Meu Impacto na Segurança'));
      await tester.tap(find.text('Meu Impacto na Segurança'));
      await tester.pumpAndSettle();
      expect(find.textContaining('Registros pessoais recebidos'),findsOneWidget);
      expect(find.textContaining('não medem riscos eliminados'),findsOneWidget);
      expect(find.textContaining('números podem estar desatualizados'),
        findsOneWidget);
    });
}

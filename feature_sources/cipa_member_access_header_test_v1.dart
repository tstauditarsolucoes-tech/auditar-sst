import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/widgets/cipa_member_access_header.dart';
import 'package:auditar_sst/services/cipa_member_identity.dart';

void main() {
  testWidgets('nome aparece com função da CIPA no acesso',
      (tester) async {
    final profile = CipaMemberProfileContract.fromVerifiedMembership(
      authenticatedUserId:'u-1',grantedCompanyId:'c-1',
      grantedMandateId:'m-1',grantedMemberId:'member-1',
      membershipUserId:'u-1',membershipCompanyId:'c-1',
      membershipMandateId:'m-1',membershipMemberId:'member-1',
      membershipWorkerId:'w-1',fullName:'Maria Silva',
      cipaRole:'Vice-presidente',representation:'Empregados',
      jobTitle:'Auxiliar de Produção',
      userActive:true,mandateActive:true,memberActive:true,
    );
    expect(profile, isNotNull);
    await tester.pumpWidget(MaterialApp(home:Scaffold(
      body:CipaMemberAccessHeader(
        profile:profile!,companyName:'Empresa de Teste',
        mandateLabel:'2026/2027',
      ),
    )));
    expect(find.text('Maria Silva — Vice-presidente da CIPA'),findsOneWidget);
    expect(find.textContaining('Cargo na empresa: Auxiliar de Produção'),
      findsOneWidget);
    expect(find.textContaining('Empresa de Teste'),findsOneWidget);
    expect(find.textContaining('não concede acesso'),findsOneWidget);
    expect(find.text('Validar conclusão'),findsNothing);
    expect(find.text('Gerenciar usuários'),findsNothing);
  });
}

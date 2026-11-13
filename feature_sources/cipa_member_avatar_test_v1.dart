import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as image_codec;
import 'package:auditar_sst/services/cipa_member_avatar_image.dart';
import 'package:auditar_sst/services/cipa_member_identity.dart';
import 'package:auditar_sst/widgets/cipa_member_access_header.dart';

void main(){
  final photo=Uint8List.fromList(
    image_codec.encodePng(image_codec.Image(width:40,height:40)));
  test('Avatar é JPG pequeno sem carregar foto original ou EXIF',(){
    final result=CipaAvatarImage.prepare(photo);
    expect(CipaAvatarImage.validUpload(result),true);
    expect(result.length,lessThanOrEqualTo(CipaAvatarImage.maxBytes));
    expect(()=>CipaAvatarImage.prepare(Uint8List(0)),throwsStateError);
  });
  testWidgets('Perfil pessoal mostra foto opcional e confirma remoção',
    (tester)async{
    final p=CipaMemberProfileContract.fromVerifiedMembership(
      authenticatedUserId:'user-A',grantedCompanyId:'company-A',
      grantedMandateId:'mandate-A',grantedMemberId:'member-A',
      membershipUserId:'user-A',membershipCompanyId:'company-A',
      membershipMandateId:'mandate-A',membershipMemberId:'member-A',
      membershipWorkerId:'worker-A',fullName:'Maria Silva',
      cipaRole:'Titular',representation:'Empregados',
      userActive:true,mandateActive:true,memberActive:true)!;
    final jpeg=CipaAvatarImage.prepare(photo);
    var deleted=0;
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:
      SingleChildScrollView(child:CipaMemberAccessHeader(
        profile:p,companyName:'Empresa A',mandateLabel:'2026/2027',
        onLoadAvatar:()async=>jpeg,
        onSaveAvatar:(_)async{},
        onDeleteAvatar:()async{deleted++;},
      )))));
    await tester.pumpAndSettle();
    expect(find.text('Tirar foto'),findsOneWidget);
    expect(find.text('Escolher foto'),findsOneWidget);
    expect(find.text('Remover foto'),findsOneWidget);
    expect(find.textContaining('não comprova presença'),findsOneWidget);
    await tester.tap(find.text('Remover foto'));
    await tester.pumpAndSettle();
    expect(deleted,0);
    await tester.tap(find.text('Remover foto').last);
    await tester.pumpAndSettle();
    expect(deleted,1);
    expect(find.text('Remover foto'),findsNothing);
  });
}

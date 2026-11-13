import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/cipa_member_draft_store.dart';
import 'package:auditar_sst/widgets/cipa_member_guided_inspection.dart';

class MemoryCipaDraftStore extends CipaMemberDraftStore {
  MemoryCipaDraftStore():super(
    accountId:'usuario-A',companyId:'empresa-A',
    mandateId:'mandato-A',memberId:'integrante-A');
  CipaInspectionDraft? value;
  @override Future<CipaInspectionDraft?> load() async=>value;
  @override Future<void> save(CipaInspectionDraft data) async {value=data;}
  @override Future<void> clear() async {value=null;}
}

void main(){
  testWidgets('Guardar e sair recupera formulário e o mesmo requestId',
    (tester) async {
    final repository=MemoryCipaDraftStore();
    await tester.binding.setSurfaceSize(const Size(450,900));
    await tester.pumpWidget(MaterialApp(home:Scaffold(
      body:Builder(builder:(context)=>ElevatedButton(
        onPressed:()=>showDialog<bool>(
          context:context,barrierDismissible:false,
          builder:(dialog)=>CipaGuidedInspectionDialog(
            draftStore:repository,initialCategory:'Cerâmica',
            onSend:(_,__) async {}),
        ),
        child:const Text('Abrir vistoria')),
      ),
    )));
    await tester.tap(find.text('Abrir vistoria'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).first,'Moinho de cavaco');
    await tester.pump(const Duration(milliseconds:400));
    await tester.tap(find.text('Guardar e sair'));
    await tester.pumpAndSettle();
    expect(repository.value?.place,'Moinho de cavaco');
    final before=repository.value!.requestId;
    await tester.tap(find.text('Abrir vistoria'));
    await tester.pumpAndSettle();
    final resumed=tester.widget<TextField>(find.byType(TextField).first);
    expect(resumed.controller?.text,'Moinho de cavaco');
    expect(repository.value?.requestId,before);
    expect(find.text('Rascunho protegido recuperado'),findsOneWidget);
    await tester.tap(find.text('Guardar e sair'));
    await tester.pumpAndSettle();
    await tester.binding.setSurfaceSize(null);
  });
}

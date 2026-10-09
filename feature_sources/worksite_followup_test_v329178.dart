import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/screens/worksite_followup_screen.dart';
void main(){
  test('chaves isoladas por obra e usuario',(){
    expect(WorksiteFollowupStore.key('obra-1','tst'),
      isNot(WorksiteFollowupStore.key('obra-2','tst')));
    expect(WorksiteFollowupStore.key('obra-1','tst'),
      isNot(WorksiteFollowupStore.key('obra-1','outro')));
  });
  test('roundtrip preserva etapa, diario e progresso',(){
    final record=WorksiteFollowup(phase:'Estrutura',status:'Em andamento',
      progress:55,nextVisit:'2026-10-15',log:[
        const WorksiteLog('2026-10-09','Visita','Andaime verificado')]);
    final restored=WorksiteFollowup.fromMap(record.toMap());
    expect(restored.phase,'Estrutura');
    expect(restored.progress,55);
    expect(restored.log.single.note,'Andaime verificado');
    expect(WorksiteFollowup.fromMap({'progress':150}).progress,100);
  });
  test('datas sem ambiguidades',(){
    expect(WorksiteFollowup.validDate('2026-10-15'),isTrue);
    expect(WorksiteFollowup.validDate('2026-02-31'),isFalse);
    expect(WorksiteFollowup.validDate('31/10/2026'),isFalse);
  });
  for(final width in [360.0,412.0,1280.0]){
    testWidgets('atalhos de campo responsivos em $width',(tester)async{
      tester.view.physicalSize=Size(width,900);
      tester.view.devicePixelRatio=1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      var pressed=0;
      await tester.pumpWidget(MaterialApp(home:Scaffold(body:
        SingleChildScrollView(child:WorksiteQuickActions(
          onRound:()=>pressed++,onInspection:()=>pressed++,
          onPending:()=>pressed++,onHistory:()=>pressed++)))));
      await tester.tap(find.text('Nova ronda'));
      expect(pressed,1);
      expect(tester.takeException(),isNull);
    });
  }
}
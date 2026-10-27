import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/screens/nr18_field_checklist_screen.dart';

void main(){
  test('NR-18: lista por fase inclui andaimes no acabamento',(){
    expect(Nr18FieldCatalog.forStage('Acabamento').any((x)=>x.id=='andaimes'),isTrue);
    expect(Nr18FieldCatalog.forStage('Fundação').any((x)=>x.id=='escavacao'),isTrue);
    expect(Nr18FieldCatalog.forStage('Acabamento').any((x)=>x.id=='escavacao'),isFalse);
    expect(Nr18FieldCatalog.forStage('Acabamento').any((x)=>x.id=='pgr'),isTrue);
  });
  test('nada é considerado conforme sem inspeção do técnico',(){
    final draft=Nr18FieldDraft();
    expect(draft.checked,0);
    expect(draft.count(Nr18FieldStatus.compliant),0);
    expect(draft.count(Nr18FieldStatus.notChecked),Nr18FieldCatalog.topics.length);
  });
  test('registro mantém ocorrência no seu tema e separa obra/técnico',(){
    var draft=Nr18FieldDraft();
    draft=draft.updated('andaimes',const Nr18FieldAnswer(
      status:Nr18FieldStatus.nonCompliant,
      note:'Faltam travamentos; base apoiada em material a avaliar.'),
      'Acabamento','2026-10-13T10:00:00');
    final restored=Nr18FieldDraft.fromMap(draft.toMap());
    expect(restored.answer('andaimes').status,Nr18FieldStatus.nonCompliant);
    expect(restored.answer('andaimes').note,contains('travamentos'));
    expect(restored.answer('quedas').status,Nr18FieldStatus.notChecked);
    expect(restored.summary('Obra 35'),contains('Obra 35'));
    expect(restored.summary('Obra 35'),contains('Faltam travamentos'));
    expect(Nr18FieldDraftStore.key('obra35','tst'),isNot(
      Nr18FieldDraftStore.key('obra36','tst')));
    expect(Nr18FieldDraftStore.key('obra35','tst'),isNot(
      Nr18FieldDraftStore.key('obra35','admin')));
  });
  test('dados inválidos não marcam conformidade e ignoram itens externos',(){
    final draft=Nr18FieldDraft.fromMap({
      'stage':'Fase desconhecida',
      'answers':{
        'andaimes':{'status':'status_inexistente','note':'Revisar'},
        'item-externo':{'status':'compliant','note':'Não guardar'},
      },
    });
    expect(draft.stage,'Planejamento');
    expect(draft.answer('andaimes').status,Nr18FieldStatus.notChecked);
    expect(draft.answers.containsKey('item-externo'),isFalse);
  });
  for(final width in [360.0,412.0,1280.0]){
    testWidgets('cartão NR-18 responsivo em $width',(tester)async{
      tester.view.physicalSize=Size(width,900);
      tester.view.devicePixelRatio=1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      Nr18FieldStatus selected=Nr18FieldStatus.notChecked;
      await tester.pumpWidget(MaterialApp(home:Scaffold(body:SingleChildScrollView(
        child:Nr18FieldItemCard(
          topic:Nr18FieldCatalog.topics.first,
          answer:const Nr18FieldAnswer(),enabled:true,
          onStatus:(v)=>selected=v,onNote:(){})))));
      expect(find.text('PGR e planejamento'),findsOneWidget);
      await tester.tap(find.text('Não verificado'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Não conforme').last);
      await tester.pumpAndSettle();
      expect(selected,Nr18FieldStatus.nonCompliant);
      expect(tester.takeException(),isNull);
    });
  }
}

import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path_provider_platform_interface/path_provider_platform_interface.dart';
import 'package:auditar_sst/services/offline_reasoning.dart';
import 'package:auditar_sst/services/offline_report_knowledge_service.dart';
import 'package:auditar_sst/widgets/offline_report_inline_suggestions.dart';

class _Paths extends PathProviderPlatform {
  _Paths(this.path);
  final String path;
  @override
  Future<String?> getApplicationSupportPath() async => path;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late Directory dir;
  late PathProviderPlatform original;
  setUp(() async {
    dir = await Directory.systemTemp.createTemp('auditar-offline-test-');
    original = PathProviderPlatform.instance;
    PathProviderPlatform.instance = _Paths(dir.path);
    OfflineReportInlineSuggestionService.invalidateLearnedCache();
  });
  tearDown(() async {
    PathProviderPlatform.instance = original;
    OfflineReportInlineSuggestionService.invalidateLearnedCache();
    await dir.delete(recursive: true);
  });
  const cases = <String,String>{
    'Botão de emergência não funcionou':'stop',
    'botoera de emergência n funciona':'stop',
    'botão de partida inoperante':'control',
    'sensor da porta de proteção inoperante':'sensor',
    'betoneira sem proteção':'guard',
    'manutenção da máquina sem bloqueio':'lock',
    'andaime sobre tijolo':'scaffold-base',
    'andaime sem guarda-corpo':'scaffold-guard',
    'andaime com acesso improvisado':'scaffold-access',
    'talabarte preso no próprio andaime':'anchor',
    'cabo elétrico desencapado':'electric-exposed',
    'quadro elétrico sem identificação':'electric-label',
    'painel obstruído':'electric-access',
    'extintor bloqueado':'extinguisher-access',
    'extitor s placa':'extinguisher-sign',
    'extintor com manômetro no vermelho':'extinguisher-condition',
    'saída de emergência trancada':'exit',
    'iluminação de emergência inoperante':'emergency-light',
    'trabalhador sem protetor auricular':'hearing',
    'respirador não utilizado':'respirator',
    'trabalhador sem óculos':'eyes',
    'trabalhador sem capacete':'helmet',
    'trabalhador sem botina':'footwear',
    'luvas rasgadas':'gloves',
  };
  for (final item in cases.entries) {
    test('reconhece ${item.key}', () {
      final results = OfflineReasoning.analyze(item.key);
      expect(results.map((v)=>v.rule.id), contains(item.value));
      expect(results.first.description, item.key);
    });
  }
  const safe = [
    'extintor desobstruído', 'extintor não está obstruído',
    'extintor não bloqueado', 'extintor sem obstrução',
    'sensor da porta não está inoperante',
    'botão de emergência sem defeito',
    'botão de emergência não falhou',
    'botão de emergência funcionando normalmente',
    'botão de emergência falhou mas já foi corrigido',
    'extintor bloqueado anteriormente, regularizado',
    'talvez o botão de emergência esteja inoperante',
    'verificar se extintor está bloqueado',
    'sensor da porta não testado, talvez inoperante',
    'sensor de temperatura inoperante',
  ];
  for(final query in safe) {
    test('não confirma falha: $query', () {
      expect(OfflineReasoning.analyze(query), isEmpty);
    });
  }
  test('separa falhas e não atribui placa ao botão', () {
    final results = OfflineReasoning.analyze('extintor sem placa e botão de emergência inoperante');
    expect(results.map((a)=>a.rule.id).toSet(), {'stop','extinguisher-sign'});
    expect(OfflineReasoning.analyze('extintor sem placa, botão funcionando normalmente').map((a)=>a.rule.id), ['extinguisher-sign']);
  });
  test('contexto segmenta sem inventar falha e prioridade depende de resposta', () {
    expect(OfflineReasoning.analyze('visita realizada',context:['betoneira sem proteção']),isEmpty);
    final a=OfflineReasoning.analyze('andaime sem guarda corpo',context:['Obra'])[0];
    expect(a.segment,'Obra'); expect(a.priority('Não informado'),'Alta');
    expect(a.priority('Sim'),'Crítica'); expect(a.priority('Não'),'Alta');
    expect(OfflineReasoning.analyze('botão iniciar inoperante').any((a)=>a.rule.id=='stop'),isFalse);
  });
  test('busca real mantém assuntos da biblioteca e bloqueia condição negada', () async {
    for(final query in ['produto químico em recipiente sem identificação','levantamento manual com postura inadequada','cabo elétrico com emenda danificada','esmerilhadeira sem proteção','vala sem escoramento']) {
      expect(await OfflineReportInlineSuggestionService.search(query:query),isNotEmpty,reason:query);
    }
    expect(await OfflineReportInlineSuggestionService.search(query:'extintor não está obstruído'),isEmpty);
    expect(await OfflineReportInlineSuggestionService.search(query:'botão de emergência falhou mas foi corrigido'),isEmpty);
    expect(await OfflineReportInlineSuggestionService.search(query:'extintor sem placa',limit:0),isEmpty);
  });
  test('modelo aprovado reaparece na busca no caminho canônico', () async {
    final learned = await OfflineReportKnowledgeService.learnFromApprovedFields(
      title:'Extintor sem placa revisado', description:'Extintor sem placa de identificação.',
      risk:'Dificuldade para localizar equipamento.', possibleConsequence:'Demora na resposta.',
      recommendation:'Recomendação aprovada de teste.',immediateAction:'',priority:'Média',source:'manual_approved');
    expect(learned,isNotNull);
    OfflineReportInlineSuggestionService.invalidateLearnedCache();
    final found=await OfflineReportInlineSuggestionService.search(query:'extintor sem placa',limit:20);
    expect(found.any((v)=>v.learned && v.recommendation=='Recomendação aprovada de teste.'),isTrue);
    expect(found.first.id,'rule-extinguisher-sign');
    expect(await File('${dir.path}/auditar_sst/offline_report_knowledge/offline_report_knowledge_v1.json').exists(),isTrue);
  });
  test('leitura continua aceitando arquivo legado sem modificá-lo', () async {
    final file=File('${dir.path}/offline_report_knowledge_v1.json');
    final body=jsonEncode({'templates':[{'id':'legacy-approved','title':'Extintor sem placa','description':'Extintor sem placa.','risk':'Risco revisado','recommendation':'Legado aprovado','source':'manual_approved','priority':'Alta'}]});
    await file.writeAsString(body);
    final found=await OfflineReportInlineSuggestionService.search(query:'extintor sem placa',limit:20);
    expect(found.any((v)=>v.id=='legacy-approved'),isTrue);
    expect(await file.readAsString(),body);
  });
  for(final width in [360.0,412.0,1280.0]) {
    testWidgets('prévia revisável em $width px sem aplicação automática', (tester) async {
      tester.view.physicalSize=Size(width,900); tester.view.devicePixelRatio=1;
      addTearDown(tester.view.resetPhysicalSize); addTearDown(tester.view.resetDevicePixelRatio);
      OfflineInlineSuggestion? applied;
      await tester.runAsync(() => OfflineReportInlineSuggestionService.search(query:'botão de emergência inoperante'));
      await tester.pumpWidget(MaterialApp(home:Scaffold(body:MediaQuery(data:MediaQueryData(size:Size(width,900),textScaler:TextScaler.linear(1.2)),child:OfflineReportInlineSuggestions(query:'botão de emergência inoperante',onSelected:(v)=>applied=v)))));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Parada de emergência inoperante')); await tester.pumpAndSettle();
      expect(applied,isNull); expect(find.text('Revisar sugestão sem IA'),findsOneWidget);
      expect(tester.takeException(),isNull);
      await tester.ensureVisible(find.widgetWithText(ChoiceChip,'Sim'));
      await tester.tap(find.widgetWithText(ChoiceChip,'Sim')); await tester.pumpAndSettle();
      final description=find.widgetWithText(TextField,'Descrição do registro');
      await tester.ensureVisible(description); await tester.enterText(description,'Condição conferida no equipamento.');
      await tester.tap(find.text('Aplicar texto revisado')); await tester.pumpAndSettle();
      expect(applied?.description,'Condição conferida no equipamento.'); expect(applied?.priority,'Crítica');
      expect(applied?.recommendation,contains('NR-12'));
      expect(await tester.runAsync(()=>File('${dir.path}/auditar_sst/offline_report_knowledge/offline_report_knowledge_v1.json').exists()),isFalse);
      expect(tester.takeException(),isNull);
    });
  }
  testWidgets('cancelar prévia não altera registro nem aprende', (tester) async {
    var calls=0;
    await tester.runAsync(() => OfflineReportInlineSuggestionService.search(query:'extintor sem placa'));
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:OfflineReportInlineSuggestions(query:'extintor sem placa',onSelected:(_)=>calls++))));
    await tester.pumpAndSettle(); await tester.tap(find.text('Extintor sem sinalização')); await tester.pumpAndSettle();
    await tester.tap(find.text('Cancelar')); await tester.pumpAndSettle();
    expect(calls,0); expect(await tester.runAsync(()=>dir.list().toList()),isEmpty);
  });
}

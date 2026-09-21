#!/usr/bin/env python3
from pathlib import Path
import re, sys

root=Path(sys.argv[1])
pubp=root/'pubspec.yaml'
sp=root/'lib/services/training_import_service.dart'
ip=root/'lib/screens/training_import_screen.dart'
tp=root/'lib/screens/trainings_screen.dart'
cp=root/'painel_web_google_apps_script/Code.gs'
pub=pubp.read_text(encoding='utf-8')
s=sp.read_text(encoding='utf-8')
ui=ip.read_text(encoding='utf-8')
train=tp.read_text(encoding='utf-8')
code=cp.read_text(encoding='utf-8')

pub,n=re.subn(r'^version:\s*[^\n]+','version: 3.29.75+217',pub,count=1,flags=re.M)
if n!=1: raise RuntimeError('Versão não localizada')
if 'excel_community:' not in pub:
    pub=pub.replace('  archive: ^4.0.9\n','  archive: ^4.0.9\n  excel_community: ^2.4.0\n',1)
if "package:excel_community/excel_community.dart" not in s:
    s=s.replace("import 'package:file_picker/file_picker.dart';\n","import 'package:file_picker/file_picker.dart';\nimport 'package:excel_community/excel_community.dart' as legacy_excel;\n",1)
s=s.replace("allowedExtensions: const ['pdf', 'xlsx', 'csv']","allowedExtensions: const ['pdf', 'xlsx', 'xls', 'csv']")

xml_old="""  static String _xmlUnescape(String value) => value
      .replaceAll('&lt;', '<')
      .replaceAll('&gt;', '>')
      .replaceAll('&quot;', '"')
      .replaceAll('&apos;', "'")
      .replaceAll('&amp;', '&');
"""
xml_new="""  static String _xmlUnescape(String value) {
    var decoded = value
        .replaceAll('&lt;', '<')
        .replaceAll('&gt;', '>')
        .replaceAll('&quot;', '"')
        .replaceAll('&apos;', "'")
        .replaceAll('&amp;', '&');
    decoded = decoded.replaceAllMapped(
      RegExp(r'&#x([0-9A-Fa-f]+);'),
      (match) => String.fromCharCode(
        int.tryParse(match.group(1) ?? '', radix: 16) ?? 0xFFFD,
      ),
    );
    decoded = decoded.replaceAllMapped(
      RegExp(r'&#([0-9]+);'),
      (match) => String.fromCharCode(
        int.tryParse(match.group(1) ?? '') ?? 0xFFFD,
      ),
    );
    return decoded;
  }
"""
if xml_new not in s:
    if xml_old not in s: raise RuntimeError('Decoder XML do XLSX não localizado')
    s=s.replace(xml_old,xml_new,1)


old="""    if (extension == 'xlsx') {
      parsed = _parseXlsx(bytes, workers);
      if (parsed.rows.isEmpty) {
        final aiNames = await _readParticipantNamesWithExistingAi(
          await _buildLightweightPdf(parsed.fullText),
        );
        if (aiNames.isNotEmpty) {
          aiUsed = true;
          parsed = parsed.withRows(
            _rowsFromAiNames(aiNames, workers, parsed.metadata),
          );
        }
      }
    } else if (extension == 'csv') {
      parsed = _parseCsv(bytes, workers);
      if (parsed.rows.isEmpty) {
        final aiNames = await _readParticipantNamesWithExistingAi(
          await _buildLightweightPdf(parsed.fullText),
        );
        if (aiNames.isNotEmpty) {
          aiUsed = true;
          parsed = parsed.withRows(
            _rowsFromAiNames(aiNames, workers, parsed.metadata),
          );
        }
      }
    } else if (extension == 'pdf') {
      final text = await _extractPdfText(bytes, selected.path);
      parsed = _parsePdfText(text, workers);
      final essentialsMissing = parsed.rows.isEmpty ||
          parsed.metadata.trainingDate == null ||
          (parsed.metadata.code.isEmpty && parsed.metadata.title.isEmpty);
      if (essentialsMissing) {
        try {
          final aiNames = await _readParticipantNamesWithExistingAi(bytes);
          if (aiNames.isNotEmpty) {
            aiUsed = true;
            final aiRows = _rowsFromAiNames(aiNames, workers, parsed.metadata);
            parsed = parsed.withRows(_mergeRows(parsed.rows, aiRows));
          }
        } on TrainingImportException catch (error) {
          if (parsed.rows.isEmpty) rethrow;
          warnings.add('A IA não ficou disponível: ${error.message}');
        }
      }
    } else {
      throw const TrainingImportException(
        'Formato não suportado. Use PDF, XLSX ou CSV.',
      );
    }
"""
new="""    if (extension == 'xlsx') {
      parsed = _parseXlsx(bytes, workers);
      if (parsed.rows.isEmpty) {
        final ai = await _tryTrainingAi(await _buildLightweightPdf(parsed.fullText), workers, parsed, warnings);
        if (ai != null) { aiUsed = true; parsed = ai; }
      }
    } else if (extension == 'xls') {
      parsed = _parseLegacyXls(bytes, workers);
      if (parsed.rows.isEmpty) {
        final ai = await _tryTrainingAi(await _buildLightweightPdf(parsed.fullText), workers, parsed, warnings);
        if (ai != null) { aiUsed = true; parsed = ai; }
      }
    } else if (extension == 'csv') {
      parsed = _parseCsv(bytes, workers);
      if (parsed.rows.isEmpty) {
        final ai = await _tryTrainingAi(await _buildLightweightPdf(parsed.fullText), workers, parsed, warnings);
        if (ai != null) { aiUsed = true; parsed = ai; }
      }
    } else if (extension == 'pdf') {
      final text = await _extractPdfText(bytes, selected.path);
      parsed = _parsePdfText(text, workers);
      final essentialsMissing = parsed.rows.isEmpty ||
          parsed.metadata.trainingDate == null ||
          (parsed.metadata.code.isEmpty && parsed.metadata.title.isEmpty);
      if (essentialsMissing) {
        final ai = await _tryTrainingAi(bytes, workers, parsed, warnings, throwWhenNoLocalRows: true);
        if (ai != null) { aiUsed = true; parsed = ai; }
      }
    } else {
      throw const TrainingImportException('Formato não suportado. Use PDF, XLSX, XLS ou CSV.');
    }
"""
if new not in s:
    if old not in s: raise RuntimeError('Bloco de formatos não localizado')
    s=s.replace(old,new,1)

legacy=r'''  static _ParsedDocument _parseLegacyXls(Uint8List bytes, List<Worker> workers) {
    try {
      final book = legacy_excel.Excel.decodeBytes(bytes);
      final tables = <List<List<String>>>[];
      for (final sheet in book.tables.values) {
        final rows = <List<String>>[];
        for (final row in sheet.rows) {
          final values = row.map((cell) => cell?.displayText.trim() ?? '').toList(growable: false);
          if (values.any((v) => v.isNotEmpty)) rows.add(values);
        }
        if (rows.isNotEmpty) tables.add(rows);
      }
      if (tables.isEmpty) throw const TrainingImportException('A planilha XLS está vazia.');
      tables.sort((a,b)=>b.length.compareTo(a.length));
      final table=tables.first;
      final fullText=table.map((row)=>row.where((c)=>c.trim().isNotEmpty).join(' | ')).join('\n');
      return _parseTable(table, workers, fullText);
    } on TrainingImportException { rethrow; }
    catch (error) { throw TrainingImportException('Não foi possível ler a planilha XLS antiga: $error'); }
  }

  static Map<String,Object?> parseLegacyXlsForTesting(Uint8List bytes,List<Worker> workers) =>
      _testingMap(_parseLegacyXls(bytes,workers));

  static Map<String,Object?> parseXlsxForTesting(Uint8List bytes,List<Worker> workers) =>
      _testingMap(_parseXlsx(bytes,workers));

  static Map<String,Object?> _testingMap(_ParsedDocument parsed) => <String,Object?>{
    'code':parsed.metadata.code,
    'title':parsed.metadata.title,
    'trainingDate':parsed.metadata.trainingDate,
    'expiryDate':parsed.metadata.expiryDate,
    'rows':parsed.rows.map((row)=><String,Object?>{
      'name':row.name,'cpf':row.cpf,'code':row.code,'title':row.title,
      'trainingDate':row.trainingDate,'expiryDate':row.expiryDate,
    }).toList(),
  };

'''
if 'static _ParsedDocument _parseLegacyXls' not in s:
    s=s.replace('  static _ParsedDocument _parseXlsx(\n',legacy+'  static _ParsedDocument _parseXlsx(\n',1)

xlsx_marker="""  static _ParsedDocument _parseXlsx(
    Uint8List bytes,
    List<Worker> workers,
  ) {
"""
xlsx_preface="""  static _ParsedDocument _parseXlsx(
    Uint8List bytes,
    List<Worker> workers,
  ) {
    try {
      final communityParsed = _parseLegacyXls(bytes, workers);
      if (communityParsed.rows.isNotEmpty) return communityParsed;
    } catch (_) {
      // Mantém o leitor XLSX anterior como fallback.
    }
"""
if 'final communityParsed = _parseLegacyXls(bytes, workers);' not in s:
    if xlsx_marker not in s: raise RuntimeError('Entrada do parser XLSX não localizada')
    s=s.replace(xlsx_marker,xlsx_preface,1)


ai=r'''  static Future<_ParsedDocument?> _tryTrainingAi(
    Uint8List pdfBytes,List<Worker> workers,_ParsedDocument local,List<String> warnings,{
    bool throwWhenNoLocalRows=false,
  }) async {
    if (pdfBytes.isEmpty) return null;
    try {
      final ai=await _readTrainingDocumentWithExistingAi(pdfBytes);
      if (ai != null) {
        final meta=_TrainingMetadata(
          code:local.metadata.code.isNotEmpty?local.metadata.code:ai.metadata.code,
          title:local.metadata.title.isNotEmpty?local.metadata.title:ai.metadata.title,
          trainingDate:local.metadata.trainingDate??ai.metadata.trainingDate,
          expiryDate:local.metadata.expiryDate??ai.metadata.expiryDate,
        );
        final aiRows=ai.rows.map((row)=>_RawTrainingRow(
          sourceLine:row.sourceLine,name:row.name,cpf:row.cpf,
          code:row.code.isNotEmpty?row.code:meta.code,
          title:row.title.isNotEmpty?row.title:meta.title,
          trainingDate:row.trainingDate??meta.trainingDate,
          expiryDate:row.expiryDate??meta.expiryDate,
        )).toList();
        return _ParsedDocument(rows:_mergeRows(local.rows,aiRows),metadata:meta,fullText:local.fullText);
      }
      final names=await _readParticipantNamesWithExistingAi(pdfBytes);
      if (names.isEmpty) return null;
      return local.withRows(_mergeRows(local.rows,_rowsFromAiNames(names,workers,local.metadata)));
    } on TrainingImportException catch(error) {
      if (throwWhenNoLocalRows && local.rows.isEmpty) {
        throw TrainingImportException('${error.message} Se for um PDF escaneado, use também "Tirar foto da lista", que funciona localmente.');
      }
      warnings.add('A IA não ficou disponível: ${error.message}');
      return null;
    }
  }

  static Future<_ParsedDocument?> _readTrainingDocumentWithExistingAi(Uint8List pdfBytes) async {
    final endpoint=(await AppDatabase.instance.getSetting('management_panel_endpoint',fallback:'')).trim();
    final syncKey=(await AppDatabase.instance.getSetting('management_panel_sync_key',fallback:'')).trim();
    if (endpoint.isEmpty||syncKey.isEmpty) {
      throw const TrainingImportException('A IA precisa da Central Online configurada. A leitura local continua disponível.');
    }
    try {
      final response=await AppsScriptHttp.postJson(Uri.parse(endpoint),{
        'action':'ai_assistant','syncKey':syncKey,'authToken':AuthService.sessionToken,
        'payload':{'mode':'training_record_import','document':'data:application/pdf;base64,${base64Encode(pdfBytes)}'},
      },timeout:const Duration(seconds:65),allowLongAndroidRequest:true);
      final decoded=jsonDecode(utf8.decode(response.bodyBytes,allowMalformed:true));
      if(response.statusCode<200||response.statusCode>=300||decoded is! Map||decoded['ok']!=true){
        final errorCode=decoded is Map?'${decoded['code']??''}':'';
        final message=decoded is Map?'${decoded['message']??'A IA não concluiu a leitura do treinamento.'}':'A Central retornou uma resposta inválida.';
        if(errorCode=='AI_MODE_INVALID'||_normalize(message).contains('tipo de analise de ia invalido')) return null;
        throw TrainingImportException(message);
      }
      final result=decoded['result'];
      if(result is! Map) return null;
      final training=result['training'];
      final participants=result['participants'];
      if(participants is! List) return null;
      final t=training is Map?training:const <String,dynamic>{};
      final meta=_TrainingMetadata(
        code:'${t['code']??''}'.trim(),title:'${t['title']??''}'.trim(),
        trainingDate:_parseDate('${t['trainingDate']??''}'),expiryDate:_parseDate('${t['expiryDate']??''}'),
      );
      final rows=<_RawTrainingRow>[];
      for(var i=0;i<participants.length;i++){
        final raw=participants[i]; if(raw is! Map) continue;
        final name='${raw['name']??''}'.trim(); if(name.isEmpty) continue;
        rows.add(_RawTrainingRow(
          sourceLine:i+1,name:name,code:'${raw['code']??''}'.trim(),title:'${raw['title']??''}'.trim(),
          trainingDate:_parseDate('${raw['trainingDate']??''}'),expiryDate:_parseDate('${raw['expiryDate']??''}'),
        ));
      }
      return _ParsedDocument(rows:_dedupeRaw(rows),metadata:meta,fullText:'');
    } on TrainingImportException { rethrow; }
    on SocketException { throw const TrainingImportException('A IA precisa de internet para analisar a listagem.'); }
    catch(error){ throw TrainingImportException('Não foi possível consultar a IA: $error'); }
  }

'''
if '_readTrainingDocumentWithExistingAi(' not in s:
    marker='  static Future<List<Map<String, dynamic>>> _readParticipantNamesWithExistingAi(\n'
    if marker not in s: raise RuntimeError('Marcador IA não localizado')
    s=s.replace(marker,ai+marker,1)

ui=ui.replace('Importe PDF, XLSX ou CSV, ou fotografe a lista.','Importe PDF, XLSX, XLS ou CSV, ou fotografe a lista.')
ui=ui.replace("label: Text(current == null ? 'PDF/planilha' : 'Outro arquivo')","label: Text(current == null ? 'PDF/Excel' : 'Outro arquivo')")
train=train.replace("subtitle: 'PDF, planilha ou foto'","subtitle: 'PDF, Excel ou foto'")

oldm="['checklist_photo', 'safety_observation_photo', 'report_conclusion', 'report_review_chat', 'company_priorities', 'training_management', 'employee_pdf_import', 'medical_pdf_import', 'pgr_extract', 'pgr_question', 'checklist_builder']"
newm="['checklist_photo', 'safety_observation_photo', 'report_conclusion', 'report_review_chat', 'company_priorities', 'training_management', 'training_record_import', 'employee_pdf_import', 'medical_pdf_import', 'pgr_extract', 'pgr_question', 'checklist_builder']"
if newm not in code:
    if oldm not in code: raise RuntimeError('Whitelist IA não localizada')
    code=code.replace(oldm,newm,1)
code=code.replace("if (mode === 'employee_pdf_import' || mode === 'medical_pdf_import') {","if (mode === 'training_record_import' || mode === 'employee_pdf_import' || mode === 'medical_pdf_import') {")
code=code.replace("maxOutputTokens: mode === 'employee_pdf_import' || mode === 'medical_pdf_import'\n        ? 12000","maxOutputTokens: mode === 'training_record_import' || mode === 'employee_pdf_import' || mode === 'medical_pdf_import'\n        ? 12000")

pm="  if (mode === 'employee_pdf_import') {\n"
ptext=r'''  if (mode === 'training_record_import') {
    return [
      'Leia este PDF como registro ou lista de presença de treinamento de SST.',
      'Extraia o treinamento e os participantes sem inventar informações.',
      'Em training.code informe a NR/código quando estiver explícito; caso contrário use texto vazio.',
      'Em training.title transcreva o título do treinamento quando estiver legível.',
      'Converta datas válidas para AAAA-MM-DD. Não calcule validade: use texto vazio se ela não estiver informada.',
      'Em participants extraia somente participantes/alunos/trabalhadores, ignorando instrutor, responsável, cabeçalho, rodapé e textos administrativos.',
      'Quando uma linha tiver data ou validade própria, registre no participante; caso contrário deixe vazio para usar os dados gerais.',
      'Transcreva nomes como aparecem. Não inclua CPF, matrícula, telefone, endereço ou dados médicos.'
    ].join('\n');
  }
'''
u0=code.find('function aiUserPrompt_'); u1=code.find('function aiOutputSchema_')
if "if (mode === 'training_record_import')" not in code[u0:u1]:
    pos=code.find(pm,u0)
    if pos<0: raise RuntimeError('Prompt employee não localizado')
    code=code[:pos]+ptext+code[pos:]

schema=r'''  if (mode === 'training_record_import') {
    return {
      type:'object',
      properties:{
        training:{type:'object',properties:{
          code:{type:'string'},title:{type:'string'},trainingDate:{type:'string'},expiryDate:{type:'string'}
        },required:['code','title','trainingDate','expiryDate']},
        participants:{type:'array',items:{type:'object',properties:{
          name:{type:'string'},code:{type:'string'},title:{type:'string'},trainingDate:{type:'string'},expiryDate:{type:'string'}
        },required:['name','code','title','trainingDate','expiryDate']}}
      },
      required:['training','participants']
    };
  }
'''
ss=code.find('function aiOutputSchema_'); pos=code.find(pm,ss)
if pos<0: raise RuntimeError('Schema employee não localizado')
if "if (mode === 'training_record_import')" not in code[ss:pos]:
    code=code[:pos]+schema+code[pos:]

oldcall=r'''  try {
    const endpoint = GEMINI_API_BASE_URL + encodeURIComponent(model) + ':generateContent';
    const response = UrlFetchApp.fetch(endpoint, {
      method: 'post',
      contentType: 'application/json',
      headers: {'x-goog-api-key': apiKey},
      payload: JSON.stringify(body),
      muteHttpExceptions: true
    });
    const status = response.getResponseCode();
    const raw = response.getContentText();
    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch (_) {
      parsed = {};
    }
    if (status < 200 || status >= 300) {
      const apiMessage = parsed && parsed.error ? parsed.error.message : '';
      if (status === 429) {
        return {ok: false, message: 'A cota gratuita da IA foi atingida. Tente novamente mais tarde.'};
      }
      return {ok: false, message: apiMessage || ('A IA respondeu com erro ' + status + '.')};
    }
    const outputText = extractGeminiText_(parsed);
    if (!outputText) return {ok: false, message: 'A IA não retornou uma análise utilizável.'};
    let result;
    try {
      result = JSON.parse(outputText);
    } catch (_) {
      return {ok: false, message: 'Não foi possível interpretar a análise da IA.'};
    }
    return {ok: true, result: result, model: model};
  } catch (error) {
    return {ok: false, message: 'Falha ao consultar a IA: ' + String(error)};
  }
'''
if 'return callGeminiWithFallback_(apiKey, model, body);' not in code:
    if oldcall not in code: raise RuntimeError('Chamada Gemini não localizada')
    code=code.replace(oldcall,'  return callGeminiWithFallback_(apiKey, model, body);\n',1)

helper=r'''function callGeminiWithFallback_(apiKey, preferredModel, body) {
  const candidates=[];
  [String(preferredModel||'').trim(),'gemini-3.5-flash-lite','gemini-3.6-flash','gemini-3.5-flash'].forEach(m=>{
    if(m&&candidates.indexOf(m)<0)candidates.push(m);
  });
  let lastMessage='',quotaMessage='';
  for(let i=0;i<candidates.length;i++){
    const currentModel=candidates[i];
    try{
      const response=UrlFetchApp.fetch(GEMINI_API_BASE_URL+encodeURIComponent(currentModel)+':generateContent',{
        method:'post',contentType:'application/json',headers:{'x-goog-api-key':apiKey},
        payload:JSON.stringify(body),muteHttpExceptions:true
      });
      const status=response.getResponseCode(),raw=response.getContentText();
      let parsed; try{parsed=JSON.parse(raw);}catch(_){parsed={};}
      if(status>=200&&status<300){
        const outputText=extractGeminiText_(parsed);
        if(!outputText){lastMessage='A IA não retornou uma análise utilizável.';continue;}
        let result;try{result=JSON.parse(outputText);}catch(_){lastMessage='Não foi possível interpretar a análise da IA.';continue;}
        return {ok:true,result:result,model:currentModel};
      }
      const apiMessage=parsed&&parsed.error?String(parsed.error.message||''):'';
      if(status===429){quotaMessage='A cota da IA está temporariamente indisponível para os modelos configurados.';lastMessage=apiMessage||quotaMessage;continue;}
      if(status===400||status===404||status===503){lastMessage=apiMessage||('Modelo '+currentModel+' indisponível ('+status+').');continue;}
      return {ok:false,message:apiMessage||('A IA respondeu com erro '+status+'.')};
    }catch(error){lastMessage='Falha ao consultar '+currentModel+': '+String(error);}
  }
  return {ok:false,code:'AI_MODEL_NOT_AVAILABLE',message:quotaMessage||lastMessage||'Nenhum modelo de IA ficou disponível nesta tentativa.'};
}

'''
if 'function callGeminiWithFallback_' not in code:
    code=code.replace('function aiSafetyInstructions_() {\n',helper+'function aiSafetyInstructions_() {\n',1)

oldmsg="""      return {ok: false, message: mode === 'medical_pdf_import'
        ? 'Selecione um PDF válido com o controle de periódicos.'
        : 'Selecione um PDF válido com a lista de funcionários.'};
"""
newmsg="""      return {ok: false, message: mode === 'medical_pdf_import'
        ? 'Selecione um PDF válido com o controle de periódicos.'
        : mode === 'training_record_import'
          ? 'Selecione um PDF válido com o registro de treinamento.'
          : 'Selecione um PDF válido com a lista de funcionários.'};
"""
code=code.replace(oldmsg,newmsg,1)

pubp.write_text(pub,encoding='utf-8',newline='\n')
sp.write_text(s,encoding='utf-8',newline='\n')
ip.write_text(ui,encoding='utf-8',newline='\n')
tp.write_text(train,encoding='utf-8',newline='\n')
cp.write_text(code,encoding='utf-8',newline='\n')

assert 'version: 3.29.75+217' in pub
assert 'excel_community: ^2.4.0' in pub
assert "allowedExtensions: const ['pdf', 'xlsx', 'xls', 'csv']" in s
assert '_parseLegacyXls(' in s and "'mode':'training_record_import'" in s
assert 'PDF, XLSX, XLS ou CSV' in ui
assert "subtitle: 'PDF, Excel ou foto'" in train
assert "'training_record_import'" in code and 'function callGeminiWithFallback_' in code
print('TRAINING_IMPORT_ROBUST_V32975_OK')

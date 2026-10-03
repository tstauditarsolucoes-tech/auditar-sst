#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
root=Path(sys.argv[1]); platform=sys.argv[2].lower(); assert platform in ('android','windows')
def rd(p): return (root/p).read_text(encoding='utf-8')
def wr(p,s): (root/p).write_text(s,encoding='utf-8',newline='\n')
protected=['lib/database.dart','lib/services/device_sync_service.dart','lib/services/apps_script_http.dart','lib/services/sync_coordinator.dart','lib/services/auth_service.dart','lib/services/drive_service.dart','lib/services/media_sync_service.dart','lib/services/ai_assistant_service.dart','lib/services/auditar_technical_inspection_pdf_service.dart','lib/services/auditar_standard2_pdf_service.dart','lib/services/auditar_standard3_pdf_service.dart','lib/services/report_logo_service.dart','painel_web_google_apps_script/Code.gs','painel_web_google_apps_script/MultiUser.gs','painel_web_google_apps_script/ClientPortal.gs','painel_web_google_apps_script/ClientPortal.html','painel_web_google_apps_script/ReportEmail.gs']
before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in protected}

# Ronda UI only: no AI changes.
p='lib/screens/express_round_screen.dart'; s=rd(p)
for a,b in [
('Resumo da Ronda Expressa','Resumo da vistoria'),
("_summaryChip('Não conformidades',","_summaryChip('Não conformes',"),
("_summaryChip('Conformidades',","_summaryChip('Conformes',"),
("_summaryChip('Recorrentes',","_summaryChip('Poss. recorrências',"),
('IA - revisar toda a ronda','IA · revisar a vistoria e conclusão'),
('Relatório fotográfico - estilo Performance/Quality','Gerar relatório de vistoria'),
('Relatório técnico - situação, riscos e recomendações','Relatório técnico detalhado'),
('Conclusão da IA revisada e pronta para entrar no relatório.','Conclusão revisada e pronta para o relatório.'),
('Continuar para a conclusão','Revisar conclusão'),
('A análise abaixo é apoio ao responsável técnico. Revise antes de emitir o PDF.','A IA preparou uma síntese dos registros. Revise o conteúdo técnico antes de emitir o PDF.'),
]: s=s.replace(a,b)
s=s.replace("? 'IA analisando foto • ${_aiPhotoElapsedSeconds}s'", "? (_aiPhotoElapsedSeconds < 8 ? 'Preparando foto para análise...' : _aiPhotoElapsedSeconds < 35 ? 'IA analisando a evidência...' : _aiPhotoElapsedSeconds < 55 ? 'Quase concluindo...' : 'A análise está demorando um pouco mais...')")
start=s.find('  List<Widget> _reviewWidgets(')
if start<0: raise RuntimeError('_reviewWidgets ausente')
m=re.search(r'\n  (?:Future<[^\n]+>|Future<void>|void|Widget|String|int|bool|Map<[^\n]+>|List<[^\n]+>)\s+_[A-Za-z0-9_]+\(',s[start+10:])
if not m: raise RuntimeError('fim _reviewWidgets ausente')
end=start+10+m.start()+1
new=r'''  List<Widget> _reviewWidgets(Map<String, dynamic> data) {
    String text(List<String> keys) {
      for (final key in keys) {
        final value = data[key];
        if (value is String && value.trim().isNotEmpty) return value.trim();
        if (value is List) {
          final joined = value.whereType<String>().map((e) => e.trim()).where((e) => e.isNotEmpty).join('\n');
          if (joined.isNotEmpty) return joined;
        }
      }
      return '';
    }
    Widget card(String title, String body) => Container(
      width: double.infinity, margin: const EdgeInsets.only(bottom: 10), padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: const Color(0xFFF7F9FC), borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFD9E0EA))),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children:[Text(title,style:const TextStyle(fontWeight:FontWeight.w800,color:AuditarBrand.navy)),const SizedBox(height:5),Text(body,style:const TextStyle(height:1.35))]));
    final out=<Widget>[];
    final conclusion=text(const ['finalConclusion','conclusion','conclusao','conclusaoFinal','executiveSummary','managementSummary','summary']);
    final critical=text(const ['criticalSummary','prioritySummary','mainRisks','criticalFindings']);
    final notes=text(const ['generalNotes','technicalSummary','overview']);
    final refs=text(const ['likelyReferences','references','probableReferences','normativeReferences']);
    if(conclusion.isNotEmpty) out.add(card('Conclusão sugerida',conclusion));
    if(critical.isNotEmpty && critical!=conclusion) out.add(card('Pontos prioritários',critical));
    if(notes.isNotEmpty && notes!=conclusion && notes!=critical && notes.length<1200) out.add(card('Resumo técnico',notes));
    if(refs.isNotEmpty) out.add(card('Referências para conferência',refs));
    final raw=data['actionPlanSuggestions']??data['actionPlan']??data['actions']??data['suggestedActions'];
    if(raw is List){
      final actions=raw.whereType<Map>().take(8).toList();
      if(actions.isNotEmpty) out.add(const Padding(padding:EdgeInsets.only(top:2,bottom:7),child:Text('Ações sugeridas',style:TextStyle(fontSize:17,fontWeight:FontWeight.w800,color:AuditarBrand.navy))));
      for(var i=0;i<actions.length;i++){
        final a=Map<String,dynamic>.from(actions[i]);
        String first(List<String> keys){for(final k in keys){final v='${a[k]??''}'.trim();if(v.isNotEmpty&&v.toLowerCase()!='null')return v;}return '';}
        final lines=<String>[first(['nonConformity','finding','description','title']),if(first(['locationDetail','location','sector'])).isNotEmpty)'Local: ${first(['locationDetail','location','sector'])}',if(first(['correctiveAction','recommendation','action','immediateAction'])).isNotEmpty)'Correção: ${first(['correctiveAction','recommendation','action','immediateAction'])}',if(first(['responsible','responsibleProfile','owner'])).isNotEmpty)'Responsável sugerido: ${first(['responsible','responsibleProfile','owner'])}',if(first(['priority'])).isNotEmpty)'Prioridade: ${first(['priority'])}',if(first(['suggestedDeadlineDays','deadlineDays'])).isNotEmpty)'Prazo sugerido: ${first(['suggestedDeadlineDays','deadlineDays'])} dia(s)'].where((e)=>e.isNotEmpty).toList();
        out.add(card('Ação ${i+1}',lines.join('\n')));
      }
    }
    return out.isEmpty ? const [Text('Revisão concluída sem conteúdo textual estruturado para exibição.')] : out;
  }
'''
s=s[:start]+new+s[end:]; wr(p,s)

# Ronda PDF adopts Padrão Auditar 3 visual structure.
p='lib/services/express_round_pdf_service.dart'; q=rd(p)
q=q.replace("'RELATÓRIO FOTOGRÁFICO DE VISTORIA SST'","'RELATÓRIO DE VISTORIA TÉCNICA'").replace("'RELATÓRIO TÉCNICO DE VISTORIA SST'","'RELATÓRIO DE VISTORIA TÉCNICA'")
a=q.find('  static pw.Widget _header('); b=q.find('  static pw.Widget _companyTable(',a)
if a<0 or b<0: raise RuntimeError('header Ronda ausente')
header=r'''  static pw.Widget _header(Company company,pw.ImageProvider? companyLogo,pw.ImageProvider? auditarLogo,PdfColor primary,String logoMode) => pw.Column(children:[
    pw.Row(crossAxisAlignment:pw.CrossAxisAlignment.center,children:[_pdfLogo(auditarLogo,72,47),pw.Expanded(child:pw.Column(children:[pw.Text('RELATÓRIO DE VISTORIA TÉCNICA',textAlign:pw.TextAlign.center,style:pw.TextStyle(color:primary,fontSize:12,fontWeight:pw.FontWeight.bold)),pw.SizedBox(height:2),pw.Text(company.name.toUpperCase(),textAlign:pw.TextAlign.center,style:pw.TextStyle(color:primary,fontSize:11,fontWeight:pw.FontWeight.bold))])),_pdfLogo(companyLogo,70,50)]),
    pw.SizedBox(height:6),pw.Text([company.name.toUpperCase(),if((company.cnpj??'').trim().isNotEmpty)'CNPJ: ${(company.cnpj??'').trim()}'].join('  |  '),textAlign:pw.TextAlign.center,style:pw.TextStyle(fontSize:7.4,fontWeight:pw.FontWeight.bold)),pw.SizedBox(height:7),pw.Container(height:.6,color:PdfColors.grey500),pw.SizedBox(height:8)]);

'''
q=q[:a]+header+q[b:]
a=q.find('  static pw.Widget _companyTable('); mm=re.search(r'\n  static pw\.[A-Za-z]+ _tableRow\(',q[a:])
if a<0 or not mm: raise RuntimeError('companyTable Ronda ausente')
b=a+mm.start()+1
company=r'''  static pw.Widget _companyTable(Company company,DateTime? visitDate){
    final locality=[if((company.city??'').trim().isNotEmpty)company.city!.trim(),if((company.uf??'').trim().isNotEmpty)company.uf!.trim()].join('/');
    final date=visitDate==null?'Não informado':DateFormat('dd/MM/yyyy').format(visitDate);
    pw.Widget v(String l,String x)=>pw.RichText(text:pw.TextSpan(children:[pw.TextSpan(text:'$l: ',style:pw.TextStyle(fontSize:7.4,fontWeight:pw.FontWeight.bold)),pw.TextSpan(text:x.trim().isEmpty?'Não informado':x.trim(),style:const pw.TextStyle(fontSize:7.4))]));
    return pw.Container(decoration:pw.BoxDecoration(border:pw.Border.all(color:PdfColors.grey500,width:.6)),padding:const pw.EdgeInsets.all(8),child:pw.Column(crossAxisAlignment:pw.CrossAxisAlignment.start,children:[pw.Text('IDENTIFICAÇÃO DA EMPRESA',style:pw.TextStyle(color:const PdfColor(.08,.20,.29),fontSize:9,fontWeight:pw.FontWeight.bold)),pw.SizedBox(height:6),pw.Row(children:[pw.Expanded(child:v('RAZÃO SOCIAL',company.name)),pw.SizedBox(width:10),pw.Expanded(child:v('CNPJ',company.cnpj??''))]),pw.SizedBox(height:4),pw.Row(children:[pw.Expanded(child:v('LOCALIDADE',locality)),pw.SizedBox(width:10),pw.Expanded(child:v('DATA DA VISTORIA',date))]),pw.SizedBox(height:4),v('ENDEREÇO COMPLETO','Não informado')]));
  }

'''
q=q[:a]+company+q[b:]
a=q.find('  static List<pw.Widget> _photographicBlocks('); b=q.find('  static List<pw.Widget> _technicalBlocks(',a)
if a<0 or b<0: raise RuntimeError('photographic Ronda ausente')
paren=q.find('(',a); dep=0; close=-1
for i in range(paren,len(q)):
    if q[i]=='(': dep+=1
    elif q[i]==')':
        dep-=1
        if dep==0: close=i; break
body=q.find('{',close); sig=q[a:body+1]
for n in ('record','sectors','primary'):
    if not re.search(r'\b'+n+r'\b',sig): raise RuntimeError('param '+n+' ausente')
photo=r'''
    final first=_photo(record), second=_secondPhoto(record), image=first??second, image2=first==null?null:second; final p=record.payload; final conform=_conformity(record);
    String pick(List<Object?> xs){for(final x in xs){final v='${x??''}'.trim();if(v.isNotEmpty&&v.toLowerCase()!='null')return v;}return '';}
    final situation=pick([p['description'],p['nonConformity'],record.title]); final risk=conform?'':pick([p['risk'],p['riskIdentified'],p['possibleConsequence']]); final correction=pick([p['recommendation'],p['correctiveAction'],p['immediateAction']]); final priority=pick([p['priority'],record.priority]); final title=pick([p['aiTitle'],p['title'],p['category'],record.title,conform?'Boa prática observada':'Não conformidade']);
    final direct=pick([p['location'],p['locationDetail'],p['sectorName']]); final line=_locationLine(record,sectors); final location=direct.isNotEmpty?direct:line.replaceFirst(RegExp(r'\s+-\s+\d{2}/\d{2}/\d{4}.*$'),'').trim();
    pw.Widget f(String l,String v)=>pw.Padding(padding:const pw.EdgeInsets.only(bottom:5),child:pw.RichText(text:pw.TextSpan(children:[pw.TextSpan(text:'$l: ',style:pw.TextStyle(fontSize:8.1,fontWeight:pw.FontWeight.bold)),pw.TextSpan(text:v,style:const pw.TextStyle(fontSize:8.1,lineSpacing:1.7))])));
    final evidence=image==null?pw.Container(height:145,alignment:pw.Alignment.center,decoration:pw.BoxDecoration(color:PdfColors.grey100,border:pw.Border.all(color:PdfColors.grey300)),child:const pw.Text('Sem fotografia associada',style:pw.TextStyle(fontSize:8,color:PdfColors.grey600))):image2==null?pw.SizedBox(height:150,child:pw.Image(image,fit:pw.BoxFit.contain)):pw.Row(mainAxisAlignment:pw.MainAxisAlignment.center,children:[pw.Image(image,width:108,height:145,fit:pw.BoxFit.contain),pw.SizedBox(width:5),pw.Image(image2,width:108,height:145,fit:pw.BoxFit.contain)]);
    return [pw.Container(constraints:const pw.BoxConstraints(minHeight:205),decoration:pw.BoxDecoration(border:pw.Border.all(color:PdfColors.grey500,width:.55)),child:pw.Row(crossAxisAlignment:pw.CrossAxisAlignment.start,children:[pw.Expanded(flex:49,child:pw.Container(padding:const pw.EdgeInsets.all(8),decoration:const pw.BoxDecoration(border:pw.Border(right:pw.BorderSide(color:PdfColors.grey500,width:.55))),child:pw.Column(mainAxisAlignment:pw.MainAxisAlignment.center,children:[evidence,if(location.isNotEmpty)...[pw.SizedBox(height:5),pw.Text(location,textAlign:pw.TextAlign.center,style:const pw.TextStyle(fontSize:6.6,color:PdfColors.grey700))]]))),pw.Expanded(flex:51,child:pw.Padding(padding:const pw.EdgeInsets.all(9),child:pw.Column(crossAxisAlignment:pw.CrossAxisAlignment.start,children:[pw.Text(title.toUpperCase(),style:pw.TextStyle(color:const PdfColor(.08,.20,.29),fontSize:9.5,fontWeight:pw.FontWeight.bold)),pw.SizedBox(height:7),f('Local',location.isEmpty?'Não informado':location),if(situation.isNotEmpty)f('Situação',situation),if(risk.isNotEmpty)f('Risco',risk),if(correction.isNotEmpty)f('Correção',correction),if(priority.isNotEmpty)pw.Text('PRIORIDADE: ${priority.toUpperCase()}',style:pw.TextStyle(color:priority.toLowerCase().contains('crít')||priority.toLowerCase().contains('critic')||priority.toLowerCase().contains('imediat')?PdfColors.red800:const PdfColor(.62,.42,.05),fontSize:8.2,fontWeight:pw.FontWeight.bold))]))))]))];
  }

'''
q=q[:a]+sig+photo+q[b:]
a=q.find('  static List<pw.Widget> _technicalBlocks('); b=q.find('  static List<pw.Widget> _aiReviewBlocks(',a)
paren=q.find('(',a); dep=0; close=-1
for i in range(paren,len(q)):
    if q[i]=='(': dep+=1
    elif q[i]==')':
        dep-=1
        if dep==0: close=i; break
body=q.find('{',close); sig2=q[a:body+1]
q=q[:a]+sig2+'\n    return _photographicBlocks(record,sectors,primary);\n  }\n\n'+q[b:]
old="""nonConformities == 0
                    ? 'Nos registros desta vistoria constam ${sorted.length} item(ns), sem não conformidades registradas. Recomenda-se manter os controles observados e acompanhar suas condições.'
                    : 'Nos registros desta vistoria constam ${sorted.length} item(ns), sendo ${nonConformities} não conformidade(s) e ${conformities} conformidade(s). Recomenda-se programar as correções descritas e verificar sua execução em acompanhamento posterior.',"""
newc="""aiConclusion.trim().isNotEmpty
                    ? aiConclusion.trim()
                    : nonConformities == 0
                        ? 'Nos registros desta vistoria constam ${sorted.length} item(ns), sem não conformidades registradas. Recomenda-se manter os controles observados e acompanhar suas condições.'
                        : 'Nos registros desta vistoria constam ${sorted.length} item(ns), sendo ${nonConformities} não conformidade(s) e ${conformities} conformidade(s). Recomenda-se programar as correções descritas e verificar sua execução em acompanhamento posterior.',"""
if old not in q: raise RuntimeError('conclusao Ronda ausente')
q=q.replace(old,newc,1)
head=q[q.find('  static pw.Widget _header('):q.find('  static pw.Widget _companyTable(')]
if 'companyLogo ?? auditarLogo' in head: raise RuntimeError('logo duplicada')
wr(p,q)

p='lib/services/report_template_service.dart'; t=rd(p).replace("name: 'Padrão Auditar anterior'","name: 'Padrão Auditar (legado)'"); wr(p,t)
p='pubspec.yaml'; v=rd(p); oldv,newv=(('3.29.152+294','3.29.153+295') if platform=='android' else ('3.30.71+258','3.30.72+259')); assert v.count('version: '+oldv)==1; wr(p,v.replace('version: '+oldv,'version: '+newv,1))
changed=[p for p,h in before.items() if hashlib.sha256((root/p).read_bytes()).hexdigest()!=h]
if changed: raise SystemExit('PROTECTED_CORE_OR_AI_MODIFIED: '+repr(changed))
assert 'Resumo da vistoria' in rd('lib/screens/express_round_screen.dart') and 'Ações sugeridas' in rd('lib/screens/express_round_screen.dart')
assert 'RELATÓRIO DE VISTORIA TÉCNICA' in rd('lib/services/express_round_pdf_service.dart') and "f('Situação'" in rd('lib/services/express_round_pdf_service.dart') and 'aiConclusion.trim().isNotEmpty' in rd('lib/services/express_round_pdf_service.dart')
print('RONDA_UI_PADRAO3_OK',platform,newv); print('AI_SYNC_DB_AUTH_HTTP_MEDIA_DRIVE_GS_PREVIOUS_REPORTS_BYTE_IDENTICAL_OK')

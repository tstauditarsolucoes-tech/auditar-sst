#!/usr/bin/env python3
"""Ênfase OPCIONAL no relatório técnico Padrão Auditar 3, com escopo por PDF.
Não altera schema, dados, sincronização, login, mídia, GS ou relatórios legados.
"""
from pathlib import Path
import hashlib,re,shutil,sys
root=Path(sys.argv[1]); repo=Path(__file__).resolve().parents[1]
assert len(sys.argv)==3 and sys.argv[2] in ('android','windows')
report=root/'lib/screens/report_screen.dart'
renderer=root/'lib/services/auditar_standard3_pdf_service.dart'
scope=root/'lib/services/report_pdf_emphasis_scope.dart'
assert report.exists() and renderer.exists() and not scope.exists()
protected=['lib/database.dart','lib/models.dart','lib/services/auth_service.dart',
 'lib/services/device_sync_service.dart','lib/services/sync_coordinator.dart',
 'lib/services/media_sync_service.dart','lib/services/drive_service.dart',
 'lib/services/apps_script_http.dart','lib/services/ai_assistant_service.dart',
 'lib/services/styled_report_pdf_service.dart','lib/services/pdf_service.dart',
 'lib/services/auditar_standard2_pdf_service.dart',
 'painel_web_google_apps_script/Code.gs','painel_web_google_apps_script/MultiUser.gs']
before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in protected if (root/p).exists()}
def exactly(text,old,new):
 assert text.count(old)==1,(old,text.count(old))
 return text.replace(old,new,1)
shutil.copyfile(repo/'feature_sources/report_pdf_emphasis_scope_v1.dart',scope)
s=report.read_text(encoding='utf8')
s="import '../services/report_pdf_emphasis_scope.dart';\n"+s
s=exactly(s,"  String _buildOfflineInspectionConclusion() {",
"  bool _highlightRecommendationsPdf = false;\n\n  String _buildOfflineInspectionConclusion() {")
marker="'Conclusão do relatório — sem IA'"
assert s.count(marker)==1
idx=s.index(marker)
card=s.rfind('Card(',0,idx)
assert card>=0
start=s.rfind('\n',0,card)+1
indent=s[start:card]
assert not indent.strip()
control="""SwitchListTile.adaptive(
  title: const Text('Destacar recomendações importantes no PDF'),
  subtitle: const Text('Opcional: negrito e realce discreto das correções no Padrão Auditar 3.'),
  value: _highlightRecommendationsPdf,
  onChanged: (v) => setState(() => _highlightRecommendationsPdf = v),
),
"""
s=s[:start]+indent+control.replace('\n','\n'+indent)+s[start:]
startPhrase=r'final bytes\s*=\s*await PdfService\.generateInspectionPdf\('
matches=list(re.finditer(startPhrase,s))
assert len(matches)==1,('pdf-generation-calls',len(matches))
m=matches[0]
tail=s[m.end():]
# A chamada tem parâmetros nomeados; localiza o fechamento desta invocação.
end=re.search(r'\n\s*\);',tail)
assert end is not None
prefix='final bytes = await ReportPdfEmphasisScope.run(_highlightRecommendationsPdf,\n'
replacement=prefix+'        () => PdfService.generateInspectionPdf('+tail[:end.start()]+'\n      ));'
s=s[:m.start()]+replacement+tail[end.end():]
report.write_text(s,encoding='utf8',newline='\n')
s=renderer.read_text(encoding='utf8')
s="import 'report_pdf_emphasis_scope.dart';\n"+s
correction=r"_paragraph\(\s*'Correção'\s*,\s*issue\.correction\s*\)"
hits=list(re.finditer(correction,s))
assert len(hits)==1,('correction-block-count',len(hits))
m=hits[0]
s=s[:m.start()]+"(ReportPdfEmphasisScope.enabled ? _emphasizedCorrection(issue.correction) : "+m.group(0)+")"+s[m.end():]
helper="""  static pw.Widget _emphasizedCorrection(String recommendation) =>
      pw.Container(
        margin: const pw.EdgeInsets.only(bottom:5),
        padding: const pw.EdgeInsets.all(7),
        decoration: pw.BoxDecoration(
          color: const PdfColor(0.94,0.97,0.93),
          border: pw.Border(left: pw.BorderSide(color:_green,width:2.5))),
        child: pw.RichText(text:pw.TextSpan(children:[
          pw.TextSpan(text:'CORREÇÃO RECOMENDADA: ',style:pw.TextStyle(
            fontSize:8.3,color:_navy,fontWeight:pw.FontWeight.bold)),
          pw.TextSpan(text:recommendation,style:pw.TextStyle(
            fontSize:8.3,color:_navy,fontWeight:pw.FontWeight.bold)),
        ])),
      );

"""
anchor="  static pw.Widget _paragraph("
assert s.count(anchor)==1
s=s.replace(anchor,helper+anchor,1)
renderer.write_text(s,encoding='utf8',newline='\n')
for path,digest in before.items():
 assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest,path
assert '_highlightRecommendationsPdf' in report.read_text(encoding='utf8')
assert 'ReportPdfEmphasisScope.enabled' in renderer.read_text(encoding='utf8')
print('STANDARD_3_REPORT_EMPHASIS_OPT_IN_ONLY_NO_DATA_CHANGES')

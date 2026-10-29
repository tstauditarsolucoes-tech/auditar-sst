#!/usr/bin/env python3
"""Ampliação aditiva da biblioteca offline e ênfase opcional no PDF gerencial."""
from pathlib import Path
import hashlib,re,shutil,sys
assert len(sys.argv)==3 and sys.argv[2] in ('android','windows')
root=Path(sys.argv[1]);repo=Path(__file__).resolve().parents[1]
protected=[
 'lib/database.dart','lib/models.dart','lib/services/auth_service.dart',
 'lib/services/device_sync_service.dart','lib/services/sync_coordinator.dart',
 'lib/services/media_sync_service.dart','lib/services/drive_service.dart',
 'lib/services/apps_script_http.dart','lib/services/ai_assistant_service.dart',
 'painel_web_google_apps_script/Code.gs','painel_web_google_apps_script/MultiUser.gs',
 'painel_web_google_apps_script/ClientPortal.gs','painel_web_google_apps_script/ClientPortal.html']
before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in protected if (root/p).exists()}
def exactly(src,old,new):
    n=src.count(old)
    assert n==1,(old,n)
    return src.replace(old,new,1)
def pattern(src,rx,fn):
    matches=list(re.finditer(rx,src,re.S))
    assert len(matches)==1,(rx,len(matches))
    m=matches[0]
    return src[:m.start()]+fn(m)+src[m.end():]

widget=root/'lib/widgets/offline_report_inline_suggestions.dart'
manager=root/'lib/screens/manager_reports_screen.dart'
assert widget.is_file() and manager.is_file()
dest=root/'lib/services/offline_sst_expanded_catalog_v1.dart'
assert not dest.exists()
shutil.copyfile(repo/'feature_sources/offline_sst_expanded_catalog_v1.dart',dest)

s=widget.read_text(encoding='utf8')
s=exactly(s,"import '../services/offline_reasoning.dart';",
"import '../services/offline_reasoning.dart';\nimport '../services/offline_sst_expanded_catalog_v1.dart';")
newCatalog="""  static final List<OfflineInlineSuggestion> _expanded = [
    for(final item in OfflineSstExpandedCatalog.entries)
      OfflineInlineSuggestion(
        id:item['id']!, title:item['title']!, description:item['description']!,
        risk:item['risk']!, possibleConsequence:item['possibleConsequence']!,
        recommendation:item['recommendation']!, priority:item['priority']!,
        source:'auditar_seed'),
  ];

"""
s=pattern(s,r'(?m)^(\s*)static const _fallback = <OfflineInlineSuggestion>\[',
    lambda m: newCatalog+m.group(0))
s=pattern(s,r'\.\.\._fallback,\s*\.\.\.await _learnedSuggestions\(\),',
    lambda m:"..._fallback,\n      ..._expanded,\n      ...await _learnedSuggestions(),")
s=pattern(s,r'int limit\s*=\s*3,',lambda m:'int limit = 6,')
s=pattern(s,r'static List<OfflineInlineSuggestion> get fallbackForTesting\s*=>\s*_fallback\s*;',
    lambda m:'static List<OfflineInlineSuggestion> get fallbackForTesting => [..._fallback, ..._expanded];')
s=pattern(s,r'final ranked\s*=\s*_fallback(?=\s*\.map)',
    lambda m:'final ranked = <OfflineInlineSuggestion>[..._fallback, ..._expanded]')
widget.write_text(s,encoding='utf8',newline='\n')

m=manager.read_text(encoding='utf8')
helper="""  static pw.Widget _emphasisLine(String label, String data) => pw.Container(
    margin: const pw.EdgeInsets.only(bottom:5),
    padding: const pw.EdgeInsets.symmetric(horizontal:9,vertical:7),
    decoration: pw.BoxDecoration(
      color:pale, border: pw.Border(left:pw.BorderSide(color:green,width:3))),
    child:pw.RichText(text:pw.TextSpan(children:[
      pw.TextSpan(text:'$label  ',style:pw.TextStyle(
        color:navy,fontSize:9,fontWeight:pw.FontWeight.bold)),
      pw.TextSpan(text:data.isEmpty?'Não informado':data,
        style:pw.TextStyle(color:navy,fontSize:9,fontWeight:pw.FontWeight.bold)),
    ])),
  );
"""
m=pattern(m,r'(?m)^\s*static pw.Widget _section\(',lambda x:helper+x.group(0))
m=pattern(m,r'required bool includePhotos,\s*String search\s*=\s*'+"''"+r',',
    lambda x:"required bool includePhotos,\n    bool highlightRecommendations = false,\n    String search = '',")
for label,value in [
 ('Correção recomendada',('nc','recommendation')),
 ('Plano de ação',('action','corrective_action')),
 ('Ação necessária',('action','corrective_action')),
]:
 rx=(r'_line\(\s*'+re.escape("'"+label+"'")+r'\s*,\s*_short\(\s*value\(\s*'
      +value[0]+r'\s*,\s*'+re.escape("'"+value[1]+"'")+r'\s*\)\s*\)\s*\)')
 matches=list(re.finditer(rx,m,re.S))
 if label=='Ação necessária' and not matches:
  # Algumas versões já tratam a ação em um renderer separado.
  continue
 assert len(matches)==1,(label,len(matches))
 m=pattern(m,rx,lambda x:'(highlightRecommendations ? _emphasisLine'+x.group(0)[5:]+' : '+x.group(0)+')')
m=pattern(m,r'bool includePhotos\s*=\s*true\s*;',
    lambda x:x.group(0)+'\n  bool highlightRecommendations = false;')
# Liga a opção visual somente quando se identifica o ponto de geração do PDF.
# Em versões com chamada diferente, não exibe uma caixa inoperante.
callPattern=r'includePhotos:\s*includePhotos\s*,'
calls=list(re.finditer(callPattern,m))
linked=len(calls)==1
if linked:
 m=pattern(m,callPattern,lambda x:x.group(0)+'\n          highlightRecommendations: highlightRecommendations,')
label="'Incluir fotografias disponíveis'"
pos=m.index(label)
anchor=m.rfind('SwitchListTile.adaptive(',0,pos)
assert anchor>=0
start=m.rfind('\n',0,anchor)+1
indent=m[start:anchor]
assert not indent.strip()
addition="""SwitchListTile.adaptive(
  contentPadding: EdgeInsets.zero,
  title: const Text('Destacar recomendações importantes'),
  subtitle: const Text('Opcional: negrito e faixa discreta nas correções prioritárias.'),
  value: highlightRecommendations,
  onChanged: busy ? null : (v) => setState(() => highlightRecommendations = v),
),
"""
if linked:
 m=m[:start]+indent+addition.replace('\n','\n'+indent)+m[start:]
else:
 print('PDF_MANAGER_HIGHLIGHT_UI_SKIPPED_CALL_NOT_FOUND')
manager.write_text(m,encoding='utf8',newline='\n')
pub=root/'pubspec.yaml'
current=pub.read_text(encoding='utf8')
old,new=('3.29.195+337','3.29.196+338') if sys.argv[2]=='android' else ('3.30.123+310','3.30.124+311')
pub.write_text(exactly(current,'version: '+old,'version: '+new),encoding='utf8',newline='\n')
for path,digest in before.items():
    assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest,path
print('SST_LIBRARY_AND_OPTIONAL_MANAGER_PDF_EMPHASIS_READY',sys.argv[2])

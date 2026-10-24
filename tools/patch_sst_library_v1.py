#!/usr/bin/env python3
"""Amplia sugestões offline e adiciona realce OPCIONAL nos PDFs gerenciais."""
from pathlib import Path
import hashlib,shutil,sys
root=Path(sys.argv[1]);repo=Path(__file__).resolve().parents[1]
assert len(sys.argv)>2 and sys.argv[2] in ('android','windows')
protected=['lib/database.dart','lib/models.dart','lib/services/auth_service.dart',
 'lib/services/device_sync_service.dart','lib/services/sync_coordinator.dart',
 'lib/services/media_sync_service.dart','lib/services/drive_service.dart',
 'lib/services/apps_script_http.dart','lib/services/ai_assistant_service.dart',
 'painel_web_google_apps_script/Code.gs','painel_web_google_apps_script/MultiUser.gs',
 'painel_web_google_apps_script/ClientPortal.gs','painel_web_google_apps_script/ClientPortal.html']
before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in protected if (root/p).exists()}
def replace_one(src,old,new):
 assert src.count(old)==1,(old,src.count(old))
 return src.replace(old,new,1)
widget=root/'lib/widgets/offline_report_inline_suggestions.dart'
manager=root/'lib/screens/manager_reports_screen.dart'
assert widget.exists() and manager.exists()
dest=root/'lib/services/offline_sst_expanded_catalog_v1.dart'
assert not dest.exists()
shutil.copyfile(repo/'feature_sources/offline_sst_expanded_catalog_v1.dart',dest)
s=widget.read_text(encoding='utf8')
s=replace_one(s,"import '../services/offline_reasoning.dart';",
"import '../services/offline_reasoning.dart';\nimport '../services/offline_sst_expanded_catalog_v1.dart';")
added="""  static final List<OfflineInlineSuggestion> _expanded = [
    for (final item in OfflineSstExpandedCatalog.entries)
      OfflineInlineSuggestion(
        id: item['id']!, title: item['title']!, description: item['description']!,
        risk: item['risk']!, possibleConsequence: item['possibleConsequence']!,
        recommendation: item['recommendation']!, priority: item['priority']!,
        source: 'auditar_seed'),
  ];

"""
s=replace_one(s,"  static const _fallback = <OfflineInlineSuggestion>[",added+"  static const _fallback = <OfflineInlineSuggestion>[")
s=replace_one(s,"      ..._fallback,\n      ...await _learnedSuggestions(),",
"      ..._fallback,\n      ..._expanded,\n      ...await _learnedSuggestions(),")
s=replace_one(s,"    int limit = 3,","    int limit = 6,")
s=replace_one(s,"  static List<OfflineInlineSuggestion> get fallbackForTesting => _fallback;",
"  static List<OfflineInlineSuggestion> get fallbackForTesting => [..._fallback, ..._expanded];")
s=replace_one(s,"    final ranked = _fallback\n",
"    final ranked = <OfflineInlineSuggestion>[..._fallback, ..._expanded]\n")
widget.write_text(s,encoding='utf8',newline='\n')
m=manager.read_text(encoding='utf8')
helper="""  static pw.Widget _emphasisLine(String label, String data) => pw.Container(
    margin: const pw.EdgeInsets.only(bottom:5),
    padding: const pw.EdgeInsets.symmetric(horizontal:9,vertical:7),
    decoration: pw.BoxDecoration(color:pale,
      border: pw.Border(left: pw.BorderSide(color:green,width:3))),
    child: pw.RichText(text:pw.TextSpan(children:[
      pw.TextSpan(text:'$label  ',style:pw.TextStyle(
        fontSize:9,color:navy,fontWeight:pw.FontWeight.bold)),
      pw.TextSpan(text:data.isEmpty?'Não informado':data,
        style:pw.TextStyle(fontSize:9,color:navy,fontWeight:pw.FontWeight.bold)),
    ])),
  );
"""
m=replace_one(m,"  static pw.Widget _section(String title) =>",helper+"  static pw.Widget _section(String title) =>")
m=replace_one(m,"    required bool includePhotos,\n    String search = '',",
"    required bool includePhotos,\n    bool highlightRecommendations = false,\n    String search = '',")
for label,expr in [
 ('Correção recomendada',"_short(value(nc, 'recommendation'))"),
 ('Plano de ação',"_short(value(action, 'corrective_action'))"),
 ('Ação necessária',"_short(value(action, 'corrective_action'))"),
]:
 old=f"_line('{label}', {expr})"
 new=f"(highlightRecommendations ? _emphasisLine('{label}', {expr}) : _line('{label}', {expr}))"
 m=replace_one(m,old,new)
m=replace_one(m,"  bool includePhotos = true;",
"  bool includePhotos = true;\n  bool highlightRecommendations = false;")
m=replace_one(m,"          includePhotos: includePhotos,\n          search: specificSearch,",
"          includePhotos: includePhotos,\n          highlightRecommendations: highlightRecommendations,\n          search: specificSearch,")
old="""                onChanged: busy ? null : (v) => setState(() => includePhotos = v),
              ),
"""
new=old+"""              SwitchListTile.adaptive(
                contentPadding: EdgeInsets.zero,
                title: const Text('Destacar recomendações importantes'),
                subtitle: const Text('Opcional: texto em negrito e realce discreto para leitura rápida.'),
                value: highlightRecommendations,
                onChanged: busy ? null : (v) => setState(() => highlightRecommendations = v),
              ),
"""
m=replace_one(m,old,new)
manager.write_text(m,encoding='utf8',newline='\n')
for path,digest in before.items():
 assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest,path
print('LIBRARY_MORE_OPTIONS_AND_OPTIONAL_MANAGER_PDF_EMPHASIS_OK')

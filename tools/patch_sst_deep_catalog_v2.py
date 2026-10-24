#!/usr/bin/env python3
"""Biblioteca detalhada de vistorias com consulta por NR, sem depender da IA."""
from pathlib import Path
import re,hashlib,shutil,sys
assert len(sys.argv)==3 and sys.argv[2] in ('android','windows')
root=Path(sys.argv[1]);repo=Path(__file__).resolve().parents[1]
widget=root/'lib/widgets/offline_report_inline_suggestions.dart'
dest=root/'lib/services/offline_sst_deep_catalog_v2.dart'
assert widget.exists() and not dest.exists()
protected=['lib/database.dart','lib/models.dart','lib/services/auth_service.dart',
 'lib/services/device_sync_service.dart','lib/services/sync_coordinator.dart',
 'lib/services/media_sync_service.dart','lib/services/drive_service.dart',
 'lib/services/apps_script_http.dart','lib/services/ai_assistant_service.dart',
 'painel_web_google_apps_script/Code.gs','painel_web_google_apps_script/MultiUser.gs',
 'painel_web_google_apps_script/ClientPortal.gs','painel_web_google_apps_script/ClientPortal.html']
before={x:hashlib.sha256((root/x).read_bytes()).hexdigest() for x in protected if (root/x).is_file()}
shutil.copyfile(repo/'feature_sources/offline_sst_deep_catalog_v2.dart',dest)
def pattern(s,rx,replace):
 m=list(re.finditer(rx,s,re.S))
 assert len(m)==1,(rx,len(m))
 a=m[0]
 return s[:a.start()]+(replace(a) if callable(replace) else replace)+s[a.end():]
s=widget.read_text(encoding='utf8')
s=pattern(s,r"import '../services/offline_sst_expanded_catalog_v1.dart';",
 "import '../services/offline_sst_expanded_catalog_v1.dart';\nimport '../services/offline_sst_deep_catalog_v2.dart';")
s=pattern(s,r'for\s*\(\s*final item in OfflineSstExpandedCatalog\.entries\s*\)',
 """for (final item in <Map<String, String>>[
       ...OfflineSstExpandedCatalog.entries,
       ...OfflineSstDeepCatalog.entries,
     ])""")
# Só sugere uma nova falha se tema e condição estiverem explícitos na frase.
needle='final assessments = OfflineReasoning.analyze(query, context: contextTerms);'
assert s.count(needle)==1
s=s.replace(needle,"""final specificIds = OfflineSstDeepCatalog.matches(query)
        .map((entry) => entry['id']!)
        .toSet();
    final specific = _expanded.where((item) => specificIds.contains(item.id)).toList();
    """+needle,1)
s=pattern(s,r'final results\s*=\s*<OfflineInlineSuggestion>\[\s*\]\s*;',
 'final results = <OfflineInlineSuggestion>[...specific];')
s=pattern(s,r'results\.sort\(\(a,\s*b\)\s*\{',
 """results.sort((a,b) {
        final detailed = (specificIds.contains(b.id) ? 1 : 0)
          .compareTo(specificIds.contains(a.id) ? 1 : 0);
        if (detailed != 0) return detailed;""")
needle='if (OfflineReasoning.explicitSafeOrUncertain(query)) return const [];'
assert s.count(needle)==1
s=s.replace(needle,"if (specific.isNotEmpty) return specific.take(limit).toList();\n    "+needle,1)
s=pattern(s,r'if\s*\(_clearlyCompliant\(normalized\)\)\s*return const \[\];',
 """if (_clearlyCompliant(normalized)) return const [];
    if (RegExp(r'^nr\s*-?\s*\d{1,2}$').hasMatch(normalized)) return const [];""")
# Navegar modelos não significa validar automaticamente que existe uma NC.
method="""  Future<void> _browseCatalog(BuildContext context) async {
    final search = TextEditingController();
    var selected = 'Todas';
    const areas = <String>['Todas','NR-12','NR-06','NR-18','NR-23','NR-31','NR-35','Outras'];
    await showModalBottomSheet<void>(
      context:context,isScrollControlled:true,showDragHandle:true,
      builder:(modalContext)=>StatefulBuilder(builder:(innerContext,refresh) {
        final searchText=OfflineSstDeepCatalog.normalize(search.text);
        final matches=OfflineSstDeepCatalog.entries.where((item) {
          final nr=item['nr'] ?? '';
          final inArea=selected=='Todas'||(selected=='Outras'
             ? !areas.contains(nr):selected==nr);
          if(!inArea) return false;
          if(searchText.isEmpty) return true;
          return OfflineSstDeepCatalog.normalize(
            (item['title'] ?? '')+' '+(item['description'] ?? '')+' '+
            nr+' '+(item['recommendation'] ?? '')).contains(searchText);
        }).toList();
        return SafeArea(child:SizedBox(
          height:MediaQuery.of(innerContext).size.height*.8,
          child:Center(child:ConstrainedBox(
            constraints:const BoxConstraints(maxWidth:760),
            child:Padding(padding:const EdgeInsets.all(12),
              child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
                const Text('Biblioteca de SST por NR',
                  style:TextStyle(fontSize:17,fontWeight:FontWeight.w800)),
                const SizedBox(height:8),
                SingleChildScrollView(scrollDirection:Axis.horizontal,
                  child:Row(children:[
                    for(final area in areas) Padding(
                      padding:const EdgeInsets.only(right:6),
                      child:ChoiceChip(label:Text(area),selected:selected==area,
                        onSelected:(v) {if(v) refresh(()=>selected=area);}),
                    ),
                  ])),
                const SizedBox(height:8),
                TextField(controller:search,onChanged:(_)=>refresh((){}),
                  decoration:const InputDecoration(
                    border:OutlineInputBorder(),
                    prefixIcon:Icon(Icons.search),
                    labelText:'Pesquisar situação ou recomendação')),
                const SizedBox(height:6),
                Text('Opções encontradas: '+matches.length.toString(),
                  style:const TextStyle(fontSize:12)),
                Expanded(child:matches.isEmpty
                  ?const Center(child:Text('Nenhuma sugestão encontrada.'))
                  :ListView.builder(itemCount:matches.length,
                    itemBuilder:(listContext,index){
                      final item=matches[index];
                      return ListTile(
                        title:Text(item['title'] ?? ''),
                        subtitle:Text((item['nr'] ?? '')+' • '+(item['risk'] ?? '')),
                        trailing:const Icon(Icons.chevron_right),
                        onTap:(){
                          final id=item['id'] ?? '';
                          final suggestion=OfflineReportInlineSuggestionService
                            .fallbackForTesting.firstWhere((v)=>v.id==id);
                          Navigator.of(modalContext).pop();
                          if(context.mounted) _review(context,suggestion);
                        },
                      );
                    })),
                const Text('Sugestões orientativas: confira no local, revise e ajuste antes de registrar.',
                  style:TextStyle(fontSize:11)),
              ]),
            ),
          )),
        ));
      }),
    );
    search.dispose();
  }

  Widget _browseButton(BuildContext context) => OutlinedButton.icon(
    onPressed:()=>_browseCatalog(context),
    icon:const Icon(Icons.menu_book_outlined),
    label:const Text('Consultar biblioteca por NR'),
  );

"""
at=s.index("class OfflineReportInlineSuggestions extends StatelessWidget")
build=s.index("  @override\n  Widget build(BuildContext context) {",at)
s=s[:build]+method+s[build:]
s=pattern(s,r'if\s*\(query\.trim\(\)\.length\s*<\s*3\)\s*return const SizedBox\.shrink\(\);',
 'if (query.trim().length < 3) return _browseButton(context);')
s=pattern(s,r'if\s*\(hidden\.isNotEmpty\)\s*\n\s*TextButton\.icon\(',
 """_browseButton(context),
                    if (hidden.isNotEmpty)
                      TextButton.icon(""")
s=pattern(s,r'const Icon\(Icons\.search_off_rounded,\s*size:\s*18\),',
 """const Icon(Icons.search_off_rounded, size: 18),
                  IconButton(
                    tooltip:'Consultar biblioteca por NR',
                    onPressed:()=>_browseCatalog(context),
                    icon:const Icon(Icons.menu_book_outlined)), """)
widget.write_text(s,encoding='utf8',newline='\n')
pub=root/'pubspec.yaml'
v=pub.read_text(encoding='utf8')
old,new=('3.29.196+338','3.29.197+339') if sys.argv[2]=='android' else ('3.30.124+311','3.30.125+312')
assert v.count('version: '+old)==1,'Unexpected baseline'
pub.write_text(v.replace('version: '+old,'version: '+new,1),encoding='utf8',newline='\n')
for key,value in before.items():
 assert hashlib.sha256((root/key).read_bytes()).hexdigest()==value,key
print('DEEP_NR_SST_122_OPTIONS_SEARCH_AND_BROWSE_OK',sys.argv[2])

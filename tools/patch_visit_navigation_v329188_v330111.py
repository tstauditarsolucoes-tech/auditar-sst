#!/usr/bin/env python3
"""Navigation-only patch: switch tasks while preserving selected company."""
from pathlib import Path
import hashlib
import sys

root=Path(sys.argv[1])
platform=sys.argv[2]
assert platform in ("android","windows")
old,new=(("3.29.187+329","3.29.188+330") if platform=="android"
         else ("3.30.110+297","3.30.111+298"))
path=root/"lib/screens/quick_visit_screen.dart"
s=path.read_text(encoding="utf-8")
assert s.count("enum VisitIntent { visit, drafts, pending, reports }")==1
assert "class VisitIntentTabs " not in s
protected=[p for folder in ("lib","painel_web_google_apps_script")
           for p in (root/folder).rglob("*") if p.is_file() and p!=path]
hashes={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
tabs="""class VisitIntentTabs extends StatelessWidget {
  const VisitIntentTabs({super.key,required this.selected,required this.onSelected});
  final VisitIntent selected;
  final ValueChanged<VisitIntent>? onSelected;
  static const labels=<VisitIntent,String>{
    VisitIntent.visit:'Visita',
    VisitIntent.drafts:'Rascunhos',
    VisitIntent.pending:'Pendências',
    VisitIntent.reports:'Relatórios'
  };
  @override
  Widget build(BuildContext context)=>Wrap(
    spacing: 8,
    runSpacing: 8,
    children:[
      for(final entry in labels.entries)Padding(
        padding:const EdgeInsets.only(right:8),
        child:ChoiceChip(
          key:ValueKey('visit-intent-'+entry.key.name),
          label:Text(entry.value),
          selected:selected==entry.key,
          onSelected:onSelected==null?null:(_)=>onSelected!(entry.key),
        ),
      ),
    ],
  );
}
"""
enum="enum VisitIntent { visit, drafts, pending, reports }"
s=s.replace(enum,enum+"\n\n"+tabs,1)
assert s.count("  bool _opening = false;")==1
s=s.replace("  bool _opening = false;","  bool _opening = false;\n  late VisitIntent _activeIntent;",1)
anchor="    super.initState();\n    _load();"
assert s.count(anchor)==1
s=s.replace(anchor,"    super.initState();\n    _activeIntent=widget.intent;\n    _load();",1)
start=s.index("  Widget _tasks() {")
end=s.index("  Widget _picker() {",start)
part=s[start:end]
assert part.count("widget.intent ==")==4
part=part.replace("widget.intent ==","_activeIntent ==")
anchor="        if (_activeIntent == VisitIntent.visit) ...["
assert part.count(anchor)==1
part=part.replace(anchor,"""        VisitIntentTabs(
          selected:_activeIntent,
          onSelected:_opening?null:(intent){
            if(mounted)setState(()=>_activeIntent=intent);
          },
        ),
        const SizedBox(height:10),
"""+anchor,1)
s=s[:start]+part+s[end:]
# The header must reflect the currently selected task, not the entry intent.
# Only navigation presentation changes; no route, data, or service is replaced.
assert s.count("switch (widget.intent)") == 1, "Quick Visit app bar changed unexpectedly"
s=s.replace("switch (widget.intent)", "switch (_activeIntent)", 1)
path.write_text(s,encoding="utf-8")
pub=root/"pubspec.yaml"
v=pub.read_text(encoding="utf-8")
assert v.count("version: "+old)==1
pub.write_text(v.replace("version: "+old,"version: "+new,1),encoding="utf-8")
for f,d in hashes.items():
  assert hashlib.sha256(f.read_bytes()).hexdigest()==d,str(f)
print("NAVIGATION_COMPANY_CONTEXT_OK",platform,new,"PROTECTED_FILES_UNCHANGED")

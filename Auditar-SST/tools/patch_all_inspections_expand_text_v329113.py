#!/usr/bin/env python3
from pathlib import Path
import sys,re
root=Path(sys.argv[1]); platform=sys.argv[2]
assert platform in ('android','windows')

widget_src=Path(__file__).with_name('expandable_text_field_v329113.dart')
(root/'lib/widgets/expandable_text_field.dart').write_text(widget_src.read_text(encoding='utf-8'),encoding='utf-8',newline='\n')

def load(rel):
    p=root/rel; return p,p.read_text(encoding='utf-8')
def save(p,s): p.write_text(s,encoding='utf-8',newline='\n')
def add_import(s):
    imp="import '../widgets/expandable_text_field.dart';\n"
    if imp not in s:
        # place before local package imports near first ../ import
        m=re.search(r"^import '\.\./",s,re.M)
        if m: s=s[:m.start()]+imp+s[m.start():]
        else:
            last=max([m.end() for m in re.finditer(r"^import .*?;\n",s,re.M)],default=0)
            s=s[:last]+imp+s[last:]
    return s

def replace_target(s,controller):
    # Replace TextField/TextFormField whose first nearby named arg is this controller.
    pat=re.compile(r"(Text(?:Form)?Field\(\s*\n\s*controller:\s*"+re.escape(controller)+r",)")
    s,n=pat.subn(lambda m:m.group(1).replace('TextField(','ExpandableTextField(').replace('TextFormField(','ExpandableTextField('),s)
    return s,n

targets={
 'lib/screens/checklist_screen.dart':[
   '_fastDescription','description','risk','recommendation'
 ],
 'lib/screens/express_round_screen.dart':[
   'descriptionCtl','riskCtl','consequenceCtl','recommendationCtl','immediateCtl',
   'description','controller'
 ],
 'lib/screens/safety_observations_screen.dart':[
   'description','risk','consequence','immediateAction','recommendation','notes'
 ],
 'lib/screens/sst_record_form_screen.dart':[
   'descriptionController','participantsController','notesController','risksController',
   'controlsController','causesController','measuresController'
 ],
 'lib/screens/signature_screen.dart':[
   'generalNotesController','conclusionController'
 ],
}

total=0
for rel,controllers in targets.items():
    p,s=load(rel); s=add_import(s)
    changed=0
    for c in controllers:
        s,n=replace_target(s,c); changed+=n
    if changed:
        save(p,s); total+=changed
    else:
        # signature controller names vary; do not fail optional screen.
        if rel!='lib/screens/signature_screen.dart':
            raise RuntimeError(f'no expandable fields patched in {rel}')

# Some multiline fields are constructed inline in SST records; explicit replacements.
p,s=load('lib/screens/sst_record_form_screen.dart')
inline=[
("TextFormField(controller: descriptionController, maxLines: 3,", "ExpandableTextField(controller: descriptionController, maxLines: 3,"),
("TextFormField(controller: participantsController, maxLines: 3,", "ExpandableTextField(controller: participantsController, maxLines: 3,"),
("TextFormField(controller: notesController, maxLines: 5,", "ExpandableTextField(controller: notesController, maxLines: 5,"),
("TextFormField(controller: risksController, maxLines: 4,", "ExpandableTextField(controller: risksController, maxLines: 4,"),
("TextFormField(controller: controlsController, maxLines: 4,", "ExpandableTextField(controller: controlsController, maxLines: 4,"),
("TextFormField(controller: descriptionController, maxLines: 4,", "ExpandableTextField(controller: descriptionController, maxLines: 4,"),
("TextFormField(controller: causesController, maxLines: 3,", "ExpandableTextField(controller: causesController, maxLines: 3,"),
("TextFormField(controller: measuresController, maxLines: 3,", "ExpandableTextField(controller: measuresController, maxLines: 3,"),
("TextFormField(controller: notesController, maxLines: 3,", "ExpandableTextField(controller: notesController, maxLines: 3,"),
]
for a,b in inline:
    if a in s: s=s.replace(a,b)
save(p,s)

# General inspection closing notes and conclusion: match by labels because controller names may differ.
p,s=load('lib/screens/signature_screen.dart');s=add_import(s)
for label in ['Observações gerais da vistoria','Conclusão do relatório']:
    # nearest preceding TextField in a compact block.
    idx=s.find("labelText: '"+label+"'")
    if idx>=0:
        st=max(s.rfind('TextField(',0,idx),s.rfind('TextFormField(',0,idx))
        if st>=0 and idx-st<500:
            if s.startswith('TextField(',st):
                s=s[:st]+'ExpandableTextField('+s[st+len('TextField('):]
            elif s.startswith('TextFormField(',st):
                s=s[:st]+'ExpandableTextField('+s[st+len('TextFormField('):]
save(p,s)

# Bump after report-model patch has produced .112/.36.
pub=root/'pubspec.yaml'; ps=pub.read_text(encoding='utf-8')
old,new={'android':('3.29.112+254','3.29.113+255'),'windows':('3.30.36+223','3.30.37+224')}[platform]
if f'version: {old}' not in ps: raise RuntimeError('version mismatch '+old)
ps=ps.replace(f'version: {old}',f'version: {new}',1);save(pub,ps)

# Safety assertions.
assert (root/'lib/widgets/expandable_text_field.dart').is_file()
for rel in ['lib/screens/checklist_screen.dart','lib/screens/express_round_screen.dart','lib/screens/safety_observations_screen.dart','lib/screens/sst_record_form_screen.dart']:
    body=(root/rel).read_text(encoding='utf-8')
    assert "import '../widgets/expandable_text_field.dart';" in body
    assert 'ExpandableTextField(' in body
assert f'version: {new}' in ps
print('ALL_INSPECTIONS_EXPANDABLE_TEXT_OK',platform,new,total)

#!/usr/bin/env python3
"""Add full-screen text editing to every multi-line field in inspection workflows."""
from pathlib import Path
import re,shutil,sys
root=Path(sys.argv[1])
assert sys.argv[2] in ('android','windows')
widget=root/'lib/widgets/expand_text_button.dart'
widget.parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(Path(__file__).with_name('expand_text_button_v329113.dart'),widget)
paths=(
 'screens/checklist_screen.dart',
 'screens/express_round_screen.dart',
 'screens/sst_record_form_screen.dart',
 'screens/safety_observations_screen.dart',
 'screens/improvements_screen.dart',
)

def closing_paren(s,start):
 depth=0; i=start; quote=None; triple=False; line=False; block=False; escaped=False
 while i<len(s):
  ch=s[i]; ahead=s[i:i+3]
  if line:
   if ch=='\n':line=False
  elif block:
   if s[i:i+2]=='*/':block=False;i+=1
  elif quote:
   if escaped:escaped=False
   elif ch=='\\':escaped=True
   elif triple and ahead==quote*3:quote=None;triple=False;i+=2
   elif not triple and ch==quote:quote=None
  elif s[i:i+2]=='//':line=True;i+=1
  elif s[i:i+2]=='/*':block=True;i+=1
  elif ch in "'\"":
   quote=ch;triple=ahead==ch*3
   if triple:i+=2
  elif ch=='(':depth+=1
  elif ch==')':
   depth-=1
   if depth==0:return i
  i+=1
 raise RuntimeError('Unbalanced text field')
for rel in paths:
 p=root/'lib'/rel;s=p.read_text(encoding='utf-8'); changes=[]
 for m in re.finditer(r'\b(?:TextField|TextFormField)\s*\(',s):
  lo=m.end()-1;hi=closing_paren(s,lo);block=s[lo:hi+1]
  if not re.search(r'\bmaxLines:\s*(?:[2-9]|1[0-9]|maxLines)\b',block):continue
  c=re.search(r'\bcontroller:\s*([A-Za-z_][A-Za-z_0-9]*(?:\[[^\]]+\])?)',block)
  d=re.search(r'\bdecoration:\s*(?:const\s+)?InputDecoration\s*\(',block)
  if not c or not d or 'suffixIcon:' in block or 'ExpandTextButton' in block:continue
  start=lo+d.start()+len('decoration:')
  end=lo+d.end()
  changes.append((start,end,' InputDecoration(suffixIcon: ExpandTextButton(controller: '+c.group(1)+'),'))
 for start,end,txt in reversed(changes):s=s[:start]+txt+s[end:]
 if not changes:raise RuntimeError('No multi-line fields found in '+rel)
 marker="import '../brand.dart';" if "import '../brand.dart';" in s else "import '../database.dart';"
 if marker not in s:raise RuntimeError('Missing import point '+rel)
 s=s.replace(marker,marker+"\nimport '../widgets/expand_text_button.dart';",1)
 p.write_text(s,encoding='utf-8',newline='\n')
 print('EXPANDABLE_INSPECTION_TEXT_FIELDS',rel,len(changes))
assert widget.exists()

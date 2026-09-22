#!/usr/bin/env python3
from pathlib import Path
import re, sys, unicodedata, collections

root=Path(sys.argv[1])
ready=(root/'lib/ready_checklists.dart').read_text(encoding='utf-8')
screen=(root/'lib/screens/new_inspection_screen.dart').read_text(encoding='utf-8')
pub=(root/'pubspec.yaml').read_text(encoding='utf-8')

def norm(x):
    x=unicodedata.normalize('NFKD',x).encode('ascii','ignore').decode().lower()
    x=re.sub(r'[^a-z0-9 ]+',' ',x)
    return re.sub(r'\s+',' ',x).strip()

# Parser dos modelos.
starts=[m.start() for m in re.finditer(r'\bReadyChecklistDefinition\s*\(',ready)]
defs=[]
for st in starts:
    op=ready.find('(',st); d=0;q=None;esc=False;end=None
    for i in range(op,len(ready)):
        ch=ready[i]
        if q:
            if esc:esc=False
            elif ch=='\\':esc=True
            elif ch==q:q=None
            continue
        if ch in "'\"":q=ch
        elif ch=='(':d+=1
        elif ch==')':
            d-=1
            if d==0:end=i+1;break
    if not end:continue
    b=ready[st:end]
    def f(t,k):
        m=re.search(r"\b"+re.escape(k)+r"\s*:\s*(['\"])(.*?)\1",t,re.S)
        return m.group(2).strip() if m else ''
    ident=f(b,'id'); name=f(b,'name'); cat=f(b,'category')
    items=[]
    for im in re.finditer(r"ReadyChecklistItem\s*\((.*?)\)(?=\s*,|\s*\])",b,re.S):
        txt=f(im.group(1),'text')
        if txt:items.append(txt)
    if ident: defs.append((ident,name,cat,items))

assert len(defs) >= 240, f'biblioteca encolheu: {len(defs)}'
assert sum(len(x[3]) for x in defs) >= 2100, 'itens da biblioteca foram perdidos'

# Nenhuma duplicata exata dentro do mesmo checklist.
for ident,name,cat,items in defs:
    g=collections.Counter(norm(x) for x in items)
    dup=[k for k,v in g.items() if v>1]
    assert not dup, f'{ident}: pergunta repetida dentro do mesmo checklist'

byid={d[0]:d for d in defs}
generic='Máquinas e equipamentos existentes apresentam proteções, comandos e condições seguras de operação?'
for tid in [
    'ready-apoio-administrativo',
    'ready-saude-clinica',
    'ready-logistica-almoxarifado',
    'ready-logistica-recebimento',
    'ready-logistica-expedicao',
    'ready-telecom-sala-tecnica',
    'ready-ceramica-expedicao',
    'ready-ceramica-patio-barreiro',
]:
    assert tid in byid, tid+' ausente'
    assert generic not in byid[tid][3], tid+' ainda contém pergunta genérica fora de contexto'

# Panificação específica deve excluir os dois gerais na combinação.
for marker in [
    "ready-panificacao-amassadeira",
    "ready-panificacao-cilindro",
    "ready-panificacao-modeladora",
    "ready-panificacao-fatiadora",
    "ready-panificacao-batedeira",
    "ready-panificacao-laminadora",
    "ready-panificacao-moinho-farinha-rosca",
    "return templateId == 'ready-panificacao-nr12-geral'",
    "templateId == 'ready-panificacao-vistoria-maquinas'",
]:
    assert marker in screen, 'regra Panificação ausente: '+marker

assert 'Dica de campo: quando um requisito realmente não existir' in screen
assert re.search(r'^version:\s*3\.(29\.85|30\.13)\+',pub,re.M), 'versão checklist não aplicada'
print('CHECKLIST_REVIEW_REGRESSION_OK',len(defs),sum(len(x[3]) for x in defs))

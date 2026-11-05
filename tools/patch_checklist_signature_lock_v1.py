#!/usr/bin/env python3
"""Bloqueia apenas a tela de desenho embutida da assinatura do checklist.

A assinatura ampliada continua habilitada após tocar em "Assinar em tela
cheia". Não altera a assinatura capturada, arquivos, banco, sync ou PDF.
"""
from pathlib import Path
import hashlib
import sys

if len(sys.argv) != 2:
    raise SystemExit("Uso: patch_checklist_signature_lock_v1.py <APP_DIR>")
root=Path(sys.argv[1])
target=root/"lib/screens/signature_screen.dart"
assert target.is_file(), "Tela de assinatura de checklist não encontrada"
protected=[
    "lib/database.dart",
    "lib/models.dart",
    "lib/screens/checklist_screen.dart",
    "lib/screens/new_inspection_screen.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/auth_service.dart",
    "lib/services/media_sync_service.dart",
    "lib/widgets/large_signature_capture.dart",
    "painel_web_google_apps_script/Code.gs",
]
before={
    rel:hashlib.sha256((root/rel).read_bytes()).hexdigest()
    for rel in protected if (root/rel).is_file()
}
code=target.read_text(encoding="utf-8")
start_marker="  Widget _signatureCard({"
start=code.find(start_marker)
assert start>=0, "Cartão da assinatura não encontrado"
sig=code.find("Signature(",start)
assert sig>=0 and sig-start < 10000, "Assinatura embutida não localizada"
# Delimite da declaração: não modificar uma eventual tela ampliada.
next_method=code.find("\n  Widget ",start+len(start_marker))
next_class=code.find("\nclass ",start+len(start_marker))
limit=min([x for x in (next_method,next_class) if x>=0],default=len(code))
assert sig<limit, "Assinatura está fora do cartão"
segment=code[start:limit]
assert segment.count("Signature(")==1, "Cartão inesperado; nenhuma alteração"

# O IgnorePointer inibe completamente eventos de toque no canvas embutido.
# O filho Signature continua mostrando a assinatura que já foi desenhada
# na tela dedicada, mas nunca mais captura gestos de rolagem nesta página.
anchor="Signature("
call_start=segment.index(anchor)
depth=1
q=call_start+len(anchor)
quote=None
while q<len(segment) and depth:
    char=segment[q]
    if quote:
        if char=="\\":
            q+=2
            continue
        if char==quote:
            quote=None
    elif char in ("'",'"'):
        quote=char
    elif char=="(":
        depth+=1
    elif char==")":
        depth-=1
    q+=1
assert depth==0,"Não foi possível delimitar o canvas"
original=segment[call_start:q]
assert "IgnorePointer" not in segment[max(0,call_start-75):call_start], (
    "Canvas já protegido ou estrutura mudou")
segment=segment[:call_start]+(
    "IgnorePointer(\n"
    "                  ignoring: true,\n"
    "                  child: "+original+",\n"
    "                )"
)+segment[q:]
code=code[:start]+segment+code[limit:]

# A opção ativa do usuário é a página dedicada; o cartão continua visível
# e não libera nenhum risco acidental antes desse gesto explícito.
assert "ASSINAR EM TELA CHEIA" in code or "Assinar em tela cheia" in code
target.write_text(code,encoding="utf-8",newline="\n")
for rel,sha in before.items():
    assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==sha,rel
print("CHECKLIST_SIGNATURE_LOCK_OK: inline inativo; tela cheia preservada")

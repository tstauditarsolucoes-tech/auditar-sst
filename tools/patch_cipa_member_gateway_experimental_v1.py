#!/usr/bin/env python3
"""Instalador EXPERIMENTAL para uma CÓPIA da Central Online.

Não execute sobre a Central implantada sem backup, autorização específica,
comparação do Code.gs real e plano de rollback. A funcionalidade permanece
desabilitada pelo script property CIPA_MEMBER_V1_ENABLED (padrão ausente).
Não modifica MultiUser.gs nem qualquer rota atual de sincronização.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv)!=3 or sys.argv[2]!="--homologacao":
    raise SystemExit(
        "Uso: patch_cipa_member_gateway_experimental_v1.py APP_DIR --homologacao")
root=Path(sys.argv[1])
repo=Path(__file__).resolve().parents[1]
backend=root/"painel_web_google_apps_script"
code=backend/"Code.gs"
policy=backend/"CipaMemberServerPolicy.gs"
gateway=backend/"CipaMemberGatewayV1.gs"
assert code.is_file() and (backend/"MultiUser.gs").is_file(), (
    "Fonte da Central com autenticação não encontrada")
assert not policy.exists() and not gateway.exists(), (
    "Não sobrescrever módulos do portal individual já existentes")
allowed={code,policy,gateway}
protected={
    p:hashlib.sha256(p.read_bytes()).hexdigest()
    for folder in [root/"lib",backend]
    if folder.is_dir()
    for p in folder.rglob("*")
    if p.is_file() and p not in allowed
}
s=code.read_text(encoding="utf-8")
old="    const request = JSON.parse((e.postData && e.postData.contents) || '{}');"
new=old+"""
    // Homologação somente: não expor chave de sincronização ao membro.
    // Se CIPA_MEMBER_V1_ENABLED não for true, bloquear sem exceção.
    const cipaMemberResponse = cipaMemV1Route_(request);
    if (cipaMemberResponse !== null) {
      return jsonResponse_(cipaMemberResponse);
    }
"""
if s.count(old)!=1 or "cipaMemV1Route_(request)" in s:
    raise SystemExit("Code.gs diferente da origem esperada; não sobrescrever.")
code.write_text(s.replace(old,new,1),encoding="utf-8",newline="\n")
shutil.copyfile(repo/"feature_sources/cipa_member_server_policy_v1.js",policy)
shutil.copyfile(repo/"feature_sources/CipaMemberGatewayV1.gs",gateway)
assert all(hashlib.sha256(p.read_bytes()).hexdigest()==digest
    for p,digest in protected.items()),"Arquivo existente protegido mudou"
assert code.read_text().count("cipaMemV1Route_(request)")==1
assert "CIPA_MEMBER_V1_ENABLED" in gateway.read_text()
print("CIPA_MEMBER_GATEWAY_EXPERIMENTAL_READY_DEFAULT_OFF")

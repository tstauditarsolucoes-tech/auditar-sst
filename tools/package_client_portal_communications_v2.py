#!/usr/bin/env python3
"""Candidate-only portal bundle; NEVER deploy or replace production GS automatically."""
from pathlib import Path
import hashlib
import subprocess
import sys
import zipfile

source = Path(sys.argv[1])
dest = Path(sys.argv[2])
repo = Path(__file__).resolve().parents[1]
base_commit = "f040c839f589411e49b724dc687682b2cb80e7f2"

def previous(path):
    return subprocess.check_output(
        ["git", "show", base_commit + ":" + path], cwd=repo).decode("utf-8")

def one(value, needle, replacement, label):
    found = value.count(needle)
    if found != 1:
        raise RuntimeError(f"{label}: expected one anchor; got {found}")
    return value.replace(needle, replacement, 1)

src = source / "Central-Painel-Cliente"
if not src.is_dir():
    raise RuntimeError("Previous audited client-portal artifact not found")
base_html = (src / "ClientPortal.html").read_text(encoding="utf-8")
old_js = previous("feature_sources/client_treatment_portal_ui_v1.js")
old_css = previous("feature_sources/client_treatment_portal_ui_v1.css")
new_js = (repo / "feature_sources/client_treatment_portal_ui_v1.js").read_text(encoding="utf-8")
new_css = (repo / "feature_sources/client_treatment_portal_ui_v1.css").read_text(encoding="utf-8")
html = one(base_html, old_js, new_js, "ClientPortal original JS")
html = one(html, old_css, new_css, "ClientPortal original CSS")
html = one(html, "res.companies.forEach(renderCompany);",
           "res.companies.forEach(renderCompany);\n  renderTreatmentInboxV2();",
           "Inbox mounting")
client_gs = (src / "ClientPortal.gs.txt").read_text(encoding="utf-8")
code_gs = (src / "Code.gs.txt").read_text(encoding="utf-8")
multi_gs = (src / "MultiUser.gs.txt").read_text(encoding="utf-8")
mod = (repo / "feature_sources/ClientPortalTreatments_v1.gs").read_text(encoding="utf-8")

for token in ("'tratativas'", "clientPortalPermissions_"):
    if token not in client_gs:
        raise RuntimeError("Existing portal permission wiring missing: " + token)
for token in ("function clientPortalTreatmentPost", "clientTreatmentPublishedTopicsV2_",
              "pedido_apoio", "informar_correcao"):
    if token not in mod:
        raise RuntimeError("Candidate backend incomplete: " + token)
for token in ("Solicitar apoio técnico", "Pendências resolvidas publicadas",
              "renderTreatmentInboxV2();", "clientPortalTreatmentTopics"):
    if token not in html:
        raise RuntimeError("Candidate portal incomplete: " + token)
for token in ("client_treatment_v2",):
    if token not in code_gs:
        raise RuntimeError("Reference Code.gs route missing: " + token)

dest.mkdir(parents=True, exist_ok=True)
files = {
    "ClientPortal.html": html,
    "ClientPortalTreatments.gs.txt": mod,
    "ClientPortal.gs.txt": client_gs,
    "REFERENCIA-NAO-SUBSTITUIR/Code.gs.txt": code_gs,
    "REFERENCIA-NAO-SUBSTITUIR/MultiUser.gs.txt": multi_gs,
}
for name, data in files.items():
    f = dest / name
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(data, encoding="utf-8", newline="\n")

steps = """AUDITAR SST — PAINEL DO CLIENTE / CANDIDATO DE HOMOLOGACAO V2

OBJETIVO
- Mostrar comunicacao e linha do tempo para pendencias abertas e resolvidas PUBLICADAS.
- Permitir solicitar apoio com protocolo e resposta na caixa de entrada Auditar.
- Permitir ao cliente INFORMAR correcoes sem fechar NC ou validar eficacia automaticamente.
- Manter mensagens, autores e historico por empresa e ocorrencia.

ATENCAO
- ESTES ARQUIVOS NAO FORAM INSTALADOS NO APPS SCRIPT DE PRODUCAO.
- Nao executar setupAuditar() em producao.
- Nao substituir Code.gs/MultiUser.gs sem comparar versoes ativas.
- Antes de instalar: backup de TODOS os GS e HTML da Central instalada.
- Em ClientPortal.gs, autorizar explicitamente a permissao 'tratativas' da conta cliente.
- A rota client_treatment_v2 no Code.gs precisa estar ativa e homologada para o aplicativo receber.
- Testar uma empresa cliente e uma conta Auditar em ambiente de homologacao.
- Para empresas com restricao naoConformidades=false, as ocorrencias continuam restritas.
- Conversas e registros historicos nao devem ser apagados.
- Linha do tempo de NC resolvida depende da sua presenca no snapshot PUBLICADO da empresa.
- Indicadores do snapshot nao mudam automaticamente quando o cliente informa correcao.

ARQUIVOS
ClientPortal.html — interface do cliente com comunicacao e apoio.
ClientPortalTreatments.gs.txt — backend aditivo de mensagens e tratativas.
ClientPortal.gs.txt — referencia de permissoes da mesma base; comparar.
REFERENCIA-NAO-SUBSTITUIR — so para conferencia da integracao.

PROVA MINIMA DE HOMOLOGACAO
1) Abrir cliente com 'tratativas' habilitado e conferir conversa GERAL.
2) Clicar Solicitar apoio, escrever pedido e conferir protocolo de envio.
3) Conferir pedido na Caixa de entrada Auditar, responder e validar retorno.
4) Informar uma correcao numa NC e conferir que NC nao foi encerrada.
5) Consultar NC resolvida publicada e seu historico completo.
6) Verificar isolamento: outro cliente NAO deve acessar a empresa nem mensagens.
7) Verificar ausencia de efeitos em login, fotos, sincronizacao, relatorios e dados.
"""
(dest / "LEIA-ANTES-DE-INSTALAR.txt").write_text(steps, encoding="utf-8")
manifest = "\n".join(
    hashlib.sha256(p.read_bytes()).hexdigest() + "  " + p.relative_to(dest).as_posix()
    for p in sorted(dest.rglob("*")) if p.is_file()) + "\n"
(dest / "SHA256.txt").write_text(manifest, encoding="utf-8")
script = html.split("<script>", 1)[1].split("</script>", 1)[0]
subprocess.run(["node", "--check", "-"], input=script, text=True, check=True)
subprocess.run(["node", "--check", "-"], input=mod, text=True, check=True)
bundle = dest.parent / "AUDITAR-SST-PAINEL-CLIENTE-COMUNICACAO-V2-CANDIDATO.zip"
with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED, compresslevel=8) as archive:
    for path in sorted(dest.rglob("*")):
        if path.is_file():
            archive.write(path, path.relative_to(dest).as_posix())
print("PANEL_V2_BUNDLE_READY", bundle, "FILES", len(files), "NO_DEPLOY")

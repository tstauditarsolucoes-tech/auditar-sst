#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) < 2:
    raise SystemExit("uso: patch_checklist_ai_stable_v32992_v33019.py <APP_DIR> [android|windows]")

root=Path(sys.argv[1])
platform=(sys.argv[2] if len(sys.argv)>2 else "android").lower()

def read(rel):
    return (root/rel).read_text(encoding="utf-8")

def write(rel,text):
    (root/rel).write_text(text,encoding="utf-8",newline="\n")

def replace_method(text, signature, replacement):
    start=text.find(signature)
    if start<0:
        raise RuntimeError("metodo nao localizado: "+signature)
    brace=text.find("{",start)
    if brace<0:
        raise RuntimeError("abertura nao localizada: "+signature)
    depth=0; quote=None; esc=False; line=False; block=False; i=brace
    while i<len(text):
        ch=text[i]; nxt=text[i+1] if i+1<len(text) else ""
        if line:
            if ch=="\n": line=False
            i+=1; continue
        if block:
            if ch=="*" and nxt=="/": block=False; i+=2; continue
            i+=1; continue
        if quote:
            if esc: esc=False
            elif ch=="\\": esc=True
            elif ch==quote: quote=None
            i+=1; continue
        if ch=="/" and nxt=="/": line=True; i+=2; continue
        if ch=="/" and nxt=="*": block=True; i+=2; continue
        if ch in ("'", '"'): quote=ch; i+=1; continue
        if ch=="{": depth+=1
        elif ch=="}":
            depth-=1
            if depth==0:
                return text[:start]+replacement.rstrip()+text[i+1:]
        i+=1
    raise RuntimeError("fim nao localizado: "+signature)

# ------------------------------------------------------------
# IA: usa o mesmo transporte robusto/compactacao que ja funciona na Ronda.
# ------------------------------------------------------------
rel="lib/services/ai_assistant_service.dart"
ai=read(rel)
sig="  static Future<AiAssistantReply> analyzeChecklistPhotos({"
start=ai.find(sig)
end=ai.find("  static Future<AiAssistantReply> analyzeSafetyObservationPhoto({",start)
if start<0 or end<0:
    raise RuntimeError("analyzeChecklistPhotos nao localizado")
method=ai[start:end]

if "_prepareRoundPhotoForAi(originalBytes)" not in method:
    if "_prepareImage(originalBytes)" not in method:
        raise RuntimeError("preparo antigo da foto do checklist nao localizado")
    method=method.replace("_prepareImage(originalBytes)","_prepareRoundPhotoForAi(originalBytes)",1)

if "'rondaDeferred': true," not in method:
    old="""        'mode': 'checklist_photo',
        'companyName': companyName,
"""
    new="""        'mode': 'checklist_photo',
        // Reaproveita a rota robusta de foto da Ronda: payload compacto,
        // janela de 95 s e fallback de modelo no backend. O prompt continua
        // sendo o do Checklist; somente o transporte/fallback e compartilhado.
        'rondaDeferred': true,
        'companyName': companyName,
"""
    if old not in method:
        raise RuntimeError("payload do checklist nao localizado")
    method=method.replace(old,new,1)

ai=ai[:start]+method+ai[end:]
write(rel,ai)

# ------------------------------------------------------------
# Fila: uma chamada robusta por item. Evita 2/3 POSTs longos duplicados.
# ------------------------------------------------------------
rel="lib/services/inspection_photo_ai_queue_service.dart"
q=read(rel)
new_retry=r'''  static Future<AiAssistantReply> _analyzeWithRetry({
    required Inspection inspection,
    required String companyName,
    required ChecklistItem item,
    required List<String> photoPaths,
    required String technicianContext,
  }) async {
    // analyzeChecklistPhotos ja usa a mesma rota robusta da Ronda (95 s +
    // fallback de modelo). Nao repetimos automaticamente um POST longo porque
    // o Apps Script pode ainda estar finalizando a primeira solicitacao.
    // Se nao concluir, a evidencia fica salva para o tecnico tentar novamente.
    return AiAssistantService.analyzeChecklistPhotos(
      inspection: inspection,
      companyName: companyName,
      item: item,
      photoPaths: photoPaths,
      technicianContext: technicianContext,
    );
  }'''
q=replace_method(q,"  static Future<AiAssistantReply> _analyzeWithRetry({",new_retry)
write(rel,q)

# ------------------------------------------------------------
# Checklist: o auto-save nao pode rebaixar ANALISANDO/ERRO para PENDENTE.
# ------------------------------------------------------------
rel="lib/screens/checklist_screen.dart"
c=read(rel)
old="""    if (eligibleForLaterAi &&
        !const ['PRONTA_REVISAO', 'APLICADA', 'DESCARTADA']
            .contains(aiStatus)) {
      currentAi['status'] = 'PENDENTE';
      currentAi.putIfAbsent(
        'queuedAt',
        () => DateTime.now().toUtc().toIso8601String(),
      );
    }
"""
new="""    if (eligibleForLaterAi && aiStatus.isEmpty) {
      currentAi['status'] = 'PENDENTE';
      currentAi.putIfAbsent(
        'queuedAt',
        () => DateTime.now().toUtc().toIso8601String(),
      );
    }
"""
if old not in c:
    raise RuntimeError("normalizacao PENDENTE do auto-save nao localizada")
c=c.replace(old,new,1)

c=c.replace(
"""                '${summary.failed} foto(s) ficaram pendentes por instabilidade da Central. Você pode tentar novamente no final da vistoria.',
""",
"""                '${summary.failed} análise(s) não concluíram nesta tentativa. As fotos continuam salvas; tente novamente no final da vistoria.',
""",
1,
)
c=c.replace(
"""              'A análise ficou pendente. A foto continua salva e pode ser processada no final da vistoria.',
""",
"""              'A análise não concluiu nesta tentativa. A foto continua salva e pode ser analisada novamente no final da vistoria.',
""",
1,
)
write(rel,c)

# Versao
rel="pubspec.yaml"
pub=read(rel)
version="3.30.19+206" if platform=="windows" else "3.29.92+234"
pub,count=re.subn(r"(?m)^version:\s*[^\r\n]+","version: "+version,pub,count=1)
if count!=1:
    raise RuntimeError("versao nao localizada")
write(rel,pub)

# Verificacoes
ai=read("lib/services/ai_assistant_service.dart")
q=read("lib/services/inspection_photo_ai_queue_service.dart")
c=read("lib/screens/checklist_screen.dart")
check_method=ai[ai.find(sig):ai.find("  static Future<AiAssistantReply> analyzeSafetyObservationPhoto({",ai.find(sig))]
assert "_prepareRoundPhotoForAi(originalBytes)" in check_method
assert "'rondaDeferred': true" in check_method
assert "_prepareImage(originalBytes)" not in check_method
retry=q[q.find("  static Future<AiAssistantReply> _analyzeWithRetry({"):q.find("  static String _photoFingerprint",q.find("  static Future<AiAssistantReply> _analyzeWithRetry({"))]
assert "for (var attempt" not in retry
assert "return AiAssistantService.analyzeChecklistPhotos(" in retry
assert "eligibleForLaterAi && aiStatus.isEmpty" in c
assert "instabilidade da Central" not in c
assert "As fotos continuam salvas" in c
assert f"version: {version}" in read("pubspec.yaml")
print("CHECKLIST_AI_STABLE_OK",platform,version)

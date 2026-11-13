#!/usr/bin/env python3
"""Testar compatibilidade de patch seletivo de timeout com duas versões da IA.

Não modifica projetos reais; simula respostas do transporte refatorado e
original. Exige falha segura para estruturas não reconhecidas e protege sync.
"""
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile

repo=Path(__file__).resolve().parents[1]
script=repo/"tools/patch_checklist_builder_reliability_v329200_v330128.py"

old_reply="""          return const AiAssistantReply(
            success: false,
            message:
                'A análise da foto demorou além do limite da IA. O registro continua salvo; tente novamente em alguns instantes.',
          );"""

protected=[
    "lib/database.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/auth_service.dart",
    "lib/services/drive_service.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
    "painel_web_google_apps_script/ClientPortal.html",
    "painel_web_google_apps_script/ReportEmail.gs",
]

timeout="""    final requestTimeout =
        rondaDeferred
            ? const Duration(seconds: 90)
            : aiMode == 'checklist_photo' ||
                aiMode == 'safety_observation_photo'
                ? const Duration(seconds: 50)
                : aiMode == 'report_review_chat'
                    ? const Duration(seconds: 75)
                    : const Duration(seconds: 65);"""

screen="""class ChecklistTemplatesScreen {
  Future<void> _createChecklistWithAi() async {
    setState(() => generatingWithAi = true);
    final reply = await AiAssistantService.createChecklist(request: request);
    if (!mounted) return;
    setState(() => generatingWithAi = false);
    if (reply.success) {
      insertChecklistTemplate(template);
    }
    const Text('Salvar checklist');
  }
  Future<void> _addTemplate() async {}
}
"""

for case in ("classic","transport"):
  with tempfile.TemporaryDirectory(prefix="auditar_timeout_") as temp:
    root=Path(temp)
    for name in protected:
      f=root/name
      f.parent.mkdir(parents=True,exist_ok=True)
      f.write_text("CORE_PROTEGIDO_"+name,encoding="utf-8")
    before={name:hashlib.sha256((root/name).read_bytes()).hexdigest()
      for name in protected}
    ai=root/"lib/services/ai_assistant_service.dart"
    ai.parent.mkdir(parents=True,exist_ok=True)
    body=(
      "  } on CentralTransportException catch (error) {\n"
      "    final message = error.message.toLowerCase();\n"
      "    if (message.contains('não respondeu a tempo') ||\n"
      "        message.contains('timeoutexception')) {\n"
      + (old_reply if case=="classic" else
        "      return const AiAssistantReply(success: false,\n"
        "        message: 'Falha no transporte, tente novamente.');")
      +"\n    }\n  }\n"
    )
    ai.write_text("class AiAssistantService {\n"
        "  static Future<AiAssistantReply> _send() async {\n"+
        timeout+"\n"+body+"  }\n}\n",encoding="utf-8")
    templates=root/"lib/screens/checklist_templates_screen.dart"
    templates.parent.mkdir(parents=True,exist_ok=True)
    templates.write_text(screen,encoding="utf-8")
    home=root/"lib/screens/home_screen.dart"
    home.write_text(
      "Auditar SST para Windows • versão 3.30.127",encoding="utf-8")
    (root/"pubspec.yaml").write_text(
      "version: 3.30.127+314\n",encoding="utf-8")
    for pass_id in (1,2):
      result=subprocess.run([sys.executable,str(script),str(root),"windows"],
          capture_output=True,text=True)
      assert result.returncode==0,(case,pass_id,result.stdout,result.stderr)
    final_ai=ai.read_text(encoding="utf-8")
    assert final_ai.count("A criação do checklist com IA demorou mais que o limite.")==1,case
    assert final_ai.count("aiMode == 'checklist_builder'")>=1,case
    assert "const Duration(seconds: 120)" in final_ai,case
    assert all(hashlib.sha256((root/k).read_bytes()).hexdigest()==v
        for k,v in before.items()),"Arquivo do núcleo protegido foi alterado"
    print("CHECKLIST_TIMEOUT_COMPAT_OK",case)

print("CHECKLIST_TIMEOUT_PATCH_FAIL_CLOSED_AND_IDEMPOTENT_OK")

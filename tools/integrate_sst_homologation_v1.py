#!/usr/bin/env python3
"""Integrador *fail closed* das melhorias SST já testadas em fixtures.

Não publica nem modifica servidores/GS, não instala aplicativos nos usuários,
não cria novas bases, não acessa segredos e não altera componentes protegidos.
Somente para cópias temporárias do projeto, na montagem CI de homologação.
"""
from pathlib import Path
import hashlib
import subprocess
import sys

if len(sys.argv)!=3 or sys.argv[2] not in {"android","windows"}:
    raise SystemExit("Uso: integrate_sst_homologation_v1.py APP_DIR android|windows")
root=Path(sys.argv[1]).resolve()
platform=sys.argv[2]
repo=Path(__file__).resolve().parents[1]
required=[
    "lib/database.dart","lib/models.dart",
    "lib/services/auth_service.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/sync_coordinator.dart",
    "lib/screens/quick_visit_screen.dart",
    "lib/screens/express_round_screen.dart",
    "lib/screens/new_inspection_screen.dart",
    "lib/screens/cipa_management_screen.dart",
    "lib/screens/manager_reports_screen.dart",
    "lib/screens/company_detail_screen.dart",
    "lib/services/offline_sst_deep_catalog_v2.dart",
    "painel_web_google_apps_script/Code.gs",
]
assert all((root/p).is_file() for p in required), (
    "App original incompleto: scripts de homologação bloqueados.")
protected=[
    "lib/database.dart","lib/models.dart",
    "lib/services/auth_service.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/drive_service.dart",
    "lib/services/ai_assistant_service.dart",
    "lib/screens/express_round_screen.dart",
    "lib/screens/new_inspection_screen.dart",
    "lib/screens/report_screen.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
]
# A versão do formulário/IA de ronda pode receber ajustes somente pelo patch
# específico de conclusão. Ele preserva o registro e o envio.
if platform=="android":
    protected.remove("lib/screens/express_round_screen.dart")
before={p:hashlib.sha256((root/p).read_bytes()).hexdigest()
        for p in protected if (root/p).is_file()}

steps=(
    ["tools/patch_android_unified_visits_v1.py",
     "tools/patch_android_standard_conclusion_v1.py",
     "tools/patch_checklist_signature_lock_v1.py"]
    if platform=="android" else
    ["tools/patch_windows_smart_visit_v1.py"]
)
steps += [
    "tools/patch_nr12_bakery_library_v1.py",
    "tools/patch_all_nrs_library_v1.py",
    "tools/patch_nrs_browser_entry_v1.py",
    "tools/patch_sst_report_center_v1.py",
    "tools/patch_cipa_triage_v1.py",
    "tools/patch_cipa_guided_home_v1.py",
    "tools/patch_cipa_meeting_coach_v1.py",
    "tools/patch_cipa_member_label_v1.py",
    "tools/patch_cipa_member_admin_ui_v1.py",
]
for script in steps:
    print("HOMOLOGACAO_APLICAR",script,flush=True)
    completed=subprocess.run(
        [sys.executable,str(repo/script),str(root)],
        cwd=repo,check=False)
    if completed.returncode:
        raise SystemExit("INTEGRAÇÃO BLOQUEADA: "+script+
                         " retornou "+str(completed.returncode)+
                         "; não gerar nem distribuir instaladores.")
    for p,hash_ in before.items():
        if hashlib.sha256((root/p).read_bytes()).hexdigest()!=hash_:
            raise SystemExit("INTEGRAÇÃO BLOQUEADA: arquivo protegido: "+p)

# O backend do portal individual CIPA NÃO é instalado/ativado nesta etapa;
# sua homologação tem fluxo separado, com sessão de membro e acesso restrito.
assert not (root/"painel_web_google_apps_script/CipaMemberGatewayV1.gs").exists(),(
    "Portal de membro não deve ser acoplado ao Apps Script operacional.")
assert (root/"lib/screens/smart_visit_briefing_screen.dart").is_file()
assert (root/"lib/screens/sst_report_center_screen.dart").is_file()
assert (root/"lib/services/offline_sst_all_nrs_v1.dart").is_file()
assert (root/"lib/screens/cipa_meeting_coach_home.dart").is_file()
print("HOMOLOGACAO_MONTAGEM_OK",platform.upper(),
      "modulos",len(steps),"núcleo protegido inalterado")

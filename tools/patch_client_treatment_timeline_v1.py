#!/usr/bin/env python3
"""Add-only timeline panel extension. No sync/auth/DB/media/IA or Code.gs mutation."""
from pathlib import Path
import hashlib,shutil,sys
root=Path(sys.argv[1])
repo=Path(__file__).resolve().parents[1]
gs=root/'painel_web_google_apps_script/ClientPortal.gs'
html=root/'painel_web_google_apps_script/ClientPortal.html'
assert gs.exists() and html.exists()
new=gs.parent/'ClientPortalTreatments.gs'
assert not new.exists(), 'Treatments module already exists'
protected=[
 'lib/database.dart','lib/models.dart',
 'lib/services/device_sync_service.dart','lib/services/sync_coordinator.dart',
 'lib/services/auth_service.dart','lib/services/media_sync_service.dart',
 'lib/services/drive_service.dart','lib/services/apps_script_http.dart',
 'lib/services/ai_assistant_service.dart',
 'painel_web_google_apps_script/Code.gs',
 'painel_web_google_apps_script/MultiUser.gs',
 'painel_web_google_apps_script/ReportEmail.gs',
 'painel_web_google_apps_script/Index.html',
]
before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in protected}
s=gs.read_text(encoding='utf-8')
def once(old,new,label):
 global s
 assert s.count(old)==1,(label,s.count(old))
 s=s.replace(old,new,1)
once("'relatorios', 'enviarEvidencia'\n];",
 "'relatorios', 'enviarEvidencia', 'tratativas'\n];",'permission key')
once('relatorios:true, enviarEvidencia:false};',
 'relatorios:true, enviarEvidencia:false, tratativas:true};','internal default')
gs.write_text(s,encoding='utf-8',newline='\n')
shutil.copyfile(repo/'feature_sources/ClientPortalTreatments_v1.gs',new)
h=html.read_text(encoding='utf-8')
assert h.count('</style>')==1 and h.count('</script>')==1
assert 'auditar-tratativas-v1' not in h
css=(repo/'feature_sources/client_treatment_portal_ui_v1.css').read_text(encoding='utf-8')
js=(repo/'feature_sources/client_treatment_portal_ui_v1.js').read_text(encoding='utf-8')
h=h.replace('</style>',css+'\n</style>',1)
a='function renderCompany(company){'
assert h.count(a)==1
h=h.replace(a,js+'\n'+a,1)
a=' shell.append(renderReportHighlights(company));'
assert h.count(a)==1
h=h.replace(a,a+"\n const treatmentHub=renderTreatmentHubV1(company);\n if(treatmentHub)shell.append(treatmentHub);",1)
# Client accounts explicitly opt in, including existing accounts. Staff allowed.
a='<label><input id="cp_enviarEvidencia"'
assert h.count(a)==1,'admin permissions form missing'
h=h.replace(a,'<label><input id="cp_tratativas" type="checkbox" checked style="width:auto"> Comunicação e tratativas por ocorrência</label>\n     '+a,1)
a="const CLIENT_PERMISSION_KEYS=['indicadores','naoConformidades','acoesCorretivas','relatorios','enviarEvidencia'];"
assert h.count(a)==1,'admin permission keys missing'
h=h.replace(a,"const CLIENT_PERMISSION_KEYS=['indicadores','naoConformidades','acoesCorretivas','relatorios','enviarEvidencia','tratativas'];",1)
a='relatorios:true,enviarEvidencia:false};'
assert h.count(a)==1,'admin default permissions missing'
h=h.replace(a,'relatorios:true,enviarEvidencia:false,tratativas:true};',1)
html.write_text(h,encoding='utf-8',newline='\n')
for path,digest in before.items():
 assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest,'Protected mutation: '+path
assert "tratativas" in gs.read_text(encoding='utf-8')
assert "clientPortalTreatmentPost" in new.read_text(encoding='utf-8')
assert "function renderTreatmentHubV1" in html.read_text(encoding='utf-8')
print('CLIENT_PORTAL_TIMELINE_READY: additive + company permissions; core unchanged')

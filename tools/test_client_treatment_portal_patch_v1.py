#!/usr/bin/env python3
"""Smoke check only the additive portal timeline; verify original routes remain."""
from pathlib import Path
import subprocess,sys,tempfile
root=Path(sys.argv[1]);panel=root/'painel_web_google_apps_script'
gs=(panel/'ClientPortal.gs').read_text(encoding='utf-8')
html=(panel/'ClientPortal.html').read_text(encoding='utf-8')
mod=(panel/'ClientPortalTreatments.gs').read_text(encoding='utf-8')
for needle in ['clientPortalLogin(', 'clientPortalData(', 'clientPortalSubmitEvidence(',
               'clientPortalAdminSaveClient(', 'function clientPortalPermissions_',
               'tratativas']:
 assert needle in gs,needle
for needle in ['function clientPortalTreatmentList(', 'function clientPortalTreatmentPost(',
 'userCanAccessCompany_', 'clientPortalFindSnapshot_', 'CLIENT_TREATMENT_SHEET_V1']:
 assert needle in mod,needle
for needle in ['id="login"', 'id="dashboard"', 'id="companies"', 'id="cp_tratativas"',
  'id="cp_enviarEvidencia"', 'function renderTreatmentHubV1','function treatmentTimelineV1',
  'function renderCompany(company)', 'function renderImprovementPlan(company)']:
 assert needle in html,needle
assert html.count('<script>')==1 and html.count('</script>')==1
assert "document.createElement('textarea')" in html
assert "clientPortalTreatmentPost" in html
# Syntax check for new Apps Script and existing inlined JS.
with tempfile.TemporaryDirectory() as temp:
 for name,contents in [
   ('ClientPortalTreatments.js',mod),
   ('ClientPortal.js',gs),
   ('PortalInline.js',html.split('<script>',1)[1].split('</script>',1)[0]),
 ]:
  file=Path(temp)/name
  file.write_text(contents,encoding='utf-8')
  subprocess.run(['node','--check',str(file)],check=True)
print('CLIENT_PORTAL_TREATMENTS_PATCH_V1_OK; portal login/admin/evidence preserved')

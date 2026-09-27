#!/usr/bin/env python3
"""Regression guards for the compact executive Client Portal.

Read-only portal additions only. Structured sync, media sync, DB and auth core stay outside this patch.
"""
from pathlib import Path
import re,sys
root=Path(sys.argv[1])
gs=(root/'painel_web_google_apps_script/ClientPortal.gs').read_text(encoding='utf-8')
html=(root/'painel_web_google_apps_script/ClientPortal.html').read_text(encoding='utf-8')
for marker in (
    'function clientPortalDeviceSstRecords_',
    'function clientPortalOperationalSummary_',
    "type==='DDS'",
    "type==='TREINAMENTO_SESSAO'",
    'result.ddsSummary = operational.dds',
    'result.trainingRecords = operational.trainingRecords',
    "current:safeTraining('current')",
    "expired:safeTraining('expired')",
    "pending:safeTraining('pending')",
):
    if marker not in gs:
        raise SystemExit('CLIENT_EXECUTIVE missing GS marker: '+marker)
for forbidden in (
    'setValue(', 'setValues(', 'appendRow(', 'deleteRow(',
    'PropertiesService.getScriptProperties().set',
):
    body=gs[gs.index('function clientPortalDeviceSstRecords_'):]
    if forbidden in body:
        raise SystemExit('CLIENT_EXECUTIVE read-only helper writes data: '+forbidden)
for marker in (
    'executive-compact-v329137',
    "function renderKanban(actions)",
    "function renderTrainingAndDds(company)",
    "Atualização automática",
    "setInterval(()=>",
    "},60000)",
    "document.addEventListener('visibilitychange'",
    "window.addEventListener('focus'",
    "Painel Gerencial de SST",
):
    if marker not in html:
        raise SystemExit('CLIENT_EXECUTIVE missing HTML marker: '+marker)
if html.count('id="companies"') != 1:
    raise SystemExit('CLIENT_EXECUTIVE companies root changed')
if 'innerHTML=' in html:
    raise SystemExit('CLIENT_EXECUTIVE unsafe innerHTML introduced')
print('CLIENT_PORTAL_EXECUTIVE_COMPACT_OK')
print('CLIENT_PORTAL_AUTO_REFRESH_KANBAN_TRAINING_DDS_OK')

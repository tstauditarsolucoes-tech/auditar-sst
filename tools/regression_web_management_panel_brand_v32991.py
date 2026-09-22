#!/usr/bin/env python3
from pathlib import Path
import sys

root=Path(sys.argv[1])
web=root/'painel_web_google_apps_script'
code=(web/'Code.gs').read_text(encoding='utf-8')
index=(web/'Index.html').read_text(encoding='utf-8')

for marker in [
    'function panelCompanyLogoDataUri_',
    'function panelLogoDataUriFromFile_',
    'publicPayload.company.logoDataUri',
    "setTitle(publicCompanyName + ' • Painel Gerencial SST')",
]:
    assert marker in code, marker

for marker in [
    'Painel Executivo Gerencial Web v3.29.91',
    'company-logo-shell',
    'Logo da empresa',
    'setupCompanyBranding(company)',
    'applyCompanyTheme(image)',
    'Identidade visual da empresa',
    "root.style.setProperty('--navy'",
    "root.style.setProperty('--navy-dark'",
]:
    assert marker in index, marker

for marker in [
    'Resumo executivo',
    'O que exige ação agora',
    'Desempenho por setor',
    'Treinamentos',
    'NCs e ações',
    'Atos e condições',
    'Melhorias',
    'Agenda SST',
    'Extintores',
    'Vistorias',
]:
    assert marker in index, 'recurso do painel perdido: '+marker

print('WEB_MANAGEMENT_PANEL_BRAND_REGRESSION_OK')

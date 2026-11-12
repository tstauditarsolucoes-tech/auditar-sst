#!/usr/bin/env python3
"""Windows: acesso à Visita Inteligente a partir da empresa na Visita Rápida.

Uso somente em compilação de homologação. As telas originais, banco,
sincronização, autenticação, fotos, PDFs e Apps Script permanecem inalterados.
Falhar com segurança se a navegação da versão atual estiver diferente.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv)!=2:
    raise SystemExit("Uso: patch_windows_smart_visit_v1.py <APP_DIR>")
root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
quick=root/"lib/screens/quick_visit_screen.dart"
screen=root/"lib/screens/smart_visit_briefing_screen.dart"
rules=root/"lib/services/visit_intelligence.dart"
assert quick.is_file() and not screen.exists() and not rules.exists(), (
    "Navegação Windows inesperada ou Visita Inteligente já instalada.")
protected=[
    "lib/database.dart","lib/models.dart",
    "lib/services/auth_service.dart","lib/services/device_sync_service.dart",
    "lib/services/sync_coordinator.dart","lib/services/media_sync_service.dart",
    "lib/screens/express_round_screen.dart",
    "lib/screens/new_inspection_screen.dart",
    "painel_web_google_apps_script/Code.gs",
]
checks={
    relative:hashlib.sha256((root/relative).read_bytes()).hexdigest()
    for relative in protected if (root/relative).is_file()
}
text=quick.read_text(encoding="utf-8")
start="import 'express_round_screen.dart';"
assert text.count(start)==1, "Import do módulo de rondas inesperado"
text=text.replace(start,start+"\nimport 'smart_visit_briefing_screen.dart';",1)
needle="""          _action(
            'Nova ronda',
            'Fotos e descrição das situações encontradas',
            Icons.add_a_photo_outlined,
            ExpressRoundScreen(company: c),
          ),"""
assert text.count(needle)==1, (
    "Seletor de empresa mudou: não sobrescrever atalhos existentes.")
addition="""          _action(
            'Preparar Visita Inteligente',
            'Conferir observações locais antes da vistoria.',
            Icons.route_outlined,
            SmartVisitBriefingScreen(company: c),
          ),
"""
text=text.replace(needle,addition+needle,1)
quick.write_text(text,encoding="utf-8",newline="\n")
shutil.copyfile(repo/"feature_sources/smart_visit_briefing_screen_v1.dart",screen)
shutil.copyfile(repo/"feature_sources/visit_intelligence_v1.dart",rules)
assert all(hashlib.sha256((root/k).read_bytes()).hexdigest()==v
    for k,v in checks.items()),"Núcleo alterado: compilação bloqueada"
assert text.count("SmartVisitBriefingScreen(company: c)")==1
print("WINDOWS_SMART_VISIT_SAFE: acesso local adicionado sem alterar o núcleo")

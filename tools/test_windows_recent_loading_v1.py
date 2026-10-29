#!/usr/bin/env python3
"""Static regression for Windows-only progressive screen loading."""
from pathlib import Path
import re
import sys

assert len(sys.argv) == 2
app = Path(sys.argv[1])
screen = app / "lib/screens"
center = (screen / "admin_center_screen.dart").read_text(encoding="utf-8")
hub = (screen / "admin_operational_hub_screen.dart").read_text(encoding="utf-8")
agenda = (screen / "technician_agenda_screen.dart").read_text(encoding="utf-8")

def require(markers, text, label):
    for marker in markers:
        if marker not in text:
            raise AssertionError(f"{label}: {marker!r} ausente")

require([
    "Future.wait<void>", "AuthService.listUsers()",
    "AppDatabase.instance.getCompanies(", "AuditarAdminAccess.isAdmin",
    "Contas indisponíveis na Central Online",
    "const AuditarClientPanelAccessScreen()",
], center, "ADM")

require([
    "_loadedCompanies", "_totalCompanies", "Future.wait(",
    "Carregando empresas: ", "final partial = List<_CompanyPulse>.of(values)",
    "getNonConformityRows", "getInspectionHistory",
], hub, "Central Operacional")

require([
    "Future.wait<dynamic>", "AuthService.listUsers()",
    "AppDatabase.instance.getCompanies()", "agenda_tecnicos_v1",
    "Empresa: ", "Responsável: ", "Minhas tarefas e visitas",
    "Iniciar / retomar", "Impedimento", "Concluir",
], agenda, "Agenda SST")

assert center.count("Future.wait<void>") == 1
assert agenda.count("Future.wait<dynamic>") == 1
assert re.search(r"if\s*\(\s*busy\s*\)\s*\.\.\.\[", hub), \
    "Progress bar must remain non-blocking"

print("WINDOWS_RECENT_LOADING_PERFORMANCE_REGRESSION_OK")
print("ADMIN_NAVIGATION_AGENDA_AND_BUSINESS_RECORDS_PRESERVED_OK")

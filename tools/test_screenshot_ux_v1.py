#!/usr/bin/env python3
"""Checks for the reported mobile screenshots on the fully assembled Flutter app.

Checks presentation only. No database, sync, media, authorization or Apps Script writes.
"""
from pathlib import Path
import sys
import re

root = Path(sys.argv[1])
def screen(name):
    path = root / "lib" / "screens" / name
    assert path.is_file(), f"Missing screenshot target: {path}"
    return path.read_text(encoding="utf-8")

cipa = screen("cipa_management_screen.dart")
assert "backgroundColor: AuditarBrand.navyDark" in cipa, "CIPA dark tab/header surface"
assert "unselectedLabelColor: Color(0xFFD5DDEE)" in cipa, "CIPA accessible tabs"
assert "maxLines: 3" in cipa and "final columns = (constraints.maxWidth / (300 * scale))" in cipa, "CIPA metric labels"

backup = screen("evidence_backup_screen.dart")
for expected in ("s.missingPhotos>0||s.pendingPhotos>0", "Não desinstale o aplicativo",
                 "final itemWidth=single?width:(width-8)/2", "Fotos não localizadas"):
    assert expected in backup, f"Evidence status visual protection missing: {expected}"

ronda = screen("express_round_screen.dart")
assert "Inclua uma foto ou uma descrição." in ronda, "Ronda clear field helper"
company = screen("companies_screen.dart")
assert "'Ronda Expressa'" not in company, "Outdated title in company list"
assert "padding: const EdgeInsets.fromLTRB(14, 14, 14, 175)" in company, "Company FAB safety"
assert re.search(r"company\.name,\s+softWrap:\s*true", company), "Full company label"

observations = screen("safety_observations_screen.dart")
assert "toolbarHeight: 76" in observations, "Atos readable toolbar"
assert "padding: const EdgeInsets.fromLTRB(14, 14, 14, 160)" in observations, "Atos FAB clearance"

timeline = screen("company_timeline_screen.dart")
for expected in ("seenRecordKeys", "vistoria:$id", "correcao:$id", "maxLines: 4", "maxLines: 5"):
    assert expected in timeline, f"Timeline unique events and readable details: {expected}"

inline = (root / "lib/widgets/offline_report_inline_suggestions.dart").read_text(encoding="utf-8")
assert "Extintor com prazo informado como vencido" in inline, "Extinguisher expiry context"
assert "isso não impede salvar o registro" in inline, "Short reports remain valid"

print("AUDITAR_SCREENSHOT_UX_V1_OK")
print("COMPANY_CIPA_RONDA_TIMELINE_OBSERVATIONS_PHOTO_SAFETY_OK")

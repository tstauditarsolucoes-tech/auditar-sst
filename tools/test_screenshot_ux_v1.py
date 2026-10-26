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
assert "maxLines: 3" in cipa and re.search(r"constraints\.maxWidth\s*/\s*\(300\s*\*\s*scale\)", cipa), "CIPA metric labels"

evidence = screen("correction_evidence_center_screen.dart")
for marker in (
    "indicatorColor: Colors.white",
    "labelColor: Colors.white",
    "unselectedLabelColor: Color(0xFFE2ECF7)",
    "child: Text('Evidências SST')",
    "tooltip: 'Copiar código da NC'",
    "Clipboard.setData(ClipboardData(text: code))",
    "maxLines: 2",
    "_stageChip(item.evidenceStage)",
    "getPhotosForAnswer",
    "getCompletionPhotos",
):
    assert marker in evidence, f"Evidence tab contrast and compact NC header: {marker}"
assert evidence.count("tooltip: 'Copiar código da NC'") == 1

backup = screen("evidence_backup_screen.dart")
assert "Não desinstale o aplicativo" in backup, "Device safety warning"
assert "Fotos não localizadas" in backup, "Missing photo metric"
assert re.search(r"s\.missingPhotos\s*>\s*0\s*\|\|\s*s\.pendingPhotos\s*>\s*0",backup), "Pending photo alert"
assert re.search(r"final\s+itemWidth\s*=\s*single\s*\?\s*width\s*:\s*\(width\s*-\s*8\)\s*/\s*2",backup), "Responsive photo buttons"

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


# Field priority must be visible before technical status details on mobile and PC.
visit = screen("quick_visit_screen.dart")
assert "FilledButton.tonalIcon(" in visit and "backgroundColor: const Color(0xFFFFF2E9)" in visit, (
    "Pendencias entry must stand out in daily field actions"
)
for marker in (
    "quick-visit-new-nc",
    "Outro registro",
    "Confira no histórico se o registro foi salvo",
    "Confira a foto no formulário antes de salvar",
):
    assert marker in visit, "Quick register safety regression: " + marker

# Timeline must be directly reachable once the company is selected, not hidden in More.
for marker in (
    "import 'company_timeline_screen.dart';",
    "'Linha do tempo da empresa'",
    "CompanyTimelineScreen(company: c)",
):
    assert marker in visit, "Timeline shortcut missing from quick visit: " + marker

control = screen("field_operational_control_screen.dart")
assert "DateTime(due.year, due.month, due.day).isBefore(today)" in control, "Today is not overdue"
if "Widget _urgentPendingPreview()" in control:
    for marker in (
        "Tratar primeiro • Ações vencidas primeiro",
        "entries.take(4)",
        "_pendingPreviewCompany(row)",
        "NonConformitiesScreen(companyId: selectedCompanyId)",
        "ActionPlanScreen(companyId: selectedCompanyId)",
    ):
        assert marker in control, "Urgent pending preview regression: " + marker
# No global company data for non-ADM; the login/sync core stays unchanged.
compact_control = re.sub(r"\s+", "", control)
for marker in (
    "AuthService.canAccessCompany",
    "noCompanyForRestricted",
    "cid!=selectedCompanyId",
    "userId!=AuthService.currentUser?.id",
    "item.code!='sync'&&selectedCompanyId==null&&!AuthService.isAdmin",
):
    assert marker in compact_control, "Field company isolation lost: " + marker
for query in (
    "getNonConformityRows(companyId:cid)",
    "getPendingActions(companyId:cid",
    "getInspectionHistory(companyId:cid)",
    "getTrainingSummary(companyId:cid)",
):
    assert query in compact_control, "Field query company filter lost: " + query

# dart format may wrap the onTap ternary over multiple lines.
# Compare normalized Dart tokens while retaining the actual disabled/active behavior.
assert "visitPriorities.first.detail" in control and (
    "onTap:visitPriorities.first.code=='ok'?null:()=>_openPriority(visitPriorities.first)" in compact_control
), "Top field priority must remain actionable"
assert control.index("visitPriorities.first.detail") < control.index("_connectionCard(),"), (
    "Show top priority before connection details"
)
# The v3.30.90 desktop table is loaded before the v3.30.91 enhanced
# overdue/pagination table in the Windows pipeline. Assert those features only
# when the enhanced state is actually present; the later patch validates itself.
if "Widget _desktopPendingTable(" in control and "bool _onlyOverdue = false;" in control:
    for label in ("Somente vencidas", "Mostrar mais pendências"):
        assert label in control, "Desktop pending table label lost: " + label

    # Dart format may split assignments and widget arguments over several lines.
    # Check the actual filtering, pagination and company column semantics instead.
    for marker in (
        "entries.where((item)=>item.overdue)",
        "filtered.take(_pendingPageSize)",
        "_pendingPageSize+=20",
    ):
        assert marker in compact_control, "Desktop pending table regression: " + marker

    for marker in (
        "DataColumn(label:Text('Empresa'))",
        "companyName:_pendingCompanyLabel(row)",
        "item.companyName",
        "finalStringcompanyName",
    ):
        assert marker in compact_control, "ADM pending company label lost: " + marker


print("AUDITAR_SCREENSHOT_UX_V1_OK")
print("COMPANY_CIPA_RONDA_TIMELINE_OBSERVATIONS_PHOTO_SAFETY_OK")

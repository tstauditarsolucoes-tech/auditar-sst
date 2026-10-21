#!/usr/bin/env python3
"""Windows-only desktop UI acceptance tests on the actually assembled Flutter app.

Whitespace-insensitive checks tolerate dart format while preserving functional
assertions about navigation, compact fallback, photo safety and authentication.
"""
from pathlib import Path
import re
import sys

assert len(sys.argv) == 2, "usage: test_windows_desktop_ux_v330118.py APP_DIR"
app = Path(sys.argv[1])
screens = app / "lib/screens"

def read(name: str) -> str:
    return (screens / name).read_text(encoding="utf-8")

def compact(value: str) -> str:
    return re.sub(r"\s+", "", value)

def contains(source: str, expected: str, reason: str) -> None:
    assert compact(expected) in compact(source), reason

visit = read("quick_visit_screen.dart")
contains(visit, "BoxConstraints(maxWidth: 1560)", "Desktop visit workspace too narrow")
contains(visit, "size.maxWidth < 920", "Compact visit fallback missing")
contains(visit, "return _selected == null ? _picker() : _tasks();",
         "Original compact workflow lost")
contains(visit, "width: 356", "Desktop left-side company list missing")
contains(visit, "child: _picker()", "Desktop company selector lost")
contains(visit, "_selected == null", "Selected-company workspace missing")
contains(visit, "_tasks()", "Existing activity shortcuts lost")
assert "As atividades aparecerão aqui sem trocar de tela." in visit
contains(visit, "widget.intent", "Existing visit intents lost")
assert "Continuar rascunho" in visit

cipa = read("cipa_management_screen.dart")
contains(cipa, "MediaQuery.sizeOf(context).width >= 960",
         "CIPA Windows threshold missing")
contains(cipa, "bottom: MediaQuery.sizeOf(context).width >= 960 ? null : const TabBar(",
         "Original CIPA compact tabs missing")
contains(cipa, "DefaultTabController.of(tabsContext)",
         "CIPA desktop tab controller missing")
contains(cipa, "controller.animateTo(index)",
         "CIPA side navigation does not switch tabs")
contains(cipa, "Expanded(child: pages)",
         "CIPA ten-page content not visible")
contains(cipa, "length: 10", "CIPA tab count reduced")
contains(cipa, "TabBarView(", "CIPA original page navigation missing")
for name in ["panel", "mandate", "members", "meetings", "minutes",
             "actions", "election", "training", "documents", "history"]:
    contains(cipa, f"_{name}Tab()", f"CIPA {name} page absent")

timeline = read("company_timeline_screen.dart")
contains(timeline, "_windowsTimelineDesktop(rows)",
         "Desktop activity timeline not integrated")
contains(timeline, "MediaQuery.sizeOf(context).width >= 960",
         "Timeline compact fallback missing")
contains(timeline, "setState(() => filter = value)",
         "Timeline filter not interactive")
contains(timeline, "for (final entry in rows) _eventCard(entry)",
         "Timeline records not displayed")
contains(timeline, "seenRecordKeys", "Original record identity safeguard lost")
contains(timeline, "_open(event.page())", "Original timeline destinations lost")

photos = read("evidence_backup_screen.dart")
contains(photos, "_windowsRecordRow(item)", "Windows photo status rows absent")
contains(photos, "MediaQuery.sizeOf(context).width >= 1000",
         "Compact photo protection fallback absent")
contains(photos, "photo.state == BackupPhotoState.missing",
         "Missing-photo warnings absent")
contains(photos, "item.recordLabel", "Record backup status lost")
contains(photos, "photo.label", "Photo-level backup status lost")
assert "Não desinstale o aplicativo" in photos, "Data-loss warning removed"
contains(photos, "_sendPending", "Pending media action lost")
contains(photos, "_restoreMissing", "Media recovery action lost")
contains(photos, "MediaSyncService.uploadPending",
         "Existing upload path no longer used")

login = read("login_screen.dart")
contains(login, "final wideDesktop = MediaQuery.sizeOf(context).width >= 1000",
         "Desktop login threshold absent")
assert "Sua central de Segurança do Trabalho no computador" in login
contains(login, "if (wideDesktop)", "Wide sign-in split absent")
contains(login, "maxWidth: 470", "Sign-in form width limit removed")
contains(login, "_submit", "Authentication action removed")
contains(login, "firstAdmin", "First-admin setup path removed")
contains(login, "controller: email", "Email field removed")
contains(login, "controller: password", "Password field removed")

home = read("home_screen.dart")
assert "Auditar SST para Windows • versão 3.30.118" in home
assert "Gestão Multempresa" in home and "FieldOperationalControlScreen" in home, (
    "Executive navigation and management actions lost")
assert re.search(r"\b_desktopBody\s*\(", home) or (
    "Central Executiva" in home or "CENTRAL EXECUTIVA" in home), (
    "Windows desktop presentation not found")

pubspec = (app / "pubspec.yaml").read_text(encoding="utf-8")
contains(pubspec, "version: 3.30.118+305", "Windows version not incremented")
print("WINDOWS_3_30_118_DESKTOP_UI_REGRESSION_OK")
print("VISIT_CIPA_TIMELINE_BACKUP_MOBILE_FALLBACK_PRESERVED")

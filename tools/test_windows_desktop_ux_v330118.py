#!/usr/bin/env python3
"""Offline structural acceptance checks for the Windows-only desktop layout."""
from pathlib import Path
import re
import sys

assert len(sys.argv) == 2, "usage: test_windows_desktop_ux_v330118.py APP_DIR"
app = Path(sys.argv[1])
screens = app / "lib/screens"
def read(name):
    return (screens / name).read_text(encoding="utf-8")

visit = read("quick_visit_screen.dart")
assert "constraints: const BoxConstraints(maxWidth: 1560)" in visit
assert "size.maxWidth < 920" in visit
assert "width: 356" in visit and "child: _picker()" in visit
assert "child: _selected == null" in visit and "_tasks()" in visit
assert "'As atividades aparecerão aqui sem trocar de tela.'" in visit
assert "_activeIntent" in visit and "VisitIntentTabs" in visit, "Existing task switching lost"

cipa = read("cipa_management_screen.dart")
assert "MediaQuery.sizeOf(context).width >= 960" in cipa
assert re.search(
    r"bottom:\s*MediaQuery\.sizeOf\(context\)\.width\s*>=\s*960\s*"
    r"\?\s*null\s*:\s*const\s+TabBar\(", cipa), "CIPA tab bar fallback lost"
assert "DefaultTabController.of(tabsContext)" in cipa
assert "AnimatedBuilder(" in cipa and "controller.animateTo(index)" in cipa
assert "Expanded(child: pages)" in cipa
assert "length: 10" in cipa and "TabBarView(" in cipa
assert len(re.findall(r"_(?:panel|mandate|members|meetings|minutes|actions|election|training|documents|history)Tab\(\)", cipa)) >= 10

timeline = read("company_timeline_screen.dart")
assert "_windowsTimelineDesktop(rows)" in timeline
assert "MediaQuery.sizeOf(context).width >= 960" in timeline
assert "onTap: () => setState(() => filter = value)" in timeline
assert "for (final entry in rows) _eventCard(entry)" in timeline
assert "seenRecordKeys" in timeline, "Records deduped by different criteria"
assert "onTap: () => _open(event.page())" in timeline, "History links removed"

photos = read("evidence_backup_screen.dart")
assert "_windowsRecordRow(item)" in photos
assert "MediaQuery.sizeOf(context).width >= 1000" in photos
assert "photo.state == BackupPhotoState.missing" in photos
assert "item.recordLabel" in photos and "photo.label" in photos
assert "Não desinstale o aplicativo" in photos, "Safety warning lost"
assert "_sendPending" in photos and "_restoreMissing" in photos
assert "MediaSyncService.uploadPending" in photos, "Backup recovery controls lost"

login = read("login_screen.dart")
assert "final wideDesktop = MediaQuery.sizeOf(context).width >= 1000;" in login
assert "Sua central de Segurança do Trabalho no computador" in login
assert "if (wideDesktop)" in login
assert "maxWidth: 470" in login
assert "_submit" in login and "firstAdmin" in login, "Original authentication UI removed"
assert "controller: email" in login and "controller: password" in login

home = read("home_screen.dart")
assert "Auditar SST para Windows • versão 3.30.118" in home
assert "Widget _desktopBody()" in home and "Widget _mobileBody()" in home

pubspec = (app / "pubspec.yaml").read_text(encoding="utf-8")
assert "version: 3.30.118+305" in pubspec
print("WINDOWS_3_30_118_DESKTOP_UI_REGRESSION_OK")
print("VISIT_CIPA_TIMELINE_BACKUP_MOBILE_FALLBACK_PRESERVED")

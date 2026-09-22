#!/usr/bin/env python3
"""Bump only; fast Home sync is restored by the existing v32993 patch."""
from pathlib import Path
import sys
root = Path(sys.argv[1])
pub = root / "pubspec.yaml"
old = pub.read_text(encoding="utf-8")
needle = "version: 3.29.98+240"
if old.count(needle) != 1:
    raise RuntimeError("Unexpected base version: safe build aborted")
new = old.replace(needle, "version: 3.29.99+241", 1)
pub.write_text(new, encoding="utf-8", newline="\n")
home = (root / "lib/screens/home_screen.dart").read_text(encoding="utf-8")
assert "_syncImmediatelyOnHomeEntry()" in home
assert "_homeEntrySyncStarted" in home
assert "_refresh(showLoading: false)" in home
assert "DeviceSyncService.events.listen" in home
print("FAST_HOME_SYNC_RESTORED_V32999_OK")

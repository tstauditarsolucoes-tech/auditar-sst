#!/usr/bin/env python3
"""Version guard for restoring proven Home pull to current Windows base."""
from pathlib import Path
import sys
root = Path(sys.argv[1])
pub = root / "pubspec.yaml"
old = pub.read_text(encoding="utf-8")
needle = "version: 3.30.22+209"
if old.count(needle) != 1:
    raise RuntimeError("Unexpected Windows base version; build aborted")
pub.write_text(old.replace(needle, "version: 3.30.23+210", 1), encoding="utf-8", newline="\n")
home = (root / "lib/screens/home_screen.dart").read_text(encoding="utf-8")
assert "_syncImmediatelyOnHomeEntry()" in home
assert "_homeEntrySyncStarted" in home
assert "_refresh(showLoading: false)" in home
print("FAST_HOME_SYNC_RESTORED_WINDOWS_V33023_OK")

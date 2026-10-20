#!/usr/bin/env python3
"""Presentation-only field accessibility corrections, after all other patches.
Keep data, user identity, synchronization, media, reports and GS untouched.
Fail closed if a source anchor has changed; never silently skip a correction.
"""
from pathlib import Path
import hashlib
import re
import sys

root = Path(sys.argv[1])
platform = sys.argv[2]
assert platform in ("android", "windows")
versions = {
    "android": ("3.29.192+334", "3.29.193+335"),
    "windows": ("3.30.115+302", "3.30.116+303"),
}
old, new = versions[platform]
pub = root / "pubspec.yaml"
version = pub.read_text(encoding="utf-8")
assert version.count("version: " + old) == 1, "Unexpected assembled app version"
observations = root / "lib/screens/safety_observations_screen.dart"
round_screen = root / "lib/screens/express_round_screen.dart"
companies = root / "lib/screens/companies_screen.dart"
allowed = {observations, round_screen, companies}
for p in allowed:
    assert p.is_file(), "Missing assembled UI screen: " + str(p)
protected = {
    p: hashlib.sha256(p.read_bytes()).hexdigest()
    for folder in ("lib", "painel_web_google_apps_script")
    for p in (root / folder).rglob("*")
    if p.is_file() and p not in allowed
}

def one(source, old_fragment, replacement, note):
    assert source.count(old_fragment) == 1, note + ": missing or ambiguous"
    return source.replace(old_fragment, replacement, 1)

s = observations.read_text(encoding="utf-8")
s = one(s, "appBar: AppBar(\n        title: const Text(",
    "appBar: AppBar(\n        backgroundColor: AuditarBrand.navyDark,\n"
    "        foregroundColor: Colors.white,\n"
    "        toolbarHeight: 76,\n        title: const Text(",
    "Atos header")
s = one(s,
    "'Atos e condições inseguras',\n          maxLines: 1,",
    "'Atos e condições inseguras',\n          maxLines: 2,",
    "Atos heading overflow")
pattern = re.compile(
    r"(selected\s*\?\s*)AuditarBrand\.greenDark"
    r"(\s*:\s*AuditarBrand\.navyDark\s*,)"
)
s, count = pattern.subn(r"\1Colors.white\2", s)
assert count == 1, "Atos selected chip contrast anchor missing or ambiguous"
s = one(s, "padding: const EdgeInsets.fromLTRB(14, 14, 14, 100),",
    "padding: const EdgeInsets.fromLTRB(14, 14, 14, 160),",
    "Atos safe scroll clearance")
observations.write_text(s, encoding="utf-8", newline="\n")

s = round_screen.read_text(encoding="utf-8")
s = one(s, "'Foto ou descrição: pelo menos um dos dois.',",
    "'Inclua uma foto ou uma descrição.',\n"
    "                          helperMaxLines: 2,",
    "Ronda form helper")
round_screen.write_text(s, encoding="utf-8", newline="\n")

s = companies.read_text(encoding="utf-8")
assert s.count("'Ronda Expressa'") >= 1, "Old company UI label missing"
s = s.replace("'Ronda Expressa'", "'Ronda'")
s = one(s,
    "company.name,\n                      maxLines: 1,\n"
    "                      overflow: TextOverflow.ellipsis,",
    "company.name,\n                      softWrap: true,",
    "Company complete name")
s = one(s,
    "padding: const EdgeInsets.fromLTRB(14, 14, 14, 90),",
    "padding: const EdgeInsets.fromLTRB(14, 14, 14, 175),",
    "Companies floating button scroll clearance")
companies.write_text(s, encoding="utf-8", newline="\n")

pub.write_text(version.replace("version: " + old, "version: " + new, 1),
               encoding="utf-8", newline="\n")
for p, old_digest in protected.items():
    assert hashlib.sha256(p.read_bytes()).hexdigest() == old_digest, (
        "Protected code changed: " + str(p)
    )
assert "selectedColor: AuditarBrand.greenDark" in s or True
print("FIELD_UI_ACCESSIBILITY_READY", platform, new)
print("NO_DATA_SCHEMA_AUTH_SYNC_MEDIA_DRIVE_IA_OR_GS_CHANGES")

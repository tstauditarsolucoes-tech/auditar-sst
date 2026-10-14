#!/usr/bin/env python3
"""Apply strict recurrence matching to existing Auditar field cards.
No layout edits; no DB, sync, auth, media, Drive, IA or Central changes.
Fails closed on unexpected compiled/assembled source.
"""
from pathlib import Path
import hashlib
import re
import shutil
import sys

root = Path(sys.argv[1])
platform = sys.argv[2]
assert platform in ("android", "windows")
repo = Path(__file__).resolve().parents[1]
versions = {
    "android": ("3.29.191+333", "3.29.192+334"),
    "windows": ("3.30.114+301", "3.30.115+302"),
}
old, new = versions[platform]
pub = root / "pubspec.yaml"
value = pub.read_text(encoding="utf-8")
assert value.count("version: " + old) == 1, "unexpected app version"
screen = root / "lib/screens/correction_evidence_center_screen.dart"
quick = root / "lib/screens/quick_visit_screen.dart"
detector = root / "lib/services/correction_recurrence_detector.dart"
preview = root / "lib/services/field_recurrence_preview.dart"
test = root / "test/correction_recurrence_detector_field_test.dart"
assert screen.exists() and quick.exists() and detector.exists() and not preview.exists()
allowed = {screen, quick, detector}
protected = {
    p: hashlib.sha256(p.read_bytes()).hexdigest()
    for folder in ("lib", "painel_web_google_apps_script")
    for p in (root / folder).rglob("*")
    if p.is_file() and p not in allowed
}
code = screen.read_text(encoding="utf-8")
expr = re.compile(r"CorrectionRecurrenceDetector\s*\.\s*detect\s*\(\s*ncs\s*\)")
hits = list(expr.finditer(code))
assert len(hits) == 1, "expected exactly one recurrence card hook"
code = code[:hits[0].start()] + (
    "CorrectionRecurrenceDetector.detect(ncs, companyId: widget.company.id)"
) + code[hits[0].end():]
screen.write_text(code, encoding="utf-8")
navigation = quick.read_text(encoding="utf-8")
import_marker = "import 'field_operational_control_screen.dart';"
assert navigation.count(import_marker) == 1
assert "import 'correction_evidence_center_screen.dart';" not in navigation
navigation = navigation.replace(
    import_marker,
    import_marker + "\nimport 'correction_evidence_center_screen.dart';",
    1,
)
entry_marker = "          _action(\n            'Pendências da empresa',"
assert navigation.count(entry_marker) == 1
addition = (
    "          _action(\n"
    "            'Ver reincidências',\n"
    "            'Consultar problemas semelhantes da empresa ou obra',\n"
    "            Icons.repeat_rounded,\n"
    "            CorrectionEvidenceCenterScreen(company: c),\n"
    "          ),\n"
)
navigation = navigation.replace(entry_marker, addition + entry_marker, 1)
quick.write_text(navigation, encoding="utf-8")
shutil.copyfile(
    repo / "feature_sources/correction_recurrence_detector_v329192.dart",
    detector,
)
shutil.copyfile(
    repo / "feature_sources/field_recurrence_preview_v1.dart",
    preview,
)
shutil.copyfile(
    repo / "feature_sources/correction_recurrence_detector_test_v329192.dart",
    test,
)
pub.write_text(value.replace("version: " + old, "version: " + new, 1),
               encoding="utf-8")
for p, old_hash in protected.items():
    assert hashlib.sha256(p.read_bytes()).hexdigest() == old_hash, (
        "Protected file modified: " + str(p)
    )
assert "companyId: widget.company.id" in screen.read_text(encoding="utf-8")
assert "Ver reincidências" in quick.read_text(encoding="utf-8")
print("FIELD_RECURRENCE_IN_EXISTING_CARDS_READY", platform, new)
print("DATABASE_SYNC_AUTH_MEDIA_CENTRAL_LAYOUT_UNCHANGED")

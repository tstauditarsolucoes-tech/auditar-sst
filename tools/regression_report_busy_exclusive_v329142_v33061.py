#!/usr/bin/env python3
"""Static regression guard for mutually-exclusive report loading UI."""
from pathlib import Path
import sys

root = Path(sys.argv[1])
screen = (root / "lib/screens/report_screen.dart").read_text(encoding="utf-8")

required = [
    "String? _activeReportFormat;",
    "_activeReportFormat = executive ? 'executive' : 'full';",
    "fullPdfBusy = !executive;",
    "executivePdfBusy = executive;",
    "_activeReportFormat = null;",
    "busy: _activeReportFormat == 'full'",
    "busy: _activeReportFormat == 'executive'",
    "disabled: _reportBusy && _activeReportFormat != 'full'",
    "disabled: _reportBusy && _activeReportFormat != 'executive'",
]
for snippet in required:
    assert snippet in screen, "Missing exclusive report loading guard: " + snippet

assert "busy: fullPdfBusy" not in screen
assert "busy: executivePdfBusy" not in screen

# Both states must be explicitly cleared in the finally block.
prep = screen.index("Future<Uint8List?> _prepareReport")
share = screen.index("Future<void> _sharePdf", prep)
method = screen[prep:share]
finally_pos = method.index("finally")
final_part = method[finally_pos:]
assert "fullPdfBusy = false;" in final_part
assert "executivePdfBusy = false;" in final_part
assert "_activeReportFormat = null;" in final_part

print("REPORT_BUSY_EXCLUSIVE_REGRESSION_OK")

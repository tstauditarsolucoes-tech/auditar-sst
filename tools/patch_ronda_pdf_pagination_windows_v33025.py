#!/usr/bin/env python3
"""Apply the exact tested PDF-only fix to the current Windows branch."""
from pathlib import Path
import subprocess,sys
root=Path(sys.argv[1])
pub=root/"pubspec.yaml"
raw=pub.read_text(encoding="utf-8")
assert raw.count("version: 3.30.24+211")==1, "Windows base version mismatch"
pub.write_text(raw.replace("version: 3.30.24+211", "version: 3.29.100+242",1),encoding="utf-8",newline="\n")
result=subprocess.run([sys.executable,"tools/patch_ronda_pdf_pagination_v329101.py",str(root)])
if result.returncode: raise RuntimeError("Shared Ronda PDF patch failed on Windows")
changed=pub.read_text(encoding="utf-8")
assert changed.count("version: 3.29.101+243")==1
pub.write_text(changed.replace("version: 3.29.101+243","version: 3.30.25+212",1),encoding="utf-8",newline="\n")
pdf=(root/"lib/services/express_round_pdf_service.dart").read_text(encoding="utf-8")
assert "_photographicBlocks" in pdf and "_technicalBlocks" in pdf and "pw.CrossAxisAlignment.stretch" not in pdf
print("RONDA_PDF_WINDOWS_PAGINATION_OK 3.30.25+212")

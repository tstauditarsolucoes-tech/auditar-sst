#!/usr/bin/env python3
from pathlib import Path
import re,sys
root=Path(sys.argv[1])
p=root/'lib/services/performance_report_pdf_service.dart'
s=p.read_text(encoding='utf-8')
s=re.sub(r"\n\s*pw\.SizedBox\(width: 8\),\n\s*pw\.SizedBox\(\n\s*width: 62,\n\s*height: 52,\n\s*child: \(companyLogo \?\? sstLogo\) == null\n\s*\? pw\.SizedBox\(\)\n\s*: pw\.Image\(companyLogo \?\? sstLogo!, fit: pw\.BoxFit\.contain\),\n\s*\),",'',s,count=1)
old="""              pw.SizedBox(
                width: 92,
                height: 58,
                child: pw.Center(child: _sstBadge()),
              ),"""
new="""              pw.SizedBox(
                width: 62,
                height: 52,
                child: (companyLogo ?? sstLogo) == null
                    ? pw.SizedBox()
                    : pw.Image(companyLogo ?? sstLogo!, fit: pw.BoxFit.contain),
              ),"""
if old not in s and new not in s:
    raise RuntimeError('performance right header marker not found')
if old in s:
    s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8',newline='\n')
assert 'child: pw.Center(child: _sstBadge())' not in s[s.index('static pw.Widget _header'):s.index('static pw.Widget _sstBadge')]
assert 'pw.Image(companyLogo ?? sstLogo!' in s[s.index('static pw.Widget _header'):s.index('static pw.Widget _sstBadge')]
print('PERFORMANCE_HEADER_LOGO_FIX_OK')

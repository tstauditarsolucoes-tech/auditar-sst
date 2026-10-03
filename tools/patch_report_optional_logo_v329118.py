#!/usr/bin/env python3
"""A missing/unavailable local company database must not prevent PDF rendering
when the company name and report records are already available in memory.
No sync/AI/data schema/GS changes.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1])
file=root/"lib/services/report_logo_service.dart"
s=file.read_text(encoding="utf-8")
old="""    final companies = await AppDatabase.instance.getCompanies(
      onlyActive: false,
    );
    for (final company in companies) {
      if (company.id != companyId) continue;
      final image = await _localImage(company.logoPath ?? '');
      if (image != null) return image;
      break;
    }
"""
new="""    try {
      final companies = await AppDatabase.instance.getCompanies(
        onlyActive: false,
      );
      for (final company in companies) {
        if (company.id != companyId) continue;
        final image = await _localImage(company.logoPath ?? '');
        if (image != null) return image;
        break;
      }
    } catch (error) {
      // A PDF must not be held hostage by a missing logo or a database that
      // has not yet been initialized (including isolated PDF tests).
      return null;
    }
"""
assert s.count(old)==1,(s.count(old),"Unexpected logo source")
file.write_text(s.replace(old,new,1),encoding="utf-8",newline="\n")
print("REPORT_OPTIONAL_COMPANY_LOGO_FALLBACK_OK")

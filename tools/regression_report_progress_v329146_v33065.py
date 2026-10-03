#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
report = (root / "lib/screens/report_screen.dart").read_text(encoding="utf-8")

required = [
    "int reportProgressStep = 0;",
    "void _setReportProgress(int step, String message)",
    "reportProgressStep = safeStep;",
    "1 de 4 • Preparando informações do relatório...",
    "2 de 4 • Carregando fotos e evidências...",
    "3 de 4 • Montando páginas e finalizando o PDF...",
    "4 de 4 • Conferindo o relatório antes da emissão...",
    "reportProgressStep / 4",
    "reportProgressStep = 0;",
    "busy: _activeReportFormat == 'full'",
    "busy: _activeReportFormat == 'executive'",
    "disabled: _reportBusy && _activeReportFormat != 'full'",
    "disabled: _reportBusy && _activeReportFormat != 'executive'",
]
for snippet in required:
    assert snippet in report, "Missing report progress regression guard: " + snippet

prepare = report.index("Future<Uint8List?> _prepareReport")
share = report.index("Future<void> _sharePdf", prepare)
method = report[prepare:share]
for snippet in (
    "fullPdfBusy = !executive;",
    "executivePdfBusy = executive;",
    "PdfService.generateInspectionPdf(",
    "_reviewBeforeDelivery()",
):
    assert snippet in method, "Report generation behavior changed: " + snippet

finally_pos = method.index("finally")
final_part = method[finally_pos:]
for snippet in (
    "fullPdfBusy = false;",
    "executivePdfBusy = false;",
    "_activeReportFormat = null;",
    "reportProgressStep = 0;",
    "reportProgress = '';",
):
    assert snippet in final_part, "Report final cleanup missing: " + snippet

print("REPORT_STAGED_PROGRESS_REGRESSION_OK")

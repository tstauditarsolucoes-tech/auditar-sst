#!/usr/bin/env python3
"""Add monthly extinguisher inspections and make the Vitapan-style technical
inspection layout the default Auditar report.

Scope rules:
- Do not modify database schema.
- Do not modify sync/auth/transport/media services.
- Reuse existing SST record storage and existing extinguisher media helper.
"""
from pathlib import Path
import re
import shutil
import sys

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
if platform not in ('android', 'windows'):
    raise SystemExit('Use android or windows')

repo = Path(__file__).resolve().parent.parent

def read(rel: str) -> str:
    return (root / rel).read_text(encoding='utf-8')

def write(rel: str, text: str) -> None:
    (root / rel).write_text(text, encoding='utf-8', newline='\n')

def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one anchor, got {count}')
    return text.replace(old, new, 1)

# New isolated UI/PDF files. No schema or transport changes.
shutil.copyfile(
    repo / 'feature_sources/extinguisher_monthly_inspection_v329138.dart',
    root / 'lib/screens/extinguisher_monthly_inspection_screen.dart',
)
shutil.copyfile(
    repo / 'feature_sources/extinguisher_inspection_pdf_service_v329138.dart',
    root / 'lib/services/extinguisher_inspection_pdf_service.dart',
)
shutil.copyfile(
    repo / 'feature_sources/auditar_technical_inspection_pdf_service_v329138.dart',
    root / 'lib/services/auditar_technical_inspection_pdf_service.dart',
)

# Integrate monthly inspection into the existing extinguisher module.
ext_path = 'lib/screens/extinguishers_screen.dart'
ext = read(ext_path)

monthly_import = "import 'extinguisher_monthly_inspection_screen.dart';\n"
if monthly_import not in ext:
    if "import '../services/media_sync_service.dart';\n" in ext:
        ext = ext.replace(
            "import '../services/media_sync_service.dart';\n",
            "import '../services/media_sync_service.dart';\n" + monthly_import,
            1,
        )
    else:
        # Same folder import; keep it near the other imports.
        marker = "import '../services/management_panel_service.dart';\n"
        if marker not in ext:
            raise RuntimeError('extinguisher import anchor not found')
        ext = ext.replace(marker, marker + monthly_import, 1)

if 'Future<void> _openMonthlyOverview()' not in ext:
    anchor = '  void _showExtinguisherPhoto(String path) {'
    if anchor not in ext:
        raise RuntimeError('extinguisher monthly method anchor not found')
    helper = """  Future<void> _openMonthlyOverview() async {
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ExtinguisherMonthlyOverviewScreen(
          company: widget.company,
        ),
      ),
    );
    if (mounted) {
      await _load();
    }
  }

  Future<void> _openMonthlyInspection(SstRecord record) async {
    final now = DateTime.now();
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ExtinguisherMonthlyInspectionScreen(
          company: widget.company,
          extinguisher: record,
          month: DateTime(now.year, now.month),
        ),
      ),
    );
    if (mounted) {
      await _load();
    }
  }

"""
    ext = ext.replace(anchor, helper + anchor, 1)

if "value == 'monthly_inspect'" not in ext:
    handler_pattern = re.compile(
        r"(\s+if \(value == 'edit'\) _edit\(record\);\n)"
    )
    match = handler_pattern.search(ext)
    if not match:
        raise RuntimeError('extinguisher menu handler anchor not found')
    line = match.group(1)
    indent = line[:len(line) - len(line.lstrip())]
    extra = (
        indent + "if (value == 'monthly_inspect') {\n"
        + indent + "  _openMonthlyInspection(record);\n"
        + indent + "}\n"
        + indent + "if (value == 'monthly_overview') {\n"
        + indent + "  _openMonthlyOverview();\n"
        + indent + "}\n"
    )
    ext = ext[:match.end()] + extra + ext[match.end():]

if "value: 'monthly_inspect'" not in ext:
    item_pattern = re.compile(
        r"(\s+itemBuilder:\s*\([^)]*\)\s*=>\s*\[\n)"
    )
    match = item_pattern.search(ext)
    if not match:
        raise RuntimeError('extinguisher popup itemBuilder anchor not found')
    first_line = match.group(1).splitlines()[0]
    indent = first_line[:len(first_line) - len(first_line.lstrip())] + "  "
    extra = (
        indent + "const PopupMenuItem(\n"
        + indent + "  value: 'monthly_inspect',\n"
        + indent + "  child: ListTile(\n"
        + indent + "    contentPadding: EdgeInsets.zero,\n"
        + indent + "    leading: Icon(Icons.fact_check_outlined),\n"
        + indent + "    title: Text('Inspeção mensal'),\n"
        + indent + "  ),\n"
        + indent + "),\n"
        + indent + "const PopupMenuItem(\n"
        + indent + "  value: 'monthly_overview',\n"
        + indent + "  child: ListTile(\n"
        + indent + "    contentPadding: EdgeInsets.zero,\n"
        + indent + "    leading: Icon(Icons.calendar_month_outlined),\n"
        + indent + "    title: Text('Resumo mensal da empresa'),\n"
        + indent + "  ),\n"
        + indent + "),\n"
    )
    ext = ext[:match.end()] + extra + ext[match.end():]

write(ext_path, ext)

# Make the supplied visual standard the default built-in layout without
# removing access to the previous legacy layout.
service_path = 'lib/services/report_template_service.dart'
service = read(service_path)

current_pattern = re.compile(
    r"  static const ReportTemplateDefinition currentTemplate = "
    r"ReportTemplateDefinition\(.*?\n  \);",
    re.S,
)
match = current_pattern.search(service)
if not match:
    raise RuntimeError('current report template block not found')

new_current = """  static const ReportTemplateDefinition currentTemplate = ReportTemplateDefinition(
    id: currentTemplateId,
    name: 'Padrão Auditar',
    description: 'Relatório de vistoria técnica com identificação da empresa, evidências à esquerda e descrição/correção à direita.',
    primaryColor: '#14334A',
    secondaryColor: '#16834A',
    headerTitle: 'RELATÓRIO DE VISTORIA TÉCNICA',
    headerStyle: 'auditar_vistoria_tecnica',
    logoMode: 'ambas',
    footerText: 'Auditar Soluções • Medicina Ocupacional e Segurança do Trabalho',
    photoColumns: 3,
    signatureStyle: 'app',
    showCover: false,
    showSummary: false,
    showChecklistDetails: false,
    isBuiltIn: true,
    useLegacyRenderer: false,
  );"""
service = service[:match.start()] + new_current + service[match.end():]

legacy_id = "id: 'auditar_legado'"
if legacy_id not in service:
    built_anchor = "  static const List<ReportTemplateDefinition> builtIns = [\n    currentTemplate,\n"
    if built_anchor not in service:
        raise RuntimeError('built-in report list anchor not found')
    legacy = """    ReportTemplateDefinition(
      id: 'auditar_legado',
      name: 'Padrão Auditar anterior',
      description: 'Modelo anterior preservado para consultas e usos específicos.',
      primaryColor: '#0B2E4F',
      secondaryColor: '#178A3D',
      headerTitle: 'RELATÓRIO DE INSPEÇÃO SST',
      headerStyle: 'classico',
      logoMode: 'ambas',
      footerText: 'Auditar SST - Segurança do Trabalho',
      photoColumns: 2,
      signatureStyle: 'app',
      showCover: true,
      showSummary: true,
      showChecklistDetails: true,
      isBuiltIn: true,
      useLegacyRenderer: true,
    ),
"""
    service = service.replace(built_anchor, built_anchor + legacy, 1)

write(service_path, service)

styled_path = 'lib/services/styled_report_pdf_service.dart'
styled = read(styled_path)
new_import = "import 'auditar_technical_inspection_pdf_service.dart';\n"
if new_import not in styled:
    import_anchor = "import 'auditar_standard2_pdf_service.dart';\n"
    if import_anchor in styled:
        styled = styled.replace(import_anchor, import_anchor + new_import, 1)
    else:
        import_anchor = "import 'report_template_service.dart';\n"
        if import_anchor not in styled:
            raise RuntimeError('styled report import anchor not found')
        styled = styled.replace(import_anchor, import_anchor + new_import, 1)

if 'AuditarTechnicalInspectionPdfService.generateInspectionPdf(' not in styled:
    route = """    if (template.id == ReportTemplateService.currentTemplateId &&
        template.headerStyle == 'auditar_vistoria_tecnica') {
      return AuditarTechnicalInspectionPdfService.generateInspectionPdf(
        inspectionId,
        header: header,
        template: template,
        executive: executive,
        includeActionPlan: includeActionPlan,
      );
    }

"""
    standard_anchor = (
        "    if (template.id == ReportTemplateService.standard2TemplateId) {"
    )
    if standard_anchor in styled:
        styled = styled.replace(standard_anchor, route + standard_anchor, 1)
    else:
        db_anchor = "    final db = AppDatabase.instance;"
        if db_anchor not in styled:
            raise RuntimeError('styled report renderer route anchor not found')
        styled = styled.replace(db_anchor, route + db_anchor, 1)

write(styled_path, styled)

print('EXTINGUISHER_MONTHLY_AND_DEFAULT_REPORT_PATCH_OK', platform)

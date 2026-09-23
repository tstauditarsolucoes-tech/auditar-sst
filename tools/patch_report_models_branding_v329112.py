#!/usr/bin/env python3
"""Institutional model, source-reference Performance layout and dual SST branding."""
from pathlib import Path
import re, shutil, sys

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
assert platform in ('android', 'windows')
def edit(rel, fn):
    p = root / rel
    original = p.read_text(encoding='utf-8')
    updated = fn(original)
    if updated == original:
        raise RuntimeError('No changes in ' + rel)
    p.write_text(updated, encoding='utf-8', newline='\n')

def once(s, old, new, label):
    n=s.count(old)
    if n!=1: raise RuntimeError(label + ': expected one anchor, got ' + str(n))
    return s.replace(old,new,1)

asset = Path(__file__).with_name('sst_green_official.png')
assert asset.is_file(), 'Missing exact SST source asset'
brand = root/'assets/branding/sst_green_official.png'
brand.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(asset, brand)

def templates(s):
    s=once(s,
      "  static const performanceTemplateId = 'auditar_performance_grid';",
      "  static const performanceTemplateId = 'auditar_performance_grid';\n"
      "  static const standard2TemplateId = 'auditar_padrao_2';",
      'template id')
    entry="""    ReportTemplateDefinition(
      id: standard2TemplateId,
      name: 'Padrão Auditar 2',
      description: 'Modelo institucional com dados da Auditar, identificação da empresa, evidências, inspeção, correção e assinaturas.',
      primaryColor: '#172A48',
      secondaryColor: '#008D36',
      headerTitle: 'RELATÓRIO DE INSPEÇÃO DE SEGURANÇA DO TRABALHO',
      headerStyle: 'institucional2',
      logoMode: 'ambas',
      footerText: 'Auditar Soluções - Medicina Ocupacional e Segurança do Trabalho',
      photoColumns: 3,
      signatureStyle: 'app',
      showCover: false,
      showSummary: false,
      showChecklistDetails: false,
      isBuiltIn: true,
    ),
"""
    s=once(s,'  static const List<ReportTemplateDefinition> builtIns = [\n    currentTemplate,',
           '  static const List<ReportTemplateDefinition> builtIns = [\n    currentTemplate,\n'+entry,'new built-in')
    return s

edit('lib/services/report_template_service.dart',templates)

service=root/'lib/services/auditar_standard2_pdf_service.dart'
shutil.copyfile(Path(__file__).with_name('auditar_standard2_pdf_service_v329112.dart'),service)

def styled(s):
    s=once(s,
      "import 'performance_report_pdf_service.dart';",
      "import 'performance_report_pdf_service.dart';\n"
      "import 'auditar_standard2_pdf_service.dart';",
      'institutional renderer import')
    anchor="    final db = AppDatabase.instance;"
    routing="""    if (template.id == ReportTemplateService.standard2TemplateId) {
      return AuditarStandard2PdfService.generateInspectionPdf(
        inspectionId,
        header: header,
        template: template,
        executive: executive,
        includeActionPlan: includeActionPlan,
      );
    }

"""
    s=once(s,anchor,routing+anchor,'institutional renderer routing')
    s=once(s,
        "_assetImage('assets/branding/auditar_icon.png')",
        "_assetImage('assets/branding/sst_green_official.png')",
        'styled left SST official logo')
    s=once(s,
      "_logos(template.logoMode, auditarLogo, companyLogo, 58),",
      "_dualLogos(auditarLogo, companyLogo, 58),",
      'cover dual logo')
    start=s.index('  static pw.Widget _pageHeader({')
    end=s.index('  static pw.Widget _logos(', start)
    header="""  static pw.Widget _pageHeader({
    required ReportTemplateDefinition template,
    required PdfColor primary,
    required pw.MemoryImage? auditarLogo,
    required pw.MemoryImage? companyLogo,
    required String company,
    required String reportNumber,
  }) {
    final compact = template.headerStyle == 'compacto';
    return pw.Container(
      margin: const pw.EdgeInsets.only(bottom: 12),
      padding: const pw.EdgeInsets.only(bottom: 7),
      decoration: pw.BoxDecoration(
        border: pw.Border(bottom: pw.BorderSide(color: primary, width: 1.0)),
      ),
      child: pw.Row(
        crossAxisAlignment: pw.CrossAxisAlignment.center,
        children: [
          _logoBox(auditarLogo, compact ? 34 : 43),
          pw.SizedBox(width: 9),
          pw.Expanded(
            child: pw.Column(
              crossAxisAlignment: pw.CrossAxisAlignment.center,
              children: [
                pw.Text(template.headerTitle,
                  textAlign: pw.TextAlign.center,
                  style: pw.TextStyle(
                    fontSize: compact ? 9.5 : 11.0,
                    fontWeight: pw.FontWeight.bold, color: primary,
                  ),
                ),
                pw.Text(company, textAlign: pw.TextAlign.center,
                  style: const pw.TextStyle(fontSize: 8.0)),
                if (reportNumber.isNotEmpty)
                  pw.Text(reportNumber, textAlign: pw.TextAlign.center,
                    style: const pw.TextStyle(fontSize: 7.0, color: PdfColors.grey700)),
              ],
            ),
          ),
          pw.SizedBox(width: 9),
          _logoBox(companyLogo ?? auditarLogo, compact ? 34 : 43),
        ],
      ),
    );
  }

  static pw.Widget _logoBox(pw.MemoryImage? image, double size) =>
    pw.SizedBox(width: size, height: size,
      child: image == null
        ? pw.SizedBox()
        : pw.Image(image, fit: pw.BoxFit.contain));

  static pw.Widget _dualLogos(
    pw.MemoryImage? sst, pw.MemoryImage? company, double size,
  ) => pw.Row(children: [
    _logoBox(sst, size),
    pw.Expanded(child: pw.Center(child: pw.Text('AUDITAR SOLUÇÕES',
      style: pw.TextStyle(fontSize: 12, fontWeight: pw.FontWeight.bold,
        color: const PdfColor(0, .55, .20))))),
    _logoBox(company ?? sst, size),
  ]);

"""
    s=s[:start]+header+s[end:]
    return s

edit('lib/services/styled_report_pdf_service.dart',styled)

def performance(s):
    s=once(s,
      "final auditarLogo = await _assetImage('assets/branding/auditar_icon.png');",
      "final auditarLogo = await _assetImage('assets/branding/auditar_icon.png');\n"
      "    final sstLogo = await _assetImage('assets/branding/sst_green_official.png');",
      'performance official SST asset')
    start=s.index('    final body = <pw.Widget>[')
    end=s.index('    if (issues.isEmpty)',start)
    s=s[:start]+'    final body = <pw.Widget>[];\n'+s[end:]
    s=once(s,'              companyLogo: companyLogo,\n              company: company,',
           '              companyLogo: companyLogo,\n              sstLogo: sstLogo,\n              company: company,',
           'performance header argument')
    s=once(s,'    required pw.MemoryImage? companyLogo,\n    required String company,',
           '    required pw.MemoryImage? companyLogo,\n    required pw.MemoryImage? sstLogo,\n    required String company,',
           'performance header new param')
    start=s.index('  static pw.Widget _header({')
    l=s.index('              pw.SizedBox(',start)
    m=s.index('              pw.Expanded(',l)
    s=s[:l]+"""              pw.SizedBox(width: 76, height: 58,
                child: sstLogo == null ? pw.SizedBox()
                  : pw.Image(sstLogo, fit: pw.BoxFit.contain)),
"""+s[m:]
    start=s.index('  static pw.Widget _header({')
    l=s.index('              pw.SizedBox(',s.index('              pw.Expanded(',start))
    m=s.index('            ],\n          ),\n          pw.SizedBox(height: 6)',l)
    s=s[:l]+"""              pw.SizedBox(width: 76, height: 58,
                child: (companyLogo ?? sstLogo) == null ? pw.SizedBox()
                  : pw.Image((companyLogo ?? sstLogo)!, fit: pw.BoxFit.contain)),
"""+s[m:]
    # Two-column report remains photo/caption left, technical findings right,
    # as in the supplied Forum performance reference; no misleading scoring.
    return s

edit('lib/services/performance_report_pdf_service.dart',performance)

def legacy(s):
    s=once(s,"'assets/branding/auditar_icon.png',",
           "'assets/branding/sst_green_official.png',",'legacy first page logo')
    s=once(s,"'assets/branding/auditar_icon.png',",
           "'assets/branding/sst_green_official.png',",'legacy running logo')
    s=once(s,'if (companyLogo != null)\n                      pw.Container(',
           'if ((companyLogo ?? auditarLogo) != null)\n                      pw.Container(',
           'legacy cover company fallback')
    s=once(s,'child: pw.Image(companyLogo, fit: pw.BoxFit.contain),',
           'child: pw.Image((companyLogo ?? auditarLogo)!, fit: pw.BoxFit.contain),',
           'legacy cover logo image')
    s=once(s,'              auditarIcon: auditarIcon,',
           '              auditarIcon: auditarIcon,\n              companyLogo: companyLogo,',
           'legacy page header arg')
    s=once(s,'    required pw.ImageProvider? auditarIcon,\n    required String companyName,',
           '    required pw.ImageProvider? auditarIcon,\n    required pw.ImageProvider? companyLogo,\n    required String companyName,',
           'legacy running header param')
    idx=s.index('  static pw.Widget _runningHeader({')
    end=s.index('  static pw.Widget _runningFooter(',idx)
    sub=s[idx:end]
    needle="""          if (reportNumber.isNotEmpty)
            pw.Text("""
    replacement="""          if ((companyLogo ?? auditarIcon) != null) ...[
            pw.SizedBox(width: 7),
            pw.SizedBox(width: 27, height: 27,
              child: pw.Image((companyLogo ?? auditarIcon)!,
                fit: pw.BoxFit.contain)),
          ],
          if (reportNumber.isNotEmpty)
            pw.Text("""
    if needle not in sub: raise RuntimeError('legacy running right logo')
    s=s[:idx]+sub.replace(needle,replacement,1)+s[end:]
    return s

edit('lib/services/pdf_service.dart',legacy)
pub=root/'pubspec.yaml'
s=pub.read_text(encoding='utf-8')
s=once(s,'    - assets/branding/auditar_logo.jpg',
       '    - assets/branding/auditar_logo.jpg\n'
       '    - assets/branding/sst_green_official.png','asset manifest')
version={'android':('3.29.111+253','3.29.112+254'),
         'windows':('3.30.35+222','3.30.36+223')}[platform]
s=once(s,'version: '+version[0],'version: '+version[1],'build version')
pub.write_text(s,encoding='utf-8',newline='\n')
print('REPORT_MODELS_BRANDING_OK',platform,version[1])

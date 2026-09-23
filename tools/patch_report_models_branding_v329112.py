#!/usr/bin/env python3
"""Institutional model, source-reference Performance layout and dual SST branding."""
from pathlib import Path
import re, shutil, sys, base64, hashlib

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

asset = Path(__file__).with_name('sst_green_logo.b64')
assert asset.is_file(), 'Missing exact user-supplied SST logo'
brand = root/'assets/branding/sst_green_official.png'
brand.parent.mkdir(parents=True, exist_ok=True)
brand.write_bytes(base64.b64decode(asset.read_text(encoding='ascii').strip()))
assert hashlib.sha256(brand.read_bytes()).hexdigest() == '0d068782c48f34996fe4251bd60c869930f21805b62ab3d8178b0e8b247eb106', 'SST logo not identical to user image'
test_dir=root/'test'
test_dir.mkdir(parents=True,exist_ok=True)
shutil.copyfile(Path(__file__).with_name('report_logo_smoke_test_v329112.dart'),test_dir/'report_logo_smoke_test.dart')

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
shutil.copyfile(Path(__file__).with_name('report_logo_service_v329112.dart'), root/'lib/services/report_logo_service.dart')

def styled(s):
    s=once(s,"import 'report_template_service.dart';",
      "import 'report_template_service.dart';\nimport 'report_logo_service.dart';",'styled logo import')
    s=once(s,
      "    final companyLogo = await _fileImage(\n      '${header['company_logo_path'] ?? ''}',\n    );",
      "    final companyLogo = await ReportLogoService.forCompany(header);",
      'styled logo resolve')
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
    s=once(s,"import 'report_template_service.dart';",
      "import 'report_template_service.dart';\nimport 'report_logo_service.dart';",'performance logo import')
    s=once(s,
      "    final companyLogo = await _fileImage(\n      '${header['company_logo_path'] ?? ''}',\n    );",
      "    final companyLogo = await ReportLogoService.forCompany(header);",
      'performance logo resolve')
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
    end=s.index('  static pw.Widget _sstBadge()',start)
    # The Forum reference has a true three-zone header (logo/title/client).
    # Replace the entire old header, preserving all company identity fields.
    s=s[:start]+r'''  static pw.Widget _header({
    required ReportTemplateDefinition template,
    required pw.MemoryImage? companyLogo,
    required pw.MemoryImage? sstLogo,
    required String company,
    required String worksite,
    required String dateText,
    required String location,
    required String companyCnpj,
    required String companyAddress,
    required String companyCity,
    required String companyUf,
  }) {
    final titleLine = template.headerTitle.trim().isEmpty
        ? 'RELATÓRIO PERFORMANCE'
        : template.headerTitle.trim().toUpperCase();
    final secondLine =
        worksite.trim().isEmpty ? company.toUpperCase() : worksite.toUpperCase();
    final displayAddress = [
      if (companyAddress.trim().isNotEmpty) companyAddress.trim(),
      if (companyCity.trim().isNotEmpty) companyCity.trim(),
      if (companyUf.trim().isNotEmpty) companyUf.trim(),
    ].join(' - ');
    return pw.Container(
      margin: const pw.EdgeInsets.only(bottom: 8),
      child: pw.Column(
        children: [
          pw.Row(
            crossAxisAlignment: pw.CrossAxisAlignment.center,
            children: [
              pw.SizedBox(
                width: 76,
                height: 58,
                child: sstLogo == null
                    ? pw.SizedBox()
                    : pw.Image(sstLogo, fit: pw.BoxFit.contain),
              ),
              pw.Expanded(
                child: pw.Column(
                  children: [
                    pw.Text(titleLine,
                      textAlign: pw.TextAlign.center,
                      style: pw.TextStyle(
                        fontSize: 12.5,
                        fontWeight: pw.FontWeight.bold,
                        color: _blue,
                      ),
                    ),
                    pw.SizedBox(height: 1),
                    pw.Text(secondLine,
                      textAlign: pw.TextAlign.center,
                      style: pw.TextStyle(
                        fontSize: 11.2,
                        fontWeight: pw.FontWeight.bold,
                        color: _blue,
                      ),
                    ),
                  ],
                ),
              ),
              pw.SizedBox(
                width: 76,
                height: 58,
                child: (companyLogo ?? sstLogo) == null
                    ? pw.SizedBox()
                    : pw.Image((companyLogo ?? sstLogo)!, fit: pw.BoxFit.contain),
              ),
            ],
          ),
          pw.SizedBox(height: 6),
          pw.Text('Vistoria realizada em $dateText  |  $location',
            style: pw.TextStyle(fontSize: 7.8, fontWeight: pw.FontWeight.bold),
            textAlign: pw.TextAlign.center,
          ),
          if (companyCnpj.trim().isNotEmpty)
            pw.Text('CNPJ: ' + companyCnpj.trim(),
              style: const pw.TextStyle(fontSize: 7.4),
            ),
          if (displayAddress.isNotEmpty)
            pw.Text('Endereço: $displayAddress',
              textAlign: pw.TextAlign.center,
              style: const pw.TextStyle(fontSize: 7.3),
            ),
          pw.SizedBox(height: 7),
        ],
      ),
    );
  }

'''+s[end:]
    # Two-column report remains photo/caption left, technical findings right,
    # as in the supplied Forum performance reference; no misleading scoring.
    return s

edit('lib/services/performance_report_pdf_service.dart',performance)

def legacy(s):
    s=once(s,"import 'styled_report_pdf_service.dart';",
      "import 'styled_report_pdf_service.dart';\nimport 'report_logo_service.dart';",'legacy logo import')
    s=once(s,
      "    final companyLogo = await _loadImage(\n      header['company_logo_path'] as String?,\n    );",
      "    final companyLogo = await ReportLogoService.forCompany(header);",
      'legacy logo resolve')
    original_logo="'assets/branding/auditar_icon.png',"
    assert s.count(original_logo)==2, 'legacy logo count'
    s=s.replace(original_logo,"'assets/branding/sst_green_official.png',",2)
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

def ronda(s):
    s=once(s,"import 'report_template_service.dart';",
      "import 'report_template_service.dart';\nimport 'report_logo_service.dart';",
      'express round logo resolver import')
    s=once(s,
      "final auditarLogo = await _asset('assets/branding/auditar_icon.png');",
      "final auditarLogo = await _asset('assets/branding/sst_green_official.png');",
      'express round official logo')
    s=once(s,
      "final companyLogo = await _localImage(company.logoPath ?? '');",
      """final companyLogo = await ReportLogoService.forCompany(<String, Object?>{
      'company_id': company.id,
      'company_logo_path': company.logoPath,
    });""",
      'express round company logo resolve')
    start=s.index('                  if (companyLogo != null &&')
    end=s.index('                  pw.SizedBox(height: 70),',start)
    s=s[:start]+"""                  pw.Row(
                    children: [
                      _pdfLogo(auditarLogo, 64, 64),
                      pw.Spacer(),
                      _pdfLogo(companyLogo ?? auditarLogo, 64, 64),
                    ],
                  ),
"""+s[end:]
    start=s.index('  static pw.Widget _header(')
    end=s.index('  static pw.Widget _companyTable(',start)
    s=s[:start]+"""  static pw.Widget _pdfLogo(
    pw.ImageProvider? image,
    double width,
    double height,
  ) => pw.SizedBox(
    width: width,
    height: height,
    child: image == null
        ? pw.SizedBox()
        : pw.Image(image, fit: pw.BoxFit.contain),
  );

  static pw.Widget _header(
    Company company,
    pw.ImageProvider? companyLogo,
    pw.ImageProvider? auditarLogo,
    PdfColor primary,
    String logoMode,
  ) {
    return pw.Container(
      padding: const pw.EdgeInsets.only(bottom: 7),
      decoration: const pw.BoxDecoration(
        border: pw.Border(bottom: pw.BorderSide(color: PdfColors.grey300)),
      ),
      child: pw.Row(
        crossAxisAlignment: pw.CrossAxisAlignment.center,
        children: [
          _pdfLogo(auditarLogo, 47, 47),
          pw.SizedBox(width: 8),
          pw.Expanded(
            child: pw.Column(
              crossAxisAlignment: pw.CrossAxisAlignment.center,
              children: [
                pw.Text(company.name,
                  textAlign: pw.TextAlign.center,
                  style: pw.TextStyle(
                    fontSize: 10, fontWeight: pw.FontWeight.bold,
                    color: primary,
                  ),
                ),
                if ((company.cnpj ?? '').trim().isNotEmpty)
                  pw.Text('CNPJ: ' + (company.cnpj ?? ''),
                    textAlign: pw.TextAlign.center,
                    style: const pw.TextStyle(
                      fontSize: 7.5, color: PdfColors.grey700,
                    ),
                  ),
              ],
            ),
          ),
          pw.SizedBox(width: 8),
          _pdfLogo(companyLogo ?? auditarLogo, 47, 47),
        ],
      ),
    );
  }

"""+s[end:]
    return s

edit('lib/services/express_round_pdf_service.dart',ronda)
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

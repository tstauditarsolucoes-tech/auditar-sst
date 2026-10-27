#!/usr/bin/env python3
from pathlib import Path
import re
import shutil
import sys

root = Path(sys.argv[1])

def read(rel):
    return (root / rel).read_text(encoding='utf-8')

def write(rel, text):
    (root / rel).write_text(text, encoding='utf-8', newline='\n')

def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError('Marcador não localizado: ' + label)
    return text.replace(old, new, 1)

# Versão
pub = read('pubspec.yaml')
pub, n = re.subn(
    r'^version:\s*[^\n]+',
    'version: 3.29.80+222',
    pub,
    count=1,
    flags=re.M,
)
if n != 1:
    raise RuntimeError('Versão não localizada')
write('pubspec.yaml', pub)

# Novo renderer dedicado
src = Path.cwd() / 'build_sources/v3.29.80-performance-report/performance_report_pdf_service.dart'
if not src.exists():
    raise RuntimeError('Fonte do renderer Performance não localizada')
dst = root / 'lib/services/performance_report_pdf_service.dart'
dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(src, dst)

# Biblioteca de modelos
rel = 'lib/services/report_template_service.dart'
c = read(rel)
c = replace_once(
    c,
    "  static const currentTemplateId = 'auditar_atual';\n",
    "  static const currentTemplateId = 'auditar_atual';\n"
    "  static const performanceTemplateId = 'auditar_performance_grid';\n",
    'id modelo performance',
)

anchor = """    ReportTemplateDefinition(
      id: 'auditar_obra',
"""
performance = """    ReportTemplateDefinition(
      id: performanceTemplateId,
      name: 'Performance - Foto + Descrição',
      description:
          'Modelo visual em duas colunas: foto à esquerda e análise técnica à direita, com conclusão e assinatura no fechamento.',
      primaryColor: '#15506F',
      secondaryColor: '#0B8A3D',
      headerTitle: 'RELATÓRIO PERFORMANCE',
      headerStyle: 'performance',
      logoMode: 'cliente',
      footerText: 'Auditar Soluções',
      photoColumns: 1,
      signatureStyle: 'app',
      showCover: false,
      showSummary: false,
      showChecklistDetails: false,
      isBuiltIn: true,
    ),
"""
c = replace_once(c, anchor, performance + anchor, 'template performance built-in')
write(rel, c)

# Roteamento do renderer
rel = 'lib/services/styled_report_pdf_service.dart'
c = read(rel)
c = replace_once(
    c,
    "import 'report_template_service.dart';\n",
    "import 'report_template_service.dart';\n"
    "import 'performance_report_pdf_service.dart';\n",
    'import performance renderer',
)
anchor = """  }) async {
    final db = AppDatabase.instance;
"""
route = """  }) async {
    if (template.id == ReportTemplateService.performanceTemplateId ||
        template.headerStyle == 'performance') {
      return PerformanceReportPdfService.generateInspectionPdf(
        inspectionId,
        header: header,
        template: template,
        executive: executive,
        includeActionPlan: includeActionPlan,
      );
    }

    final db = AppDatabase.instance;
"""
c = replace_once(c, anchor, route, 'roteamento renderer performance')
write(rel, c)

# Garantias
templates = read('lib/services/report_template_service.dart')
styled = read('lib/services/styled_report_pdf_service.dart')
performance_src = read('lib/services/performance_report_pdf_service.dart')

assert 'version: 3.29.80+222' in read('pubspec.yaml')
assert "performanceTemplateId = 'auditar_performance_grid'" in templates
assert "name: 'Performance - Foto + Descrição'" in templates
assert "headerStyle: 'performance'" in templates
assert "PerformanceReportPdfService.generateInspectionPdf" in styled
assert "template.headerStyle == 'performance'" in styled
for marker in [
    'Situação',
    'Risco',
    'Correção',
    'PRIORIDADE',
    'CONCLUSÃO',
    'RESPONSÁVEL TÉCNICO',
    'Vistoria realizada em',
]:
    assert marker in performance_src, f'marcador ausente: {marker}'

print('PERFORMANCE_REPORT_V32980_OK')

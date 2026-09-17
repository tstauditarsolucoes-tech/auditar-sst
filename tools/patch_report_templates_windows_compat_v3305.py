#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else 'app/Auditar_SST_v1_5_dashboard')

# A base Windows tem pequenas diferenças de composição em Configurações.
# Este complemento toca somente Settings/PDF/versionamento; não acessa sync.
settings=root/'lib/screens/settings_screen.dart'
text=settings.read_text(encoding='utf-8')
if "import 'report_template_library_screen.dart';" not in text:
    anchor="import 'login_screen.dart';\n"
    if anchor not in text:
        raise SystemExit('import de login não encontrado no Settings Windows')
    text=text.replace(anchor, anchor+"import 'report_template_library_screen.dart';\n",1)

if 'Biblioteca e editor de modelos de relatório' not in text:
    save_pos=text.find('onPressed: _save')
    if save_pos<0:
        raise SystemExit('botão Salvar configurações não encontrado no Settings Windows')
    button_pos=text.rfind('FilledButton.icon(',0,save_pos)
    if button_pos<0:
        raise SystemExit('início do botão Salvar não encontrado no Settings Windows')
    line_start=text.rfind('\n',0,button_pos)+1
    indent=text[line_start:button_pos]
    block=(
        f"{indent}OutlinedButton.icon(\n"
        f"{indent}  onPressed: () => Navigator.of(context).push(\n"
        f"{indent}    MaterialPageRoute(builder: (_) => const ReportTemplateLibraryScreen()),\n"
        f"{indent}  ),\n"
        f"{indent}  icon: const Icon(Icons.dashboard_customize_outlined),\n"
        f"{indent}  label: Text(\n"
        f"{indent}    Platform.isWindows\n"
        f"{indent}        ? 'Biblioteca e editor de modelos de relatório'\n"
        f"{indent}        : 'Modelos de relatório',\n"
        f"{indent}  ),\n"
        f"{indent}),\n"
        f"{indent}const SizedBox(height: 12),\n"
    )
    text=text[:line_start]+block+text[line_start:]
settings.write_text(text,encoding='utf-8',newline='\n')

pdf=root/'lib/services/pdf_service.dart'
text=pdf.read_text(encoding='utf-8')
if "import 'report_template_service.dart';" not in text:
    class_anchor='class PdfService {\n'
    if class_anchor not in text:
        raise SystemExit('classe PdfService não encontrada no Windows')
    text=text.replace(class_anchor,"import 'report_template_service.dart';\nimport 'styled_report_pdf_service.dart';\n\n"+class_anchor,1)

if 'final reportTemplate = await ReportTemplateService.resolveForHeader(header);' not in text:
    anchor='    final answers = await db.getAnswers(inspectionId);\n'
    if anchor not in text:
        raise SystemExit('ponto de roteamento PDF não encontrado no Windows')
    route="""    final reportTemplate = await ReportTemplateService.resolveForHeader(header);
    if (!reportTemplate.useLegacyRenderer) {
      return StyledReportPdfService.generateInspectionPdf(
        inspectionId,
        header: header,
        template: reportTemplate,
        executive: executive,
        includeActionPlan: includeActionPlan,
      );
    }

"""
    text=text.replace(anchor,route+anchor,1)
pdf.write_text(text,encoding='utf-8',newline='\n')

pub=root/'pubspec.yaml'
text=pub.read_text(encoding='utf-8')
text,count=re.subn(r'^version:\s*[^\n]+','version: 3.29.62+204',text,count=1,flags=re.M)
if count!=1:
    raise SystemExit('version ausente no pubspec Windows')
pub.write_text(text,encoding='utf-8',newline='\n')

print('Compatibilidade Windows dos modelos aplicada somente em Settings/PDF/versionamento.')

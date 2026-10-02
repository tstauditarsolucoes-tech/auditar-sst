#!/usr/bin/env python3
"""Auditar SST v3.29.152 / v3.30.71

Padrão Auditar 3:
- torna o modelo técnico enviado pelo usuário o relatório principal;
- logo Auditar à esquerda e logo CADASTRADA da empresa à direita;
- identidade, foto/texto em duas colunas, conclusão, referências e TST;
- preserva todos os demais modelos;
- não altera banco, sync, auth, HTTP, mídia, IA, Drive ou Apps Script.
"""
from pathlib import Path
import hashlib
import sys

if len(sys.argv) < 3:
    raise SystemExit(
        "uso: patch_auditar3_main_report_v329152_v33071.py "
        "<APP_DIR> <android|windows>"
    )

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
if platform not in ("android", "windows"):
    raise SystemExit("plataforma invalida")

def read(rel):
    return (root / rel).read_text(encoding="utf-8")

def write(rel, value):
    (root / rel).write_text(value, encoding="utf-8", newline="\n")

def once(text, old, new, label):
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: esperado 1, encontrado {count}")
    return text.replace(old, new, 1)

protected = [
    "lib/database.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/auth_service.dart",
    "lib/services/drive_service.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/ai_assistant_service.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
    "painel_web_google_apps_script/ClientPortal.html",
    "painel_web_google_apps_script/ReportEmail.gs",
]
before = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected
}

# 1) Modelo principal: mantém o mesmo ID canônico para não quebrar seleções.
rel = "lib/services/report_template_service.dart"
service = read(rel)
start = service.find(
    "  static const ReportTemplateDefinition currentTemplate = "
    "ReportTemplateDefinition("
)
end = service.find("\n  );", start)
if start < 0 or end < 0:
    raise RuntimeError("currentTemplate nao localizado")
end += len("\n  );")
block = service[start:end]
if "name: 'Padrão Auditar'," not in block:
    raise RuntimeError("nome atual do modelo principal nao localizado")
block = block.replace(
    "name: 'Padrão Auditar',",
    "name: 'Padrão Auditar 3',",
    1,
)
block = block.replace(
    "description: 'Relatório de vistoria técnica com identificação da empresa, evidências à esquerda e descrição/correção à direita.',",
    "description: 'Modelo principal Auditar: logo da empresa cadastrada, evidência à esquerda e análise técnica à direita.',",
    1,
)
service = service[:start] + block + service[end:]
write(rel, service)

# 2) Renderer técnico: seguir o PDF de referência.
rel = "lib/services/auditar_technical_inspection_pdf_service.dart"
pdf = read(rel)

pdf = once(
    pdf,
    "import 'report_template_service.dart';\n",
    "import 'report_template_service.dart';\n"
    "import 'report_logo_service.dart';\n",
    "import logo service",
)

old_identity_vars = """    final activity = _first([
      header['company_activity'],
      header['activity'],
      header['cnae_description'],
    ]);
    final rawDate = DateTime.tryParse('${header['date'] ?? ''}');
"""
new_identity_vars = """    final companies = await db.getCompanies(onlyActive: false);
    final companyId = _first([header['company_id']]);
    Company? companyRecord;
    for (final item in companies) {
      if (item.id == companyId) {
        companyRecord = item;
        break;
      }
    }
    final city = _first([header['company_city'], companyRecord?.city]);
    final uf = _first([header['company_uf'], companyRecord?.uf]);
    final locality = [city, uf]
        .where((value) => value.trim().isNotEmpty)
        .join('/');
    final address = _first([
      header['worksite_address'],
      header['company_address'],
      header['address'],
    ]);
    final rawDate = DateTime.tryParse('${header['date'] ?? ''}');
"""
pdf = once(pdf, old_identity_vars, new_identity_vars, "identidade empresa")

old_logos = """    final auditarLogo = await _asset('assets/branding/auditar_logo.jpg') ??
        await _asset('assets/branding/auditar_icon.png');
    final sstLogo = await _asset('assets/branding/sst_green_official.png');
    final techSignature =
"""
new_logos = """    final auditarLogo = await _asset('assets/branding/auditar_logo.jpg') ??
        await _asset('assets/branding/auditar_icon.png');
    // O espaço da direita pertence exclusivamente à logo cadastrada da
    // empresa. Nunca usar uma logo fixa de cliente e nunca repetir a Auditar
    // como substituta nesse espaço.
    final companyLogo = await ReportLogoService.forCompany(header);
    final techSignature =
"""
pdf = once(pdf, old_logos, new_logos, "logos cabecalho")

old_correction = """      final priority = _first([
        if (linked.isNotEmpty) linked.first.priority,
        nc?.classification,
      ]);

      // Itens conformes"""
new_correction = """      final priority = _first([
        if (linked.isNotEmpty) linked.first.priority,
        nc?.classification,
      ]);
      final location = _first([
        if (linked.isNotEmpty) linked.first.locationDetail,
        header['sector_name'],
        header['area'],
        header['worksite_name'],
      ]);

      // Itens conformes"""
pdf = once(pdf, old_correction, new_correction, "local do achado")

old_issue = """        _IssueData(
          title: _first([
            answer.questionCategory,
            answer.questionText,
            'Item avaliado',
          ]),
          caption: answer.questionText.trim(),
          situation: situation,
          risk: risk,
          correction: correction,
          priority: priority,
          reference: answer.questionReference.trim(),
          status: answer.status.trim(),
          photos: images,
        ),"""
new_issue = """        _IssueData(
          title: _first([
            answer.questionText,
            answer.questionCategory,
            'Item avaliado',
          ]),
          caption: answer.questionText.trim() == _first([
            answer.questionText,
            answer.questionCategory,
            'Item avaliado',
          ])
              ? ''
              : answer.questionText.trim(),
          location: location,
          situation: situation,
          risk: risk,
          correction: correction,
          priority: priority,
          reference: answer.questionReference.trim(),
          status: answer.status.trim(),
          photos: images,
        ),"""
pdf = once(pdf, old_issue, new_issue, "dados do achado")

old_widgets = """      _identityBox(
        company: company,
        cnpj: cnpj,
        activity: activity,
        dateText: dateText,
        reportNumber: reportNumber,
      ),
"""
new_widgets = """      _identityBox(
        company: company,
        cnpj: cnpj,
        locality: locality,
        address: address,
        dateText: dateText,
      ),
"""
pdf = once(pdf, old_widgets, new_widgets, "chamada identidade")

old_before_conclusion = """    widgets.addAll([
      pw.SizedBox(height: 14),
"""
new_before_conclusion = """    final generalReferences = issueData
        .map((item) => item.reference.trim())
        .where((value) => value.isNotEmpty)
        .toSet()
        .join(' • ');

    widgets.addAll([
      pw.SizedBox(height: 14),
"""
pdf = once(pdf, old_before_conclusion, new_before_conclusion, "referencias gerais")

old_conclusion_tail = """      pw.Text(
        conclusion.isNotEmpty
            ? conclusion
            : 'Este relatório registra as condições documentadas na data da vistoria. '
                'As correções identificadas devem ser acompanhadas e verificadas em nova inspeção. '
                'O documento não comprova regularização posterior.',
        textAlign: pw.TextAlign.justify,
        style: const pw.TextStyle(fontSize: 9, lineSpacing: 2),
      ),
      pw.SizedBox(height: 34),
"""
new_conclusion_tail = """      pw.Text(
        conclusion.isNotEmpty
            ? conclusion
            : 'Priorizar as correções registradas neste relatório e verificar '
                'as medidas adotadas em nova visita.',
        textAlign: pw.TextAlign.justify,
        style: const pw.TextStyle(fontSize: 9, lineSpacing: 2),
      ),
      pw.SizedBox(height: 7),
      pw.Text(
        'Relatório elaborado com os registros fotográficos e as informações '
        'fornecidas na vistoria. Não confirma regularização posterior.',
        textAlign: pw.TextAlign.justify,
        style: const pw.TextStyle(fontSize: 7.8, lineSpacing: 1.7),
      ),
      if (generalReferences.isNotEmpty) ...[
        pw.SizedBox(height: 5),
        pw.RichText(
          text: pw.TextSpan(
            children: [
              pw.TextSpan(
                text: 'Referências gerais: ',
                style: pw.TextStyle(
                  fontSize: 7.8,
                  fontWeight: pw.FontWeight.bold,
                ),
              ),
              pw.TextSpan(
                text: generalReferences,
                style: const pw.TextStyle(fontSize: 7.8),
              ),
            ],
          ),
        ),
      ],
      pw.SizedBox(height: 34),
"""
pdf = once(pdf, old_conclusion_tail, new_conclusion_tail, "conclusao padrao")

old_header_call = """        header: (context) => _header(
          auditarLogo: auditarLogo,
          sstLogo: sstLogo,
          company: company,
          cnpj: cnpj,
          dateText: dateText,
        ),
        footer: (context) => _footer(context),
"""
new_header_call = """        header: (context) => _header(
          auditarLogo: auditarLogo,
          companyLogo: companyLogo,
          company: company,
          cnpj: cnpj,
        ),
        footer: (context) => _footer(context, auditarLogo),
"""
pdf = once(pdf, old_header_call, new_header_call, "header footer calls")

header_start = pdf.find("  static pw.Widget _header({")
identity_start = pdf.find("  static pw.Widget _identityBox({", header_start)
if header_start < 0 or identity_start < 0:
    raise RuntimeError("bloco header/identity nao localizado")
new_header = r"""  static pw.Widget _header({
    required pw.MemoryImage? auditarLogo,
    required pw.MemoryImage? companyLogo,
    required String company,
    required String cnpj,
  }) =>
      pw.Column(
        children: [
          pw.Row(
            crossAxisAlignment: pw.CrossAxisAlignment.center,
            children: [
              _logo(auditarLogo, 76, 50),
              pw.Expanded(
                child: pw.Column(
                  children: [
                    pw.Text(
                      'RELATÓRIO DE VISTORIA TÉCNICA',
                      textAlign: pw.TextAlign.center,
                      style: pw.TextStyle(
                        color: _navy,
                        fontSize: 12.5,
                        fontWeight: pw.FontWeight.bold,
                      ),
                    ),
                    pw.SizedBox(height: 2),
                    pw.Text(
                      company.toUpperCase(),
                      textAlign: pw.TextAlign.center,
                      style: pw.TextStyle(
                        color: _navy,
                        fontSize: 11,
                        fontWeight: pw.FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
              _logo(companyLogo, 58, 52),
            ],
          ),
          pw.SizedBox(height: 6),
          pw.Text(
            [
              company.toUpperCase(),
              if (cnpj.isNotEmpty) 'CNPJ: $cnpj',
            ].join('  |  '),
            textAlign: pw.TextAlign.center,
            style: pw.TextStyle(
              fontSize: 7.4,
              fontWeight: pw.FontWeight.bold,
            ),
          ),
          pw.SizedBox(height: 7),
          pw.Container(height: .6, color: _line),
          pw.SizedBox(height: 8),
        ],
      );

"""
pdf = pdf[:header_start] + new_header + pdf[identity_start:]

identity_start = pdf.find("  static pw.Widget _identityBox({")
issue_start = pdf.find("  static pw.Widget _issueBlock(", identity_start)
if identity_start < 0 or issue_start < 0:
    raise RuntimeError("identity/issue nao localizado")
new_identity = r"""  static pw.Widget _identityBox({
    required String company,
    required String cnpj,
    required String locality,
    required String address,
    required String dateText,
  }) =>
      pw.Container(
        decoration: pw.BoxDecoration(
          border: pw.Border.all(color: _line, width: .6),
        ),
        padding: const pw.EdgeInsets.all(8),
        child: pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            pw.Text(
              'IDENTIFICAÇÃO DA EMPRESA',
              style: pw.TextStyle(
                color: _navy,
                fontSize: 9,
                fontWeight: pw.FontWeight.bold,
              ),
            ),
            pw.SizedBox(height: 6),
            pw.Row(
              children: [
                pw.Expanded(child: _labelValue('RAZÃO SOCIAL', company)),
                pw.SizedBox(width: 10),
                pw.Expanded(child: _labelValue('CNPJ', cnpj)),
              ],
            ),
            pw.SizedBox(height: 4),
            pw.Row(
              children: [
                pw.Expanded(child: _labelValue('LOCALIDADE', locality)),
                pw.SizedBox(width: 10),
                pw.Expanded(
                  child: _labelValue('DATA DA VISTORIA', dateText),
                ),
              ],
            ),
            pw.SizedBox(height: 4),
            _labelValue('ENDEREÇO COMPLETO', address),
          ],
        ),
      );

"""
pdf = pdf[:identity_start] + new_identity + pdf[issue_start:]

pdf = once(
    pdf,
    """                  pw.SizedBox(height: 7),
                  if (issue.situation.isNotEmpty)
                    _paragraph('Situação', issue.situation),""",
    """                  pw.SizedBox(height: 7),
                  if (issue.location.isNotEmpty)
                    _paragraph('Local', issue.location),
                  if (issue.situation.isNotEmpty)
                    _paragraph('Situação', issue.situation),""",
    "local no bloco",
)
pdf = pdf.replace(
    """                  if (issue.reference.isNotEmpty)
                    _paragraph('Referência', issue.reference),
""",
    "",
    1,
)

pdf = once(
    pdf,
    "'RESPONSÁVEL TÉCNICO',",
    "'TÉCNICO EM SEGURANÇA DO TRABALHO',",
    "titulo assinatura",
)

footer_start = pdf.find("  static pw.Widget _footer(")
logo_start = pdf.find("  static pw.Widget _logo(", footer_start)
if footer_start < 0 or logo_start < 0:
    raise RuntimeError("footer/logo nao localizado")
new_footer = r"""  static pw.Widget _footer(
    pw.Context context,
    pw.MemoryImage? auditarLogo,
  ) =>
      pw.Row(
        crossAxisAlignment: pw.CrossAxisAlignment.end,
        children: [
          pw.Expanded(child: pw.SizedBox()),
          _logo(auditarLogo, 48, 26),
          pw.Expanded(
            child: pw.Align(
              alignment: pw.Alignment.centerRight,
              child: pw.Text(
                'Página ${context.pageNumber}/${context.pagesCount}',
                style: const pw.TextStyle(
                  fontSize: 6.8,
                  color: PdfColors.grey700,
                ),
              ),
            ),
          ),
        ],
      );

"""
pdf = pdf[:footer_start] + new_footer + pdf[logo_start:]

pdf = once(
    pdf,
    """  final String caption;
  final String situation;""",
    """  final String caption;
  final String location;
  final String situation;""",
    "campo location",
)
pdf = once(
    pdf,
    """    required this.caption,
    required this.situation,""",
    """    required this.caption,
    required this.location,
    required this.situation,""",
    "constructor location",
)

write(rel, pdf)

# 3) Versão.
rel = "pubspec.yaml"
pub = read(rel)
old_version, new_version = (
    ("3.29.151+293", "3.29.152+294")
    if platform == "android"
    else ("3.30.70+257", "3.30.71+258")
)
marker = "version: " + old_version
if pub.count(marker) != 1:
    raise RuntimeError("versao esperada ausente: " + old_version)
write(rel, pub.replace(marker, "version: " + new_version, 1))

changed = [
    name for name, digest in before.items()
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

final_service = read("lib/services/report_template_service.dart")
final_pdf = read("lib/services/auditar_technical_inspection_pdf_service.dart")

assert "name: 'Padrão Auditar 3'" in final_service
assert "headerStyle: 'auditar_vistoria_tecnica'" in final_service
assert "ReportLogoService.forCompany(header)" in final_pdf
assert "_logo(companyLogo, 58, 52)" in final_pdf
assert "IDENTIFICAÇÃO DA EMPRESA" in final_pdf
assert "RAZÃO SOCIAL" in final_pdf
assert "LOCALIDADE" in final_pdf
assert "DATA DA VISTORIA" in final_pdf
assert "ENDEREÇO COMPLETO" in final_pdf
assert "_paragraph('Local', issue.location)" in final_pdf
assert "_paragraph('Situação', issue.situation)" in final_pdf
assert "_paragraph('Risco', issue.risk)" in final_pdf
assert "_paragraph('Correção', issue.correction)" in final_pdf
assert "PRIORIDADE:" in final_pdf
assert "Referências gerais:" in final_pdf
assert "TÉCNICO EM SEGURANÇA DO TRABALHO" in final_pdf
assert "assets/branding/sst_green_official.png" not in final_pdf
assert "version: " + new_version in read("pubspec.yaml")

print("PADRAO_AUDITAR_3_MAIN_REPORT_OK", platform, new_version)
print("COMPANY_REGISTERED_LOGO_ONLY_OK")
print("SYNC_DB_AUTH_HTTP_MEDIA_AI_DRIVE_GS_BYTE_IDENTICAL_OK")

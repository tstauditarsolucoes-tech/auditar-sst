#!/usr/bin/env python3
from pathlib import Path
import hashlib
import re
import shutil
import sys

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
assert platform in ("android", "windows")
repo = Path(__file__).resolve().parent.parent

def read(rel):
    return (root / rel).read_text(encoding="utf-8")

def write(rel, value):
    (root / rel).write_text(value, encoding="utf-8", newline="\n")

protected = [
    "lib/database.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/auth_service.dart",
    "lib/services/drive_service.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/ai_assistant_service.dart",
    "lib/services/auditar_technical_inspection_pdf_service.dart",
    "lib/services/auditar_standard2_pdf_service.dart",
    "lib/services/auditar_standard3_pdf_service.dart",
    "lib/services/report_logo_service.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
    "painel_web_google_apps_script/ClientPortal.html",
    "painel_web_google_apps_script/ReportEmail.gs",
]
before = {
    p: hashlib.sha256((root / p).read_bytes()).hexdigest()
    for p in protected
}

# ---------------------------------------------------------------------------
# 1) Ronda UI: somente apresentação. Nenhuma chamada/rota/modelo da IA muda.
# ---------------------------------------------------------------------------
screen_rel = "lib/screens/express_round_screen.dart"
screen = read(screen_rel)

for old, new in [
    ("Resumo da Ronda Expressa", "Resumo da vistoria"),
    ("'Não conformidades'", "'Não conformes'"),
    ("'Conformidades'", "'Conformes'"),
    ("'Recorrentes'", "'Poss. recorrências'"),
    ("IA - revisar toda a ronda", "IA · Revisar conclusão"),
    ("IA · revisar a vistoria e conclusão", "IA · Revisar conclusão"),
    ("Relatório fotográfico - estilo Performance/Quality", "Gerar relatório de vistoria"),
    ("Relatório técnico - situação, riscos e recomendações", "Relatório técnico detalhado"),
    ("Conclusão da IA revisada e pronta para entrar no relatório.", "Conclusão revisada e pronta para o relatório."),
    ("Continuar para a conclusão", "Revisar conclusão"),
    ("Revisão da ronda pela IA", "Revisão técnica da vistoria"),
    (
        "A análise abaixo é apoio ao responsável técnico. Revise antes de emitir o PDF.",
        "A IA preparou uma síntese dos registros. Revise o conteúdo técnico antes de emitir o PDF.",
    ),
]:
    screen = screen.replace(old, new)

screen = screen.replace(
    "? 'IA analisando foto • ${_aiPhotoElapsedSeconds}s'",
    "? (_aiPhotoElapsedSeconds < 8 "
    "? 'Preparando foto para análise...' "
    ": _aiPhotoElapsedSeconds < 40 "
    "? 'IA analisando a evidência...' "
    ": _aiPhotoElapsedSeconds < 55 "
    "? 'Quase concluindo...' "
    ": 'Análise em andamento...')",
)

start = screen.find("  List<Widget> _reviewWidgets(")
if start < 0:
    raise RuntimeError("_reviewWidgets ausente")
next_method = re.search(
    r"\n  (?:Future<[^\n]+>|Future<void>|void|Widget|String|int|bool|"
    r"Map<[^\n]+>|List<[^\n]+>)\s+_[A-Za-z0-9_]+\(",
    screen[start + 10:],
)
if not next_method:
    raise RuntimeError("fim de _reviewWidgets ausente")
end = start + 10 + next_method.start() + 1

clean_review = r'''  List<Widget> _reviewWidgets(Map<String, dynamic> data) {
    String text(List<String> keys) {
      for (final key in keys) {
        final value = data[key];
        if (value is String && value.trim().isNotEmpty) return value.trim();
        if (value is List) {
          final joined = value
              .whereType<String>()
              .map((item) => item.trim())
              .where((item) => item.isNotEmpty)
              .join('\n');
          if (joined.isNotEmpty) return joined;
        }
      }
      return '';
    }

    Widget card(String title, String body) => Container(
          width: double.infinity,
          margin: const EdgeInsets.only(bottom: 10),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: const Color(0xFFF7F9FC),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: const Color(0xFFD9E0EA)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontWeight: FontWeight.w800,
                  color: AuditarBrand.navy,
                ),
              ),
              const SizedBox(height: 5),
              Text(body, style: const TextStyle(height: 1.35)),
            ],
          ),
        );

    String first(Map<String, dynamic> item, List<String> keys) {
      for (final key in keys) {
        final raw = item[key];
        if (raw is String) {
          final value = raw.trim();
          if (value.isNotEmpty && value.toLowerCase() != 'null') return value;
        }
        if (raw is num || raw is bool) return '$raw';
      }
      return '';
    }

    final out = <Widget>[];
    final conclusion = text(const [
      'finalConclusion',
      'conclusion',
      'conclusao',
      'conclusaoFinal',
      'executiveSummary',
      'managementSummary',
      'summary',
    ]);
    final critical = text(const [
      'criticalSummary',
      'prioritySummary',
      'mainRisks',
      'criticalFindings',
    ]);
    final notes = text(const [
      'generalNotes',
      'technicalSummary',
      'overview',
    ]);
    final references = text(const [
      'likelyReferences',
      'references',
      'probableReferences',
      'normativeReferences',
    ]);
    final limitations = text(const [
      'limitations',
      'validationNotes',
      'checksRequired',
    ]);

    if (conclusion.isNotEmpty) {
      out.add(card('Conclusão sugerida', conclusion));
    }
    if (critical.isNotEmpty && critical != conclusion) {
      out.add(card('Pontos prioritários', critical));
    }
    if (notes.isNotEmpty &&
        notes != conclusion &&
        notes != critical &&
        notes.length <= 1200) {
      out.add(card('Resumo técnico', notes));
    }
    if (references.isNotEmpty) {
      out.add(card('Referências para conferência', references));
    }
    if (limitations.isNotEmpty) {
      out.add(card('Pontos para validação técnica', limitations));
    }

    final rawActions = data['actionPlanSuggestions'] ??
        data['actionPlan'] ??
        data['actions'] ??
        data['suggestedActions'];
    if (rawActions is List) {
      final actions = rawActions.whereType<Map>().take(8).toList();
      if (actions.isNotEmpty) {
        out.add(
          const Padding(
            padding: EdgeInsets.only(top: 2, bottom: 7),
            child: Text(
              'Ações sugeridas',
              style: TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.w800,
                color: AuditarBrand.navy,
              ),
            ),
          ),
        );
      }
      for (var i = 0; i < actions.length; i++) {
        final action = Map<String, dynamic>.from(actions[i]);
        final finding = first(
          action,
          const ['nonConformity', 'finding', 'description', 'title'],
        );
        final location = first(
          action,
          const ['locationDetail', 'location', 'sector'],
        );
        final correction = first(
          action,
          const ['correctiveAction', 'recommendation','action','immediateAction'],
       );
        final responsible = first(
          action,
          const ['responsible', 'responsibleProfile', 'owner'],
        );
        final priority = first(action, const ['priority']);
        final deadline = first(
          action,
          const ['suggestedDeadlineDays', 'deadlineDays'],
        );

        final lines = <String>[
          if (finding.isNotEmpty) finding,
          if (location.isNotEmpty) 'Local: $location',
          if (correction.isNotEmpty) 'Correção: $correction',
          if (responsible.isNotEmpty) 'Responsável sugerido: $responsible',
          if (priority.isNotEmpty) 'Prioridade: $priority',
          if (deadline.isNotEmpty) 'Prazo sugerido: $deadline dia(s)',
        ];
        if (lines.isNotEmpty) {
          out.add(card('Ação ${i + 1}', lines.join('\n')));
        }
      }
    }

    return out.isEmpty
        ? const [
            Text(
              'Revisão concluída sem conteúdo textual estruturado para exibição.',
            ),
          ]
        : out;
  }
'''

screen = screen[:start] + clean_review + screen[end:]
write(screen_rel, screen)

# ------------------------------------------------------------------------------
# 2) Padrão Auditar 3 da Ronda: renderer isolado, sem destruir modelos antigos.
# ---------------------------------------------------------------------------
source = repo / "feature_sources/ronda_standard3_pdf_service_v329153.dart"
if not source.exists():
    raise RuntimeError("renderer Ronda Padrão Auditar 3 ausente")
shutil.copyfile(source, root / "lib/services/ronda_standard3_pdf_service.dart")

pdf_rel = "lib/services/express_round_pdf_service.dart"
pdf = read(pdf_rel)

import_line = "import 'ronda_standard3_pdf_service.dart';\n"
if import_line not in pdf:
    anchor = "import 'report_template_service.dart';\n"
    if anchor not in pdf:
        raise RuntimeError("import report_template_service ausente")
    pdf = pdf.replace(anchor, anchor + import_line, 1)

signature = re.search(
    r"static\s+Future<[^\n{]+>\s+generate\s*\((?P<params>.*?)\)\s*async\s*\{",
    pdf,
    re.S,
)
if not signature:
    raise RuntimeError("ExpressRoundPdfService.generate ausente")
params = signature.group("params")

company_match = re.search(r"\bCompany\s+(\w+)", params)
records_match = re.search(r"\bList\s*<\s*SstRecord\s*>\s+(\w+)", params)
template_match = re.search(
    r"\bReportTemplateDefinition(\?)?\s+(\w+)",
    params,
)
conclusion_match = re.search(
    r"\bString(?:\?)?\s+(\w*[Cc]onclusion\w*)",
    params,
)
if not company_match or not records_match or not template_match:
    raise RuntimeError("assinatura da Ronda sem company/records/template")

company_var = company_match.group(1)
records_var = records_match.group(1)
template_var = template_match.group(2)
template_nullable = template_match.group(1) == "?"
conclusion_var = conclusion_match.group(1) if conclusion_match else "''"

access = f"{template_var}{'?.' if template_nullable else '.'}"
condition = (
    f"{access}headerStyle == 'auditar_padrao_3' || "
    f"{access}name == 'Padrão Auditar 3'"
)

route = f'''
    // Renderer isolado da Ronda para o Padrão Auditar 3.
    // Demais modelos continuam no renderer anterior.
    if ({condition}) {{
      return RondaStandard3PdfService.generate(
        company: {company_var},
        records: {records_var},
        conclusion: {conclusion_var},
      );
    }}
'''

body_start = signature.end()
near = pdf[body_start:body_start + 2200]
if "RondaStandard3PdfService.generate(" not in near:
    pdf = pdf[:body_start] + route + pdf[body_start:]

write(pdf_rel, pdf)

template_rel = "lib/services/report_template_service.dart"
templates = read(template_rel)
templates = templates.replace(
    "name: 'Padrão Auditar anterior'",
    "name: 'Padrão Auditar (legado)'",
)
write(template_rel, templates)

pub_rel = "pubspec.yaml"
pub = read(pub_rel)
old_version, new_version = (
    ("3.29.152+294", "3.29.153+295")
    if platform == "android"
    else ("3.30.71+258", "3.30.72+259")
)
marker = "version: " + old_version
if pub.count(marker) != 1:
    raise RuntimeError("versão base esperada ausente: " + old_version)
write(pub_rel, pub.replace(marker, "version: " + new_version, 1))

changed = [
    p
    for p, digest in before.items()
    if hashlib.sha256((root / p).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit("PROTECTED_CORE_OR_AI_MODIFIED: " + repr(changed))

final_screen = read(screen_rel)
final_pdf = read(pdf_rel)
final_ronda3 = read("lib/services/ronda_standard3_pdf_service.dart")

assert "Resumo da vistoria" in final_screen
assert "Pontos prioritários" in final_screen
assert "Ações sugeridas" in final_screen
assert "Gerar relatório de vistoria" in final_screen
assert "General Notes" not in final_screen
assert "Critical Summary" not in final_screen
assert "Action Plan Suggestions" not in final_screen
assert "RondaStandard3PdfService.generate(" in final_pdf
assert "RELATÓRIO DE VISTORIA TÉCNICA" in final_ronda3
assert "IDENTIFICAÇÃO DA EMPRESA" in final_ronda3
assert "_paragraph('Situação'" in final_ronda3
assert "_paragraph('Risco'" in final_ronda3
assert "_paragraph('Correção'" in final_ronda3
assert "PRIORIDADE:" in final_ronda3
assert "_logo(companyLogo, 70, 50)" in final_ronda3
assert "companyLogo ?? auditarLogo" not in final_ronda3

print("RONDA_UI_REVIEW_CLEAN_OK")
print("RONDA_STANDARD3_ROUTING_OK", platform,new_version)
print("AI_SYNC_DB_AUTH_HTTP_MEDIA_DRIVE_GS_PREVIOUS_REPORTS_BYTE_IDENTICAL_OK")

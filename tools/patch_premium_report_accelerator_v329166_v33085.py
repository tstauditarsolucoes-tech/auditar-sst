#!/usr/bin/env python3
"""Auditar SST v3.29.166 / v3.30.85 — captura rápida e relatório Premium.

Amplia sugestões, remove o texto visual "sem internet" e adiciona indicadores
não bloqueantes de qualidade na Ronda e na Vistoria. IA permanece disponível.
Não altera schema, sync, auth, HTTP, mídia/Drive, IA, Apps Script ou PDF.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv) < 3:
    raise SystemExit("uso: patch_premium_report_accelerator_v329166_v33085.py <APP_DIR> <android|windows>")

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
repo = Path(__file__).resolve().parents[1]
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
    "lib/models.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/auth_service.dart",
    "lib/services/drive_service.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/ai_assistant_service.dart",
    "lib/services/offline_report_knowledge_service.dart",
    "lib/services/auditar_technical_inspection_pdf_service.dart",
    "lib/services/auditar_standard2_pdf_service.dart",
    "lib/services/auditar_standard3_pdf_service.dart",
    "lib/services/ronda_standard3_pdf_service.dart",
    "lib/services/express_round_pdf_service.dart",
    "lib/services/report_template_service.dart",
    "lib/services/styled_report_pdf_service.dart",
    "lib/services/report_logo_service.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
    "painel_web_google_apps_script/ClientPortal.html",
    "painel_web_google_apps_script/ReportEmail.gs",
]
before = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected if (root / name).exists()
}

copies = [
    ("feature_sources/offline_report_inline_suggestions_v329166.dart",
     "lib/widgets/offline_report_inline_suggestions.dart"),
    ("feature_sources/offline_report_inline_suggestions_test_v329166.dart",
     "test/offline_report_inline_suggestions_test.dart"),
]
for source, target in copies:
    src = repo / source
    dst = root / target
    if not src.exists():
        raise RuntimeError("fonte ausente: " + source)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)

# Ronda: indicador de qualidade sem criar etapa obrigatória.
rel = "lib/screens/express_round_screen.dart"
s = read(rel)
anchor = "  Future<void> _finish() async {\n"
if "int get _roundReportQualityScore" not in s:
    methods = r'''  bool _roundRecordNeedsPremiumReview(SstRecord record) {
    final payload = record.payload;
    if (payload['positivePractice'] == true) return false;
    return '${payload['findingType'] ?? ''}' != 'CONFORMIDADE';
  }

  int get _roundReportQualityScore {
    final findings = roundRecords.where(_roundRecordNeedsPremiumReview).toList();
    if (roundRecords.isEmpty) return 0;
    if (findings.isEmpty) return 100;
    var possible = 0;
    var complete = 0;
    for (final record in findings) {
      final payload = record.payload;
      for (final value in <String>[
        '${payload['description'] ?? ''}',
        '${payload['risk'] ?? ''}',
        '${payload['recommendation'] ?? ''}',
      ]) {
        possible++;
        if (value.trim().isNotEmpty) complete++;
      }
      possible++;
      final hasPhoto =
          '${payload['photoPath'] ?? ''}'.trim().isNotEmpty ||
          '${payload['photoPath2'] ?? ''}'.trim().isNotEmpty;
      if (hasPhoto) complete++;
    }
    return possible == 0 ? 100 : ((complete * 100) / possible).round();
  }

  List<String> get _roundReportQualityWarnings {
    var noPhoto = 0;
    var noRisk = 0;
    var noRecommendation = 0;
    for (final record in roundRecords.where(_roundRecordNeedsPremiumReview)) {
      final payload = record.payload;
      if ('${payload['photoPath'] ?? ''}'.trim().isEmpty &&
          '${payload['photoPath2'] ?? ''}'.trim().isEmpty) {
        noPhoto++;
      }
      if ('${payload['risk'] ?? ''}'.trim().isEmpty) noRisk++;
      if ('${payload['recommendation'] ?? ''}'.trim().isEmpty) {
        noRecommendation++;
      }
    }
    return <String>[
      if (noPhoto > 0) '$noPhoto achado(s) sem evidência fotográfica.',
      if (noRisk > 0) '$noRisk achado(s) sem risco preenchido.',
      if (noRecommendation > 0)
        '$noRecommendation achado(s) sem recomendação preenchida.',
    ];
  }

'''
    s = once(s, anchor, methods + anchor, "qualidade Ronda")

setores = "                      _summaryChip('Setores', _sectorCount, AuditarBrand.navy),\n"
if "Qualidade ${_roundReportQualityScore}%" not in s:
    quality_chip = setores + """                      Chip(
                        avatar: const Icon(
                          Icons.workspace_premium_outlined,
                          size: 16,
                        ),
                        label: Text('Qualidade ${_roundReportQualityScore}%'),
                      ),
"""
    s = once(s, setores, quality_chip, "chip qualidade Ronda")

conclusion_anchor = """                  const SizedBox(height: 12),
                  if (roundAiConclusion.trim().isNotEmpty) ...[
"""
if "Conferir para um relatório mais completo" not in s:
    review_box = """                  const SizedBox(height: 12),
                  if (_roundReportQualityWarnings.isNotEmpty) ...[
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFFF7E6),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: const Color(0xFFF0C36A)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Conferir para um relatório mais completo',
                            style: TextStyle(fontWeight: FontWeight.w800),
                          ),
                          const SizedBox(height: 5),
                          ..._roundReportQualityWarnings.take(3).map(
                            (item) => Padding(
                              padding: const EdgeInsets.only(bottom: 3),
                              child: Text('• ' + item),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),
                  ],
                  if (roundAiConclusion.trim().isNotEmpty) ...[
"""
    s = once(s, conclusion_anchor, review_box, "avisos qualidade Ronda")
write(rel, s)

# Tela de relatório: calcula qualidade usando apenas dados existentes.
rel = "lib/screens/report_screen.dart"
s = read(rel)
state_anchor = "  int na = 0;\n\n"
if "int reportQualityScore = 0;" not in s:
    s = once(s, state_anchor, """  int na = 0;
  int reportQualityScore = 0;
  List<String> reportQualityWarnings = const [];

""", "estado qualidade relatório")

load_anchor = """    final photoAiState = await InspectionPhotoAiQueueService.state(
      widget.inspectionId,
    );

    if (!mounted) return;
"""
if "computedReportQuality" not in s:
    quality_load = """    final photoAiState = await InspectionPhotoAiQueueService.state(
      widget.inspectionId,
    );

    final premiumFindings = answers
        .where((e) => e.status == 'Não Conforme' || e.status == 'Parcial')
        .toList();
    var qualityPossible = 0;
    var qualityComplete = 0;
    var qualityNoPhoto = 0;
    var qualityNoDescription = 0;
    var qualityNoRisk = 0;
    var qualityNoRecommendation = 0;
    var qualityNoReference = 0;
    for (final answer in premiumFindings) {
      qualityPossible += 5;
      if (answer.observation.trim().isNotEmpty) {
        qualityComplete++;
      } else {
        qualityNoDescription++;
      }
      if (answer.riskIdentified.trim().isNotEmpty) {
        qualityComplete++;
      } else {
        qualityNoRisk++;
      }
      if (answer.recommendation.trim().isNotEmpty) {
        qualityComplete++;
      } else {
        qualityNoRecommendation++;
      }
      if (answer.questionReference.trim().isNotEmpty) {
        qualityComplete++;
      } else {
        qualityNoReference++;
      }
      final photos = await db.getPhotosForAnswer(answer.id);
      var hasPhoto = false;
      for (final photo in photos) {
        if (photo.path.trim().isNotEmpty && await File(photo.path).exists()) {
          hasPhoto = true;
          break;
        }
      }
      if (hasPhoto) {
        qualityComplete++;
      } else {
        qualityNoPhoto++;
      }
    }
    final computedReportQuality = premiumFindings.isEmpty
        ? (answers.isEmpty ? 0 : 100)
        : ((qualityComplete * 100) / qualityPossible).round();
    final computedQualityWarnings = <String>[
      if (qualityNoDescription > 0)
        '$qualityNoDescription achado(s) sem descrição.',
      if (qualityNoRisk > 0)
        '$qualityNoRisk achado(s) sem risco identificado.',
      if (qualityNoRecommendation > 0)
        '$qualityNoRecommendation achado(s) sem recomendação.',
      if (qualityNoReference > 0)
        '$qualityNoReference achado(s) sem referência normativa.',
      if (qualityNoPhoto > 0)
        '$qualityNoPhoto achado(s) sem foto disponível neste aparelho.',
    ];

    if (!mounted) return;
"""
    s = once(s, load_anchor, quality_load, "calculo qualidade relatório")

set_anchor = """      na = answers.where((e) => e.status == 'Não se aplica').length;
      driveLinked = enabled == 'true';
"""
if "reportQualityScore = computedReportQuality;" not in s:
    s = once(s, set_anchor, """      na = answers.where((e) => e.status == 'Não se aplica').length;
      reportQualityScore = computedReportQuality;
      reportQualityWarnings = computedQualityWarnings;
      driveLinked = enabled == 'true';
""", "atribuir qualidade relatório")

if "Qualidade do relatório" not in s:
    marker = "Análise de fotos no final"
    pos = s.find(marker)
    if pos < 0:
        raise RuntimeError("card de analise de fotos nao localizado")
    card_start = s.rfind("          Card(", 0, pos)
    if card_start < 0:
        raise RuntimeError("inicio do card de fotos nao localizado")
    quality_card = r'''          Card(
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
              side: BorderSide(
                color: reportQualityScore >= 85
                    ? AuditarBrand.green.withOpacity(.35)
                    : Colors.orange.shade200,
              ),
            ),
            child: Padding(
              padding: const EdgeInsets.all(15),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(
                        Icons.workspace_premium_outlined,
                        color: AuditarBrand.navy,
                      ),
                      const SizedBox(width: 9),
                      Expanded(
                        child: Text(
                          'Qualidade do relatório • $reportQualityScore%',
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w800,
                            color: AuditarBrand.navyDark,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  LinearProgressIndicator(
                    value: reportQualityScore / 100,
                    minHeight: 7,
                    borderRadius: BorderRadius.circular(99),
                  ),
                  const SizedBox(height: 8),
                  if (reportQualityWarnings.isEmpty)
                    const Text(
                      'Os achados principais estão completos para a emissão. '
                      'A IA continua disponível para revisão e refinamento.',
                    )
                  else ...[
                    const Text(
                      'Antes de enviar, vale conferir:',
                      style: TextStyle(fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 5),
                    ...reportQualityWarnings.take(4).map(
                      (item) => Padding(
                        padding: const EdgeInsets.only(bottom: 3),
                        child: Text('• ' + item),
                      ),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'A emissão não é bloqueada; esta conferência serve para '
                      'manter o padrão Premium do relatório.',
                      style: TextStyle(fontSize: 12.5, color: Colors.black54),
                    ),
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(height: 14),
'''
    s = s[:card_start] + quality_card + s[card_start:]
write(rel, s)

pub = read("pubspec.yaml")
old_version, new_version = (
    ("3.29.165+307", "3.29.166+308")
    if platform == "android"
    else ("3.30.84+271", "3.30.85+272")
)
marker = "version: " + old_version
if pub.count(marker) != 1:
    raise RuntimeError("versao base esperada ausente: " + old_version)
write("pubspec.yaml", pub.replace(marker, "version: " + new_version, 1))

after = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected if (root / name).exists()
}
changed = [name for name in before if before[name] != after[name]]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

widget = read("lib/widgets/offline_report_inline_suggestions.dart")
ronda = read("lib/screens/express_round_screen.dart")
report = read("lib/screens/report_screen.dart")
assert widget.count("OfflineInlineSuggestion(") >= 80
assert "'sem internet'" not in widget
assert "Nenhum modelo semelhante encontrado" in widget
assert "auditar-saida-emergencia-obstruida" in widget
assert "auditar-empilhadeira-sem-cinto" in widget
assert "auditar-escavacao-sem-escoramento" in widget
assert "Qualidade ${_roundReportQualityScore}%" in ronda
assert "Conferir para um relatório mais completo" in ronda
assert "Qualidade do relatório • $reportQualityScore%" in report
assert "A IA continua disponível" in report
assert "version: " + new_version in read("pubspec.yaml")

print("PREMIUM_REPORT_ACCELERATOR_OK", platform, new_version)
print("OFFLINE_SUGGESTIONS_80_PLUS_OK")
print("VISIBLE_SEM_INTERNET_LABEL_REMOVED_OK")
print("RONDA_REPORT_QUALITY_INDICATOR_OK")
print("INSPECTION_REPORT_QUALITY_INDICATOR_OK")
print("AI_SYNC_DB_AUTH_HTTP_MEDIA_DRIVE_GS_PDF_RENDERERS_PRESERVED_OK")

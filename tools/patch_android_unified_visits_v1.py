#!/usr/bin/env python3
"""Android: unified visit entry + read-only Ronda metrics.

Presentation-only: does not modify persisted records, database schema, sync,
auth, photos, AI, Apps Script or PDF renderers. Fails closed on unknown UI.
"""
from pathlib import Path
import hashlib
import re
import shutil
import sys

if len(sys.argv) != 2:
    raise SystemExit("Uso: patch_android_unified_visits_v1.py <APP_DIR>")
app = Path(sys.argv[1])
repo = Path(__file__).resolve().parents[1]
home = app / "lib/screens/home_screen.dart"
quick = app / "lib/screens/quick_visit_screen.dart"
chooser = app / "lib/screens/visit_type_chooser_screen.dart"
metrics = app / "lib/services/unified_visit_metrics.dart"
briefing = app / "lib/screens/smart_visit_briefing_screen.dart"
intelligence = app / "lib/services/visit_intelligence.dart"
pub = app / "pubspec.yaml"

protected_names = (
    "lib/database.dart", "lib/models.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/auth_service.dart",
    "lib/services/drive_service.dart",
    "lib/services/ai_assistant_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/screens/new_inspection_screen.dart",
    "lib/screens/express_round_screen.dart",
    "lib/screens/field_quick_screen.dart",
    "painel_web_google_apps_script/Code.gs",
)
protected = {
    name: hashlib.sha256((app/name).read_bytes()).hexdigest()
    for name in protected_names if (app/name).is_file()
}
assert home.exists() and quick.exists() and not chooser.exists()
assert not metrics.exists(), "Métrica unificada já instalada; inspecione a versão"
assert not briefing.exists() and not intelligence.exists(), (
    "Visita inteligente já existe; inspecione a versão")

def one(src, old, new, why):
    count = src.count(old)
    if count != 1:
        raise RuntimeError(f"{why}: âncora encontrada {count} vez(es)")
    return src.replace(old, new, 1)

# Keep all existing screens/forms; this is a new selector only.
shutil.copyfile(repo/"feature_sources/android_visit_type_chooser_v1.dart", chooser)
shutil.copyfile(repo/"feature_sources/android_unified_visit_metrics_v1.dart", metrics)
shutil.copyfile(repo/"feature_sources/smart_visit_briefing_screen_v1.dart", briefing)
shutil.copyfile(repo/"feature_sources/visit_intelligence_v1.dart", intelligence)

# Quick Visit already performs safe company filtering. Reuse it for Ronda,
# keeping one entry point after company selection and all existing controls.
s = quick.read_text(encoding="utf-8")
s = one(s, "import 'express_round_screen.dart';",
        "import 'express_round_screen.dart';\n"
        "import 'visit_type_chooser_screen.dart';", "import seletor")
s = one(s, "    this.onSelected,\n  });",
        "    this.onSelected,\n    this.onlyRound = false,\n  });",
        "modo Ronda apos escolha")
s = one(s, "  final ValueChanged<Company>? onSelected;",
        "  final ValueChanged<Company>? onSelected;\n"
        "  final bool onlyRound;", "campo modo Ronda")
old_actions = """          _action(
            'Nova ronda',
            'Fotos e descrição das situações encontradas',
            Icons.add_a_photo_outlined,
            ExpressRoundScreen(company: c),
          ),
          _action(
            'Nova vistoria',
            'Inspeção com checklist da empresa selecionada',
            Icons.fact_check_outlined,
            NewInspectionScreen(initialCompany: c, fieldMode: true),
          ),"""
new_actions = """          if (widget.onlyRound)
            _action(
              'Iniciar Ronda Expressa',
              'Empresa selecionada. Abra a coleta de fotos e registros.',
              Icons.add_a_photo_outlined,
              ExpressRoundScreen(company: c),
            ),
          if (!widget.onlyRound)
            _action(
              'Iniciar vistoria',
              'Escolha Checklist, Ronda Expressa ou Vistoria rápida.',
              Icons.fact_check_outlined,
              AuditarVisitTypeChooserScreen(initialCompany: c),
            ),"""
s = one(s, old_actions, new_actions, "opcoes da visita por empresa")
quick.write_text(s, encoding="utf-8", newline="\n")

# Home: the same screen loads locally saved Ronda findings independently.
s = home.read_text(encoding="utf-8")
s = one(s, "import '../services/device_sync_service.dart';",
        "import '../services/device_sync_service.dart';\n"
        "import '../services/unified_visit_metrics.dart';",
        "import das metricas")
if "import 'quick_visit_screen.dart';" not in s:
    raise RuntimeError("Entrada QuickVisit nao instalada")
s = one(s, "import 'quick_visit_screen.dart';",
        "import 'quick_visit_screen.dart';\n"
        "import 'visit_type_chooser_screen.dart';", "import do seletor")

# Restrict insertion to the Home refresh method, not a global text replace.
start = s.index("  Future<void> _refresh(")
end = s.index("  Future<void> _open(", start)
refresh = s[start:end]
assert refresh.count("summary = result;") == 1
assert refresh.count("openNcs = ncRows.length;") == 1
sync_mark = "      summary = result;"
read_metrics = """      // A Ronda grava achados em sst_records; cada roundId conta uma
      // unica vistoria, nao uma vistoria por foto/ocorrencia.
      // Uma falha na consulta nunca impede a Home de abrir.
      RoundVisitOverview? roundMetrics;
      try {
        final savedRoundRecords = await AppDatabase.instance.getSstRecords(
          type: 'OBSERVACAO_SEGURANCA',
        ).timeout(const Duration(seconds: 10));
        final linked = <String>{};
        for (final nc in ncRows) {
          for (final key in const [
            'sst_record_id', 'source_record_id', 'origin_record_id',
          ]) {
            final id = (nc[key] ?? '').toString().trim();
            if (id.isNotEmpty) linked.add(id);
          }
        }
        roundMetrics = UnifiedVisitMetrics.calculate(
          savedRoundRecords.map((record) => <String,Object?>{
            'id': record.id,
            'companyId': record.companyId,
            'status': record.status,
            'payload': record.payload,
          }),
          existingIssueRecordIds: linked,
        );
      } catch (_) {
        // Os dados originais não são alterados; mostra contagens existentes.
      }
"""
# Insert before setState, where final result/ncRows are already in scope.
at = refresh.index("    setState(() {", refresh.index("final result = "))
refresh = refresh[:at] + read_metrics + refresh[at:]
refresh = one(refresh, "      summary = result;",
              "      summary = {...result, 'inspections': "
              "(result['inspections'] ?? 0) + (roundMetrics?.rounds ?? 0)};",
              "total de vistorias")
refresh = one(refresh, "      openNcs = ncRows.length;",
              "      openNcs = ncRows.length + (roundMetrics?.openIssues ?? 0);",
              "total de NCs")
s = s[:start] + refresh + s[end:]

# Only reroute existing Home new-inspection buttons. The actual checklist,
# Ronda and avulsa implementations remain byte-for-byte unchanged.
needle = "() => _open(const NewInspectionScreen())"
count = s.count(needle)
if count < 1 or count > 4:
    raise RuntimeError(f"Rotas de nova vistoria inesperadas: {count}")
s = s.replace(needle, "() => _open(const AuditarVisitTypeChooserScreen())")

# Remove *only* the two redundant main CTA cards between the current green
# button and Acesso rápido. Do not hide reports, progress or pending queues.
begin = s.find("  Widget _completeMobileBody() {")
finish = s.find("  Widget _completeDesktopBody() {", begin)
if begin < 0 or finish <= begin:
    raise RuntimeError("Tela Mais opções não identificada; manter intacta")
body = s[begin:finish]
main = re.search(
    r"(?P<button>_newInspectionButton\(\),)(?P<extra>.*?)"
    r"(?P<section>_sectionHeader\(\s*'Acesso rápido')", body, re.S)
if main is None:
    raise RuntimeError("Layout dos atalhos mudou: não é seguro remover botões")
extra = main.group("extra")
if not (0 < len(extra) < 4000 and "_fieldQuickButton()" in extra):
    raise RuntimeError("Atalhos desconhecidos: atualização interrompida")
if any(x in extra for x in ("_continueInspectionCard()", "_syncQueueCard()",
                             "_overviewPanel(", "_routinePanel(",
                             "_companyResourcesCard()")):
    raise RuntimeError("Área contém componente protegido; nenhuma remoção")
body = body[:main.start("extra")] + (
    "\n          const SizedBox(height: 18),\n          "
) + body[main.end("extra"):]
s = s[:begin] + body + s[finish:]
home.write_text(s, encoding="utf-8", newline="\n")

old = pub.read_text(encoding="utf-8")
old_ver="version: 3.29.200+342"
if old.count(old_ver)!=1:
    raise RuntimeError("Versão Android inesperada; não gerar APK")
pub.write_text(old.replace(old_ver,"version: 3.29.201+343",1),
               encoding="utf-8", newline="\n")
for name,digest in protected.items():
    assert hashlib.sha256((app/name).read_bytes()).hexdigest()==digest, name

assert "UnifiedVisitMetrics.calculate" in home.read_text()
assert "SmartVisitBriefingScreen" in chooser.read_text()
assert "Visita Inteligente" in briefing.read_text()
assert "AuditarVisitTypeChooserScreen" in quick.read_text()
print("ANDROID_UNIFIED_VISITS_READY: UI+read-only metrics; core unchanged")

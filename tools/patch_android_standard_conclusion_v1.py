#!/usr/bin/env python3
"""Ronda Android: use the checklist-style conclusion as the standard draft.

Keep approved conclusions, final review, AI, PDF, photos, DB and sync intact.
The checklist conclusion UI and implementation remain the reference and are
not modified. Fail if the assembled Android source has unexpected structure.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv) != 2:
    raise SystemExit("Uso: patch_android_standard_conclusion_v1.py <APP_DIR>")
root=Path(sys.argv[1])
repo=Path(__file__).resolve().parents[1]
round_file=root/"lib/screens/express_round_screen.dart"
service=root/"lib/services/auditar_unified_conclusion.dart"
test=root/"test/auditar_unified_conclusion_test.dart"
pub=root/"pubspec.yaml"
assert round_file.exists() and not service.exists()
protected=[
    "lib/database.dart", "lib/models.dart",
    "lib/screens/checklist_screen.dart", "lib/screens/report_screen.dart",
    "lib/screens/new_inspection_screen.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/auth_service.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/ai_assistant_service.dart",
    "lib/services/express_round_pdf_service.dart",
    "lib/services/ronda_standard3_pdf_service.dart",
    "painel_web_google_apps_script/Code.gs",
]
before={
    name:hashlib.sha256((root/name).read_bytes()).hexdigest()
    for name in protected if (root/name).is_file()
}
s=round_file.read_text(encoding="utf-8")
import_anchor="import '../services/express_round_pdf_service.dart';"
assert s.count(import_anchor)==1
s=s.replace(import_anchor,import_anchor+
    "\nimport '../services/auditar_unified_conclusion.dart';",1)

# Both the AI fallback and no-IA generated conclusion start with the *same*
# checklist-style neutral structure. They do not replace saved technician text.
common="""  String _standardRoundConclusion() =>
      AuditarUnifiedConclusion.fromRound(
        companyName: widget.company.name,
        findings: roundRecords.length,
        conformities: _conformities,
        nonConformities: _nonConformities,
        highPriority: _highCritical,
        possibleRecurrences: _recurringCount,
      );

"""
offline_start="  String _buildOfflineRoundConclusion() {"
offline_next="  Future<void> _generateRoundConclusionOffline() async {"
fallback_start="  String _fallbackRoundConclusion() {"
fallback_next="  String _extractAiConclusion("
for anchor,nxt,method in [
    (offline_start,offline_next,
     "  String _buildOfflineRoundConclusion() => _standardRoundConclusion();\n\n"),
    (fallback_start,fallback_next,
     "  String _fallbackRoundConclusion() => _standardRoundConclusion();\n\n")
]:
    assert s.count(anchor)==1 and s.count(nxt)==1,(anchor,nxt)
    start=s.index(anchor); end=s.index(nxt,start)
    assert 100<end-start<5500, "Escopo inesperado: "+anchor
    s=s[:start]+method+s[end:]
assert s.count(fallback_start)==0
assert s.count("String _fallbackRoundConclusion() =>")==1
assert s.count("String _buildOfflineRoundConclusion() =>")==1
anchor="  String _buildOfflineRoundConclusion() =>"
assert s.count(anchor)==1
s=s.replace(anchor,common+anchor,1)

# Preserve existing showDialog, handlers, saved settings and PDF calls.
# Only update labels in the conclusion editors.
def in_method_replace(start_marker,end_marker,old,new,label):
    global s
    assert s.count(start_marker)==1 and s.count(end_marker)==1,label
    start=s.index(start_marker); end=s.index(end_marker,start)
    part=s[start:end]
    assert part.count(old)==1,(label,part.count(old))
    s=s[:start]+part.replace(old,new,1)+s[end:]

in_method_replace(
    "  Future<String?> _editRoundConclusion(",
    "  Future<bool> _prepareRoundConclusion(",
    "Conclusão geral da ronda", "Conclusão final da vistoria", "title-ia")
in_method_replace(
    "  Future<String?> _editRoundConclusion(",
    "  Future<bool> _prepareRoundConclusion(",
    "A IA preparou a conclusão com base nos registros da ronda. Revise e ajuste o texto antes de usar no relatório.",
    "Confira e ajuste a conclusão técnica antes de salvar. "
    "Use a IA como apoio, quando disponível; a validação é do responsável técnico.",
    "description-ia")
in_method_replace(
    "  Future<String?> _editRoundConclusion(",
    "  Future<bool> _prepareRoundConclusion(",
    "const Text('Usar no relatório')", "const Text('Salvar conclusão')", "save-ia")
in_method_replace(
    "  Future<void> _generateRoundConclusionOffline() async {",
    "  String _fallbackRoundConclusion() =>",
    "Text('Conclusão sem IA')", "Text('Conclusão do relatório sem IA')",
    "title-offline")
# The offline dialog already has its own cancellation and validation.

round_file.write_text(s,encoding="utf-8",newline="\n")
shutil.copyfile(repo/"feature_sources/auditar_unified_conclusion_v1.dart",service)
shutil.copyfile(repo/"feature_sources/auditar_unified_conclusion_test_v1.dart",test)
pub_text=pub.read_text(encoding="utf-8")
assert pub_text.count("version: 3.29.201+343")==1
pub.write_text(pub_text.replace("version: 3.29.201+343",
    "version: 3.29.202+344",1),encoding="utf-8",newline="\n")
for name,digest in before.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
assert "'express_round_conclusion_$roundId'" in s
assert "_prepareRoundConclusion(" in s
assert "_generateRoundConclusionOffline()" in s
print("ANDROID_CHECKLIST_CONCLUSION_STANDARD_OK; originals and DB intact")

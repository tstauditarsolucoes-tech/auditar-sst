#!/usr/bin/env python3
"""Preflight isolado do guia de investigação; não usa banco real nem gera APK."""
from pathlib import Path
import re

repo = Path(__file__).resolve().parents[1]
guide = (repo / "feature_sources/sst_accident_investigation_guide_v1.dart").read_text(encoding="utf-8")
screen = (repo / "feature_sources/sst_report_center_screen_v1.dart").read_text(encoding="utf-8")
models = (repo / "feature_sources/sst_report_center_models_v1.dart").read_text(encoding="utf-8")
installer = (repo / "tools/patch_sst_report_center_v1.py").read_text(encoding="utf-8")

assert guide.count("    _GuideStage(") == 6, "Deve haver 6 etapas objetivas"
assert len(re.findall(r"\('incident-\d\d',", guide)) == 9, "Nove perguntas acessíveis"
assert {f"incident-{n:02d}" for n in range(1, 10)}.issubset(set(
    re.findall(r"incident-\d\d", guide)
)), "Cada pergunta deve possuir caminho de navegação"
assert "SstAccidentInvestigationGuide(" in screen
assert "if(isIncident)" in screen
assert "_jumpToIncidentQuestion" in screen
assert "Scrollable.ensureVisible" in screen
assert "Card(key:isIncident?_incidentKeys[question.id]:null" in screen
assert "sst_accident_investigation_guide.dart" in screen
assert "sst_accident_investigation_guide_v1.dart" in installer
assert "incident-07" in models and "cinco porquês" in models.lower()
assert "incident-08" in models and "prazo" in models.lower()
assert "incident-09" in models
assert "O aplicativo não envia a CAT" in guide
assert not any(token in guide for token in [
    "Firebase", "http.post", "setSetting", "delete", "AppsScript"
]), "Guia não deve tocar backend ou armazenar dados paralelos"
assert "SstFieldDraftStore" in screen, "Rascunho existente preservado"
assert "SstFieldReportScreen" in screen, "Relatório existente preservado"
print("ACCIDENT_GUIDE_PREFLIGHT_OK: 6 etapas, 9 vínculos, núcleo preservado")

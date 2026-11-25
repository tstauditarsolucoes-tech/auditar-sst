#!/usr/bin/env python3
"""Preflight isolado: assistente, reuso, PET e minutas. Não é compilação Flutter."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
def src(filename):
    return (root / filename).read_text(encoding="utf-8")

guide_model = src("feature_sources/sst_activity_guide_models_v1.dart")
guide_ui = src("feature_sources/sst_activity_guide_screen_v1.dart")
risk_model = src("feature_sources/sst_risk_documents_models_v1.dart")
risk_ui = src("feature_sources/sst_risk_documents_screen_v1.dart")
pet_model = src("feature_sources/sst_pet_nr33_models_v1.dart")
pet_ui = src("feature_sources/sst_pet_nr33_screen_v1.dart")
risk_pdf = src("feature_sources/sst_risk_documents_pdf_v1.dart")
pet_pdf = src("feature_sources/sst_pet_nr33_pdf_v1.dart")
guide_test = src("feature_sources/sst_activity_guide_test_v1.dart")
pet_test = src("feature_sources/sst_pet_nr33_test_v1.dart")
patch = src("tools/patch_sst_report_center_v1.py")

for code in ("altura", "confinado", "maquinas", "soldagem",
             "escavacao", "eletrica", "forno"):
    assert f"code: '{code}'" in guide_model, code
assert "class SstActivityPlan" in guide_model
assert "SstActivityPlanStore" in guide_model
assert "Uri.encodeComponent(user)" in guide_model
assert "Uri.encodeComponent(company)" in guide_model
assert "json['userId'] != expectedUser" in guide_model
assert "json['companyId'] != expectedCompany" in guide_model
assert "class SstActivityGuideScreen" in guide_ui
assert "1. Escolha a atividade" in guide_ui
assert "2. Identifique o serviço e o local" in guide_ui
assert "3. Veja perigos e perguntas" in guide_ui
assert "4. Escolha qual documento" in guide_ui
assert "SstPetNr33Screen(company: widget.company, initialPlan: plan)" in guide_ui
assert "initialPlan: plan" in guide_ui
assert "presetUnreviewed" in risk_model
assert "!presetUnreviewed &&" in risk_model
assert "json['presetUnreviewed'] == true" in risk_model
assert "presetUnreviewed: true" in risk_ui
assert "presetUnreviewed: false" in risk_ui
assert "if (current.items.isEmpty)" in risk_ui
assert "Somente campos vazios serão preenchidos" in risk_ui
assert "SUGESTÃO NÃO CONFERIDA" in risk_ui
assert "SstActivityGuideScreen(company: company)" in risk_ui
assert "Future<void> _importPlan(" in risk_ui
assert "Future<void> _importPlan(" in pet_ui
assert "Somente esses dois campos vazios" in pet_ui
assert "next.withValue('activity', selected.activity)" in pet_ui
assert "next.withValue('location', selected.sector)" in pet_ui
for forbidden in ("next.withValue('oxygen'", "next.withValue('lel'",
                  "next.withValue('supervisor'", "next.withValue('attendant'",
                  "next.withValue('rescuePlan'"):
    assert forbidden not in pet_ui
assert "class SstPetAtmosphereReading" in pet_model
assert "final List<SstPetAtmosphereReading> readings" in pet_model
assert "readings.map((r) => r.toJson())" in pet_model
assert "Future<void> _addAtmosphereReading()" in pet_ui
assert "Leituras atmosféricas complementares" in pet_ui
assert "List<String> get criticalAlerts" in pet_model
assert "d.criticalAlerts" in pet_ui
assert "Leituras atmosféricas complementares - INFORMADAS" in pet_pdf
assert "Não comprova atmosfera segura" in pet_pdf
for source in (risk_pdf, pet_pdf):
    assert "assets/branding/auditar_logo.jpg" in source
    assert "pw.Image(logo" in source
assert "MINUTA PARA CONFERÊNCIA TÉCNICA" in risk_pdf
assert "NÃO É PET EMITIDA" in pet_pdf
assert "ENTRADA PROIBIDA" in pet_pdf
assert guide_test.count("test('") >= 6
assert pet_test.count("test('") >= 12
for new_source in ("sst_activity_guide_models_v1.dart",
                   "sst_activity_guide_screen_v1.dart",
                   "sst_activity_guide_test_v1.dart"):
    assert new_source in patch
for source in (guide_model, guide_ui, risk_model, pet_model):
    assert "http.post(" not in source
    assert "AppsScript" not in source
print("SST_ACTIVITY_GUIDE_PREFLIGHT_OK: flow, human review, PET isolation")

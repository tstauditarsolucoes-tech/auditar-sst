#!/usr/bin/env python3
"""Pré-verificação da PET NR-33; não compila, não acessa fotos/dados reais."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
model = (root/"feature_sources/sst_pet_nr33_models_v1.dart").read_text(encoding="utf-8")
screen = (root/"feature_sources/sst_pet_nr33_screen_v1.dart").read_text(encoding="utf-8")
pdf = (root/"feature_sources/sst_pet_nr33_pdf_v1.dart").read_text(encoding="utf-8")
tests = (root/"feature_sources/sst_pet_nr33_test_v1.dart").read_text(encoding="utf-8")
risk = (root/"feature_sources/sst_risk_documents_screen_v1.dart").read_text(encoding="utf-8")
central = (root/"feature_sources/sst_report_center_screen_v1.dart").read_text(encoding="utf-8")
patch = (root/"tools/patch_sst_report_center_v1.py").read_text(encoding="utf-8")

assert "class SstPetDraft" in model
assert "PetCheckStatus" in model
assert "PetTemplate" in model
for name in ("spaceId", "location", "activity", "hazards",
             "entryHazards", "energyIsolation", "supervisor",
             "attendant", "entrants", "plannedIssue", "plannedEnd",
             "measurementTime", "measurementBy", "detector",
             "oxygen", "lel", "toxic", "monitoring", "rescuePlan",
             "communication", "training", "closingNotes"):
    assert "'"+name+"'" in model, name
assert "PetCheckStatus.notChecked" in model
assert "reportedNo" in model and "notApplicable" in model
assert "Justificar: " in model
assert "if (!_measurementValid(value('oxygen')))" in model
assert "if (!_measurementValid(value('lel')))" in model
assert "double.tryParse" in model and "replaceAll(',', '.')" in model
assert "readyForReviewPdf" in model
assert "Uri.encodeComponent(user)" in model
assert "Uri.encodeComponent(company)" in model
assert "json['userId'] != expectedUser" in model
assert "json['companyId'] != expectedCompany" in model
assert "Já arquivada" in model
assert "NÃO É PET EMITIDA" in pdf
assert "ENTRADA PROIBIDA" in pdf
assert "assinatura certificada" in pdf
assert "SstPetNr33Pdf.generate" in screen
assert "MINUTA - ENTRADA NÃO AUTORIZADA" in screen
assert "Tentar salvar rascunho novamente" in screen
assert "AppDatabase.activeUserId" in screen
assert "AuthService.canAccessCompany" in screen
assert "Não entre no espaço para medir" in screen
assert "SstPetNr33Screen(company: company)" in risk
assert "APR, PT, AR e PET guiados" in central
for file in ("sst_pet_nr33_models_v1.dart", "sst_pet_nr33_pdf_v1.dart",
             "sst_pet_nr33_screen_v1.dart", "sst_pet_nr33_test_v1.dart"):
    assert file in patch, file
assert tests.count("test('") >= 8
for src in (model, screen, pdf):
    assert "http.post(" not in src
    assert "AppsScript" not in src
    assert "upsertSstRecord" not in src
print("PET_NR33_PREFLIGHT_OK: campos, atmosfera, vigia, minutas e isolamento")

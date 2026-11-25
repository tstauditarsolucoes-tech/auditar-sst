#!/usr/bin/env python3
"""Preflight do modulo APR, PT e AR sem dados reais ou backend."""
from pathlib import Path
import re
root = Path(__file__).resolve().parents[1]
models = (root/"feature_sources/sst_risk_documents_models_v1.dart").read_text(encoding="utf-8")
screen = (root/"feature_sources/sst_risk_documents_screen_v1.dart").read_text(encoding="utf-8")
pdf = (root/"feature_sources/sst_risk_documents_pdf_v1.dart").read_text(encoding="utf-8")
central = (root/"feature_sources/sst_report_center_screen_v1.dart").read_text(encoding="utf-8")
patch = (root/"tools/patch_sst_report_center_v1.py").read_text(encoding="utf-8")
tests = (root/"feature_sources/sst_risk_documents_test_v1.dart").read_text(encoding="utf-8")

assert "enum SstRiskDocKind { apr, pt, ar }" in models
assert "SstRiskDocKind.pre" not in models
assert "Permissão de Trabalho" in models
assert "canExportDraft" in models
assert "kind != SstRiskDocKind.pt" in models
assert "authorizer.trim().isNotEmpty" in models
assert "referenceAr.trim().isNotEmpty" in models
assert "team.trim().isNotEmpty" in models
assert "validUntil.trim().isNotEmpty" in models
assert "SstRiskDocStore" in models
assert "Uri.encodeComponent(user)" in models
assert "Uri.encodeComponent(company)" in models
assert "draft.kind" in models
assert "Documento já arquivado; não sobrescrever" in models
assert "SstRiskDocsHomeScreen(company:company)" in central
assert "APR, PT e AR guiados" in central
assert "SstRiskDocKind.values" in screen
assert "await store.save(" in screen
assert "_retrySave()" in screen
assert "await store.archive(" in screen
assert "await Printing.layoutPdf(" in screen
assert "Não foi possível gerar a minuta PDF" in screen
assert "A PT não libera trabalho" in screen
assert "A pessoa indicada NÃO assinou" in pdf
assert "MINUTA PARA CONFERÊNCIA TÉCNICA" in pdf
assert "NÃO AUTORIZA INÍCIO" in pdf
assert "SstRiskDocumentPdf.generate(" in screen
assert "kind == SstRiskDocKind.pt" in screen
assert "NR-33" in screen and "PET específica" in screen
assert "SstRiskDocKind.pt" in tests
assert tests.count("test('") >= 8
assert "sst_risk_documents_models_v1.dart" in patch
assert "sst_risk_documents_pdf_v1.dart" in patch
assert "sst_risk_documents_screen_v1.dart" in patch
assert "sst_risk_documents_test_v1.dart" in patch
assert not re.search(r"(?i)(firebase|http\.post|url\.parse|apps_script)", models+screen+pdf)
assert "auth_service.dart" in screen
assert "AuthService.canAccessCompany" in screen
assert "AppDatabase.activeUserId.toString()" in screen
print("APR_PT_AR_PREFLIGHT_OK: kinds, separacao, minutas, conta, PT e seguranca")

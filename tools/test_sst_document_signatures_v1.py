#!/usr/bin/env python3
"""Checagem estática da captura de rubricas; não valida assinatura legal."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def read(path):
    return (root/path).read_text(encoding='utf-8')

model=read("feature_sources/sst_document_signature_models_v1.dart")
panel=read("feature_sources/sst_document_signature_panel_v1.dart")
test=read("feature_sources/sst_document_signature_test_v1.dart")
risk_ui=read("feature_sources/sst_risk_documents_screen_v1.dart")
pet_ui=read("feature_sources/sst_pet_nr33_screen_v1.dart")
risk_pdf=read("feature_sources/sst_risk_documents_pdf_v1.dart")
pet_pdf=read("feature_sources/sst_pet_nr33_pdf_v1.dart")
installer=read("tools/patch_sst_report_center_v1.py")

assert "class SstHandwrittenMark" in model
assert "class SstHandwrittenSignatureStore" in model
assert "bool isCurrent(String snapshot)" in model
assert "documentSnapshot == snapshot" in model
assert "sstScopedKey(" in model
assert "sstScopedKey(" in model
assert "sstScopedKey(" in model
assert "sstScopedKey(" in model
assert "allowedRoles.contains(mark.roleCode)" in model
assert "validForDocument" in model
assert "m.isCurrent(snapshot)" in model or "mark.isCurrent(snapshot)" in model
assert "SstHandwrittenMark.fromJson(mark.toJson())" in model
assert "pngBase64" in model and "base64Decode" in model
assert "package:signature/signature.dart" in panel
assert "SignatureController(" in panel
assert "await controller.toPngBytes()" in panel
assert "controller.isNotEmpty" in panel
assert "Nome completo do signatário" in panel
assert "Função declarada" in panel
assert "Registrar ciência" in panel
assert "Substituir rubrica" in panel
assert "NÃO autoriza PT/PET" in panel
assert "não é assinatura certificada" in panel
assert "AppDatabase.activeUserId.toString() == widget.userId" in panel
assert "AuthService.canAccessCompany(widget.companyId)" in panel
assert "snapshot != widget.snapshot" in panel
assert "SstDocumentSignaturePanel(" in risk_ui
assert "SstDocumentSignaturePanel(" in pet_ui
assert "signatureStore.validForDocument(" in risk_ui
assert "signatureStore.validForDocument(" in pet_ui
assert "snapshot: sstDocumentFingerprint(value.toJson())" in risk_ui
assert "snapshot: sstDocumentFingerprint(source.toJson())" in pet_ui
assert "sha256.convert(utf8.encode(jsonEncode(fields)))" in model
assert "field('documentSnapshot', 64)" in model
assert "kind: 'pet_nr33'" in pet_ui
assert "kind: 'risk_' + widget.kind.name" in risk_ui
assert "'supervisor_ack'" in pet_ui and "'attendant_ack'" in pet_ui
assert "signatures: signatures" in risk_ui and "signatures: signatures" in pet_ui
assert "List<SstHandwrittenMark> signatures" in risk_pdf
assert "List<SstHandwrittenMark> signatures" in pet_pdf
assert "Assinatura desatualizada" in risk_pdf and "Assinatura desatualizada" in pet_pdf
assert "pw.MemoryImage(base64Decode(mark.pngBase64))" in risk_pdf
assert "pw.MemoryImage(base64Decode(mark.pngBase64))" in pet_pdf
assert "MINUTA" in risk_pdf and "MINUTA" in pet_pdf
assert "ENTRADA PROIBIDA" in pet_pdf
for source in ("sst_document_signature_models_v1.dart",
               "sst_document_signature_panel_v1.dart",
               "sst_document_signature_test_v1.dart"):
    assert source in installer
assert test.count("test('") >= 7
for source in (model, panel, risk_ui, pet_ui):
    assert "http.post(" not in source
    assert "Firebase" not in source
print("SST_SIGN_PREFLIGHT_OK: rubrica local, versão vinculada, PDF e não-autorização")

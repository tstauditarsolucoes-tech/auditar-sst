#!/usr/bin/env python3
"""Inspeciona montagem integral protegida em CI. Nunca publica binários.

Este projeto-base remonta à v3.29.0; prova de integração não é homologação
de atualização sobre Android v3.29.195 ou Windows v3.30.123.
"""
from pathlib import Path
import sys

if len(sys.argv) != 3 or sys.argv[2] not in {"baseline", "integrated"}:
    raise SystemExit("Uso: test_sst_full_integration_probe_v1.py APP_DIR baseline|integrated")
app = Path(sys.argv[1]).resolve()
if not app.is_dir():
    raise SystemExit("Pasta não existente")
pub = (app / "pubspec.yaml").read_text(encoding="utf-8")
version = next((x for x in pub.splitlines() if x.startswith("version:")), "")
assert version
# O arquivo ZIP disponível na raiz do repositório recompõe v3.29.0.
# Não prosseguir à integração de tela/relatório com essa fonte desatualizada.
# No Android operacional a base informada é v3.29.195, no Windows v3.30.123.
import re
m = re.match(r"version:\\s*(\\d+)\\.(\\d+)\\.(\\d+)", version)
if m is None:
    raise SystemExit("BLOQUEADO: versão do fonte não identificável: " + version)
built = tuple(int(x) for x in m.groups())
if built < (3, 29, 195):
    raise SystemExit(
        "BASE_DESATUALIZADA_BLOQUEADA: projeto montado em " + version +
        "; o Android operacional é v3.29.195 e o Windows v3.30.123. "
        "Faltam telas e dependências atuais. Exigida fonte integral recente "
        "para atualizar com segurança. Nenhum binário deve ser publicado."
    )
base = [
    "lib/main.dart", "lib/models.dart", "lib/database.dart",
    "lib/services/auth_service.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/sync_coordinator.dart",
    "lib/screens/new_inspection_screen.dart",
    "lib/screens/express_round_screen.dart",
    "lib/screens/quick_visit_screen.dart",
    "lib/screens/company_detail_screen.dart",
    "painel_web_google_apps_script/Code.gs",
]
missing = [x for x in base if not (app / x).is_file()]
assert not missing, "Projeto-base incompleto: " + ", ".join(missing)
if sys.argv[2] == "integrated":
    expected = [
        "lib/screens/sst_report_center_screen.dart",
        "lib/screens/sst_risk_documents_screen.dart",
        "lib/screens/sst_pet_nr33_screen.dart",
        "lib/screens/sst_activity_guide_screen.dart",
        "lib/screens/sst_document_signature_panel.dart",
        "lib/services/sst_risk_documents_models.dart",
        "lib/services/sst_pet_nr33_models.dart",
        "lib/services/sst_activity_guide_models.dart",
        "lib/services/sst_document_signature_models.dart",
        "lib/services/sst_scope_key.dart",
        "test/sst_scope_key_test.dart",
        "test/sst_document_signature_test.dart",
    ]
    missing = [x for x in expected if not (app / x).is_file()]
    assert not missing, "Integração parcial: " + ", ".join(missing)
    pdf = (app / "lib/services/sst_pet_nr33_pdf.dart").read_text("utf-8")
    assert "ENTRADA PROIBIDA" in pdf
    assert "NÃO É PET EMITIDA" in pdf
print("SST_FULL_APP_PROBE_OK", sys.argv[2], version)
if not version.startswith("version: 3.29.195") and not version.startswith("version: 3.30.123"):
    print("AVISO: base de montagem mais antiga que a versão instalada; "
          "não distribuir como atualização.")

#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) < 2:
    raise SystemExit("uso: regression_operational_finish_v329149_v33068.py <APP_DIR>")

root = Path(sys.argv[1])
center = (root / "lib/screens/training_activity_center_screen.dart").read_text(
    encoding="utf-8"
)
field = (root / "lib/screens/field_intelligence_center_screen.dart").read_text(
    encoding="utf-8"
)
cipa = (root / "lib/screens/cipa_management_screen.dart").read_text(
    encoding="utf-8"
)

for marker in [
    "Capacitação e DDS",
    "type: 'DDS'",
    "type: 'TREINAMENTO_SESSAO'",
    "type: 'INTEGRACAO'",
    "Assinaturas pendentes",
    "Consulta os registros existentes",
]:
    if marker not in center:
        raise SystemExit("OPER_FINISH_TRAINING_MISSING: " + marker)

for marker in [
    "Consultar DDS, treinamentos e integrações",
    "Operação local sem alertas técnicos",
    "Este aparelho requer atenção",
]:
    if marker not in field:
        raise SystemExit("OPER_FINISH_FIELD_MISSING: " + marker)

for marker in [
    "Acesso rápido às pendências",
    "Reuniões • $pending",
    "Atas • $pendingMinutesCount",
    "Ações • $openActions",
    "Treinamentos • $pendingTrainingCount",
]:
    if marker not in cipa:
        raise SystemExit("OPER_FINISH_CIPA_MISSING: " + marker)

for forbidden in ["CREATE TABLE", "ALTER TABLE", "DROP TABLE"]:
    if forbidden in center:
        raise SystemExit("OPER_FINISH_SCHEMA_FORBIDDEN: " + forbidden)

print("OPERATIONAL_FINISH_REGRESSION_OK")

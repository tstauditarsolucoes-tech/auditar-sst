#!/usr/bin/env python3
"""Regressão estática do histórico de treinamentos v3.29.148 / v3.30.67."""
from pathlib import Path
import sys

if len(sys.argv) < 2:
    raise SystemExit(
        "uso: regression_training_history_filters_v329148_v33067.py <APP_DIR>"
    )

root = Path(sys.argv[1])
screen = (root / "lib/screens/training_records_screen.dart").read_text(
    encoding="utf-8"
)

required = [
    "Pesquisar treinamento ou participante",
    "Nome, código, instrutor, local ou colaborador",
    "'Em andamento'",
    "'Finalizados'",
    "'Assinaturas pendentes'",
    "_visibleHistoryRecords",
    "participantNames",
    "visibleRecords.length",
    "TrainingRecordDetailScreen",
    "Pré-admissão / integração",
]
for marker in required:
    if marker not in screen:
        raise SystemExit("TRAINING_HISTORY_REGRESSION_MISSING: " + marker)

for forbidden in [
    "CREATE TABLE",
    "ALTER TABLE",
    "DROP TABLE",
]:
    if forbidden in screen:
        raise SystemExit("TRAINING_HISTORY_REGRESSION_FORBIDDEN: " + forbidden)

print("TRAINING_HISTORY_FILTERS_REGRESSION_OK")

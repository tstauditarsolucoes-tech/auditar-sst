#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import hashlib
import io
import sys
import tarfile
from pathlib import Path

EXPECTED_GZ_SHA256 = "053b2591010f090fcd4b90e8c333c88edb2fd381f704705060ad81fdb518e8e5"
PARTS = [f"v3290s.part{i:02d}" for i in range(14)]


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: apply_v3290_final_overrides.py <raiz-do-app>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    if not (root / "pubspec.yaml").exists():
        print(f"raiz inválida: {root}", file=sys.stderr)
        return 2

    here = Path(__file__).resolve().parent
    chunks: list[str] = []
    for name in PARTS:
        path = here / name
        if not path.exists():
            raise RuntimeError(f"parte ausente: {name}")
        chunks.append(path.read_text(encoding="utf-8").strip())

    gz = base64.b64decode("".join(chunks), validate=True)
    digest = hashlib.sha256(gz).hexdigest()
    if digest != EXPECTED_GZ_SHA256:
        raise RuntimeError(
            f"payload final v3.29.0 corrompido: sha256={digest}, esperado={EXPECTED_GZ_SHA256}"
        )

    tar_bytes = gzip.decompress(gz)
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:") as tf:
        members = tf.getmembers()
        for member in members:
            target = (root / member.name).resolve()
            try:
                target.relative_to(root)
            except ValueError as exc:
                raise RuntimeError(f"caminho inseguro no payload: {member.name}") from exc
        tf.extractall(root, members=members)

    required = {
        "pubspec.yaml": "version: 3.29.0+142",
        "lib/screens/signature_screen.dart": "Assinar externamente por Gov.br",
        "lib/screens/report_screen.dart": "Incluir plano de ação no relatório",
        "lib/services/pdf_service.dart": "O QUE FOI IDENTIFICADO",
        "lib/database.dart": "report_signature_mode",
        "lib/screens/new_inspection_screen.dart": "backgroundColor: Colors.white",
        "lib/screens/home_screen.dart": "versão 3.29.0",
    }
    for rel, marker in required.items():
        text = (root / rel).read_text(encoding="utf-8")
        if marker not in text:
            raise RuntimeError(f"validação final falhou em {rel}: {marker}")

    if "include_action_plan" not in (root / "lib/database.dart").read_text(encoding="utf-8"):
        raise RuntimeError("campo include_action_plan ausente")

    print("Overrides finais v3.29.0 aplicados e validados com sucesso")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

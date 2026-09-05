#!/usr/bin/env python3
from __future__ import annotations

import base64
import io
import sys
import tarfile
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: patch_v3290.py <raiz-do-app>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    if not (root / "pubspec.yaml").exists():
        print(f"raiz inválida: {root}", file=sys.stderr)
        return 2

    payload = Path(__file__).resolve().parent / "v3290_overrides.b64"
    if not payload.exists():
        print("overrides finais da v3.29.0 ausentes", file=sys.stderr)
        return 2

    raw = base64.b64decode(payload.read_text(encoding="utf-8").strip())
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        for member in archive.getmembers():
            target = (root / member.name).resolve()
            if root not in target.parents and target != root:
                raise RuntimeError(f"caminho inválido no pacote: {member.name}")
        archive.extractall(root)

    print(
        "v3.29.0 aplicada por overrides finais: relatório executivo, Gov.br, "
        "emissão sem assinatura, plano de ação opcional, permissões, versão e desempenho"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

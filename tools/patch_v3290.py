#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: patch_v3290.py <raiz-do-app>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    if not (root / "pubspec.yaml").exists():
        print(f"raiz inválida: {root}", file=sys.stderr)
        return 2

    here = Path(__file__).resolve().parent
    parts: list[str] = []
    for index in range(1, 5):
        part = here / f"patch_v3290.part{index}"
        if not part.exists():
            raise RuntimeError(f"parte ausente: {part.name}")
        parts.append(part.read_text(encoding="utf-8").strip())

    diff = gzip.decompress(base64.b64decode("".join(parts)))

    repo_root = here.parent.resolve()
    try:
        relative_root = root.relative_to(repo_root).as_posix()
    except ValueError as exc:
        raise RuntimeError(f"raiz do app fora do repositório: {root}") from exc

    with tempfile.NamedTemporaryFile(suffix=".diff", delete=False) as handle:
        handle.write(diff)
        patch_name = handle.name

    try:
        subprocess.run(
            [
                "git",
                "apply",
                "--unsafe-paths",
                "--whitespace=nowarn",
                f"--directory={relative_root}",
                patch_name,
            ],
            cwd=repo_root,
            check=True,
        )
    finally:
        Path(patch_name).unlink(missing_ok=True)

    required = [
        ("pubspec.yaml", "version: 3.29.0+142"),
        ("lib/screens/signature_screen.dart", "Assinar externamente por Gov.br"),
        ("lib/screens/signature_screen.dart", "Emitir sem assinatura"),
        ("lib/screens/report_screen.dart", "Incluir plano de ação"),
        ("lib/services/pdf_service.dart", "O QUE FOI IDENTIFICADO"),
        ("lib/services/auth_service.dart", "purgeCompaniesOutsideAccess"),
        ("lib/screens/home_screen.dart", "versão 3.29.0"),
        ("lib/screens/new_inspection_screen.dart", "backgroundColor: Colors.white"),
    ]
    for rel, marker in required:
        text = (root / rel).read_text(encoding="utf-8")
        if marker not in text:
            raise RuntimeError(f"validação v3.29.0 falhou em {rel}: {marker}")

    print("v3.29.0 aplicada sobre a base v3.27.0 com sucesso")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
    parts = []
    for name in ("patch_v3290.new1", "patch_v3290.new2", "patch_v3290.new3"):
        part = here / name
        if not part.exists():
            print(f"parte ausente: {name}", file=sys.stderr)
            return 2
        parts.append(part.read_text(encoding="utf-8").strip())

    diff = gzip.decompress(base64.b64decode("".join(parts)))
    with tempfile.NamedTemporaryFile(suffix=".diff", delete=False) as f:
        f.write(diff)
        patch_name = f.name

    try:
        repo_top = Path(
            subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=root,
                text=True,
            ).strip()
        ).resolve()
        relative_root = root.relative_to(repo_top).as_posix()
        subprocess.run(
            [
                "git",
                "apply",
                "--unsafe-paths",
                "--whitespace=nowarn",
                f"--directory={relative_root}",
                patch_name,
            ],
            cwd=repo_top,
            check=True,
        )
    finally:
        Path(patch_name).unlink(missing_ok=True)

    required = {
        "pubspec.yaml": "version: 3.29.0+142",
        "lib/screens/signature_screen.dart": "Assinar externamente por Gov.br",
        "lib/screens/report_screen.dart": "Incluir plano de ação",
        "lib/services/pdf_service.dart": "O QUE FOI IDENTIFICADO",
        "lib/services/auth_service.dart": "purgeCompaniesOutsideAccess",
        "lib/screens/home_screen.dart": "versão 3.29.0",
        "lib/screens/new_inspection_screen.dart": "backgroundColor: Colors.white",
    }
    for rel, marker in required.items():
        text = (root / rel).read_text(encoding="utf-8")
        if marker not in text:
            raise RuntimeError(f"validação v3.29.0 falhou em {rel}: {marker}")

    print("v3.29.0 aplicada no app montado com sucesso")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

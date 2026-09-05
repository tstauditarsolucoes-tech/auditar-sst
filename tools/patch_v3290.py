#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import shutil
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
    for i in range(1, 20):
        part = here / f"patch_v3290.part{i}"
        if not part.exists():
            break
        parts.append(part.read_text(encoding="utf-8").strip())
    if not parts:
        print("payload da v3.29.0 ausente", file=sys.stderr)
        return 2

    diff = gzip.decompress(base64.b64decode("".join(parts)))
    with tempfile.NamedTemporaryFile(suffix=".diff", delete=False) as f:
        f.write(diff)
        patch_name = f.name

    nested_git = root / ".git"
    created_nested_git = not nested_git.exists()

    try:
        # O app é montado dentro do checkout principal do GitHub Actions. Sem um
        # repositório Git próprio aqui, `git apply` pode interpretar os caminhos
        # relativamente ao repositório pai e ignorar os arquivos do app montado.
        if created_nested_git:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)

        subprocess.run(
            [
                "git",
                "apply",
                "--unsafe-paths",
                "--whitespace=nowarn",
                patch_name,
            ],
            cwd=root,
            check=True,
        )
    finally:
        Path(patch_name).unlink(missing_ok=True)
        if created_nested_git:
            shutil.rmtree(nested_git, ignore_errors=True)

    print(
        "v3.29.0 aplicada: relatório executivo, Gov.br, permissões, versão e desempenho"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

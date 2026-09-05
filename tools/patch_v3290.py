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
    for name in ("patch_v3290.part1", "patch_v3290.part2"):
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
        subprocess.run(
            ["git", "apply", "--unsafe-paths", "--whitespace=nowarn", patch_name],
            cwd=root,
            check=True,
        )
    finally:
        Path(patch_name).unlink(missing_ok=True)

    print("v3.29.0 aplicada sobre a base v3.27.0 com sucesso")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

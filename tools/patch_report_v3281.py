#!/usr/bin/env python3
from __future__ import annotations
import base64, gzip, subprocess, sys, tempfile
from pathlib import Path


def _apply_inside_app(root: Path, patch_name: str) -> None:
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


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: patch_report_v3281.py <raiz-do-app>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    if not (root / "pubspec.yaml").exists():
        print(f"raiz inválida: {root}", file=sys.stderr)
        return 2
    here = Path(__file__).resolve().parent
    parts = []
    for i in range(1, 10):
        part = here / f"patch_report_v3281.part{i}"
        if not part.exists():
            break
        parts.append(part.read_text(encoding="utf-8").strip())
    if not parts:
        print("payload da v3.28.1 ausente", file=sys.stderr)
        return 2
    diff = gzip.decompress(base64.b64decode("".join(parts)))
    with tempfile.NamedTemporaryFile(suffix=".diff", delete=False) as f:
        f.write(diff)
        name = f.name
    try:
        _apply_inside_app(root, name)
    finally:
        Path(name).unlink(missing_ok=True)

    required = {
        "pubspec.yaml": "version: 3.28.1+142",
        "lib/screens/report_screen.dart": "Incluir plano de ação no PDF",
        "lib/services/pdf_service.dart": "O QUE FOI IDENTIFICADO",
    }
    for rel, marker in required.items():
        if marker not in (root / rel).read_text(encoding="utf-8"):
            raise RuntimeError(f"v3.28.1 não foi aplicada no app montado em {rel}: {marker}")
    print("v3.28.1 relatório executivo aplicada no app com sucesso")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

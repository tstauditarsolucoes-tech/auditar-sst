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
    names = [
        "v3290_clean.part1a",
        "v3290_clean.part1b",
        "v3290_clean.part2",
        "v3290_clean.part3",
        "v3290_clean.part4",
        "v3290_clean.part5",
        "v3290_clean.part6",
    ]
    parts = []
    for name in names:
        part = here / name
        if not part.exists():
            print(f"payload ausente: {part.name}", file=sys.stderr)
            return 2
        parts.append(part.read_text(encoding="utf-8").strip())

    try:
        diff = gzip.decompress(base64.b64decode("".join(parts), validate=True))
    except Exception as exc:
        raise RuntimeError(f"payload v3.29.0 inválido: {exc}") from exc

    # O banco montado pela cadeia atual já vem formatado exatamente como o
    # primeiro hunk do diff tentava formatar. Removemos somente esse hunk
    # cosmético para preservar todas as alterações funcionais seguintes.
    cosmetic_hunk = b"""@@ -61,10 +61,9 @@\n \n   Future<String> get databaseFilePath async {\n     final dbPath = await getDatabasesPath();\n-    final fileName =\n-        _activeUserId.isEmpty\n-            ? 'auditar_sst.db'\n-            : 'auditar_sst_$_activeUserId.db';\n+    final fileName = _activeUserId.isEmpty\n+        ? 'auditar_sst.db'\n+        : 'auditar_sst_$_activeUserId.db';\n     return join(dbPath, fileName);\n   }\n \n"""
    if cosmetic_hunk in diff:
        diff = diff.replace(cosmetic_hunk, b"", 1)

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
        "lib/screens/report_screen.dart": "Incluir plano de ação no relatório",
        "lib/services/pdf_service.dart": "O QUE FOI IDENTIFICADO",
        "lib/services/auth_service.dart": "purgeCompaniesOutsideAccess",
        "lib/screens/home_screen.dart": "versão 3.29.0",
        "lib/screens/new_inspection_screen.dart": "backgroundColor: Colors.white",
        "lib/database.dart": "report_signature_mode",
    }
    for rel, marker in required.items():
        text = (root / rel).read_text(encoding="utf-8")
        if marker not in text:
            raise RuntimeError(f"validação v3.29.0 falhou em {rel}: {marker}")

    signature = (root / "lib/screens/signature_screen.dart").read_text(encoding="utf-8")
    if "Emitir sem assinatura" not in signature:
        raise RuntimeError("emissão sem assinatura ausente")

    database = (root / "lib/database.dart").read_text(encoding="utf-8")
    if "include_action_plan" not in database:
        raise RuntimeError("campo include_action_plan ausente")

    print("v3.29.0 consolidada aplicada com sucesso")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

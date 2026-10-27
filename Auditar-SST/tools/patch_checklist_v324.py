#!/usr/bin/env python3
"""Aplica as melhorias de checklist/vistoria da v3.24 sobre a fonte montada."""
from __future__ import annotations

import base64
import re
import sys
import zlib
from pathlib import Path

_PATCH_B64 = (
    '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'
    'Bn3dQHCv4fH//6EIz/U='
)

_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

def _apply_file(root: Path, rel: str, hunks: list[list[str]]) -> None:
    path = root / rel
    source = path.read_text(encoding="utf-8").splitlines(True)
    out: list[str] = []
    cursor = 0

    for hunk in hunks:
        match = _HUNK.match(hunk[0])
        if not match:
            raise RuntimeError(f"Hunk inválido em {rel}: {hunk[0].strip()}")
        old_start = int(match.group(1))
        target = max(0, old_start - 1)
        out.extend(source[cursor:target])
        cursor = target

        for line in hunk[1:]:
            if line.startswith("\\"):
                continue
            prefix = line[:1]
            content = line[1:]
            if prefix == " ":
                if cursor >= len(source) or source[cursor] != content:
                    raise RuntimeError(
                        f"Contexto divergente em {rel} na linha {cursor + 1}."
                    )
                out.append(source[cursor])
                cursor += 1
            elif prefix == "-":
                if cursor >= len(source) or source[cursor] != content:
                    raise RuntimeError(
                        f"Remoção divergente em {rel} na linha {cursor + 1}."
                    )
                cursor += 1
            elif prefix == "+":
                out.append(content)
            else:
                raise RuntimeError(f"Linha de patch inválida em {rel}: {line!r}")

    out.extend(source[cursor:])
    path.write_text("".join(out), encoding="utf-8")

def _apply_patch(root: Path, patch_text: str) -> None:
    lines = patch_text.splitlines(True)
    i = 0
    while i < len(lines):
        if not lines[i].startswith("--- a/"):
            i += 1
            continue
        old_rel = lines[i][6:].strip()
        i += 1
        if i >= len(lines) or not lines[i].startswith("+++ b/"):
            raise RuntimeError(f"Cabeçalho de patch incompleto para {old_rel}.")
        new_rel = lines[i][6:].strip()
        if old_rel != new_rel:
            raise RuntimeError(f"Rename não suportado: {old_rel} -> {new_rel}")
        i += 1

        hunks: list[list[str]] = []
        while i < len(lines) and not lines[i].startswith("--- a/"):
            if lines[i].startswith("@@ "):
                hunk = [lines[i]]
                i += 1
                while (
                    i < len(lines)
                    and not lines[i].startswith("@@ ")
                    and not lines[i].startswith("--- a/")
                ):
                    hunk.append(lines[i])
                    i += 1
                hunks.append(hunk)
            else:
                i += 1
        _apply_file(root, new_rel, hunks)

def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: patch_checklist_v324.py <pasta-do-projeto>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    patch_text = zlib.decompress(base64.b64decode(_PATCH_B64)).decode("utf-8")
    _apply_patch(root, patch_text)

    pubspec = root / "pubspec.yaml"
    text = pubspec.read_text(encoding="utf-8")
    text = re.sub(
        r"^version:\s*\d+\.\d+\.\d+\+\d+\s*$",
        "version: 3.24.0+100",
        text,
        flags=re.M,
    )
    pubspec.write_text(text, encoding="utf-8")
    print("Checklist inteligente v3.24 aplicado.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

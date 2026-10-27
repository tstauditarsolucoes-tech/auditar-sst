#!/usr/bin/env python3
from pathlib import Path
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: fix_v3290_pdf_syntax.py <raiz-do-app>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    path = root / "lib/services/pdf_service.dart"
    text = path.read_text(encoding="utf-8")

    old = """        ),\n      )\n    else\n      body.add(\n        _signatureInfoBlock("""
    new = """        ),\n      );\n    else\n      body.add(\n        _signatureInfoBlock("""

    if old in text:
        text = text.replace(old, new, 1)
        path.write_text(text, encoding="utf-8")
        print("v3.29.0: sintaxe do bloco de assinatura do PDF corrigida")
    elif new in text:
        print("v3.29.0: correção do PDF já aplicada")
    else:
        raise RuntimeError("trecho esperado do bloco de assinatura não encontrado")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

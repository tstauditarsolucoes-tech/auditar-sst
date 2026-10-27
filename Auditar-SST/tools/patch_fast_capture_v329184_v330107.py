#!/usr/bin/env python3
"""Atalho opcional de nova NC mantendo o formulario e dados atuais."""
from pathlib import Path
import hashlib
import sys

root = Path(sys.argv[1])
platform = sys.argv[2]
assert platform in ("android", "windows")
quick = root / "lib/screens/quick_visit_screen.dart"
assert quick.exists()
protected = [p for folder in ("lib", "painel_web_google_apps_script")
             for p in (root / folder).rglob("*") if p.is_file() and p != quick]
before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
s = quick.read_text(encoding="utf-8")
anchor = "      await _open(SafetyObservationFormScreen(company: c, sectors: sectors));"
assert s.count(anchor) == 1 and "Registrar outra ocorrência nesta empresa?" not in s
# Source with the safer close-form notice already has "Outro registro".
# Avoid duplicate snackbars; do not change the form or its save behavior.
if "'Outro registro'" in s:
    assert "Formulário fechado" in s, "Unrecognized existing capture notice"
else:
    s = s.replace(anchor, anchor + """
      // Reabre o fluxo original. Não presume que o formulário foi salvo.
      if (!mounted || _selected?.id != c.id) return;
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Registrar outra ocorrência nesta empresa?'),
          duration: const Duration(seconds: 7),
          action: SnackBarAction(
            label: 'Novo registro',
            onPressed: _recordObservation,
          ),
        ),
      );""", 1)
quick.write_text(s, encoding="utf-8", newline="\n")
pub = root / "pubspec.yaml"
s = pub.read_text(encoding="utf-8")
old, new = (("3.29.183+325", "3.29.184+326") if platform == "android"
            else ("3.30.106+293", "3.30.107+294"))
assert s.count("version: " + old) == 1
pub.write_text(s.replace("version: " + old, "version: " + new, 1),
               encoding="utf-8", newline="\n")
for path, digest in before.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, str(path)
print("CAPTURA_SEQUENCIAL_READY; CORE_AND_GS_UNCHANGED", platform)

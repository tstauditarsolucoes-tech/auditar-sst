#!/usr/bin/env python3
"""Regressão isolada: campo de assinatura embutido nunca recebe toques."""
from pathlib import Path
import subprocess
import sys
import tempfile

script=Path(__file__).with_name("patch_checklist_signature_lock_v1.py")
with tempfile.TemporaryDirectory() as temp:
    root=Path(temp)
    screen=root/"lib/screens/signature_screen.dart"
    screen.parent.mkdir(parents=True)
    before="""class SignatureTestScreen {
  Widget _signatureCard({
    required SignatureController controller,
  }) {
    return Column(children: [
      Signature(
        controller: controller,
        width: 200,
        height: 220,
        backgroundColor: Colors.white,
      ),
      const Text('ASSINAR EM TELA CHEIA • ÁREA MAIOR'),
    ]);
  }
  Widget other() => const Text('Não afetar outra função');
}
"""
    screen.write_text(before,encoding="utf-8")
    run=subprocess.run([sys.executable,str(script),str(root)],
        capture_output=True,text=True)
    assert run.returncode==0,(run.stdout,run.stderr)
    after=screen.read_text(encoding="utf-8")
    assert "IgnorePointer(" in after
    assert "ignoring: true" in after
    assert "child: Signature(" in after
    assert "Widget other() => const Text('Não afetar outra função')" in after
    assert "ASSINAR EM TELA CHEIA" in after
    # Falhar fechado quando a assinatura já está protegida evita duplicá-la.
    second=subprocess.run([sys.executable,str(script),str(root)],
        capture_output=True,text=True)
    assert second.returncode!=0
    assert screen.read_text(encoding="utf-8")==after
print("SIGNATURE_LOCK_ISOLATED_REGRESSION_OK")
